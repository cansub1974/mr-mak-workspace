"""MO01 drapery for the four arched windows (called from build_kit_mo01.py, Blender).

Window frame: X along the wall (0 = window centre, +X to the right seen from the room), Y out of the wall face into the
room, Z up from the floor top. The surveyed arches (Survey_MO01.json) are slightly pointed two-centred arches on the
approved I06 stone surrounds: outer half-width 1.067 m; N: springing 2.606 / apex 3.766 above the floor; E: 2.346 / 3.466.
The interior stone sills project 0.13 m, so the drapery hangs in front of them.

Owner, 12 Nov 2026 (second review): "Let's see the single swag." Pieces:
  SM_MO01_DrapeSide_L/_R   velvet curtains hung inside the arch, heading under the pelmet line (cloth simulation,
                           mo01_cloth.py; E windows: Z scale 0.905)
  SM_MO01_Sheer            ivory sheer across the glass, heading under the pelmet line (cloth simulation; E: Z 0.905)
  SM_MO01_Swag_N/_E        the single swag per arch, as the reference: hung from the pelmet between t = 0.27 and 0.73,
                           five folds that run from the board's arch into the hem's catenary and gather into the ends
  SM_MO01_Tail_N/_E_L/_R   pleated tails (cascades) over the swag ends; R is the mirror of L, so one bake serves both
  SM_MO01_Fringe_*         bullion fringe cards along the swag hem and the tail hems
The swag and tails are tailored shapes (procedural surfaces): the high poly adds fine creases for the normal bake.
UV0 = the piece's own grid (u, v) for its baked fold normal and AO; UV1 = the flat fabric in metres / tile.
"""
import os
import numpy as np
import bmesh, bpy
import mo01_cloth as C

TILE_VELVET, TILE_SHEER = 0.284, 0.261


def grid_mesh(name, co, uv0, uv1, c, mats, mat_idx=0, smooth=True):
    rows, cols = co.shape[:2]
    V = co.reshape(-1, 3)
    r, cc = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = (r * cols + cc).ravel()
    q = np.stack([a, a + 1, a + cols + 1, a + cols], -1)       # row 0 = top: (u right, v down) -> faces toward +Y
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    F = len(q)
    me.loops.add(F * 4); me.loops.foreach_set("vertex_index", q.astype(np.int32).ravel())
    me.polygons.add(F); me.polygons.foreach_set("loop_start", np.arange(0, 4 * F, 4, dtype=np.int32))
    me.update(calc_edges=True)
    for arr, nm in ((uv0, "UV0_Bake"), (uv1, "UV1_Fabric")):
        A = arr.reshape(-1, 2)[q.ravel()]
        lay = me.uv_layers.new(name=nm); lay.data.foreach_set("uv", A.astype(np.float32).ravel())
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.full(F, mat_idx, np.int32))
    me.polygons.foreach_set("use_smooth", np.full(F, smooth))
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    # faces should look into the room (+Y)
    n = np.zeros(F * 3, np.float32); me.polygons.foreach_get("normal", n)
    if n.reshape(-1, 3)[:, 1].mean() < 0:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()
    return ob


def fringe(name, hem, c, mats):
    """Bullion fringe card hanging 0.055 m below a hem polyline (alpha card, two-sided in the material)."""
    n = len(hem)
    top = hem.copy(); top[:, 1] += 0.004
    bot = top.copy(); bot[:, 2] -= 0.055
    co = np.stack([top, bot], 0)                                  # rows: top, bottom
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(hem[:, [0, 2]], axis=0), axis=1))]
    U = np.stack([L / 0.20, L / 0.20], 0); Vv = np.stack([np.ones(n), np.zeros(n)], 0)
    uv = np.stack([U, Vv], -1)
    return grid_mesh(name, co, uv, uv, c, mats, smooth=True)


