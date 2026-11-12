"""Read-only: which level is open, Play state, dirty packages, recent log activity."""
import unreal, json, sys
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ed.get_editor_world()
d = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
print("STATE", json.dumps({"world": w.get_name() if w else None, "path": w.get_path_name() if w else None,
                           "pie": bool(ed.get_game_world()), "dirty": d[:40], "n_dirty": len(d)}))
