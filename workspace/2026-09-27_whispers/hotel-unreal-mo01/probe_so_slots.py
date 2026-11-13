"""Read-only: where the Smart Object subsystem puts Meredith's desk slots vs the Life objects' Use (Play or editor), and the
level's Smart Object collections.

    python ue_bridge.py run probe_so_slots.py [game|editor]
"""
import unreal, json, sys
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
L = lambda v: [round(c, 1) for c in (lambda q: (q.x, q.y, q.z))(Hinv.transform_location(v))]
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ed.get_game_world() if (len(sys.argv) < 2 or sys.argv[1] == "game") and ed.get_game_world() else ed.get_editor_world()
S = unreal.SmartObjectSubsystem.get_current(w) if hasattr(unreal.SmartObjectSubsystem, "get_current") else None
rows = {}
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersLifeObject):
    if not a.get_actor_label().startswith("Life_Manager_"):
        continue
    so = a.smart_object
    h = so.get_registered_handle() if hasattr(so, "get_registered_handle") else None
    r = {"use": L(a.get_actor_transform().transform_location(a.use.translation)), "component": L(so.get_world_location()), "handle": str(h)[:80]}
    if S and h:
        try:
            slots = S.get_all_slots(h) if hasattr(S, "get_all_slots") else []
            r["slots"] = [L(S.get_slot_transform_from_request_result(x).translation) if False else str(x)[:60] for x in slots]
        except Exception as e:  # noqa: BLE001
            r["slot_err"] = str(e)[:160]
    rows[a.get_actor_label()] = r
cols = [{"label": c.get_actor_label(), "class": c.get_class().get_name(), "package": c.get_package().get_name()}
        for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if "SmartObject" in c.get_class().get_name() and "Collection" in c.get_class().get_name()]
print("SLOTS", json.dumps({"world": w.get_name(), "rows": rows, "collections": cols, "subsystem": bool(S),
                           "subsystem_methods": [m for m in dir(S) if "slot" in m.lower() or "transform" in m.lower()][:40] if S else None}))
