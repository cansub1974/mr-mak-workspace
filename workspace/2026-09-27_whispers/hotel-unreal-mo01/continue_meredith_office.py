"""Put Meredith back in her office in Jason's Continue save (ue-mcp run_python_file; one phase per call).

Owner, 13 Nov 2026, choosing between a fresh start, fixing her position and leaving it: "Option 2, walk her back to her office".
Why: my non-isolated Play tests on 12 Nov (22:09-22:10) wrote WhispersContinue.sav and its three backups with Meredith at the
kitchen's north-west end (room.eden.l1_northwest, whose Life edges are blocked, #215): Population "externally selected travel"
to room.eden.mo, outcome "unreachable: no complete navigation path at movement start". She idles there on every Continue.

This session is deliberately NOT a smoke: it continues from the Continue slot and its commits write that slot, as the owner asked.
The only staged change is Meredith's place: onto the office floor east of her desk, projected to the navmesh, standing (the same
point the isolated #219 smoke used on 12 Nov, where Life then chose the desk by itself). No needs, clock, time scale, door,
player pose or camera is touched; the player is not moved. Life decides what she does; the quit commit records it.

    python ue_bridge.py run continue_meredith_office.py backup        # Play stopped: copy the slot and .bak1-3 aside, hashed
    python ue_bridge.py run continue_meredith_office.py play          # Play stopped: no smoke arm pending; request Play
    python ue_bridge.py run continue_meredith_office.py host          # in Play: restore finished, writes go to the project slot
    python ue_bridge.py run continue_meredith_office.py place         # in Play: Meredith onto the office floor
    python ue_bridge.py run pie_meredith.py read <label>              # in Play: observation only (never `eye`: it moves the player)
    python ue_bridge.py run continue_meredith_office.py stop          # in Play: end Play (the quit commit writes the slot)
    python ue_bridge.py run continue_meredith_office.py after         # Play stopped: what the slot now records for her
  then an isolated check that the Continue restores her in her office and writes nothing to the slot (#219 smoke slot):
    python ue_bridge.py run continue_meredith_office.py check_arm     # Play stopped: arm the AgentSmoke slot, request Play
    python ue_bridge.py run continue_meredith_office.py check_isolate # first phase in Play
    python ue_bridge.py run pie_meredith.py read <label>
    python ue_bridge.py run continue_meredith_office.py check_verify  # last phase in Play: slot and backups unchanged
    python ue_bridge.py run continue_meredith_office.py check_stop

The backup (Saved/SaveGames/_before_mo01_office_20261113/) is the way back: copy its four files over the live ones with Play
stopped. Rows go to review-media/hotel-unreal-mo01/PIE_Meredith.jsonl; state to Continue_Meredith_Office.json.
"""
import unreal, json, sys, os, shutil, base64
from WhispersTests import smoke_slot as smoke
PH = sys.argv[1] if len(sys.argv) > 1 else "after"
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
SF = REC + "/Continue_Meredith_Office.json"
BACKUP = os.path.join(smoke.slot_directory(), "_before_mo01_office_20261113")
CHECK_LABEL = "mo01_continue_check"
CHECK_BEFORE = os.path.join(smoke.saved_dir(), "Tests", "MO01Continue", "slot-before.json")
FILES = [smoke.LIVE_FILE] + ["%s.bak%d" % (smoke.LIVE_FILE, i) for i in smoke.BACKUP_INDICES]
st = json.load(open(SF)) if os.path.exists(SF) else {}
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()


def log(row):
    open(REC + "/PIE_Meredith.jsonl", "a", encoding="utf-8").write(json.dumps(row, default=str) + "\n"); print("CONTINUE", json.dumps(row, default=str)[:3000])


def save_state():
    json.dump(st, open(SF, "w"), indent=1, default=str)


def local(t):
    p = Hinv.transform_location(unreal.Vector(t["x"], t["y"], t["z"])); return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]


def meredith_in(path):
    """Her Population record and Life action in one slot file (plain JSON; participant payloads are base64)."""
    if not os.path.exists(path):
        return None
    j = json.load(open(path, encoding="utf-8")); out = {"savedAtWorldTimeSeconds": round(j.get("savedAtWorldTimeSeconds", 0), 1)}
    for p in j["participants"]:
        b = base64.b64decode(p["payloadBase64"])
        if p["kind"] == "WorldRegistryPopulation":
            o = json.loads(b[b.index(b"{"):b.rindex(b"}") + 1].decode("utf-8"))
            rec = next(r for r in json.loads(o["population"])["records"] if r["cardId"] == "npc.meredith")
            out["population"] = {k: rec.get(k) for k in ("currentRoom", "destination", "activity", "outcome", "materialization", "locationProvenance")}
            if rec.get("bHasBodyPlace"):
                out["population"]["bodyPlace_local"] = local(rec["bodyPlace"]["translation"])
        elif p["kind"] == "WhispersLife":
            o = json.loads(b[b.index(b"{"):b.rindex(b"}") + 1].decode("utf-8"))
            rec = next(r for r in o["records"] if r.get("cardId") == "npc.meredith")
            act = rec.get("action")
            out["life_action"] = act if isinstance(act, str) else json.dumps(act)[:400]
    return out


