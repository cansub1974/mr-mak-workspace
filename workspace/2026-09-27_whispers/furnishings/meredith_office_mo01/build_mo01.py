"""MO01 Meredith's office: build into the MS02 master (Blender, background).

    blender -b --factory-startup Hotel_Eden_Master_MS02.blend --python build_mo01.py -- [--save] [--render[=views]]
Owner, 12 Nov 2026: "Use the attached reference image to model the interior of Meredith's office. The layout is not
identical but use the reference as close as possible. Same rules as the executive corridor. This is a hero room so it
must be high quality game assets. Do not model the furniture. That will be done separately. You can place temporary
furniture to test the layout. Blender first until I receive it."

Owner, 12 Nov 2026 (second review): "Add a couple of the Executive Corridor's sconces into the room for lighting. Let's
see the single swag.Keep the wallpaper colour. Model the books, candalabra and the clock in final game model quality
and deliver them with the room. Keep the windows."

Owner, 12 Nov 2026 (third review): "Just make the area rug larger and a bit more vibrant/less worn. Remove the temporary
furniture. In the corner straight across from the door, remove the temp stuff and add in a copy of the ferns from the
lobby, scaled down to fit the room."

Builds "MO01 | Meredith office" (re-running replaces it; nothing else in the master changes, checked by inventory):
  walls      EC01 dado system (mahogany framework, veneer raised fields, skirting, dado rail on the EC01 trim sheet),
             the PW01 damask recoloured after the reference, a painted plaster cornice (EC01 cornice at 0.56 scale)
  fireplace  a chimney breast on the west wall with a brick-lined firebox, the baked marble mantel (kit), a marble hearth,
             the approved G01 grate and fuel; a brass picture light over the portrait
  bookcases  south wall (6 bays, brass ladder rail and a rolling library ladder) and the alcove (3 bays): fluted
             pilasters, panelled cupboards, shelves, frieze and crown; repeated parts are shared meshes
  windows    arched painted architraves round the approved I06 surrounds (the hotel's own Gothic windows, kept); a
             single swag with pleated tails and bullion fringe on an arched pelmet, velvet curtains and sheers hung
             inside the arch (kit: tailored swag and tails, cloth-simulated curtains and sheers, baked)
  door       an office-side mahogany architrave on the EC01 door D-MO-24
  floor      herringbone parquet; the AIC Ushak rug (CC0, 5.30 x 3.53 m, restored a little) with the approved Carpet001 pile
  portraits  three AIC CC0 portraits in the approved AF02 frame
  books      book-row modules (kit, 192 period volumes on one 2K atlas) on every open shelf, instanced so that no row
             repeats beside or above itself; five volumes on the mantel
  mantel     a pair of five-light brass candelabra and an arch-top mahogany clock (kit, baked), after the reference
  lighting   game-rule fixtures: Fireplace (Point 1500 lm 1900 K), four WindowFill (Rect 3000 lm 5500 K), PictureLight
             (WallSconce rule, Spot 400 lm 2700 K), and two EC01 S06 sconces on the chimney breast with the corridor's
             Unreal profile (Point 1400 lm 2700 K)
  colliders  UCX boxes: chimney breast, mantel, both bookcases
  palm       the lobby's approved stair palm (FUR-024 P03, the master's own meshes, shared) at its own size in the north-east
             corner, across from the door; every frond 30 mm or more clear of the walls and the window dressing (checked)
No furniture: it comes separately (the TEMP layout-test furniture was removed at the third review).
Plan (x, y) -> model (x, -y). Heights above the Level 3 floor top, Z 9.004.
"""
import bpy, bmesh, json, math, os, sys, time, hashlib, array, random
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
EC_DIR = os.path.join(HERE, "..", "executive_corridor_ec01")
sys.path.insert(0, HERE); sys.path.insert(1, EC_DIR)
import mo01_spec as S
import ec01_geom as G
import ec01_mats as M

WS = os.path.abspath(os.path.join(HERE, "..", ".."))
W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
TEX = os.path.join(W, "textures"); KIT = os.path.join(W, "kit")
EC_TEX = "D:/AI_Modelling/hotel_eden/working/executive_EC01/textures"
RM = os.path.join(WS, "review-media", "meredith-office-mo01"); BUILD = os.path.join(RM, "build"); os.makedirs(BUILD, exist_ok=True)
AF02_BLEND = os.path.join(WS, "approved-media", "artwork-af02", "AF02_Game.blend")
G01_BLEND = os.path.join(WS, "approved-media", "furnishings-g01", "Hotel_Eden_Fireplace_G01_Game.blend")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MASTER = "D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend"
assert os.path.normcase(os.path.abspath(bpy.data.filepath)) == os.path.normcase(os.path.abspath(MASTER)), bpy.data.filepath
REC = json.load(open(os.path.join(W, "Material_Recipes.json")))
TRIM_ROWS = {k: tuple(v) for k, v in json.load(open("D:/AI_Modelling/hotel_eden/working/executive_EC01/kit/Kit_Info.json"))["trim"]["rows"].items()}
FL = S.FL; CEIL = S.CEIL
ROOT = "MO01 | Meredith office"; TEMP = "MO01 | TEMP furniture (not for export)"     # TEMP: removed builds only
SUB = ["MO01 | Walls", "MO01 | Fireplace", "MO01 | Bookcases", "MO01 | Windows", "MO01 | Door", "MO01 | Floor and ceiling",
       "MO01 | Portraits", "MO01 | Books and mantel", "MO01 | Decoration", "MO01 | Furniture", "MO01 | Lighting", "MO01 | Colliders"]
KITS = dict(drapes=os.path.join(KIT, "MO01_Kit_drapes.blend"), books=os.path.join(KIT, "MO01_Kit_books.blend"),
            props=os.path.join(KIT, "MO01_Kit_candelabra_clock.blend"))
EC_KIT = "D:/AI_Modelling/hotel_eden/working/executive_EC01/kit"
CORNICE_K = 0.56
CORNICE_BED = CEIL - 0.536 * CORNICE_K          # 3.896
PAPER = (0.95, CORNICE_BED)
WIN_ARCH_K = 0.70                               # window architrave: EC01 Architrave at 70 mm
# clearances from the hotel's own shell (Unreal port, 12 Nov): at 1 mm the office ceiling z-fought the hotel's interior shell
# (dark timber) in Unreal; the paper stands 3 mm off the wall, the ceiling plane 10 mm under the shell's ceiling
PAPER_OFF, CEIL_DROP = 0.003, 0.010
A_HALF = 1.067
ARCH = {"N": dict(spring=11.61 - FL, apex=12.77 - FL, sill=10.14 - FL), "E": dict(spring=11.35 - FL, apex=12.47 - FL, sill=9.94 - FL)}
OUT = dict(revision="MO01", date="2026-11-12", items={})
t0 = time.time()


def log(*a):
    print(f"[{time.time() - t0:7.1f}s]", *a, flush=True)


# ------------------------------------------------------------------ frames
class Run:
    def __init__(self, name, a, b, n):
        self.name = name
        N = Vector((n[0], -n[1], 0)); U = N.cross(Vector((0, 0, 1)))
        d = Vector((b[0] - a[0], -(b[1] - a[1]), 0))
        if d.dot(U) < 0:
            a, b = b, a
        self.a, self.b = a, b
        self.L = math.hypot(b[0] - a[0], b[1] - a[1])
        self.A = Vector((a[0], -a[1], FL)); self.U = U; self.N = N; self.Z = Vector((0, 0, 1))

    def w(self, s, d, z):
        return self.A + self.U * s + self.N * d + self.Z * z

    def matrix(self, s, d, z):
        m = Matrix((self.U, self.N, self.Z)).transposed().to_4x4(); m.translation = self.w(s, d, z); return m


LOOP = [(17.1, 6.7), (25.7, 6.7), (25.7, 0.3), (17.1, 0.3), (17.1, 3.25), (17.62, 3.25), (17.62, 5.75), (17.1, 5.75)]
RUN_DEF = [("S", (17.1, 6.7), (25.7, 6.7), (0, -1)), ("E", (25.7, 6.7), (25.7, 0.3), (-1, 0)), ("N", (25.7, 0.3), (17.1, 0.3), (0, 1)),
           ("WN", (17.1, 0.3), (17.1, 3.25), (1, 0)), ("BN", (17.1, 3.25), (17.62, 3.25), (0, -1)),
           ("BF", (17.62, 3.25), (17.62, 5.75), (1, 0)), ("BS", (17.62, 5.75), (17.1, 5.75), (0, 1)), ("WS", (17.1, 5.75), (17.1, 6.7), (1, 0))]
RUNS = {n: Run(n, a, b, nn) for n, a, b, nn in RUN_DEF}
for n, a, b, nn in RUN_DEF:                          # the loop order and the run directions must agree
    assert (RUNS[n].a, RUNS[n].b) == (a, b), n
CASE_S = (S.CASE_SOUTH["x0"] - 17.1, S.CASE_SOUTH["x1"] - 17.1)           # run S, s 0-5.40
CASE_A = (0.0, RUNS["WN"].L)                                               # run WN, the whole alcove
DOOR_ARCH = (23.15 - 17.1 - 0.10, 24.75 - 17.1 + 0.10)                     # run S, s 5.95-7.75
MANTEL_S = (S.FIRE_C - 3.25 - 1.0 - 0.015, S.FIRE_C - 3.25 + 1.0 + 0.015)  # run BF
WINDOWS = [dict(id="W3-06", run="N", kind="N", s=25.7 - 23.1, plan=(23.1, 0.3)), dict(id="W3-07", run="N", kind="N", s=25.7 - 19.1, plan=(19.1, 0.3)),
           dict(id="E13-W-1", run="E", kind="E", s=6.7 - 5.45, plan=(25.7, 5.45)), dict(id="E13-W-0", run="E", kind="E", s=6.7 - 2.55, plan=(25.7, 2.55))]
# lower finish (skirting, dado framework/fields, dado rail) blocked by full-height joinery, the door and the mantel
LOWER_BLOCK = {"S": [CASE_S, DOOR_ARCH], "N": [(25.7 - 17.1 - S.CASE["base_d"], RUNS["N"].L)], "WN": [CASE_A], "BN": [(0.0, S.CASE["base_d"])],
               "BF": [MANTEL_S], "WS": [(0.95 - S.CASE["base_d"], 0.95)]}
RAIL_BLOCK = {"E": [(w["s"] - A_HALF - 0.08, w["s"] + A_HALF + 0.08) for w in WINDOWS if w["run"] == "E"]}


def arch_sz(kind, t, grow=0.0):
    """Surround outer arch (window frame x, z above the floor), grown outward by `grow`; t 0..1 left springing -> right."""
    a = A_HALF + grow; zs = ARCH[kind]["spring"]; rise = ARCH[kind]["apex"] + grow - zs
    c = (rise * rise - a * a) / (2 * a); R = a + c
    th_apex = math.atan2(rise, -c)
    if t <= 0.5:
        th = math.pi + (th_apex - math.pi) * (t / 0.5)
        return (c + R * math.cos(th), zs + R * math.sin(th))
    x, z = arch_sz(kind, 1 - t, grow)
    return (-x, z)


# ------------------------------------------------------------------ mesh helpers
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); (parent or bpy.context.scene.collection).children.link(c)
    return c


def empty_part():
    return dict(verts=[], faces=[], uv0=[], uv1=[], mat=[])


def add_quad(part, pts, uv1, mat, uv0=None):
    o = len(part["verts"])
    part["verts"] += [tuple(p) for p in pts]
    part["faces"].append(tuple(range(o, o + len(pts))))
    part["uv1"].append(uv1); part["uv0"].append(uv0 or [(0.999, 0.999)] * len(pts)); part["mat"].append(mat)


def add_part(part, sub, mat):
    o = len(part["verts"])
    part["verts"] += [tuple(v) for v in sub["verts"]]
    part["faces"] += [tuple(i + o for i in f) for f in sub["faces"]]
    part["uv0"] += sub["uv0"]; part["uv1"] += sub["uv1"]; part["mat"] += [mat] * len(sub["faces"])


def mesh_obj(name, part, mats, c, sharp=60, smooth=True, uv1_name="UV1_Wood"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in part["verts"]], [], [tuple(f) for f in part["faces"]])
    for key, uvn in (("uv0", "UV0_Bake"), ("uv1", uv1_name)):
        lay = me.uv_layers.new(name=uvn)
        src = part.get(key) or part.get("uv1")
        if src:
            lay.data.foreach_set("uv", np.array([c_ for f in src for uv in f for c_ in uv], np.float32))
    for m in mats:
        me.materials.append(m)
    if part.get("mat"):
        me.polygons.foreach_set("material_index", np.array(part["mat"], np.int32))
    me.polygons.foreach_set("use_smooth", np.full(len(me.polygons), smooth))
    if smooth and sharp:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def place(name, mesh, mat4, c):
    ob = bpy.data.objects.new(name, mesh); ob.matrix_world = mat4; c.objects.link(ob)
    return ob


