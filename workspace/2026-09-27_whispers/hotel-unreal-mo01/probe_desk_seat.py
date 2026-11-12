"""Read-only (editor, Play stopped): can Meredith reach her desk seat with the real chair in place?

    python ue_bridge.py run probe_desk_seat.py

Reports, in hotel-local cm: the seven Life_Manager_*_SL8 slots (Approach / Use / Leave), what blocks their approach point
(overlapping collision near it, navmesh projection), the chair's collision; and, for comparison, the working seated slots
elsewhere (staff rest, reception, dining) with the collision of the furniture under them. Nothing is modified.
"""
import unreal, json
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K" and not ed.get_game_world()
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
nav = unreal.NavigationSystemV1.get_navigation_system(W)


def L(v):
    p = Hinv.transform_location(v); return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]


def near(world_pt, radius, skip=()):
    out = []
    for a in A:
        if a.get_actor_label() in skip or isinstance(a, unreal.WhispersLifeObject):
            continue
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            try:
                if str(c.get_collision_enabled()) in ("CollisionEnabled.NO_COLLISION",):
                    continue
                bo, be, _ = unreal.SystemLibrary.get_component_bounds(c)
                d = (bo - world_pt); dx = max(abs(d.x) - be.x, 0); dy = max(abs(d.y) - be.y, 0); dz = max(abs(d.z) - be.z, 0)
                gap = (dx * dx + dy * dy + dz * dz) ** 0.5
                if gap <= radius:
                    out.append({"actor": a.get_actor_label(), "comp": c.get_name(), "cls": c.get_class().get_name(), "gap_cm": round(gap, 1),
                                "profile": str(c.get_collision_profile_name()), "enabled": str(c.get_collision_enabled()),
                                "pawn": str(c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)),
                                "nav": bool(c.get_editor_property("can_ever_affect_navigation"))})
            except Exception as ex:  # noqa: BLE001
                out.append({"actor": a.get_actor_label(), "comp": c.get_name(), "err": str(ex)[:120]})
    return sorted(out, key=lambda r: r.get("gap_cm", 999))[:12]


def proj(world_pt):
    try:
        p = unreal.NavigationSystemV1.project_point_to_navigation(W, world_pt, None, None, unreal.Vector(30, 30, 200))
        return L(p) if p else None
    except Exception as ex:  # noqa: BLE001
        return "err " + str(ex)[:120]


def slot(o):
    t = o.get_actor_transform()
    ap = unreal.MathLibrary.compose_transforms(o.approach, t).translation
    us = unreal.MathLibrary.compose_transforms(o.use, t).translation
    lv = unreal.MathLibrary.compose_transforms(o.leave, t).translation
    return {"label": o.get_actor_label(), "id": str(o.object_id), "room": str(o.room_id), "advertise": o.b_advertise if hasattr(o, "b_advertise") else o.get_editor_property("advertise"),
            "actor": L(t.translation), "approach": L(ap), "use": L(us), "leave": L(lv), "via": [(str(v.room), str(v.anchor)) for v in o.approach_via],
            "approach_nav": proj(ap), "def": o.advertisement_definition.get_name() if o.advertisement_definition else None}


out = {"manager": [], "near_manager_approach": None, "chair": {}, "compare": []}
mgr = sorted([a for a in A if isinstance(a, unreal.WhispersLifeObject) and str(a.object_id).startswith("life.eden.manager.")], key=lambda a: a.get_actor_label())
for o in mgr:
    out["manager"].append(slot(o))
if mgr:
    ap = unreal.MathLibrary.compose_transforms(mgr[0].approach, mgr[0].get_actor_transform()).translation
    out["near_manager_approach"] = near(ap, 60)
ch = next((a for a in A if a.get_actor_label() == "Chair_Swivel_MO"), None)
if ch:
    out["chair"] = {"class": ch.get_class().get_name(), "local": L(ch.get_actor_location()),
                    "comps": [{"n": c.get_name(), "cls": c.get_class().get_name(), "profile": str(c.get_collision_profile_name()), "enabled": str(c.get_collision_enabled()),
                               "nav": bool(c.get_editor_property("can_ever_affect_navigation")), "ext": [round(v, 1) for v in (lambda e: (e.x, e.y, e.z))(unreal.SystemLibrary.get_component_bounds(c)[1])]}
                              for c in ch.get_components_by_class(unreal.PrimitiveComponent)]}
# working seated slots elsewhere: what is under / around their approach point
for key in ("life.eden.staff.rest", "life.eden.reception", "life.eden.staff.meal", "life.eden.dining"):
    for o in [a for a in A if isinstance(a, unreal.WhispersLifeObject) and str(a.object_id).startswith(key)][:2]:
        r = slot(o); ap = unreal.MathLibrary.compose_transforms(o.approach, o.get_actor_transform()).translation
        r["near_approach"] = near(ap, 40); out["compare"].append(r)
print("SEAT", json.dumps(out, default=str)[:14000])
