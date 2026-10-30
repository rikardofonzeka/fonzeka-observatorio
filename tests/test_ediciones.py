import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.monitor_dof import collect_editions, EditionLinks, run
from scripts.validar_publicacion import validar
from scripts.generar_bandeja import generar

ROOT = Path(__file__).resolve().parents[1]
DAY = dt.date(2026, 10, 30)


def page(edition, other='', title='Documento', code='123'):
    return (f'<a href="nota_to_pdf.php?fecha=30/10/2026&edicion={edition}">PDF</a>'
            f'<a href="index.php?year=2026&month=10&day=30&edicion={other}">Otra</a>'
            f'<a href="nota_detalle.php?codigo={code}&fecha=30/10/2026">{title}</a>')


class EditionTest(unittest.TestCase):
    def test_archived_mat_and_ves_are_combined(self):
        evidence = ROOT / 'data/integraciones_dof/2026-10-30'
        def fetch(url):
            name = 'fonzeka-indice-30-mat.html' if 'edicion=MAT' in url else 'fonzeka-indice-30.html'
            raw = (evidence / name).read_bytes()
            return raw, raw.decode()
        with tempfile.TemporaryDirectory() as d, patch('scripts.monitor_dof.fetch', side_effect=fetch) as request:
            records, sources, complete = collect_editions(DAY, Path(d))
            self.assertTrue(complete)
            self.assertEqual(len(records), 19)
            self.assertEqual({s['edicion']: s['enlaces'] for s in sources}, {'VES': 4, 'MAT': 15})
            self.assertEqual(request.call_count, 2)
            self.assertTrue(all(r['procedencia'] for r in records))
            self.assertTrue((Path(d) / 'indice_MAT.html').exists())

    def test_duplicate_document_preserves_both_sources(self):
        def fetch(url):
            raw = page('MAT', 'VES') if 'edicion=VES' not in url else page('VES', 'MAT')
            return raw.encode(), raw
        with tempfile.TemporaryDirectory() as d, patch('scripts.monitor_dof.fetch', side_effect=fetch):
            records, _, _ = collect_editions(DAY, Path(d))
            self.assertEqual(len(records), 1)
            self.assertEqual(len(records[0]['procedencia']), 2)

    def test_failed_alternate_does_not_persist_partial_history(self):
        raw = page('MAT', 'VES')
        with tempfile.TemporaryDirectory() as d, patch('scripts.monitor_dof.fetch', side_effect=[(raw.encode(), raw), OSError('unavailable')]):
            base = Path(d)
            state = base / 'state.json'
            self.assertEqual(run(str(DAY), base / 'output', state, fetch_documents=False), 1)
            self.assertFalse(state.exists())
            status = json.loads((base / 'output/estado.json').read_text())
            self.assertEqual(status['estado'], 'ERROR')

    def test_redirect_to_other_edition_is_rejected(self):
        raw = page('MAT', 'VES')
        with tempfile.TemporaryDirectory() as d, patch('scripts.monitor_dof.fetch', return_value=(raw.encode(), raw)):
            with self.assertRaisesRegex(RuntimeError, 'no coincide'):
                collect_editions(DAY, Path(d))

    def test_discovery_does_not_follow_external_or_other_date(self):
        parser = EditionLinks(DAY)
        parser.feed('<a href="https://example.com/index.php?year=2026&month=10&day=30&edicion=VES">bad</a>'
                    '<a href="index.php?year=2026&month=10&day=29&edicion=VES">old</a>')
        self.assertEqual(parser.editions, set())

    def test_unidentified_coverage_blocks_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'estado.json').write_text(json.dumps({'estado':'OK_EXTRACCION_PRELIMINAR','tipo_consulta':'EDICION_DEL_DIA','cobertura_ediciones_enlazadas':False}))
            self.assertEqual(validar(p), (False, 'Cobertura de ediciones no comprobada'))

    def test_generated_tray_preserves_provenance_and_validator_rejects_tampering(self):
        class Clock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 30, 12, tzinfo=tz)
        raw = page('MAT')
        with tempfile.TemporaryDirectory() as d, patch('scripts.monitor_dof.fetch', return_value=(raw.encode(), raw)), patch('scripts.validar_publicacion.dt.datetime', Clock):
            base = Path(d)
            out = base / 'output'
            self.assertEqual(run(str(DAY), out, base / 'state.json', fetch_documents=False), 0)
            generar(out)
            self.assertTrue(validar(out)[0])
            tray = json.loads((out / 'bandeja.json').read_text())
            self.assertEqual(tray['registros'][0]['procedencia'][0]['edicion'], 'MAT')
            self.assertIn('Edición: MAT', (out / 'bandeja.html').read_text())
            tray['indices_consultados'] = []
            (out / 'bandeja.json').write_text(json.dumps(tray))
            self.assertFalse(validar(out)[0])
