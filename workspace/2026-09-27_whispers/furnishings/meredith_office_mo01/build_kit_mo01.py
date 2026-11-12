"""MO01 kit: game meshes with their baked maps (Blender, background), one kit file per run.

    blender -b --factory-startup --python build_kit_mo01.py -- --only=<mantel|drapes|books|candelabra,clock> [--nobake] [--preview]
mantel      SM_MO01_Mantel: warm statuary marble chimneypiece after the reference: moulded shelf on a cyma bed mould,
            a frieze with the scanned rosette-and-scroll crest (EC01 Crest, Poly Haven ornate_mirror_01, CC0), leg
            blocks with scanned rosettes, S-scroll consoles with the scanned acanthus drop (ClassicConsole_01, CC0) and
            volutes, sunk leg panels, plinths, and a black-marble slip round the fire opening. 4096 BaseColor/Normal
            (hero piece seen within a metre), 2048 ORM.
drapes      SM_MO01_DrapeSide (L/R), SM_MO01_Sheer, SM_MO01_Swag_N/_E, SM_MO01_Tail_N/_E_L/_R and fringe cards:
            velvet curtains and ivory sheers hung inside the arch (cloth simulation, mo01_cloth.py), one tailored swag
            per arch with knife-pleated tails over its ends (owner, 12 Nov: "Let's see the single swag.", mo01_drapes.py).
            High: the settled grid or the creased surface; low: a coarser grid of the same surface. 1024 normal per
            piece (tails 512); colour from the tiling velvet / sheer maps on UV1.
books       SM_MO01_BookRow_* (20 row modules) and SM_MO01_Books_Mantel from the spine atlas (prepare_books.py,
            mo01_books.py); writes kit/Books_Rows.json with the shelf layout.
candelabra  SM_MO01_Candelabra and SM_MO01_Clock (mo01_props.py): baked 1K sets; the clock's dial is prepare_props.py.
clock
Frames: mantel X along the wall (0 = centre), Y out of the wall, Z up from the floor top. Drapes: X along the wall
(0 = window centre), Y out of the wall face, Z up from the floor top. Books: the bookcase run frame (mo01_books.py).
Saves meredith_office_MO01/kit/MO01_Kit_<kits>.blend (game meshes, materials and the high poly, hidden) and merges
Kit_Info.json. Build final kits without --preview: the preview scaffolding would be saved into the kit.
"""
import bpy, bmesh, json, math, os, sys, time
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mo01_spec as S
import mo01_geom as G

W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
KIT = os.path.join(W, "kit"); BAKE = os.path.join(KIT, "bake"); TEX = os.path.join(W, "textures")
EC_TEX = "D:/AI_Modelling/hotel_eden/working/executive_EC01/textures"
os.makedirs(BAKE, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = next((a.split("=", 1)[1].split(",") for a in ARGS if a.startswith("--only=")), ["mantel", "drapes", "books", "candelabra", "clock"])
NOBAKE = "--nobake" in ARGS
REC = json.load(open(os.path.join(W, "Material_Recipes.json")))
ECR = json.load(open("D:/AI_Modelling/hotel_eden/working/executive_EC01/Material_Recipes.json"))["carving_heightfields"]["tiles"]
INFO = {}
t0 = time.time()


def log(*a):
    print(f"[{time.time() - t0:7.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ scene
def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    dev = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = t
            except TypeError:
                continue
            prefs.get_devices()
            if [d for d in prefs.devices if d.type == t]:
                for d in prefs.devices:
                    d.use = d.type == t
                dev = t; break
    except Exception as e:
        print("GPU setup", e)
    sc.cycles.device = "GPU" if dev != "CPU" else "CPU"
    sc.cycles.samples = 64
    log("DEVICE", dev)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c


def obj_from_part(name, part, c, smooth=True, sharp=40):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in part["verts"]], [], [tuple(f) for f in part["faces"]])
    me.validate(); me.update()
    for _ in range(max(part.get("mat") or [0]) + 1):
        me.materials.append(None)                                  # slots first, so material indices survive modifiers
    if part.get("mat") and len(part["mat"]) == len(me.polygons):
        me.polygons.foreach_set("material_index", np.array(part["mat"], np.int32))
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), smooth))
    if smooth and sharp:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; me.name = old.name
    bpy.data.meshes.remove(old)
    return ob


def bevel(ob, width, segs, angle=40, harden=True):
    md = ob.modifiers.new("bevel", "BEVEL"); md.width = width; md.segments = segs; md.limit_method = "ANGLE"
    md.angle_limit = math.radians(angle); md.harden_normals = harden; md.miter_outer = "MITER_ARC"
    return apply_mods(ob)


