"""Meredith at her new desk (FUR-107) and chair (FUR-108): bounded Play observation in L_EdenE2K, after tools/life/sl8_cover.py.
One phase per ue-mcp call; NPC movement is never placed, only the clock is set.

    python ue_bridge.py run pie_meredith.py jump <minute> | read <label> | eye <name> | scale <x>
Owner, 12 Nov 2026: "yes I do want Meredith to sit and use the new desk and chair".
Writes review-media/hotel-unreal-mo01/PIE_Meredith.jsonl.
"""
import unreal, json, sys, math
PH = sys.argv[1] if len(sys.argv) > 1 else "read"; ARG = sys.argv[2] if len(sys.argv) > 2 else ""
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
SIT = (1930.0, 400.0, 951.3)                 # the Desk_* use point, hotel-local cm (marker 991.3 - 40)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); assert w, "PIE world required"
s = next(x for x in unreal.ObjectIterator(unreal.WhispersLifeSubsystem) if x.get_outer() == w)
r = next(x for x in unreal.ObjectIterator(unreal.WhispersWorldRegistrySubsystem) if x.get_outer() == w)


def loc_local(v):
    p = Hinv.transform_location(v); return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]


def log(row):
    open(REC + "/PIE_Meredith.jsonl", "a", encoding="utf-8").write(json.dumps(row, default=str) + "\n"); print("MEREDITH", json.dumps(row, default=str)[:3000])


if PH == "jump":
    log({"phase": "jump", "jump": s.development("jump_time", "", {"minute": ARG or "600"}), "scale": s.development("time_scale", "", {"scale": "1"})})
elif PH == "needs":
    # as the Life smokes (held_prop_smoke_227): needs satisfied, so the routine chooses work over meals and breaks
    out = {n: s.development("set_need", "npc.meredith", {"need": "Life.Need." + n, "value": ARG or "90"})[:60]
           for n in ("Energy", "Hunger", "Thirst", "Bladder", "Hygiene", "Rest", "Social", "Fun")}
    log({"phase": "needs", "value": ARG or "90", "ok": all("true" in v for v in out.values()), "replies": out})
elif PH == "scale":
    log({"phase": "scale", "scale": s.development("time_scale", "", {"scale": ARG or "1"})})
elif PH == "read":
    l = s.runner("npc.meredith"); read = json.loads(s.development("read", "npc.meredith", {})) if l else None
    keep = {k: read.get(k) for k in ("active_role", "block", "phase", "slot", "step", "drawn", "day", "minute", "claim", "activity", "target")} if read else None
    a = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith"), None)
    row = {"phase": "read", "label": ARG, "world_seconds": unreal.GameplayStatics.get_time_seconds(w), "life": keep, "band": l.active_band if l else None}
    if a:
        p = loc_local(a.get_actor_location()); b = a.get_component_by_class(unreal.WhispersBodyComponent)
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        pel = loc_local(mesh.get_socket_location("pelvis")) if mesh else None
        row.update(position_local=p, yaw_local=round(a.get_actor_rotation().yaw - H.rotation.rotator().yaw, 1), room=str(r.resolve_room(a.get_actor_location())),
                   body=b.get_activity_readback()[:400] if b else None, pelvis_local=pel,
                   to_sit_cm=round(math.dist(p[:2], SIT[:2]), 1), hidden=a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else None)
    row["read_keys"] = sorted(read.keys())[:40] if read else None
    log(row)
elif PH == "eye":
    VIEWS = {"desk": ((2330, 560, 900.4 + 165), (1960, 380, 900.4 + 95)), "desk_side": ((1990, 120, 900.4 + 160), (1960, 410, 900.4 + 80)),
             "room": ((2510, 605, 900.4 + 155), (1760, 290, 900.4 + 145))}
    eye, at = VIEWS[ARG or "desk"]
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0); off = pawn.get_actor_eyes_view_point()[0] - pawn.get_actor_location()
    pawn.set_actor_location(H.transform_location(unreal.Vector(*eye)) - off, False, True)
    d = [at[i] - eye[i] for i in range(3)]
    unreal.GameplayStatics.get_player_controller(w, 0).set_control_rotation(unreal.Rotator(roll=0, pitch=math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))),
                                                                                      yaw=math.degrees(math.atan2(d[1], d[0])) + H.rotation.rotator().yaw))
    log({"phase": "eye", "view": ARG})
