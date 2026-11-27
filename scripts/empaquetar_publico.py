"""Lista explícita de archivos públicos. Nunca empaqueta datos o carpetas privadas."""
import argparse
import json
import shutil
from pathlib import Path
try:
    from .publico_v2 import public_files
except ImportError:
    from publico_v2 import public_files


def empaquetar(root, output):
    names = [
        'index.html',
        'observatorio.html',
        'expediente-001.html',
        'logo-fonzeka.png',
        'fonzeka-vista-previa-linkedin.png',
        'observatorio-vista-previa.png',
        'icono.png',
        'cronologia-electrica-2024-2026.pdf',
        'proyecto-oasis.pdf',
        'chicoasen-ii/chicoasen-ii-expediente.pdf',
        'publicaciones/panorama-social-alc-2026.html',
        'monitor-dof/index.html',
        'proyectos-mixtos/index.html',
        'proyectos-mixtos/data/proyectos.json',
        'proyectos-mixtos/data/proyectos.csv',
        'proyectos-mixtos/data/fuentes.json',
        'proyectos-mixtos/data/fuentes.csv',
        'proyectos-mixtos/data/plan-expansion-2026-2030.json',
        'proyectos-mixtos/data/plan-expansion-2026-2030.csv',
    ]

    names += public_files(root)

    for name in names:
        source = root / name
        if not source.is_file() or source.is_symlink():
            raise ValueError('Falta archivo público: ' + name)
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    empaquetar(Path('.'), a.output)
