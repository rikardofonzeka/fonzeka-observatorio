"""Integra únicamente la proyección pública de expedientes autorizados."""
import argparse
import json
from pathlib import Path
try:
    from .publico_v2 import CARD, card, detail, fields, require, public_files
except ImportError:
    from publico_v2 import CARD, card, detail, fields, require, public_files

def integrate(root, queue):
    fields(queue, {'schema', 'items', 'blocked'})
    require(queue['schema'] == 2 and isinstance(queue['items'], list) and isinstance(queue['blocked'], list), 'Cola inválida')
    folder = root / 'publicaciones/dof'
    path = folder / 'catalogo.json'
    public_files(root)
    catalog = json.loads(path.read_text(encoding='utf-8'))
    by_code = {row['codigo_dof']: row for row in catalog['expedientes']}
    pending, seen = {}, set()
    for document in queue['items']:
        require(isinstance(document, dict) and CARD.issubset(document), 'Expediente incompleto')
        record = card({key: document[key] for key in CARD})
        detail(document, record)
        code = record['codigo_dof']
        require(code not in seen, 'Código repetido en la cola')
        seen.add(code)
        if code in by_code:
            continue
        require(not (folder / ('expediente-' + code + '.json')).exists(), 'Archivo público huérfano; revisar antes de integrar')
        pending[code] = (record, document)
    for code, (record, document) in pending.items():
        (folder / ('expediente-' + code + '.json')).write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        catalog['expedientes'].append(record)
    if pending:
        catalog['expedientes'].sort(key=lambda row: (row['fecha_dof'], row['codigo_dof']), reverse=True)
        path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    public_files(root)
    return len(pending)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('queue', type=Path)
    args = parser.parse_args()
    data = json.loads(args.queue.read_text(encoding='utf-8'))
    print(f'Expedientes históricos nuevos: {integrate(Path("."), data)}; comprobaciones pendientes: {len(data["blocked"])}')
