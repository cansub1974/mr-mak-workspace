"""Read-only: a working dining seat overlay's anchors relative to its Seat anchor (proportions for Meredith's desk chair overlay).

    python ue_bridge.py run probe_seat_overlays.py
"""
import unreal, json
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
V = lambda v: [round(v.x, 2), round(v.y, 2), round(v.z, 2)]
out = []
for o in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.WhispersReceptionOverlay):
    seat = o.find_anchor("Seat")
    if not seat or not (o.furniture_actor or "seat" in str(o.overlay_id).lower() or "dining" in str(o.overlay_id).lower()):
        continue
    st = seat.get_world_transform()
    rows = {}
    for a in o.anchors:
        if a:
            rows[str(a.anchor_id)] = {"rel_seat": V(st.inverse_transform_location(a.get_world_location())), "kind": str(a.kind), "limb": str(a.allowed_limb)}
    out.append({"label": o.get_actor_label(), "id": str(o.overlay_id), "furniture": o.furniture_actor.get_actor_label() if o.furniture_actor else None,
                "seat_world_z": round(st.translation.z, 1), "anchors": rows})
    if len(out) >= 3:
        break
ids = sorted({(str(o.overlay_id), o.get_class().get_name()) for o in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.WhispersReceptionOverlay)})
print("OVERLAYS", json.dumps({"seats": out, "ids": ids[:80]}))
