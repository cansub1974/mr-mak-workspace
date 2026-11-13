"""MS02 master (saved in place) + export: the ivory sheers must stay behind the sage velvet curtains (owner, 13 Nov 2026: "The
sage curtains should not have the white translucent curtains clipping through them. Please fix those.").

    blender -b --factory-startup <MS02.blend> --python fix_sheer_mo01.py

Why: the sheer and the side curtains were simulated separately (mo01_cloth.py), with no collision between them. Settled, the sheer's
hem and lower folds billow out to 33 cm from the wall face, through the curtains (rear-most folds from 16 cm): 178 of its 1020
game-mesh vertices stood in front of the curtain behind which they hang, by up to 14.5 cm (worst near the floor).
Fix, on the one shared game mesh SM_MO01_Sheer (all four windows): every sheer vertex that hangs behind a curtain (a curtain
vertex within 3.5 cm along the wall and 6 cm in height) goes at least CLEAR behind that curtain's rear-most fold there; the push
is spread to its neighbours (decaying 0.8 per edge ring) so the cloth bends instead of creasing. Nothing moves forward; the open
middle of the window keeps its simulated folds. Bounds kept: 2 cm off the wall face, and in front of the stone sill (0.13 m) at
sill height. Then SM_MO01_Sheer.fbx is exported exactly as export_mo01.export_resource does, and its manifest entry updated.
Writes review-media/meredith-office-mo01/build/Sheer_Fix.json.
"""
import bpy, bmesh, json, os, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
WS = Path("C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers")
MASTER = "D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend"
OUT = Path("D:/Unreal Projects/Whispers 5.8/SourceAssets/HotelEden/MO01")
REC = WS / "review-media/hotel-unreal-mo01"
assert os.path.normcase(os.path.abspath(bpy.data.filepath)) == os.path.normcase(os.path.abspath(MASTER)), bpy.data.filepath
CLEAR, NEAR_X, NEAR_Z, WALL, SILL_PROJ = 0.015, 0.035, 0.06, 0.02, 0.13
SILL = {"N": (10.04 - 9.004, 10.14 - 9.004), "E": ((9.84 - 9.004) / 0.9, (9.94 - 9.004) / 0.9)}   # in the sheer mesh's own Z


def co(me):
    a = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", a); return a.reshape(-1, 3)


sheer = bpy.data.meshes["SM_MO01_Sheer"]
C = np.vstack([co(bpy.data.meshes["SM_MO01_DrapeSide_L"]), co(bpy.data.meshes["SM_MO01_DrapeSide_R"])])
# Always from the settled simulation (the master's sheer before any fix), so the script can be rerun.
ORIG = WS / "review-media/meredith-office-mo01/build/Sheer_Simulated_Original.npy"
S = np.load(ORIG)
assert S.shape == (len(sheer.vertices), 3), S.shape


from mathutils import Vector
from mathutils.bvhtree import BVHTree


def curtain_tree(zscale):
    """The two side curtains as one BVH, in the sheer mesh's frame. The E windows hang the curtains at Z 0.903 and the sheer at
    0.9, so in the sheer's frame their curtains stand 0.903 / 0.9 taller."""
    verts, polys = [], []
    for name in ("SM_MO01_DrapeSide_L", "SM_MO01_DrapeSide_R"):
        me = bpy.data.meshes[name]; base = len(verts)
        verts += [Vector((v.co.x, v.co.y, v.co.z * zscale)) for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
    return BVHTree.FromPolygons(verts, polys)


TREES = [curtain_tree(1.0), curtain_tree(0.903 / 0.9)]
OFFS = [(0, 0), (0.025, 0), (-0.025, 0), (0, 0.04), (0, -0.04)]


def limits(P):
    """Per vertex: the deepest allowed Y - CLEAR behind every curtain surface on the depth lines through the vertex and four
    points round it (inf where no curtain hangs there). Ray casts on the curtain faces, all layers of a fold."""
    lim = np.full(len(P), np.inf)
    for i, (x, y, z) in enumerate(P):
        best = np.inf
        for tree in TREES:
            for dx, dz in OFFS:
                o = Vector((x + dx, 1.0, z + dz)); d = Vector((0, -1, 0))
                for _ in range(8):                                  # every layer along the line
                    hit = tree.ray_cast(o, d, 2.0)
                    if hit[0] is None:
                        break
                    best = min(best, hit[0].y); o = hit[0] + d * 1e-4
        if np.isfinite(best):
            lim[i] = best - CLEAR
    return lim


def report(P, lim):
    cov = np.isfinite(lim)
    over = P[cov, 1] - lim[cov]
    return {"behind_curtains": int(cov.sum()), "too_far_forward": int((over > 1e-6).sum()), "worst_cm": round(float(max(over.max(), 0)) * 100, 2)}


lim = limits(S)
before = report(S, lim)
# required pushes (never forward), then spread along the edges so the cloth bends
need = np.where(np.isfinite(lim), np.minimum(0.0, lim - S[:, 1]), 0.0)
# Local bend, not a global shift: each required push fades to nothing within FALL (along the wall and in height), so only
# the sheer behind and right round the curtains moves; the open middle of the window keeps its simulated folds.
FALL = 0.10
req = np.nonzero(need < 0)[0]
d = need.copy()
for j in req:
    t = np.hypot(S[:, 0] - S[j, 0], S[:, 2] - S[j, 2]) / FALL
    w = np.where(t < 1, 0.5 * (1 + np.cos(np.pi * np.minimum(t, 1))), 0.0)
    d = np.minimum(d, need[j] * w)
new = S.copy(); new[:, 1] = S[:, 1] + d
# bounds: off the wall face; in front of the stone sill at sill height (either window type's sill)
new[:, 1] = np.maximum(new[:, 1], WALL)
for lo, hi in SILL.values():
    at_sill = (new[:, 2] > lo - 0.01) & (new[:, 2] < hi + 0.01)
    new[at_sill, 1] = np.maximum(new[at_sill, 1], SILL_PROJ + 0.005)
after = report(new, lim)
assert after["too_far_forward"] == 0, after
moved = np.abs(new[:, 1] - S[:, 1]) > 1e-3
mid = np.abs(S[:, 0]) < 0.25
sheer.vertices.foreach_set("co", new.astype(np.float32).ravel()); sheer.update()
rec = {"before": before, "after": after, "moved_vertices": int(moved.sum()), "max_push_cm": round(float((S[:, 1] - new[:, 1]).max()) * 100, 2), "middle_max_push_cm": round(float((S[mid, 1] - new[mid, 1]).max()) * 100, 2), "moved_over_1mm": int(moved.sum()),
       "params": {"clear_m": CLEAR, "near_x_m": NEAR_X, "near_z_m": NEAR_Z, "falloff_m": FALL}, "mesh": sheer.name,
       "users": sorted(o.name for o in bpy.data.objects if o.data == sheer)}
bpy.ops.wm.save_mainfile()
print("SHEER_FIX", json.dumps(rec))

# ---- export SM_MO01_Sheer as export_mo01.export_resource does (shared mesh in its own frame) -------------------------------
dg = bpy.context.evaluated_depsgraph_get()
src = bpy.data.objects["MO01 | W3-07 | Sheer"]
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg); me.name = "SM_MO01_Sheer_x"
mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get("material_index", mi)
me.materials.clear()
for sl in src.material_slots:
    me.materials.append(sl.material)
