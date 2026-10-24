"""IV02-r2 S5b: facade per-corner FBX round trip in a clean factory-startup process.

Reimports exports/SM_IV02_FacadeBay.fbx into an empty scene and compares every triangle corner
with qa/facade_baseline.npz (the evaluated, clipped fixture triangulated exactly as io_scene_fbx
does; written by facade_baseline.py from the read-only master). Merges the result into
qa/fbx_roundtrip.json under 'facade_per_corner' and renders the actual imported mesh.

  blender --factory-startup --disable-autoexec -b --python roundtrip_facade.py -- <ivy_IV02 root>
"""
import bpy, sys, json, math, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(sys.argv[sys.argv.index('--') + 1])
EXP = ROOT / 'exports'; QA = ROOT / 'qa'; REN = ROOT / 'renders'
B = np.load(QA / 'facade_baseline.npz')
TOL = {'position_m': 1e-4, 'normal_deg': 1.0, 'uv': 1e-5}

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
IMPORT = dict(use_custom_normals=True, use_image_search=False, use_anim=False, global_scale=1.0,
              bake_space_transform=False, axis_forward='-Y', axis_up='Z')
fbx = EXP / 'SM_IV02_FacadeBay.fbx'
bpy.ops.import_scene.fbx(filepath=str(fbx), **IMPORT)
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
me = ob.data; M = ob.matrix_world; M3 = M.to_3x3().inverted().transposed()

