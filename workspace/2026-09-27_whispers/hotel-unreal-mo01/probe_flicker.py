import unreal
c = unreal.WhispersLightComponent
names = [n for n in dir(c) if "flick" in n.lower() or "mood" in n.lower() or "base" in n.lower()]
p = unreal.load_asset("/Game/Whispers/World/Lighting/Profiles/DA_LightProfile_Fireplace")
pn = [n for n in dir(p) if "flick" in n.lower()]
print("FLK comp", names, "| profile", pn, "| allowed", p.get_editor_property("allowed_flicker_patterns") if hasattr(p, "allowed_flicker_patterns") else None)
for n in pn:
    try:
        print("FLK", n, p.get_editor_property(n))
    except Exception as e:
        print("FLK", n, "ERR", e)