def wood_uv(q, vertical, tile=1.0, off=(0.0, 0.0)):
    if vertical:
        return [((p[2] + off[0]) / tile, (p[0] + off[1]) / tile) for p in q]
    return [((p[0] + off[0]) / tile, (p[2] + off[1]) / tile) for p in q]


def box_world(part, run, s0, s1, d0, d1, z0, z1, mat, faces=("+d", "-s", "+s", "+z", "-z"), vertical=True, tile=1.0, off=(0.0, 0.0)):
    F = {"+d": [(s0, d1, z0), (s1, d1, z0), (s1, d1, z1), (s0, d1, z1)], "-d": [(s1, d0, z0), (s0, d0, z0), (s0, d0, z1), (s1, d0, z1)],
         "-s": [(s0, d0, z0), (s0, d1, z0), (s0, d1, z1), (s0, d0, z1)], "+s": [(s1, d1, z0), (s1, d0, z0), (s1, d0, z1), (s1, d1, z1)],
         "+z": [(s0, d1, z1), (s1, d1, z1), (s1, d0, z1), (s0, d0, z1)], "-z": [(s0, d0, z0), (s1, d0, z0), (s1, d1, z0), (s0, d1, z0)]}
    want = {"+d": run.N, "-d": -run.N, "-s": -run.U, "+s": run.U, "+z": run.Z, "-z": -run.Z}
    for k in faces:
        q = F[k]; wq = [run.w(*p) for p in q]
        if Vector(G.newell([tuple(v) for v in wq])).dot(want[k]) < 0:
            q = q[::-1]; wq = wq[::-1]
        if k in ("+z", "-z"):
            uv = [((p[0] + off[0]) / tile, (p[1] + off[1]) / tile) for p in q]
        elif k in ("-s", "+s"):
            uv = [((p[2] + off[0]) / tile, (p[1] + off[1]) / tile) for p in q]
        else:
            uv = wood_uv(q, vertical, tile, off)
        add_quad(part, wq, uv, mat)


