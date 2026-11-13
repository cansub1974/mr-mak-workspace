"""Meredith and her swivel desk chair in Play, on the #219 test slot (never WhispersContinue.sav). One phase per ue-mcp call.

    python ue_bridge.py run pie_chair_smoke.py arm            # Play stopped: arm the AgentSmoke slot, request Play
    python ue_bridge.py run pie_chair_smoke.py isolate        # first phase in Play
    python ue_bridge.py run pie_chair_smoke.py stage [x y]    # put her on the office floor (hotel-local; default 2060 600)
    python ue_bridge.py run pie_chair_smoke.py record <sec> <label>   # a per-frame recorder (slate post-tick) for <sec> seconds
    python ue_bridge.py run pie_chair_smoke.py need <Need> <value>    # e.g. Bladder 2: Life then takes her away from the desk
    python ue_bridge.py run pie_chair_smoke.py scale <x>      # game time scale (development)
    python ue_bridge.py run pie_chair_smoke.py check          # last phase in Play: the live slot and its backups unchanged
    python ue_bridge.py run pie_chair_smoke.py stop
Recorder rows (hotel-local cm): Body phase/held/awaiting, activity, chair readback, actor, pelvis and both hands of the VISIBLE
body mesh, the desk top. Rows go to review-media/hotel-unreal-mo01/PIE_Chair_<label>.jsonl.
"""
import unreal, json, sys, os
from WhispersTests import smoke_slot as smoke
PH = sys.argv[1] if len(sys.argv) > 1 else "isolate"
LABEL = "mo01_chair"
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
BEFORE = os.path.join(smoke.saved_dir(), "Tests", "MO01Chair", "slot-before.json")
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
L = lambda v: [round(c, 1) for c in (lambda q: (q.x, q.y, q.z))(Hinv.transform_location(v))]


def log(row, name="PIE_Chair.jsonl"):
    open(os.path.join(REC, name), "a", encoding="utf-8").write(json.dumps(row, default=str) + "\n"); print("CHAIR", json.dumps(row, default=str)[:3000])


def world():
    w = ed.get_game_world(); assert w, "Play required"; return w


def meredith(w):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith")


def label_of(w, name):
    return next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_actor_label() == name), None)


if PH == "arm":
    assert not ed.get_game_world(), "Play is running; stop it first"
    r = smoke.arm(LABEL, BEFORE)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    log({"phase": "arm", "armed": r["armed"], "requested": r["requested"]})
elif PH == "isolate":
    r = smoke.isolate(world(), LABEL); log({"phase": "isolate", **r}); assert r["ok"], r
elif PH == "stage":
    # Smoke-only staging (the slot is redirected): her Continue place is the kitchen's north-west end (no Life routes, #215)
    # until the owner's save is used again; put her on the office floor, standing. Life decides the rest.
    w = world(); a = meredith(w)
    x, y = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (2060.0, 600.0)
    half = a.capsule_component.get_scaled_capsule_half_height()
    p = unreal.NavigationSystemV1.project_point_to_navigation(w, H.transform_location(unreal.Vector(x, y, 901.7 + half)), None, None, unreal.Vector(40, 40, 150))
    assert p, "no navmesh there"
    before = a.get_actor_location()
    a.set_actor_location_and_rotation(unreal.Vector(p.x, p.y, p.z + half), unreal.Rotator(roll=0, pitch=0, yaw=H.rotation.rotator().yaw + 180.0), False, True)
    log({"phase": "stage", "from": L(before), "to": L(a.get_actor_location())})
