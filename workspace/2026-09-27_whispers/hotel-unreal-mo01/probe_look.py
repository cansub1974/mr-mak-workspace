"""Read-only: every overridden setting of the hotel's interior look volume and E2K's look post, plus its bounds."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
out = {}
for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.PostProcessVolume):
    if a.get_actor_label() not in ("HotelEden_InteriorLook", "E2K_LookPost"):
        continue
    s = a.get_editor_property("settings"); d = {}
    for n in dir(s):
        if n.startswith("override_"):
            try:
                if s.get_editor_property(n):
                    k = n[len("override_"):]
                    v = s.get_editor_property(k); d[k] = v if isinstance(v, (int, float, bool, str)) else str(v)[:80]
            except Exception:
                pass
    o, e = a.get_actor_bounds(False)
    out[a.get_actor_label()] = {"priority": a.get_editor_property("priority"), "unbound": a.get_editor_property("unbound"),
                                "blend_radius": a.get_editor_property("blend_radius"), "overrides": d, "bounds": [str(o), str(e)]}
print("LOOK", json.dumps(out))
