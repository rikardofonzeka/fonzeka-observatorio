#!/usr/bin/env python3
"""Publica solo fichas aprobadas y enviadas por la mesa privada; no publica bandejas."""
import argparse
import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def validar(item):
    if not isinstance(item, dict) or not isinstance(item.get('document'), dict):
        raise ValueError('Ficha inválida')
    d = item['document']
    expected = {'id','codigo','fecha_dof','titulo','url','dependencia','alcance','version','editorial','plantilla_sha256'}
    if set(d) != expected or not all(isinstance(v, str) for k,v in d.items() if k!='editorial'):
        raise ValueError('Campos no permitidos')
    if not re.fullmatch(r'\d{7}', d['codigo']):
        raise ValueError('Código inválido')
    date = dt.date.fromisoformat(d['fecha_dof'])
    if d['id'] != f"DOF-{d['codigo']}-{date}" or not re.fullmatch(r'[1-9][0-9]*',d['version']):
        raise ValueError('Identificador o versión inválidos')
    if not 5 <= len(d['titulo']) <= 4000 or len(d['alcance']) > 2000:
        raise ValueError('Contenido fuera de límites')
    u = urlparse(d['url']); q = parse_qs(u.query)
    if u.scheme != 'https' or u.netloc != 'dof.gob.mx' or u.path != '/nota_detalle.php' or q.get('codigo') != [d['codigo']] or q.get('fecha') != [date.strftime('%d/%m/%Y')]:
        raise ValueError('Fuente oficial inconsistente')
    fields={'resumen','cambios','antecedentes','transitorios','implicaciones','evidencia'}
    if not isinstance(d['editorial'],dict) or set(d['editorial'])!=fields or not all(isinstance(v,str) and 10<=len(v.strip())<=12000 for v in d['editorial'].values()):
        raise ValueError('Ficha editorial incompleta')
    template=json.loads((Path(__file__).parent/'publication-template.json').read_text())
    if hashlib.sha256(template.encode()).hexdigest()!=d['plantilla_sha256']:
        raise ValueError('La plantilla no coincide con la versión aprobada')
    digest = hashlib.sha256(json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    if item.get('content_hash') != digest or item.get('review_key') != d['id']+':'+digest:
        raise ValueError('La huella de la versión autorizada no coincide')
    instants = {}
    for f in ['approved_at', 'sent_at']:
        instant = dt.datetime.fromisoformat(item[f].replace('Z','+00:00'))
        instants[f] = instant
        if instant.tzinfo is None:
            raise ValueError('Fecha sin zona horaria')
    if instants['sent_at'] < instants['approved_at']:
        raise ValueError('Envío anterior a aprobación')
    return d


def page(title, body):
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' | fonzeka®</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:850px;margin:40px auto;padding:20px;color:#172c40;background:#f6f8fa;line-height:1.7}article{background:white;padding:24px;border:1px solid #dce2e9;border-radius:12px}a{color:#0e6e8b}h1{font-size:1.6rem}small{display:block;overflow-wrap:anywhere;color:#627788}</style></head><body>'+body+'</body></html>\n'


def publicar(queue, root, ack):
    if queue.get('schema') != 1 or not isinstance(queue.get('items'), list) or len(queue['items']) > 100:
        raise ValueError('Cola inválida')
    # Validate the complete batch before changing any file.
    validated = [(i, validar(i)) for i in queue['items']]
    if not validated:
        ack.write_text(json.dumps({'keys':[]})+'\n'); return
    out = root/'publicaciones/dof'
    manifest = out/'aprobaciones.json'
    old = json.loads(manifest.read_text()) if manifest.exists() else []
    entries = {r['id']:r for r in old}
    out.mkdir(parents=True, exist_ok=True)
    for i,d in validated:
        filename = f"expediente-{d['codigo']}-v{d['version']}.html"
        existing = entries.get(d['id'])
        if existing and existing['version']==d['version'] and existing['sha256_contenido'] != i['content_hash']:
            raise ValueError('No se sobrescribe otra versión aprobada')
        record = {**d,'archivo':filename,'sha256_contenido':i['content_hash'],'autorizacion_editorial_utc':i['approved_at'],'envio_publicacion_utc':i['sent_at']}
        entries[d['id']] = record
        template=json.loads((Path(__file__).parent/'publication-template.json').read_text())
        escape=html.escape
        def paragraphs(text):
            return ''.join('<p>'+escape(x).replace('\n','<br>')+'</p>' for x in re.split(r'\n\s*\n',text))
        values={'BASE':'../../','TITLE':escape(d['titulo']),'CODE':escape(d['codigo']),'DATE':escape(d['fecha_dof']),'AGENCY':escape(d['dependencia'] or 'Fuente oficial'),'VERSION':escape(d['version']),'APPROVED':escape(i['approved_at']),'SCOPE':escape(d['alcance']),'URL':escape(d['url'],quote=True),'HASH':escape(i['content_hash']),'RESUMEN':escape(d['editorial']['resumen'])}
        for field in ['cambios','antecedentes','transitorios','implicaciones','evidencia']:
            values[field.upper()]=paragraphs(d['editorial'][field])
        rendered=re.sub(r'\{\{([A-Z]+)\}\}',lambda m:values[m[1]],template)
        (out/filename).write_text(rendered)
    all_records=sorted(entries.values(),key=lambda r:(r['fecha_dof'],r['codigo']),reverse=True)
    manifest.write_text(json.dumps(all_records,ensure_ascii=False,indent=2)+'\n')
    body='<nav><a href="../../">Volver al Observatorio</a></nav><h1>Publicaciones documentales DOF</h1><p>Fichas autorizadas para consulta pública. La fecha del DOF se distingue de la autorización editorial; no se certifica vigencia jurídica.</p><ul>'
    body+=''.join('<li><a href="'+html.escape(r['archivo'],quote=True)+'">'+html.escape(r['titulo'])+'</a> · '+r['fecha_dof']+'</li>' for r in all_records)+'</ul>'
    (out/'index.html').write_text(page('Publicaciones documentales DOF',body))
    home=root/'index.html'
    content=home.read_text()
    cards=''
    for r in all_records:
        cards+='<div class="steps expediente" data-fecha="'+r['fecha_dof']+'" data-expediente="DOF '+html.escape(r['codigo'])+'" data-tipo-fecha="Publicación DOF" style="border-left:4px solid #e9812e;margin:18px 0"><div class="kicker">Expediente DOF '+html.escape(r['codigo'])+' · '+html.escape(r['dependencia'] or 'Fuente oficial')+' · Publicación DOF '+r['fecha_dof']+'</div><h3 style="font-size:21px;margin:12px 0">'+html.escape(r['titulo'])+'</h3><p>'+html.escape(r['editorial']['resumen'])+'</p><p class="small">Ficha editorial autorizada · Versión '+r['version']+' · Autorización '+html.escape(r['autorizacion_editorial_utc'])+'</p><div class="links"><a href="publicaciones/dof/'+r['archivo']+'">Leer ficha técnica y transitorios →</a><a href="'+html.escape(r['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">Documento oficial DOF ↗</a></div></div>'
    start='<!-- FONZEKA_APROBADOS_INICIO -->';end='<!-- FONZEKA_APROBADOS_FIN -->'
    block=start+cards+end
    if start in content and end in content:
        content=content[:content.index(start)]+block+content[content.index(end)+len(end):]
    else:
        marker='<h2 id="titexp">Publicaciones y análisis</h2>'
        if marker not in content:raise ValueError('Portada sin punto de integración conocido')
        content=content.replace(marker,marker+block,1)
    home.write_text(content)
    ack.write_text(json.dumps({'keys':[i['review_key'] for i,d in validated]})+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--queue',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--ack',type=Path,required=True);a=p.parse_args()
    publicar(json.loads(a.queue.read_text()),a.root,a.ack)
