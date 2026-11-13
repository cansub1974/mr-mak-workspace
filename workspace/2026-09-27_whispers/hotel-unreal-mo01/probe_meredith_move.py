"""Read-only, in Play: why Meredith is not walking (movement mode, velocity, montages, path following, command, Body state).

    python ue_bridge.py run probe_meredith_move.py
"""
import unreal, json
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
L = lambda v: [round(c, 1) for c in (lambda q: (q.x, q.y, q.z))(Hinv.transform_location(v))]
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); assert w
a = next(x for x in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.WhispersNPCCharacter) if x.commands.get_npc_id() == "npc.meredith")
cm = a.get_component_by_class(unreal.CharacterMovementComponent); b = a.get_component_by_class(unreal.WhispersBodyComponent)
ctrl = a.get_controller()
pf = ctrl.get_component_by_class(unreal.PathFollowingComponent) if ctrl else None
montages = []
for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
    ai = c.get_anim_instance()
    if ai:
        m = ai.get_current_active_montage()
        montages.append((c.get_name(), m.get_name() if m else None))
row = {"actor": L(a.get_actor_location()), "mode": str(cm.movement_mode), "velocity": round(a.get_velocity().length(), 1),
       "max_walk": cm.max_walk_speed, "pf_status": str(pf.get_path_following_status()) if pf and hasattr(pf, "get_path_following_status") else None,
       "montages": montages, "body": b.get_activity_readback()[:500], "phase": str(b.get_editor_property("phase")),
       "held": b.get_editor_property("bSeatHeld"), "awaiting": b.get_editor_property("bExitAwaitingSeat"),
       "active_op": str(a.commands.get_editor_property("active_op")) if hasattr(a.commands, "active_op") else None,
       "ignored_by_capsule": [x.get_actor_label() for x in a.capsule_component.get_editor_property("move_ignore_actors")] if hasattr(a.capsule_component, "move_ignore_actors") else None}
print("MOVE", json.dumps(row, default=str))
