"""Set M_MO01_Translucent to Surface ForwardShading (the enum name differs on this build), recompile, save; read back."""
import unreal
names = [n for n in dir(unreal.TranslucencyLightingMode) if n.startswith("TLM")]
print("TLM", names)
m = unreal.load_asset("/Game/Whispers/Presentation/Environment/HotelEden/MO01/Materials/M_MO01_Translucent")
want = next(n for n in names if n in ("TLM_SURFACE", "TLM_SURFACE_FORWARD_SHADING"))
m.set_editor_property("translucency_lighting_mode", getattr(unreal.TranslucencyLightingMode, want))
unreal.MaterialEditingLibrary.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
print("TLM set", want, m.get_editor_property("translucency_lighting_mode"), "two_sided", m.get_editor_property("two_sided"), m.get_editor_property("blend_mode"))
