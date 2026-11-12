"""Read-only: the E2K forest check from docs/agents/ue-mcp-toolchain.md (volume graph, partitioning, partition actors)."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
acts = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
vol = next((a for a in acts if a.get_actor_label() == "E2K_TestVegetation"), None)
r = {"world": W.get_name(), "volume": None}
if vol:
    pcg = next((c for c in vol.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "PCGComponent"), None)
    g = pcg.get_editor_property("graph_instance") if pcg else None
    gname = None
    try:
        gname = g.get_editor_property("graph").get_name() if g and g.get_editor_property("graph") else None
    except Exception as e:
        gname = "ERR " + str(e)[:60]
    o, e = vol.get_actor_bounds(False)
    r["volume"] = {"graph": gname, "partitioned": [n for n in dir(pcg) if "partition" in n.lower()][:8] if pcg else None,
                   "loc": [round(vol.get_actor_location().x), round(vol.get_actor_location().y), round(vol.get_actor_location().z)], "extent": [round(e.x), round(e.y), round(e.z)]}
cells = [a for a in acts if a.get_class().get_name().startswith("PCGPartition")]
r["cells"] = len(cells)
r["to_delete"] = sum(1 for a in cells if a.get_actor_label().startswith("TO_DELETE"))
r["at_origin"] = sum(1 for a in cells if a.get_actor_location().length() < 1.0)
r["sample"] = [[a.get_actor_label(), round(a.get_actor_location().x), round(a.get_actor_location().y)] for a in cells[:4]]
print("FOREST", json.dumps(r))
