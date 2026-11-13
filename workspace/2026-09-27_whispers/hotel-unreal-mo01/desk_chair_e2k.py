"""Meredith's desk, chesterfield and swivel chair in L_EdenE2K (ue-mcp run_python_file; one stage per call; Play stopped).

    python ue_bridge.py run desk_chair_e2k.py plan | scale | chair | life | activities | journal <x> <y> | verify

Owner, 13 Nov 2026: "The desk and the sofa need to be about 20 percent larger. They are hero pieces." (the desk wider and
deeper only, its height kept so she works at a normal height; the chesterfield 20% all round - owner's choice in this
session). "Meredith's chair needs to be rotated about 70 degrees perpendicular to the desk when she is not in it. When she goes
to sit in it she will stand in front of the chair with her back to it. She will sit down. The chair and her will rotate so that
she and the chair are square to the desk. The chair and her will then move inwards to the desk so that she is sitting
comfortably close to the desk so that she can work at it. ... Her hands must work at the level of the desk plus the width of a
journal. Place the same journal that is on the reception desk on Meredith's desk right where she is writing".

  scale       Desk_Pedestal_MO x (1.2, 1.2, 1.0) in its own axes, same centre; Sofa_Chesterfield_MO x 1.2, its back kept where it
              stands (the centre moves out from the wall by the extra half depth).
  chair       the placed BP_SwivelChair (approved FUR-108 Blueprint, unchanged) is replaced by AWhispersSwivelDeskChair with the same
              meshes and materials: actor frame = the working pose (+X faces the desk); empty it rests turned REST_YAW and rolled
              REST_ROLL back. Its sitter overlay (AWhispersReceptionOverlay, Overlay_MO_DeskChair) is authored at the rest pose
              with the SR01 seat proportions (Backrest, feet); the default LeftHand anchor is renamed off so no hand is pinned.
  life        the six seated Life_Manager_*_SL8 advertisements: actor at the rest seat point + 40 cm, facing the rest yaw, Use
              40 cm below (the pelvis point), Approach APPROACH_CM in front (where she stands, back to the chair); their
              PresentationOverlay is the chair's overlay; each Smart Object slot is re-authored from Use. StandLean (a standing
              lean authored at the chair centre) stops advertising: it would stand her inside the chair.
  activities  the six seated DA_Office_* activities get the chair sit-down and stand-up montages and their seconds.
  journal     a copy of the reception guest ledger (UI01 LP01: same mesh and material) on the desk, PenRest at hotel-local (x, y).
State: review-media/hotel-unreal-mo01/Desk_Chair_E2K.json. Guards as furnish_e2k.py: forest checked, only expected packages saved.
"""
import unreal, json, sys, os, math
STAGE = sys.argv[1] if len(sys.argv) > 1 else "plan"
CARD = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
REC = CARD + "/review-media/hotel-unreal-mo01"
SF = REC + "/Desk_Chair_E2K.json"
st = json.load(open(SF)) if os.path.exists(SF) else {}
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); es = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K", W.get_name()
assert not ed.get_game_world(), "stop Play first"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"]))
Hinv = H.inverse(); HYAW = H.rotation.rotator().yaw

# ---- the numbers (hotel-local cm / deg) --------------------------------------------------------------------------------
FLOOR = 901.7                                   # rug top under the desk group
DESK = dict(label="Desk_Pedestal_MO", centre=(2030.0, 400.0), yaw=180.0, scale=(1.2, 1.2, 1.0))
SOFA = dict(label="Sofa_Chesterfield_MO", scale=1.2)
CHAIR_DOCK = (1942.0, 400.0)                    # swivel axis at work: pelvis ~24 cm from the desk edge (x 1969.2)
SWIVEL_Z = 24.2                                 # FUR-108: the seat 24.2 cm up on the base
SEAT_POINT = (3.0, 0.0, 25.4)                   # pelvis point in the swivel frame: 49.6 cm above the floor, as the Life use point was
REST_YAW, REST_ROLL = 70.0, 30.0
APPROACH_CM = 40.0                              # where she stands before sitting, in front of the rest seat point
SEATED = ("Desk_Sit", "Desk_Write", "Desk_Type", "Desk_Phone", "Desk_Read", "Meeting")
SIT = "/Game/Whispers/Presentation/Characters/Shared/Animation/Core/AM_SitDown_Chair_F_Action_RootMotion"
STAND = "/Game/Whispers/Presentation/Characters/Shared/Animation/Core/AM_StandUp_Chair_F_Action_RootMotion"
ENTER_S, EXIT_S = 3.2, 3.6
FOLDER = "Furniture/Office_MO"


