"""Read-only inventory. Run in a separate background Blender; never saves a blend."""
import bpy
import json
import pathlib
from mathutils import Vector

out = pathlib.Path(__file__).parent / 'evidence'
out.mkdir(exist_ok=True)
rows = []
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [min(c[i] for c in corners) for i in range(3)]
    hi = [max(c[i] for c in corners) for i in range(3)]
    rows.append({'name': obj.name, 'collections': [c.name for c in obj.users_collection],
                 'min_m': lo, 'max_m': hi, 'materials': [s.material.name if s.material else None for s in obj.material_slots]})
result = {'source': bpy.data.filepath, 'blender': bpy.app.version_string,
          'object_count': len(bpy.data.objects), 'mesh_objects': rows,
          'saved': False, 'purpose': 'Source selection only; no geometry or source mutation'}
(out / 'master-inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('IV02_READ_ONLY_INVENTORY', len(rows), str(out / 'master-inventory.json'))
