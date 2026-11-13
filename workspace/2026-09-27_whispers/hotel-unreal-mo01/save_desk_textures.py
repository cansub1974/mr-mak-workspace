"""Owner, 13 Nov 2026 (restart for the chair C++): "Save them then restart" - the three DeskPedestal textures another session
left unsaved in the editor are saved exactly as they are; nothing else. Refuses if any other package is dirty.

    python ue_bridge.py run save_desk_textures.py
"""
import unreal, json
NAMES = ["/Game/Whispers/Presentation/Environment/HotelEden/Furniture/DeskPedestal/T_DeskPedestal_BC",
         "/Game/Whispers/Presentation/Environment/HotelEden/Furniture/DeskPedestal/T_DeskPedestal_ORM",
         "/Game/Whispers/Presentation/Environment/HotelEden/Furniture/DeskPedestal/T_DeskPedestal_N"]
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert not ed.get_game_world(), "stop Play first"
dirty = {p.get_name(): p for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
assert set(dirty) <= set(NAMES), ("other dirty packages; not saving", sorted(set(dirty) - set(NAMES)))
pkgs = [dirty[n] for n in NAMES if n in dirty]
ok = unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, True) if pkgs else True
after = sorted(p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
print("SAVED", json.dumps({"ok": bool(ok), "saved": [p.get_name() for p in pkgs], "dirty_after": after}))
