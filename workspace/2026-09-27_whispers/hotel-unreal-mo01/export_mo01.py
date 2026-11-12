"""MO01 Meredith's office: MS02 master -> Unreal export (headless Blender; reads the master, never saves it).

    blender -b --factory-startup <MS02.blend> --python export_mo01.py

Owner, 12 Nov 2026: "Sync the corridor lights in MS02 to match Unreal. Then port the Blender model of Meredith's office into
the Unreal Hotel Edn 2k level. Beautiful game quality, moody lighting. Simple colliders."

Writes one FBX per Unreal asset to D:/Unreal Projects/Whispers 5.8/SourceAssets/HotelEden/MO01/meshes, the runtime textures
to .../MO01/textures, and review-media/hotel-unreal-mo01/Export_Manifest.json (+ a copy beside the FBXs).
Frames as EC01 (export_ec01.py): Unreal hotel-local cm = (x, -y, z) x 100 of the Blender model; conv = diag(1, -1, 1).
  * Office parts: one asset per unique mesh, placed as ISM instances. World-space meshes are re-pivoted to their footprint
    centre at floor level; shared meshes (book rows, case parts, drapes, candelabra) keep their own frame.
  * Reused, not exported: the EC01 S06 sconce (BP_EC01_WallSconce_S06) and the AF02 frame (SM_HE_AF02_Frame), after a
    fingerprint check against the EC01 manifest.
  * FUR-024 P03 (the lobby palm): its five meshes as one asset SM_HE_Palm_P03 (five slots) with one UCX box round the
    planter. The approved G01 grate and fuel as SM_HE_Grate_G01 / SM_HE_Fuel_G01 (placed at the master's 0.66 scale).
  * Flame cards (Unreal only, as the lobby fireplace's): three crossed cards over the G01 fuel for M_HE_FireplaceFlame.
  * Tangent UV: two-UV meshes get channel 0 "UVT" = per face the UV their material's normal map uses (EC01 lesson); then
    1 UV0_Bake, 2 UV1_Wood (UV1_Fabric is renamed UV1_Wood). Single-UV meshes keep their one channel.
  * Fabric bump: Blender bumps the drapes with the weave normal map's Blue channel as height (Distance 0.6 mm, Strength
    0.35); that is baked to T_MO01_VelvetBump_NormalGL / T_MO01_SheerBump_NormalGL for the material's grain layer.
Colliders (simple): the master's four UCX boxes (chimney breast, mantel, both bookcases) and the palm's planter box.
"""
import bpy, bmesh, json, hashlib, shutil, os, math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

CARD = Path(__file__).resolve().parents[1]
REC = CARD / "review-media/hotel-unreal-mo01"
OUT = Path("D:/Unreal Projects/Whispers 5.8/SourceAssets/HotelEden/MO01")
EC_MAN = json.loads((CARD / "review-media/hotel-unreal-ec01/Export_Manifest.json").read_text())
HE = "/Game/Whispers/Presentation/Environment/HotelEden"
D = HE + "/MO01"
DEST = {"MO01": D, "P03": HE + "/P03", "G01": HE + "/G01"}
FL = 9.004
for d in (OUT / "meshes", OUT / "textures", REC):
    d.mkdir(parents=True, exist_ok=True)
conv = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))
s = bpy.context.scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ROOT = bpy.data.collections["MO01 | Meredith office"]
MO = list(ROOT.all_objects)
# the master's own objects carry asset names; rename them IN MEMORY so export copies keep the names (never saved)
for _o in list(bpy.data.objects):
    if _o.name.startswith(("SM_MO01_", "UCX_", "SM_HE_", "SM_EC01_")):
        _o.name = _o.name + "__ms02"
xs = bpy.data.scenes.new("MO01 export only")
xs.unit_settings.system = "METRIC"; xs.unit_settings.scale_length = 1.0


def P(*a):
    print("MO01X", *a, flush=True)


def ue_tf(M):
    m = conv @ M @ conv
    lo, qu, sc = m.decompose()
    err = max(abs(m[r][c] - Matrix.LocRotScale(lo, qu, sc)[r][c]) for r in range(4) for c in range(4))
    assert err < 1e-4, ("shear", err)
    assert m.determinant() > 0, "negative determinant"
    return {"translation_cm": [v * 100 for v in lo], "rotation_quat": [qu.x, qu.y, qu.z, qu.w], "scale": list(sc)}


