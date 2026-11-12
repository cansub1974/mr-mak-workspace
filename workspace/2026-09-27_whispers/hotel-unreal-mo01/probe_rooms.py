"""Read-only, in Play: which Life room the world registry resolves across Meredith's office (hotel-local cm), and the room
volumes there. Answers why her desk slots at (1930, 400) lose room.eden.mo.

    python ue_bridge.py run probe_rooms.py
"""
import unreal, json
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); assert w, "Play required"
r = next(x for x in unreal.ObjectIterator(unreal.WhispersWorldRegistrySubsystem) if x.get_outer() == w)
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
Z = 991.0
pts = {"old_chair": (2390.9, 355.4), "new_chair": (1930.0, 400.0), "new_desk": (2030.0, 400.0), "stage": (2250.0, 520.0)}
out = {"named": {k: str(r.resolve_room(H.transform_location(unreal.Vector(x, y, Z)))) for k, (x, y) in pts.items()}}
grid = {}
for x in range(1700, 2700, 100):
    grid[x] = {y: str(r.resolve_room(H.transform_location(unreal.Vector(x, y, Z)))).replace("room.eden.", "") for y in range(0, 900, 100)}
out["grid_x_by_y"] = grid
vols = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    lab = a.get_actor_label()
    if not any(k in lab for k in ("WM22b_", "Life_Room", "Room_mo", "room_mo", "_MO_", "TMP_Life_Room")):
        continue
    o, e = a.get_actor_bounds(False)
    c = Hinv.transform_location(o)
    if abs(c.z - 950) > 400 or abs(c.x - 2200) > 1200 or abs(c.y - 400) > 1200:
        continue
    vols.append({"label": lab, "class": a.get_class().get_name(), "centre_local": [round(c.x), round(c.y), round(c.z)], "extent": [round(e.x), round(e.y), round(e.z)],
                 "room_id": str(a.get_editor_property("room_id")) if hasattr(a, "room_id") else None})
out["volumes"] = vols
print("ROOMS", json.dumps(out))
