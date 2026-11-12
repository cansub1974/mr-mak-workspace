"""MO01 drapes kit: point M_MO01_Sheer's fold normal (UV0_Bake) at T_MO01_SheerFolds_NormalGL.png (Blender, background).

    blender -b --factory-startup kit/MO01_Kit_drapes.blend --python fix_sheer_kit.py -- --save

Found 12 Nov at the Unreal port: the drapes bake wrote the sheer's fold normal as T_MO01_Sheer_NormalGL.png, the name of the
tiling crepe weave (prepare_textures.sheer), so both of the sheer's normal nodes read the fold bake. The bake is now
T_MO01_SheerFolds_NormalGL.png (mo01_drapes.fold_name), the weave was regenerated, and this repoints the kit's material
without re-baking. Everything else in the kit is left alone.
"""
import bpy, os, sys

TEX = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01/textures"
m = bpy.data.materials["M_MO01_Sheer"]
nt = m.node_tree
uvmap = {}
for l in nt.links:
    if l.to_node.type == "TEX_IMAGE" and l.from_node.type == "UVMAP":
        uvmap[l.to_node.name] = l.from_node.uv_map
weave = [n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("T_MO01_Sheer_NormalGL")]
assert len(weave) == 2, [n.name for n in weave]
fold = next(n for n in weave if uvmap[n.name] == "UV0_Bake")
im = bpy.data.images.load(os.path.join(TEX, "T_MO01_SheerFolds_NormalGL.png"), check_existing=True)
im.colorspace_settings.name = "Non-Color"
fold.image = im
w = next(n for n in weave if uvmap[n.name] == "UV1_Fabric").image
assert not w.packed_file, "the weave image is packed in the kit"
w.reload()
print("SHEER KIT", {n.name: (n.image.name, uvmap.get(n.name)) for n in nt.nodes if n.type == "TEX_IMAGE"})
if "--save" in sys.argv:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
