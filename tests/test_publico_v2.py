import json
import tempfile
import unittest
from pathlib import Path
from scripts.publico_v2 import card, detail, public_files
from scripts.integrar_historicos import integrate

def fixture():
    record={'codigo_dof':'1234567','fecha_dof':'2026-11-24','institucion':'SENER','titulo':'Ejemplo ficticio de consulta','tema':'Prueba','resumen':'Contenido de prueba, no publicado.','url_oficial':'https://sidof.segob.gob.mx/notas/1234567'}
    doc={**record,'tipo':'Acuerdo','contexto':'Contexto de prueba','cambio':'Cambio de prueba','alcance':'Alcance de prueba','vigencia':'Por confirmar','actores':['Interesados de prueba'],'analisis':[{'titulo':'Módulo de prueba','texto':'Texto de ejemplo','fuentes':['F1']}],'acciones':[{'interesado':'Interesado de prueba','accion':'Consultar fuente','tipo':'Recomendación','condicion':'','momento':'','evidencia':'','fuentes':['F1']}],'fuentes':[{'id':'F1','titulo':'DOF de prueba','url':record['url_oficial'],'localizador':'Texto de prueba'}],'limites':['Prueba sin efecto documental'],'pdf_oficial':None}
    return record,doc

class PublicContractTest(unittest.TestCase):
    def test_authorized_history_integration_once_and_no_private_fields(self):
        record, doc = fixture()
        with tempfile.TemporaryDirectory() as path:
            root = Path(path); folder = root/'publicaciones/dof'; folder.mkdir(parents=True)
            (folder/'catalogo.json').write_text(json.dumps({'schema':2,'expedientes':[]}))
            queue = {'schema':2,'items':[doc],'blocked':[]}
            self.assertEqual(integrate(root,queue),1)
            self.assertEqual(integrate(root,queue),0)
            with self.assertRaises(ValueError):
                integrate(root,{'schema':2,'items':[{**doc,'owner_id':'privado'}],'blocked':[]})
            with self.assertRaises(ValueError):
                integrate(root,{'schema':2,'items':[doc,doc],'blocked':[]})
            self.assertEqual(json.loads((folder/'catalogo.json').read_text())['expedientes'],[record])
    def test_valid_projection_and_privacy(self):
        record,doc=fixture();card(record);detail(doc,record)
        with self.assertRaises(ValueError):detail({**doc,'control':{'estado':'autorizado'}},record)
        with self.assertRaises(ValueError):card({**record,'version_interna':2})
    def test_rejects_unknown_source_and_correspondence(self):
        record,doc=fixture();other={**record,'url_oficial':'https://sidof.segob.gob.mx/notas/7654321'}
        with self.assertRaises(ValueError):card(other)
        with self.assertRaises(ValueError):detail({**doc,'titulo':'Otro título'},record)
        with self.assertRaises(ValueError):detail({**doc,'pdf_oficial':{'url':'https://example.org/archivo.pdf','tipo':'individual','paginas':''}},record)
    def test_only_listed_expedientes_exposed(self):
        record,doc=fixture()
        with tempfile.TemporaryDirectory() as path:
            root=Path(path);f=root/'publicaciones/dof';f.mkdir(parents=True)
            (f/'catalogo.json').write_text(json.dumps({'schema':2,'expedientes':[record]}));(f/'expediente-1234567.json').write_text(json.dumps(doc));(f/'expediente-7654321.json').write_text('privado')
            names=public_files(root)
            self.assertIn('publicaciones/dof/expediente-1234567.json',names)
            self.assertNotIn('publicaciones/dof/expediente-7654321.json',names)
    def test_production_catalog_excludes_legacy_private_manifest(self):
        root=Path(__file__).resolve().parents[1];payload=json.loads((root/'publicaciones/dof/catalogo.json').read_text());self.assertEqual(payload['schema'],2)
        self.assertNotIn('publicaciones/dof/aprobaciones.json',public_files(root))