def world_sweep(path2d, prof, closed, row, z_base=FL, run=None, wall_plane=False, tile=1.0):
    part = G.sweep(path2d, prof, closed=closed, row=row, wood_tile=tile)
    if wall_plane:
        part["verts"] = [tuple(run.w(v[0], v[2], v[1])) for v in part["verts"]]
        G.orient(part, lambda c: tuple(run.N))
    else:
        part["verts"] = [(v[0], v[1], z_base + v[2]) for v in part["verts"]]
        P = path2d + ([path2d[0]] if closed else [])
        def ref(c):
            best, nb = 1e9, (0, 0)
            for a, b in zip(P[:-1], P[1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy + 1e-12
                t = max(0, min(1, ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2))
                dd = (c[0] - a[0] - t * dx) ** 2 + (c[1] - a[1] - t * dy) ** 2
                if dd < best:
                    best, nb = dd, (-dy / math.sqrt(L2), dx / math.sqrt(L2))
            return (nb[0], nb[1], 0.0)
        G.orient(part, ref)
    return part


def end_cap(part, p, dirv, prof, mat, at_start, z_base=FL):
    x, y = p; tx, ty = dirv; L = math.hypot(tx, ty); tx, ty = tx / L, ty / L
    nx, ny = -ty, tx
    pts = [(x + nx * d, y + ny * d, z_base + z) for d, z in prof]
    if prof[0][0] > 1e-6 or prof[-1][0] > 1e-6:
        pts = [(x, y, z_base + prof[0][1])] + pts + [(x, y, z_base + prof[-1][1])]
    want = Vector((-tx, -ty, 0)) if at_start else Vector((tx, ty, 0))
    if Vector(G.newell(pts)).dot(want) < 0:
        pts = pts[::-1]
    add_quad(part, pts, [((q[2] - z_base), math.hypot(q[0] - x, q[1] - y)) for q in pts], mat)


def orient_faces(part, fn):
    """Flip each face whose normal points against fn(face centre) (a direction)."""
    for i, f in enumerate(part["faces"]):
        vs = [part["verts"][k] for k in f]; n = G.newell(vs)
        cc = [sum(v[k] for v in vs) / len(vs) for k in range(3)]
        r = fn(cc)
        if n[0] * r[0] + n[1] * r[1] + n[2] * r[2] < 0:
            part["faces"][i] = tuple(reversed(f)); part["uv0"][i] = list(reversed(part["uv0"][i])); part["uv1"][i] = list(reversed(part["uv1"][i]))
    return part


# ------------------------------------------------------------------ restore / inventory
def restore_previous():
    for nm in [ROOT, TEMP] + SUB:
        c = bpy.data.collections.get(nm)
        if c:
            for o in list(c.all_objects):
                me = o.data
                bpy.data.objects.remove(o, do_unlink=True)
                if isinstance(me, bpy.types.Mesh) and me.users == 0:
                    bpy.data.meshes.remove(me)
    for nm in SUB + [TEMP, ROOT]:
        c = bpy.data.collections.get(nm)
        if c:
            bpy.data.collections.remove(c)
    for m in list(bpy.data.materials):
        if m.users == 0 and m.name.startswith(("M_MO01_", "BAKE_", "M_SofaChesterfield", "M_DeskPedestal", "M_ChairSwivel")):
            bpy.data.materials.remove(m)
    for im in list(bpy.data.images):
        if im.users == 0 and im.name.startswith(("T_MO01_", "BAKE_", "Candelabra_", "Clock_", "T_SofaChesterfield", "T_DeskPedestal", "T_ChairSwivel")):
            bpy.data.images.remove(im)
    for L in list(bpy.data.lights):
        if L.users == 0 and L.name.startswith(("Hotel.MeredithOffice", "MO01 ")):
            bpy.data.lights.remove(L)


def inventory():
    mine = set()
    for nm in [ROOT, TEMP] + SUB:
        c = bpy.data.collections.get(nm)
        if c:
            mine |= {o.name for o in c.all_objects}
    objects = {o.name: [o.type, o.data.name if o.data else None, o.parent.name if o.parent else None,
                        [round(x, 6) for row in o.matrix_world for x in row], sorted(c.name for c in o.users_collection), o.hide_render, o.hide_viewport]
               for o in bpy.data.objects if o.name not in mine}
    meshes = {}
    for m in bpy.data.meshes:
        if m.users == 0 or m.name in APPENDED or m.name.startswith(("SM_MO01", "UCX_SM_MO01", "MO01", "TEMP_")):
            continue
        v = array.array("f", [0]) * (len(m.vertices) * 3); m.vertices.foreach_get("co", v)
        meshes[m.name] = hashlib.sha256(v.tobytes()).hexdigest()
    return {"objects": objects, "meshes": meshes}


# ------------------------------------------------------------------ materials
def img(path, data=True):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = "Non-Color" if data else "sRGB"
    return im


def mat_tiling(name, prefix, tile, uv="UV1_Wood", rough_mul=1.0, normal_strength=1.0, tint=None, alpha=None, extra=None):
    """Tiling PBR on a metre UV (scale 1/tile): BaseColor, NormalGL, ORM (AO into colour 0.5, G roughness)."""
    m, nt, out = M.fresh(name)
    b = M.principled(nt, out)
    def tx(suffix, data, loc):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(os.path.join(TEX, f"{prefix}_{suffix}.png"), data); t.location = loc
        u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = uv
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tile[0], 1 / tile[1], 1) if isinstance(tile, (list, tuple)) else (1 / tile, 1 / tile, 1)
        nt.links.new(u.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    bc = tx("BaseColor", False, (-500, 300)); orm = tx("ORM", True, (-500, 0)); nm = tx("NormalGL", True, (-500, -300))
    s = M.orm_split(nt, orm)
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.5
    nt.links.new(bc.outputs["Color"], mx.inputs["A"]); nt.links.new(s.outputs["Red"], mx.inputs["B"])
    col = mx.outputs["Result"]
    if tint is not None:
        tn = nt.nodes.new("ShaderNodeMix"); tn.data_type = "RGBA"; tn.blend_type = "MULTIPLY"; tn.inputs["Factor"].default_value = 1.0
        tn.inputs["B"].default_value = (*tint, 1); nt.links.new(col, tn.inputs["A"]); col = tn.outputs["Result"]
    if extra == "soot":
        ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Soot"
        sm = nt.nodes.new("ShaderNodeMix"); sm.data_type = "RGBA"; sm.blend_type = "MULTIPLY"; sm.inputs["Factor"].default_value = 1.0
        nt.links.new(col, sm.inputs["A"]); nt.links.new(ca.outputs["Color"], sm.inputs["B"]); col = sm.outputs["Result"]
    nt.links.new(col, b.inputs["Base Color"])
    if rough_mul != 1.0:
        rm = nt.nodes.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = rough_mul
        nt.links.new(s.outputs["Green"], rm.inputs[0]); nt.links.new(rm.outputs[0], b.inputs["Roughness"])
    else:
        nt.links.new(s.outputs["Green"], b.inputs["Roughness"])
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = uv; n.inputs["Strength"].default_value = normal_strength
    nt.links.new(nm.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    return m


def refresh_trim_ao():
    """EC01's trim-sheet ORM had AO in only 82 of its 256 columns (the rest 0), so mouldings banded every metre. The
    texture was refilled along u (constant per row, from the valid columns) on 12 Nov; repack the master's copy."""
    im = bpy.data.images.get("T_EC01_Trim_ORM.png")
    if im is None:
        return None
    src = os.path.join(EC_TEX, "T_EC01_Trim_ORM.png")
    if im.packed_file:
        im.unpack(method="REMOVE")
    im.filepath = src; im.reload(); im.pack()
    OUT["items"]["ec01_trim_ao_refilled"] = dict(image=im.name, source=src, note="AO constant along u; was 0 in columns 82-255")
    return im.name


def materials():
    refresh_trim_ao()
    mats = {}
    for key, nm in (("mah", "M_EC01_Mahogany"), ("trim", "M_EC01_MahoganyTrim"), ("ven", "M_EC01_FiguredVeneer"),
                    ("brass", "M_EC01_HardwareBrass"), ("collider", "M_EC01_Collider"), ("af02", "M_HotelEden_AF02 | scanned aged gilt, baked game maps")):
        mats[key] = bpy.data.materials.get(nm); assert mats[key], nm
    # painted plaster with the EC01 trim-sheet relief on UV0 (cornice, window architraves)
    m, nt, out = M.fresh("M_MO01_PaintedPlaster"); b = M.principled(nt, out)
    b.inputs["Base Color"].default_value = (0.74, 0.70, 0.62, 1); b.inputs["Roughness"].default_value = 0.55
    tn = M.tex(nt, os.path.join(EC_TEX, "T_EC01_Trim_NormalGL.png"), "UV0_Bake", True, (-500, -200))
    ta = M.tex(nt, os.path.join(EC_TEX, "T_EC01_Trim_ORM.png"), "UV0_Bake", True, (-500, 100))
    sa = M.orm_split(nt, ta)
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.35
    mx.inputs["A"].default_value = (0.74, 0.70, 0.62, 1); nt.links.new(sa.outputs["Red"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = "UV0_Bake"; nt.links.new(tn.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    mats["paint"] = m
    mats["paper"] = mat_tiling("M_MO01_Wallpaper", "T_MO01_Wallpaper", tuple(REC["wallpaper"]["tile_m"]), uv="UV1_Wood")
    mats["parquet"] = mat_tiling("M_MO01_Parquet", "T_MO01_Parquet", REC["parquet"]["tile_m"])
    mats["brick"] = mat_tiling("M_MO01_FireBrick", "T_MO01_FireBrick", REC["firebrick"]["tile_m"], extra="soot")
    mats["marble"] = mat_tiling("M_MO01_MarbleHearth", "T_MO01_Marble", REC["Marble"]["tile_m"], rough_mul=1.0)
    mats["plaster"] = M.flat("M_MO01_BreastPlaster", (0.62, 0.58, 0.50), 0.85)
    mats["pelmet"] = mat_tiling("M_MO01_PelmetVelvet", "T_MO01_Velvet", REC["velvet"]["tile_m"])
    mats["ceiling"] = M.flat("M_MO01_Ceiling", (0.76, 0.72, 0.64), 0.9)
    mats["iron"] = M.flat("M_MO01_FireboxIron", (0.03, 0.028, 0.026), 0.7, metal=0.6)
    # rug: woven image on UV0, the approved Carpet001 pile on UV1 (6 per metre)
    m, nt, out = M.fresh("M_MO01_Rug"); b = M.principled(nt, out)
    t = M.tex(nt, os.path.join(TEX, "T_MO01_Rug_BaseColor.png"), "UV0_Bake", False, (-400, 200))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    pile = os.path.join(WS, "approved-media", "rug-r01-concept", "source", "Carpet001_2K-JPG_NormalGL.jpg")
    pn = M.tex(nt, pile, "UV1_Wood", True, (-400, -200))
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = "UV1_Wood"; n.inputs["Strength"].default_value = 0.8
    nt.links.new(pn.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 0.12; b.inputs["Sheen Roughness"].default_value = 0.5
    mats["rug"] = m
    m, nt, out = M.fresh("M_MO01_Portraits"); b = M.principled(nt, out)
    t = M.tex(nt, os.path.join(TEX, "T_MO01_Portraits_BaseColor.png"), "UV0_Bake", False, (-400, 200))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    cn = M.tex(nt, os.path.join(EC_TEX, "T_EC01_Canvas_NormalGL.png"), "UV1_Wood", True, (-400, -200))
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = "UV1_Wood"; n.inputs["Strength"].default_value = 0.35
    nt.links.new(cn.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.42
    mats["portrait"] = m
    return mats


# ------------------------------------------------------------------ loop intervals (skirting / dado rail / cornice)
LOOP_ORDER = [d[0] for d in RUN_DEF]
OFFS = {}
_acc = 0.0
for nm in LOOP_ORDER:
    OFFS[nm] = _acc; _acc += RUNS[nm].L
LOOP_L = _acc


def loop_point(t):
    t %= LOOP_L
    for nm in LOOP_ORDER:
        r = RUNS[nm]
        if t <= OFFS[nm] + r.L + 1e-9:
            s = t - OFFS[nm]
            p = r.A + r.U * s
            return (p.x, p.y)
    r = RUNS[LOOP_ORDER[-1]]; p = r.A + r.U * r.L
    return (p.x, p.y)


def visible_paths(blocks):
    """Open model-XY polylines along the loop outside the blocked intervals {run: [(s0, s1)]}."""
    B = sorted([(OFFS[r] + max(0.0, a), OFFS[r] + min(RUNS[r].L, b)) for r, iv in blocks.items() for a, b in iv if b > a])
    merged = []
    for a, b in B:
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    if not merged:
        return None
    vis = []
    for (a0, b0), (a1, b1) in zip(merged, merged[1:] + [(merged[0][0] + LOOP_L, merged[0][1] + LOOP_L)]):
        if a1 - b0 > 0.02:
            vis.append((b0, a1))
    corners = [OFFS[nm] for nm in LOOP_ORDER]
    paths = []
    for t0, t1 in vis:
        pts = [loop_point(t0)]
        for c in corners + [c + LOOP_L for c in corners]:
            if t0 + 1e-6 < c < t1 - 1e-6:
                pts.append(loop_point(c))
        pts.append(loop_point(t1))
        paths.append(pts)
    return paths


def build_mouldings(mats, c):
    objs = {}
    for name, blocks in (("Skirting", LOWER_BLOCK), ("DadoRail", {**{k: list(v) for k, v in LOWER_BLOCK.items()}, **{k: LOWER_BLOCK.get(k, []) + v for k, v in RAIL_BLOCK.items()}})):
        prof = G.horizontal(name, False)
        part = empty_part()
        for path in visible_paths(blocks):
            add_part(part, world_sweep(path, prof, False, TRIM_ROWS[name]), 0)
            for at_start in (True, False):
                p = path[0] if at_start else path[-1]; q = path[1] if at_start else path[-2]
                dirv = (q[0] - p[0], q[1] - p[1]) if at_start else (p[0] - q[0], p[1] - q[1])
                end_cap(part, p, dirv, prof, 0, at_start)
        objs[name] = mesh_obj(f"SM_MO01_{name}", part, [mats["trim"]], c)
    # cornice: the closed loop, EC01 profile at CORNICE_K, painted
    loop = [(p[0], -p[1]) for p in LOOP]
    prof = [(d * CORNICE_K, CEIL - (0.536 - w) * CORNICE_K - 0.0) for w, d in G.profile("Cornice", False)]
    v0, v1, L = TRIM_ROWS["Cornice"]
    part = world_sweep(loop, prof, True, (v0, v1, L * CORNICE_K))
    p2 = empty_part(); add_part(p2, part, 0)
    objs["Cornice"] = mesh_obj("SM_MO01_Cornice", p2, [mats["paint"]], c)
    return objs


# ------------------------------------------------------------------ dado framework, fields and paper per run
def dado_intervals(rn):
    L = RUNS[rn].L
    blocks = sorted(LOWER_BLOCK.get(rn, []))
    out, cur = [], 0.0
    for a, b in blocks:
        if a - cur > 0.02:
            out.append((cur, min(a, L)))
        cur = max(cur, b)
    if L - cur > 0.02:
        out.append((cur, L))
    return out


def framework_quads(part, run, holes, z0, z1, s0, s1, mat=0):
    xs = sorted(set([s0, s1] + [v for h in holes for v in (h[0], h[1]) if s0 < v < s1]))
    zs = sorted(set([z0, z1] + [v for h in holes for v in (h[2], h[3]) if z0 < v < z1]))
    d = 0.022
    for xa, xb in zip(xs[:-1], xs[1:]):
        col = []
        for za, zb in zip(zs[:-1], zs[1:]):
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            col.append(not any(h[0] <= cx <= h[1] and h[2] <= cz <= h[3] for h in holes))
        k = 0
        while k < len(col):
            if not col[k]:
                k += 1; continue
            j = k
            while j + 1 < len(col) and col[j + 1]:
                j += 1
            za, zb = zs[k], zs[j + 1]
            q = [(xa, d, za), (xb, d, za), (xb, d, zb), (xa, d, zb)]
            wq = [run.w(*p) for p in q]
            if Vector(G.newell([tuple(v) for v in wq])).dot(run.N) < 0:
                q = q[::-1]; wq = wq[::-1]
            add_quad(part, wq, wood_uv(q, (zb - za) > (xb - xa), 1.0, (0.13 * (xa % 7), 0.29)), mat)
            k = j + 1


def field_plane(part, run, r, d, inset, mat, tile):
    s0, s1, z0, z1 = r[0] + inset, r[1] - inset, r[2] + inset, r[3] - inset
    q = [(s0, d, z0), (s1, d, z0), (s1, d, z1), (s0, d, z1)]
    wq = [run.w(*p) for p in q]
    if Vector(G.newell([tuple(v) for v in wq])).dot(run.N) < 0:
        q = q[::-1]; wq = wq[::-1]
    cs = (s0 + s1) / 2
    add_quad(part, wq, [((p[0] - cs) / tile + 0.5, (p[2] - z0) / tile + 0.05) for p in q], mat)


def loop_sweep(part, run, r, profile, mat):
    s0, s1, z0, z1 = r[:4]
    path = [(s0, z0), (s1, z0), (s1, z1), (s0, z1)]
    add_part(part, world_sweep(path, G.profile(profile, False), True, TRIM_ROWS[profile], run=run, wall_plane=True), mat)


def build_dado(mats, c):
    objs = []
    tile_v = 2.43
    for rn in LOOP_ORDER:
        run = RUNS[rn]
        part = empty_part()
        for s0, s1 in dado_intervals(rn):
            w = s1 - s0
            fields = []
            if w > 0.40:
                st, mun = 0.08, 0.08
                n = max(1, int(round((w - 2 * st) / 0.70)))
                pw = (w - 2 * st - (n - 1) * mun) / n
                for k in range(n):
                    a = s0 + st + k * (pw + mun)
                    fields.append((a, a + pw, S.DADO_PANEL[0], S.DADO_PANEL[1]))
            framework_quads(part, run, fields, S.SKIRT_TOP - 0.01, S.DADO_RAIL[0] + 0.01, s0, s1)
            for f in fields:
                field_plane(part, run, f, 0.020, 0.066, 1, tile_v)
                loop_sweep(part, run, f, "Raise", 2)
            # 22 mm returns at the interval ends (convex corners and stops)
            box_world(part, run, s0, s0, 0.0, 0.022, S.SKIRT_TOP - 0.01, S.DADO_RAIL[0] + 0.01, 0, faces=("-s",))
            box_world(part, run, s1, s1, 0.0, 0.022, S.SKIRT_TOP - 0.01, S.DADO_RAIL[0] + 0.01, 0, faces=("+s",))
        if part["faces"]:
            objs.append(mesh_obj(f"SM_MO01_Dado_{rn}", part, [mats["mah"], mats["ven"], mats["trim"]], c))
    return objs


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def window_outline(w, grow):
    """Window surround outline in run (s, z): jambs from the sill to the springing, arch over (closed polygon)."""
    k = w["kind"]; sc = w["s"]
    pts = [(sc - (A_HALF + grow), ARCH[k]["sill"] - 0.12)]
    for i in range(41):
        x, z = arch_sz(k, i / 40, grow)
        pts.append((sc + x, z))
    pts.append((sc + (A_HALF + grow), ARCH[k]["sill"] - 0.12))
    return pts


def build_paper(mats, c):
    objs = []
    tu, tv = REC["wallpaper"]["tile_m"]
    for rn in LOOP_ORDER:
        run = RUNS[rn]
        holes = []
        if rn == "S":
            holes += [[(CASE_S[0] - 0.01, 0.9), (CASE_S[1], 0.9), (CASE_S[1], 3.40), (CASE_S[0] - 0.01, 3.40)]]
            holes += [[(DOOR_ARCH[0] + 0.02, 0.9), (DOOR_ARCH[1] - 0.02, 0.9), (DOOR_ARCH[1] - 0.02, 2.41 + 0.08), (DOOR_ARCH[0] + 0.02, 2.41 + 0.08)]]
        if rn == "WN":
            holes += [[(-0.01, 0.9), (run.L + 0.01, 0.9), (run.L + 0.01, 3.40), (-0.01, 3.40)]]
        for w in WINDOWS:
            if w["run"] == rn:
                holes.append(window_outline(w, 0.02))
        # bmesh: rectangle with the holes, scanfilled, then hole faces removed
        bm = bmesh.new()
        def loop_edges(poly):
            vs = [bm.verts.new((p[0], p[1], 0.0)) for p in poly]
            for i in range(len(vs)):
                bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
        z0, z1 = PAPER
        outer = [(0.0, z0), (run.L, z0), (run.L, z1), (0.0, z1)]
        loop_edges(outer)
        clipped = []
        for h in holes:
            hp = [(min(max(p[0], 0.0005), run.L - 0.0005), min(max(p[1], z0 + 0.0005), z1 - 0.0005)) for p in h]
            clipped.append(hp); loop_edges(hp)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bm.edges)
        kill = [f for f in bm.faces if any(point_in_poly(*tuple(f.calc_center_median())[:2], hp) for hp in clipped)]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        verts = [tuple(run.w(v.co.x, PAPER_OFF, v.co.y)) for v in bm.verts]
        idx = {v: i for i, v in enumerate(bm.verts)}
        part = empty_part()
        part["verts"] = verts
        for f in bm.faces:
            ids = [idx[v] for v in f.verts]
            part["faces"].append(tuple(ids)); part["mat"].append(0)
            part["uv1"].append([(v.co.x, v.co.y) for v in f.verts])
            part["uv0"].append([(0.999, 0.999)] * len(ids))
        bm.free()
        orient_faces(part, lambda cc, run=run: tuple(run.N))
        if part["faces"]:
            objs.append(mesh_obj(f"SM_MO01_Paper_{rn}", part, [mats["paper"]], c, sharp=0, smooth=False))
    return objs


# ------------------------------------------------------------------ chimney breast, firebox, hearth, mantel
OPEN = dict(y0=S.FIRE_C - 0.46, y1=S.FIRE_C + 0.46, h=0.84)
FIRE_BACK = dict(x=17.62 - S.FIREBOX["depth"], y0=S.FIRE_C - 0.35, y1=S.FIRE_C + 0.35)


def build_breast(mats, c):
    B = S.BREAST
    part = empty_part()
    def quad(pl, mat, uvfn=None):
        q = [(p[0], -p[1], FL + p[2]) for p in pl]
        add_quad(part, q, [(0, 0)] * 4 if uvfn is None else [uvfn(p) for p in pl], mat)
    x1 = B["x1"]
    ys = [B["y0"], OPEN["y0"], OPEN["y1"], B["y1"]]; zs = [0.0, OPEN["h"], CEIL]
    for i in range(3):
        for j in range(2):
            if i == 1 and j == 0:
                continue
            quad([(x1, ys[i], zs[j]), (x1, ys[i], zs[j + 1]), (x1, ys[i + 1], zs[j + 1]), (x1, ys[i + 1], zs[j])], 0)
    quad([(B["x0"], B["y0"], 0), (B["x0"], B["y0"], CEIL), (x1, B["y0"], CEIL), (x1, B["y0"], 0)], 0)
    quad([(x1, B["y1"], 0), (x1, B["y1"], CEIL), (B["x0"], B["y1"], CEIL), (B["x0"], B["y1"], 0)], 0)
    orient_faces(part, lambda cc: (1.0, 0.0, 0.0) if abs(cc[0] - x1) < 1e-4 else ((0.0, 1.0, 0.0) if -cc[1] < S.FIRE_C else (0.0, -1.0, 0.0)))
    breast = mesh_obj("SM_MO01_ChimneyBreast", part, [mats["plaster"]], c, smooth=False)
    # firebox: splayed cheeks, back, floor and a sooty throat; subdivided for the per-vertex soot
    fp = empty_part()
    fx, fy0, fy1 = FIRE_BACK["x"], FIRE_BACK["y0"], FIRE_BACK["y1"]
    def grid(p00, p10, p11, p01, nu, nv, mat, normal):
        base = len(fp["verts"])
        P = []
        for j in range(nv + 1):
            for i in range(nu + 1):
                u, v = i / nu, j / nv
                a = [p00[k] * (1 - u) * (1 - v) + p10[k] * u * (1 - v) + p11[k] * u * v + p01[k] * (1 - u) * v for k in range(3)]
                P.append(a)
        for p in P:
            fp["verts"].append((p[0], -p[1], FL + p[2]))
        for j in range(nv):
            for i in range(nu):
                a = base + j * (nu + 1) + i
                f = (a, a + 1, a + nu + 2, a + nu + 1)
                vs = [fp["verts"][k] for k in f]
                n = G.newell(vs)
                if n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] < 0:
                    f = f[::-1]
                fp["faces"].append(f); fp["mat"].append(mat)
                fp["uv1"].append([((P[k - base][1] + P[k - base][0]) , P[k - base][2]) for k in f])
                fp["uv0"].append([(0.999, 0.999)] * 4)
    h = OPEN["h"]
    grid((fx, fy0, 0), (fx, fy1, 0), (fx, fy1, h), (fx, fy0, h), 6, 8, 0, (1, 0, 0))                        # back
    grid((17.62, OPEN["y0"], 0), (fx, fy0, 0), (fx, fy0, h), (17.62, OPEN["y0"], h), 4, 8, 0, (0.4, 1, 0))     # north cheek (faces +y plan? see orient below)
    grid((fx, fy1, 0), (17.62, OPEN["y1"], 0), (17.62, OPEN["y1"], h), (fx, fy1, h), 4, 8, 0, (0.4, -1, 0))
    grid((17.62, OPEN["y0"], 0.002), (17.62, OPEN["y1"], 0.002), (fx, fy1, 0.002), (fx, fy0, 0.002), 6, 4, 0, (0, 0, 1))  # floor
    grid((17.62, OPEN["y0"], h), (fx, fy0, h + 0.10), (fx, fy1, h + 0.10), (17.62, OPEN["y1"], h), 4, 2, 1, (0, 0, -1))   # throat
    # orient every face towards the firebox's inside point
    ins = (17.45, -S.FIRE_C, FL + 0.35)
    for i, f in enumerate(fp["faces"]):
        vs = [fp["verts"][k] for k in f]; n = G.newell(vs)
        cc = [sum(v[k] for v in vs) / len(vs) for k in range(3)]
        if sum(n[k] * (ins[k] - cc[k]) for k in range(3)) < 0:
            fp["faces"][i] = tuple(reversed(f)); fp["uv1"][i] = list(reversed(fp["uv1"][i]))
    fb = mesh_obj("SM_MO01_Firebox", fp, [mats["brick"], mats["iron"]], c, smooth=False)
    # soot: darker up the back and towards the throat
    me = fb.data
    ca = me.color_attributes.new("Soot", "BYTE_COLOR", "CORNER")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            z = max(0.0, (v.z - FL) / h); depth = max(0.0, (17.62 - v.x) / S.FIREBOX["depth"])
            k = max(0.18, 1.0 - 0.75 * z ** 1.3 - 0.25 * depth * z)
            ca.data[li].color = (k, k, k, 1.0)
    # hearth slab
    hp = empty_part()
    hx0, hx1 = 17.62, 17.62 + S.HEARTH["depth"]; hy0, hy1 = S.FIRE_C - S.HEARTH["width"] / 2, S.FIRE_C + S.HEARTH["width"] / 2; ht = S.HEARTH["t"]
    for q, nrm in (([(hx0, hy0, ht), (hx1, hy0, ht), (hx1, hy1, ht), (hx0, hy1, ht)], (0, 0, 1)),
                   ([(hx1, hy0, 0), (hx1, hy1, 0), (hx1, hy1, ht), (hx1, hy0, ht)], (1, 0, 0)),
                   ([(hx0, hy0, 0), (hx1, hy0, 0), (hx1, hy0, ht), (hx0, hy0, ht)], (0, 1, 0)),
                   ([(hx1, hy1, 0), (hx0, hy1, 0), (hx0, hy1, ht), (hx1, hy1, ht)], (0, -1, 0))):
        wq = [(p[0], -p[1], FL + p[2]) for p in q]
        nn = (nrm[0], -nrm[1], nrm[2])
        if sum(a * b for a, b in zip(G.newell(wq), nn)) < 0:
            wq = wq[::-1]
        add_quad(hp, wq, [(v[0], v[1]) for v in wq], 0)
    hearth = mesh_obj("SM_MO01_Hearth", hp, [mats["marble"]], c, sharp=30)
    return [breast, fb, hearth]


APPENDED = set()


def append_object_mesh(blend, names):
    """Append objects for their mesh data only; the appended objects themselves are removed again."""
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    out = {}
    for o in dst.objects:
        if o is None:
            continue
        nm = o.name.split(".")[0] if o.name.split(".")[0] in names else o.name
        out[nm] = o.data; APPENDED.add(o.data.name)
        bpy.data.objects.remove(o, do_unlink=True)
    return out


def build_mantel_and_grate(c):
    kit = append_object_mesh(os.path.join(KIT, "MO01_Kit_mantel.blend"), ["SM_MO01_Mantel"])
    me = kit["SM_MO01_Mantel"]
    rot = Matrix.Rotation(math.radians(-90), 4, "Z")
    m = Matrix.Translation((S.BREAST["x1"], -S.FIRE_C, FL)) @ rot
    mantel = place("SM_MO01_Mantel", me, m, c)
    g = {}
    for nm in ("SM_HE_Fireplace_Grate_G01", "SM_HE_Fireplace_Fuel_G01"):
        o = bpy.data.objects.get(nm)
        if o is not None and o.type == "MESH":
            g[nm] = o.data
    if len(g) < 2:
        g = append_object_mesh(G01_BLEND, ["SM_HE_Fireplace_Grate_G01", "SM_HE_Fireplace_Fuel_G01"])
    sc_ = 0.66
    mg = Matrix.Translation(((FIRE_BACK["x"] + 17.62) / 2 + 0.02, -S.FIRE_C, FL - 0.147 * sc_ + 0.004)) @ Matrix.Rotation(math.radians(90), 4, "Z") @ Matrix.Diagonal((sc_, sc_, sc_, 1))
    grate = place("MO01 | G01 grate (approved, placed)", g["SM_HE_Fireplace_Grate_G01"], mg, c)
    fuel = place("MO01 | G01 fuel (approved, placed)", g["SM_HE_Fireplace_Fuel_G01"], mg, c)
    OUT["items"]["grate"] = dict(source=os.path.relpath(G01_BLEND, WS), scale=sc_, note="approved G01 grate and fuel, uniform scale 0.66 into the brick firebox")
    return [mantel, grate, fuel]


# ------------------------------------------------------------------ bookcases
def flute_pilaster_mesh(mats):
    """SM_MO01_CasePilaster: 0.11 x 0.04 fluted pilaster, z 0.955-3.20 (base and capital blocks). Local: x across,
    y out of the carcass front (0 = carcass front plane), z up from the floor."""
    p = empty_part()
    run = Run("_pl", (0.0, 0.0), (1.0, 0.0), (0, -1))          # a neutral frame: U = +x, N = +y(model)... local build
    # build directly in local coords with simple lists
    verts, faces, uv1, mat = [], [], [], []
    def q(pts, m, uv):
        o = len(verts); verts.extend(pts); faces.append(tuple(range(o, o + len(pts)))); uv1.append(uv); mat.append(m)
    hw, d0, d1 = 0.055, 0.0, 0.04
    zb0, zb1, zc0, zc1 = 0.955, 1.03, 3.09, 3.20
    # fluted front: 5 flutes across the inner 0.085, 8 segments each
    xs, ys = [], []
    nfl, seg = 5, 8
    fl_w = 0.085 / nfl
    xs.append(-hw); ys.append(d1)
    xs.append(-0.0425); ys.append(d1)
    for k in range(nfl):
        for j in range(1, seg + 1):
            t = j / seg
            x = -0.0425 + (k + t) * fl_w
            y = d1 - 0.007 * math.sin(math.pi * t) if j < seg else d1
            xs.append(x); ys.append(y)
    xs.append(hw); ys.append(d1)
    for i in range(len(xs) - 1):
        q([(xs[i], ys[i], zb1), (xs[i + 1], ys[i + 1], zb1), (xs[i + 1], ys[i + 1], zc0), (xs[i], ys[i], zc0)], 0,
          [(zb1, xs[i]), (zb1, xs[i + 1]), (zc0, xs[i + 1]), (zc0, xs[i])])
    for sx in (-1, 1):
        x = sx * hw
        f = [(x, d0, zb1), (x, d1, zb1), (x, d1, zc0), (x, d0, zc0)]
        q(f if sx < 0 else f[::-1], 0, [(zb1, 0), (zb1, 0.04), (zc0, 0.04), (zc0, 0)])
    # base and capital blocks (slightly larger), with chamfered tops
    for (z0, z1, gw, gd) in ((zb0, zb1, 0.012, 0.012), (zc0, zc1, 0.014, 0.018)):
        x0, x1, y1 = -hw - gw, hw + gw, d1 + gd
        q([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)][::-1], 0, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)])
        q([(x0, d0, z0), (x0, y1, z0), (x0, y1, z1), (x0, d0, z1)], 0, [(0, z0), (y1, z0), (y1, z1), (0, z1)])
        q([(x1, y1, z0), (x1, d0, z0), (x1, d0, z1), (x1, y1, z1)], 0, [(0, z0), (y1, z0), (y1, z1), (0, z1)])
        q([(x0, d0, z1), (x0, y1, z1), (x1, y1, z1), (x1, d0, z1)][::-1], 0, [(x0, 0), (x0, y1), (x1, y1), (x1, 0)])
        q([(x0, d0, z0), (x1, d0, z0), (x1, y1, z0), (x0, y1, z0)][::-1], 0, [(x0, 0), (x1, 0), (x1, y1), (x0, y1)])
    part = dict(verts=verts, faces=faces, uv1=uv1, uv0=[[(0.999, 0.999)] * len(f) for f in faces], mat=mat)
    def ref(cc):
        return (0.0, 1.0, 0.0)
    # orient: every face away from the pilaster's core axis (0, 0.0, z)
    for i, f in enumerate(part["faces"]):
        vs = [part["verts"][k] for k in f]; n = G.newell(vs)
        ccen = [sum(v[k] for v in vs) / len(vs) for k in range(3)]
        dvec = (ccen[0], ccen[1] - 0.01, 0.0 if zb1 + 0.01 < ccen[2] < zc0 - 0.01 else (ccen[2] - (zb0 + zb1) / 2 if ccen[2] < 2 else ccen[2] - (zc0 + zc1) / 2))
        if n[0] * dvec[0] + n[1] * dvec[1] + n[2] * dvec[2] < 0:
            part["faces"][i] = tuple(reversed(f)); part["uv1"][i] = list(reversed(part["uv1"][i]))
    me_ob = mesh_obj("SM_MO01_CasePilaster", part, [mats["mah"]], bpy.context.scene.collection, sharp=50)
    me = me_ob.data; bpy.data.objects.remove(me_ob, do_unlink=True)
    return me


def door_mesh(mats, w, h):
    """SM_MO01_CaseDoor: a 22 mm cupboard door (local x 0..w, y 0..0.022 out, z 0..h) with a raised field (EC01 Raise)."""
    run = Run("_door", (0.0, 0.0), (w, 0.0), (0, -1)); run.A = Vector((0, 0, 0))
    part = empty_part()
    box_world(part, run, 0.0, w, 0.0, 0.022, 0.0, h, 0, faces=("-s", "+s", "+z", "-z"), vertical=True)
    r = (0.06, w - 0.06, 0.06, h - 0.06)
    framework_quads(part, run, [r], 0.0, h, 0.0, w)
    field_plane(part, run, r, 0.020, 0.066, 0, 1.0)
    loop_sweep(part, run, r, "Raise", 1)
    ob = mesh_obj("SM_MO01_CaseDoor", part, [mats["mah"], mats["trim"]], bpy.context.scene.collection)
    me = ob.data; bpy.data.objects.remove(ob, do_unlink=True)
    return me


def knob_mesh(mats):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.013)
    for v in bm.verts:
        v.co.y = v.co.y * 1.2 + 0.03
    st = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.006, radius2=0.006, depth=0.03)
    for v in st["verts"]:
        v.co = Matrix.Rotation(math.radians(90), 3, "X") @ v.co; v.co.y += 0.015
    me = bpy.data.meshes.new("SM_MO01_CaseKnob"); bm.to_mesh(me); bm.free()
    me.uv_layers.new(name="UV0_Bake"); me.uv_layers.new(name="UV1_Wood")
    me.materials.append(mats["brass"])
    for p in me.polygons:
        p.use_smooth = True
    return me


def build_bookcase(name, run, s0, s1, n_bays, mats, shared, c, end_visible=(False, False), ladder=False):
    C = S.CASE
    L = s1 - s0; pw = C["pil_w"]
    bay = (L - (n_bays + 1) * pw) / n_bays
    part = empty_part()
    bd, ud = C["base_d"], C["upper_d"]
    # plinth (toe recess 0.03), cupboard front frame with door openings, carcass ends, counter top
    box_world(part, run, s0, s1, 0.0, bd - 0.03, 0.0, C["plinth_h"], 0, faces=("+d",) + (("-s",) if end_visible[0] else ()) + (("+s",) if end_visible[1] else ()), vertical=False)
    holes = []
    for k in range(n_bays):
        a = s0 + pw + k * (bay + pw)
        holes.append((a, a + bay, C["plinth_h"] + 0.025, C["base_h"] - 0.025))
    fr = empty_part()
    framework_quads(fr, run, holes, C["plinth_h"], C["base_h"], s0, s1)
    fr["verts"] = [tuple(Vector(v) + run.N * (bd - 0.022)) for v in fr["verts"]]
    add_part(part, fr, 0)
    for (a, b, z0, z1) in holes:                                            # reveals of the door openings (dark carcass)
        box_world(part, run, a, b, bd - 0.03, bd, z0, z1, 0, faces=("-z", "+z", "-s", "+s"), vertical=True)
        box_world(part, run, a, b, 0.0, bd - 0.03, z0, z1, 0, faces=("+d",), vertical=True)
    for e, s_ in ((0, s0), (1, s1)):
        if end_visible[e]:
            box_world(part, run, s_, s_, 0.0, bd, C["plinth_h"], C["base_h"], 0, faces=("-s",) if e == 0 else ("+s",), vertical=True)
    ct = C["top_t"]
    box_world(part, run, s0 - (0.02 if end_visible[0] else 0), s1 + (0.02 if end_visible[1] else 0), 0.0, bd + 0.025, C["base_h"], C["base_h"] + ct, 0,
              faces=("+d", "+z", "-z") + (("-s",) if end_visible[0] else ()) + (("+s",) if end_visible[1] else ()), vertical=False)
    z_up0 = C["base_h"] + ct
    # back panel, dividers, shelves (shared mesh) per bay
    box_world(part, run, s0, s1, 0.0, 0.006, z_up0, 3.42, 0, faces=("+d",), vertical=True)              # back panel up to the crown
    for k in range(n_bays + 1):
        pc = s0 + pw / 2 + k * (bay + pw)
        box_world(part, run, pc - 0.0125, pc + 0.0125, 0.006, ud, z_up0, 3.20, 0, faces=("-s", "+s"), vertical=True)
    if end_visible[1]:
        box_world(part, run, s1, s1, 0.0, ud + 0.005, z_up0, 3.42, 0, faces=("+s",), vertical=True)
    if end_visible[0]:
        box_world(part, run, s0, s0, 0.0, ud + 0.005, z_up0, 3.42, 0, faces=("-s",), vertical=True)
    # frieze board and crown (EC01 Band profile along the front, returned at visible ends)
    box_world(part, run, s0, s1, ud, ud + 0.012, 3.20, 3.30, 0, faces=("+d", "-z"), vertical=False)
    # the crown path is the frieze front line; returns follow the visible ends back to the wall
    path = [tuple(run.w(s0, 0.0, 0)[:2])] * end_visible[0] + [tuple(run.w(s0, ud - 0.010, 0)[:2]), tuple(run.w(s1, ud - 0.010, 0)[:2])] + [tuple(run.w(s1, 0.0, 0)[:2])] * end_visible[1]
    crown = world_sweep(path, [(d, w + 3.30) for w, d in G.profile("Band", False)], False, TRIM_ROWS["Band"])
    add_part(part, crown, 2)
    box_world(part, run, s0, s1, 0.0, ud + 0.045, 3.42, 3.42, 0, faces=("+z",), vertical=False)
    ob = mesh_obj(f"SM_MO01_Bookcase_{name}", part, [mats["mah"], mats["ven"], mats["trim"]], c)
    objs = [ob]
    # shared parts
    rot = Matrix((run.U, run.N, run.Z)).transposed().to_4x4()
    for k in range(n_bays + 1):
        pc = s0 + pw / 2 + k * (bay + pw)
        m = Matrix.Translation(run.w(pc, ud, 0.0)) @ rot
        objs.append(place(f"MO01 | {name} | Pilaster | {k:02d}", shared["pil"], m, c))
    dw = (bay - 0.006) / 2; dh = C["base_h"] - 0.025 - (C["plinth_h"] + 0.025) - 0.006
    sx = dw / shared["door_w"]
    for k in range(n_bays):
        a = s0 + pw + k * (bay + pw)
        for j in range(2):
            s_ = a + 0.002 + j * (dw + 0.002)
            m = Matrix.Translation(run.w(s_, bd, C["plinth_h"] + 0.028)) @ rot @ Matrix.Diagonal((sx, 1, 1, 1))
            objs.append(place(f"MO01 | {name} | Door | {k:02d}{'ab'[j]}", shared["door"], m, c))
            kx = s_ + (dw - 0.04 if j == 0 else 0.04)
            objs.append(place(f"MO01 | {name} | Knob | {k:02d}{'ab'[j]}", shared["knob"], Matrix.Translation(run.w(kx, bd + 0.022, C["base_h"] - 0.12)) @ rot, c))
        for zk in (1.315, 1.675, 2.035, 2.395, 2.755):
            m = Matrix.Translation(run.w(a, 0.006, zk)) @ rot @ Matrix.Diagonal((bay, 1, 1, 1))
            objs.append(place(f"MO01 | {name} | Shelf | {k:02d} | {zk:.2f}", shared["shelf"], m, c))
    OUT["items"][f"bookcase_{name}"] = dict(run=run.name, s=[round(s0, 3), round(s1, 3)], bays=n_bays, bay_w=round(bay, 4))
    if ladder:
        objs += build_ladder(run, s0, s1, n_bays, bay, mats, c)
    return objs, bay


def shelf_mesh(mats):
    """Unit-width shelf (local x 0..1, scaled per bay), 0.315 deep, 0.028 thick with a 0.040 front lip."""
    run = Run("_sh", (0.0, 0.0), (1.0, 0.0), (0, -1)); run.A = Vector((0, 0, 0))
    part = empty_part()
    box_world(part, run, 0.0, 1.0, 0.0, 0.315, 0.0, 0.028, 0, faces=("+z", "-z"), vertical=False)
    box_world(part, run, 0.0, 1.0, 0.315, 0.335, -0.012, 0.028, 0, faces=("+d", "+z", "-z"), vertical=False)
    ob = mesh_obj("SM_MO01_CaseShelf", part, [mats["mah"]], bpy.context.scene.collection)
    me = ob.data; bpy.data.objects.remove(ob, do_unlink=True)
    return me


def tube(part, p0, p1, r, mat, n=10):
    d = (p1 - p0); L = d.length; d.normalize()
    a = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(a).normalized(); v = d.cross(u)
    ring0 = [p0 + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    ring1 = [p + d * L for p in ring0]
    for k in range(n):
        q = [ring0[k], ring0[(k + 1) % n], ring1[(k + 1) % n], ring1[k]]
        cc = sum(q, Vector()) / 4; axis = p0 + d * ((cc - p0).dot(d))
        if Vector(G.newell([tuple(x) for x in q])).dot(cc - axis) < 0:
            q = q[::-1]
        add_quad(part, q, [(k / n, 0), ((k + 1) / n, 0), ((k + 1) / n, L), (k / n, L)], mat)


def build_ladder(run, s0, s1, n_bays, bay, mats, c):
    C = S.CASE
    rp = empty_part()
    zr = S.LADDER_RAIL_Z; dr = C["upper_d"] + 0.04 + 0.10
    tube(rp, run.w(s0 + 0.05, dr, zr), run.w(s1 - 0.05, dr, zr), 0.014, 0, n=12)
    for k in range(n_bays + 1):
        pc = s0 + C["pil_w"] / 2 + k * (bay + C["pil_w"])
        if s0 + 0.04 < pc < s1 - 0.04:
            tube(rp, run.w(pc, C["upper_d"] + 0.04, zr), run.w(pc, dr, zr), 0.009, 0, n=8)
    rail = mesh_obj("SM_MO01_LadderRail", rp, [mats["brass"]], c, sharp=0)
    # rolling library ladder hung on the rail, feet 0.70 m out from the cupboard front
    lp = empty_part()
    s_c = s0 + 1.20; wl = 0.46
    top_d, foot_d = dr, C["base_d"] + 0.70
    for side in (-1, 1):
        sx = s_c + side * wl / 2
        a = run.w(sx, foot_d, 0.06); b = run.w(sx, top_d - 0.03, zr - 0.02)
        tube(lp, a, b, 0.024, 0, n=8)
        tube(lp, b, run.w(sx, top_d + 0.016, zr + 0.03), 0.010, 1, n=6)                                       # brass hook
        tube(lp, run.w(sx, foot_d, 0.06), run.w(sx, foot_d + 0.0, 0.0), 0.028, 1, n=8)                       # castor
    n_t = 9
    for i in range(1, n_t + 1):
        t = i / (n_t + 1)
        d_ = foot_d + (top_d - 0.03 - foot_d) * t; z_ = 0.06 + (zr - 0.08) * t
        box_world(lp, run, s_c - wl / 2, s_c + wl / 2, d_ - 0.06, d_ + 0.06, z_ - 0.014, z_ + 0.014, 0, faces=("+z", "-z", "+d", "-d"), vertical=False)
    ladder = mesh_obj("SM_MO01_LibraryLadder", lp, [mats["mah"], mats["brass"]], c)
    OUT["items"]["ladder"] = dict(rail_z=zr, rail_out=round(dr, 3), ladder_at_s=round(s_c, 3))
    return [rail, ladder]


# ------------------------------------------------------------------ windows: architraves and drapes
def tailored(k):
    return [f"SM_MO01_Swag_{k}", f"SM_MO01_Tail_{k}_L", f"SM_MO01_Tail_{k}_R", f"SM_MO01_Fringe_Swag_{k}", f"SM_MO01_Fringe_Tail_{k}_L",
            f"SM_MO01_Fringe_Tail_{k}_R"]


def build_windows(mats, c):
    objs = []
    prof = [(w * WIN_ARCH_K, d * WIN_ARCH_K) for w, d in G.profile("Architrave", False)]
    v0, v1, L = TRIM_ROWS["Architrave"]
    kit = append_object_mesh(KITS["drapes"], ["SM_MO01_DrapeSide_L", "SM_MO01_DrapeSide_R", "SM_MO01_Sheer"] + tailored("N") + tailored("E"))
    H_N = ARCH["N"]["spring"] + 0.10 - 0.012; H_Ns = ARCH["N"]["spring"] + 0.02 - 0.016
    for w in WINDOWS:
        run = RUNS[w["run"]]; k = w["kind"]; sc = w["s"]
        z_bot = 0.95 if k == "N" else 0.80
        grow = 0.004
        path = [(sc - (A_HALF + grow), z_bot), (sc - (A_HALF + grow), ARCH[k]["spring"])]
        for i in range(1, 40):
            x, z = arch_sz(k, i / 40, grow)
            path.append((sc + x, z))
        path += [(sc + (A_HALF + grow), ARCH[k]["spring"]), (sc + (A_HALF + grow), z_bot)]
        # path runs up the low-s jamb: LEFT of it is -s (outward), as the profile w grows away from the opening
        part = world_sweep(path, prof, False, (v0, v1, L * WIN_ARCH_K), run=run, wall_plane=True)
        p2 = empty_part(); add_part(p2, part, 0)
        # flat bottom caps of the two legs
        for sgn, s_ in ((-1, sc - (A_HALF + grow)), (1, sc + (A_HALF + grow))):
            s_out = s_ + sgn * prof[-1][0]
            box_world(p2, run, min(s_, s_out), max(s_, s_out), 0.0, max(d for _, d in prof), z_bot, z_bot, 0, faces=("-z",), vertical=False)
        objs.append(mesh_obj(f"SM_MO01_WindowArchitrave_{w['id']}", p2, [mats["paint"]], c))
        # drapes in the window frame: X along the wall (= run U), Y into the room (= run N), Z up, origin at the wall face
        rot = Matrix((run.U, run.N, run.Z)).transposed().to_4x4()
        base = Matrix.Translation(run.w(sc, 0.0, 0.0)) @ rot
        zs = 1.0 if k == "N" else (ARCH["E"]["spring"] + 0.10 - 0.012) / H_N
        zss = 1.0 if k == "N" else (ARCH["E"]["spring"] + 0.02 - 0.016) / H_Ns
        for nm in ("SM_MO01_DrapeSide_L", "SM_MO01_DrapeSide_R"):
            objs.append(place(f"MO01 | {w['id']} | {nm[8:]}", kit[nm], base @ Matrix.Diagonal((1, 1, zs, 1)), c))
        objs.append(place(f"MO01 | {w['id']} | Sheer", kit["SM_MO01_Sheer"], base @ Matrix.Diagonal((1, 1, zss, 1)), c))
        objs.append(pelmet(w, run, mats, c))
        for nm in tailored(k):                                     # the swag, its tails and their fringes, per arch
            objs.append(place(f"MO01 | {w['id']} | {nm[8:]}", kit[nm], base, c))
    OUT["items"]["windows"] = [dict(id=w["id"], run=w["run"], s=round(w["s"], 3), kind=w["kind"]) for w in WINDOWS]
    return objs


def pelmet(w, run, mats, c):
    """A slim velvet-covered arched pelmet board: front 45 mm tall at 0.29 m off the wall, top and bottom returned to the
    wall. The swag and its tails hang from its top edge; the curtains and sheer hang under it."""
    k = w["kind"]; sc = w["s"]
    n = 48
    inset = 0.05
    pts = []
    for i in range(n + 1):
        x, z = arch_sz(k, i / n, 0.0)
        pts.append((sc + x * (1 - inset / A_HALF), z - inset * 0.6))
    yf, hh = 0.29, 0.045
    part = empty_part()
    L = 0.0
    for (s0, z0), (s1, z1) in zip(pts[:-1], pts[1:]):
        dl = math.hypot(s1 - s0, z1 - z0)
        q_front = [run.w(s0, yf, z0), run.w(s1, yf, z1), run.w(s1, yf, z1 + hh), run.w(s0, yf, z0 + hh)]
        add_quad(part, q_front, [(L, 0), (L + dl, 0), (L + dl, hh), (L, hh)], 0)
        add_quad(part, [run.w(s0, 0.0, z0 + hh), run.w(s0, yf, z0 + hh), run.w(s1, yf, z1 + hh), run.w(s1, 0.0, z1 + hh)],
                 [(L, 0), (L, yf), (L + dl, yf), (L + dl, 0)], 0)
        add_quad(part, [run.w(s0, 0.0, z0), run.w(s1, 0.0, z1), run.w(s1, yf, z1), run.w(s0, yf, z0)],
                 [(L, 0), (L + dl, 0), (L + dl, yf), (L, yf)], 0)
        L += dl
    for (s_, z_) in (pts[0], pts[-1]):
        add_quad(part, [run.w(s_, 0.0, z_), run.w(s_, yf, z_), run.w(s_, yf, z_ + hh), run.w(s_, 0.0, z_ + hh)], [(0, 0), (yf, 0), (yf, hh), (0, hh)], 0)
    cen = run.w(sc, yf / 2, (ARCH[k]["spring"] + ARCH[k]["apex"]) / 2 - 0.3)
    orient_faces(part, lambda cc: tuple(Vector(cc) - cen) if True else None)
    return mesh_obj(f"SM_MO01_Pelmet_{w['id']}", part, [mats["pelmet"]], c, sharp=40)


def build_door_architrave(mats, c):
    run = RUNS["S"]
    a, b = 23.15 - 17.1, 24.75 - 17.1
    head = 2.41
    path = [(a, 0.0), (a, head), (b, head), (b, 0.0)]
    prof = G.profile("Architrave", False)
    part = world_sweep(path, prof, False, TRIM_ROWS["Architrave"], run=run, wall_plane=True)
    p2 = empty_part(); add_part(p2, part, 0)
    return [mesh_obj("SM_MO01_DoorArchitrave_D-MO-24", p2, [mats["trim"]], c)]


# ------------------------------------------------------------------ floor, ceiling, rug
def build_floor_ceiling_rug(mats, c):
    R = S.ROOM
    p = empty_part()
    z = FL + S.FLOOR_T
    q = [(R["x0"], -R["y1"], z), (R["x1"], -R["y1"], z), (R["x1"], -R["y0"], z), (R["x0"], -R["y0"], z)]
    add_quad(p, q, [(v[0], v[1]) for v in q], 0)
    floor = mesh_obj("SM_MO01_Parquet", p, [mats["parquet"]], c, sharp=0, smooth=False)
    p = empty_part()
    z = FL + CEIL - CEIL_DROP
    q = [(R["x0"], -R["y1"], z), (R["x0"], -R["y0"], z), (R["x1"], -R["y0"], z), (R["x1"], -R["y1"], z)]
    add_quad(p, q, [(v[0], v[1]) for v in q], 0)
    ceil_ = mesh_obj("SM_MO01_Ceiling", p, [mats["ceiling"]], c, sharp=0, smooth=False)
    # rug: long axis along x; image row 0 (top) towards the fireplace; 9 mm with a bound edge
    Rg = S.RUG; w_ = REC["rug"]["aspect_w_over_l"] * Rg["l"]
    x0, x1 = Rg["cx"] - Rg["l"] / 2, Rg["cx"] + Rg["l"] / 2; y0, y1 = Rg["cy"] - w_ / 2, Rg["cy"] + w_ / 2
    zt = FL + S.FLOOR_T + Rg["t"]; zb = FL + S.FLOOR_T
    p = empty_part()
    top = [(x0, -y1, zt), (x1, -y1, zt), (x1, -y0, zt), (x0, -y0, zt)]
    # UV0: u across the rug width (plan y), v along its length (x): v = 1 at the fireplace end (x0)
    def uv0(v):
        return ((-v[1] - y0) / w_, 1 - (v[0] - x0) / Rg["l"])
    add_quad(p, top, [(v[0] * 6, v[1] * 6) for v in top], 0, uv0=[uv0(v) for v in top])
    for a, b in ((top[0], top[1]), (top[1], top[2]), (top[2], top[3]), (top[3], top[0])):
        qq = [(a[0], a[1], zb), (b[0], b[1], zb), (b[0], b[1], zt), (a[0], a[1], zt)]
        add_quad(p, qq, [(0, 0)] * 4, 0, uv0=[uv0(a), uv0(b), uv0(b), uv0(a)])
    orient_faces(p, lambda cc: (cc[0] - Rg["cx"], cc[1] + Rg["cy"], 0.0) if abs(cc[2] - zt) > 1e-5 else (0, 0, 1))
    rug = mesh_obj("SM_MO01_Rug", p, [mats["rug"]], c, sharp=30)
    OUT["items"]["rug"] = dict(size=[round(Rg["l"], 3), round(w_, 3)], centre=[Rg["cx"], Rg["cy"]], x=[round(x0, 3), round(x1, 3)],
                               y=[round(y0, 3), round(y1, 3)], source="AIC 22030 (CC0), full image, restored (Material_Recipes.json)",
                               texture=REC["rug"]["files"]["base_color"]["size"])
    return [floor, ceil_, rug]


# ------------------------------------------------------------------ portraits, picture light
def frame_rebate(af_mesh):
    off = Vector((0.0, 0.0, -500.0))
    tmp = bpy.data.objects.new("_af_probe", af_mesh); bpy.context.scene.collection.objects.link(tmp); tmp.location = off
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
    ow, oh = S.AF02_OPEN[0] / 2, S.AF02_OPEN[1] / 2
    zs = []
    for k in range(40):
        t = k / 40
        for (x, y) in ((-ow - 0.004, -oh + 2 * oh * t), (ow + 0.004, -oh + 2 * oh * t), (-ow + 2 * ow * t, oh + 0.004), (-ow + 2 * ow * t, -oh - 0.004)):
            hit, loc, nor, idx, ob, _ = sc.ray_cast(dg, off + Vector((x, y, 0.3)), Vector((0, 0, -1)), distance=0.6)
            if hit and ob == tmp:
                zs.append(loc.z - off.z)
    bpy.data.objects.remove(tmp, do_unlink=True)
    zs.sort()
    return (zs[len(zs) // 10] if zs else -0.03), (zs[-1] if zs else 0.03)


def build_portraits(mats, c, cL):
    src = next((o for o in bpy.data.objects if o.name.startswith("EC01 | Portrait frame") and o.type == "MESH"), None)
    af = src.data if src else append_object_mesh(AF02_BLEND, ["SM_HotelEden_ArtworkFrame_AF02"])["SM_HotelEden_ArtworkFrame_AF02"]
    OUT["items"]["af02_mesh"] = af.name + (" (the master's own approved AF02 mesh)" if src else " (appended)")
    z_lip, _ = frame_rebate(af)
    tiles = {t["name"]: t for t in REC["portraits"]["tiles"]}
    objs = []
    OUT["portraits"] = []
    for P in S.PORTRAITS:
        if P["wall"] == "W_breast":
            run = RUNS["BF"]; s_ = P["along"] - 3.25; d_face = 0.001
        elif P["wall"] == "N":
            run = RUNS["N"]; s_ = 25.7 - P["along"]; d_face = 0.001
        else:
            run = RUNS["WN"]; s_ = P["along"] - 0.3; d_face = S.CASE["upper_d"] + 0.04 + 0.005
        sc_ = P["scale"]
        back = 0.0632 * sc_
        loc = run.w(s_, d_face + back + 0.002, P["z"])
        rot = Matrix((-run.U, run.Z, run.N)).transposed().to_4x4()
        mw = Matrix.Translation(loc) @ rot @ Matrix.Diagonal((sc_, sc_, sc_, 1))
        fo = place(f"MO01 | Portrait frame | {P['name']}", af, mw, c)
        t = tiles[P["name"]]; u0, v0, u1, v1 = t["uv"]
        ow, oh = S.AF02_OPEN[0] / 2 + 0.010, S.AF02_OPEN[1] / 2 + 0.010
        zc = z_lip - 0.004
        me = bpy.data.meshes.new(f"SM_MO01_Canvas_{P['name']}")
        me.from_pydata([(-ow, -oh, zc), (ow, -oh, zc), (ow, oh, zc), (-ow, oh, zc)], [], [(0, 1, 2, 3)])
        l0 = me.uv_layers.new(name="UV0_Bake"); l1 = me.uv_layers.new(name="UV1_Wood")
        l0.data.foreach_set("uv", np.array([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], np.float32).ravel())
        l1.data.foreach_set("uv", np.array([(x * sc_ / 0.05, y * sc_ / 0.05) for x, y in [(-ow, -oh), (ow, -oh), (ow, oh), (-ow, oh)]], np.float32).ravel())
        me.materials.append(mats["portrait"])
        cv = place(f"MO01 | Portrait canvas | {P['name']}", me, mw, c)
        objs += [fo, cv]
        OUT["portraits"].append(dict(name=P["name"], run=run.name, s=round(s_, 3), z=P["z"], scale=sc_, aic=t["aic"], title=t["title"], artist=t["artist"]))
        if P["name"] == "OverMantel":
            objs += picture_light(run, s_, P["z"] + S.AF02_OUTER[1] * sc_ / 2, mats, c, cL)
    return objs


# ------------------------------------------------------------------ books and the mantel garniture (kits)
def build_books_and_mantel(c):
    """Book-row modules on every open shelf (layout from Books_Rows.json: no module beside or above itself), five
    volumes on the mantel, the candelabra pair and the clock."""
    import mo01_books as B
    rows = json.load(open(os.path.join(KIT, "Books_Rows.json")))
    names = sorted(rows["rows"]) + ["SM_MO01_Books_Mantel"]
    kit = append_object_mesh(KITS["books"], names)
    props = append_object_mesh(KITS["props"], ["SM_MO01_Candelabra", "SM_MO01_Clock"])
    objs, C = [], S.CASE
    pw = C["pil_w"]; crown = S.CASE["upper_d"] - 0.02                       # spines 2 cm behind the cases' front line
    cases = {"South": (RUNS["S"], CASE_S, S.CASE_SOUTH["n_bays"]), "Alcove": (RUNS["WN"], CASE_A, S.CASE_ALCOVE["n_bays"])}
    used = {}
    for key, v in rows["layout"].items():
        case, k, r = key.split("|"); k, r = int(k), int(r)
        run, (s0, s1), nb = cases[case]
        bay = (s1 - s0 - (nb + 1) * pw) / nb
        a = s0 + pw + k * (bay + pw)
        nm = f"SM_MO01_BookRow_{case}_{B.ROW_CLASS[r]}_{v:02d}"
        m = Matrix.Translation(run.w(a, crown, B.SHELF_Z[r])) @ Matrix((run.U, run.N, run.Z)).transposed().to_4x4()
        objs.append(place(f"MO01 | Books | {case} | bay {k} | row {r}", kit[nm], m, c))
        used[nm] = used.get(nm, 0) + 1
    bf = RUNS["BF"]; rot = Matrix((bf.U, bf.N, bf.Z)).transposed().to_4x4(); top = S.MANTEL["shelf_top"]
    MP = S.MANTEL_PROPS
    wbk = kit["SM_MO01_Books_Mantel"]
    width = max(v.co.x for v in wbk.vertices)
    objs.append(place("MO01 | Mantel | Books", wbk, Matrix.Translation(bf.w(MP["books"]["centre"] - 3.25 - width / 2, MP["books"]["d"], top)) @ rot, c))
    for i, cd in enumerate(MP["candelabra"], 1):
        objs.append(place(f"MO01 | Mantel | Candelabra | {i:02d}", props["SM_MO01_Candelabra"], Matrix.Translation(bf.w(cd["along"] - 3.25, cd["d"], top)) @ rot, c))
    ck = MP["clock"]
    objs.append(place("MO01 | Mantel | Clock", props["SM_MO01_Clock"], Matrix.Translation(bf.w(ck["along"] - 3.25, ck["d"], top)) @ rot, c))
    OUT["items"]["books"] = dict(row_modules=len(rows["rows"]), rows_placed=len(rows["layout"]),
                                 volumes_placed=sum(rows["rows"][n]["books"] * u for n, u in used.items()) + 5,
                                 per_module_use=used, atlas="T_MO01_Books 2048 (BaseColor, NormalGL, ORM)", mantel=rows["mantel"])
    OUT["items"]["mantel"] = dict(candelabra=[cd["along"] for cd in MP["candelabra"]], clock=ck["along"], books=MP["books"]["centre"], shelf_top=top)
    return objs


# ------------------------------------------------------------------ the EC01 sconces on the chimney breast
def build_sconces(cL):
    """Two of the Executive Corridor's S06 sconces flanking the over-mantel portrait: the master's own SM_EC01_Sconce_S06
    mesh (shared), each with a Point light at the corridor's Unreal profile (DA_LightProfile_EC01_Sconce)."""
    me = bpy.data.meshes.get("SM_EC01_Sconce_S06")
    assert me is not None, "SM_EC01_Sconce_S06 not in the master"
    flame = Vector(json.load(open(os.path.join(EC_KIT, "Sconce_S06.json")))["flame_local"])
    R = S.LIGHTS["WallSconce"]; bf = RUNS["BF"]
    out = []
    for n, sco in enumerate(S.SCONCES, 1):
        m = bf.matrix(sco["along"] - 3.25, 0.0, sco["flame_z"] - flame.z)
        ob = place(f"MO01 | Sconce S06 | {n:02d}", me, m, cL)
        ob.visible_shadow = False                                    # the fitting never shadows its own lamp
        L = bpy.data.lights.new(S.LIGHT_ID.format(fixture="WallSconce", n=n), "POINT")
        L.shadow_soft_size = R["source_radius_cm"] / 100; L.color = kelvin_rgb(R["temperature_k"]); L.energy = R["lumens"] / 30.0
        L.use_custom_distance = True; L.cutoff_distance = R["attenuation_radius_cm"] / 100
        lo = bpy.data.objects.new(f"Light | {S.LIGHT_ID.format(fixture='WallSconce', n=n)}", L); cL.objects.link(lo)
        lo.matrix_world = Matrix.Translation(m @ (flame + Vector((0, 0, 0.045))))
        ident(lo, "WallSconce", n, R, {"Profile": R["profile"], "SourceRadiusCm": R["source_radius_cm"], "AllowMegaLights": True,
                                        "Fitting": "SM_EC01_Sconce_S06 (EC01 S06, shared)", "ShadeCastShadow": False,
                                        "EmissiveParams": "EmissiveStrength / EmissiveColor on M_EC01_SconceGlass"})
        lo.parent = ob; lo.matrix_parent_inverse = ob.matrix_world.inverted()
        out.append(ob)
    OUT["items"]["sconces"] = [dict(along=sco["along"], flame_z=sco["flame_z"]) for sco in S.SCONCES]
    return out


def kelvin_rgb(k):
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, v)) / 255.0 for v in (r, g, b)]
    c = [v ** 2.2 for v in c]; m = max(c)
    return tuple(v / m for v in c)


def ident(lo, fixture, n, rule, extra):
    lid = S.LIGHT_ID.format(fixture=fixture, n=n)
    props = {"LightId": lid, "Zone": S.ZONE, "Role": rule["role"], "Fixture": fixture, "Lumens": rule["lumens"], "TemperatureK": rule["temperature_k"],
             "AttenuationRadiusCm": rule.get("attenuation_radius_cm"), "Shadows": rule.get("shadows"), "ActorLabel": f"{fixture}_MeredithOffice_{n:02d}",
             "OutlinerFolder": "Lighting/Hotel/MeredithOffice", "Circuit": "Panel.Hotel.MeredithOffice.A (proposed; confirm at Unreal integration)" if fixture != "Fireplace" else "",
             "BlenderPreviewW": round(lo.data.energy, 2)}
    props.update(extra)
    for k, v in props.items():
        if v is not None:
            lo[f"mo01_{k}"] = v
    t = lo.matrix_basis.translation                                  # matrix_world is not evaluated yet in a background build
    OUT.setdefault("lights", []).append(dict(id=lid, plan=[round(t.x, 3), round(-t.y, 3)], z=round(t.z - FL, 3), type=lo.data.type))
    return lo


def picture_light(run, s_, z_top, mats, c, cL):
    """A brass picture light over the over-mantel portrait (the reference shows one): bar on two arms, spot down."""
    p = empty_part()
    zb = z_top + 0.10; dout = 0.17
    tube(p, run.w(s_ - 0.26, dout, zb), run.w(s_ + 0.26, dout, zb), 0.024, 0, n=14)
    for k in (-0.15, 0.15):
        tube(p, run.w(s_ + k, 0.002, zb + 0.06), run.w(s_ + k, dout, zb), 0.007, 0, n=6)
    tube(p, run.w(s_ - 0.04, 0.0, zb + 0.06), run.w(s_ + 0.04, 0.0, zb + 0.06), 0.03, 0, n=8)
    ob = mesh_obj("SM_MO01_PictureLight", p, [mats["brass"]], c, sharp=0)
    R = S.LIGHTS["PictureLight"]
    L = bpy.data.lights.new(S.LIGHT_ID.format(fixture="PictureLight", n=1), "SPOT")
    L.spot_size = math.radians(R["outer_cone_deg"]); L.spot_blend = 1 - R["inner_cone_deg"] / R["outer_cone_deg"]
    L.shadow_soft_size = R["source_radius_cm"] / 100; L.color = kelvin_rgb(R["temperature_k"]); L.energy = R["lumens"] / 30.0
    L.use_custom_distance = True; L.cutoff_distance = R["attenuation_radius_cm"] / 100
    lo = bpy.data.objects.new(f"Light | {S.LIGHT_ID.format(fixture='PictureLight', n=1)}", L); cL.objects.link(lo)
    pos = run.w(s_, dout - 0.01, zb - 0.03)
    aim = run.w(s_, 0.0, z_top - 0.55) - pos
    lo.matrix_world = Matrix.Translation(pos) @ aim.to_track_quat("-Z", "Y").to_matrix().to_4x4()
    ident(lo, "PictureLight", 1, R, {"Rule": "WallSconce", "OuterConeDeg": R["outer_cone_deg"], "InnerConeDeg": R["inner_cone_deg"], "Direction": "down onto the portrait"})
    return [ob]


def build_lights(cL):
    out = []
    R = S.LIGHTS["Fireplace"]
    L = bpy.data.lights.new(S.LIGHT_ID.format(fixture="Fireplace", n=1), "POINT")
    L.shadow_soft_size = R["source_radius_cm"] / 100; L.color = kelvin_rgb(R["temperature_k"]); L.energy = R["lumens"] / 30.0
    L.use_custom_distance = True; L.cutoff_distance = R["attenuation_radius_cm"] / 100
    lo = bpy.data.objects.new(f"Light | {S.LIGHT_ID.format(fixture='Fireplace', n=1)}", L); cL.objects.link(lo)
    lo.location = (17.40, -S.FIRE_C, FL + 0.30)
    ident(lo, "Fireplace", 1, R, {"Flicker": R["flicker"], "SourceRadiusCm": R["source_radius_cm"]})
    out.append(lo)
    R = S.LIGHTS["WindowFill"]
    for n, w in enumerate(WINDOWS, 1):
        run = RUNS[w["run"]]; k = w["kind"]
        Ld = bpy.data.lights.new(S.LIGHT_ID.format(fixture="WindowFill", n=n), "AREA")
        Ld.shape = "RECTANGLE"; Ld.size = 1.70; Ld.size_y = (ARCH[k]["apex"] - ARCH[k]["sill"]) * 0.92
        Ld.color = kelvin_rgb(R["temperature_k"]); Ld.energy = R["lumens"] / 30.0
        Ld.use_custom_distance = True; Ld.cutoff_distance = R["attenuation_radius_cm"] / 100
        Ld.use_shadow = R["shadows"] != "None"                         # Unreal: the office's shadowless fill profile
        lo = bpy.data.objects.new(f"Light | {S.LIGHT_ID.format(fixture='WindowFill', n=n)}", Ld); cL.objects.link(lo)
        zc = (ARCH[k]["apex"] + ARCH[k]["sill"]) / 2
        pos = run.w(w["s"], -0.30, zc)                               # just inside the glass (the reveal is 0.34 deep)
        # the area light emits along its local -Z: aim it into the room (run N); local Y up
        m = Matrix((run.U, run.Z, -run.N)).transposed().to_4x4(); m.translation = pos
        lo.matrix_world = m
        ident(lo, "WindowFill", n, R, {"Window": w["id"], "SizeCm": [170, round(Ld.size_y * 100)], "Note": R["note"]})
        out.append(lo)
    return out


# ------------------------------------------------------------------ colliders
def collider_box(name, mn, mx, mats, c):
    x0, y0, z0 = mn; x1, y1, z1 = mx
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)]
    me = bpy.data.meshes.new(name); me.from_pydata(P, [], F); me.materials.append(mats["collider"]); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob); ob.hide_render = True; ob.display_type = "WIRE"; ob["mo01_collider"] = True
    return ob


