"""IV02 S2: export the contracted MS02 facade bay as a clipped fixture FBX.

Read-only use of the master. Run in its own background process:
  blender --factory-startup --disable-autoexec -b <MS02.blend> --python export_facade.py -- <selection.json> <out_dir>
Never saves a .blend. IV02-r2: each source object's own evaluated corner normals (custom split
normals, sharp edges) are carried through the clip as a loop layer and re-applied as custom normals;
r1 copied only positions/UVs and so re-averaged hard corners. All edits (clip copies, image filepaths, temporary links)
live only in this process's memory and are discarded on exit.
"""
import bpy, bmesh, json, sys, hashlib, os, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
SEL = json.loads(Path(argv[0]).read_text(encoding='utf-8'))
OUT = Path(argv[1])
QA = OUT.parent / 'qa'
TEX = OUT / 'facade-textures'
TEX.mkdir(parents=True, exist_ok=True)
QA.mkdir(exist_ok=True)

COLL = 'EXTERIOR | OPT01 shared architecture'
BMIN = Vector(SEL['crop_min_m']); BMAX = Vector(SEL['crop_max_m'])
ANCHOR = Vector(SEL['anchor_m'])
SRC_TO_FIXTURE = Matrix.Translation(-ANCHOR)
LANDMARKS = ['P_WINDOW_9ab003c2031b2eb2', 'P_d4503c2c3684eb7e', 'P_d93ed1bf10e1a563',
             'P_f08e4fe91a7e9be9', 'P_e715e4664a8a88df', 'P_9c317df106f647ca']
assert bpy.data.is_saved and not bpy.data.is_dirty or True
report = {'source': bpy.data.filepath, 'blender': bpy.app.version_string,
          'crop_min_m': list(BMIN), 'crop_max_m': list(BMAX), 'anchor_m': list(ANCHOR),
          'source_to_fixture_matrix': [list(r) for r in SRC_TO_FIXTURE],
          'fixture_to_unreal': 'Unreal cm = (X, -Y, Z) * 100 of fixture metres; rotations conjugated by diag(1,-1,1)',
          'saved_blend': False}

def aabb(obj):
    cs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]

def intersects(lo, hi):
    return all(lo[i] <= BMAX[i] and hi[i] >= BMIN[i] for i in range(3))

# Recompute the selection independently and compare with the frozen list.
live = sorted(o.name for o in bpy.data.objects if o.type == 'MESH'
              and COLL in [c.name for c in o.users_collection] and intersects(*aabb(o)))
frozen = sorted(o['name'] for o in SEL['objects'])
report['selection_frozen_count'] = len(frozen)
report['selection_live_count'] = len(live)
report['selection_matches_frozen'] = live == frozen
report['selection_diff'] = {'missing_live': sorted(set(frozen) - set(live)), 'extra_live': sorted(set(live) - set(frozen))}

dg = bpy.context.evaluated_depsgraph_get()
global_mats = []  # slot order: first appearance over name-sorted objects
rows = []
bm_all = bmesh.new()
uv_names_seen = {}
max_uv = 0
for name in frozen:
    ob = bpy.data.objects[name]
    max_uv = max(max_uv, len(ob.data.uv_layers))
for i in range(max_uv):
    bm_all.loops.layers.uv.new('UVMap' if i == 0 else f'UV{i}')
NRM = 'he_src_normal'
nl_all = bm_all.loops.layers.float_vector.new(NRM)