nl = len(me.loops)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
co = co @ np.array(M.to_3x3()).T + np.array(M.translation)
lv = np.empty(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
cn = np.empty(nl * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3) @ np.array(M3).T
cn /= np.linalg.norm(cn, axis=1, keepdims=True)
uvn = [l.name for l in me.uv_layers]
uv = []
for l in me.uv_layers:
    a = np.empty(nl * 2); l.data.foreach_get('uv', a); uv.append(a.reshape(-1, 2))
ls = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_start', ls)
mi = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('material_index', mi)

bco, blv, bcn = B['tri_co'], B['tri_loop_vert'], B['tri_corner_normal']
bls, bmi = B['tri_loop_start'], B['tri_mat']
counts = {'vertices': [int(len(bco)), int(len(co))], 'triangles': [int(len(bls)), int(len(ls))], 'corners': [int(len(blv)), nl]}

# Correspondence. FBX keeps Blender vertices as control points and polygons in order; check that
# directly (vertex positions and per-triangle corner vertex indices). If either fails, fall back to
# matching triangles by their sorted rounded corner positions.
vert_order = len(bco) == len(co) and float(np.abs(bco - co).max()) < TOL['position_m']
tri_order = vert_order and nl == len(blv) and bool((lv == blv).all())
if tri_order:
    corr = np.arange(nl); method = 'identity: vertex order and per-triangle corner vertex indices identical to the baseline'
    unmatched = 0
else:
    def keys(c, l, starts):
        out = {}
        for t, s in enumerate(starts):
            k = tuple(sorted(tuple(np.round(c[l[s + i]], 5)) for i in range(3)))
            out.setdefault(k, []).append(t)
        return out
    bk = keys(bco, blv, bls)
    corr = np.full(nl, -1); unmatched = 0
    for t, s in enumerate(ls):
        k = tuple(sorted(tuple(np.round(co[lv[s + i]], 5)) for i in range(3)))
        cand = bk.get(k)
        if not cand:
            unmatched += 1; continue
        bt = cand.pop(0); bs = bls[bt]
        for i in range(3):
            j = int(np.argmin(np.linalg.norm(bco[blv[bs:bs + 3]] - co[lv[s + i]], axis=1)))
            corr[s + i] = bs + j
    method = 'fallback: triangles matched by sorted rounded (1e-5 m) corner positions, corners by nearest position'

ok = corr >= 0
pe = np.linalg.norm(co[lv[ok]] - bco[blv[corr[ok]]], axis=1)
dots = np.clip((cn[ok] * bcn[corr[ok]]).sum(1), -1, 1)
ne = np.degrees(np.arccos(dots))
res = {}
for k, (name, bkey) in enumerate((('UVMap', 'tri_uv0'), ('UV1', 'tri_uv1'))):
    if k >= len(uv):
        res[name] = {'present': False}; continue
    e = np.abs(uv[k][ok] - B[bkey][corr[ok]]).max(1)
    res[name] = {'present': True, 'reimport_layer': uvn[k], 'samples': int(e.size), 'max_error': float(e.max()),
                 'p99_error': float(np.percentile(e, 99)), 'n_over_tol': int((e > TOL['uv']).sum())}
tri_corr = corr[ls] // 3 if tri_order else None
mat_ok = bool((mi == bmi).all()) if tri_order else None

# FBX/engine vertex split: a render vertex per unique (vertex, normal, UV0, UV1) corner tuple.
key = np.concatenate([lv[:, None].astype(np.float64), np.round(cn, 5), np.round(uv[0], 6), np.round(uv[1], 6)], axis=1)
split = int(len(np.unique(key, axis=0)))

pc = {'fbx': str(fbx.relative_to(ROOT)).replace('\\', '/'), 'fbx_sha256': hashlib.sha256(fbx.read_bytes()).hexdigest(),
      'baseline': 'qa/facade_baseline.npz', 'baseline_sha256': hashlib.sha256((QA / 'facade_baseline.npz').read_bytes()).hexdigest(),
      'import_settings': IMPORT, 'counts_baseline_reimport': counts,
      'vertex_order_preserved': vert_order, 'triangle_corner_order_preserved': tri_order,
      'correspondence_method': method, 'unmatched_triangles': unmatched,
      'corners_compared': int(ok.sum()), 'material_index_per_triangle_equal': mat_ok,
      'max_position_error_m': float(pe.max()),
      'normal_error_deg': {'samples': int(ne.size), 'max': float(ne.max()), 'p99': float(np.percentile(ne, 99)),
                           'mean': float(ne.mean()), 'n_over_tol': int((ne > TOL['normal_deg']).sum())},
      'uv': res, 'uv_channel_mapping': {'UVMap': 'UV0 = source BakeAtlas', 'UV1': 'UV1 = source SurfaceMetres'},
      'tolerances': TOL,
      'has_custom_normals_reimport': bool(me.has_custom_normals),
      'unique_vertex_normal_uv0_uv1_corner_keys_after_split': split,
      'split_note': 'FBX stores control points (= Blender vertices) and per-corner normals/UVs; an engine splits a control point wherever corner data differ',
      'saved_blend': False}
pc['pass'] = (counts['triangles'][0] == counts['triangles'][1] and counts['vertices'][0] == counts['vertices'][1]
              and unmatched == 0 and pc['corners_compared'] == counts['corners'][0]
              and pc['max_position_error_m'] <= TOL['position_m'] and pc['normal_error_deg']['n_over_tol'] == 0
              and all(r.get('present') and r['n_over_tol'] == 0 for r in res.values()) and mat_ok is not False)

# Render the actual imported mesh: neutral clay so corner normals read, plus its own UV1 checker.
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE'
except TypeError:
    pass
sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('W'); sc.world = w
bgn = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bgn.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bgn.inputs['Strength'].default_value = 0.5
sd = bpy.data.lights.new('S', 'SUN'); sd.energy = 4; so = bpy.data.objects.new('S', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(-50), 0, math.radians(-35))
clay = bpy.data.materials.new('Clay')
bs = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value = (0.6, 0.58, 0.55, 1); bs.inputs['Roughness'].default_value = 0.6
chk = bpy.data.materials.new('UV1Checker'); nt = chk.node_tree
b2 = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
uvn_ = nt.nodes.new('ShaderNodeUVMap'); uvn_.uv_map = 'UV1'
ct = nt.nodes.new('ShaderNodeTexChecker'); ct.inputs['Scale'].default_value = 4.0
nt.links.new(uvn_.outputs['UV'], ct.inputs['Vector']); nt.links.new(ct.outputs['Color'], b2.inputs['Base Color'])
cd_ = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd_); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000


def shot(name, mat, loc, tgt, lens):
    for i in range(len(ob.material_slots)):
        ob.material_slots[i].material = mat
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd_.lens = lens
    sc.render.filepath = str(REN / name); bpy.ops.render.render(write_still=True)
    return f'renders/{name}'


pc['renders'] = [shot('IV02_facade_roundtrip_clay_wide.png', clay, (0.5, 9.5, 2.6), (0.0, 0.0, 2.0), 28),
                 shot('IV02_facade_roundtrip_clay_plinth.png', clay, (2.0, 3.0, 1.2), (3.8, 0.3, 0.4), 35),
                 shot('IV02_facade_roundtrip_uv1_checker.png', chk, (0.5, 9.5, 2.6), (0.0, 0.0, 2.0), 28)]
pc['render_note'] = 'actual reimported facade FBX mesh with its imported custom normals; clay and UV1 (SurfaceMetres) checker overrides, render only'

rt = QA / 'fbx_roundtrip.json'
rep = json.loads(rt.read_text(encoding='utf-8'))
rep['facade_per_corner'] = pc
rt.write_text(json.dumps(rep, indent=1, default=str), encoding='utf-8')
print('IV02_FACADE_ROUNDTRIP', pc['pass'], counts, pc['corners_compared'], pc['max_position_error_m'],
      pc['normal_error_deg'], {k: v.get('max_error') for k, v in res.items()}, method)