def build_colliders(mats, c):
    B = S.BREAST
    out = [collider_box("UCX_SM_MO01_ChimneyBreast_00", (B["x0"], -B["y1"], FL), (B["x1"], -B["y0"], FL + CEIL), mats, c),
           collider_box("UCX_SM_MO01_Mantel_00", (B["x1"], -(S.FIRE_C + 1.0), FL), (B["x1"] + 0.34, -(S.FIRE_C - 1.0), FL + S.MANTEL["shelf_top"]), mats, c),
           collider_box("UCX_SM_MO01_Bookcase_South_00", (17.1, -6.7, FL), (22.50, -(6.7 - S.CASE["base_d"] - 0.03), FL + 3.42), mats, c),
           collider_box("UCX_SM_MO01_Bookcase_Alcove_00", (17.1, -3.25, FL), (17.1 + S.CASE["base_d"] + 0.03, -0.3, FL + 3.42), mats, c)]
    return out


# ------------------------------------------------------------------ the approved furniture (FUR-106 sofa, FUR-107 desk, FUR-108 chair)
def ue_matrix(cm, yaw_deg):
    """Unreal hotel-local (cm, yaw) -> Blender world matrix: conv @ T @ R @ conv, metres (conv = diag(1, -1, 1))."""
    conv = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))
    m = Matrix.Translation(Vector(cm) * 0.01) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")
    return conv @ m @ conv


