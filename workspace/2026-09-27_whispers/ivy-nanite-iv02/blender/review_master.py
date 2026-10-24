"""IV02 review: render the actual exported ivy FBX on the clipped MS02 facade bay with the
master's own materials, at a measured supported placement. Read-only master use:

  blender --factory-startup --disable-autoexec -b <MS02.blend> --python review_master.py -- <selection.json> <ivy_IV02 root>

Clipped copies, the review scene and imported ivy exist in memory only; nothing is saved.
"""
import bpy, bmesh, json, sys, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
SEL = json.loads(Path(argv[0]).read_text(encoding='utf-8'))
ROOT = Path(argv[1]); REN = ROOT / 'renders'; QA = ROOT / 'qa'
BMIN = Vector(SEL['crop_min_m']); BMAX = Vector(SEL['crop_max_m'])
names = sorted(o['name'] for o in SEL['objects'])
rev = bpy.data.scenes.new('IV02_Review_NotSaved')
dg = bpy.context.evaluated_depsgraph_get()
fix_objs = []
all_v, all_f = [], []
for name in names:
    ob = bpy.data.objects[name]
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    ob.evaluated_get(dg).to_mesh_clear()
    for axis in range(3):
        for sign, val in ((1, BMIN[axis]), (-1, BMAX[axis])):
            co = Vector((0, 0, 0)); co[axis] = val
            no = Vector((0, 0, 0)); no[axis] = -sign
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_outer=True, dist=1e-6)
    nm = bpy.data.meshes.new('IV02R_' + name[:40]); bm.to_mesh(nm); bm.free()
    for s in ob.material_slots:
        nm.materials.append(s.material)
    o2 = bpy.data.objects.new(nm.name, nm); rev.collection.objects.link(o2); fix_objs.append(o2)
    for k in ob.keys():
        if k.startswith('he_'):
            o2[k] = ob[k]   # materials read these OBJECT attributes for their UV transform
    off = len(all_v); all_v += [v.co.copy() for v in nm.vertices]; all_f += [tuple(i + off for i in p.vertices) for p in nm.polygons]
bvh = BVHTree.FromPolygons(all_v, all_f)

# ---------------------------------------------------------------- placement survey (source frame)
WALL_Y = 1.8   # bay front face (anchor plane)
ROT = Matrix.Rotation(math.radians(90), 4, 'Z')   # patch +X -> source +Y (outward), patch +Y -> source -X
build = json.loads((QA / 'ivy_build.json').read_text(encoding='utf-8'))['export_mesh']
ylo, yhi = build['tight_min_m'][1], build['tight_max_m'][1]
depth = build['tight_max_m'][0]
def score(root):
    ok = clear = 0; rows = []
    for py in (ylo, (ylo + 0) / 2, 0.0, yhi / 2, yhi):
        for pz in (0.1, 0.5, 1.0, 1.5, 1.8):
            p = root + Vector((-py, 0, pz))
            hit = bvh.ray_cast(Vector((p.x, WALL_Y + 0.6, p.z)), Vector((0, -1, 0)), 1.0)
            sup = hit[0] is not None and abs(hit[0].y - WALL_Y) <= 0.01 and hit[1].y > 0.95
            # nothing may stand inside the ivy depth envelope in front of the wall
            fr = bvh.ray_cast(Vector((p.x, WALL_Y + 0.002, p.z)), Vector((0, 1, 0)), depth + 0.01)
            cl = fr[0] is None
            ok += sup; clear += cl
            rows.append({'patch_y': round(py, 3), 'patch_z': pz, 'supported': bool(sup), 'clear_front': bool(cl)})
    return ok, clear, rows
best = None; survey = []
for i in range(0, 321):
    x = -0.9 + i * 0.025
    root = Vector((x, WALL_Y, 0.55))
    ok, clear, rows = score(root)
    survey.append({'root_x': round(x, 3), 'supported': ok, 'clear': clear})
    key = (ok + clear, -abs(x - SEL['anchor_m'][0]))
    if best is None or key > best[0]:
        best = (key, x, rows)
