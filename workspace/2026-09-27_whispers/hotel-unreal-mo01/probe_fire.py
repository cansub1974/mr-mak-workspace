"""Read-only: components using the hotel fireplace flame material, fireplace audio, and fireplace light fixtures."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
acts = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
H = next(a for a in acts if a.get_actor_label() == "HotelEden" and a.get_class().get_name() == "LevelInstance"); Hinv = H.get_actor_transform().inverse()
out = []
for a in acts:
    for c in a.get_components_by_class(unreal.ActorComponent):
        d = None
        if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh:
            mats = [m.get_path_name() if m else "" for m in c.get_materials()]
            if any("FireplaceFlame" in m for m in mats):
                d = {"mesh": c.static_mesh.get_path_name(), "mats": mats, "n": c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1}
                if isinstance(c, unreal.InstancedStaticMeshComponent):
                    t = c.get_instance_transform(0, True); p = Hinv.transform_location(t.translation)
                    d["first_local"] = [round(p.x), round(p.y), round(p.z)]; d["scale"] = str(t.scale3d)
        elif isinstance(c, unreal.AudioComponent) and c.sound and "Fire" in c.sound.get_name():
            p = Hinv.transform_location(c.get_world_location()); d = {"sound": c.sound.get_path_name(), "local": [round(p.x), round(p.y), round(p.z)],
                 "atten": c.attenuation_settings.get_path_name() if c.attenuation_settings else None, "vol": c.volume_multiplier}
        elif c.get_class().get_name() == "WhispersLightComponent" and "Fire" in a.get_class().get_name():
            p = Hinv.transform_location(a.get_actor_location()); d = {"light_id": str(c.get_editor_property("LightId")), "local": [round(p.x), round(p.y), round(p.z)]}
        if d:
            d.update(actor=a.get_actor_label(), cls=a.get_class().get_name(), comp=c.get_name(), level=a.get_level().get_outer().get_name()); out.append(d)
m = unreal.load_asset("/Game/Whispers/Presentation/Environment/HotelEden/Fireplace/M_HE_FireplaceFlame")
ml = unreal.MaterialEditingLibrary
info = {"blend": str(m.get_editor_property("blend_mode")), "shading": str(m.get_editor_property("shading_model")), "two_sided": m.get_editor_property("two_sided"),
        "scalars": [str(x) for x in ml.get_scalar_parameter_names(m)], "textures": [str(x) for x in ml.get_texture_parameter_names(m)],
        "vectors": [str(x) for x in ml.get_vector_parameter_names(m)]} if m else None
print("FIRE", json.dumps({"uses": out, "flame_material": info}))