def build_furniture(c):
    """The owner's three pieces from the approved library, placed after the reference with the numbers Unreal uses (spec
    FURNITURE). The chair keeps its relation to the desk (as Meredith's Life desk advertisements in Unreal)."""
    F = S.FURNITURE; out = []
    kits = {k: append_object_mesh(os.path.join(WS, v["blend"]), v["objects"]) for k, v in F.items()}
    md = ue_matrix(F["desk"]["cm"], F["desk"]["yaw"])
    out.append(place("MO01 | Furniture | Desk (FUR-107)", kits["desk"]["SM_DeskPedestal"], md, c))
    ch = F["chair"]
    mc = md @ ue_matrix(ch["rel_desk_cm"], ch["rel_yaw"])
    out.append(place("MO01 | Furniture | Chair base (FUR-108)", kits["chair"]["SM_ChairSwivel_Base"], mc, c))
    out.append(place("MO01 | Furniture | Chair seat (FUR-108)", kits["chair"]["SM_ChairSwivel_Seat"], mc @ Matrix.Translation((0, 0, ch["seat_z_cm"] * 0.01)), c))
    out.append(place("MO01 | Furniture | Sofa (FUR-106)", kits["sofa"]["SM_SofaChesterfield"], ue_matrix(F["sofa"]["cm"], F["sofa"]["yaw"]), c))
    for o in out:
        o["mo01_fur"] = next(v["fur"] for k, v in F.items() if o.data.name in v["objects"])
    bpy.context.view_layer.update()
    rows = {}
    for o in out:
        bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
        rows[o.name] = dict(mesh=o.data.name, x=[round(min(v.x for v in bb), 3), round(max(v.x for v in bb), 3)],
                            y=[round(min(-v.y for v in bb), 3), round(max(-v.y for v in bb), 3)], z=[round(min(v.z for v in bb) - FL, 3), round(max(v.z for v in bb) - FL, 3)])
    OUT["items"]["furniture"] = dict(spec={k: {kk: vv for kk, vv in v.items() if kk != "objects"} for k, v in F.items()}, placed=rows)
    return out


