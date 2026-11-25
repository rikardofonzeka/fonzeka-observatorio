"""Distingue ediciones no confirmadas en fin de semana de errores reales."""
import datetime as dt
import json
import sys
from pathlib import Path

INDICE_NO_CONFIRMADO = (
    "El índice no confirma la fecha y edición solicitadas; "
    "no se declara ausencia de publicaciones"
)


def evaluar(payload):
    rows = payload.get("results")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Respuesta del monitor vacía o inválida")
    correctos, pendientes, errores = [], [], []
    fechas = set()
    for row in rows:
        fecha = dt.date.fromisoformat(row["day"])
        if fecha.isoformat() != row["day"] or fecha in fechas:
            raise ValueError("Fecha de consulta inválida o duplicada")
        fechas.add(fecha)
        if row["status"] == "OK":
            correctos.append(row)
        elif (
            row["status"] == "ERROR"
            and fecha.weekday() >= 5
            and row.get("error") == INDICE_NO_CONFIRMADO
        ):
            # No declarar ausencia: la mesa conserva ERROR y vuelve a consultar.
            pendientes.append(row)
        else:
            errores.append(row)
    return correctos, pendientes, errores


def main(path):
    correctos, pendientes, errores = evaluar(json.loads(Path(path).read_text()))
    print(f"Consultas DOF: {len(correctos)+len(pendientes)+len(errores)} · Confirmadas: {len(correctos)} · Fin de semana pendiente: {len(pendientes)} · Errores: {len(errores)}")
    for row in pendientes:
        print(f"::warning::DOF {row['day']}: edición de fin de semana no confirmada. Se mantiene pendiente de nueva consulta.")
    for row in errores:
        print(f"::error::DOF {row['day']}: {row.get('error', 'Consulta no confirmada')}")
    if errores or not correctos:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