root = Vector((best[1], WALL_Y, 0.55))
place = Matrix.Translation(root) @ ROT

# ---------------------------------------------------------------- the actual exported ivy
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT / 'exports' / 'SM_Ivy_WallPatch_Prototype.fbx'), use_custom_normals=True,
                         axis_forward='-Y', axis_up='Z', colors_type='LINEAR')
ivy = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
for c in list(ivy.users_collection):
    c.objects.unlink(ivy)
rev.collection.objects.link(ivy)
ivy.matrix_world = place @ ivy.matrix_world
mat = ivy.material_slots[0].material; mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
for fn, sock, data in (('T_Ivy_Atlas_BaseColor.png', 'Base Color', False), ('T_Ivy_Atlas_Roughness.png', 'Roughness', True), ('T_Ivy_Atlas_Normal.png', 'Normal', True)):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(ROOT / 'textures' / fn))
    if data:
        t.image.colorspace_settings.name = 'Non-Color'
    if sock == 'Normal':
        nmn = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(t.outputs['Color'], nmn.inputs['Color']); nt.links.new(nmn.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        nt.links.new(t.outputs['Color'], bsdf.inputs[sock])
iv = [ivy.matrix_world @ v.co for v in ivy.data.vertices]
ivy_bvh = BVHTree.FromPolygons(iv, [tuple(p.vertices) for p in ivy.data.polygons])
pairs = ivy_bvh.overlap(bvh)
hit_tris = sorted({a for a, b in pairs})

# ---------------------------------------------------------------- render (memory-only scene)
sc = rev
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 96
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('IV02R_World'); sc.world = w; w.use_nodes = True
bgn = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bgn.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bgn.inputs['Strength'].default_value = 0.7
sd = bpy.data.lights.new('IV02R_Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(1.5)
so = bpy.data.objects.new('IV02R_Sun', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(55), 0, math.radians(200))   # sun from the +Y facade side, from the left
cdat = bpy.data.cameras.new('IV02R_Cam'); cam = bpy.data.objects.new('IV02R_Cam', cdat); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, tgt, lens, res):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cdat.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(REN / name)
    bpy.ops.render.render(write_still=True, scene=sc.name)
    return f'renders/{name}'
c = root
shots = [shot('IV02_facade_bay_wide.png', (c.x, c.y + 7.5, 2.0), (c.x, c.y, 1.6), 30, (1920, 1080)),
         shot('IV02_facade_first_person.png', (c.x - 1.2, c.y + 3.0, 1.7), (c.x, c.y, 1.4), 35, (1920, 1080)),
         shot('IV02_facade_close.png', (c.x + 0.25, c.y + 1.3, 1.5), (c.x, c.y, 1.4), 35, (1600, 1600)),
         shot('IV02_facade_oblique.png', (c.x + 1.6, c.y + 1.5, 1.6), (c.x, c.y, 1.3), 35, (1600, 1600))]
rep = {'source': bpy.data.filepath, 'saved_blend': False, 'master_dirty_in_memory_note': 'review scene and clipped copies are unsaved memory data',
       'placement': {'root_source_m': list(root), 'rotation': 'Rz(+90 deg): patch +X -> source +Y (out of the bay front), patch +Y -> source -X',
                     'matrix_patch_to_source': [list(r) for r in place],
                     'matrix_patch_to_fixture': [list(r) for r in (Matrix.Translation(-Vector(SEL['anchor_m'])) @ place)],
                     'note': 'review placement only, chosen by the survey; the Unreal fixture placement belongs to #114'},
       'survey_best_samples': best[2], 'survey_scan_root_z_0p55': survey,
       'interference': {'ivy_triangles_intersecting_facade': len(hit_tris), 'pairs': len(pairs),
                        'intersecting_centroids_patch_local_m': [list(place.inverted() @ (sum((iv[k] for k in ivy.data.polygons[t].vertices), Vector()) / 3)) for t in hit_tris]},
       'renders': shots}
(QA / 'facade_review.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
print('IV02_REVIEW', best[1], best[0], len(hit_tris))
