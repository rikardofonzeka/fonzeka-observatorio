#!/usr/bin/env python3
"""fonzeka® DOF 0.2. Extracción conservadora con estado persistente, sin publicación editorial."""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from html.parser import HTMLParser
from html import unescape

BASE = 'https://dof.gob.mx/'
KEYWORDS = ('electricidad','eléctric','energía','energia','generaci','transmisión','distribución',
            'interconexión','cenace','comisión nacional de energía','sector eléctrico',
            'sener','comisión federal de electricidad','cfe','red nacional de transmisión')
MAX_BYTES = 3_000_000

class DOFLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.current=None; self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if 'nota_detalle' in href and ('codigo=' in href or 'codigo%3D' in href):
                self.current=[href,[]]
    def handle_data(self,data):
        if self.current is not None: self.current[1].append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:
            href,chunks=self.current
            title=' '.join(unescape(''.join(chunks)).split())
            if title: self.items.append({'url':urllib.parse.urljoin(BASE,href),'titulo':title})
            self.current=None

def extract_links(raw):
    parser=DOFLinks();parser.feed(raw)
    result={}
    for item in parser.items:
        parsed=urllib.parse.urlparse(item['url']); qs=urllib.parse.parse_qs(parsed.query)
        key=qs.get('codigo',[''])[0] or item['url']
        if key not in result: result[key]={**item,'codigo':key}
    return list(result.values())

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'fonzeka-observatorio/0.2 (investigacion documental)',
                                            'Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req,timeout=25) as response:
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise RuntimeError('Respuesta supera el limite de lectura de 3 MB')
        charset=response.headers.get_content_charset() or 'utf-8'
    return raw,raw.decode(charset,errors='replace')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def load_state(path):
    if not path.exists(): return {'schema':2,'documents':{},'runs':[]}
    o=json.loads(path.read_text(encoding='utf-8'))
    if o.get('schema')!=2 or not isinstance(o.get('documents'),dict):raise ValueError('Historial incompatible')
    return o

