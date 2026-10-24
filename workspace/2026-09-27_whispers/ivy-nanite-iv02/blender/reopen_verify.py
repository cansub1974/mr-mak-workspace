"""IV02 S4: reopen the ivy source in a clean factory-startup Blender, verify the
editable source and render the actual export mesh (front / side / oblique / masks).

  blender --factory-startup --disable-autoexec -b IV02_Ivy_Prototype.blend --python reopen_verify.py -- <ivy_IV02 root> [--quick]

Renders use a temporary backdrop plane and lights created in this process only; the
.blend is never saved here.
"""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ROOT = Path(argv[0]); QUICK = '--quick' in argv
REN = ROOT / 'renders'; REN.mkdir(exist_ok=True)
QA = ROOT / 'qa'

rep = {'blend': bpy.data.filepath, 'blender': bpy.app.version_string,
       'blend_sha256': hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()}
rep['collections'] = {c.name: sorted(o.name for o in c.objects) for c in bpy.data.collections}
st = bpy.data.objects.get('IV02_Stems')
rep['curves_editable'] = {'object_type': st.type if st else None, 'curves': len(st.data.curves) if st else 0,
                          'points': len(st.data.points) if st else 0,
                          'attributes': sorted(a.name for a in st.data.attributes) if st else []}
gn = bpy.data.objects.get('IV02_IvyPatch_GN')
mod = gn.modifiers.get('IV02_IvyGrowth') if gn else None
dg = bpy.context.evaluated_depsgraph_get()
ev_me = gn.evaluated_get(dg).to_mesh()
ev_tris = sum(len(p.vertices) - 2 for p in ev_me.polygons)
gn.evaluated_get(dg).to_mesh_clear()
ex = bpy.data.objects['SM_Ivy_WallPatch_Prototype']
rep['geometry_nodes'] = {'modifier': mod.name if mod else None, 'node_group': mod.node_group.name if mod else None,
                         'nodes': len(mod.node_group.nodes) if mod else 0,
                         'evaluates_on_reopen_triangles': ev_tris,
                         'export_copy_triangles': len(ex.data.polygons),
                         'gn_matches_export': ev_tris == len(ex.data.polygons)}
hotel_like = [o.name for o in bpy.data.objects if o.name.startswith('P_') or 'HE PBR01' in ''.join(s.material.name for s in o.material_slots if s.material)]
rep['no_hotel_data'] = {'objects_total': len(bpy.data.objects), 'hotel_like_objects': hotel_like,
                        'materials': sorted(m.name for m in bpy.data.materials),
                        'meshes': len(bpy.data.meshes)}
rep['images'] = [{'name': i.name, 'packed': bool(i.packed_file), 'colorspace': i.colorspace_settings.name, 'size': list(i.size)} for i in bpy.data.images if i.name not in ('Render Result',)]

# ---------------------------------------------------------------- render setup (memory only)
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE'
except TypeError as e:
    print('engine', e)
sc.eevee.taa_render_samples = 32 if QUICK else 96
sc.render.resolution_x, sc.render.resolution_y = (960, 960) if QUICK else (1600, 1600)
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'
for o in bpy.data.objects:
    o.hide_render = o.name != 'SM_Ivy_WallPatch_Prototype'