# ------------------------------------------------------------------ the lobby's stair palm in the north-east corner
def build_corner_palm(c):
    """A copy of the lobby's approved stair palm (FUR-024 P03, LP01) in the corner across from the door: new objects on
    the master's own P03 meshes (nothing duplicated or changed), at the approved P03's own size. The canopy's clearance
    from the walls, the cornice and every window-dressing object is measured on the placed vertices (>= min_clear)."""
    P = S.PALM
    src = bpy.data.objects.get(P["source_placement"])
    assert src is not None, P["source_placement"]
    parts = [o for o in src.children if o.type == "MESH"]
    assert len(parts) == 5, [o.name for o in parts]
    s_ = P["scale"]
    planter = next(o for o in parts if o.name.endswith("Planter"))
    z_foot = min(v.co.z for v in planter.data.vertices)                 # the pot's foot ring sits on the parquet
    m = (Matrix.Translation((P["cx"], -P["cy"], FL + S.FLOOR_T - z_foot * s_)) @ Matrix.Rotation(math.radians(P["yaw_deg"]), 4, "Z")
         @ Matrix.Diagonal((s_, s_, s_, 1.0)))
    pl = bpy.data.objects.new("MO01 | Corner palm | placement", None); c.objects.link(pl)
    pl.empty_display_type = "ARROWS"; pl.empty_display_size = 0.3; pl.matrix_world = m
    for k in ("asset_id", "approved_revision", "source_game_model"):
        if k in src.keys():
            pl[k] = src[k]
    pl["mo01_copy_of"] = src.name; pl["mo01_scale"] = s_
    out = []
    for o in sorted(parts, key=lambda o: o.name):
        ob = bpy.data.objects.new("MO01 | Corner palm | " + o.name.split(" | ")[-1], o.data); c.objects.link(ob)
        ob.parent = pl; ob.matrix_parent_inverse = Matrix.Identity(4); ob.matrix_basis = Matrix.Identity(4)
        for k in o.keys():
            ob[k] = o[k]
        out.append(ob)
    bpy.context.view_layer.update()                                  # evaluate the parented parts' world matrices
    # clearance of the canopy (leaflets and fronds), measured on the placed vertices
    canopy = np.concatenate([np.array([m @ v.co for v in o.data.vertices]) for o in parts
                             if o.data.name.startswith(("P03 |", "SM_HE_Palm_P03_Rachis"))])
    x, y, z = canopy[:, 0], -canopy[:, 1], canopy[:, 2] - FL
    R = S.ROOM
    clear = {"east_wall": round(float(R["x1"] - x.max()), 3), "north_wall": round(float(y.min() - R["y0"]), 3),
             "cornice": round(float(CORNICE_BED - z.max()), 3)}
    hits = {}
    for ob in bpy.data.collections["MO01 | Windows"].objects:
        if ob.type != "MESH":
            continue
        bb = [ob.matrix_world @ Vector(cc) for cc in ob.bound_box]
        lo = np.array([min(v.x for v in bb), min(-v.y for v in bb), min(v.z for v in bb) - FL]) - P["min_clear"]
        hi = np.array([max(v.x for v in bb), max(-v.y for v in bb), max(v.z for v in bb) - FL]) + P["min_clear"]
        n = int(((x > lo[0]) & (x < hi[0]) & (y > lo[1]) & (y < hi[1]) & (z > lo[2]) & (z < hi[2])).sum())
        if n:
            hits[ob.name] = n
    assert not hits and min(clear.values()) >= P["min_clear"], (clear, hits)
    OUT["items"]["corner_palm"] = dict(asset=P["asset"], revision=P["revision"], copy_of=src.name, plan=[P["cx"], P["cy"]],
                                       yaw_deg=P["yaw_deg"], scale=s_, lobby_scale=round(parts[0].matrix_world.to_scale().x, 3),
                                       height_m=round(float(z.max()), 3), canopy_plan_x=[round(float(x.min()), 3), round(float(x.max()), 3)],
                                       canopy_plan_y=[round(float(y.min()), 3), round(float(y.max()), 3)], clearance_m=clear,
                                       window_dressing_hits=hits, meshes=sorted(o.data.name for o in parts))
    return out


