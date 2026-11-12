"""MO01 mantel props: the pair of brass candelabra and the mantel clock (Blender, from build_kit_mo01.py).

Owner, 12 Nov 2026 (second review): "Model the books, candalabra and the clock in final game model quality and deliver
them with the room." Both follow the reference's mantel: a five-light brass candelabrum at each end and an arch-top
clock right of centre.

SM_MO01_Candelabra (one mesh, placed twice): a lathe-turned body (domed foot, bead ring, knop, vase baluster, collar,
  arm boss, drip pan and socket), four S-scroll arms with curled brackets and their own drip pans and sockets, and five
  part-burnt candles with wicks; 0.56 m to the tallest wick. High poly: gadrooned foot and vase, beaded rings, wax
  drips. One material, M_MO01_Candelabra: baked BaseColor / NormalGL / ORM (1K; brass tarnished in the recesses).
SM_MO01_Clock: an arch-top mahogany case on a moulded plinth with brass bun feet, a convex brass bezel over an enamel
  dial (T_MO01_ClockDial_BaseColor, prepare_props.py), blued steel hands at 10:09, side sound frets and an urn finial;
  0.215 x 0.135 x 0.31 m. Sections: 0 M_MO01_Clock (baked 1K), 1 M_MO01_ClockDial, 2 M_MO01_ClockGlass.
Frames: Z up from the mantel shelf, the clock's dial faces +Y; the candelabra is symmetric about Z.
Bake (as the mantel): selected to active, Cycles: NORMAL, AO, and EMIT of the high poly's albedo, roughness and metal,
with the EC01 aged brass and mahogany box-projected; composed so that recesses tarnish and dull.
"""
import math, os
import numpy as np
import bmesh, bpy
from mathutils import Vector, Matrix

EC_TEX = "D:/AI_Modelling/hotel_eden/working/executive_EC01/textures"


def srgb(*c):
    c = np.asarray(c, float) / 255
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


ALBEDO = {"wax": srgb(238, 228, 204), "wick": srgb(22, 20, 18), "steel": srgb(30, 36, 60)}
ROUGH = {"wax": 0.48, "wick": 0.9, "steel": 0.35}
METAL = {"brass": 1.0, "steel": 0.8}
TILE = {"brass": ("T_EC01_Brass", 0.25, 1.0), "wood": ("T_EC01_Mahogany", 0.32, 0.6)}  # prefix, tile m, roughness scale


# ------------------------------------------------------------------ mesh builders
def mesh_from(name, verts, faces, c, sharp=50, recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [tuple(int(i) for i in f) for f in faces])
    me.validate(); me.update()
    if recalc:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    if sharp:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def resample(prof, step):
    out = [prof[0]]
    for a, b in zip(prof[:-1], prof[1:]):
        n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return out


def lathe(name, prof, segs, c, lobes=None, M=None, closed_loop=False, sharp=50):
    """Surface of revolution about local Z of prof [(r, z)]; an r = 0 end closes on the axis. lobes(phi, z, r) -> radial
    factor (gadroons, beads). closed_loop: the profile is a closed section (a ring). M places it."""
    phi = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    verts, rings = [], []
    for r, z in prof:
        if r < 1e-7:
            rings.append([len(verts)]); verts.append((0.0, 0.0, z)); continue
        f = lobes(phi, z, r) if lobes else np.ones(segs)
        rings.append(list(range(len(verts), len(verts) + segs)))
        verts += [(r * f[k] * math.cos(phi[k]), r * f[k] * math.sin(phi[k]), z) for k in range(segs)]
    pairs = list(zip(rings[:-1], rings[1:])) + ([(rings[-1], rings[0])] if closed_loop else [])
    faces = []
    for a, b in pairs:
        if len(a) == 1 and len(b) == 1:
            continue
        for k in range(segs):
            k1 = (k + 1) % segs
            if len(a) == 1:
                faces.append((a[0], b[k1], b[k]))
            elif len(b) == 1:
                faces.append((a[k], a[k1], b[0]))
            else:
                faces.append((a[k], a[k1], b[k1], b[k]))
    if M is not None:
        verts = [tuple(M @ Vector(v)) for v in verts]
    return mesh_from(name, verts, faces, c, sharp=sharp)


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def tube(name, pts, radii, sides, c, sharp=None):
    """Closed tube along pts (N, 3) with radii (N,), parallel-transported frames and capped ends."""
    pts = np.asarray(pts, float); N = len(pts)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    a = np.array([0, 0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0, 0])
    U = np.cross(T[0], a); U /= np.linalg.norm(U)
    frames = []
    for i in range(N):
        if i:
            U = U - T[i] * (U @ T[i]); U /= np.linalg.norm(U)
        frames.append((U.copy(), np.cross(T[i], U)))
    verts, faces = [], []
    ang = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    for i in range(N):
        u, v = frames[i]
        verts += [tuple(pts[i] + radii[i] * (math.cos(t) * u + math.sin(t) * v)) for t in ang]
    for i in range(N - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k1, (i + 1) * sides + k1, (i + 1) * sides + k))
    c0 = len(verts); verts.append(tuple(pts[0])); c1 = len(verts); verts.append(tuple(pts[-1]))
    for k in range(sides):
        k1 = (k + 1) % sides
        faces.append((c0, k1, k)); faces.append(((N - 1) * sides + k, (N - 1) * sides + k1, c1))
    return mesh_from(name, verts, faces, c, sharp=sharp)


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


