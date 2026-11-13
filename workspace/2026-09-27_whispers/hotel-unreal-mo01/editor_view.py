"""Editor viewport camera at a hotel-local view of Meredith's desk (no Play), optionally posing the swivel chair (PreviewDock).

    python ue_bridge.py run editor_view.py <view> [dock 0..2]
Views as pie_meredith.py's eye, plus "top" (looking down on the desk group). PreviewDock is not saved: the chair's
construction puts it back at rest; this script restores 0 when called without a dock value.
"""
import unreal, json, sys, math
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
VIEW = sys.argv[1] if len(sys.argv) > 1 else "desk"
DOCK = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"]))
VIEWS = {"desk": ((2330, 560, 1065.4), (1960, 380, 995.4)), "desk_side": ((1990, 120, 1060.4), (1960, 410, 980.4)),
         "room": ((2510, 605, 1055.4), (1760, 290, 1045.4)), "top": ((1990, 470, 1240), (1960, 410, 905)),
         "chair_front": ((1990, 560, 1010), (1915, 405, 940)), "sofa": ((2110, 520, 1060), (2110, 120, 960))}
eye, at = VIEWS[VIEW]
E, T = H.transform_location(unreal.Vector(*eye)), H.transform_location(unreal.Vector(*at))
d = T - E
r = unreal.Rotator(roll=0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x)))
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(E, r)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ch = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor) if a.get_actor_label() == "Chair_Swivel_MO"), None)
if ch and hasattr(ch, "preview_dock"):
    ch.preview_dock(DOCK)
print("VIEW", json.dumps({"view": VIEW, "dock": DOCK, "readback": ch.readback() if ch else None,
                          "dirty": [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]}))
