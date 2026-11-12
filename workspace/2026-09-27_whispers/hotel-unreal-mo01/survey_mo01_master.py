"""Read-only survey of MO01 in the MS02 master for the Unreal port (never saves).

    blender -b --factory-startup <MS02.blend> --python survey_mo01_master.py

Writes review-media/hotel-unreal-mo01/MO01_Blender_Materials.json (every material graph the office uses: nodes, values,
images, UV maps, links, as dump_ec01_materials.py) and MO01_Master_Survey.json (every MO01 object: type, mesh, users,
slots, UV layers, transform, custom properties; and the other master objects inside the office's bounds).
"""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector

CARD = Path(r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers")
REC = CARD / "review-media" / "hotel-unreal-mo01"; REC.mkdir(parents=True, exist_ok=True)
exec(compile(open(CARD / "hotel-unreal-ec01" / "dump_ec01_materials.py", encoding="utf-8").read().split("objs = [o for o in coll")[0]
             .replace('coll = bpy.data.collections.get("EC01 | Executive corridor")\nassert coll, "EC01 collection missing"', ""),
             "dump_helpers", "exec"))
FL = 9.004
root = bpy.data.collections["MO01 | Meredith office"]
bpy.context.view_layer.update()
objs = list(root.all_objects)
used = {}
for o in objs:
    if o.type != "MESH":
        continue
    for slot in o.material_slots:
        if slot.material:
            u = used.setdefault(slot.material.name, {"objects": [], "uv_layers": set()})
            u["objects"].append(o.name); u["uv_layers"] |= {x.name for x in o.data.uv_layers}
mats = {}
for name, info in sorted(used.items()):
    m = bpy.data.materials[name]
    mats[name] = {"objects_count": len(info["objects"]), "objects_sample": info["objects"][:6], "uv_layers": sorted(info["uv_layers"]),
                  "blend_method": getattr(m, "blend_method", None), "surface_render_method": getattr(m, "surface_render_method", None),
                  "use_backface_culling": m.use_backface_culling, "tree": tree(m.node_tree) if m.use_nodes else None}
json.dump({"file": bpy.data.filepath, "materials": mats}, open(REC / "MO01_Blender_Materials.json", "w"), indent=1, default=str)


def coll_of(o):
    return [c.name for c in o.users_collection]


rows = []
for o in sorted(objs, key=lambda o: o.name):
    r = {"name": o.name, "type": o.type, "colls": coll_of(o), "parent": o.parent.name if o.parent else None,
         "matrix_world": [[round(x, 6) for x in row] for row in o.matrix_world],
         "props": {k: (o[k] if isinstance(o[k], (int, float, str)) else str(o[k])) for k in o.keys()}}
    if o.type == "MESH":
        me = o.data
        r.update(mesh=me.name, mesh_users=me.users, tris=sum(len(p.vertices) - 2 for p in me.polygons),
                 slots=[s.material.name if s.material else None for s in o.material_slots], uv=[u.name for u in me.uv_layers],
                 attrs=[a.name for a in me.attributes if a.domain in ("CORNER", "POINT") and a.data_type in ("FLOAT_COLOR", "BYTE_COLOR")],
                 modifiers=[m.type for m in o.modifiers], library=me.library.filepath if me.library else None)
    elif o.type == "LIGHT":
        L = o.data
        r.update(light=dict(type=L.type, energy=L.energy, radius=L.shadow_soft_size, color=list(L.color), cutoff=L.cutoff_distance,
                            spot=getattr(L, "spot_size", None), size=getattr(L, "size", None), size_y=getattr(L, "size_y", None),
                            shape=getattr(L, "shape", None)))
    rows.append(r)
# other master objects inside the office (plan x 17.1-25.7, y 0.3-6.7, z FL-0.1 .. FL+4.3), excluding MO01's own
mine = {o.name for o in objs}
inside = []
for o in bpy.data.objects:
    if o.name in mine or o.type not in ("MESH", "EMPTY", "LIGHT", "CURVE"):
        continue
    if o.type == "MESH":
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    else:
        bb = [o.matrix_world.translation]
    xs = [v.x for v in bb]; ys = [-v.y for v in bb]; zs = [v.z for v in bb]
    if max(xs) > 17.15 and min(xs) < 25.65 and max(ys) > 0.35 and min(ys) < 6.65 and max(zs) > FL + 0.02 and min(zs) < FL + 4.15:
        hidden = o.hide_render or any(c.hide_render for c in o.users_collection)
        inside.append({"name": o.name, "type": o.type, "data": o.data.name if o.data else None, "colls": coll_of(o)[:3], "hidden_render": hidden,
                       "x": [round(min(xs), 3), round(max(xs), 3)], "y": [round(min(ys), 3), round(max(ys), 3)], "z": [round(min(zs) - FL, 3), round(max(zs) - FL, 3)]})
json.dump({"objects": rows, "others_inside_office": inside}, open(REC / "MO01_Master_Survey.json", "w"), indent=1, default=str)
print("SURVEY OK", len(rows), "objects;", len(mats), "materials;", len(inside), "other objects inside the office")
