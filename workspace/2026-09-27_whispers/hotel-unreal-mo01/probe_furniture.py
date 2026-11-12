"""Read-only: editor world, play state, dirty packages, and every furniture actor in Meredith's office (hotel-local)."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
d = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
res = {"world": W.get_name(), "pie": bool(ed.get_game_world()), "dirty": d}
I = json.load(open(r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/MO01_Install_State.json"))["world"]["instance"]
Ht = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = Ht.inverse()
rows = []
for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor):
    lab = a.get_actor_label()
    if not (str(a.get_folder_path()).startswith("Furniture/Office_MO") or lab.startswith(("TMP_Life_Manager", "Desk", "SM_Desk", "Sofa_", "Chair_"))
            or any(isinstance(c, unreal.StaticMeshComponent) and c.static_mesh and "DeskPedestal" in c.static_mesh.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent))):
        continue
    t = a.get_actor_transform(); lt = unreal.MathLibrary.compose_transforms(t, Hinv)
    r = {"label": lab, "class": a.get_class().get_name(), "folder": str(a.get_folder_path()), "package": a.get_package().get_name(),
         "hidden_ed": a.is_hidden_ed(), "hidden_game": a.get_editor_property("hidden"),
         "local_loc": [round(lt.translation.x, 1), round(lt.translation.y, 1), round(lt.translation.z, 1)],
         "local_yaw": round(lt.rotation.rotator().yaw, 2), "scale": [round(t.scale3d.x, 4), round(t.scale3d.y, 4), round(t.scale3d.z, 4)], "comps": []}
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh:
            mb = c.static_mesh.get_bounding_box()
            r["comps"].append({"comp": c.get_name(), "mesh": c.static_mesh.get_path_name().split(".")[0], "mesh_size_cm": [round(mb.max.x - mb.min.x, 1), round(mb.max.y - mb.min.y, 1), round(mb.max.z - mb.min.z, 1)],
                               "rel_scale": str(c.get_editor_property("relative_scale3d")), "visible": c.is_visible(),
                               "mats": [m.get_path_name().split(".")[0] if m else None for m in c.get_materials()]})
    rows.append(r)
res["furniture"] = rows
print("FURN", json.dumps(res))