world = bpy.data.worlds.new('IV02_ReviewWorld'); sc.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bg.inputs['Strength'].default_value = 0.6
sun_d = bpy.data.lights.new('IV02_Sun', 'SUN'); sun_d.energy = 4.0; sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new('IV02_Sun', sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-35), math.radians(60))   # light from front-left-above
wall_me = bpy.data.meshes.new('IV02_Backdrop')
wall_me.from_pydata([(0, -0.9, -0.1), (0, 0.9, -0.1), (0, 0.9, 2.2), (0, -0.9, 2.2)], [], [(0, 1, 2, 3)])
wm = bpy.data.materials.new('IV02_BackdropStone'); wm.use_nodes = True
wb = next(n for n in wm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
wb.inputs['Base Color'].default_value = (0.55, 0.50, 0.42, 1); wb.inputs['Roughness'].default_value = 0.85
wall_me.materials.append(wm)
wall = bpy.data.objects.new('IV02_Backdrop', wall_me); sc.collection.objects.link(wall)
if wall_me.polygons[0].normal.x < 0:
    wall_me.flip_normals()
cam_d = bpy.data.cameras.new('IV02_Cam'); cam = bpy.data.objects.new('IV02_Cam', cam_d); sc.collection.objects.link(cam)
sc.camera = cam

def look_at(loc, target, lens=35, ortho=None):
    cam.location = Vector(loc)
    d = (Vector(target) - cam.location)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam_d.type = 'ORTHO'; cam_d.ortho_scale = ortho
    else:
        cam_d.type = 'PERSP'; cam_d.lens = lens

def shot(name, loc, target, lens=35, ortho=None, res=None):
    look_at(loc, target, lens, ortho)
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(REN / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    return f'renders/{name}.png'

shots = {}
shots['front_full'] = shot('IV02_front_full', (2.6, 0, 1.0), (0, 0, 1.0), lens=40, res=(1000, 1600) if not QUICK else (600, 960))
shots['front_close'] = shot('IV02_front_close', (0.75, 0.05, 1.15), (0, 0.0, 1.05), lens=35, res=(1600, 1600) if not QUICK else (960, 960))
shots['oblique_close'] = shot('IV02_oblique_close', (0.65, 0.75, 1.35), (0.02, 0.0, 1.05), lens=35)
shots['side_close'] = shot('IV02_side_close', (0.05, 1.3, 1.0), (0.05, 0.0, 1.0), lens=50)
shots['side_low'] = shot('IV02_side_root', (0.35, 0.6, 0.25), (0.02, 0.0, 0.2), lens=35)
if not QUICK:
    shots['first_person'] = shot('IV02_first_person_1p7m', (1.6, -0.5, 1.7), (0, 0.0, 1.1), lens=24, res=(1920, 1080))
    # mask diagnostics: emission of each vertex-colour channel and UV checker
    ex_mat = ex.data.materials[0]
    diag = bpy.data.materials.new('IV02_Diag'); diag.use_nodes = True
    ntd = diag.node_tree
    for n in list(ntd.nodes):
        ntd.nodes.remove(n)
    out = ntd.nodes.new('ShaderNodeOutputMaterial')
    vc = ntd.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    sp = ntd.nodes.new('ShaderNodeSeparateColor'); ntd.links.new(vc.outputs['Color'], sp.inputs['Color'])
    em = ntd.nodes.new('ShaderNodeEmission'); ntd.links.new(em.outputs['Emission'], out.inputs['Surface'])
    ex.data.materials[0] = diag
    wall.hide_render = True
    bg.inputs['Strength'].default_value = 0.0
    for ch in ('Red', 'Green', 'Blue'):
        for l in list(em.inputs['Color'].links):
            ntd.links.remove(l)
        ntd.links.new(sp.outputs[ch], em.inputs['Color'])
        shots[f'mask_{ch}'] = shot(f'IV02_mask_{ch[0]}', (2.6, 0, 1.0), (0, 0, 1.0), lens=40, res=(1000, 1600))
    for l in list(em.inputs['Color'].links):
        ntd.links.remove(l)
    tex = ntd.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images['T_Ivy_Atlas_BaseColor.png']
    uvn = ntd.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    ntd.links.new(uvn.outputs['UV'], tex.inputs['Vector']); ntd.links.new(tex.outputs['Color'], em.inputs['Color'])
    shots['unlit_basecolor'] = shot('IV02_unlit_basecolor_close', (0.75, 0.05, 1.15), (0, 0.0, 1.05), lens=35, res=(1600, 1600))
    ex.data.materials[0] = ex_mat
rep['renders'] = shots
rep['render_settings'] = {'engine': sc.render.engine, 'samples': sc.eevee.taa_render_samples, 'view_transform': 'AgX',
                          'sun_rotation_deg': [round(math.degrees(a), 1) for a in sun.rotation_euler], 'sun_energy': sun_d.energy,
                          'backdrop': 'flat plane X=0, RGB (0.55,0.50,0.42), render-only, not saved'}
rep['saved_blend'] = False
(QA / ('reopen_quick.json' if QUICK else 'reopen_verify.json')).write_text(json.dumps(rep, indent=1), encoding='utf-8')
print('IV02_REOPEN', rep['geometry_nodes'], rep['no_hotel_data']['hotel_like_objects'])
