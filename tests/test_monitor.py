import tempfile
import unittest
from pathlib import Path
from scripts.monitor_dof import extract_links,run

HTML='''<html><a href="/nota_detalle.php?codigo=123&fecha=20/10/2026">Código de Conducta CFE</a><a href="/nota_detalle.php?codigo=999">Otro tema</a></html>'''
class MonitorTest(unittest.TestCase):
    def test_extract(self):
        x=extract_links(HTML)
        self.assertEqual(len(x),2)
        self.assertEqual(x[0]['codigo'],'123')
    def test_persistence_without_false_novelty(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); html=base/'indice.html';html.write_text(HTML)
            state=base/'data.json'
            self.assertEqual(run('2026-10-20',base/'r1',state,html,False),0)
            self.assertEqual(run('2026-10-20',base/'r2',state,html,False),0)
            import json
            s=json.loads((base/'r2'/'estado.json').read_text())
            self.assertEqual(s['nuevos'],0)
            self.assertEqual(s['candidatos_palabra_clave'],1)
            self.assertEqual(len(json.loads(state.read_text())['documents']),1)
if __name__=='__main__':unittest.main()
