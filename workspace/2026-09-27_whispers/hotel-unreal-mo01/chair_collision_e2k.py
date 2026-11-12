"""Let Meredith reach and sit in the new swivel chair (FUR-108) in L_EdenE2K (ue-mcp run_python_file; one stage per call).

    python ue_bridge.py run chair_collision_e2k.py plan | apply | verify

Owner, 12 Nov 2026: "yes I do want Meredith to sit and use the new desk and chair".
Measured (probe_desk_seat.py): her seven Life_Manager_*_SL8 desk slots approach the chair centre (1930, 400) and warp her pelvis
40 cm below it, as authored against the grey TMP_Life_Manager_ChairSeat_SL8 block, which had NoCollision
(npc-life-temp-props.md: the real chair keeps "the seven Life_Manager_*_SL8 advertisements and their approach/use transforms").
The real chair's Base and Seat block every pawn (BlockAllDynamic) and cut the dynamic navmesh, which now projects that approach
point onto the chair top, 103 cm up: no path, so no claim. The project's dining chairs avoid this in code (only the sitter ignores
the chair); this plain Blueprint has no such hook. So the placed chair takes the block's collision role: its two components
ignore the Pawn channel and do not affect navigation; they still block the camera, visibility and physics bodies. The Life
slots, the chair Blueprint asset and the desk are unchanged. Tradeoff: the player can walk through the chair, as through the block.
Guards as furnish_e2k.py: nothing else dirty, E2K forest checked, only the chair's actor package saved. State:
review-media/hotel-unreal-mo01/Chair_Collision_E2K.json (the before values, to restore).
"""
import unreal, json, sys, os
STAGE = sys.argv[1] if len(sys.argv) > 1 else "plan"
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
SF = REC + "/Chair_Collision_E2K.json"
st = json.load(open(SF)) if os.path.exists(SF) else {}
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K", W.get_name()
assert not ed.get_game_world(), "stop Play first"
CH = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor) if a.get_actor_label() == "Chair_Swivel_MO")
COMPS = [c for c in CH.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() in ("Base", "Seat")]
assert len(COMPS) == 2, [c.get_name() for c in COMPS]
PAWN = unreal.CollisionChannel.ECC_PAWN


def comp(name):
    return next(c for c in CH.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == name)


def state(c):
    return {"profile": str(c.get_collision_profile_name()), "enabled": str(c.get_collision_enabled()),
            "pawn": str(c.get_collision_response_to_channel(PAWN)),
            "camera": str(c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA)),
            "visibility": str(c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY)),
            "nav": bool(c.get_editor_property("can_ever_affect_navigation"))}


def dirty():
    return sorted(p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())


def forest():
    A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
    vol = next((a for a in A if a.get_actor_label() == "E2K_TestVegetation"), None); g = None
    if vol:
        pcg = next((c for c in vol.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "PCGComponent"), None)
        gi = pcg.get_editor_property("graph_instance") if pcg else None
        g = gi.get_editor_property("graph").get_name() if gi and gi.get_editor_property("graph") else None
    cells = [a for a in A if a.get_class().get_name().startswith("PCGPartition")]
    r = {"graph": g, "cells": len(cells), "to_delete": sum(1 for a in cells if a.get_actor_label().startswith("TO_DELETE")),
         "at_origin": sum(1 for a in cells if a.get_actor_location().length() < 1.0)}
    r["ok"] = r["graph"] == "PCG_E2K_Vegetation" and r["cells"] == 64 and r["to_delete"] == 0 and r["at_origin"] == 0
    return r


if STAGE == "plan":
    st["before"] = {c.get_name(): state(c) for c in COMPS}; st["package"] = CH.get_package().get_name(); st["dirty_before"] = dirty(); st["forest_before"] = forest()
    json.dump(st, open(SF, "w"), indent=1); print("PLAN", json.dumps(st)[:2000])
elif STAGE == "apply":
    assert st.get("before"), "plan first"
    # Another session's unsaved work (12 Nov: the desk textures being reimported) is left dirty and unsaved: only the chair's
    # package is saved, and nothing beyond it may have become dirty from this edit.
    d0 = dirty(); pkg = CH.get_package(); assert pkg.get_name() not in d0, ("the chair already has unsaved changes; stop", d0)
    f0 = forest(); assert f0["ok"], ("E2K forest check failed; restart the editor", f0)
    # A Blueprint actor reruns its construction script on each edit, which replaces its components (the old ones become
    # TRASH_*): fetch each one fresh by name before editing it, and skip one that is already right (idempotent).
    CH.modify()
    for name in ("Base", "Seat"):
        c = comp(name)
        if "IGNORE" in str(c.get_collision_response_to_channel(PAWN)) and not c.get_editor_property("can_ever_affect_navigation"):
            continue
        c.modify()
        c.set_collision_response_to_channel(PAWN, unreal.CollisionResponseType.ECR_IGNORE)
        comp(name).set_editor_property("can_ever_affect_navigation", False)
    d1 = dirty(); extra = sorted(set(d1) - set(d0) - {pkg.get_name()}); st["others_unsaved_left"] = d0
    f1 = forest(); assert f1["ok"] and not extra, ("not saving", f1, extra)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([pkg], True)
    st.update(applied=True, after={n: state(comp(n)) for n in ("Base", "Seat")}, saved_packages=[pkg.get_name()], forest_at_save=f1, dirty_after=dirty())
    json.dump(st, open(SF, "w"), indent=1); print("APPLIED", json.dumps(st["after"]), "dirty after", st["dirty_after"])
elif STAGE == "verify":
    now = {n: state(comp(n)) for n in ("Base", "Seat")}
    ok = all("IGNORE" in v["pawn"] and not v["nav"] and "BLOCK" in v["camera"] and "QUERY_AND_PHYSICS" in v["enabled"] for v in now.values())
    st["verify"] = {"components": now, "ok": ok, "dirty": dirty()}; json.dump(st, open(SF, "w"), indent=1)
    assert ok, now
    print("VERIFIED", json.dumps(st["verify"]))
else:
    raise SystemExit("unknown stage " + STAGE)
