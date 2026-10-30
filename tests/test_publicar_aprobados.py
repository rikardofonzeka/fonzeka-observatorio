import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.publicar_aprobados import publicar,validar
from scripts.empaquetar_publico import empaquetar
ROOT=Path(__file__).resolve().parents[1]

def fixture():
 t=json.loads((ROOT/'scripts/publication-template.json').read_text())
 d={'id':'DOF-5802463-2026-10-29','codigo':'5802463','fecha_dof':'2026-10-29','titulo':'DOCUMENTO DE PRUEBA — no publicar','url':'https://dof.gob.mx/nota_detalle.php?codigo=5802463&fecha=29/10/2026','dependencia':'SENER','alcance':'Contenido de prueba aislado sin efecto editorial.','version':'2','editorial':{k:'Texto de prueba del apartado editorial. No constituye análisis real.' for k in ['resumen','cambios','antecedentes','transitorios','implicaciones','evidencia']},'plantilla_sha256':hashlib.sha256(t.encode()).hexdigest()}
 h=hashlib.sha256(json.dumps(d,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 return {'review_key':d['id']+':'+h,'content_hash':h,'document':d,'approved_at':'2026-10-30T20:00:00.000Z','sent_at':'2026-10-30T20:01:00.000Z'}

class PublicationTest(unittest.TestCase):
 def test_changed_content_rejected(self):
  i=fixture();i['document']['titulo']='Otro título';self.assertRaises(ValueError,validar,i)
 def test_nonofficial_source_rejected(self):
  i=fixture();i['document']['url']='https://example.org';self.assertRaises(ValueError,validar,i)
 def test_template_change_rejected(self):
  i=fixture();i['document']['plantilla_sha256']='0'*64;self.assertRaises(ValueError,validar,i)
 def test_incomplete_analysis_rejected(self):
  i=fixture();i['document']['editorial']['transitorios']='';self.assertRaises(ValueError,validar,i)
 def test_cne_structure_and_existing_publication_preserved(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);root.joinpath('index.html').write_text((ROOT/'index.html').read_text());root.joinpath('expediente-001.html').write_bytes((ROOT/'expediente-001.html').read_bytes())
   original=root.joinpath('expediente-001.html').read_bytes();i=fixture();ack=root/'ack.json'
   publicar({'schema':1,'items':[i]},root,ack)
   p=root/'publicaciones/dof/expediente-5802463-v2.html';s=p.read_text()
   for heading in ['¿Qué cambia?','Antecedentes verificables','Transitorios que requieren atención','Implicaciones evaluadas por fonzeka®','Evidencia y estado de revisión']:self.assertIn(heading,s)
   self.assertEqual(original,root.joinpath('expediente-001.html').read_bytes())
   self.assertIn('expediente-001.html',root.joinpath('index.html').read_text())
   publicar({'schema':1,'items':[i]},root,ack)
   self.assertEqual(root.joinpath('index.html').read_text().count('FONZEKA_APROBADOS_INICIO'),1)
 def test_packager_excludes_private_files(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)/'source';out=Path(folder)/'out';root.mkdir()
   for name in ['index.html','expediente-001.html','logo-fonzeka.png','icono.png','monitor-dof/index.html']:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('publico')
   (root/'datos-privados.json').write_text('privado');empaquetar(root,out)
   self.assertFalse((out/'datos-privados.json').exists())

if __name__=='__main__':unittest.main()