def np_mesh(name, co, quads, c, smooth=True):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co)); me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    F = len(quads)
    me.loops.add(F * 4); me.loops.foreach_set("vertex_index", quads.astype(np.int32).ravel())
    me.polygons.add(F); me.polygons.foreach_set("loop_start", np.arange(0, 4 * F, 4, dtype=np.int32))
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.full(F, smooth))
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


def heightfield(name):
    """EC01 scanned carving tile: height in metres (h=0 = the carrier face), and its placed size at scale 1."""
    t = ECR[name]
    im = bpy.data.images.load(os.path.join(EC_TEX, t["height"]["file"]), check_existing=False)
    im.colorspace_settings.name = "Non-Color"
    a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1, :, 0]
    bpy.data.images.remove(im)
    return a * t["height_max_m"], tuple(t["size_m"])


def flip_to(ob, out_dir):
    me = ob.data
    n = np.zeros(len(me.polygons) * 3, np.float32); me.polygons.foreach_get("normal", n); n = n.reshape(-1, 3)
    a = np.zeros(len(me.polygons), np.float32); me.polygons.foreach_get("area", a)
    if float((n * a[:, None]).sum(0) @ np.asarray(out_dir, np.float32)) < 0:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()
    return ob


def hf_grid(name, h, size, scale, c, frame, pool=2, exag=1.0, out_dir=(0, 1, 0)):
    """A displaced grid of a carving tile. frame(u, v, d) -> world (x, y, z): u across, v up, d out of the face."""
    if pool > 1:
        H_, W_ = h.shape[0] // pool * pool, h.shape[1] // pool * pool
        h = h[:H_, :W_].reshape(H_ // pool, pool, W_ // pool, pool).mean((1, 3))
    rows, cols = h.shape
    us = np.linspace(-size[0] * scale / 2, size[0] * scale / 2, cols); vs = np.linspace(size[1] * scale / 2, -size[1] * scale / 2, rows)
    U, Vv = np.meshgrid(us, vs)
    D = h * scale * exag + 0.0003
    co = frame(U.ravel(), Vv.ravel(), D.ravel())
    r, cc = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = r * cols + cc
    q = np.stack([a, a + cols, a + cols + 1, a + 1], -1).reshape(-1, 4)
    ob = np_mesh(name, co, q, c)
    return flip_to(ob, out_dir)


# ------------------------------------------------------------------ materials
def img(path, data):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = "Non-Color" if data else "sRGB"
    return im


def mat_box(name, prefix, mode, tile_m):
    """High-poly bake material: box-projected tiling map in object space (emission of BaseColor / ORM, or a plain BSDF)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if mode == "shade":
        b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"]); return m
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile_m, 1 / tile_m, 1 / tile_m)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.projection = "BOX"; t.projection_blend = 0.25
    t.image = img(os.path.join(TEX, f"{prefix}_{'BaseColor' if mode == 'bc' else 'ORM'}.png"), mode != "bc")
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(e.outputs[0], out.inputs["Surface"])
    if mode == "rough":
        sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(t.outputs["Color"], sp.inputs["Color"])
        nt.links.new(sp.outputs["Green"], e.inputs["Color"])
    else:
        nt.links.new(t.outputs["Color"], e.inputs["Color"])
    return m


def mat_unique(name, prefix, uv="UV0_Bake", placeholder=True):
    """Runtime material: baked BaseColor / NormalGL / ORM on UV0 (AO multiplied at 0.5, as EC01)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    def tx(suffix, data):
        p = os.path.join(TEX, f"{prefix}_{suffix}.png")
        t = nt.nodes.new("ShaderNodeTexImage")
        if os.path.exists(p):
            t.image = img(p, data)
        else:
            im = bpy.data.images.new(os.path.basename(p), 4, 4); im.source = "FILE"; im.filepath = p
            im.colorspace_settings.name = "Non-Color" if data else "sRGB"; t.image = im
        u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = uv; nt.links.new(u.outputs["UV"], t.inputs["Vector"])
        return t
    bc, nm, orm = tx("BaseColor", False), tx("NormalGL", True), tx("ORM", True)
    sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(orm.outputs["Color"], sp.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.5
    nt.links.new(bc.outputs["Color"], mx.inputs["A"]); nt.links.new(sp.outputs["Red"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"]); nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
    nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.uv_map = uv
    nt.links.new(nm.outputs["Color"], nmap.inputs["Color"]); nt.links.new(nmap.outputs["Normal"], b.inputs["Normal"])
    if "Coat Weight" in b.inputs:                                  # polished marble: a thin clear coat, kept for Blender only
        b.inputs["Coat Weight"].default_value = 0.0
    return m


# ------------------------------------------------------------------ bake
def bake(low, highs, size, kind, path, cage=0.03, dist=0.06, samples=64, uv="UV0_Bake", margin=16, slots=None):
    """Selected-to-active bake into one image. slots: the material slot indices that receive it (others bake into a
    scratch image, so a separately textured section such as a clock dial is not painted over)."""
    Wp, Hp = size
    im = bpy.data.images.get(os.path.basename(path))
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(os.path.basename(path), Wp, Hp, alpha=False, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    scratch = bpy.data.images.get("BAKE_scratch") or bpy.data.images.new("BAKE_scratch", 64, 64, float_buffer=True)
    for i, slot in enumerate(low.material_slots):
        nt = slot.material.node_tree
        n = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.name == "BAKE_TARGET"), None)
        if n is None:
            n = nt.nodes.new("ShaderNodeTexImage"); n.name = "BAKE_TARGET"
        n.image = im if (slots is None or i in slots) else scratch; nt.nodes.active = n
    sc = bpy.context.scene; sc.cycles.samples = samples
    keep = set(highs) | {low}
    saved = {o.name: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o not in keep
    bpy.ops.object.select_all(action="DESELECT")
    for h in highs:
        h.select_set(True)
    low.select_set(True); bpy.context.view_layer.objects.active = low
    t = time.time()
    bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=cage, max_ray_distance=dist, margin=margin,
                        normal_space="TANGENT", uv_layer=uv, target="IMAGE_TEXTURES", use_clear=True)
    for o in bpy.data.objects:
        if o.name in saved:
            o.hide_render = saved[o.name]
    im.filepath_raw = path; im.file_format = "OPEN_EXR"; im.save()
    log("BAKED", kind, os.path.basename(path), Wp, Hp, round(time.time() - t, 1), "s")
    return path


def exr(path):
    im = bpy.data.images.load(path, check_existing=False)
    a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)[::-1]
    bpy.data.images.remove(im)
    return a


def png(a, name, srgb=False):
    """Save an (H, W, 3) linear array (row 0 = top) as an 8-bit PNG; srgb=True encodes it for a colour map."""
    a = np.clip(a, 0, 1)
    if srgb:
        a = np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)
    Hh, Ww = a.shape[:2]
    im = bpy.data.images.new(name, Ww, Hh, alpha=True, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    rgba = np.concatenate([a[::-1], np.ones((Hh, Ww, 1), np.float32)], -1)
    im.pixels.foreach_set(rgba.astype(np.float32).ravel())
    p = os.path.join(TEX, name)
    im.filepath_raw = p; im.file_format = "PNG"
    sc = bpy.context.scene
    sc.render.image_settings.color_depth = "8"
    im.save()
    bpy.data.images.remove(im)
    return p


def smart_uv(ob, margin=0.003, angle=60):
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    me = ob.data
    if not me.uv_layers.get("UV0_Bake"):
        me.uv_layers.new(name="UV0_Bake")
    me.uv_layers.active = me.uv_layers["UV0_Bake"]
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


# ------------------------------------------------------------------ mantel
MT = S.MANTEL
HW = MT["width"] / 2                      # 1.00
LEG_O, LEG_I = HW - MT["shelf_over"], HW - MT["shelf_over"] - MT["leg_w"]      # 0.94, 0.67
FZ0, FZ1 = MT["frieze"]                   # 1.00, 1.245
SH0, SH1 = FZ1, FZ1 + MT["shelf_t"]       # 1.245, 1.32
SHELF_D = 0.34
OPEN_HW = 0.46; OPEN_H = 0.84            # fire opening in the slip
SLIP_Y = 0.165                           # slip face, 35 mm behind the frieze face
FRIEZE_Y = 0.20; BLOCK_Y = 0.245; LEG_Y = MT["leg_d"]
CORB_Z = (MT["plinth_h"], FZ1)
CORB_HW = 0.095


def mantel_parts(high):
    """Returns {name: (part or object builder)} for the mantel; marble = mat 0, black slip = mat 1."""
    c = coll("MO01 | High" if high else "MO01 | Low")
    objs = []
    # plinths, legs (shafts), leg blocks, frieze body, slip
    p = G.empty()
    for sx in (-1, 1):
        x0, x1 = sorted((sx * LEG_I, sx * LEG_O))
        G.box(p, x0 - 0.015, x1 + 0.015, 0.0, LEG_Y + 0.018, 0.0, MT["plinth_h"], 0, skip=("-y", "-z"))
        G.box(p, x0, x1, 0.0, LEG_Y, MT["plinth_h"], FZ0, 0, skip=("-y", "-z", "+z"))
        G.box(p, x0 - 0.01, x1 + 0.01, 0.0, BLOCK_Y, FZ0, FZ1, 0, skip=("-y",))
    G.box(p, -LEG_I, LEG_I, 0.0, FRIEZE_Y, FZ0, FZ1, 0, skip=("-y", "-x", "+x", "+z"))
    blocks = obj_from_part("MT_Blocks", p, c)
    objs.append(bevel(blocks, 0.006 if high else 0.003, 4 if high else 1))
    # the black-marble slip with its fire opening; reveal back to the firebox
    p = G.empty()
    G.frame_with_hole(p, -LEG_I, LEG_I, 0.0, FZ0, -OPEN_HW, OPEN_HW, 0.0, OPEN_H, SLIP_Y, 1, normal_y=1)
    for a, b in (((-OPEN_HW, 0.0), (-OPEN_HW, OPEN_H)), ((OPEN_HW, OPEN_H), (OPEN_HW, 0.0))):
        q = [(a[0], SLIP_Y, a[1]), (b[0], SLIP_Y, b[1]), (b[0], 0.0, b[1]), (a[0], 0.0, a[1])]
        G.add(p, q, [(0, 1, 2, 3)], 1)
    G.add(p, [(-OPEN_HW, 0.0, OPEN_H), (OPEN_HW, 0.0, OPEN_H), (OPEN_HW, SLIP_Y, OPEN_H), (-OPEN_HW, SLIP_Y, OPEN_H)], [(0, 1, 2, 3)], 1)
    G.orient(p, start=len(p["faces"]) - 3, ref_point=(0.0, SLIP_Y / 2, OPEN_H * 0.45))
    slip = obj_from_part("MT_Slip", p, c)
    objs.append(bevel(slip, 0.004 if high else 0.002, 3 if high else 1, angle=50))
    # shelf (moulded front and returns) and bed mould, frieze bead
    prof = G.chaikin(G.SHELF_EDGE, 4 if high else 1)
    core = [(-HW + 0.05, 0.0), (-HW + 0.05, SHELF_D - 0.05), (HW - 0.05, SHELF_D - 0.05), (HW - 0.05, 0.0)]
    v, f = G.sweep_open(core, [(w, SH0 + h) for w, h in prof])
    p = G.empty(); G.add(p, v, f, 0)
    G.add(p, [(-HW + 0.05, 0.0, SH1), (HW - 0.05, 0.0, SH1), (HW - 0.05, SHELF_D - 0.05, SH1), (-HW + 0.05, SHELF_D - 0.05, SH1)], [(0, 3, 2, 1)], 0)
    G.add(p, [(-HW + 0.05, 0.0, SH0), (HW - 0.05, 0.0, SH0), (HW - 0.05, SHELF_D - 0.05, SH0), (-HW + 0.05, SHELF_D - 0.05, SH0)], [(0, 1, 2, 3)], 0)
    G.orient(p, ref_point=(0.0, 0.12, (SH0 + SH1) / 2))
    objs.append(obj_from_part("MT_Shelf", p, c, sharp=50))
    bed = G.chaikin(G.BED, 4 if high else 1)
    path = [(-LEG_O - 0.01, 0.0), (-LEG_O - 0.01, BLOCK_Y), (-LEG_I + 0.01, BLOCK_Y), (-LEG_I + 0.01, FRIEZE_Y),
            (LEG_I - 0.01, FRIEZE_Y), (LEG_I - 0.01, BLOCK_Y), (LEG_O + 0.01, BLOCK_Y), (LEG_O + 0.01, 0.0)]
    v, f = G.sweep_open(path, [(w, SH0 + h) for w, h in bed])
    p = G.empty(); G.add(p, v, f, 0)
    G.orient(p, ref_point=(0.0, 0.05, SH0 - 0.02))
    objs.append(obj_from_part("MT_Bed", p, c, sharp=50))
    bead = G.chaikin(G.BEAD, 4 if high else 1)
    v, f = G.sweep_open([(-LEG_I + 0.01, FRIEZE_Y - 0.004), (LEG_I - 0.01, FRIEZE_Y - 0.004)], [(w, FZ0 + 0.012 + h) for w, h in bead])
    p = G.empty(); G.add(p, v, f, 0)
    G.orient(p, ref_point=(0.0, FRIEZE_Y - 0.03, FZ0 + 0.012))
    objs.append(obj_from_part("MT_Bead", p, c, sharp=60))
    # S-scroll consoles: front surface swept across x, flat sides filled from the outline, volutes on the sides
    n = 90 if high else 40
    outl = G.corbel_outline(CORB_Z[0], CORB_Z[1], n=n)
    for sx in (-1, 1):
        cx = sx * (LEG_I + LEG_O) / 2
        xs = np.linspace(cx - CORB_HW, cx + CORB_HW, 24 if high else 2)
        verts, faces = [], []
        for i, x in enumerate(xs):
            for (yy, zz) in outl:
                verts.append((x, LEG_Y + yy, zz))
        m = len(outl)
        for i in range(len(xs) - 1):
            for k in range(m - 1):
                a = i * m + k
                faces.append((a, a + 1, a + m + 1, a + m))
        p = G.empty(); G.add(p, verts, faces, 0)
        G.orient(p, start=0, out_dir=(0, 1, 0))                         # front strip faces away from the leg
        n_front = len(p["faces"])
        # sides: polygon of the outline closed along the leg face
        for side, x in ((-1, xs[0]), (1, xs[-1])):
            ring = [(x, LEG_Y + yy, zz) for yy, zz in outl] + [(x, LEG_Y - 0.001, CORB_Z[1]), (x, LEG_Y - 0.001, CORB_Z[0])]
            k0 = len(p["faces"])
            G.add(p, ring, [tuple(range(len(ring)))], 0)
            G.orient(p, start=k0, out_dir=(side, 0, 0))
        for zc, yc, sz in ((CORB_Z[0], outl[0][0], -1), (CORB_Z[1], outl[-1][0], 1)):
            k0 = len(p["faces"])
            G.add(p, [(xs[0], LEG_Y - 0.001, zc), (xs[-1], LEG_Y - 0.001, zc), (xs[-1], LEG_Y + yc, zc), (xs[0], LEG_Y + yc, zc)], [(0, 1, 2, 3)], 0)
            G.orient(p, start=k0, out_dir=(0, 0, sz))
        ob = obj_from_part(f"MT_Console_{'R' if sx > 0 else 'L'}", p, c, sharp=50)
        # make the side n-gons render cleanly
        bm = bmesh.new(); bm.from_mesh(ob.data)
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="EAR_CLIP")
        bm.to_mesh(ob.data); bm.free()
        objs.append(bevel(ob, 0.004 if high else 0.002, 3 if high else 1, angle=45))
    return objs


def mantel_carving(c):
    """High-only displaced carvings: crest on the frieze, rosettes on the leg blocks, acanthus drops on the consoles,
    raised volute ribbons on the console sides."""
    out = []
    h, size = heightfield("Crest")
    sc_ = 0.66 / size[0]
    out.append(hf_grid("MT_Carve_Crest", h, size, sc_, c, lambda u, v, d: np.stack([u, FRIEZE_Y + d, (FZ0 + FZ1) / 2 + 0.004 + v], -1), pool=1))
    h, size = heightfield("Rosette")
    for sx in (-1, 1):
        cx = sx * (LEG_I - 0.14)
        out.append(hf_grid(f"MT_Carve_Rosette_{sx}", h, size, 0.17 / size[0], c,
                           lambda u, v, d, cx=cx: np.stack([cx + u, FRIEZE_Y + d, (FZ0 + FZ1) / 2 + 0.004 + v], -1), pool=1, exag=0.8))
    # acanthus drop on the console front: map v along the curve (arc length), u across, d along the curve normal
    h, size = heightfield("Drop")
    outl = np.array(G.corbel_outline(CORB_Z[0], CORB_Z[1], n=400))
    seg = np.r_[0, np.cumsum(np.hypot(np.diff(outl[:, 0]), np.diff(outl[:, 1])))]
    L = seg[-1]
    for sx in (-1, 1):
        cx = sx * (LEG_I + LEG_O) / 2
        sc_ = min(0.130 / size[0], (L * 0.62) / size[1])
        def frame(u, v, d, cx=cx, sc_=sc_):
            s = np.clip(L * 0.50 + v, 0, L)                       # v: centred on the console length (up = +v)
            y = np.interp(s, seg, outl[:, 0]); z = np.interp(s, seg, outl[:, 1])
            ty = np.gradient(outl[:, 0]); tz = np.gradient(outl[:, 1]); tn = np.hypot(ty, tz)
            ny = np.interp(s, seg, tz / tn); nz = np.interp(s, seg, -ty / tn)
            return np.stack([cx + u, LEG_Y + y + ny * d, z + nz * d], -1)
        out.append(hf_grid(f"MT_Carve_Drop_{sx}", h, size, sc_, c, frame, pool=1, exag=1.3))
    # volute ribbons on each console side (half-round 9 mm cord along a spiral)
    for sx in (-1, 1):
        cx = sx * (LEG_I + LEG_O) / 2
        for side in (-1, 1):
            x = cx + side * (CORB_HW + 0.0004)
            H_ = CORB_Z[1] - CORB_Z[0]
            for (vcz, r0, turns) in ((CORB_Z[0] + 0.80 * H_, 0.080, 1.75), (CORB_Z[0] + 0.07 * H_, 0.040, 1.5)):
                y_out = np.interp(vcz, [z for _, z in G.corbel_outline(CORB_Z[0], CORB_Z[1])], [y for y, _ in G.corbel_outline(CORB_Z[0], CORB_Z[1])])
                cy = LEG_Y + y_out - r0 - 0.006
                pts = G.volute(cy, vcz, r0, turns=turns, n=140, sign=1 if vcz > 1 else -1)
                verts, faces = [], []
                k = 10
                for i, (py, pz) in enumerate(pts):
                    if i == 0:
                        ty_, tz_ = pts[1][0] - py, pts[1][1] - pz
                    else:
                        ty_, tz_ = py - pts[i - 1][0], pz - pts[i - 1][1]
                    tl = math.hypot(ty_, tz_) or 1; ny_, nz_ = -tz_ / tl, ty_ / tl
                    rr = 0.0055 * (1 - 0.55 * i / len(pts))
                    for j in range(k + 1):
                        a = math.pi * j / k
                        verts.append((x + side * math.sin(a) * rr, py + math.cos(a) * rr * ny_, pz + math.cos(a) * rr * nz_))
                for i in range(len(pts) - 1):
                    for j in range(k):
                        a_ = i * (k + 1) + j
                        faces.append((a_, a_ + 1, a_ + k + 2, a_ + k + 1) if side > 0 else (a_, a_ + k + 1, a_ + k + 2, a_ + 1))
                p = G.empty(); G.add(p, verts, faces, 0)
                G.orient(p, out_dir=(side, 0, 0))
                out.append(obj_from_part(f"MT_Volute_{sx}_{side}_{vcz:.2f}", p, c, sharp=0))
    return out


def mantel():
    log("mantel: high")
    hi = mantel_parts(True) + mantel_carving(coll("MO01 | High"))
    log("mantel: low")
    lo_parts = mantel_parts(False)
    low = join(lo_parts, "SM_MO01_Mantel")
    for p in low.data.polygons:
        p.use_smooth = True
    low.data.set_sharp_from_angle(angle=math.radians(40))
    smart_uv(low, margin=0.002, angle=55)
    marble_tile = REC["Marble"]["tile_m"]; black_tile = REC["BlackMarble"]["tile_m"]
    INFO["mantel"] = dict(low_tris=tris(low), high_tris=sum(tris(o) for o in hi), maps="4096 BaseColor/NormalGL, 2048 ORM")
    log("mantel tris", INFO["mantel"])
    if not NOBAKE:
        bm = [bpy.data.materials.new("BAKE_low")]
        low.data.materials.clear(); low.data.materials.append(bm[0])
        low.data.polygons.foreach_set("material_index", np.zeros(len(low.data.polygons), np.int32))

        def set_high(mode):
            ma = mat_box(f"BAKE_marble_{mode}", "T_MO01_Marble", mode, marble_tile)
            mb = mat_box(f"BAKE_black_{mode}", "T_MO01_BlackMarble", mode, black_tile)
            for o in hi:                                   # assign into the slots: clearing them resets face indices to 0
                while len(o.data.materials) < 2:
                    o.data.materials.append(None)
                o.data.materials[0] = ma; o.data.materials[1] = mb
        set_high("shade")
        bake(low, hi, (4096, 4096), "NORMAL", os.path.join(BAKE, "Mantel_Normal.exr"), samples=1)
        set_high("bc")
        bake(low, hi, (4096, 4096), "EMIT", os.path.join(BAKE, "Mantel_BaseColor.exr"), samples=1)
        set_high("rough")
        bake(low, hi, (2048, 2048), "EMIT", os.path.join(BAKE, "Mantel_Rough.exr"), samples=1)
        set_high("shade")
        bake(low, hi, (2048, 2048), "AO", os.path.join(BAKE, "Mantel_AO.exr"), samples=48)
        n = exr(os.path.join(BAKE, "Mantel_Normal.exr"))[..., :3]
        png(n, "T_MO01_Mantel_NormalGL.png")
        png(exr(os.path.join(BAKE, "Mantel_BaseColor.exr"))[..., :3], "T_MO01_Mantel_BaseColor.png", srgb=True)
        ao = exr(os.path.join(BAKE, "Mantel_AO.exr"))[..., 0]; ro = exr(os.path.join(BAKE, "Mantel_Rough.exr"))[..., 0]
        png(np.stack([ao, ro, np.zeros_like(ro)], -1), "T_MO01_Mantel_ORM.png")
    low.data.materials.clear(); low.data.materials.append(mat_unique("M_MO01_Mantel", "T_MO01_Mantel"))
    low.data.polygons.foreach_set("material_index", np.zeros(len(low.data.polygons), np.int32))
    return low, hi


def preview(objs_hi, low, name, views=(("front", (0, 4.2, 0.75), (90, 0, 180)), ("oblique", (2.6, 3.0, 1.2), (78, 0, 140)),
                                          ("close", (0.95, 1.1, 1.05), (80, 0, 150)))):
    """Workbench-free quick look in EEVEE: high on the left (x - 1.2), low on the right (x + 1.2)."""
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    for o in objs_hi:
        o.hide_render = False; o.location.x -= 1.2
    low.location.x += 1.2; low.hide_render = False
    w = bpy.data.worlds.new("pv"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    for nm, loc, rot in (("k", (2.5, 3.5, 3.0), (55, 0, 140)), ("f", (-3.0, 2.0, 1.5), (70, 0, -120))):
        L = bpy.data.lights.new(nm, "AREA"); L.energy = 600 if nm == "k" else 200; L.size = 2.0
        lo = bpy.data.objects.new(nm, L); lo.location = loc; lo.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(lo)
    cam = bpy.data.cameras.new("pv"); cam.lens = 35; co = bpy.data.objects.new("pv", cam); sc.collection.objects.link(co); sc.camera = co
    clay = bpy.data.materials.new("clay"); clay.use_nodes = True
    bsdf = clay.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value = (0.75, 0.73, 0.70, 1); bsdf.inputs["Roughness"].default_value = 0.45
    saved = {}
    for o in objs_hi + [low]:
        saved[o.name] = list(o.data.materials); o.data.materials.clear(); o.data.materials.append(clay)
    out = []
    for vn, loc, rot in views:
        co.location = loc; co.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = os.path.join(KIT, f"preview_{name}_{vn}.png"); bpy.ops.render.render(write_still=True); out.append(sc.render.filepath)
    for o in objs_hi + [low]:
        o.data.materials.clear()
        for m in saved[o.name]:
            o.data.materials.append(m)
        o.location.x = 0.0
    log("PREVIEW", out)


def preview_set(objs, name, views):
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
    w = bpy.data.worlds.new("pv"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    for nm, loc, rot in (("k", (2.5, 4.0, 3.5), (50, 0, 150)), ("f", (-3.0, 3.0, 1.5), (70, 0, -130))):
        L = bpy.data.lights.new(nm, "AREA"); L.energy = 900 if nm == "k" else 300; L.size = 2.0
        lo = bpy.data.objects.new(nm, L); lo.location = loc; lo.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(lo)
    cam = bpy.data.cameras.new("pv"); cam.lens = 30; co = bpy.data.objects.new("pv", cam); sc.collection.objects.link(co); sc.camera = co
    for vn, loc, rot in views:
        co.location = loc; co.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = os.path.join(KIT, f"preview_{name}_{vn}.png"); bpy.ops.render.render(write_still=True)
    log("PREVIEW", name)


def preview_props(made):
    """The candelabra and the clock side by side on a mantel-like ledge (EEVEE); objects are put back afterwards."""
    objs = [made[k] for k in ("candelabra", "clock") if k in made]
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in objs
    xs = {"candelabra": -0.16, "clock": 0.16}
    for k in ("candelabra", "clock"):
        if k in made:
            made[k].location.x = xs[k]
    ledge = bpy.data.materials.new("pv_ledge"); ledge.use_nodes = True
    ledge.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.72, 0.66, 1)
    wall = bpy.data.materials.new("pv_wall"); wall.use_nodes = True
    wall.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.10, 0.12, 0.08, 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.02)); g = bpy.context.active_object; g.scale = (1.2, 0.5, 0.04); g.data.materials.append(ledge)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.2, 0.5), rotation=(math.pi / 2, 0, 0)); w = bpy.context.active_object; w.scale = (1.4, 1.2, 1); w.data.materials.append(wall)
    preview_set(objs + [g, w], "props", (("front", (0.0, 1.25, 0.32), (84, 0, 180)), ("clock", (0.28, 0.42, 0.22), (82, 0, 160)),
                                         ("candelabra", (-0.05, 0.48, 0.45), (72, 0, 200))))
    for k in ("candelabra", "clock"):
        if k in made:
            made[k].location.x = 0.0
    for o in (g, w):
        bpy.data.objects.remove(o, do_unlink=True)