def kind(o, k):
    o["mo01_kind"] = k
    return o


# ------------------------------------------------------------------ bake materials and composition
def emit_mat(K, k, mode):
    """High-poly material for one bake pass: 'shade' (plain BSDF), or emission of the albedo / roughness / metal."""
    name = f"BAKE_{k}_{mode}"
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if mode == "shade":
        b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"]); return m
    e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(e.outputs[0], out.inputs["Surface"])
    if mode == "metal":
        v = METAL.get(k, 0.0); e.inputs["Color"].default_value = (v, v, v, 1); return m
    if k in TILE:
        prefix, tile, rs = TILE[k]
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1 / tile); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        t = nt.nodes.new("ShaderNodeTexImage"); t.projection = "BOX"; t.projection_blend = 0.3
        t.image = K.img(os.path.join(EC_TEX, f"{prefix}_{'BaseColor' if mode == 'albedo' else 'ORM'}.png"), mode != "albedo")
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        if mode == "albedo":
            nt.links.new(t.outputs["Color"], e.inputs["Color"])
        else:
            sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(t.outputs["Color"], sp.inputs["Color"])
            mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = rs
            nt.links.new(sp.outputs["Green"], mu.inputs[0]); nt.links.new(mu.outputs[0], e.inputs["Color"])
        return m
    v = ALBEDO[k] if mode == "albedo" else (ROUGH[k],) * 3
    e.inputs["Color"].default_value = (*v, 1)
    return m