def mesh_from_grid(name, P, rest, rows, cols, c, mats, tile=TILE_VELVET):
    """Mesh from (a resampling of) a settled grid. rows/cols index the full grid: UV0 = (u, 1 - v) over the full grid,
    UV1 = the rest (flat) panel's x and z in metres / tile."""
    nv, nu = rest.shape[:2]
    R = rest[np.ix_(rows, cols)]
    UU, VV = np.meshgrid(np.asarray(cols) / (nu - 1), np.asarray(rows) / (nv - 1))
    uv0 = np.stack([UU, 1 - VV], -1)
    uv1 = np.stack([R[..., 0] / tile, R[..., 2] / tile], -1)
    return grid_mesh(name, P, uv0, uv1, c, mats)


def fabric_uv(P, tile):
    """UV1 for a tailored surface: arc length along each row (centred) and down each column, in metres / tile."""
    du = np.linalg.norm(np.diff(P, axis=1), axis=-1); dv = np.linalg.norm(np.diff(P, axis=0), axis=-1)
    su = np.concatenate([np.zeros((P.shape[0], 1)), np.cumsum(du, 1)], 1); su -= su[:, -1:] / 2
    sv = np.concatenate([np.zeros((1, P.shape[1])), np.cumsum(dv, 0)], 0)
    return np.stack([su / tile, -sv / tile], -1)


def vnoise(U, V, fu, fv, seed):
    """Smooth value noise in [0, 1] over the (U, V) grid with fu x fv cells (for irregular creases)."""
    g = np.random.default_rng(seed).random((fv + 2, fu + 2))
    x, y = U * fu, V * fv
    i, j = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - i, y - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = g[j, i], g[j, i + 1], g[j + 1, i], g[j + 1, i + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def swag_surface(kind, nu, nv, high, n_folds=4):
    """The single swag: the board line (pelmet top between the ends) morphs into the hem, a catenary from 0.16 m under
    each end to 0.22 of the rise above the springing. Four folds, crest forward, closer and shallower near the board and
    deepest at the hem, gathered into the ends; the swag bellies forward of the board towards its hem."""
    top, _ = C.arc_points(kind, C.SWAG_T0, 1 - C.SWAG_T0, nu, top=True)
    tx, tz = top[:, 0], top[:, 1] - 0.010
    zs = C.ARCH[kind]["spring"]; rise = C.ARCH[kind]["apex"] - zs
    xe, ze = tx[0], tz[0]
    z_hc, z_he = zs + 0.22 * rise, ze - 0.16
    u = np.linspace(0, 1, nu); v = np.linspace(0, 1, nv)
    U, V = np.meshgrid(u, v)
    bx = (xe + 0.03) * (1 - 2 * u)
    bz = z_hc + (z_he - z_hc) * np.abs(2 * u - 1) ** 1.9
    w = V ** 0.92
    X = tx[None] * (1 - w) + bx[None] * w
    Z = tz[None] * (1 - w) + bz[None] * w
    side = np.sin(np.pi * U) ** 0.5
    wav = 0.05 * np.sin(2 * np.pi * (1.3 * U + 0.4 * V) + 1.1) * np.sin(np.pi * U)       # fold lines not quite regular
    t = (n_folds * V ** 0.8 + wav) % 1.0
    prof = 0.5 - 0.5 * np.cos(2 * np.pi * t ** 0.85)          # soft crests, soft tucks (no seam lines)
    amp = (0.016 + 0.05 * V) * side * (0.78 + 0.44 * vnoise(U, V, 3, 4, 11))
    Y = C.Y_SWAG + amp * prof
    Y += 0.065 * np.sin(np.pi * U) ** 0.8 * V ** 0.7 * (1 - 0.4 * V ** 2)
    if high:
        r = np.minimum(U, 1 - U)
        Y += 0.0045 * (vnoise(U, V, 26, 7, 3) - 0.5) * side * (0.4 + V)
        Y += 0.0020 * (vnoise(U, V, 70, 18, 4) - 0.5)
        Y += 0.0040 * np.exp(-r * 10) * (vnoise(U, V, 4, 24, 5) - 0.5)        # crush lines into the gathered ends
    return np.stack([X, Y, Z], -1)


def tail_surface(kind, nu, nv, high, n_pleats=3):
    """Left tail (cascade): hung from the pelmet top between t = 0.05 and TAIL_T1 in three knife pleats (a broad face
    and a steep return each) that open a little towards the hem. The hem runs from 0.30 m under the springing
    (outside) to 0.42 m above it (inside) and steps down at each pleat's fold."""
    arc, L = C.arc_points(kind, 0.05, C.TAIL_T1, 800, top=True)
    La = np.r_[0, np.cumsum(np.hypot(*np.diff(arc, axis=0).T))]
    u = np.linspace(0, 1, nu); v = np.linspace(0, 1, nv)
    U, V = np.meshgrid(u, v)
    hx = np.interp(u * L, La, arc[:, 0]); hz = np.interp(u * L, La, arc[:, 1]) - 0.010
    zs = C.ARCH[kind]["spring"]
    ph = (n_pleats * u) % 1.0
    tri = np.where(ph < 7 / 9, ph * 9 / 7, (1 - ph) * 9 / 2)        # knife pleat: broad face, steep return (on grid columns)
    zb = (zs - 0.30) * (1 - u) + (zs + 0.42) * u - 0.07 * tri       # each fold hangs lower than its return: a stepped hem
    Z = hz[None] - V * (hz - zb)[None]
    TRI = np.broadcast_to(tri[None], U.shape)
    Y = C.Y_TAIL + 0.075 * (1 - 0.2 * V) * TRI + 0.02 * V
    X = hx[None] + (U - 0.5) * 0.08 * V - 0.02 * V
    if high:
        Y += 0.0035 * (vnoise(U, V, 12, 9, 6) - 0.5) * (0.5 + V) + 0.0015 * (vnoise(U, V, 40, 30, 7) - 0.5)
    return np.stack([X, Y, Z], -1)

def mirrored(name, ob, c):
    """Mirror a drape mesh across the window centre (X); the faces are re-wound to keep looking into the room. The UVs
    are kept, so the mirror uses the same baked maps (tangent space follows the mirrored UVs)."""
    me = ob.data.copy(); me.name = name
    co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3); co[:, 0] *= -1; me.vertices.foreach_set("co", co.ravel())
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    return o