def preview_books(made, B):
    """Two south bays of row modules on plain shelves against a dark back, front and close views (EEVEE)."""
    rows = made["rows"]
    keep = []
    back = bpy.data.materials.new("pv_back"); back.use_nodes = True
    back.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.04, 0.025, 1)
    for bay in range(2):
        x0 = bay * (B.BAYS["South"] + 0.11)
        for r in range(6):
            cls = B.ROW_CLASS[r]
            nm = f"SM_MO01_BookRow_South_{cls}_{(bay * 2 + r) % B.VARIANTS[('South', cls)]:02d}"
            o = bpy.data.objects.new(f"pv_{bay}_{r}", rows[nm].data); bpy.context.scene.collection.objects.link(o)
            o.location = (x0, 0.0, B.SHELF_Z[r] - B.SHELF_Z[0]); keep.append(o)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x0 + B.BAYS["South"] / 2, -0.15, B.SHELF_Z[r] - B.SHELF_Z[0] - 0.014))
            sh = bpy.context.active_object; sh.scale = (B.BAYS["South"] + 0.11, 0.33, 0.028); sh.data.materials.append(back); keep.append(sh)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.8, -0.31, 1.2), rotation=(math.pi / 2, 0, 0)); bp = bpy.context.active_object
    bp.scale = (2.0, 2.6, 1); bp.data.materials.append(back); keep.append(bp)
    for o in bpy.data.objects:
        if o.type == "MESH" and o not in keep:
            o.hide_render = True
    preview_set(keep, "books", (("front", (0.85, 2.6, 1.1), (88, 0, 180)), ("close", (0.55, 0.75, 1.05), (84, 0, 158)),
                                ("low", (0.35, 0.55, 0.62), (68, 0, 165))))


