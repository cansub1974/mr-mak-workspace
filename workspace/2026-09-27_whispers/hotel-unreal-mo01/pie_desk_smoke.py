"""Meredith at her new desk and chair: a Play smoke that never writes Jason's Continue slot (docs/agents/evidence.md, #219).

    python ue_bridge.py run pie_desk_smoke.py arm       # Play stopped: arm the AgentSmoke slot and request Play at once
    python ue_bridge.py run pie_desk_smoke.py isolate   # first phase in Play: prove the redirect is active
    python ue_bridge.py run pie_meredith.py needs 90 | read <label> | eye desk ...   # observation (pie_meredith.py)
    python ue_bridge.py run pie_desk_smoke.py check     # last phase in Play: the live slot and its 3 backups are unchanged
    python ue_bridge.py run pie_desk_smoke.py stop

Owner, 12 Nov 2026: "yes I do want Meredith to sit and use the new desk and chair". The session continues from the Continue
slot (the restore reads it); every write from the first commit goes to Saved/SaveGames/AgentSmoke/mo01_desk. No NPC is
staged or placed; the clock is not jumped. Rows go to review-media/hotel-unreal-mo01/PIE_Meredith.jsonl.
"""
import unreal, json, sys, os
from WhispersTests import smoke_slot as smoke
PH = sys.argv[1] if len(sys.argv) > 1 else "isolate"
LABEL = "mo01_desk"
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
BEFORE = os.path.join(smoke.saved_dir(), "Tests", "MO01Desk", "slot-before.json")
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)


def log(row):
    open(REC + "/PIE_Meredith.jsonl", "a", encoding="utf-8").write(json.dumps(row, default=str) + "\n"); print("SMOKE", json.dumps(row, default=str)[:3000])


if PH == "arm":
    assert not ed.get_game_world(), "Play is running; stop it first"
    r = smoke.arm(LABEL, BEFORE)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    log({"phase": "smoke_arm", "armed": r["armed"], "requested": r["requested"], "before": {k: (v.get("size"), (v.get("sha256") or "")[:16]) for k, v in r["before"]["files"].items()}})
elif PH == "isolate":
    w = ed.get_game_world(); assert w, "Play required"
    r = smoke.isolate(w, LABEL); log({"phase": "smoke_isolate", **r}); assert r["ok"], r
elif PH == "stage":
    # Smoke-only staging (the slot is redirected, as in #223's re-staging beside the SR01 chairs): Meredith restores at the
    # kitchen's north-west end, room.eden.l1_northwest, whose Life edges are blocked (#215), so no advertisement has a route
    # and she idles. Put her on the office floor east of the desk, projected to the navmesh, standing; Life then decides.
    w = ed.get_game_world(); assert w, "Play required"
    I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
    H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"]))
    a = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith")
    half = a.capsule_component.get_scaled_capsule_half_height()
    want = H.transform_location(unreal.Vector(2250.0, 520.0, 901.7 + half))
    p = unreal.NavigationSystemV1.project_point_to_navigation(w, want, None, None, unreal.Vector(40, 40, 150))
    assert p, "no navmesh at the staging point"
    before = a.get_actor_location()
    a.set_actor_location_and_rotation(unreal.Vector(p.x, p.y, p.z + half), unreal.Rotator(roll=0, pitch=0, yaw=H.rotation.rotator().yaw + 180.0), False, True)
    Hinv = H.inverse(); L = lambda v: [round(c, 1) for c in (lambda q: (q.x, q.y, q.z))(Hinv.transform_location(v))]
    log({"phase": "smoke_stage", "from_local": L(before), "to_local": L(a.get_actor_location()), "nav_local": L(p)})
elif PH == "check":
    r = smoke.verify_file(BEFORE)
    log({"phase": "smoke_check", "ok": r["ok"], "changed": r["changed"]}); assert r["ok"], r["changed"]
elif PH == "stop":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); log({"phase": "smoke_stop"})
else:
    raise SystemExit("unknown phase " + PH)
