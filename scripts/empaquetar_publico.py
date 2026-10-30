"""Lista explícita de archivos públicos. Nunca empaqueta datos o carpetas privadas."""
import argparse
import json
import shutil
from pathlib import Path


def empaquetar(root,output):
    names=['index.html','expediente-001.html','logo-fonzeka.png','icono.png','monitor-dof/index.html']
    folder=root/'publicaciones/dof';manifest=folder/'aprobaciones.json'
    if manifest.exists():
        names+=['publicaciones/dof/index.html','publicaciones/dof/aprobaciones.json']
        for entry in json.loads(manifest.read_text()):
            name=entry['archivo']
            if Path(name).name!=name or not name.endswith('.html'):
                raise ValueError('Ruta pública no permitida')
            names.append('publicaciones/dof/'+name)
    for name in names:
        source=root/name
        if not source.is_file() or source.is_symlink():raise ValueError('Falta archivo público: '+name)
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();empaquetar(Path('.'),a.output)
