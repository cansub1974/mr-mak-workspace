"""Read-only (editor, Play stopped): what the swivel desk chair setup needs (owner, 13 Nov 2026: desk and sofa 20% larger,
the chair turned ~70 deg when empty, sit / swivel / roll in, hands at desk + journal, the reception journal on her desk).

    python ue_bridge.py run probe_chair_setup.py
"""
import unreal, json
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world(); assert not ed.get_game_world()
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor)); L = {a.get_actor_label(): a for a in A}
V = lambda v: [round(v.x, 2), round(v.y, 2), round(v.z, 2)]
loc = lambda v: V(Hinv.transform_location(v))
yaw = lambda r: round(r.yaw - H.rotation.rotator().yaw, 2)
out = {}


def comp_rows(a):
    rows = {}
    for c in a.get_components_by_class(unreal.SceneComponent):
        r = {"class": c.get_class().get_name(), "rel_loc": V(c.relative_location), "rel_rot": [round(x, 2) for x in (c.relative_rotation.roll, c.relative_rotation.pitch, c.relative_rotation.yaw)],
             "rel_scale": V(c.relative_scale3d), "world_local": loc(c.get_world_location())}
        if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh:
            m = c.static_mesh; bb = m.get_bounding_box()
            r.update(mesh=m.get_path_name(), mats=[x.get_path_name() if x else None for x in c.get_materials()], box_min=V(bb.min), box_max=V(bb.max))
        rows[c.get_name()] = r
    return rows


for lab in ("Chair_Swivel_MO", "Desk_Pedestal_MO", "Sofa_Chesterfield_MO"):
    a = L.get(lab)
    if a:
        out[lab] = {"class": a.get_class().get_path_name(), "local": loc(a.get_actor_location()), "yaw_local": yaw(a.get_actor_rotation()),
                    "scale": V(a.get_actor_scale3d()), "package": a.get_package().get_name(), "components": comp_rows(a)}
# reception guest ledger
for a in A:
    if "ledger" in a.get_actor_label().lower() or "journal" in a.get_actor_label().lower():
        out.setdefault("ledgers", {})[a.get_actor_label()] = {"class": a.get_class().get_path_name(), "components": comp_rows(a),
                                                             "world": V(a.get_actor_location()), "rot": str(a.get_actor_rotation())}
# Meredith's profile and the activity definitions
m = L.get("Meredith"); body = m.get_component_by_class(unreal.WhispersBodyComponent)
prof = body.get_editor_property("profile")
out["profile"] = {"path": prof.get_path_name(), **{k: str(prof.get_editor_property(k)) for k in ("seat_calibration", "back_calibration")}}
acts = {}
for p in unreal.EditorAssetLibrary.list_assets("/Game/Whispers/Characters/Life/Activities", False):
    if "Office" in p or "Meal" in p or "Dining" in p or "Break" in p:
        d = unreal.load_asset(p)
        if isinstance(d, unreal.WhispersActivityDefinition):
            acts[p.rsplit("/", 1)[1].split(".")[0]] = {k: str(d.get_editor_property(k).get_path_name() if hasattr(d.get_editor_property(k), "get_path_name") else d.get_editor_property(k))
                                                      for k in ("EnterClip", "ExitClip", "LoopClip", "EnterSeconds", "ExitSeconds", "bSeated", "HandAnchor", "PropId", "bFitRootToSeat", "LayerMask")}
out["activities"] = acts
for p in ("/Game/Whispers/Presentation/Characters/Shared/Animation/Core/AM_SitDown_Chair_F_Action_RootMotion",
          "/Game/Whispers/Presentation/Characters/Shared/Animation/Core/AM_StandUp_Chair_F_Action_RootMotion"):
    a = unreal.load_asset(p); out.setdefault("montages", {})[p.rsplit("/", 1)[1]] = round(a.get_play_length(), 3) if a else None
# Life desk objects
life = {}
for a in A:
    if isinstance(a, unreal.WhispersLifeObject) and a.get_actor_label().startswith("Life_Manager_"):
        t = a.get_actor_transform()
        life[a.get_actor_label()] = {"local": loc(t.translation), "yaw_local": yaw(t.rotation.rotator()), "approach_rel": V(a.approach.translation), "use_rel": V(a.use.translation),
                                     "use_yaw": round(a.use.rotation.rotator().yaw, 2), "presentation": a.presentation_overlay.get_name() if a.presentation_overlay else None,
                                     "advertise": a.get_editor_property("bAdvertise"), "kind": str(a.action_kind),
                                     "parent": a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None}
out["life"] = life
print("SETUP", json.dumps(out))
