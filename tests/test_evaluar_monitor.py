import json
import tempfile
import unittest
from pathlib import Path
from scripts.evaluar_monitor import evaluar, main, INDICE_NO_CONFIRMADO


class MonitorStatusTest(unittest.TestCase):
    def test_weekend_pending_does_not_fail_successful_queries(self):
        rows = [{"day": "2026-11-24", "status": "OK"}] + [
            {"day": day, "status": "ERROR", "error": INDICE_NO_CONFIRMADO}
            for day in ("2026-11-21", "2026-11-22")
        ]
        ok, pending, errors = evaluar({"results": rows})
        self.assertEqual((len(ok), len(pending), len(errors)), (1, 2, 0))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "result.json"
            p.write_text(json.dumps({"results": rows}))
            self.assertEqual(main(p), 0)
    def test_actual_errors_still_fail_including_weekends(self):
        rows = [{"day": "2026-11-24", "status": "OK"},
                {"day": "2026-11-21", "status": "ERROR", "error": "DOF respondió HTTP 503"},
                {"day": "2026-11-23", "status": "ERROR", "error": INDICE_NO_CONFIRMADO}]
        ok, pending, errors = evaluar({"results": rows})
        self.assertEqual((len(ok), len(pending), len(errors)), (1, 0, 2))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "result.json"
            p.write_text(json.dumps({"results": rows}))
            self.assertEqual(main(p), 1)
    def test_extraordinary_weekend_edition_is_not_skipped(self):
        row = {"day": "2026-11-22", "status": "OK", "count": 1}
        self.assertEqual(evaluar({"results": [row]}), ([row], [], []))
    def test_empty_or_duplicate_response_fails(self):
        with self.assertRaises(ValueError):
            evaluar({"results": []})
        row = {"day": "2026-11-24", "status": "OK"}
        with self.assertRaises(ValueError):
            evaluar({"results": [row, row]})
