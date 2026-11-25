"""Contrato exclusivo de la salida pública. No importa ni autoriza expedientes privados."""
import datetime as dt
import json
import re
from urllib.parse import urlparse, parse_qs

CARD = {'codigo_dof','fecha_dof','institucion','titulo','tema','resumen','url_oficial'}
DETAIL = CARD | {'tipo','contexto','cambio','alcance','vigencia','actores','analisis','acciones','fuentes','limites','pdf_oficial'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def fields(value, expected):
    require(isinstance(value, dict) and set(value) == expected, 'Campos públicos inesperados o incompletos')

def string(value, allow_empty=False):
    return isinstance(value, str) and len(value) <= 30000 and (allow_empty or bool(value.strip()))

def array(value):
    require(isinstance(value, list) and len(value) <= 300, 'Lista pública inválida')
    return value

def official(url):
    if not string(url): return False
    try:
        u=urlparse(url); host=u.hostname or ''
        return u.scheme=='https' and not u.username and not u.password and not u.port and (host=='gob.mx' or host.endswith('.gob.mx') or host=='cfe.mx' or host.endswith('.cfe.mx'))
    except ValueError: return False

def note(url, code):
    if not official(url): return False
    u=urlparse(url)
    return (u.hostname=='sidof.segob.gob.mx' and u.path in (f'/notas/{code}',f'/notas/docFuente/{code}')) or (u.hostname=='dof.gob.mx' and u.path=='/nota_detalle.php' and parse_qs(u.query).get('codigo')==[code])

def card(data):
    fields(data,CARD)
    require(all(string(data[k]) for k in CARD), 'Dato público incompleto')
    require(re.fullmatch(r'\d{7}', data['codigo_dof']) is not None, 'Código DOF inválido')
    require(dt.date.fromisoformat(data['fecha_dof']).isoformat()==data['fecha_dof'], 'Fecha DOF inválida')
    require(note(data['url_oficial'],data['codigo_dof']), 'Fuente DOF incongruente')
    return data

def detail(data, record):
    fields(data,DETAIL)
    require(card({k:data[k] for k in CARD})==record, 'El expediente no coincide con el catálogo')
    require(all(string(data[k]) for k in ('tipo','contexto','cambio','alcance','vigencia')), 'Contenido incompleto')
    for k in ('actores','limites'):
        require(all(string(x) for x in array(data[k])), 'Lista de contenido inválida')
    sources={}
    for f in array(data['fuentes']):
        fields(f,{'id','titulo','url','localizador'})
        require(re.fullmatch(r'F\d+',f['id']) is not None and f['id'] not in sources and string(f['titulo']) and official(f['url']) and string(f['localizador']), 'Fuente pública inválida')
        sources[f['id']]=f
    require(any(note(f['url'],data['codigo_dof']) for f in sources.values()),'Falta la fuente primaria del expediente')
    def refs(values):
        require(bool(array(values)) and all(isinstance(x,str) and x in sources for x in values),'Referencia pública incompleta')
    for m in array(data['analisis']):
        fields(m,{'titulo','texto','fuentes'}); require(string(m['titulo']) and string(m['texto']),'Módulo público incompleto'); refs(m['fuentes'])
    for a in array(data['acciones']):
        fields(a,{'interesado','accion','tipo','condicion','momento','evidencia','fuentes'})
        require(all(string(a[k],k in ('condicion','momento','evidencia')) for k in ('interesado','accion','condicion','momento','evidencia')) and a['tipo'] in ('Obligación','Recomendación','Verificación'),'Acción pública inválida'); refs(a['fuentes'])
    pdf=data['pdf_oficial']
    if pdf is not None:
        fields(pdf,{'url','tipo','paginas'}); require(official(pdf['url']) and pdf['tipo'] in ('individual','edicion') and string(pdf['paginas'],True),'PDF oficial inválido')
        u=urlparse(pdf['url']); require(u.path.endswith('.pdf') or u.path.startswith('/notas/getNewsletter/') or u.path=='/abrirPDF.php','El enlace no identifica un PDF oficial')

def public_files(root):
    folder=root/'publicaciones/dof'; path=folder/'catalogo.json'
    require(path.is_file() and not path.is_symlink(),'Falta el catálogo público')
    payload=json.loads(path.read_text(encoding='utf-8'));fields(payload,{'schema','expedientes'});require(payload['schema']==2,'Esquema público incorrecto')
    records=payload['expedientes'];require(isinstance(records,list),'Catálogo inválido')
    codes=set(); names=['publicaciones/dof/'+n for n in ('index.html','catalogo.json','catalogo.js','catalogo.css','expediente.html','expediente.js')]
    for row in records:
        card(row);code=row['codigo_dof'];require(code not in codes,'Código DOF duplicado');codes.add(code)
        name='expediente-'+code+'.json';p=folder/name
        require(p.is_file() and not p.is_symlink(),'Expediente público ausente')
        detail(json.loads(p.read_text(encoding='utf-8')),row);names.append('publicaciones/dof/'+name)
    return names
