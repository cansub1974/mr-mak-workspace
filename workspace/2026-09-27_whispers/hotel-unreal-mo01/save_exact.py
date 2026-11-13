"""Save exactly the named packages of this task, only when they are precisely the dirty set; E2K forest checked first.

    python ue_bridge.py run save_exact.py <package> [<package> ...]
"""
import unreal, json, sys
WANT = sorted(sys.argv[1:])
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K" and not ed.get_game_world()
dirty = {p.get_name(): p for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
assert sorted(dirty) == WANT, ("dirty set differs; not saving", sorted(dirty))
A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
vol = next(x for x in A if x.get_actor_label() == "E2K_TestVegetation")
pcg = next(c for c in vol.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "PCGComponent")
cells = [x for x in A if x.get_class().get_name().startswith("PCGPartition")]
assert pcg.get_editor_property("graph_instance").get_editor_property("graph").get_name() == "PCG_E2K_Vegetation" and len(cells) == 64 and \
    not any(x.get_actor_label().startswith("TO_DELETE") or x.get_actor_location().length() < 1 for x in cells), "forest check failed"
ok = unreal.EditorLoadingAndSavingUtils.save_packages([dirty[n] for n in WANT], True)
print("SAVED", json.dumps({"ok": bool(ok), "saved": WANT, "dirty_after": [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}))
