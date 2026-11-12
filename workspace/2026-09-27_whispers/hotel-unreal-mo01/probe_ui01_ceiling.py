"""Read-only: vertices of the hotel's Unreal interior shells near the office ceiling (hotel-local), per mesh: z histogram."""
import unreal, json, collections
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
I = json.load(open(r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/MO01_Install_State.json"))["world"]["instance"]
Hinv = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])).inverse()
out = {}
for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor):
    if not a.get_actor_label().startswith("UI01_ZONE"):
        continue
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = c.static_mesh
        if not m or c.get_instance_count() == 0:
            continue
        t = c.get_instance_transform(0, True); mb = m.get_bounding_box()
        pts = [Hinv.transform_location(t.transform_location(unreal.Vector(x, y, z))) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y) for z in (mb.min.z, mb.max.z)]
        if not (max(p.z for p in pts) > 1290 and min(p.z for p in pts) < 1330 and max(p.x for p in pts) > 1750 and min(p.x for p in pts) < 2550
                and max(p.y for p in pts) > 60 and min(p.y for p in pts) < 640):
            continue
        md = m.get_static_mesh_description(0); n = md.get_vertex_count(); hist = collections.Counter(); xy = []
        for i in range(n):
            v = Hinv.transform_location(t.transform_location(md.get_vertex_position(unreal.VertexID(i))))
            if 1740 < v.x < 2560 and 40 < v.y < 660 and 1250 < v.z < 1340:
                hist[round(v.z, 1)] += 1
                if len(xy) < 12:
                    xy.append([round(v.x), round(v.y), round(v.z, 2)])
        if hist:
            out[f"{a.get_actor_label()}/{c.get_name()}"] = {"mesh": m.get_name(), "mat": [x.get_name() if x else None for x in c.get_materials()][:2],
                                                           "verts": n, "z_hist": sorted(hist.items())[:20], "sample": xy}
print("UI01C", json.dumps(out))
