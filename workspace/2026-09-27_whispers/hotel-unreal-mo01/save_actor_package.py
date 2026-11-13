"""Save exactly one E2K actor package of this task (by actor label) when it is the only dirty package; forest checked first.

    python ue_bridge.py run save_actor_package.py <actor label>
"""
import unreal, json, sys, importlib.util
LABEL = sys.argv[1]
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K" and not ed.get_game_world()
a = next(x for x in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor) if x.get_actor_label() == LABEL)
pkg = a.get_package()
dirty = [p for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert [p.get_name() for p in dirty] == [pkg.get_name()], ("other dirty packages; not saving", [p.get_name() for p in dirty])
A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
vol = next(x for x in A if x.get_actor_label() == "E2K_TestVegetation")
pcg = next(c for c in vol.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "PCGComponent")
cells = [x for x in A if x.get_class().get_name().startswith("PCGPartition")]
ok_forest = pcg.get_editor_property("graph_instance").get_editor_property("graph").get_name() == "PCG_E2K_Vegetation" and len(cells) == 64 and \
    not any(x.get_actor_label().startswith("TO_DELETE") or x.get_actor_location().length() < 1 for x in cells)
assert ok_forest, "forest check failed"
print("SAVED", json.dumps({"label": LABEL, "package": pkg.get_name(), "ok": bool(unreal.EditorLoadingAndSavingUtils.save_packages([pkg], True)),
                           "scale": [a.get_actor_scale3d().x, a.get_actor_scale3d().y, a.get_actor_scale3d().z]}))
