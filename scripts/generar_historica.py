#!/usr/bin/env python3
"""Presenta el artefacto histórico local sin alterar sus originales ni el monitor."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / 'monitor-dof/historico/2026-10-29'


def generar():
    originales = DESTINO / 'originales'
    estado = json.loads((originales / 'estado.json').read_text())
    datos = json.loads((originales / 'bandeja.json').read_text())
    enlaces = json.loads((originales / 'enlaces_indice.json').read_text())
    historial = json.loads((ROOT / 'data/monitor_dof_state.json').read_text())
    consulta = next(r for r in historial['runs'] if r['fecha_consultada'] == '2026-10-29')
    if estado != consulta or datos['fecha'] != '2026-10-29':
        raise ValueError('La consulta original no coincide con el historial')
    if len(datos['registros']) != 20 or len(enlaces) != 20:
        raise ValueError('Se esperaban los 20 enlaces originales')
    destacado = next(r for r in datos['registros'] if r['codigo'] == '5802463')
    if destacado['titulo'] != historial['documents']['5802463']['titulo']:
        raise ValueError('Título del destacado inconsistente')
    procedencia_path = DESTINO / 'procedencia.json'
    anterior = json.loads(procedencia_path.read_text()) if procedencia_path.exists() else {}
    procedencia = {
        'fecha_integracion_utc': anterior.get('fecha_integracion_utc', dt.datetime.now(dt.timezone.utc).isoformat()),
        'consulta_original_utc': estado['consulta_utc'],
        'ejecucion_original': 'https://github.com/rikardofonzeka/fonzeka-observatorio/actions/runs/40942408866',
        'evento_original_verificado_api': 'schedule',
        'artefacto': 'dof-consulta-29', 'artefacto_id': 12928365248,
        'origen_recuperacion': 'Carpeta local descomprimida dof-consulta-29',
        'sha256_zip_declarado_github': '4d475e0684667b472a2560b82ad600066d056256f2105338f5cb02ebca7507e7',
        'zip_verificado': False,
        'limitacion': 'Sin ZIP original no se acredita identidad con el paquete de GitHub. No se archivó el texto de los documentos DOF ni se verificó su vigencia.',
        'archivos_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(originales.iterdir()) if p.is_file()},
    }
    procedencia_path.write_text(json.dumps(procedencia, ensure_ascii=False, indent=2) + '\n')
    aviso = ('RECUPERACIÓN HISTÓRICA · 29 de octubre de 2026. '
             '20 enlaces del índice original; 1 candidato por palabras clave. '
             'Esta integración no es una nueva ejecución automática ni sustituye la bandeja vigente.')
    datos.update(tipo_consulta='RECUPERACION_HISTORICA', procedencia='procedencia.json')
    destacado.update(destacado=True, dependencia='SENER — Secretaría de Energía')
    (DESTINO / 'bandeja.json').write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n')
    intro = ('<nav><a href="../../index.html">Monitor DOF</a></nav><p class="aviso">' + aviso + '</p>'
             '<p>Consulta original UTC: ' + estado['consulta_utc'] + '.<br>Integración histórica UTC: ' + procedencia['fecha_integracion_utc'] + '.</p>'
             '<p><a href="procedencia.json">Procedencia y huellas</a> · <a href="bandeja.json">Datos JSON</a> · <a href="bandeja.md">Markdown</a></p>')
    pagina = (originales / 'bandeja.html').read_text()
    if pagina.count('<body>') != 1 or pagina.count('<article>') != 20:
        raise ValueError('Estructura HTML original inesperada')
    pagina = pagina.replace('<body>', '<body>' + intro, 1)
    pagina = pagina.replace('<article>', '<article style="border:2px solid #09599a"><p><strong>DESTACADO · SENER · Código 5802463</strong></p>', 1)
    (DESTINO / 'bandeja.html').write_text(pagina)
    texto = '# Recuperación histórica DOF\n\n' + aviso + '\n\nDestacado: SENER, código 5802463.\n\nConsulta original UTC: ' + estado['consulta_utc'] + '\n\nIntegración histórica UTC: ' + procedencia['fecha_integracion_utc'] + '\n\nProcedencia y limitaciones: [procedencia.json](procedencia.json).\n\n'
    (DESTINO / 'bandeja.md').write_text(texto + (originales / 'bandeja.md').read_text())


if __name__ == '__main__':
    generar()
