"""Read-only: the three office furniture assets in Unreal (bounds/pivot, triangles, collision, Nanite, materials, textures)
and BP_SwivelChair's components."""
import unreal, json
F = "/Game/Whispers/Presentation/Environment/HotelEden/Furniture"
mel = unreal.MaterialEditingLibrary; smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
out = {}
for p in ("SofaChesterfield/SM_SofaChesterfield", "ChairSwivel/SM_ChairSwivel_Base", "ChairSwivel/SM_ChairSwivel_Seat", "DeskPedestal/SM_DeskPedestal"):
    m = unreal.load_asset(f"{F}/{p}"); bb = m.get_bounding_box(); bs = m.get_editor_property("body_setup"); ag = bs.get_editor_property("agg_geom")
    r = {"bounds_min": [round(bb.min.x, 2), round(bb.min.y, 2), round(bb.min.z, 2)], "bounds_max": [round(bb.max.x, 2), round(bb.max.y, 2), round(bb.max.z, 2)],
         "tris": m.get_static_mesh_description(0).get_triangle_count(), "nanite": m.get_editor_property("nanite_settings").enabled,
         "collision": {"boxes": len(ag.get_editor_property("box_elems")), "convex": len(ag.get_editor_property("convex_elems")),
                       "spheres": len(ag.get_editor_property("sphere_elems")), "trace": str(bs.get_editor_property("collision_trace_flag"))},
         "uv_channels": smes.get_num_uv_channels(m, 0), "import_file": None, "mats": []}
    try:
        ai = m.get_editor_property("asset_import_data"); r["import_file"] = ai.get_first_filename() if ai else None
    except Exception:
        pass
    for sm in m.static_materials:
        mi = sm.material_interface; row = {"slot": str(sm.material_slot_name), "mi": mi.get_path_name().split(".")[0] if mi else None}
        if isinstance(mi, unreal.MaterialInstanceConstant):
            row["parent"] = mi.get_editor_property("parent").get_path_name().split(".")[0]
            row["textures"] = {str(t.parameter_info.name): (t.parameter_value.get_name() if t.parameter_value else None) for t in mi.get_editor_property("texture_parameter_values")}
            row["switches"] = {str(n): mel.get_material_instance_static_switch_parameter_value(mi, n) for n in mel.get_static_switch_parameter_names(mi)} if hasattr(mel, "get_static_switch_parameter_names") else None
            row["scalars"] = {str(s.parameter_info.name): round(s.parameter_value, 3) for s in mi.get_editor_property("scalar_parameter_values")}
        r["mats"].append(row)
    out[p.split("/")[-1]] = r
for t in ("SofaChesterfield/T_SofaChesterfield_BC", "SofaChesterfield/T_SofaChesterfield_N", "SofaChesterfield/T_SofaChesterfield_ORM", "ChairSwivel/T_ChairSwivel_BC",
          "ChairSwivel/T_ChairSwivel_N", "ChairSwivel/T_ChairSwivel_ORM", "DeskPedestal/T_DeskPedestal_BC", "DeskPedestal/T_DeskPedestal_ORM"):
    x = unreal.load_asset(f"{F}/{t}")
    out[t.split("/")[-1]] = {"size": [x.blueprint_get_size_x(), x.blueprint_get_size_y()], "srgb": x.get_editor_property("srgb"),
                             "comp": str(x.get_editor_property("compression_settings")), "flipG": x.get_editor_property("flip_green_channel")}
ds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); fl = unreal.SubobjectDataBlueprintFunctionLibrary
bp = unreal.load_asset(f"{F}/ChairSwivel/BP_SwivelChair"); comps = {}
for h in ds.k2_gather_subobject_data_for_blueprint(bp):
    o = fl.get_object_for_blueprint(fl.get_data(h), bp)
    if isinstance(o, unreal.SceneComponent):
        comps[o.get_name()] = {"cls": o.get_class().get_name(), "loc": str(o.get_editor_property("relative_location")), "rot": str(o.get_editor_property("relative_rotation")),
                               "mesh": o.static_mesh.get_name() if isinstance(o, unreal.StaticMeshComponent) and o.static_mesh else None,
                               "collision": str(o.get_collision_profile_name()) if isinstance(o, unreal.PrimitiveComponent) else None}
out["BP_SwivelChair"] = {"components": comps}
print("FASSETS", json.dumps(out))