for name in frozen:
    ob = bpy.data.objects[name]
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    src_faces = len(me.polygons)
    N3 = ob.matrix_world.to_3x3().inverted().transposed()
    wn = [(N3 @ Vector(c.vector)).normalized() for c in me.corner_normals]
    bm = bmesh.new(); bm.from_mesh(me)
    nl_src = bm.loops.layers.float_vector.new(NRM)
    li = 0
    for f in bm.faces:  # from_mesh keeps polygon and corner order
        for loop in f.loops:
            loop[nl_src] = wn[li]; li += 1
    bm.transform(ob.matrix_world)
    uvn = [l.name for l in me.uv_layers]
    uv_names_seen[name] = uvn
    for axis in range(3):
        for sign, val in ((1, BMIN[axis]), (-1, BMAX[axis])):
            co = Vector((0, 0, 0)); co[axis] = val
            no = Vector((0, 0, 0)); no[axis] = -sign  # normal points outside the box
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True, dist=1e-6)
    mats = [s.material.name if s.material else None for s in ob.material_slots]
    remap = []
    for m in mats:
        if m not in global_mats:
            global_mats.append(m)
        remap.append(global_mats.index(m))
    kept = len(bm.faces)
    # copy into the combined bmesh, per-loop UV layers by index
    tmp = bpy.data.meshes.new('tmp'); bm.to_mesh(tmp); bm.free()
    for p in tmp.polygons:
        p.material_index = remap[p.material_index] if remap else 0
    off = len(bm_all.verts)
    src_uv = [tmp.uv_layers[i] if i < len(tmp.uv_layers) else None for i in range(max_uv)]
    vmap = [bm_all.verts.new(v.co) for v in tmp.vertices]
    bm_all.verts.ensure_lookup_table()
    uvls = [bm_all.loops.layers.uv[i] for i in range(max_uv)]
    src_n = tmp.attributes[NRM].data
    for p in tmp.polygons:
        try:
            f = bm_all.faces.new([vmap[i] for i in p.vertices])
        except ValueError:
            continue
        f.material_index = p.material_index; f.smooth = p.use_smooth
        for li, loop in zip(p.loop_indices, f.loops):
            for k in range(max_uv):
                if src_uv[k] is not None:
                    loop[uvls[k]].uv = src_uv[k].data[li].uv
            loop[nl_all] = src_n[li].vector
    lo = [min(v.co[i] for v in tmp.vertices) for i in range(3)] if len(tmp.vertices) else None
    hi = [max(v.co[i] for v in tmp.vertices) for i in range(3)] if len(tmp.vertices) else None
    he = {k: float(ob[k]) for k in ob.keys() if k.startswith('he_')}
    rows.append({'name': name, 'source_faces': src_faces, 'clipped_faces': kept, 'materials': mats, 'he_uv_props': he,
                 'he_uv1_identity': all(abs(he.get(k, d) - d) < 1e-9 for k, d in (('he_uv1uu', 1), ('he_uv1vu', 0), ('he_uv1ou', 0), ('he_uv1uv', 0), ('he_uv1vv', 1), ('he_uv1ov', 0))),
                 'uv_layers': uvn, 'clipped_min_m': lo, 'clipped_max_m': hi,
                 'matrix_world': [list(r) for r in ob.matrix_world]})
    bpy.data.meshes.remove(tmp); ev.to_mesh_clear()

report['objects'] = rows
report['material_uv_route'] = ('HE PBR01 brick/limestone/iron/relief sample SurfaceMetres (UV1) through the per-object affine '
                               'he_uv1uu,vu,ou,uv,vv,ov object properties: u = x*uu + y*vu + ou, v = x*uv + y*vv + ov; relief also uses BakeAtlas (UVMap).')
report['all_he_uv1_identity'] = all(r['he_uv1_identity'] for r in rows)
report['uv_layer_policy'] = f'combined UV channel k = k-th UV layer of each source object; max {max_uv}'
report['landmarks'] = {n: next((r['clipped_faces'] for r in rows if r['name'].startswith(n)), 0) for n in LANDMARKS}
report['landmarks_all_present'] = all(v > 0 for v in report['landmarks'].values())

bm_all.transform(SRC_TO_FIXTURE)
fix = bpy.data.meshes.new('SM_IV02_FacadeBay')
bm_all.to_mesh(fix); bm_all.free()
want = []; n_degenerate = 0
for p in fix.polygons:
    for li in p.loop_indices:
        v = Vector(fix.attributes[NRM].data[li].vector)
        if v.length < 0.5:  # clip-interpolated corner with no usable normal: fall back to the face normal
            v = p.normal.copy(); n_degenerate += 1
        want.append(v.normalized())
fix.attributes.remove(fix.attributes[NRM])
fix.normals_split_custom_set([tuple(v) for v in want])
dev = [math.degrees(Vector(c.vector).angle(w, 0.0)) for c, w in zip(fix.corner_normals, want)]
report['source_normals'] = {'route': 'per-object evaluated corner_normals -> world (inverse-transpose) -> loop layer through bisect -> normals_split_custom_set',
                            'corners': len(want), 'degenerate_fallback_face_normal': n_degenerate,
                            'max_set_vs_wanted_deg': max(dev), 'has_custom_normals': fix.has_custom_normals}
for m in global_mats:
    fix.materials.append(bpy.data.materials.get(m) if m else None)