def L2W(x, y, z):
    return H.transform_location(unreal.Vector(x, y, z))


def W2L(v):
    p = Hinv.transform_location(v); return [round(p.x, 2), round(p.y, 2), round(p.z, 2)]


def rot(yaw_local):
    return unreal.Rotator(roll=0, pitch=0, yaw=yaw_local + HYAW)


def acts():
    return {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor)}


def tag(name):
    t = unreal.GameplayTag(); assert t.import_text('(TagName="' + name + '")'); return t


def tags(*names):
    t = unreal.GameplayTagContainer(); assert t.import_text("(GameplayTags=(" + ",".join('(TagName="' + n + '")' for n in names) + "))"); return t


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


def save_only(expected_pkgs, d0, label):
    """Save when everything newly dirty is expected; packages dirty before this stage (others' work) are left alone."""
    d1 = dirty(); new = sorted(set(d1) - set(d0))
    extra = [p for p in new if p not in expected_pkgs and not p.startswith("/Game/__ExternalActors__/Whispers/World/EdenE2K/L_EdenE2K/")]
    f = forest(); assert f["ok"], ("E2K forest check failed; not saving", f)
    assert not extra, ("unexpected dirty packages; not saving", extra)
    pkgs = [p for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() if p.get_name() in new]
    ok = unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, True) if pkgs else True
    st.setdefault("saves", []).append({"stage": label, "saved": [p.get_name() for p in pkgs], "ok": bool(ok), "others_left": d0, "forest": f})
    return ok, [p.get_name() for p in pkgs]


def snap_actor(a):
    t = a.get_actor_transform()
    return {"local": W2L(t.translation), "yaw_local": round(t.rotation.rotator().yaw - HYAW, 3), "scale": [round(s, 4) for s in (t.scale3d.x, t.scale3d.y, t.scale3d.z)],
            "package": a.get_package().get_name(), "class": a.get_class().get_path_name()}


def chair_transform():
    return unreal.Transform(L2W(CHAIR_DOCK[0], CHAIR_DOCK[1], FLOOR), rot(0.0), unreal.Vector(1, 1, 1))


def rest_seat_frame():
    """The pelvis point and facing at the rest pose, computed from the chair parameters (independent of components)."""
    roll = REST_ROLL; yw = REST_YAW
    ax = CHAIR_DOCK[0] - roll; ay = CHAIR_DOCK[1]
    c, s = math.cos(math.radians(yw)), math.sin(math.radians(yw))
    px = ax + c * SEAT_POINT[0] - s * SEAT_POINT[1]; py = ay + s * SEAT_POINT[0] + c * SEAT_POINT[1]
    return (px, py, FLOOR + SWIVEL_Z + SEAT_POINT[2]), yw


