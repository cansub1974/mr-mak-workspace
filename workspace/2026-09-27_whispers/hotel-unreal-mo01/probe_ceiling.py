"""Read-only: hotel geometry near the office ceiling (hotel-local z 1290-1340 over the room), with each piece's z range."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
acts = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
I = json.load(open(r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/MO01_Install_State.json"))["world"]["instance"]
Hinv = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])).inverse()
out = []
for a in acts:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if not m:
            continue
        mb = m.get_bounding_box()
        ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())] if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()]
        for i, t in enumerate(ts):
            if t.scale3d.length() < 1e-3:
                continue
            pts = [Hinv.transform_location(t.transform_location(unreal.Vector(x, y, z))) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y) for z in (mb.min.z, mb.max.z)]
            xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
            if max(xs) > 1750 and min(xs) < 2550 and max(ys) > 60 and min(ys) < 640 and max(zs) > 1300 and min(zs) < 1330:
                mats = [x.get_name() if x else None for x in c.get_materials()][:3]
                out.append({"actor": a.get_actor_label(), "comp": c.get_name(), "i": i, "mesh": m.get_name(), "mats": mats,
                            "x": [round(min(xs)), round(max(xs))], "y": [round(min(ys)), round(max(ys))], "z": [round(min(zs), 2), round(max(zs), 2)],
                            "nanite": m.get_editor_property("nanite_settings").enabled})
print("CEIL", json.dumps(out)[:5000])