def mesh_copy(o, name):
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = name
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("material_index", mi)
    me.materials.clear()
    for sl in o.material_slots:
        me.materials.append(sl.material)
    me.polygons.foreach_set("material_index", mi); me.update()
    return me


def triangulate(me):
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="FIXED", ngon_method="BEAUTY")
    bm.to_mesh(me); bm.free(); me.update()


def fingerprint(me):
    h = hashlib.sha256()
    for data, field, width, dtype in [(me.vertices, "co", 3, np.float32), (me.loops, "vertex_index", 1, np.int32),
                                      (me.polygons, "material_index", 1, np.int32)]:
        a = np.empty(len(data) * width, dtype=dtype); data.foreach_get(field, a); h.update(np.round(a, 5).tobytes() if dtype == np.float32 else a.tobytes())
    for uv in me.uv_layers:
        a = np.empty(len(uv.data) * 2, dtype=np.float32); uv.data.foreach_get("uv", a); h.update(np.round(a, 5).tobytes())
    return h.hexdigest()


def box_mesh(name, verts, Minv):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for p in verts:
        bm.verts.new(Minv @ p)
    bm.verts.ensure_lookup_table(); bmesh.ops.convex_hull(bm, input=bm.verts); bm.to_mesh(me); bm.free()
    return me


def repivot(me):
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    piv = Vector(((co[:, 0].min() + co[:, 0].max()) / 2, (co[:, 1].min() + co[:, 1].max()) / 2, co[:, 2].min()))
    me.transform(Matrix.Translation(-piv)); me.update()
    return Matrix.Translation(piv)


def world_space(o):
    return all(abs(o.matrix_world[r][c] - (1.0 if r == c else 0.0)) < 1e-9 for r in range(4) for c in range(4))


# tangent UV: the materials whose normal map is on the second (tiling) UV; every other two-UV material uses UV0_Bake
UV1_NORMAL = {"M_EC01_Mahogany", "M_EC01_FiguredVeneer", "M_EC01_HardwareBrass", "M_MO01_Wallpaper", "M_MO01_Parquet",
              "M_MO01_FireBrick", "M_MO01_MarbleHearth", "M_MO01_PelmetVelvet", "M_MO01_Rug", "M_MO01_Portraits"}


def add_tangent_uv(me):
    names = [u.name for u in me.uv_layers]
    if names == ["UV0_Bake", "UV1_Fabric"]:
        me.uv_layers["UV1_Fabric"].name = "UV1_Wood"; names = ["UV0_Bake", "UV1_Wood"]
    if names != ["UV0_Bake", "UV1_Wood"]:
        return False
    n = len(me.loops)
    uv0 = np.empty(n * 2, dtype=np.float32); me.uv_layers["UV0_Bake"].data.foreach_get("uv", uv0)
    uv1 = np.empty(n * 2, dtype=np.float32); me.uv_layers["UV1_Wood"].data.foreach_get("uv", uv1)
    slot = np.array([bool(m and m.name in UV1_NORMAL) for m in me.materials] or [False])
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("material_index", mi)
    ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("loop_total", lt)
    assert ls[0] == 0 and (np.diff(ls) == lt[:-1]).all()
    use1 = np.repeat(slot[mi], lt)
    uvt = np.where(np.repeat(use1, 2), uv1, uv0)
    for name, data in (("UVT", uvt), ("UV0_Bake_n", uv0), ("UV1_Wood_n", uv1)):
        layer = me.uv_layers.new(name=name); layer.data.foreach_set("uv", data)
    me.uv_layers.remove(me.uv_layers["UV0_Bake"]); me.uv_layers.remove(me.uv_layers["UV1_Wood"])
    me.uv_layers["UV0_Bake_n"].name = "UV0_Bake"; me.uv_layers["UV1_Wood_n"].name = "UV1_Wood"
    me.uv_layers.active_index = 0
    for u in me.uv_layers:
        u.active_render = (u.name == "UVT")
    assert [u.name for u in me.uv_layers] == ["UVT", "UV0_Bake", "UV1_Wood"]
    me.update()
    return True


resources = {}


