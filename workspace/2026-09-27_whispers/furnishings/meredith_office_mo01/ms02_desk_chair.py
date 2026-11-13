"""MS02 master (saved in place): Meredith's desk group as installed in L_EdenE2K on 13 Nov 2026 (owner: desk and sofa ~20%
larger - the desk wider and deeper, its height kept; the chesterfield 20% all round; the chair at its empty rest pose, turned
70 deg and rolled 30 cm back; the reception journal on the desk under her writing hand).

    blender -b --factory-startup <MS02.blend> --python ms02_desk_chair.py

Numbers come from review-media/hotel-unreal-mo01/Desk_Chair_E2K.json (the Unreal install record), so the master and the game
match. The journal is a new object on the master's own LP01 ledger mesh data (shared, not copied). Prints a receipt and writes
review-media/meredith-office-mo01/build/MS02_Desk_Chair.json.
"""
import bpy, json, math, os
from mathutils import Matrix, Vector
WS = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
ST = json.load(open(WS + "/review-media/hotel-unreal-mo01/Desk_Chair_E2K.json"))
OUT = WS + "/review-media/meredith-office-mo01/build/MS02_Desk_Chair.json"
MASTER = "D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend"
assert os.path.normcase(os.path.abspath(bpy.data.filepath)) == os.path.normcase(os.path.abspath(MASTER)), bpy.data.filepath


def ue_matrix(cm, yaw_deg):
    """Unreal hotel-local (cm, yaw) -> Blender world matrix (as build_mo01.ue_matrix): conv @ T @ R @ conv, metres."""
    conv = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))
    return conv @ (Matrix.Translation(Vector(cm) * 0.01) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")) @ conv


O = bpy.data.objects
desk, sofa = O["MO01 | Furniture | Desk (FUR-107)"], O["MO01 | Furniture | Sofa (FUR-106)"]
base, seat = O["MO01 | Furniture | Chair base (FUR-108)"], O["MO01 | Furniture | Chair seat (FUR-108)"]
before = {o.name: [round(v, 4) for v in o.matrix_world.translation] + [round(v, 4) for v in o.matrix_world.to_scale()] for o in (desk, sofa, base, seat)}

sc = ST["scale"]
d, s = sc["desk"], sc["sofa"]
desk.matrix_world = ue_matrix(d["local"], d["yaw_local"]) @ Matrix.Diagonal((*d["scale"], 1.0))
sofa.matrix_world = ue_matrix(s["local"], s["yaw_local"]) @ Matrix.Diagonal((*s["scale"], 1.0))

# the chair at rest: the carriage rolled back along the actor's -X, the seat turned on the swivel (the FUR-108 meshes face +Y)
ch = ST["chair"]["actor"]; roll = ST["plan"]["rest_roll"]; yaw = ST["plan"]["rest_yaw"]
cx, cy, cz = ch["local"]
ay = ch["yaw_local"]
rx = cx - roll * math.cos(math.radians(ay)); ry = cy - roll * math.sin(math.radians(ay))
base.matrix_world = ue_matrix((rx, ry, cz), ay - 90.0)
seat.matrix_world = ue_matrix((rx, ry, cz), ay + yaw - 90.0) @ Matrix.Translation((0, 0, 0.242))

# the journal: the reception's LP01 open guest ledger, shared mesh data, where Unreal placed Journal_Ledger_MO
j = ST["journal"]["actor"]
src = O["LP01 | Reception guest ledger | SM_HotelEden_OpenLedger_DP02"]
name = "MO01 | Furniture | Journal (LP01 reception ledger)"
jo = O.get(name)
if jo is None:
    jo = bpy.data.objects.new(name, src.data)
    bpy.data.collections["MO01 | Furniture"].objects.link(jo)
assert jo.data == src.data
jo.matrix_world = ue_matrix(j["local"], j["yaw_local"])
jo["mo01_copy_of"] = src.name; jo["mo01_unreal"] = "Journal_Ledger_MO"
for k in src.keys():
    if k not in ("mo01_copy_of",):
        jo[k] = src[k]
bpy.context.view_layer.update()


def bb(o):
    pts = [o.matrix_world @ Vector(v) for v in o.bound_box]
    return {"x": [round(min(p.x for p in pts) * 100, 1), round(max(p.x for p in pts) * 100, 1)],
            "y": [round(min(-p.y for p in pts) * 100, 1), round(max(-p.y for p in pts) * 100, 1)],
            "z": [round(min(p.z for p in pts) * 100, 1), round(max(p.z for p in pts) * 100, 1)]}


rec = {"before": before, "after_hotel_local_cm": {o.name: bb(o) for o in (desk, sofa, base, seat, jo)},
       "journal_shares_mesh": jo.data.name, "chair_rest": {"axis_cm": [round(rx, 2), round(ry, 2)], "seat_yaw": ay + yaw}}
bpy.ops.wm.save_mainfile()
json.dump(rec, open(OUT, "w"), indent=1)
print("MS02_DESK_CHAIR", json.dumps(rec))