# ------------------------------------------------------------------ main
def tri_count(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs if o.type == "MESH")


def pack_images():
    n = 0
    for im in bpy.data.images:
        if im.source == "FILE" and not im.packed_file and im.filepath:
            fp = bpy.path.abspath(im.filepath).replace("\\", "/")
            if "meredith_office_MO01" in fp or "rug-r01-concept" in fp or "/approved-media/" in fp and fp.split("/approved-media/")[1].startswith(
                    ("sofa-chesterfield-cf01", "desk-pedestal-pd01", "chair-swivel-sw01")):
                try:
                    im.pack(); n += 1
                except Exception as e:
                    log("pack failed", im.name, e)
    OUT["packed_images"] = n


def main():
    restore_previous()
    before = inventory()
    root = coll(ROOT)
    cs = {nm: coll(nm, root) for nm in SUB}
    mats = materials()
    log("materials")
    built = {}
    built["mouldings"] = list(build_mouldings(mats, cs["MO01 | Walls"]).values())
    built["dado"] = build_dado(mats, cs["MO01 | Walls"])
    built["paper"] = build_paper(mats, cs["MO01 | Walls"])
    log("walls")
    built["fireplace"] = build_breast(mats, cs["MO01 | Fireplace"]) + build_mantel_and_grate(cs["MO01 | Fireplace"])
    log("fireplace")
    shared = dict(pil=flute_pilaster_mesh(mats), shelf=shelf_mesh(mats), knob=knob_mesh(mats))
    C = S.CASE
    bay_s = (CASE_S[1] - CASE_S[0] - (S.CASE_SOUTH["n_bays"] + 1) * C["pil_w"]) / S.CASE_SOUTH["n_bays"]
    shared["door_w"] = (bay_s - 0.006) / 2
    shared["door"] = door_mesh(mats, shared["door_w"], C["base_h"] - 0.025 - (C["plinth_h"] + 0.025) - 0.006)
    bs, _ = build_bookcase("South", RUNS["S"], CASE_S[0], CASE_S[1], S.CASE_SOUTH["n_bays"], mats, shared, cs["MO01 | Bookcases"], end_visible=(False, True), ladder=True)
    ba, _ = build_bookcase("Alcove", RUNS["WN"], CASE_A[0], CASE_A[1], S.CASE_ALCOVE["n_bays"], mats, shared, cs["MO01 | Bookcases"], end_visible=(False, False))
    built["bookcases"] = bs + ba
    log("bookcases")
    built["windows"] = build_windows(mats, cs["MO01 | Windows"])
    built["door"] = build_door_architrave(mats, cs["MO01 | Door"])
    built["floor"] = build_floor_ceiling_rug(mats, cs["MO01 | Floor and ceiling"])
    built["portraits"] = build_portraits(mats, cs["MO01 | Portraits"], cs["MO01 | Lighting"])
    built["books_mantel"] = build_books_and_mantel(cs["MO01 | Books and mantel"])
    built["sconces"] = build_sconces(cs["MO01 | Lighting"])
    built["palm"] = build_corner_palm(cs["MO01 | Decoration"])
    built["furniture"] = build_furniture(cs["MO01 | Furniture"])
    built["lights"] = build_lights(cs["MO01 | Lighting"])
    built["colliders"] = build_colliders(mats, cs["MO01 | Colliders"])
    log("built")
    # budgets
    OUT["triangles"] = {k: tri_count(v) for k, v in built.items()}
    OUT["sconce_mesh"] = "SM_EC01_Sconce_S06, EC01's own mesh shared by the two placements (counted under sconces)"
    OUT["palm_meshes"] = "FUR-024 P03, the master's own five meshes shared with the lobby's LP01 palms (counted under palm)"
    uniq = {o.data.name for k, v in built.items() if k != "colliders" for o in v if o.type == "MESH"}
    OUT["unique_meshes"] = len(uniq)
    OUT["objects"] = {k: len(v) for k, v in built.items()}
    OUT["visible_triangles"] = sum(v for k, v in OUT["triangles"].items() if k != "colliders")
    after = inventory()
    changed = sorted(n for n in set(before["objects"]) | set(after["objects"]) if before["objects"].get(n) != after["objects"].get(n))
    mesh_changed = sorted(n for n in before["meshes"] if after["meshes"].get(n) != before["meshes"][n])     # new meshes are ours
    OUT["other_objects_changed"] = changed[:50]; OUT["other_meshes_changed"] = mesh_changed[:50]
    assert not changed and not mesh_changed, (changed[:10], mesh_changed[:10])
    pack_images()
    json.dump(OUT, open(os.path.join(BUILD, "Build_MO01.json"), "w"), indent=1, default=str)
    log("BUILD OK", json.dumps({k: OUT[k] for k in ("triangles", "unique_meshes", "visible_triangles", "packed_images")}))
    rv = next((a for a in ARGS if a.startswith("--render")), None)
    if rv:
        import render_mo01
        render_mo01.render_all(rv.split("=", 1)[1].split(",") if "=" in rv else None)
    if "--save" in ARGS:
        bpy.ops.wm.save_mainfile()
        log("SAVED", bpy.data.filepath)


if __name__ == "__main__":
    main()
