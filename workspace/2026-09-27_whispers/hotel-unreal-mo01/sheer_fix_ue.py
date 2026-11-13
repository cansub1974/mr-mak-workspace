"""Reimport SM_MO01_Sheer after fix_sheer_mo01.py (owner, 13 Nov 2026: "The sage curtains should not have the white translucent
curtains clipping through them. Please fix those."). Play stopped; the same FBX options, material, build and Nanite settings as
install_mo01.meshes() for this one asset; only the mesh asset is saved. Every placed sheer (4 windows, ISM) uses it.

    python ue_bridge.py run sheer_fix_ue.py
"""
import unreal, json
from pathlib import Path
REC = Path("C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01")
MAN = json.loads((REC / "Export_Manifest.json").read_text()); SRC = Path(MAN["export_root"])
r = MAN["resources"]["SM_MO01_Sheer"]; path = f"{r['dest']}/SM_MO01_Sheer"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world(); assert not ed.get_game_world()
smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem); lib = unreal.EditorAssetLibrary
dirty0 = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
assert not dirty0, ("unsaved packages; not importing", dirty0)
before = unreal.load_asset(path); bb0 = before.get_bounding_box()
unreal.SystemLibrary.execute_console_command(W, "Interchange.FeatureFlags.Import.FBX 0")
try:
    t = unreal.AssetImportTask(); t.filename = str(SRC / r["file"]); t.destination_path = r["dest"]; t.destination_name = "SM_MO01_Sheer"
    t.automated = True; t.save = False; t.replace_existing = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH; d = o.static_mesh_import_data
    d.combine_meshes = True; d.auto_generate_collision = False; d.one_convex_hull_per_ucx = True; d.build_nanite = False
    d.convert_scene = True; d.convert_scene_unit = True; d.force_front_x_axis = False; d.generate_lightmap_u_vs = False
    d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    d.vertex_color_import_option = unreal.VertexColorImportOption.IGNORE
    t.options = o; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
finally:
    unreal.SystemLibrary.execute_console_command(W, "Interchange.FeatureFlags.Import.FBX 1")
mesh = unreal.load_asset(path)
mesh.set_material(0, unreal.load_asset("/Game/Whispers/Presentation/Environment/HotelEden/MO01/Materials/MI_MO01_Sheer"))
body = mesh.get_editor_property("body_setup")
if body:
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
b = smes.get_lod_build_settings(mesh, 0); b.use_full_precision_u_vs = True; b.recompute_normals = False; b.recompute_tangents = False
smes.set_lod_build_settings(mesh, 0, b)
ns = mesh.get_editor_property("nanite_settings"); ns.enabled = False; smes.set_nanite_settings(mesh, ns, True)   # translucent sheer
assert lib.save_loaded_asset(mesh, only_if_is_dirty=False), path
bb = mesh.get_bounding_box(); e = r["bounds_cm_ue"]
actual = [[bb.min.x, bb.min.y, bb.min.z], [bb.max.x, bb.max.y, bb.max.z]]
err = max(abs(actual[i][j] - e[i][j]) for i in range(2) for j in range(3))
tris = mesh.get_static_mesh_description(0).get_triangle_count()
dirty1 = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
out = {"path": path, "bounds_err_cm": round(err, 4), "bounds_before_y": [round(bb0.min.y, 2), round(bb0.max.y, 2)], "bounds_after_y": [round(bb.min.y, 2), round(bb.max.y, 2)],
       "triangles": tris, "uv_channels": smes.get_num_uv_channels(mesh, 0), "material": mesh.get_material(0).get_path_name(),
       "slots": [str(s.material_slot_name) for s in mesh.static_materials], "dirty_after": dirty1}
assert err < 1.0 and abs(tris - r["triangles"]) <= 2 and out["uv_channels"] == 3, out
(REC / "Sheer_Fix_UE.json").write_text(json.dumps(out, indent=1)); print("SHEER_UE", json.dumps(out))