me.polygons.foreach_set("material_index", mi); me.update()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="FIXED", ngon_method="BEAUTY"); bm.to_mesh(me); bm.free(); me.update()
names = [u.name for u in me.uv_layers]
if names == ["UV0_Bake", "UV1_Fabric"]:
    me.uv_layers["UV1_Fabric"].name = "UV1_Wood"
assert [u.name for u in me.uv_layers] == ["UV0_Bake", "UV1_Wood"], [u.name for u in me.uv_layers]
n = len(me.loops)
uv0 = np.empty(n * 2, dtype=np.float32); me.uv_layers["UV0_Bake"].data.foreach_get("uv", uv0)
uv1 = np.empty(n * 2, dtype=np.float32); me.uv_layers["UV1_Wood"].data.foreach_get("uv", uv1)
# M_MO01_Sheer is not in export_mo01.UV1_NORMAL: its tangent UV is UV0_Bake
for name, data in (("UVT", uv0), ("UV0_Bake_n", uv0), ("UV1_Wood_n", uv1)):
    layer = me.uv_layers.new(name=name); layer.data.foreach_set("uv", data)
me.uv_layers.remove(me.uv_layers["UV0_Bake"]); me.uv_layers.remove(me.uv_layers["UV1_Wood"])
me.uv_layers["UV0_Bake_n"].name = "UV0_Bake"; me.uv_layers["UV1_Wood_n"].name = "UV1_Wood"
me.uv_layers.active_index = 0
for u in me.uv_layers:
    u.active_render = (u.name == "UVT")
me.update()
xs = bpy.data.scenes.new("MO01X_sheer"); bpy.context.window.scene = xs
ob = bpy.data.objects.new("SM_MO01_Sheer", me); xs.collection.objects.link(ob)
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
p = OUT / "meshes" / "SM_MO01_Sheer.fbx"
bpy.ops.export_scene.fbx(filepath=str(p), use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0,
                         axis_forward="-Y", axis_up="Z", use_mesh_modifiers=False, use_tspace=True, mesh_smooth_type="FACE",
                         use_triangles=True, bake_anim=False, path_mode="ABSOLUTE", add_leaf_bones=False, colors_type="NONE")
h = hashlib.sha256()
for data, field, width, dtype in [(me.vertices, "co", 3, np.float32), (me.loops, "vertex_index", 1, np.int32), (me.polygons, "material_index", 1, np.int32)]:
    a = np.empty(len(data) * width, dtype=dtype); data.foreach_get(field, a); h.update(np.round(a, 5).tobytes() if dtype == np.float32 else a.tobytes())
for uv in me.uv_layers:
    a = np.empty(len(uv.data) * 2, dtype=np.float32); uv.data.foreach_get("uv", a); h.update(np.round(a, 5).tobytes())
c3 = co(me); lo, hi = c3.min(0), c3.max(0)
entry = {"fingerprint": h.hexdigest(), "triangles": len(me.polygons), "vertices": len(me.vertices), "uv_layers": [u.name for u in me.uv_layers],
         "bounds_cm_ue": [[lo[0] * 100, -hi[1] * 100, lo[2] * 100], [hi[0] * 100, -lo[1] * 100, hi[2] * 100]], "fbx_bytes": p.stat().st_size,
         "note": "13 Nov 2026: kept behind the side curtains (fix_sheer_mo01.py)"}
for man_path in (REC / "Export_Manifest.json", OUT / "Export_Manifest.json"):
    if man_path.exists():
        man = json.loads(man_path.read_text())
        old = man["resources"]["SM_MO01_Sheer"]
        assert old["triangles"] == entry["triangles"] and old["vertices"] == entry["vertices"], (old["triangles"], entry["triangles"])
        old.update(entry); man_path.write_text(json.dumps(man, indent=1))
rec["export"] = entry
(WS / "review-media/meredith-office-mo01/build/Sheer_Fix.json").write_text(json.dumps(rec, indent=1))
print("SHEER_EXPORT", json.dumps(entry))
