"""IV02-r2 S5a: facade per-corner baseline from the read-only master.

Re-runs export_facade.py unchanged into a scratch folder (so the delivered exports/ and
qa/facade_export.json are never touched), then dumps the evaluated, clipped fixture mesh
exactly as the FBX exporter sees it (new_from_object + default bmesh triangulation, the
io_scene_fbx use_triangles path) to qa/facade_baseline.npz. Also measures whether the
fixture construction kept the source objects' own corner normals and UVs.

  blender --factory-startup --disable-autoexec -b <MS02.blend> --python facade_baseline.py -- <ivy_IV02 root> <scratch dir, deleted after the run> <facade-selection.json>
Never saves a .blend.
"""
import bpy, bmesh, sys, json, runpy, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ROOT = Path(argv[0]); SCR = Path(argv[1]); SELECTION = Path(argv[2])
QA = ROOT / 'qa'
(SCR / 'exports').mkdir(parents=True, exist_ok=True)

# export_facade.py takes <selection.json> <out_dir> and writes its report to <out_dir>/../qa.
sys.argv = [sys.argv[0], '--', str(SELECTION), str(SCR / 'exports')]
runpy.run_path(str(ROOT / 'scripts' / 'export_facade.py'), run_name='__main__')

fob = bpy.data.objects['SM_IV02_FacadeBay']
dg = bpy.context.evaluated_depsgraph_get()
pre = bpy.data.meshes.new_from_object(fob, preserve_all_data_layers=True, depsgraph=dg)
tri = pre.copy()
bm = bmesh.new(); bm.from_mesh(tri); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(tri); bm.free()


