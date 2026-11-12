"""Meredith's office furniture (the Tripo-baked sofa, desk and swivel chair) -> approved library packages (Blender, background).

    blender -b --factory-startup --python package_furniture.py -- <sofa|desk|chair>

Owner, 12 Nov 2026: "D:\\Unreal Projects\\Whispers 5.8\\Saved\\Renders\\ there are blender files in there for the sofa, the desk
and the chair. Copy them over to where you keep all the other models and add them to the approved furniture list. Add them
to Meredith's office Blender file and place them like in the reference image. [...] Ensure that they are scaled properly"

Source: the working copy D:/AI_Modelling/hotel_eden/working/furnishings_MO01_furniture/<piece>_bake (copied unchanged from
Saved/Renders; made by another session, baked from Tripo models). The game asset is the very FBX Unreal imported
(<piece>_bake/export), so the Blender and Unreal meshes, pivots (base centre) and sizes are identical by construction.
Writes approved-media/<slug>/: <ID>_Game.blend (the game mesh in metres, identity transform, its material on the export maps),
<ID>_Bake_Source.blend (+ the desk's Tripo source), exports/, previews/, Package_Info.json.
"""
import bpy, json, os, shutil, sys, hashlib
import numpy as np
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PIECE = ARGS[0]
W = "D:/AI_Modelling/hotel_eden/working/furnishings_MO01_furniture"
CARD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPEC = {   # Unreal mesh bounds (cm), read from the imported assets on 12 Nov
    "sofa": dict(id="FUR-106", rev="CF01", slug="sofa-chesterfield-cf01", name="SofaChesterfield",
                 fbx={"SM_SofaChesterfield": ("SM_SofaChesterfield.fbx", (194.5, 104.54, 75.98), 0.0)},
                 tex=("T_SofaChesterfield_BC.png", "T_SofaChesterfield_N.png", "T_SofaChesterfield_ORM.png"),
                 sources=["sofa_bake/sofa_bake.blend"],
                 previews=["renders/sofa_chestnut_front.png", "renders/sofa_chestnut_close.png", "renders/sofa_front.png", "renders/sofa_back.png",
                           "sofa_bake/low_front.png", "sofa_bake/low_close.png", "sofa_bake/high_front.png"]),
    "desk": dict(id="FUR-107", rev="PD01", slug="desk-pedestal-pd01", name="DeskPedestal",
                 fbx={"SM_DeskPedestal": ("SM_DeskPedestal.fbx", (101.36, 191.92, 76.98), 0.0)},
                 tex=("T_DeskPedestal_BC.png", None, "T_DeskPedestal_ORM.png"),
                 sources=["desk_bake/desk_bake.blend", "desk_bake/desk_source.blend"],
                 previews=["desk_bake/game_front.png", "desk_bake/game_sitter.png", "renders/desk_mahogany_front.png", "renders/desk_leather_top.png",
                           "renders/desk_leather_close.png", "desk_bake/ue_desk_bc.png"]),
    "chair": dict(id="FUR-108", rev="SW01", slug="chair-swivel-sw01", name="ChairSwivel",
                  fbx={"SM_ChairSwivel_Base": ("SM_ChairSwivel_Base.fbx", (72.16, 72.18, 24.21), 0.0),
                       "SM_ChairSwivel_Seat": ("SM_ChairSwivel_Seat.fbx", (80.73, 79.99, 76.71), 0.242)},    # BP_SwivelChair: Seat at z 24.2 cm
                  tex=("T_ChairSwivel_BC.png", "T_ChairSwivel_N.png", "T_ChairSwivel_ORM.png"),
                  sources=["chair_bake/chair_bake.blend"],
                  previews=["chair_bake/low_front.png", "chair_bake/high_front.png", "chair_bake/split_close.png", "chair_bake/split_swivel35.png",
                            "chair_bake/ue_chair_a.png"]),
}[PIECE]
SRC = os.path.join(W, f"{PIECE}_bake")
OUT = os.path.join(CARD, "approved-media", SPEC["slug"]); os.makedirs(os.path.join(OUT, "exports"), exist_ok=True); os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)
info = {"id": SPEC["id"], "revision": SPEC["rev"], "piece": PIECE, "objects": {}}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# exports (FBX + maps) and the sources, copied unchanged
for f in os.listdir(os.path.join(SRC, "export")):
    if f.endswith("_N8.png"):
        continue                                          # an 8-bit preview copy of the sofa normal; the 16-bit map is the asset
    shutil.copy2(os.path.join(SRC, "export", f), os.path.join(OUT, "exports", f))
