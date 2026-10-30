
#!/usr/bin/env python3
"""fonzeka®: bandeja orientativa; no acredita publicación ni vigencia jurídica."""
import argparse
import html
import json
from pathlib import Path

PRIORIDAD_ALTA = (
    'tarif', 'mercado eléctrico', 'mercado electrico', 'interconex',
    'transmis', 'distribuc', 'generaci', 'cenace', 'sistema eléctrico',
    'sistema electrico', 'código de red', 'codigo de red',
    'comisión nacional de energía', 'comision nacional de energia',
    'permisos de generación', 'permiso de generación', 'almacenamiento',
)
PRIORIDAD_MEDIA = (
    'electric', 'energía', 'energia', 'sener', 'cfe',
    'comisión federal de electricidad', 'comision federal de electricidad',
    'gas natural', 'hidrocarb', 'subestaci',
)
INSTITUCIONAL = (
    'código de ética', 'codigo de etica', 'código de conducta',
    'codigo de conducta', 'manual de organización', 'manual de organizacion',
    'estatuto orgánico', 'estatuto organico',
)

def prioridad(titulo):
    t = titulo.casefold()
    if any(x in t for x in INSTITUCIONAL):
        return 'INSTITUCIONAL', 'Gobernanza; revisar alcance antes de priorizar'
    if any(x in t for x in PRIORIDAD_ALTA):
        return 'ALTA', 'Posible impacto técnico o regulatorio; revisar documento'
    if any(x in t for x in PRIORIDAD_MEDIA):
        return 'MEDIA', 'Relación sectorial; verificar alcance'
    return 'SIN_CLASIFICAR', 'No se infiere relevancia del título'

def leer_json(ruta, default):
    if not ruta.exists():
        return default
    return json.loads(ruta.read_text(encoding='utf-8'))

def generar(carpeta):
    estado = leer_json(carpeta / 'estado.json', {})
    candidatos = leer_json(carpeta / 'candidatos.json', [])
    enlaces = leer_json(carpeta / 'enlaces_indice.json', [])
    if not isinstance(candidatos, list) or not isinstance(enlaces, list):
        raise ValueError('Formato incorrecto de candidatos o enlaces')
    mapa = {str(x.get('codigo')): x for x in candidatos if isinstance(x, dict)}
    registros = []
    for item in enlaces:
        if not isinstance(item, dict):
            continue
        codigo = str(item.get('codigo', ''))
        candidato = mapa.get(codigo, {})
        titulo = str(item.get('titulo', '')).strip()
        url = str(item.get('url', '')).strip()
        if not titulo or not url.startswith('https://dof.gob.mx/'):
            continue
        nivel, motivo = prioridad(titulo)
        registros.append({
            'codigo': codigo, 'titulo': titulo, 'url': url,
            'prioridad_orientativa': nivel, 'motivo': motivo,
            'seleccionado_por_palabras_clave': bool(candidato),
            'estado_evidencia': candidato.get('estado_evidencia', 'NO_VERIFICADO'),
            'procedencia': item.get('procedencia', []),
        })
    orden = {'ALTA': 0, 'MEDIA': 1, 'INSTITUCIONAL': 2, 'SIN_CLASIFICAR': 3}
    registros.sort(key=lambda r: (orden[r['prioridad_orientativa']], r['titulo'].casefold()))
    titulo_pagina = 'fonzeka® | Bandeja documental DOF'
    aviso = ('DETECCIÓN ANTICIPADA — NO CONFIRMA PUBLICACIÓN OFICIAL' if
             estado.get('tipo_consulta') == 'AVANCE_NO_OFICIAL' else
             'EXTRACCIÓN PRELIMINAR — PENDIENTE DE REVISIÓN')
    fecha = estado.get('fecha_consultada', 'Sin fecha')
    lines = [f'# {titulo_pagina}', '', f'**Fecha consultada:** {fecha}',
             f'**Estado:** {estado.get("estado", "SIN_ESTADO")}',
             f'**{aviso}**', '', f'Enlaces listados: {len(registros)} · '
             f'Candidatos por palabras clave: {len(candidatos)}', '',
             'La clasificación es orientativa a partir del título. '
             'No sustituye la lectura del documento ni la validación jurídica.', '']
    for r in registros:
        ediciones = ', '.join(str(f.get('edicion', 'SIN_IDENTIFICAR')) for f in r['procedencia'])
        lines.append(f'- **{r["prioridad_orientativa"]}** · '
                     f'[{r["titulo"]}]({r["url"]}) · '
                     f'código {r["codigo"]} · {r["motivo"]}' +
                     (f' · Edición: {ediciones}' if ediciones else ''))
    if not registros:
        lines.append('No se identificaron enlaces reconocibles. No implica ausencia de publicaciones.')
    (carpeta / 'bandeja.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (carpeta / 'bandeja.json').write_text(
        json.dumps({'fecha': fecha, 'estado': estado.get('estado'), 'aviso': aviso,
                    'indices_consultados': estado.get('indices_consultados', []),
                    'cobertura_ediciones_enlazadas': estado.get('cobertura_ediciones_enlazadas', False),
                    'registros': registros}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    filas = []
    for r in registros:
        u = html.escape(r['url'], quote=True)
        filas.append('<article><span class="nivel">'+html.escape(r['prioridad_orientativa'])+
                     '</span><h2>'+html.escape(r['titulo'])+'</h2><p>'+html.escape(r['motivo'])+
                     '</p><a href="'+u+'" target="_blank" rel="noopener noreferrer">Abrir en DOF ↗</a>'+
                     '<small>Código '+html.escape(r['codigo'])+'</small></article>')
        if r['procedencia']:
            ediciones = ', '.join(str(f.get('edicion', 'SIN_IDENTIFICAR')) for f in r['procedencia'])
            filas[-1] = filas[-1].replace('</article>', '<small>Edición: '+html.escape(ediciones)+'</small></article>')
    cuerpo = '\n'.join(filas) if filas else '<p>No hay enlaces reconocibles para esta fecha.</p>'
    pagina = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              '<title>'+titulo_pagina+'</title><style>'
              'body{font-family:system-ui,Arial,sans-serif;background:#f7f8fa;color:#182331;'
              'max-width:820px;margin:0 auto;padding:24px}h1{font-size:1.7rem}h2{font-size:1.06rem;line-height:1.4}'
              'article{background:white;border:1px solid #d9dfe6;border-radius:12px;padding:17px;margin:13px 0}'
              'a{color:#09599a;font-weight:650}small{display:block;margin-top:12px;color:#64748b}'
              '.nivel{color:#ad4800;font-size:.78rem;font-weight:800;letter-spacing:.05em}'
              '.aviso{border-left:4px solid #e57820;padding:12px;background:#fff2e5}'
              '</style></head><body><h1>fonzeka® | Bandeja documental DOF</h1>'
              '<p>Fecha consultada: <strong>'+html.escape(str(fecha))+'</strong></p>'
              '<p class="aviso">'+html.escape(aviso)+'</p>'
              '<p>Prioridades orientativas basadas en títulos. No hay aprobación editorial ni certificación de vigencia.</p>'
              +cuerpo+'</body></html>')
    (carpeta / 'bandeja.html').write_text(pagina, encoding='utf-8')
    print(json.dumps({'bandeja': 'generada', 'fecha': fecha, 'registros': len(registros)}, ensure_ascii=False))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='salida_monitor')
    args = p.parse_args()
    generar(Path(args.input))
