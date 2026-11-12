"""Read-only: hotel-local transforms (cm, quat) of the office furniture, the TMP blocks and Meredith's Life desk objects,
and each one relative to the desk. Writes review-media/hotel-unreal-mo01/Furniture_Before.json."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
REC = r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
LABELS = ("Desk_Pedestal_MO", "Chair_Swivel_MO", "Sofa_Chesterfield_MO", "TMP_Life_Manager_Desk_SL8", "TMP_Life_Manager_ChairSeat_SL8")
A = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor)}
pick = [l for l in A if l in LABELS or (l.startswith("Life_Manager_") and l.endswith("_SL8"))]
def TJ(t):
    return {"t": [t.translation.x, t.translation.y, t.translation.z], "q": [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w],
            "s": [t.scale3d.x, t.scale3d.y, t.scale3d.z], "yaw": t.rotation.rotator().yaw}
out = {"instance": I, "actors": {}}
dl = unreal.MathLibrary.compose_transforms(A["Desk_Pedestal_MO"].get_actor_transform(), Hinv)
for l in sorted(pick):
    a = A[l]; w = a.get_actor_transform(); loc = unreal.MathLibrary.compose_transforms(w, Hinv)
    rel = unreal.MathLibrary.compose_transforms(loc, unreal.MathLibrary.invert_transform(dl))
    out["actors"][l] = {"class": a.get_class().get_name(), "package": a.get_package().get_name(), "world": TJ(w), "local": TJ(loc), "rel_desk": TJ(rel),
                        "attach_parent": a.get_attach_parent_actor().get_actor_label() if a.get_attach_parent_actor() else None}
json.dump(out, open(REC + "/Furniture_Before.json", "w"), indent=1)
print("GROUP", json.dumps({l: [round(v, 2) for v in r["local"]["t"]] + [round(r["local"]["yaw"], 2), "rel", [round(v, 2) for v in r["rel_desk"]["t"]], round(r["rel_desk"]["yaw"], 2)] for l, r in out["actors"].items()}))