def host(w):
    return smoke._host(w)


def no_arm():
    assert not os.path.exists(smoke.arm_path()), ("a smoke arm is pending; this session must write the Continue slot", smoke.arm_path())


if PH == "backup":
    assert not ed.get_game_world(), "stop Play first"
    os.makedirs(BACKUP, exist_ok=True)
    snap = smoke.snapshot(); copied = {}
    for name in FILES:
        src = os.path.join(smoke.slot_directory(), name)
        if os.path.exists(src):
            dst = os.path.join(BACKUP, name)
            assert not os.path.exists(dst) or smoke._identity(dst)["sha256"] == snap["files"][name]["sha256"], ("backup exists and differs; stop", dst)
            shutil.copy2(src, dst); copied[name] = smoke._identity(dst)["sha256"] == snap["files"][name]["sha256"]
    assert copied and all(copied.values()), copied
    st.update(backup_dir=BACKUP, before=snap, before_meredith=meredith_in(smoke.live_slot_path())); save_state()
    log({"phase": "continue_backup", "dir": BACKUP, "copied_and_hash_equal": copied, "meredith": st["before_meredith"]})
elif PH == "play":
    assert st.get("backup_dir"), "backup first"
    assert not ed.get_game_world(), "Play is running"
    no_arm()
    assert smoke.verify(st["before"])["ok"], "the slot changed since the backup; take the backup again"
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    log({"phase": "continue_play", "requested": True})
elif PH == "host":
    w = ed.get_game_world(); assert w, "Play required"
    h = host(w); assert h, "no persistence host"
    outcome = h.get_restore_outcome()
    row = {"phase": "continue_host", "restore": str(outcome), "redirected": bool(h.call_method("IsSlotRedirectedForTest")),
           "slot_dir": str(h.call_method("GetSlotDirectoryForSession") or ""), "seconds_since_commit": h.get_editor_property("seconds_since_last_commit")}
    a = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith"), None)
    row["meredith_local"] = local({k: getattr(a.get_actor_location(), k) for k in "xyz"}) if a else None
    log(row); assert not row["redirected"] and "RESTORED" in row["restore"].upper(), row
elif PH == "place":
    w = ed.get_game_world(); assert w, "Play required"
    h = host(w); assert h and not h.call_method("IsSlotRedirectedForTest") and "RESTORED" in str(h.get_restore_outcome()).upper()
    a = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if a.commands.get_npc_id() == "npc.meredith")
    half = a.capsule_component.get_scaled_capsule_half_height()
    want = H.transform_location(unreal.Vector(2250.0, 520.0, 901.7 + half))
    p = unreal.NavigationSystemV1.project_point_to_navigation(w, want, None, None, unreal.Vector(40, 40, 150))
    assert p, "no navmesh at the office point"
    before = a.get_actor_location()
    a.set_actor_location_and_rotation(unreal.Vector(p.x, p.y, p.z + half), unreal.Rotator(roll=0, pitch=0, yaw=H.rotation.rotator().yaw + 180.0), False, True)
    L = lambda v: local({k: getattr(v, k) for k in "xyz"})
    log({"phase": "continue_place", "from_local": L(before), "to_local": L(a.get_actor_location()), "nav_local": L(p)})
elif PH == "stop":
    assert ed.get_game_world(), "Play is not running"
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); log({"phase": "continue_stop"})
elif PH == "after":
    assert not ed.get_game_world(), "stop Play first"
    snap = smoke.snapshot()
    st.update(after=snap, after_meredith={n: meredith_in(os.path.join(smoke.slot_directory(), n)) for n in FILES}); save_state()
    log({"phase": "continue_after", "files": {n: (v.get("size"), (v.get("sha256") or "")[:16], v.get("mtime_ns")) for n, v in snap["files"].items()},
         "meredith_live": st["after_meredith"][smoke.LIVE_FILE]})
elif PH == "check_arm":
    assert not ed.get_game_world(), "stop Play first"
    r = smoke.arm(CHECK_LABEL, CHECK_BEFORE)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    log({"phase": "check_arm", "armed": r["armed"], "requested": r["requested"]})
elif PH == "check_isolate":
    w = ed.get_game_world(); assert w, "Play required"
    r = smoke.isolate(w, CHECK_LABEL); log({"phase": "check_isolate", **r}); assert r["ok"], r
elif PH == "check_verify":
    r = smoke.verify_file(CHECK_BEFORE)
    st["check"] = {"ok": r["ok"], "changed": r["changed"]}; save_state()
    log({"phase": "check_verify", "ok": r["ok"], "changed": r["changed"]}); assert r["ok"], r["changed"]
elif PH == "check_stop":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play(); log({"phase": "check_stop"})
else:
    raise SystemExit("unknown phase " + PH)
