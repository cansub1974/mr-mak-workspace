"""MO01: checks on the reopened, saved MS02 master (read-only).

    blender -b --factory-startup <MS02> --python check_mo01.py
Writes review-media/meredith-office-mo01/build/Checks_MO01.json.
"""
import bpy, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "review-media", "meredith-office-mo01", "build", "Checks_MO01.json")
root = bpy.data.collections.get("MO01 | Meredith office")
res = {"root_present": root is not None}
if root:
    res["collections"] = {c.name: len(c.objects) for c in root.children_recursive}
    objs = list(root.all_objects)
    res["objects"] = len(objs)
    game = [o for o in objs if o.type == "MESH" and not o.name.startswith("UCX_")]
    res["game_mesh_objects"] = len(game)
    res["game_triangles"] = int(sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in game))
    res["unique_game_meshes"] = len({o.data.name for o in game})
    res["colliders"] = sorted(o.name for o in objs if o.name.startswith("UCX_"))
    res["lights"] = sorted(o.name for o in objs if o.type == "LIGHT")
    res["light_identity_ok"] = all(o.get("mo01_LightId") and o.get("mo01_Zone") == "Light.Zone.Hotel.MeredithOffice" for o in objs if o.type == "LIGHT")
    # every MO01 material's images resolve (packed or on disk)
    imgs = set()
    for o in objs:
        if o.type == "MESH":
            for m in o.data.materials:
                if m and m.node_tree:
                    for n in m.node_tree.nodes:
                        if n.type == "TEX_IMAGE" and n.image:
                            imgs.add(n.image)
    missing = [i.name for i in imgs if not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))]
    res["images_used"] = len(imgs); res["images_packed"] = sum(1 for i in imgs if i.packed_file); res["images_missing"] = missing
    # meshes have UV0/UV1
    res["meshes_without_uv"] = sorted({o.data.name for o in game if len(o.data.uv_layers) == 0})
    # mantel and drapes present
    res["mantel"] = bool(bpy.data.objects.get("SM_MO01_Mantel"))
    res["drape_objects"] = sum(1 for o in objs if "| W3-0" in o.name or "| E13-W" in o.name)
    res["swags"] = sorted({o.data.name for o in objs if o.type == "MESH" and o.data.name.startswith(("SM_MO01_Swag", "SM_MO01_Tail"))})
    res["valance_left"] = [o.name for o in objs if "Valance" in o.name]
    # second review: books, mantel garniture, sconces
    rows = [o for o in objs if o.name.startswith("MO01 | Books |")]
    res["book_rows_placed"] = len(rows); res["book_row_modules"] = len({o.data.name for o in rows})
    res["book_triangles"] = int(sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in rows))
    res["mantel_props"] = sorted(o.name for o in objs if o.name.startswith("MO01 | Mantel |"))
    sc = [o for o in objs if o.name.startswith("MO01 | Sconce S06")]
    res["sconces"] = [dict(name=o.name, mesh=o.data.name, shares_ec01_mesh=o.data.users > 2,
                           light=[c.name for c in o.children if c.type == "LIGHT"]) for o in sc]
    res["sconce_lights"] = {o.name: dict(type=o.data.type, lumens=o.get("mo01_Lumens"), profile=o.get("mo01_Profile"))
                            for o in objs if o.type == "LIGHT" and "WallSconce" in o.name}
    # third review: no TEMP furniture left anywhere; the lobby palm copy on the master's own P03 meshes; the larger rug
    res["temp_left"] = dict(collection=bool(bpy.data.collections.get("MO01 | TEMP furniture (not for export)")),
                            objects=[o.name for o in bpy.data.objects if o.name.startswith("TEMP |")],
                            meshes=[m.name for m in bpy.data.meshes if m.name.startswith("TEMP_")],
                            materials=[m.name for m in bpy.data.materials if m.name.startswith("M_MO01_TEMP")])
    palm = [o for o in objs if o.name.startswith("MO01 | Corner palm |") and o.type == "MESH"]
    lobby = {o.data.name for o in bpy.data.objects if o.name.startswith("LP01 |") and o.type == "MESH"}
    pl = bpy.data.objects.get("MO01 | Corner palm | placement")
    res["corner_palm"] = dict(parts=len(palm), shares_lobby_meshes=bool(palm) and all(o.data.name in lobby for o in palm),
                              asset=pl.get("asset_id") if pl else None, revision=pl.get("approved_revision") if pl else None,
                              plan=[round(pl.matrix_world.translation.x, 3), round(-pl.matrix_world.translation.y, 3)] if pl else None,
                              scale=round(pl.matrix_world.to_scale().x, 3) if pl else None,
                              triangles=int(sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in palm)))
    rug = bpy.data.objects.get("SM_MO01_Rug")
    if rug:
        xs = [(rug.matrix_world @ v.co).x for v in rug.data.vertices]; ys = [-(rug.matrix_world @ v.co).y for v in rug.data.vertices]
        tex = next((n.image for n in rug.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Rug" in n.image.name), None)
        res["rug"] = dict(size=[round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)], x=[round(min(xs), 3), round(max(xs), 3)],
                          y=[round(min(ys), 3), round(max(ys), 3)], texture=list(tex.size) if tex else None)
    fur = [o for o in objs if o.name.startswith("MO01 | Furniture |")]
    res["furniture"] = {o.name: dict(mesh=o.data.name, fur=o.get("mo01_fur"), tris=sum(len(p.vertices) - 2 for p in o.data.polygons),
                                     loc_cm_ue=[round(o.matrix_world.translation.x * 100, 1), round(-o.matrix_world.translation.y * 100, 1),
                                                round(o.matrix_world.translation.z * 100, 1)]) for o in fur}
    mats = {m.name for o in objs if o.type == "MESH" for m in o.data.materials if m}
    res["duplicate_material_names"] = sorted(m for m in mats if m.split(".")[0] != m and m.startswith("M_MO01"))
tr = bpy.data.images.get("T_EC01_Trim_ORM.png")
if tr:
    a = np.array(tr.pixels[:], np.float32).reshape(tr.size[1], tr.size[0], tr.channels)[..., 0]
    res["ec01_trim_ao"] = dict(packed=bool(tr.packed_file), std_across_u=round(float(a.std(1).mean()), 5), mean=round(float(a.mean()), 4))
res["file"] = bpy.data.filepath
json.dump(res, open(OUT, "w"), indent=1)
print("CHECKS", json.dumps({k: v for k, v in res.items() if k not in ("collections",)}))
