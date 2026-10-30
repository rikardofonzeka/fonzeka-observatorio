
import argparse
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def validar(carpeta):
    carpeta = Path(carpeta)
    estado_path = carpeta / "estado.json"

    if not estado_path.is_file():
        return False, "Falta estado.json"

    try:
        estado = json.loads(
            estado_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return False, "estado.json no es válido"

    if not isinstance(estado, dict):
        return False, "Estructura de estado incorrecta"

    if estado.get("estado") != "OK_EXTRACCION_PRELIMINAR":
        return False, "Consulta sin estado satisfactorio"

    if estado.get("tipo_consulta") != "EDICION_DEL_DIA":
        return False, "Consulta anticipada o no ordinaria"

    hoy = dt.datetime.now(
        ZoneInfo("America/Monterrey")
    ).date().isoformat()

    if estado.get("fecha_consultada") != hoy:
        return False, "La consulta no corresponde al día vigente"

    for nombre in (
        "bandeja.html",
        "bandeja.json",
        "bandeja.md",
    ):
        archivo = carpeta / nombre

        if not archivo.is_file() or archivo.stat().st_size == 0:
            return False, f"Archivo faltante o vacío: {nombre}"

    try:
        bandeja = json.loads(
            (carpeta / "bandeja.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError):
        return False, "bandeja.json no es válido"

    if not isinstance(bandeja, dict):
        return False, "Estructura de bandeja incorrecta"

    if bandeja.get("fecha") != hoy:
        return False, "La fecha de la bandeja no coincide"

    if bandeja.get("estado") != "OK_EXTRACCION_PRELIMINAR":
        return False, "Estado de bandeja incorrecto"

    if not isinstance(bandeja.get("registros"), list):
        return False, "Registros de bandeja incorrectos"

    return True, "PUBLICACION_AUTORIZADA_TECNICAMENTE"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    valido, mensaje = validar(args.input)
    print(mensaje)

    raise SystemExit(0 if valido else 1)