def mat_baked(K, name, prefix):
    """Runtime material: baked BaseColor / NormalGL / ORM (R AO at 0.5, G roughness, B metallic) on UV0."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    def tx(suffix, data):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = K.img(os.path.join(K.TEX, f"{prefix}_{suffix}.png"), data)
        u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "UV0_Bake"; nt.links.new(u.outputs["UV"], t.inputs["Vector"])
        return t
    bc, nm, orm = tx("BaseColor", False), tx("NormalGL", True), tx("ORM", True)
    sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(orm.outputs["Color"], sp.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.5
    nt.links.new(bc.outputs["Color"], mx.inputs["A"]); nt.links.new(sp.outputs["Red"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"]); nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = "UV0_Bake"; nt.links.new(nm.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    return m


def bake_prop(K, low, highs, key, size, slots=None, cage=0.006, dist=0.012):
    def set_high(mode):
        for o in highs:
            m = emit_mat(K, o["mo01_kind"], mode)
            if len(o.data.materials) == 0:
                o.data.materials.append(m)
            else:
                o.data.materials[0] = m
    B = K.BAKE
    set_high("shade")
    K.bake(low, highs, (size, size), "NORMAL", os.path.join(B, f"{key}_Normal.exr"), cage=cage, dist=dist, samples=1, slots=slots)
    K.bake(low, highs, (size, size), "AO", os.path.join(B, f"{key}_AO.exr"), cage=cage, dist=dist, samples=64, slots=slots)
    for mode in ("albedo", "rough", "metal"):
        set_high(mode)
        K.bake(low, highs, (size, size), "EMIT", os.path.join(B, f"{key}_{mode}.exr"), cage=cage, dist=dist, samples=1, slots=slots)
    n = K.exr(os.path.join(B, f"{key}_Normal.exr"))[..., :3]
    ao = K.exr(os.path.join(B, f"{key}_AO.exr"))[..., 0]
    col = K.exr(os.path.join(B, f"{key}_albedo.exr"))[..., :3]
    ro = K.exr(os.path.join(B, f"{key}_rough.exr"))[..., 0]
    me = K.exr(os.path.join(B, f"{key}_metal.exr"))[..., 0]
    metal = (me > 0.5)[..., None]
    wood = (key == "Clock")                                         # a darker, French-polished mahogany than the joinery
    col = np.where(metal, col * (0.60 + 0.40 * ao[..., None] ** 1.3), col * (0.84 + 0.16 * ao[..., None]) * (0.62 if wood else 1.0))
    ro = np.clip(ro + 0.22 * (1 - ao) * metal[..., 0], 0.05, 1)
    K.png(n, f"T_MO01_{key}_NormalGL.png")
    K.png(col, f"T_MO01_{key}_BaseColor.png", srgb=True)
    K.png(np.stack([ao, ro, me], -1), f"T_MO01_{key}_ORM.png")
    for slot in low.material_slots:                                 # the bake targets must not ship with the materials
        nt = slot.material.node_tree
        for n in [n for n in nt.nodes if n.name == "BAKE_TARGET"]:
            nt.nodes.remove(n)


# ------------------------------------------------------------------ candelabra
BODY = [(0, 0.0), (0.074, 0.0), (0.075, 0.003), (0.074, 0.007), (0.070, 0.009), (0.066, 0.011), (0.060, 0.016), (0.052, 0.023),
        (0.046, 0.030), (0.044, 0.033), (0.0465, 0.035), (0.044, 0.037), (0.034, 0.040), (0.024, 0.046), (0.018, 0.052), (0.020, 0.056),
        (0.028, 0.063), (0.030, 0.068), (0.028, 0.073), (0.020, 0.080), (0.014, 0.086), (0.013, 0.095), (0.016, 0.100), (0.022, 0.112),
        (0.027, 0.128), (0.028, 0.142), (0.025, 0.158), (0.018, 0.172), (0.012, 0.184), (0.011, 0.192), (0.016, 0.196), (0.016, 0.201),
        (0.011, 0.205), (0.0095, 0.215), (0.0095, 0.262), (0.014, 0.268), (0.026, 0.276), (0.030, 0.284), (0.028, 0.292), (0.018, 0.298),
        (0.010, 0.304), (0.009, 0.330), (0.014, 0.335), (0.012, 0.340), (0.009, 0.345), (0.012, 0.348), (0.036, 0.350), (0.040, 0.353),
        (0.038, 0.356), (0.020, 0.357), (0.016, 0.358), (0.0155, 0.380), (0.018, 0.384), (0.017, 0.387), (0.0125, 0.387), (0.0125, 0.372),
        (0, 0.372)]
NOZZLE = [(0, 0.300), (0.008, 0.300), (0.010, 0.306), (0.009, 0.312), (0.010, 0.316), (0.032, 0.318), (0.035, 0.321), (0.033, 0.324),
          (0.018, 0.325), (0.015, 0.326), (0.014, 0.346), (0.0165, 0.350), (0.0155, 0.353), (0.0115, 0.353), (0.0115, 0.338), (0, 0.338)]
ARM = ((0.022, 0.284), (0.065, 0.258), (0.118, 0.262), (0.128, 0.300))
CURL = [(0.026, 0.272), (0.040, 0.264), (0.052, 0.254), (0.056, 0.244), (0.051, 0.236), (0.044, 0.237), (0.042, 0.243), (0.046, 0.247)]
CANDLES = [(0.372, 0.190), (0.338, 0.172), (0.338, 0.165), (0.338, 0.178), (0.338, 0.160)]   # base z, length
ARM_PHI = [45, 135, 225, 315]


def lobes_body(phi, z, r):
    f = np.ones_like(phi)
    if 0.010 <= z <= 0.031:                                         # gadrooned dome of the foot
        s = math.sin(math.pi * (z - 0.010) / 0.021)
        f += 0.055 * s * (np.abs(np.cos(8 * phi)) ** 0.6 - 0.6)
    if 0.033 <= z <= 0.037 or 0.196 <= z <= 0.201:                  # beaded rings
        nb = 40 if z < 0.1 else 22
        f += 0.045 * (0.5 + 0.5 * np.cos(nb * phi)) ** 2 * math.sin(math.pi * ((z - (0.033 if z < 0.1 else 0.196)) / (0.004 if z < 0.1 else 0.005)))
    if 0.100 <= z <= 0.150:                                         # gadrooned lower belly of the vase
        s = math.sin(math.pi * (z - 0.100) / 0.050)
        f += 0.07 * s * (np.abs(np.cos(6 * phi)) ** 0.6 - 0.6)
    if 0.268 <= z <= 0.298:                                         # lobed arm boss
        s = math.sin(math.pi * (z - 0.268) / 0.030)
        f += 0.05 * s * (np.abs(np.cos(4 * phi + math.pi / 4)) ** 0.8 - 0.5)
    if 0.348 <= z <= 0.357:                                         # beaded drip-pan rim
        f += 0.03 * (0.5 + 0.5 * np.cos(36 * phi)) ** 2 * (r > 0.03)
    return f


def candle_prof(z0, L, high):
    z1 = z0 + L
    p = [(0, z0), (0.0115, z0), (0.0115, z1 - 0.005), (0.0111, z1 - 0.0015), (0.0100, z1), (0.0075, z1 - 0.0012), (0.0035, z1 - 0.0028), (0, z1 - 0.003)]
    return resample(p, 0.002) if high else p


def candelabra(K):
    cL, cH = K.coll("MO01 | Low"), K.coll("MO01 | High")
    lo, hi = [], []
    lo.append(kind(lathe("CB_body", BODY, 28, cL), "brass"))
    hi.append(kind(lathe("CB_body_HIGH", resample(BODY, 0.0006), 160, cH, lobes=lobes_body), "brass"))
    for i, a in enumerate(ARM_PHI):
        R = Matrix.Rotation(math.radians(a), 4, "Z")
        for res, coll, out, sfx in (((18, 8, 14, 6, 16, 12), cL, lo, ""), ((70, 22, 50, 14, 96, 48), cH, hi, "_HIGH")):
            n_arm, s_arm, n_curl, s_curl, s_noz, s_can = res
            P = bezier(*ARM, n_arm)
            pts = [tuple(R @ Vector((p[0], 0, p[1]))) for p in P]
            out.append(kind(tube(f"CB_arm{i}{sfx}", pts, np.linspace(0.0075, 0.0055, n_arm), s_arm, coll, sharp=None), "brass"))
            cp = np.asarray(CURL)
            t = np.linspace(0, 1, len(cp)); tt = np.linspace(0, 1, n_curl)
            cx, cz = np.interp(tt, t, cp[:, 0]), np.interp(tt, t, cp[:, 1])
            pts = [tuple(R @ Vector((x, 0, z))) for x, z in zip(cx, cz)]
            out.append(kind(tube(f"CB_curl{i}{sfx}", pts, np.linspace(0.0045, 0.0028, n_curl), s_curl, coll, sharp=None), "brass"))
            Mz = Matrix.Translation(R @ Vector((ARM[3][0], 0, 0)))
            out.append(kind(lathe(f"CB_nozzle{i}{sfx}", resample(NOZZLE, 0.0008) if sfx else NOZZLE, s_noz, coll, M=Mz,
                                  lobes=(lambda phi, z, r: 1 + 0.03 * (0.5 + 0.5 * np.cos(30 * phi)) ** 2 * (r > 0.028)) if sfx else None), "brass"))
    for j, (z0, L) in enumerate(CANDLES):
        at = Matrix.Identity(4) if j == 0 else Matrix.Translation(Matrix.Rotation(math.radians(ARM_PHI[j - 1]), 4, "Z") @ Vector((ARM[3][0], 0, 0)))
        rng = np.random.default_rng(31 + j)
        ph, ln = rng.uniform(0, 2 * np.pi, 3), rng.uniform(0.015, 0.05, 3)
        z1 = z0 + L
        def wax_drips(phi, z, r, ph=ph, ln=ln, z1=z1):
            f = np.ones_like(phi)
            for p_, l_ in zip(ph, ln):
                if z1 - l_ <= z <= z1 - 0.002:
                    d = np.angle(np.exp(1j * (phi - p_)))
                    f += 0.10 * np.exp(-(d / 0.18) ** 2) * min(1.0, (z - (z1 - l_)) / 0.008)
            return f
        lo.append(kind(lathe(f"CB_candle{j}", candle_prof(z0, L, False), 12, cL, M=at, sharp=60), "wax"))
        hi.append(kind(lathe(f"CB_candle{j}_HIGH", candle_prof(z0, L, True), 48, cH, M=at, lobes=wax_drips, sharp=60), "wax"))
        for out, coll, sides, sfx in ((lo, cL, 5, ""), (hi, cH, 10, "_HIGH")):
            wp = [tuple(at @ Vector((0.0004 * s, 0, z1 - 0.003 + 0.010 * s))) for s in np.linspace(0, 1, 4)]
            out.append(kind(tube(f"CB_wick{j}{sfx}", wp, np.array([0.0011, 0.0011, 0.0010, 0.0007]), sides, coll), "wick"))
    # one low mesh, one material
    low = join(lo, "SM_MO01_Candelabra")
    low.data.materials.clear(); low.data.materials.append(bpy.data.materials.get("BAKE_low") or bpy.data.materials.new("BAKE_low"))
    low.data.polygons.foreach_set("material_index", np.zeros(len(low.data.polygons), np.int32))
    K.smart_uv(low, margin=0.004, angle=50)
    K.INFO["candelabra"] = dict(low_tris=K.tris(low), high_tris=sum(K.tris(o) for o in hi), maps="1024 BaseColor / NormalGL / ORM",
                                height_m=round(max(v.co.z for v in low.data.vertices), 3), candles=len(CANDLES))
    K.log("candelabra", K.INFO["candelabra"])
    if not K.NOBAKE:
        bake_prop(K, low, hi, "Candelabra", 1024)
    low.data.materials[0] = mat_baked(K, "M_MO01_Candelabra", "T_MO01_Candelabra")
    return low, hi


# ------------------------------------------------------------------ clock
CW, CD, ZB, ZS, RA = 0.215, 0.115, 0.036, 0.165, 0.1075
YF = CD / 2                                                         # the case's front face
DIAL_R = 0.0615


def prism_outline(n_arch):
    pts = [(-CW / 2, ZB)]
    for k in range(n_arch + 1):
        a = math.pi - math.pi * k / n_arch
        pts.append((RA * math.cos(a), ZS + RA * math.sin(a)))
    pts.append((CW / 2, ZB))
    return pts


def case_mesh(name, c, n_arch, bev, seg, inset):
    """Arch-top case: the outline extruded through the depth, its front and back edges rounded (not the base), and a
    sunk border on the front."""
    bm = bmesh.new()
    out = prism_outline(n_arch)
    vb = [bm.verts.new((x, -CD / 2, z)) for x, z in out]
    vf = [bm.verts.new((x, CD / 2, z)) for x, z in out]
    bm.faces.new(vb[::-1]); bm.faces.new(vf)
    n = len(out)
    for k in range(n):
        k1 = (k + 1) % n
        bm.faces.new((vb[k], vb[k1], vf[k1], vf[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    edges = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-7
             and not (e.verts[0].co.z < ZB + 1e-6 and e.verts[1].co.z < ZB + 1e-6)]
    bmesh.ops.bevel(bm, geom=edges, offset=bev, segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    bm.normal_update()
    front = max(bm.faces, key=lambda f: f.calc_center_median().y if abs(f.normal.y) > 0.99 else -1)
    r = bmesh.ops.inset_region(bm, faces=[front], thickness=inset, depth=-0.0015)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool)); me.set_sharp_from_angle(angle=math.radians(40)); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def plinth_mesh(name, c, bev, seg):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.255, 0.135, 0.022), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, 0.025), verts=bm.verts)
    top = [e for e in bm.edges if all(v.co.z > 0.035 for v in e.verts)]
    bmesh.ops.bevel(bm, geom=top, offset=bev, segments=seg, profile=0.7, affect="EDGES", clamp_overlap=True)
    vert = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.004]
    bmesh.ops.bevel(bm, geom=vert, offset=0.004, segments=max(1, seg // 2), profile=0.5, affect="EDGES", clamp_overlap=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool)); me.set_sharp_from_angle(angle=math.radians(40)); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    return ob


def hand_mesh(name, c, angle_deg, length, kind_, y, high):
    """Spade (hour) or slender (minute) hand in the dial plane, 1.2 mm thick, rotated clockwise from XII."""
    if kind_ == "hour":
        o = [(0.0016, -0.010), (0.0016, 0.55), (0.0075, 0.62), (0.0055, 0.74), (0.0020, 0.80), (0.0012, 0.88), (0, 1.0)]
    else:
        o = [(0.0016, -0.16), (0.0034, -0.20), (0.0012, -0.26), (0.0012, 0.20), (0.0010, 0.80), (0, 1.0)]
    pts = [(x, l * length) for x, l in o]
    pts = pts + [(-x, l) for x, l in pts[::-1] if x > 0]
    a = math.radians(angle_deg)
    # seen from the front (+Y) the viewer's right is -X: (right, up) = (x cos a + l sin a, -x sin a + l cos a)
    rot = [(-(x * math.cos(a) + l * math.sin(a)), -x * math.sin(a) + l * math.cos(a)) for x, l in pts]
    n = len(rot); verts = [(x, y, ZS + z) for x, z in rot] + [(x, y + 0.0012, ZS + z) for x, z in rot]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return mesh_from(name, verts, faces, c, sharp=30)


def clock(K):
    cL, cH = K.coll("MO01 | Low"), K.coll("MO01 | High")
    lo, hi = [], []
    toY = Matrix.Rotation(math.radians(-90), 4, "X")               # lathe axis Z -> +Y (the dial's axis)
    for sfx, coll, out, high in (("", cL, lo, False), ("_HIGH", cH, hi, True)):
        out.append(kind(plinth_mesh(f"CK_plinth{sfx}", coll, 0.007 if high else 0.006, 6 if high else 2), "wood"))
        out.append(kind(case_mesh(f"CK_case{sfx}", coll, 64 if high else 20, 0.0055 if high else 0.0045, 6 if high else 2, 0.009), "wood"))
        bun = [(0, 0.0), (0.010, 0.0015), (0.0125, 0.006), (0.011, 0.011), (0.008, 0.014), (0, 0.0145)]
        for fx in (-0.105, 0.105):
            for fy in (-0.050, 0.050):
                out.append(kind(lathe(f"CK_foot{fx:+.2f}{fy:+.2f}{sfx}", resample(bun, 0.001) if high else bun, 48 if high else 10, coll,
                                      M=Matrix.Translation((fx, fy, 0))), "brass"))
        bez = [(0.0605, 0.0), (0.0740, 0.0), (0.0760, 0.003), (0.0750, 0.008), (0.0710, 0.0120), (0.0660, 0.0130), (0.0620, 0.0110), (0.0605, 0.006)]
        knurl = (lambda phi, z, r: 1 + 0.012 * np.abs(np.sin(60 * phi)) * (r > 0.072)) if high else None
        out.append(kind(lathe(f"CK_bezel{sfx}", resample(bez, 0.0008) if high else bez, 128 if high else 32, coll,
                              M=Matrix.Translation((0, YF, ZS)) @ toY, closed_loop=True, lobes=knurl, sharp=60), "brass"))
        out.append(kind(lathe(f"CK_finial{sfx}", [(0, 0), (0.006, 0), (0.008, 0.004), (0.006, 0.008), (0.009, 0.016), (0.007, 0.024),
                                                  (0.003, 0.030), (0.004, 0.033), (0, 0.037)], 48 if high else 10, coll,
                              M=Matrix.Translation((0, 0, ZS + RA - 0.004))), "brass"))
        fret = [(0, 0.0022), (0.024, 0.0022), (0.026, 0.0018), (0.030, 0.0018), (0.033, 0.0012), (0.035, 0.0), (0, 0.0)]
        for sx in (-1, 1):
            Mx = Matrix.Translation((sx * CW / 2, 0, 0.13)) @ Matrix.Rotation(math.radians(90 * sx), 4, "Y")
            out.append(kind(lathe(f"CK_fret{sx:+d}{sfx}", resample(fret, 0.001) if high else fret, 64 if high else 16, coll, M=Mx,
                                  lobes=(lambda phi, z, r: 1 + 0.02 * np.cos(12 * phi) * (r < 0.024)) if high else None), "brass"))
        out.append(kind(hand_mesh(f"CK_hand_h{sfx}", coll, 304.5, 0.040, "hour", YF + 0.0035, high), "steel"))
        out.append(kind(hand_mesh(f"CK_hand_m{sfx}", coll, 54.0, 0.054, "minute", YF + 0.0050, high), "steel"))
        out.append(kind(lathe(f"CK_boss{sfx}", [(0, 0.0072), (0.0026, 0.0072), (0.0030, 0.0060), (0.0030, 0.0), (0, 0.0)], 24 if high else 8, coll,
                              M=Matrix.Translation((0, YF, ZS)) @ toY), "brass"))
    # dial and glass: their own sections, not baked
    dial = lathe("CK_dial", [(0, 0.0015), (DIAL_R, 0.0015), (DIAL_R, -0.001), (0, -0.001)], 48, cL, M=Matrix.Translation((0, YF, ZS)) @ toY, sharp=30)
    glass = lathe("CK_glass", [(0, 0.0125), (0.030, 0.0118), (0.050, 0.0095), (0.0615, 0.0062), (0.0615, 0.0056), (0.050, 0.0089),
                               (0.030, 0.0112), (0, 0.0119)], 40, cL, M=Matrix.Translation((0, YF, ZS)) @ toY, sharp=0)
    mats = [bpy.data.materials.get("BAKE_low") or bpy.data.materials.new("BAKE_low"), dial_material(K), glass_material()]
    for o in lo + [dial, glass]:
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
        idx = 1 if o is dial else 2 if o is glass else 0
        o.data.polygons.foreach_set("material_index", np.full(len(o.data.polygons), idx, np.int32))
    low = join(lo + [dial, glass], "SM_MO01_Clock")
    K.smart_uv(low, margin=0.004, angle=50)
    # the dial face: planar UV across the dial (u right, v up as seen from the front)
    uv = low.data.uv_layers["UV0_Bake"].data
    for p in low.data.polygons:
        if p.material_index == 1:
            for li in p.loop_indices:
                v = low.data.vertices[low.data.loops[li].vertex_index].co
                uv[li].uv = (0.5 - v.x / (2 * DIAL_R), 0.5 + (v.z - ZS) / (2 * DIAL_R))      # viewer's right is -X
    K.INFO["clock"] = dict(low_tris=K.tris(low), high_tris=sum(K.tris(o) for o in hi), maps="1024 BaseColor / NormalGL / ORM + 1024 dial",
                           size_m=[0.255, 0.135, round(ZS + RA + 0.033, 3)], time="10:09")
    K.log("clock", K.INFO["clock"])
    if not K.NOBAKE:
        bake_prop(K, low, hi, "Clock", 1024, slots=[0])
    low.data.materials[0] = mat_baked(K, "M_MO01_Clock", "T_MO01_Clock")
    return low, hi


def dial_material(K):
    m = bpy.data.materials.get("M_MO01_ClockDial") or bpy.data.materials.new("M_MO01_ClockDial")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = K.img(os.path.join(K.TEX, "T_MO01_ClockDial_BaseColor.png"), False)
    u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "UV0_Bake"; nt.links.new(u.outputs["UV"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.28
    return m


def glass_material():
    m = bpy.data.materials.get("M_MO01_ClockGlass") or bpy.data.materials.new("M_MO01_ClockGlass")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.95, 0.95, 0.93, 1); b.inputs["Roughness"].default_value = 0.04
    b.inputs["Alpha"].default_value = 0.12; b.inputs["IOR"].default_value = 1.5           # translucent in Unreal: opacity 0.12
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    m.use_backface_culling = True
    return m