def run(date_str,output,state_path,html_file=None,fetch_documents=True):
    day=dt.date.fromisoformat(date_str)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    url=BASE+f'index.php?year={day.year}&month={day.month:02d}&day={day.day:02d}'
    output.mkdir(parents=True,exist_ok=True)
    state=load_state(state_path)
    status={'fecha_consultada':str(day),'consulta_utc':now,'url_indice':url,
            'estado':'ERROR','total_enlaces_detectados':0,'candidatos_palabra_clave':0,
            'nuevos':0,'cambios_de_titulo':0,'cambios_de_contenido':0,
            'sin_verificacion_documental':0,'advertencia':'Deteccion automatica no equivale a evaluacion juridica ni aprobacion editorial.'}
    candidates=[]
    try:
        raw=Path(html_file).read_text(encoding='utf-8') if html_file else fetch(url)[1]
        found=extract_links(raw)
        if not found:raise RuntimeError('Indice sin enlaces reconocibles; no equivale a ausencia de publicaciones')
        status['total_enlaces_detectados']=len(found)
        for item in found:
            if not any(word in item['titulo'].lower() for word in KEYWORDS):continue
            key=item['codigo']; old=state['documents'].get(key)
            doc={'codigo':key,'url':item['url'],'titulo':item['titulo'], 'fecha_primera_deteccion': old['fecha_primera_deteccion'] if old else now,
                 'ultima_revision':now,'fecha_indice':str(day),
                 'estado_editorial':old.get('estado_editorial','PENDIENTE_DE_REVISION') if old else 'PENDIENTE_DE_REVISION',
                 'sha256_contenido':old.get('sha256_contenido') if old else None,
                 'estado_evidencia':'SIN_DESCARGAR','historial':old.get('historial',[]) if old else []}
            events=[]
            if not old:events.append('NUEVO'); status['nuevos']+=1
            elif old['titulo']!=doc['titulo']:events.append('TITULO_MODIFICADO');status['cambios_de_titulo']+=1
            if fetch_documents:
                try:
                    raw_document,_=fetch(item['url']); digest=sha(raw_document)
                    doc['sha256_contenido']=digest;doc['estado_evidencia']='HUELLA_CALCULADA_NO_ARCHIVADA'
                    if old and old.get('sha256_contenido') and old['sha256_contenido']!=digest:
                        events.append('CONTENIDO_MODIFICADO');status['cambios_de_contenido']+=1
                except Exception as exc:
                    doc['estado_evidencia']='DESCARGA_FALLIDA';doc['detalle_error']=str(exc)[:250]
                    status['sin_verificacion_documental']+=1
            else:
                doc['estado_evidencia']='MODO_PRUEBA_SIN_DESCARGA'
                status['sin_verificacion_documental']+=1
            if events:doc['historial']=doc['historial']+[{'fecha_utc':now,'eventos':events,'titulo':doc['titulo'],'sha256_contenido':doc['sha256_contenido']}]
            state['documents'][key]=doc
            candidates.append({k:doc[k] for k in ('codigo','titulo','url','estado_editorial','estado_evidencia','sha256_contenido')} | {'eventos':events})
        status['candidatos_palabra_clave']=len(candidates)
        status['estado']='OK_EXTRACCION_PRELIMINAR'
        state['runs']=(state['runs']+[status])[-90:]
        state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except Exception as exc:
        status['error']=f'{type(exc).__name__}: {exc}'
    (output/'estado.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'candidatos.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# fonzeka® | Monitor DOF 0.2','',f"Consulta: {status['consulta_utc']}",f"Estado: {status['estado']}",
           f"Índice: {url}",f"Enlaces: {status['total_enlaces_detectados']}",f"Candidatos: {len(candidates)}",
           f"Nuevos: {status['nuevos']}",f"Cambios de título: {status['cambios_de_titulo']}",f"Cambios de contenido: {status['cambios_de_contenido']}",'',
           '**Bandeja técnica: no se publica sin revisión humana.**','']
    if status.get('error'):lines+=['ERROR: '+status['error']]
    for item in candidates:
        lines += [f"- [{item['titulo']}]({item['url']}) · {', '.join(item['eventos']) or 'SIN_NOVEDAD'} · {item['estado_evidencia']}"]
    (output/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(status,ensure_ascii=False))
    return 0 if status['estado'].startswith('OK_') else 1

def resolve_date(date_arg='auto', timezone='America/Monterrey', days_back=0, now=None):
    """Usa el calendario de la zona objetivo, no el día UTC del servidor."""
    if days_back < 0 or days_back > 30:
        raise ValueError('--days-back debe estar entre 0 y 30')
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f'Zona horaria desconocida: {timezone}') from exc
    instant = now or dt.datetime.now(dt.timezone.utc)
    if instant.tzinfo is None:
        raise ValueError('now debe tener zona horaria')
    today_local = instant.astimezone(tz).date()
    if date_arg == 'auto':
        day = today_local - dt.timedelta(days=days_back)
    else:
        if days_back:
            raise ValueError('No combines --date con --days-back')
        day = dt.date.fromisoformat(date_arg)
        if day > today_local:
            raise ValueError('No se permiten fechas futuras del calendario local')
    return day.isoformat(), today_local.isoformat()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--date',default='auto',help='YYYY-MM-DD para consultar una edición concreta, o auto para fecha local')
    p.add_argument('--timezone',default='America/Monterrey',help='Zona IANA; por defecto America/Monterrey')
    p.add_argument('--days-back',type=int,default=0,help='Días anteriores a la fecha local (0-30); solo con --date auto')
    p.add_argument('--output',default='salida_monitor');p.add_argument('--state',default='data/monitor_dof_state.json')
    p.add_argument('--html-file');p.add_argument('--no-fetch-documents',action='store_true')
    a=p.parse_args()
    try:
        day,today_local=resolve_date(a.date,a.timezone,a.days_back)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps({'zona_horaria':a.timezone,'fecha_local_actual':today_local,'fecha_indice_solicitada':day,'fecha_explicita':a.date!='auto','dias_retroceso':a.days_back},ensure_ascii=False))
    return run(day,Path(a.output),Path(a.state),a.html_file,not a.no_fetch_documents)
if __name__=='__main__':sys.exit(main())