A = acts()
if STAGE == "plan":
    st["before"] = {k: snap_actor(A[k]) for k in (DESK["label"], SOFA["label"], "Chair_Swivel_MO") if k in A}
    st["before_life"] = {k: {**snap_actor(a), "approach": [a.approach.translation.x, a.approach.translation.y, a.approach.translation.z],
                             "use": [a.use.translation.x, a.use.translation.y, a.use.translation.z], "advertise": a.get_editor_property("bAdvertise")}
                         for k, a in A.items() if k.startswith("Life_Manager_")}
    acts_ = {}
    for n in SEATED + ("StandLean",):
        d = unreal.load_asset("/Game/Whispers/Characters/Life/Activities/DA_Office_" + n)
        acts_[n] = {k: str(d.get_editor_property(k)) for k in ("EnterClip", "ExitClip", "EnterSeconds", "ExitSeconds")}
    st["before_activities"] = acts_; st["dirty_before"] = dirty(); st["forest_before"] = forest()
    seat, yw = rest_seat_frame()
    st["plan"] = {"desk": DESK, "sofa": SOFA, "chair_dock": CHAIR_DOCK, "rest_yaw": REST_YAW, "rest_roll": REST_ROLL, "rest_seat_point": seat, "approach_cm": APPROACH_CM}
    json.dump(st, open(SF, "w"), indent=1); print("PLAN", json.dumps({"before": st["before"], "plan": st["plan"], "dirty": st["dirty_before"]}))

elif STAGE == "scale":
    d0 = dirty()
    desk, sofa = A[DESK["label"]], A[SOFA["label"]]
    desk.modify(); desk.set_actor_scale3d(unreal.Vector(*DESK["scale"]))
    # the chesterfield's back (its local -Y) stays where it stands; the centre moves out by the extra half depth
    bb = sofa.static_mesh_component.static_mesh.get_bounding_box(); half = (bb.max.y - bb.min.y) / 2.0
    s0 = sofa.get_actor_scale3d().y
    back_dir = sofa.get_actor_right_vector()                                  # local +Y: away from its back
    sofa.modify(); sofa.set_actor_scale3d(unreal.Vector(SOFA["scale"], SOFA["scale"], SOFA["scale"]))
    sofa.set_actor_location(sofa.get_actor_location() + back_dir * (half * (SOFA["scale"] - s0)), False, False)
    ok, saved = save_only([], d0, "scale")
    st["scale"] = {"desk": snap_actor(desk), "sofa": snap_actor(sofa), "saved": saved}
    json.dump(st, open(SF, "w"), indent=1); print("SCALE", json.dumps(st["scale"]))

elif STAGE == "chair":
    d0 = dirty()
    old = A.get("Chair_Swivel_MO")
    if old and old.get_class().get_name() != "WhispersSwivelDeskChair":
        comps = {c.get_name(): c for c in old.get_components_by_class(unreal.StaticMeshComponent)}
        meshes = {n: (comps[n].static_mesh, list(comps[n].get_materials())) for n in ("Base", "Seat")}
        st["replaced_bp"] = {"package": old.get_package().get_name(), **snap_actor(old),
                             "meshes": {n: [m.get_path_name(), [x.get_path_name() if x else None for x in mats]] for n, (m, mats) in meshes.items()}}
        es.destroy_actor(old)
    else:
        assert st.get("replaced_bp"), "no BP chair and no record"
        meshes = {n: (unreal.load_asset(v[0]), [unreal.load_asset(x) if x else None for x in v[1]]) for n, v in st["replaced_bp"]["meshes"].items()}
    ch = acts().get("Chair_Swivel_MO")
    if not ch:
        ch = es.spawn_actor_from_class(unreal.WhispersSwivelDeskChair, chair_transform().translation, chair_transform().rotation.rotator())
        ch.set_actor_label("Chair_Swivel_MO"); ch.set_folder_path(FOLDER)
    ch.modify(); ch.set_actor_transform(chair_transform(), False, False)
    for n in ("Base", "Seat"):
        c = ch.get_editor_property(n.lower()); c.modify()
        c.set_static_mesh(meshes[n][0])
        for i, m in enumerate(meshes[n][1]):
            c.set_material(i, m)
        c.set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=-90.0))     # FUR-108 faces its local +Y
    ch.swivel.set_editor_property("relative_location", unreal.Vector(0, 0, SWIVEL_Z))
    ch.set_editor_property("RestYawDegrees", REST_YAW); ch.set_editor_property("RestRollOutCm", REST_ROLL)
    ch.rerun_construction_scripts() if hasattr(ch, "rerun_construction_scripts") else None
    # the sitter's overlay, at the rest pose
    seat, yw = rest_seat_frame()
    ov = acts().get("Overlay_MO_DeskChair")
    if not ov:
        ov = es.spawn_actor_from_class(unreal.WhispersReceptionOverlay, L2W(*seat), rot(yw))
        ov.set_actor_label("Overlay_MO_DeskChair"); ov.set_folder_path(FOLDER)
    ov.modify(); ov.set_actor_location_and_rotation(L2W(*seat), rot(yw), False, False)
    ov.set_editor_property("overlay_id", "meredith.desk_chair")
    ov.set_editor_property("bHoldSeatBetweenActivities", True)
    ov.set_editor_property("furniture_actor", ch)
    layout = {"Seat": (0, 0, 0), "Backrest": (-24, 0, 32), "FootL": (20, -12, -45.5), "FootR": (20, 12, -45.5), "Approach": (APPROACH_CM, 0, 0)}
    for a in ov.anchors:
        if not a:
            continue
        a.modify(); aid = str(a.anchor_id)
        if aid in layout:
            a.set_editor_property("relative_location", unreal.Vector(*layout[aid]))
        elif aid == "LeftHand":
            a.set_editor_property("anchor_id", "LeftHand.Off")       # no pinned left hand: reading, phone and arms-crossed keep their clips
    ch.set_editor_property("seat_overlay", ov)
    ok, saved = save_only([], d0, "chair")
    st["chair"] = {"actor": snap_actor(ch), "overlay": snap_actor(ov), "rest_seat_point": seat, "rest_yaw": yw, "saved": saved,
                   "anchors": {str(a.anchor_id): W2L(a.get_world_location()) for a in ov.anchors if a}}
    json.dump(st, open(SF, "w"), indent=1); print("CHAIR", json.dumps(st["chair"]))

