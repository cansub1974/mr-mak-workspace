"""Read-only (editor, Play stopped): the office furniture's bounds against the palm planter and Meredith's placed spot (hotel-local cm).

    python ue_bridge.py run probe_office_clearances.py
"""
import unreal, json
REC = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world(); assert not ed.get_game_world()
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
A = {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor)}


def box(a, comp_filter=None):
    o, e = a.get_actor_bounds(True)
    pts = [Hinv.transform_location(o + unreal.Vector(e.x * x, e.y * y, e.z * z)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    return {k: [round(min(getattr(p, k) for p in pts), 1), round(max(getattr(p, k) for p in pts), 1)] for k in "xyz"}


out = {l: box(A[l]) for l in ("Sofa_Chesterfield_MO", "Desk_Pedestal_MO", "Chair_Swivel_MO") if l in A}
palm = [l for l in A if "Palm" in l and ("MO01" in l or "MO_" in l or "Office" in l)]
out["palm_actors"] = {l: box(A[l]) for l in palm[:4]}
m = A.get("Meredith")
out["meredith"] = [round(v, 1) for v in (lambda p: (p.x, p.y, p.z))(Hinv.transform_location(m.get_actor_location()))] if m else None
print("CLEAR", json.dumps(out))
