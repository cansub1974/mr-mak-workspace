"""MO01 Play checks in L_EdenE2K (one phase per ue-mcp call; the world ticks between calls).

    python ue_bridge.py run pie_mo01.py start | view <Name> | lights | trace | stop
  start   begin Play (editor throttling off)
  view    put the player's eye at a named office view (hotel-local cm -> world through the HotelEden instance)
  lights  Director query for Hotel.MeredithOffice with the player in the office (ids, state, intensity)
  trace   capsule-free line traces in the PIE world against the office's simple colliders
  stop    end Play
Writes review-media/hotel-unreal-mo01/PIE_Checks.json. Frames are captured separately (the capture tool does not save).
"""
import unreal, json, os, sys, time, math
PHASE = sys.argv[1] if len(sys.argv) > 1 else "lights"; VIEW = sys.argv[2] if len(sys.argv) > 2 else ""
REC = r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
OUT = REC + "/PIE_Checks.json"
st = json.load(open(OUT)) if os.path.exists(OUT) and PHASE != "start" else {"phases": {}}
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
FL = 900.4


def look(eye, at):
    d = [at[i] - eye[i] for i in range(3)]
    return (eye, math.degrees(math.atan2(d[1], d[0])), math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))))


VIEWS = {   # hotel-local eye and target, cm
    "RefMatch": look((2510, 605, FL + 155), (1760, 290, FL + 145)),          # the reference viewpoint, south-east corner looking west
    "Fireplace": look((2080, 450, FL + 150), (1762, 450, FL + 170)),
    "Mantel": look((1915, 462, FL + 140), (1762, 450, FL + 135)),
    "Windows": look((2110, 560, FL + 160), (2110, 30, FL + 210)),
    "CornerPalm": look((2395, 590, FL + 160), (2485, 100, FL + 140)),
    "Rug": look((2350, 210, FL + 170), (2080, 420, FL + 0)),
    "Books": look((1985, 500, FL + 160), (1840, 670, FL + 180)),
    "Door": look((1960, 180, FL + 160), (2400, 650, FL + 130)),
}


def save():
    st["updated"] = time.strftime("%H:%M:%S"); json.dump(st, open(OUT, "w"), indent=1, default=str)


def W():
    w = ed.get_game_world(); assert w, "no PIE world"; return w


_INST = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]


def H():
    return unreal.Transform(unreal.Vector(*_INST["translation_cm"]), unreal.Quat(*_INST["rotation_quat"]).rotator(), unreal.Vector(*_INST["scale"]))


def put_eye(w, loc_local, yaw_local, pitch):
    T = H(); pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    eye = pawn.get_actor_eyes_view_point()[0]; off = eye - pawn.get_actor_location()
    tgt = T.transform_location(unreal.Vector(*loc_local))
    pawn.set_actor_location(tgt - off, False, True)
    unreal.GameplayStatics.get_player_controller(w, 0).set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw_local + T.rotation.rotator().yaw))
    return [round(v, 1) for v in pawn.get_actor_eyes_view_point()[0].to_tuple()]


if PHASE == "start":
    eps = unreal.load_object(None, "/Script/UnrealEd.Default__EditorPerformanceSettings")
    eps.set_editor_property("bThrottleCPUWhenNotForeground", False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    st["phases"]["start"] = "requested " + time.strftime("%H:%M:%S")
elif PHASE == "view":
    w = W()
    unreal.SystemLibrary.execute_console_command(w, "r.MotionBlur.Amount 0")
    st["phases"].setdefault("views", {})[VIEW] = put_eye(w, *VIEWS[VIEW])
elif PHASE == "lights":
    w = W(); d = unreal.WhispersLightingSubsystem.get_director(w)
    r = json.loads(d.execute_json_command(json.dumps({"v": 1, "op": "query", "target": {"zone": "Hotel.MeredithOffice"}, "limit": 64})))
    z = json.loads(d.execute_json_command(json.dumps({"v": 1, "op": "list_zones"})))
    st["phases"]["lights"] = {"reply": r, "zones": [x for x in z.get("zones", []) if "Meredith" in json.dumps(x) or "Executive" in json.dumps(x)]}
elif PHASE == "trace":
    w = W(); T = H(); res = {}
    # down onto the office floor, across the chimney breast, into the bookcases, the palm planter and the rug (no collision)
    for name, a, b in (("floor_centre", (2140, 350, 1100), (2140, 350, 850)), ("breast_face", (2000, 450, 1050), (1650, 450, 1050)),
                       ("south_case", (2000, 520, 1050), (2000, 720, 1050)), ("alcove_case", (1950, 170, 1050), (1650, 170, 1050)),
                       ("palm_planter", (2474, 400, 920), (2474, 0, 920)), ("palm_fronds", (2300, 114, 1100), (2700, 114, 1100))):
        h = unreal.MCPTraceLibrary.line_trace(T.transform_location(unreal.Vector(*a)), T.transform_location(unreal.Vector(*b)), "pie", 0, "WorldStatic", False)
        res[name] = {k: (str(v) if not isinstance(v, (int, float, bool, str)) else v) for k, v in (h.items() if isinstance(h, dict) else
                     [(n, getattr(h, n)) for n in ("hit", "distance", "actor_path", "component_name") if hasattr(h, n)])}
    st["phases"]["trace"] = res
elif PHASE == "toggle":
    # PIE world only (not saved): show/hide components whose mesh name contains VIEW (argv 2); argv 3 = 0/1
    w = W(); vis = (sys.argv[3] if len(sys.argv) > 3 else "0") == "1"; hits = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh and VIEW in c.static_mesh.get_name():
                c.set_visibility(vis, False); hits.append(f"{a.get_actor_label()}/{c.get_name()}/{c.static_mesh.get_name()}")
    st["phases"].setdefault("toggles", []).append({"mesh": VIEW, "visible": vis, "components": hits})
elif PHASE == "cvar":
    # PIE session only: one console command (argv 2 .. joined), for diagnosis
    w = W(); cmd = " ".join(sys.argv[2:]); unreal.SystemLibrary.execute_console_command(w, cmd)
    st["phases"].setdefault("cvars", []).append(cmd)
elif PHASE == "light":
    # PIE session only: switch light components on actors whose label starts with argv 2 (argv 3 = 0/1), for diagnosis
    w = W(); on = (sys.argv[3] if len(sys.argv) > 3 else "0") == "1"; hits = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_actor_label().startswith(VIEW):
            for c in a.get_components_by_class(unreal.LightComponent):
                c.set_visibility(on, False); hits.append(a.get_actor_label())
    st["phases"].setdefault("light_toggles", []).append({"prefix": VIEW, "on": on, "actors": hits})
    print("LIGHTS", hits)
elif PHASE == "stop":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    st["phases"]["stop"] = "requested"
save()
print("PIE_MO01", PHASE, VIEW, json.dumps(st["phases"].get(PHASE if PHASE != "view" else "views", {}), default=str)[:3000])