def export_resource(ident, me, ucx=(), kind="part", note="", group="MO01"):
    triangulate(me)
    add_tangent_uv(me)
    for u in ucx:
        triangulate(u)
    bpy.context.window.scene = xs
    for ob in list(xs.collection.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    node = ident.replace("-", "_")
    ob = bpy.data.objects.new(node, me); xs.collection.objects.link(ob)
    uobs = []
    for k, u in enumerate(ucx):
        uo = bpy.data.objects.new(f"UCX_{node}_{k:02d}", u); xs.collection.objects.link(uo); uobs.append(uo)
    bpy.ops.object.select_all(action="DESELECT")
    for o in [ob] + uobs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    p = OUT / "meshes" / (ident + ".fbx")
    has_vc = len(me.color_attributes) > 0
    bpy.ops.export_scene.fbx(filepath=str(p), use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0,
                             axis_forward="-Y", axis_up="Z", use_mesh_modifiers=False, use_tspace=True, mesh_smooth_type="FACE",
                             use_triangles=True, bake_anim=False, path_mode="ABSOLUTE", add_leaf_bones=False,
                             colors_type="LINEAR" if has_vc else "NONE")
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("material_index", mi)
    co = np.empty(len(me.vertices) * 3, dtype=np.float64); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    lo, hi = co.min(0), co.max(0)
    resources[ident] = {"id": ident, "kind": kind, "group": group, "dest": DEST[group] + "/Meshes", "file": "meshes/" + p.name, "note": note,
                        "fingerprint": fingerprint(me), "triangles": len(me.polygons), "vertices": len(me.vertices),
                        "uv_layers": [u.name for u in me.uv_layers], "slots": [m.name if m else None for m in me.materials],
                        "slot_triangles": [int((mi == i).sum()) for i in range(len(me.materials))], "ucx": len(uobs),
                        "vertex_colors": [a.name for a in me.color_attributes],
                        "degenerate_triangles": sum(1 for pg in me.polygons if pg.area < 1e-7),
                        "bounds_cm_ue": [[lo[0] * 100, -hi[1] * 100, lo[2] * 100], [hi[0] * 100, -lo[1] * 100, hi[2] * 100]],
                        "fbx_bytes": p.stat().st_size}
    for o in [ob] + uobs:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.window.scene = s
    P("exported", ident, resources[ident]["triangles"], "tris", len(uobs), "UCX", "vc" if has_vc else "")
    return ident


# ---------------------------------------------------------------------------------------------- classify
lights = [o for o in MO if o.type == "LIGHT"]
colliders = [o for o in MO if o.name.startswith("UCX_")]
sconces = [o for o in MO if o.type == "MESH" and o.name.startswith("MO01 | Sconce S06")]
frames = [o for o in MO if o.type == "MESH" and o.name.startswith("MO01 | Portrait frame")]
palm_pl = next(o for o in MO if o.name == "MO01 | Corner palm | placement")
palm = sorted([o for o in MO if o.parent == palm_pl and o.type == "MESH"], key=lambda o: o.name)
grate = [o for o in MO if o.type == "MESH" and o.name.startswith("MO01 | G01")]
special = set(colliders) | set(sconces) | set(frames) | set(palm) | set(grate)
parts = sorted([o for o in MO if o.type == "MESH" and o not in special], key=lambda o: o.name)
P("objects", len(MO), "parts", len(parts), "sconces", len(sconces), "frames", len(frames), "palm", len(palm), "grate", len(grate),
  "colliders", len(colliders), "lights", len(lights))
placements = []


def ucx_for(base):
    return sorted([c for c in colliders if c.name.startswith("UCX_" + base + "_")], key=lambda c: c.name)


# 1. office parts
done = {}
for o in parts:
    ident = o.data.name
    if ident in done:
        placements.append({"resource": ident, "name": o.name, **ue_tf(o.matrix_world)}); continue
    users = [x for x in parts if x.data == o.data]
    me = mesh_copy(o, ident + "_x")
    single_world = world_space(o) and len(users) == 1
    M = repivot(me) if single_world else o.matrix_world.copy()
    Minv = M.inverted()
    base = o.name.replace("__ms02", "") if o.name.startswith("SM_MO01_") else ident
    ucx = [box_mesh(c.name + "_x", [c.matrix_world @ v.co for v in c.data.vertices], Minv) for c in ucx_for(base)]
    export_resource(ident, me, ucx, "collider_part" if ucx else "part")
    done[ident] = True
    placements.append({"resource": ident, "name": o.name, **ue_tf(M)})
used_ucx = {c.name for o in parts for c in ucx_for(o.name.replace("__ms02", ""))}
assert used_ucx == {c.name for c in colliders}, (sorted(used_ucx), sorted(c.name for c in colliders))

# 2. reused EC01 assets: the AF02 frame and the S06 sconce must be the very meshes EC01 exported
reuse = {}
for objs, rid in ((frames, "SM_HE_AF02_Frame"), (sconces, "SM_EC01_Sconce_S06")):
    o0 = objs[0]; assert all(x.data == o0.data for x in objs)
    me = mesh_copy(o0, rid + "_probe"); triangulate(me); add_tangent_uv(me); fp = fingerprint(me); bpy.data.meshes.remove(me)
    ec = EC_MAN["resources"][rid]
    reuse[rid] = {"path": ec["mesh_path"], "fingerprint_match": fp == ec["fingerprint"], "triangles": ec["triangles"]}
    assert fp == ec["fingerprint"], (rid, "differs from the EC01 export")
for f in sorted(frames, key=lambda o: o.name):
    placements.append({"resource": "SM_HE_AF02_Frame", "name": f.name, "reuse": True, **ue_tf(f.matrix_world)})

# 3. the palm (FUR-024 P03): one asset, five slots, a UCX box round the planter; pivot = the P03 origin (planter foot)
bpy.context.window.scene = xs
tmp = []
for o in palm:
    m = mesh_copy(o, o.data.name + "_x")
    t = bpy.data.objects.new(o.name + "_x", m); xs.collection.objects.link(t); tmp.append(t)
bpy.ops.object.select_all(action="DESELECT")
for t in tmp:
    t.select_set(True)
bpy.context.view_layer.objects.active = tmp[0]
bpy.ops.object.join()
j = tmp[0]; me = j.data; j.data = bpy.data.meshes.new("dummy"); bpy.data.objects.remove(j, do_unlink=True)
bpy.context.window.scene = s
pl = next(o for o in palm if o.name.endswith("Planter")).data
pv = np.array([v.co for v in pl.vertices]); r_ = max(np.abs(pv[:, 0]).max(), np.abs(pv[:, 1]).max())
corners = [Vector((x, y, z)) for x in (-r_, r_) for y in (-r_, r_) for z in (pv[:, 2].min(), pv[:, 2].max())]
export_resource("SM_HE_Palm_P03", me, [box_mesh("UCX_palm_x", corners, Matrix.Identity(4))], "palm",
                "FUR-024 P03 approved game mesh (the lobby LP01 palms' own meshes in MS02): planter, soil, canes, frond midribs, "
                "leaflets; one UCX box round the planter", group="P03")
placements.append({"resource": "SM_HE_Palm_P03", "name": "MO01 | Corner palm", **ue_tf(palm_pl.matrix_world)})

# 4. the approved G01 grate and fuel (in their own frames, placed at the master's uniform 0.66)
for o in grate:
    rid = "SM_HE_Grate_G01" if "grate" in o.name else "SM_HE_Fuel_G01"
    me = mesh_copy(o, rid + "_x")
    export_resource(rid, me, (), "part", "approved G01 " + ("grate" if "grate" in o.name else "fuel") + " game mesh", group="G01")
    placements.append({"resource": rid, "name": o.name, **ue_tf(o.matrix_world)})

# 5. flame cards (Unreal only, as the lobby fireplace's): three crossed cards over the fuel, UV v = 1 at the top in Blender
#    (Unreal flips V: the flame material wants v = 0 at the top of a card and 1 at its base)
fuel = next(o for o in grate if "fuel" in o.name)
bb = [fuel.matrix_world @ Vector(c) for c in fuel.bound_box]
fx = sum(v.x for v in bb) / 8; fy = sum(v.y for v in bb) / 8
fz0 = max(v.z for v in bb) - 0.06; fw = (max(v.y for v in bb) - min(v.y for v in bb)) * 0.95
fh = 0.36
me = bpy.data.meshes.new("SM_MO01_FireCards_x"); bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UV0_Bake")
for yaw, w, dx in ((0.0, fw, 0.0), (math.radians(38), fw * 0.72, -0.03), (math.radians(-38), fw * 0.72, -0.03)):
    ax = Vector((math.sin(yaw), math.cos(yaw), 0.0))           # across the card; yaw 0 = along the breast (model y)
    c0 = Vector((dx, 0.0, 0.0))
    vs = [bm.verts.new(c0 - ax * w / 2), bm.verts.new(c0 + ax * w / 2), bm.verts.new(c0 + ax * w / 2 + Vector((0, 0, fh))),
          bm.verts.new(c0 - ax * w / 2 + Vector((0, 0, fh)))]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = uv
bm.to_mesh(me); bm.free()
fm = bpy.data.materials.get("M_HE_FireplaceFlame") or bpy.data.materials.new("M_HE_FireplaceFlame"); me.materials.append(fm)
export_resource("SM_MO01_FireCards", me, (), "fire", "three crossed flame cards for the hotel's M_HE_FireplaceFlame (as the lobby fireplace)")
placements.append({"resource": "SM_MO01_FireCards", "name": "MO01 | Fire cards", **ue_tf(Matrix.Translation((fx, fy, fz0)))})
fire = {"cards_centre_ue": [fx * 100, -fy * 100, fz0 * 100], "card_width_cm": fw * 100, "card_height_cm": fh * 100,
        "sound_ue": [fx * 100, -fy * 100, (fz0 + 0.1) * 100]}

# 6. sconces and lights (identity from the master's mo01_* properties)
def ident_of(lo):
    return {k: (lo[k] if isinstance(lo[k], (int, float, str)) else str(lo[k])) for k in lo.keys() if k.startswith("mo01_")}


sconce_rows = []
for sc in sorted(sconces, key=lambda o: o.name):
    lt = next(l for l in lights if l.parent == sc)
    rel = sc.matrix_world.inverted() @ lt.matrix_world
    sconce_rows.append({"name": sc.name, "light": lt.name, **ue_tf(sc.matrix_world), "identity": ident_of(lt), "light_world": ue_tf(lt.matrix_world),
                        "light_rel_cm": [rel.translation.x * 100, -rel.translation.y * 100, rel.translation.z * 100]})
ec_rel = EC_MAN["sconces"]["light_relative"]["translation_cm"]
for r in sconce_rows:
    assert max(abs(a - b) for a, b in zip(r["light_rel_cm"], ec_rel)) < 0.05, (r["name"], r["light_rel_cm"], ec_rel)


def facing(lo):
    """Unreal rotation for a light that emits along Blender's local -Z: UE +X = that direction (yaw, pitch), roll 0."""
    d = lo.matrix_world.to_3x3() @ Vector((0, 0, -1)); d.normalize()
    due = Vector((d.x, -d.y, d.z))
    yaw = math.degrees(math.atan2(due.y, due.x)); pitch = math.degrees(math.asin(max(-1, min(1, due.z))))
    return {"yaw": yaw, "pitch": pitch, "roll": 0.0, "dir_ue": list(due)}


light_rows = []
for lo in sorted(lights, key=lambda o: o.name):
    if lo.parent in sconces:
        continue
    L = lo.data; idt = ident_of(lo)
    t = lo.matrix_world.translation
    row = {"name": lo.name, "identity": idt, "type": L.type, "location_ue": [t.x * 100, -t.y * 100, t.z * 100],
           "blender": {"energy_w": L.energy, "radius_m": L.shadow_soft_size, "color": list(L.color), "cutoff_m": L.cutoff_distance}}
    if L.type in ("SPOT", "AREA"):
        row["rotation"] = facing(lo)
    if L.type == "AREA":
        row["blender"].update(size=L.size, size_y=getattr(L, "size_y", L.size), shape=L.shape)
    if L.type == "SPOT":
        row["blender"].update(spot_deg=math.degrees(L.spot_size), blend=L.spot_blend)
    light_rows.append(row)

# 7. textures: every image the exported materials sample (EC01 / AF02 ones exist in Unreal already)
EXISTING = ("T_EC01_", "AF02_")
tex_rows = {}


def tex_kind(name):
    n = name.lower()
    if "normal" in n:
        return "normal_gl"
    if "basecolor" in n:
        return "color"
    return "masks"


def add_image(im, group):
    stem = Path(bpy.path.abspath(im.filepath)).name if im.filepath else im.name
    stem = stem if stem.lower().endswith((".png", ".jpg", ".jpeg")) else stem.split(".")[0] + ".png"
    tid = Path(stem).stem.replace(".", "_")
    if tid.startswith(EXISTING) or tid in tex_rows:
        return tid
    if tid == "Carpet001_2K-JPG_NormalGL":
        tid = "T_MO01_RugPile_NormalGL"
    dst = OUT / "textures" / (tid + Path(stem).suffix.lower())
    src = Path(bpy.path.abspath(im.filepath)) if im.filepath else None
    if src and src.exists():
        shutil.copy2(src, dst)
    else:
        dst = dst.with_suffix(".png"); im.save(filepath=str(dst)) if im.packed_file else None
        assert dst.exists(), (im.name, "no file and not packed")
    tex_rows[tid] = {"id": tid, "file": "textures/" + dst.name, "kind": tex_kind(tid), "group": group, "dest": DEST[group] + "/Textures",
                     "size": list(im.size), "alpha": "BaseColorAlpha" in tid, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()}
    return tid


mat_rows = {}
for o in parts + palm + grate:
    for sl in o.material_slots:
        m = sl.material
        if not m or m.name in mat_rows:
            continue
        group = "P03" if "Palm_P03" in m.name else ("G01" if "Grate_G01" in m.name else "MO01")
        imgs = {}
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                uv = next((l.from_node.uv_map for l in m.node_tree.links if l.to_node == n and l.from_node.type == "UVMAP"), None)
                if uv is None:
                    mp = next((l.from_node for l in m.node_tree.links if l.to_node == n and l.from_node.type == "MAPPING"), None)
                    if mp:
                        uv = next((l.from_node.uv_map for l in m.node_tree.links if l.to_node == mp and l.from_node.type == "UVMAP"), None)
                imgs[n.name] = {"texture": add_image(n.image, group), "uv": uv}
        mat_rows[m.name] = {"group": group, "images": imgs}


def bump_normal(src_png, out_png, distance_m, tile_m):
    """Blender's Bump of a height on a tiling UV (height = the weave normal map's Blue channel here), baked as an OpenGL
    tangent normal (unmixed; the material applies Strength). k = metres of relief per metre of surface per unit height."""
    img = bpy.data.images.load(str(src_png), check_existing=False); img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); hgt = px.reshape(h, w, 4)[..., 2].astype(np.float64)
    k = distance_m * (w / tile_m)
    du = (np.roll(hgt, -1, axis=1) - np.roll(hgt, 1, axis=1)) * 0.5
    dv = (np.roll(hgt, -1, axis=0) - np.roll(hgt, 1, axis=0)) * 0.5
    n = np.stack([-k * du, -k * dv, np.ones_like(du)], axis=-1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    out = bpy.data.images.new(Path(out_png).stem, w, h, alpha=False, float_buffer=False); out.colorspace_settings.name = "Non-Color"
    out.pixels.foreach_set(np.concatenate([n * 0.5 + 0.5, np.ones((h, w, 1))], axis=-1).astype(np.float32).ravel())
    out.filepath_raw = str(out_png); out.file_format = "PNG"; out.save()
    slope = np.degrees(np.arccos(np.clip(n[..., 2], -1, 1)))
    return {"size": [w, h], "k": k, "slope_deg_mean": float(slope.mean()), "slope_deg_p99": float(np.percentile(slope, 99))}


MOTEX = Path("D:/AI_Modelling/hotel_eden/working/meredith_office_MO01/textures")
bumps = {}
for tid, src, tile in (("T_MO01_VelvetBump_NormalGL", "T_MO01_Velvet_NormalGL.png", 0.284), ("T_MO01_SheerBump_NormalGL", "T_MO01_Sheer_NormalGL.png", 0.261)):
    dst = OUT / "textures" / (tid + ".png")
    bumps[tid] = bump_normal(MOTEX / src, dst, 0.0006, tile)
    tex_rows[tid] = {"id": tid, "file": "textures/" + dst.name, "kind": "normal_gl", "group": "MO01", "dest": D + "/Textures",
                     "size": bumps[tid]["size"], "alpha": False, "baked_from": src, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()}

man = {"owner": "Sync the corridor lights in MS02 to match Unreal. Then port the Blender model of Meredith's office into the Unreal "
                "Hotel Edn 2k level. Beautiful game quality, moody lighting. Simple colliders. (12 Nov 2026)",
       "master": bpy.data.filepath, "export_root": str(OUT), "destination_root": D, "destinations": DEST,
       "frame": "Unreal hotel-local cm = (x, -y, z) x 100 of the Blender model",
       "resources": resources, "reuse": reuse, "placements": placements, "sconces": sconce_rows, "lights": light_rows,
       "fire": fire, "textures": list(tex_rows.values()), "materials": mat_rows, "fabric_bumps": bumps,
       "counts": {"resources": len(resources), "placements": len(placements), "sconces": len(sconce_rows), "lights": len(light_rows),
                  "textures": len(tex_rows), "triangles_placed": sum(resources[p["resource"]]["triangles"] if p["resource"] in resources
                                                                     else reuse[p["resource"]]["triangles"] for p in placements)}}
for path in (REC / "Export_Manifest.json", OUT / "Export_Manifest.json"):
    path.write_text(json.dumps(man, indent=1, default=str))
P("MANIFEST OK", json.dumps(man["counts"]))