def dump(me):
    nl = len(me.loops)
    co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', co)
    lv = np.empty(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
    cn = np.empty(nl * 3, np.float64); me.corner_normals.foreach_get('vector', cn)
    uv = []
    for l in me.uv_layers:
        a = np.empty(nl * 2, np.float64); l.data.foreach_get('uv', a); uv.append(a.reshape(-1, 2))
    np_ = len(me.polygons)
    ls = np.empty(np_, np.int64); me.polygons.foreach_get('loop_start', ls)
    lt = np.empty(np_, np.int64); me.polygons.foreach_get('loop_total', lt)
    mi = np.empty(np_, np.int64); me.polygons.foreach_get('material_index', mi)
    sm = np.empty(np_, bool); me.polygons.foreach_get('use_smooth', sm)
    return dict(co=co.reshape(-1, 3), loop_vert=lv, corner_normal=cn.reshape(-1, 3), uv0=uv[0], uv1=uv[1],
                loop_start=ls, loop_total=lt, mat=mi, smooth=sm)


T = dump(tri); P = dump(pre)
np.savez_compressed(QA / 'facade_baseline.npz', **{f'tri_{k}': v for k, v in T.items()},
                    **{f'poly_{k}': v for k, v in P.items()})

# Source fidelity: polygons that survived clipping intact keep their centroid; compare their corner
# normals/UVs (source evaluated mesh, world space) with the fixture polygon corners (pre-triangulation).
anchor = Vector(json.loads((SCR / 'qa' / 'facade_export.json').read_text(encoding='utf-8'))['anchor_m'])
from mathutils.kdtree import KDTree
npoly = len(P['loop_start'])
kd = KDTree(npoly)
for pi in range(npoly):
    s, t = P['loop_start'][pi], P['loop_total'][pi]
    kd.insert(Vector(P['co'][P['loop_vert'][s:s + t]].mean(0)), pi)
kd.balance()
MATCH_M = 1e-5  # centroid and corner position correspondence tolerance
names = sorted(o['name'] for o in json.loads(SELECTION.read_text(encoding='utf-8'))['objects'])
src_rows = []; dn_all = []; du0 = du1 = 0.0; matched = unmatched = 0; n_coincident = 0
for name in names:
    ob = bpy.data.objects[name]; ev = ob.evaluated_get(dg); me = ev.to_mesh()
    M = ob.matrix_world; N3 = M.to_3x3().inverted().transposed()
    cn = [(N3 @ Vector(n.vector)).normalized() for n in me.corner_normals]
    uvs = [l.data for l in me.uv_layers]
    sharp = me.attributes.get('sharp_edge'); nsharp = 0
    if sharp:
        a = np.empty(len(me.edges), bool); sharp.data.foreach_get('value', a); nsharp = int(a.sum())
    flat = sum(1 for p in me.polygons if not p.use_smooth)
    om = 0.0; ok = 0
    for p in me.polygons:
        wv = [M @ me.vertices[v].co - anchor for v in p.vertices]
        c = sum(wv, Vector()) / len(wv)
        hit = [h for h in kd.find_range(c, MATCH_M) if P['loop_total'][h[1]] == len(wv)]
        if not hit:
            unmatched += 1; continue
        pn = (N3 @ p.normal).normalized()  # coincident opposite-facing polygons: pick the matching facing
        pi = max(hit, key=lambda h: pre.polygons[h[1]].normal.dot(pn))[1]; s = P['loop_start'][pi]
        n_coincident += len(hit) > 1
        fv = P['co'][P['loop_vert'][s:s + len(wv)]]
        if max(np.linalg.norm(fv - np.array(w, np.float64), axis=1).min() for w in wv) > MATCH_M:
            unmatched += 1; continue
        for li, w in zip(p.loop_indices, wv):
            j = int(np.argmin(np.linalg.norm(fv - np.array(w, np.float64), axis=1)))
            d = Vector(P['corner_normal'][s + j]).angle(cn[li], 0.0) * 57.29577951308232
            om = max(om, d); dn_all.append(d)
            du0 = max(du0, float(np.abs(np.array(uvs[0][li].uv) - P['uv0'][s + j]).max()))
            du1 = max(du1, float(np.abs(np.array(uvs[1][li].uv) - P['uv1'][s + j]).max()))
        ok += 1; matched += 1
    src_rows.append({'name': name, 'has_custom_normals': bool(me.has_custom_normals), 'sharp_edges': nsharp,
                     'flat_faces': flat, 'faces': len(me.polygons), 'intact_faces_matched': ok,
                     'max_normal_dev_deg': om})
    ev.to_mesh_clear()
dn = np.array(dn_all)
rep = {'blender': bpy.app.version_string, 'baseline_file': 'qa/facade_baseline.npz',
       'baseline_sha256': hashlib.sha256((QA / 'facade_baseline.npz').read_bytes()).hexdigest(),
       'method': 'export_facade.py rerun unchanged in scratch; fixture mesh -> bpy.data.meshes.new_from_object(preserve_all_data_layers) '
                 '-> bmesh.ops.triangulate(defaults), identical to io_scene_fbx use_triangles; corner_normals/UVMap/UV1 dumped per loop',
       'baseline_counts': {'vertices': int(len(T['co'])), 'triangles': int(len(T['loop_start'])), 'corners': int(len(T['loop_vert'])),
                           'polygons_pre_triangulation': int(len(P['loop_start'])), 'corners_pre_triangulation': int(len(P['loop_vert']))},
       'scratch_fbx_sha256': hashlib.sha256((SCR / 'exports' / 'SM_IV02_FacadeBay.fbx').read_bytes()).hexdigest(),
       'delivered_fbx_sha256': hashlib.sha256((ROOT / 'exports' / 'SM_IV02_FacadeBay.fbx').read_bytes()).hexdigest(),
       'source_fidelity': {'intact_polygons_matched': matched, 'clipped_or_unmatched_source_polygons': unmatched,
                           'corners_compared': int(dn.size), 'match_tolerance_m': MATCH_M,
                           'method': 'KD-tree on fixture polygon centroids, same corner count, every corner within match tolerance; coincident candidates resolved by polygon facing',
                           'coincident_candidate_polygons': n_coincident,
                           'normal_dev_deg': {'max': float(dn.max()), 'p99': float(np.percentile(dn, 99)),
                                              'p999': float(np.percentile(dn, 99.9)), 'mean': float(dn.mean()),
                                              'n_over_1deg': int((dn > 1).sum())},
                           'max_uv0_dev': du0, 'max_uv1_dev': du1, 'objects': src_rows},
       'master_is_dirty_in_memory': bpy.data.is_dirty, 'saved_blend': False}
(QA / 'facade_baseline.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
print('IV02_FACADE_BASELINE', rep['baseline_counts'], rep['source_fidelity']['normal_dev_deg'], du0, du1,
      rep['scratch_fbx_sha256'] == rep['delivered_fbx_sha256'])
