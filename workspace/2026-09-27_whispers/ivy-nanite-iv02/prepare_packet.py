"""Rebuild the pre-implementation packet from existing read-only observations."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
evidence = ROOT / 'evidence'
inventory = json.loads((evidence / 'master-inventory.json').read_text(encoding='utf-8'))
low, high = [-1.0, -0.4, -0.2], [8.1, 2.4, 4.2]
objects = [o for o in inventory['mesh_objects']
           if 'EXTERIOR | OPT01 shared architecture' in o['collections']
           and all(o['max_m'][i] >= low[i] and o['min_m'][i] <= high[i] for i in range(3))]
selection = {'source': inventory['source'], 'blender': inventory['blender'],
             'selection': 'world-space AABB intersects crop; evaluated export is clipped on disposable copies only',
             'crop_min_m': low, 'crop_max_m': high, 'anchor_m': [3.55, 1.8, 0],
             'objects': objects, 'status': 'inspected source candidates; export and visible surface checks NOT RUN'}
(evidence / 'facade-selection.json').write_text(json.dumps(selection, indent=2), encoding='utf-8')
contract = (ROOT / 'asset-contract.md').read_text(encoding='utf-8')
for name in ['prototype-blender-packet.md', 'prototype-unreal-packet.md']:
    path = ROOT / name
    data = path.read_text(encoding='utf-8')
    if '{{ASSET_CONTRACT}}' in data:
        path.write_text(data.replace('{{ASSET_CONTRACT}}', contract.rstrip()), encoding='utf-8')
    elif contract.rstrip() not in data:
        raise RuntimeError(f'Shared contract drift in {name}; revise both packets before publication')
spec = (ROOT / 'README.md').read_text(encoding='utf-8') + '\n\n' + (ROOT / 'continuation.md').read_text(encoding='utf-8')
(ROOT / 'workflow-specification.md').write_text(spec, encoding='utf-8')
print(json.dumps({'selected_objects': len(objects), 'packets_expanded': True, 'geometry_created': False}))