def build(K):
    """K: the build_kit_mo01 module (helpers: coll, bake, exr, png, log, INFO, BAKE, TEX, NOBAKE, tris, img)."""
    import mo01_cloth as C
    cL, cH, cS = K.coll("MO01 | Low"), K.coll("MO01 | High"), K.coll("MO01 | Sim")
    bmat = bpy.data.materials.get("BAKE_drape") or bpy.data.materials.new("BAKE_drape")
    shade = bpy.data.materials.get("BAKE_shade") or bpy.data.materials.new("BAKE_shade")
    out, pieces, fringes, info = {}, [], {}, {}

    def make(key, P, rest, ku, kv, tile=TILE_VELVET, size=1024):
        nv, nu = P.shape[:2]
        hi = mesh_from_grid(f"SM_MO01_{key}_HIGH", P, rest, np.arange(nv), np.arange(nu), cH, [shade], tile)
        Pl, rows, cols = C.resample(P, ku, kv)
        lo = mesh_from_grid(f"SM_MO01_{key}", Pl, rest, rows, cols, cL, [bmat], tile)
        pieces.append((lo, hi, size, key))
        return lo, Pl

    cols_ = C.colliders("N", cS)
    for side in (-1, 1):
        K.log("cloth: side", side)
        P, rest = C.side_cloth(side, cS)
        make(f"DrapeSide_{'R' if side > 0 else 'L'}", P, rest, 3, 6)
    K.log("cloth: sheer")
    P, rest = C.sheer_cloth(cS)
    make("Sheer", P, rest, 3, 6, tile=TILE_SHEER)
    C.remove(cols_)
    for kind in ("N", "E"):
        K.log("tailored: swag and tail", kind)
        for key, fn, hi_res, lo_res, size in ((f"Swag_{kind}", swag_surface, (361, 181), (45, 31), 1024),
                                               (f"Tail_{kind}", tail_surface, (190, 81), (28, 15), 512)):
            Ph = fn(kind, *hi_res, True); Pl = fn(kind, *lo_res, False)
            uvh = np.stack(np.meshgrid(np.linspace(0, 1, hi_res[0]), 1 - np.linspace(0, 1, hi_res[1])), -1)
            uvl = np.stack(np.meshgrid(np.linspace(0, 1, lo_res[0]), 1 - np.linspace(0, 1, lo_res[1])), -1)
            hi = grid_mesh(f"SM_MO01_{key}_HIGH", Ph, uvh, fabric_uv(Ph, TILE_VELVET), cH, [shade])
            lo = grid_mesh(f"SM_MO01_{key}", Pl, uvl, fabric_uv(Pl, TILE_VELVET), cL, [bmat])
            pieces.append((lo, hi, size, key))
            fringes[key + ("_L" if key.startswith("Tail") else "")] = Pl[-1]
        info[f"Swag_{kind}"] = dict(ends_t=[C.SWAG_T0, 1 - C.SWAG_T0], tails_t=[0.004, C.TAIL_T1], folds=5)
    K.INFO["drapes"] = {"tailored": info}
    for lo, hi, size, key in pieces:
        K.INFO["drapes"][lo.name] = dict(low_tris=K.tris(lo), high_tris=K.tris(hi), normal=f"{size}")
        if not K.NOBAKE:
            K.bake(lo, [hi], (size, size), "NORMAL", os.path.join(K.BAKE, f"{key}_Normal.exr"), cage=0.03, dist=0.06, samples=1)
            K.png(K.exr(os.path.join(K.BAKE, f"{key}_Normal.exr"))[..., :3], f"T_MO01_{fold_name(key)}_NormalGL.png")
            K.bake(lo, [hi], (size // 2, size // 2), "AO", os.path.join(K.BAKE, f"{key}_AO.exr"), cage=0.03, dist=0.06, samples=48)
            ao = K.exr(os.path.join(K.BAKE, f"{key}_AO.exr"))[..., 0]
            K.png(np.stack([ao, ao, ao], -1), f"T_MO01_{key}_AO.png")
        out[key] = lo
    for kind in ("N", "E"):
        out[f"Tail_{kind}_L"] = out.pop(f"Tail_{kind}")
        out[f"Tail_{kind}_L"].name = out[f"Tail_{kind}_L"].data.name = f"SM_MO01_Tail_{kind}_L"
        out[f"Tail_{kind}_R"] = mirrored(f"SM_MO01_Tail_{kind}_R", out[f"Tail_{kind}_L"], cL)
        h = fringes[f"Tail_{kind}_L"].copy(); h[:, 0] *= -1
        fringes[f"Tail_{kind}_R"] = h[::-1]
    for key, hem in fringes.items():
        out[f"Fringe_{key}"] = fringe(f"SM_MO01_Fringe_{key}", hem, cL, [bmat])
    mats = drape_materials(K)
    for key, lo in out.items():
        mk = "fringe" if key.startswith("Fringe") else key.rsplit("_", 1)[0] if key.startswith("Tail") else key
        lo.data.materials[0] = mats[mk]
    return out


def fold_name(key):
    """File stem of a piece's baked fold normal. The sheer's is SheerFolds: as "Sheer" it overwrote the tiling weave
    T_MO01_Sheer_NormalGL.png (prepare_textures.sheer), so the sheer tiled its own fold map (found 12 Nov at the Unreal port)."""
    return "SheerFolds" if key == "Sheer" else key


def drape_materials(K):
    """Velvet (tiling velvet on UV1 x baked fold normal + AO on UV0), sheer (alpha), fringe (alpha card)."""
    def node_img(nt, path, data, uv):
        t = nt.nodes.new("ShaderNodeTexImage")
        if os.path.exists(path):
            t.image = K.img(path, data)
        u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = uv; nt.links.new(u.outputs["UV"], t.inputs["Vector"])
        return t
    mats = {}
    for key in ("DrapeSide_L", "DrapeSide_R", "Sheer", "Swag_N", "Swag_E", "Tail_N", "Tail_E"):
        sheer = key == "Sheer"
        m = bpy.data.materials.get(f"M_MO01_{key}") or bpy.data.materials.new(f"M_MO01_{key}")
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
        fab = "T_MO01_Sheer" if sheer else "T_MO01_Velvet"
        bc = node_img(nt, os.path.join(K.TEX, f"{fab}_BaseColor.png"), False, "UV1_Fabric")
        orm = node_img(nt, os.path.join(K.TEX, f"{fab}_ORM.png"), True, "UV1_Fabric")
        fn = node_img(nt, os.path.join(K.TEX, f"{fab}_NormalGL.png"), True, "UV1_Fabric")
        ao = node_img(nt, os.path.join(K.TEX, f"T_MO01_{key}_AO.png"), True, "UV0_Bake")
        bn = node_img(nt, os.path.join(K.TEX, f"T_MO01_{fold_name(key)}_NormalGL.png"), True, "UV0_Bake")
        sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(orm.outputs["Color"], sp.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.8
        nt.links.new(bc.outputs["Color"], mx.inputs["A"]); nt.links.new(ao.outputs["Color"], mx.inputs["B"])
        nt.links.new(mx.outputs["Result"], b.inputs["Base Color"]); nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
        # fold normal (UV0 bake) with the fabric weave (UV1) on top
        n1 = nt.nodes.new("ShaderNodeNormalMap"); n1.uv_map = "UV0_Bake"; nt.links.new(bn.outputs["Color"], n1.inputs["Color"])
        hb = nt.nodes.new("ShaderNodeBump"); hb.inputs["Strength"].default_value = 0.35; hb.inputs["Distance"].default_value = 0.0006
        sepn = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(fn.outputs["Color"], sepn.inputs["Color"])
        nt.links.new(sepn.outputs["Blue"], hb.inputs["Height"]); nt.links.new(n1.outputs["Normal"], hb.inputs["Normal"])
        nt.links.new(hb.outputs["Normal"], b.inputs["Normal"])
        if "Sheen Weight" in b.inputs and not sheer:
            b.inputs["Sheen Weight"].default_value = 0.8; b.inputs["Sheen Roughness"].default_value = 0.35
            b.inputs["Sheen Tint"].default_value = (0.82, 0.88, 0.76, 1)
        if sheer:
            b.inputs["Alpha"].default_value = 0.55
            if "Transmission Weight" in b.inputs:
                b.inputs["Transmission Weight"].default_value = 0.0
            try:
                m.surface_render_method = "BLENDED"
            except Exception:
                pass
            m.use_backface_culling = False
        mats[key] = m
    m = bpy.data.materials.get("M_MO01_Fringe") or bpy.data.materials.new("M_MO01_Fringe")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    t = node_img(nt, os.path.join(K.TEX, "T_MO01_Fringe_BaseColorAlpha.png"), False, "UV0_Bake")
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    nn = node_img(nt, os.path.join(K.TEX, "T_MO01_Fringe_NormalGL.png"), True, "UV0_Bake")
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.uv_map = "UV0_Bake"; nt.links.new(nn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = 0.7; b.inputs["Roughness"].default_value = 0.45
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    m.use_backface_culling = False
    mats["fringe"] = m
    return mats
