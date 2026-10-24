"""IV02 S5: clean factory-startup FBX round trip. Reimports every export FBX into an
empty scene (no .blend opened, nothing saved) and compares against the export data.

  blender --factory-startup --disable-autoexec -b --python roundtrip.py -- <ivy_IV02 root>
"""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from collections import Counter

ROOT = Path(sys.argv[sys.argv.index('--') + 1])
EXP = ROOT / 'exports'; QA = ROOT / 'qa'; REN = ROOT / 'renders'
build = json.loads((QA / 'ivy_build.json').read_text(encoding='utf-8'))
facade = json.loads((QA / 'facade_export.json').read_text(encoding='utf-8'))
ref = json.loads((QA / 'ivy_export_reference.json').read_text(encoding='utf-8'))

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
IMPORT = dict(use_custom_normals=True, use_image_search=False, use_anim=False, global_scale=1.0,
              bake_space_transform=False, axis_forward='-Y', axis_up='Z', colors_type='LINEAR')

def imp(fn):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(EXP / fn), **IMPORT)
    objs = [o for o in bpy.data.objects if o not in before]
    return objs

def world_bounds(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    return lo, hi

rep = {'blender': bpy.app.version_string, 'process': 'factory-startup, empty scene, no blend opened', 'import_settings': IMPORT}

# ---------------------------------------------------------------- ivy
ivy = imp('SM_Ivy_WallPatch_Prototype.fbx')
meshes = [o for o in ivy if o.type == 'MESH']
assert len(meshes) == 1, [o.name for o in ivy]
ob = meshes[0]; me = ob.data
M = ob.matrix_world
lo, hi = world_bounds(ob)
e = build['export_mesh']
tol_bounds = [max(0.01, 0.02 * (e['tight_max_m'][i] - e['tight_min_m'][i])) for i in range(3)]
bdev = [max(abs(lo[i] - e['tight_min_m'][i]), abs(hi[i] - e['tight_max_m'][i])) for i in range(3)]
# per-corner comparison in loop order; fall back to centroid matching if order differs
nl = len(me.loops)
pos = [M @ me.vertices[l.vertex_index].co for l in me.loops]
order_ok = nl == len(ref['positions']) and all((pos[i] - Vector(ref['positions'][i])).length < 1e-4 for i in range(0, nl, max(1, nl // 2000)))
mapping = list(range(nl))
if not order_ok:
    key = {}
    for i, p in enumerate(ref['positions']):
        key.setdefault(tuple(round(c, 4) for c in p), []).append(i)
    mapping = []
    for p in pos:
        k = tuple(round(c, 4) for c in p)
        mapping.append(key[k].pop() if key.get(k) else None)
M3 = M.to_3x3().normalized()
nrm = [(M3 @ Vector(n.vector)).normalized() for n in me.corner_normals]
uvl = me.uv_layers[0] if me.uv_layers else None
col = me.color_attributes[0] if me.color_attributes else None
cd = [0.0] * (nl * 4)
if col and col.domain == 'CORNER':
    col.data.foreach_get('color', cd)
elif col:
    pv = [0.0] * (len(me.vertices) * 4); col.data.foreach_get('color', pv)
    for i, l in enumerate(me.loops):
        cd[i * 4:i * 4 + 4] = pv[l.vertex_index * 4:l.vertex_index * 4 + 4]
dp = du = dc = 0.0; dn = 0.0; n_cmp = 0; worst = {}
for i in range(nl):
    j = mapping[i]
    if j is None:
        continue
    n_cmp += 1
    dp = max(dp, (pos[i] - Vector(ref['positions'][j])).length)
    dn = max(dn, math.degrees(nrm[i].angle(Vector(ref['normals'][j]), 0)))
    if uvl:
        du = max(du, (Vector(uvl.data[i].uv) - Vector(ref['uv'][j])).length)
    dc = max(dc, max(abs(cd[i * 4 + k] - ref['color'][j][k]) for k in range(4)))
# FBX/Unreal split vertices wherever a corner attribute differs between faces sharing a vertex
split_keys = set()
for i, l in enumerate(me.loops):
    split_keys.add((l.vertex_index, tuple(round(c, 5) for c in nrm[i]),
                    tuple(round(c, 5) for c in uvl.data[i].uv) if uvl else None,
                    tuple(round(c, 4) for c in cd[i * 4:i * 4 + 4])))
chan_stats = {}
for k, c in enumerate('RGBA'):
    v = sorted(cd[k::4]); chan_stats[c] = {'min': v[0], 'median': v[len(v) // 2], 'max': v[-1], 'mean': sum(v) / len(v)}
rep['ivy'] = {
    'fbx_sha256': hashlib.sha256((EXP / 'SM_Ivy_WallPatch_Prototype.fbx').read_bytes()).hexdigest(),
    'imported_objects': [o.name for o in ivy], 'object_matrix_world': [list(r) for r in M],
    'object_origin_m': list(M.translation),
    'pivot_deviation_cm': (M.translation - Vector((0, 0, 0))).length * 100,
    'triangles': {'export': e['triangles'], 'reimport': len(me.polygons), 'equal': e['triangles'] == len(me.polygons),
                  'all_triangles': all(len(p.vertices) == 3 for p in me.polygons)},
    'vertices': {'export': e['vertices'], 'reimport': len(me.vertices), 'equal': e['vertices'] == len(me.vertices),
                 'unique_corner_attribute_vertices_after_split': len(split_keys),
                 'note': 'FBX stores control points (= Blender vertices) plus per-corner normals/UV/colour; an engine splits a vertex wherever corner data differ'},
    'corners': {'reimport': nl, 'export': len(ref['positions']), 'loop_order_preserved': order_ok, 'compared': n_cmp},
    'tight_bounds_reimport_m': [lo, hi], 'tight_bounds_export_m': [e['tight_min_m'], e['tight_max_m']],
    'bounds_max_deviation_cm': [d * 100 for d in bdev], 'bounds_tolerance_cm': [t * 100 for t in tol_bounds],
    'bounds_within_tolerance': all(bdev[i] <= tol_bounds[i] for i in range(3)),
    'max_position_error_m': dp, 'max_normal_error_deg': dn, 'max_uv_error': du, 'max_color_error': dc,
    'tolerances': {'position_m': 1e-4, 'normal_deg': 1.0, 'uv': 1e-5, 'color': 1.0 / 255},
    'pass_attributes': dp <= 1e-4 and dn <= 1.0 and du <= 1e-5 and dc <= 1.0 / 255,
    'uv_layers': [l.name for l in me.uv_layers],
    'color_attributes': [(a.name, a.domain, a.data_type) for a in me.color_attributes],
    'color_channel_stats': chan_stats,
    'material_slots': [s.material.name if s.material else None for s in ob.material_slots],
}

# ---------------------------------------------------------------- axis markers
mk = imp('IV02_AxisMarkers.fbx')
exp_m = build['axis_markers_m']
mrows = {}
for o in mk:
    base = o.name.split('.')[0]
    c = sum((o.matrix_world @ v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
    want = Vector(exp_m.get(base, (float('nan'),) * 3))
    mrows[base] = {'centroid_m': list(c), 'expected_m': list(want), 'error_cm': (c - want).length * 100}
rep['axis_markers'] = {'markers': mrows, 'max_error_cm': max(r['error_cm'] for r in mrows.values()),
                       'within_0p1cm': all(r['error_cm'] <= 0.1 for r in mrows.values()),
                       'basis': 'Blender +X out of wall, +Y width, +Z up; Unreal expectation (X, -Y, Z) x 100 cm'}

# ---------------------------------------------------------------- facade fixture
fx = imp('SM_IV02_FacadeBay.fbx')
fob = [o for o in fx if o.type == 'MESH'][0]
flo, fhi = world_bounds(fob)
f = facade['fixture']
fdev = [max(abs(flo[i] - f['tight_min_m'][i]), abs(fhi[i] - f['tight_max_m'][i])) for i in range(3)]
rep['facade'] = {'fbx_sha256': hashlib.sha256((EXP / 'SM_IV02_FacadeBay.fbx').read_bytes()).hexdigest(),
                 'triangles': {'export': f['triangles'], 'reimport': len(fob.data.polygons), 'equal': f['triangles'] == len(fob.data.polygons)},
                 'vertices': {'export': f['vertices'], 'reimport': len(fob.data.vertices)},
                 'material_slots_reimport': [s.material.name if s.material else None for s in fob.material_slots],
                 'material_slots_export': f['material_slots_in_order'],
                 'slot_order_preserved': [s.material.name if s.material else None for s in fob.material_slots] == f['material_slots_in_order'],
                 'uv_layers': [l.name for l in fob.data.uv_layers],
                 'tight_bounds_reimport_m': [flo, fhi], 'bounds_max_deviation_cm': [d * 100 for d in fdev],
                 'bounds_within_1cm': all(d <= 0.01 for d in fdev),
                 'origin_m': list(fob.matrix_world.translation)}

# ---------------------------------------------------------------- render the actual imported ivy mesh
for o in mk + fx:
    o.hide_render = True
mat = ob.material_slots[0].material if ob.material_slots else bpy.data.materials.new('IvyAtlas')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
for fn, sock, data in (('T_Ivy_Atlas_BaseColor.png', 'Base Color', False), ('T_Ivy_Atlas_Roughness.png', 'Roughness', True), ('T_Ivy_Atlas_Normal.png', 'Normal', True)):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(ROOT / 'textures' / fn))
    if data:
        t.image.colorspace_settings.name = 'Non-Color'
    if sock == 'Normal':
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        nt.links.new(t.outputs['Color'], bsdf.inputs[sock])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 64
sc.render.resolution_x, sc.render.resolution_y = 1000, 1600
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bgn = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bgn.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bgn.inputs['Strength'].default_value = 0.6
sd = bpy.data.lights.new('S', 'SUN'); sd.energy = 4; so = bpy.data.objects.new('S', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-35), math.radians(60))
pm = bpy.data.meshes.new('P'); pm.from_pydata([(0, -0.9, -0.1), (0, 0.9, -0.1), (0, 0.9, 2.2), (0, -0.9, 2.2)], [], [(0, 1, 2, 3)])
pl = bpy.data.objects.new('Backdrop', pm); sc.collection.objects.link(pl)
cd_ = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd_); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, tgt, lens, res):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd_.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(REN / name); bpy.ops.render.render(write_still=True)
    return f'renders/{name}'
rep['renders'] = [shot('IV02_roundtrip_front.png', (2.6, 0, 1.0), (0, 0, 1.0), 40, (1000, 1600)),
                  shot('IV02_roundtrip_oblique.png', (0.65, 0.75, 1.35), (0.02, 0, 1.05), 35, (1200, 1200))]
rep['render_note'] = 'actual reimported FBX mesh; atlas textures assigned from textures/ because the FBX stores stripped texture paths'
rep['saved_blend'] = False
(QA / 'fbx_roundtrip.json').write_text(json.dumps(rep, indent=1, default=str), encoding='utf-8')
print('IV02_ROUNDTRIP', rep['ivy']['triangles'], rep['ivy']['pass_attributes'], rep['ivy']['bounds_within_tolerance'],
      rep['axis_markers']['within_0p1cm'], rep['facade']['triangles'], rep['facade']['slot_order_preserved'])