elif STAGE == "life":
    d0 = dirty()
    ov = A["Overlay_MO_DeskChair"]
    seat, yw = rest_seat_frame()
    rows = {}
    for n in SEATED + ("StandLean",):
        a = A["Life_Manager_" + n + "_SL8"]
        a.modify()
        if n == "StandLean":
            a.set_editor_property("bAdvertise", False); rows[n] = {"advertise": False}; continue
        a.set_actor_location_and_rotation(L2W(seat[0], seat[1], seat[2] + 40.0), rot(yw), False, False)
        a.set_editor_property("use", unreal.Transform(unreal.Vector(0, 0, -40.0)))
        a.set_editor_property("approach", unreal.Transform(unreal.Vector(APPROACH_CM, 0, -40.0)))
        a.set_editor_property("presentation_overlay", ov)
        definition = a.smart_object.definition_asset
        activity = unreal.load_asset("/Game/Whispers/Characters/Life/Activities/DA_Office_" + n)
        assert definition and activity, n
        # As author_manager.repair_office_slots: the same advertisement, re-authored so the slot follows Use.
        advert = unreal.WhispersLifeAdvertisement(duration_game_minutes=5, body_activity=activity,
                                                  need_deltas={tag("Life.Need.Rest"): 10, tag("Life.Need.Fun"): 5},
                                                  eligibility_tags=tags("Life.Access.Staff"), activity_tags=tags("Role.Manager"))
        assert a.author_advertisement(definition, advert), n
        slot = list(definition.get_editor_property("slots"))[0].get_editor_property("offset")
        err = (unreal.Vector(slot.x, slot.y, slot.z) - a.use.translation).length()
        assert err < .01, (n, err)
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition, False)
        rows[n] = {"local": W2L(a.get_actor_location()), "use_world_local": W2L(a.get_actor_transform().transform_location(a.use.translation)),
                   "approach_world_local": W2L(a.get_actor_transform().transform_location(a.approach.translation)), "slot_err_cm": err,
                   "definition": definition.get_path_name()}
    ok, saved = save_only([], d0, "life")
    st["life"] = {"rows": rows, "saved": saved}
    json.dump(st, open(SF, "w"), indent=1); print("LIFE", json.dumps(st["life"]))

