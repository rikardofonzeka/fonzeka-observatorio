#!/usr/bin/env python3
"""Monitor exploratorio DOF: no publica ni interpreta normas."""
import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

KEYWORDS = ('electricidad', 'eléctric', 'energia', 'energía', 'generaci', 'transmisión',
            'distribución', 'interconexión', 'cenace', 'comisión nacional de energía',
            'sector eléctrico', 'sener', 'comisión federal de electricidad')
BASE = 'https://www.dof.gob.mx/'

class DOFLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = None; self.items = []
    def handle_starttag(self, tag, attrs):
        if tag != 'a': return
        href = dict(attrs).get('href', '')
        if 'nota_detalle' in href and ('codigo=' in href or 'codigo%3D' in href):
            self.active = [href, []]
    def handle_data(self, data):
        if self.active is not None: self.active[1].append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.active:
            href, chunks = self.active
            title = html.unescape(' '.join(''.join(chunks).split()))
            if title:
                self.items.append({'url': urllib.parse.urljoin(BASE, href), 'titulo': title})
            self.active = None


def detect_from_html(document):
    parser = DOFLinks(); parser.feed(document)
    by_url = {x['url']: x for x in parser.items}
    return list(by_url.values())


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent':'fonzeka-observatorio-monitor/0.1 (documentary research)',
                                               'Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req, timeout=25) as r:
        content = r.read(3_000_000)
        charset = r.headers.get_content_charset() or 'utf-8'
    return content.decode(charset, errors='replace')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--date', default=dt.date.today().isoformat())
    ap.add_argument('--html-file', help='Prueba local reproducible, sin red')
    ap.add_argument('--output', default='salida_monitor')
    args = ap.parse_args()
    day = dt.date.fromisoformat(args.date)
    url = BASE + f'index.php?year={day.year}&month={day.month:02d}&day={day.day:02d}'
    target = Path(args.output); target.mkdir(parents=True, exist_ok=True)
    status = {'fecha_consultada':str(day), 'consulta_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'url_indice':url, 'estado':'ERROR', 'total_enlaces_detectados':0,
              'candidatos_palabra_clave':0, 'advertencia':'Resultados preliminares sujetos a revisión humana.'}
    candidates = []
    try:
        raw = Path(args.html_file).read_text(encoding='utf-8') if args.html_file else fetch(url)
        found = detect_from_html(raw)
        if not found: raise RuntimeError('No se identificaron enlaces de notas del DOF: posible cambio de formato o consulta vacía. No se infiere que no hubo publicaciones.')
        for item in found:
            if any(w in item['titulo'].lower() for w in KEYWORDS):
                item['id_sha256'] = hashlib.sha256(item['url'].encode()).hexdigest()
                item['estado_editorial']='PENDIENTE_DE_REVISION'
                candidates.append(item)
        status.update(estado='OK_EXTRACCION_PRELIMINAR',total_enlaces_detectados=len(found), candidatos_palabra_clave=len(candidates))
    except Exception as exc:
        status['error'] = f'{type(exc).__name__}: {exc}'
    (target/'estado.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (target/'candidatos.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines = ['# fonzeka® | Monitor exploratorio DOF 0.1', '',f"Fecha consultada: {status['fecha_consultada']}",
             f"Resultado: **{status['estado']}**",f"URL de consulta: {url}",
             f"Enlaces detectados: {status['total_enlaces_detectados']}",
             f"Candidatos por título: {status['candidatos_palabra_clave']}",
             '', '**Este reporte es interno, no constituye un análisis regulatorio validado.**','']
    if 'error' in status: lines += ['## Fallo de consulta', status['error'],'']
    else:
        lines += ['## Pendientes de revisión editorial','']
        for i in candidates: lines += [f"- [{i['titulo']}]({i['url']})"]
        if not candidates: lines += ['No se encontraron coincidencias **en los títulos recuperados**. Esto no descarta documentos relevantes.']
    (target/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(status,ensure_ascii=False))
    return 0 if status['estado'].startswith('OK_') else 1

if __name__ == '__main__': sys.exit(main())