for i, s in enumerate(SPEC["sources"]):
    dst = f"{SPEC['rev']}_Bake_Source.blend" if i == 0 else f"{SPEC['rev']}_Tripo_Source.blend"
    shutil.copy2(os.path.join(W, s), os.path.join(OUT, dst)); info.setdefault("sources", {})[dst] = s
for p in SPEC["previews"]:
    if os.path.exists(os.path.join(W, p)):
        shutil.copy2(os.path.join(W, p), os.path.join(OUT, "previews", os.path.basename(p)))

# the game mesh(es): the export FBX, in metres at identity, base centre at the origin
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
mat = bpy.data.materials.new("M_" + SPEC["name"]); mat.use_nodes = True
nt = mat.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")


def tex(fn, data, x, y):
    t = nt.nodes.new("ShaderNodeTexImage"); t.location = (x, y)
    t.image = bpy.data.images.load(os.path.join(OUT, "exports", fn)); t.image.colorspace_settings.name = "Non-Color" if data else "sRGB"
    return t


bc, nm, orm = SPEC["tex"]
tb = tex(bc, False, -600, 300); nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
to = tex(orm, True, -600, 0); sp = nt.nodes.new("ShaderNodeSeparateColor"); sp.location = (-300, 0); nt.links.new(to.outputs["Color"], sp.inputs["Color"])
nt.links.new(sp.outputs["Green"], b.inputs["Roughness"]); nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
if nm:
    tn = tex(nm, True, -600, -300); n = nt.nodes.new("ShaderNodeNormalMap"); n.location = (-300, -300)     # OpenGL, as baked
    nt.links.new(tn.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
info["material"] = {"name": mat.name, "maps": [x for x in SPEC["tex"] if x], "note": "Unreal: MI_" + SPEC["name"] + " on M_HE_Master_PBR with the same maps (AO in ORM.R)"}

for name, (fbx, ue_cm, z_off) in SPEC["fbx"].items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(OUT, "exports", fbx))
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    assert len(new) == 1, [o.name for o in new]
    o = new[0]
    for x in [x for x in bpy.data.objects if x not in before and x != o]:
        bpy.data.objects.remove(x, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    o.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.name = name; o.data.name = name
    o.data.materials.clear(); o.data.materials.append(mat)
    co = np.array([v.co[:] for v in o.data.vertices])
    lo, hi = co.min(0), co.max(0); dims = (hi - lo) * 100
    # Unreal's frame: UE x = Blender x, UE y = -Blender y; sizes must agree within 2 mm
    assert max(abs(dims[i] - ue_cm[i]) for i in range(3)) < 0.2, (name, dims.round(2).tolist(), ue_cm)
    assert abs(lo[2]) < 0.002 and abs((lo[0] + hi[0]) / 2) < 0.01 and abs((lo[1] + hi[1]) / 2) < 0.01, (name, lo, hi)   # base centre pivot
    o.location = (0, 0, z_off)
    r = {"dims_cm": dims.round(2).tolist(), "triangles": sum(len(p.vertices) - 2 for p in o.data.polygons), "uv": [u.name for u in o.data.uv_layers],
         "z_offset_m": z_off}
    if PIECE == "sofa":       # which long side carries the tall back: mean height of the top tenth on each side
        top = co[co[:, 2] > np.percentile(co[:, 2], 90)]
        r["back_side_blender_y"] = "+Y" if top[:, 1].mean() > 0 else "-Y"
        r["back_side_unreal_local_y"] = "-Y" if top[:, 1].mean() > 0 else "+Y"
    info["objects"][name] = r
for im in bpy.data.images:
    if im.filepath:
        im.filepath = bpy.path.relpath(im.filepath)
game = os.path.join(OUT, f"{SPEC['rev']}_Game.blend")
bpy.ops.wm.save_as_mainfile(filepath=game, relative_remap=True)
info["files"] = {os.path.relpath(os.path.join(dp, f), OUT).replace("\\", "/"): {"bytes": os.path.getsize(os.path.join(dp, f)), "sha256": sha(os.path.join(dp, f))}
                 for dp, _, fs in os.walk(OUT) for f in fs if not f.endswith((".blend1", "Package_Info.json"))}
json.dump(info, open(os.path.join(OUT, "Package_Info.json"), "w"), indent=1)
print("PACKAGED", PIECE, json.dumps({k: v for k, v in info["objects"].items()}))