elif PH == "record":
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0; tag = sys.argv[3] if len(sys.argv) > 3 else "rec"
    w = world(); a = next((x for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if x.commands.get_npc_id() == "npc.meredith"), None)
    b = a.get_component_by_class(unreal.WhispersBodyComponent) if a else None
    ch = label_of(w, "Chair_Swivel_MO"); desk = label_of(w, "Desk_Pedestal_MO")
    top = desk.get_actor_location().z + desk.static_mesh_component.static_mesh.get_bounding_box().max.z * desk.get_actor_scale3d().z
    meshes = [c for c in a.get_components_by_class(unreal.SkeletalMeshComponent)] if a else []
    name = "PIE_Chair_%s.jsonl" % tag
    state = {"t0": unreal.GameplayStatics.get_time_seconds(w), "next": 0.0, "handle": None, "n": 0}
    log({"phase": "record_start", "seconds": seconds, "tag": tag, "desk_top_z": L(unreal.Vector(0, 0, top))[2] if False else round(Hinv.transform_location(unreal.Vector(desk.get_actor_location().x, desk.get_actor_location().y, top)).z, 2),
         "meshes": [(c.get_name(), c.is_visible(), c.get_editor_property("hidden_in_game"), c.skeletal_mesh_asset.get_name() if c.skeletal_mesh_asset else None) for c in meshes]})

    def tick(dt):
        try:
            t = unreal.GameplayStatics.get_time_seconds(w) - state["t0"]
            if t >= seconds:
                unreal.unregister_slate_post_tick_callback(state["handle"]); return
            if t < state["next"]:
                return
            state["next"] = t + 0.2; state["n"] += 1
            # Population may undraw her body (far away) and draw a new one: find her again every row.
            found = [x for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if x.commands.get_npc_id() == "npc.meredith"]
            if not found:
                open(os.path.join(REC, name), "a", encoding="utf-8").write(json.dumps({"t": round(t, 2), "absent": True}) + "\n"); return
            a = found[0]; b = a.get_component_by_class(unreal.WhispersBodyComponent)
            meshes = [c for c in a.get_components_by_class(unreal.SkeletalMeshComponent)]
            act = b.get_editor_property("activity")
            row = {"t": round(t, 2), "phase": str(b.get_editor_property("phase")).split(".")[-1].rstrip(">").split(":")[0], "held": b.get_editor_property("bSeatHeld"),
                   "awaiting": b.get_editor_property("bExitAwaitingSeat"), "active": b.get_editor_property("bSelectedActivityActive"),
                   "activity": act.get_name() if act else None, "chair": ch.readback() if ch else None, "actor": L(a.get_actor_location()),
                   "yaw": round(a.get_actor_rotation().yaw - H.rotation.rotator().yaw, 1)}
            for c in meshes:
                if c.is_visible() and not c.get_editor_property("hidden_in_game") and c.does_socket_exist("pelvis"):
                    row[c.get_name()] = {k: L(c.get_socket_location(k)) for k in ("pelvis", "hand_r", "hand_l", "spine_05", "head")}
            open(os.path.join(REC, name), "a", encoding="utf-8").write(json.dumps(row) + "\n")
        except Exception as e:  # noqa: BLE001
            open(os.path.join(REC, name), "a", encoding="utf-8").write(json.dumps({"error": str(e)}) + "\n")
            unreal.unregister_slate_post_tick_callback(state["handle"])
    state["handle"] = unreal.register_slate_post_tick_callback(tick)
elif PH == "need":
    w = world(); s = next(x for x in unreal.ObjectIterator(unreal.WhispersLifeSubsystem) if x.get_outer() == w)
    log({"phase": "need", "need": sys.argv[2], "value": sys.argv[3], "reply": s.development("set_need", "npc.meredith", {"need": "Life.Need." + sys.argv[2], "value": sys.argv[3]})[:200]})
elif PH == "scale":
    w = world(); s = next(x for x in unreal.ObjectIterator(unreal.WhispersLifeSubsystem) if x.get_outer() == w)
    log({"phase": "scale", "reply": s.development("time_scale", "", {"scale": sys.argv[2]})[:200]})
elif PH == "come":
    # A short walk to the player (development command, smoke only): the held desk chair rolls out and turns, she stands and
    # walks over; Life then takes her back to the desk, where she sits, turns and rolls in.
    w = world(); a = meredith(w)
    ok = a.commands.run_development_command("npc.move_to", {"npc": "npc.meredith", "target": "player", "urgency": "walk"}, "")
    log({"phase": "come", "admitted": ok})
elif PH == "check":
    r = smoke.verify_file(BEFORE); log({"phase": "check", "ok": r["ok"], "changed": r["changed"]}); assert r["ok"], r["changed"]
elif PH == "stop":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); log({"phase": "stop"})
else:
    raise SystemExit("unknown phase " + PH)