elif STAGE == "overlay_so":
    # With a PresentationOverlay, Life claims the overlay's own Smart Object (AWhispersLifeObject::GetActivitySmartObject), as the
    # SR01 seats do: one desk slot shared by her six seated actions, at the overlay root (the rest seat point = each Use). The
    # runtime object keeps its registered (rest) transform while the chair moves, so a held-seat admission still matches Use.
    d0 = dirty()
    path = "/Game/Whispers/World/SmartObjects/Office/SO_Manager_DeskChair"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        assert unreal.EditorAssetLibrary.duplicate_asset("/Game/Whispers/World/SmartObjects/Office/SO_Manager_Office_1", path)
    d = unreal.load_asset(path)
    slots = list(d.get_editor_property("slots")); assert len(slots) == 1, len(slots)
    off = slots[0].get_editor_property("offset")
    assert abs(off.x) < .01 and abs(off.y) < .01 and abs(off.z + 40.0) < .01, ("slot offset", off)   # as every office slot: Use 40 below
    # The slot is not editable from Python, so the overlay's frame follows it: its root stands 40 cm above the seat point
    # (as the Life objects do) and every anchor sits 40 cm lower in that frame.
    seat, yw = rest_seat_frame()
    ov = A["Overlay_MO_DeskChair"]; so = ov.smart_object
    before = so.get_definition() if hasattr(so, "get_definition") else None
    ov.modify(); ov.set_actor_location_and_rotation(L2W(seat[0], seat[1], seat[2] + 40.0), rot(yw), False, False)
    layout = {"Seat": (0, 0, 0), "Backrest": (-24, 0, 32), "FootL": (20, -12, -45.5), "FootR": (20, 12, -45.5), "Approach": (APPROACH_CM, 0, 0)}
    for a in ov.anchors:
        if a and str(a.anchor_id) in layout:
            x, y, z = layout[str(a.anchor_id)]; a.modify(); a.set_editor_property("relative_location", unreal.Vector(x, y, z - 40.0))
    ref = so.get_editor_property("definition_ref"); ref.set_editor_property("smart_object_definition", d)
    so.modify(); so.set_editor_property("definition_ref", ref)
    got = so.get_editor_property("definition_ref").get_editor_property("smart_object_definition")
    assert got and got.get_path_name() == d.get_path_name(), got
    ok, saved = save_only([path], d0, "overlay_so")
    off = list(d.get_editor_property("slots"))[0].get_editor_property("offset")
    st["overlay_so"] = {"definition": path, "before": before.get_path_name() if before else None, "slot_offset": [off.x, off.y, off.z],
                        "slot_world_local": W2L(so.get_world_location() + unreal.Vector(off.x, off.y, off.z)), "saved": saved}
    json.dump(st, open(SF, "w"), indent=1); print("OVERLAY_SO", json.dumps(st["overlay_so"]))

elif STAGE == "activities":
    d0 = dirty(); sit, stand = unreal.load_asset(SIT), unreal.load_asset(STAND); assert sit and stand
    rows = {}
    for n in SEATED:
        d = unreal.load_asset("/Game/Whispers/Characters/Life/Activities/DA_Office_" + n)
        d.modify()
        d.set_editor_property("EnterClip", sit); d.set_editor_property("ExitClip", stand)
        d.set_editor_property("EnterSeconds", ENTER_S); d.set_editor_property("ExitSeconds", EXIT_S)
        assert unreal.EditorAssetLibrary.save_loaded_asset(d, False)
        rows[n] = d.get_path_name()
    st["activities"] = {"rows": rows, "enter_s": ENTER_S, "exit_s": EXIT_S, "dirty_after": dirty()}
    json.dump(st, open(SF, "w"), indent=1); print("ACTIVITIES", json.dumps(st["activities"]))