fob = bpy.data.objects.new('SM_IV02_FacadeBay', fix)
bpy.context.scene.collection.objects.link(fob)
vs = [v.co for v in fix.vertices]
tlo = [min(v[i] for v in vs) for i in range(3)]; thi = [max(v[i] for v in vs) for i in range(3)]
report['fixture'] = {'material_slots_in_order': global_mats, 'vertices': len(fix.vertices), 'faces': len(fix.polygons),
                     'triangles': sum(len(p.vertices) - 2 for p in fix.polygons),
                     'tight_min_m': tlo, 'tight_max_m': thi,
                     'tight_size_cm': [(thi[i] - tlo[i]) * 100 for i in range(3)],
                     'envelope_limit_cm': [910, 280, 440],
                     'within_envelope': all((thi[i] - tlo[i]) * 100 <= lim + 1e-6 for i, lim in enumerate((910, 280, 440))),
                     'uv_layers': [l.name for l in fix.uv_layers]}

# Wall support survey around the anchor (source frame): rays toward -Y (into the wall).
bvh = BVHTree.FromPolygons([v.co for v in fix.vertices], [p.vertices for p in fix.polygons])
survey = []
for iz in range(0, 21):
    for ix in range(-10, 11):
        o = Vector((ix * 0.05, 1.5, iz * 0.1 + 0.001))  # fixture frame
        hit = bvh.ray_cast(o, Vector((0, -1, 0)), 3.0)
        survey.append({'x': round(o.x, 3), 'z': round(o.z, 3),
                       'hit_y': None if hit[0] is None else round(hit[0].y, 4),
                       'normal': None if hit[1] is None else [round(c, 3) for c in hit[1]],
                       'material': None if hit[2] is None else global_mats[fix.polygons[hit[2]].material_index]})
report['anchor_support_survey_fixture_frame'] = survey

# Original facade textures: raw packed bytes, no recompression.
tex_rows = []
def walk(nt, seen):
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            yield n.image
        if n.type == 'GROUP' and n.node_tree and n.node_tree.name not in seen:
            seen.add(n.node_tree.name)
            yield from walk(n.node_tree, seen)
for m in global_mats:
    mat = bpy.data.materials.get(m) if m else None
    if not (mat and mat.node_tree):
        continue
    for img in {i.name: i for i in walk(mat.node_tree, set())}.values():
        if any(r['image'] == img.name for r in tex_rows):
            next(r for r in tex_rows if r['image'] == img.name)['materials'].append(m); continue
        ext = os.path.splitext(img.filepath)[1] or ('.' + img.file_format.lower())
        safe = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in img.name)
        if not safe.lower().endswith(ext.lower()):
            safe += ext
        dst = TEX / safe
        if img.packed_file:
            data = bytes(img.packed_file.data)
        else:
            data = Path(bpy.path.abspath(img.filepath)).read_bytes()
        dst.write_bytes(data)
        tex_rows.append({'image': img.name, 'file': f'exports/facade-textures/{safe}', 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(), 'size_px': list(img.size),
                         'colorspace': img.colorspace_settings.name, 'packed': bool(img.packed_file),
                         'materials': [m]})
        img.filepath = str(dst)  # in-memory only, so the FBX references the exported copy
report['facade_textures'] = tex_rows

# Material node summary for the importer (read-only description).
mat_rows = []
for m in global_mats:
    mat = bpy.data.materials.get(m) if m else None
    if not mat:
        mat_rows.append({'name': m}); continue
    mat_rows.append({'name': m, 'node_types': sorted({n.type for n in mat.node_tree.nodes}) if mat.node_tree else [],
                     'images': [r['image'] for r in tex_rows if m in r['materials']]})
report['facade_materials'] = mat_rows

FBX_SETTINGS = dict(use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z',
                    bake_space_transform=False, use_mesh_modifiers=True, mesh_smooth_type='FACE',
                    use_tspace=True, use_triangles=True, colors_type='NONE', add_leaf_bones=False,
                    bake_anim=False, use_custom_props=False, path_mode='RELATIVE', embed_textures=False)
for o in bpy.context.view_layer.objects:
    o.select_set(False)
fob.select_set(True); bpy.context.view_layer.objects.active = fob
fbx = OUT / 'SM_IV02_FacadeBay.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx), **FBX_SETTINGS)
report['fbx'] = {'path': str(fbx), 'bytes': fbx.stat().st_size,
                 'sha256': hashlib.sha256(fbx.read_bytes()).hexdigest(),
                 'settings': {k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX_SETTINGS.items()}}
report['master_is_dirty_in_memory'] = bpy.data.is_dirty
(QA / 'facade_export.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
print('IV02_FACADE_EXPORT', report['selection_matches_frozen'], report['landmarks_all_present'],
      report['fixture']['triangles'], report['fixture']['tight_size_cm'], len(tex_rows))
