"""MO01: survey the office in the MS02 master (read-only). Window surround outlines on the room face, glass openings,
sill/apex heights, and the room planes. Writes review-media/meredith-office-mo01/Survey_MO01.json.

    blender -b --factory-startup <MS02> --python survey_mo01.py
"""
import bpy, json, os, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/meredith-office-mo01/Survey_MO01.json"
FL = 9.004
WINDOWS = {  # name: (object name fragment, wall, wall face coordinate, inward plan normal)
    "N_W3-07": ("Window structure E01_E_A06_WINDOW_W3-07", "N", 0.3, (0, 1)),
    "N_W3-06": ("Window structure E01_E_A06_WINDOW_W3-06", "N", 0.3, (0, 1)),
    "E_W0": ("Window structure E13 WINDOW LAKE-INNER-W-0", "E", 25.7, (-1, 0)),
    "E_W1": ("Window structure E13 WINDOW LAKE-INNER-W-1", "E", 25.7, (-1, 0)),
}
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
out = {"FL": FL, "windows": {}}
for key, (frag, wall, face, n) in WINDOWS.items():
    ob = next(o for o in bpy.data.objects if frag in o.name and o.type == "MESH")
    M = ob.matrix_world
    V = np.array([tuple(M @ v.co) for v in ob.data.vertices])
    px, py, z = V[:, 0], -V[:, 1], V[:, 2]
    if wall == "N":
        s = px; proud = py - face            # + into the room
    else:
        s = py; proud = face - px
    sel = proud > 0.003
    S, Z, P = s[sel], z[sel], proud[sel]
    # outer silhouette of the proud surround per 1 cm height bin
    bins = np.arange(np.floor(Z.min() * 100) / 100, Z.max() + 0.01, 0.01)
    rows = []
    for b in bins:
        m = (Z >= b - 0.006) & (Z < b + 0.006)
        if m.sum() >= 2:
            rows.append([round(float(b), 3), round(float(S[m].min()), 4), round(float(S[m].max()), 4), round(float(P[m].max()), 4)])
    # glass opening by rays at the wall face plane (just inside), every 1 cm in s at the mid height, and vertical rays
    sc_ = (S.min() + S.max()) / 2
    def ray(o, d):
        r = sc.ray_cast(dg, Vector(o), Vector(d), distance=4.0)
        return (r[0], r[1], r[4].name if r[0] else None)
    if wall == "N":
        mk = lambda s_, zz, pr: (s_, -(face - pr), zz)
        dvec = (0, 1, 0)                     # model +y = plan north = out through the wall
    else:
        mk = lambda s_, zz, pr: (face + pr, -s_, zz)
        dvec = (1, 0, 0)
    opening = []
    out["windows"][key] = dict(object=ob.name, wall=wall, face=face, normal=n, surround_outline=rows, glass_opening=opening,
                               s_range=[round(float(S.min()), 4), round(float(S.max()), 4)], z_range=[round(float(Z.min()), 4), round(float(Z.max()), 4)],
                               proud_max=round(float(P.max()), 4))
    print("WIN", key, out["windows"][key]["s_range"], out["windows"][key]["z_range"], out["windows"][key]["proud_max"], len(rows), len(opening))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), indent=1)
print("SURVEY_MO01 OK", OUT)