elif STAGE == "journal":
    # The reception guest ledger (UI01 LP01) inside the hotel level instance: same mesh and material, its PenRest under her pen.
    x, y = float(sys.argv[2]), float(sys.argv[3])
    d0 = dirty()
    src = next(a for a in A.values() if "Reception guest ledger" in a.get_actor_label())
    sc = next(c for c in src.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh)
    mesh, mats = sc.static_mesh, list(sc.get_materials())
    desk = A[DESK["label"]]
    top = desk.get_actor_location().z + desk.static_mesh_component.static_mesh.get_bounding_box().max.z * desk.get_actor_scale3d().z
    j = acts().get("Journal_Ledger_MO")
    if not j:
        j = es.spawn_actor_from_class(unreal.StaticMeshActor, L2W(x, y, 0), rot(0.0)); j.set_actor_label("Journal_Ledger_MO"); j.set_folder_path(FOLDER)
    d0 = [p for p in d0 if p != j.get_package().get_name()]
    j.modify(); c = j.static_mesh_component; c.modify(); c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_static_mesh(mesh)
    for i, m in enumerate(mats):
        c.set_material(i, m)
    c.set_collision_profile_name("NoCollision")
    # orientation relative to the writer, as at reception: the ledger's yaw relative to Rose's standing post
    rose = next(o for o in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.WhispersReceptionOverlay) if str(o.overlay_id) == "rose.reception")
    rel_yaw = sc.get_world_rotation().yaw - rose.get_actor_rotation().yaw
    j.set_actor_rotation(rot(0.0 + rel_yaw), False)                 # Meredith works facing hotel-local yaw 0 (+x)
    pen = c.get_socket_location("PenRest") if c.does_socket_exist("PenRest") else c.get_world_location()
    want = L2W(x, y, 0); want.z = top
    off = j.get_actor_location() - pen
    o_, e_, _r = unreal.SystemLibrary.get_component_bounds(c)
    j.set_actor_location(unreal.Vector(want.x + off.x, want.y + off.y, top + (j.get_actor_location().z - (o_.z - e_.z))), False, False)
    o_, e_, _r = unreal.SystemLibrary.get_component_bounds(c)
    corners = [W2L(o_ + unreal.Vector(e_.x * sx, e_.y * sy, 0)) for sx in (-1, 1) for sy in (-1, 1)]
    ok, saved = save_only([], d0, "journal")
    st["journal"] = {"actor": snap_actor(j), "pen_rest_local": W2L(c.get_socket_location("PenRest")) if c.does_socket_exist("PenRest") else None,
                     "desk_top_local_z": W2L(unreal.Vector(want.x, want.y, top))[2],
                     "rel_yaw_to_writer": round(rel_yaw, 2), "mesh": mesh.get_path_name(), "saved": saved,
                     "bottom_local_z": W2L(o_ - unreal.Vector(0, 0, e_.z))[2], "top_local_z": W2L(o_ + unreal.Vector(0, 0, e_.z))[2],
                     "footprint_local_x": [min(p[0] for p in corners), max(p[0] for p in corners)], "footprint_local_y": [min(p[1] for p in corners), max(p[1] for p in corners)]}
    json.dump(st, open(SF, "w"), indent=1); print("JOURNAL", json.dumps(st["journal"]))

elif STAGE == "verify":
    ch, ov = A["Chair_Swivel_MO"], A["Overlay_MO_DeskChair"]
    rows = {"chair": snap_actor(ch), "readback": ch.readback(), "overlay_hold": ov.get_editor_property("bHoldSeatBetweenActivities"),
            "seat_overlay": ch.get_editor_property("seat_overlay").get_actor_label() if ch.get_editor_property("seat_overlay") else None,
            "rest_swivel_local": W2L(ch.swivel_transform_at(0.0).translation), "work_swivel_local": W2L(ch.swivel_transform_at(2.0).translation),
            "life": {k: (str(a.presentation_overlay.get_actor_label()) if a.presentation_overlay else None, a.get_editor_property("bAdvertise"))
                     for k, a in A.items() if k.startswith("Life_Manager_")}, "dirty": dirty(), "forest": forest()}
    st["verify"] = rows; json.dump(st, open(SF, "w"), indent=1); print("VERIFY", json.dumps(rows))
else:
    raise SystemExit("unknown stage " + STAGE)
