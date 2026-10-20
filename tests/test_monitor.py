import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from monitor_dof import detect_from_html
class TestParser(unittest.TestCase):
    def test_links(self):
        s = '<a href="nota_detalle.php?codigo=123">Acuerdo de transmisión eléctrica</a><a href="https://example.org">Otro</a>'
        result=detect_from_html(s)
        self.assertEqual(len(result),1)
        self.assertIn('codigo=123',result[0]['url'])
if __name__=='__main__': unittest.main()