def main():
    setup()
    made = {}
    if "mantel" in ONLY:
        made["mantel"] = mantel()
        if "--preview" in ARGS:
            preview(made["mantel"][1], made["mantel"][0], "mantel")
    if "drapes" in ONLY:
        import mo01_drapes
        made["drapes"] = mo01_drapes.build(sys.modules[__name__])
        if "--preview" in ARGS:
            import mo01_cloth as C
            lows = [o for k, o in made["drapes"].items() if k.endswith("_N") or k.endswith("_N_L") or k.endswith("_N_R")
                    or k in ("DrapeSide_L", "DrapeSide_R", "Sheer")]
            for o in bpy.data.collections["MO01 | High"].objects:
                o.hide_render = True
            # context: the wall, the arched architrave line and the pelmet board
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 1.9), rotation=(math.pi / 2, 0, 0)); wall = bpy.context.active_object
            wall.scale = (4.0, 3.8, 1)
            cu = bpy.data.curves.new("arch", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.035
            sp = cu.splines.new("POLY"); pts = [(-C.A_HALF - 0.035, 0.03, 0.9)] + [(x, 0.03, z) for x, z in (C.arch_xz("N", t / 60) for t in range(61))] + [(C.A_HALF + 0.035, 0.03, 0.9)]
            sp.points.add(len(pts) - 1)
            for p_, q in zip(sp.points, pts):
                p_.co = (*q, 1)
            arch = bpy.data.objects.new("arch", cu); bpy.context.scene.collection.objects.link(arch)
            pel = []
            for t in range(61):
                x, z = C.pelmet_xz("N", t / 60)
                pel.append(((x, C.PELMET["front"], z), (x, C.PELMET["front"], z + C.PELMET["h"]), (x, 0.0, z + C.PELMET["h"]), (x, 0.0, z)))
            V = [v for ring in pel for v in ring]; Fq = []
            for i in range(60):
                for k in range(4):
                    a_, b_ = i * 4 + k, i * 4 + (k + 1) % 4
                    Fq.append((a_, b_, b_ + 4, a_ + 4))
            me = bpy.data.meshes.new("pelmet"); me.from_pydata(V, [], Fq); pob = bpy.data.objects.new("pelmet", me); bpy.context.scene.collection.objects.link(pob)
            for o in (wall, arch, pob):
                mm = bpy.data.materials.new("ctx_" + o.name); mm.use_nodes = True
                mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.27, 0.2, 1) if o is wall else (0.8, 0.78, 0.72, 1) if o is arch else (0.12, 0.16, 0.11, 1)
                o.data.materials.append(mm)
            keep = set(lows) | {wall, arch, pob}
            for o in bpy.data.objects:
                if o.type == "MESH" and o not in keep:
                    o.hide_render = True
            preview_set(lows + [wall, arch, pob], "drapes", (("front", (0, 6.0, 2.2), (88, 0, 180)), ("oblique", (3.4, 3.6, 2.4), (80, 0, 137)),
                                                             ("swag", (0.9, 2.4, 2.9), (83, 0, 158))))
    for nm in ("candelabra", "clock"):
        if nm in ONLY:
            import mo01_props
            made[nm] = getattr(mo01_props, nm)(sys.modules[__name__])[0]
    if "--preview" in ARGS and {"candelabra", "clock"} & set(ONLY):
        preview_props(made)
    if "books" in ONLY:
        import mo01_books
        made["books"] = mo01_books.build(sys.modules[__name__])
        if "--preview" in ARGS:
            preview_books(made["books"], mo01_books)
    # save the game kit (low meshes) and the source (high)
    hi_c = bpy.data.collections.get("MO01 | High")
    if hi_c:
        for o in hi_c.objects:
            o.hide_render = True; o.hide_set(True)
    ki = os.path.join(KIT, "Kit_Info.json")
    old = json.load(open(ki)) if os.path.exists(ki) else {}
    old.update(INFO)
    json.dump(old, open(ki, "w"), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(KIT, f"MO01_Kit_{'_'.join(ONLY)}.blend"))
    log("KIT OK", INFO)


if __name__ == "__main__":
    main()
