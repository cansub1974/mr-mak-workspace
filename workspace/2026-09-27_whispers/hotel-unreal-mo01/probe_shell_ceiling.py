"""Read-only: the hotel shell's surfaces over the office between z 1280 and 1360 (hotel-local): for every shell triangle whose
footprint overlaps the room, its height at a 20 x 15 grid of points; reports the lowest surface per point and which mesh."""
import unreal, json
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
I = json.load(open(r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/MO01_Install_State.json"))["world"]["instance"]
Hinv = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])).inverse()
GX = [1720 + i * (2560 - 1720) / 19 for i in range(20)]; GY = [40 + j * (660 - 40) / 14 for j in range(15)]
low = {}
meshes = {}
for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor):
    if a.get_actor_label().startswith("MO01_"):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if not m or not c.is_visible():
            continue
        ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())] if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()]
        mb = m.get_bounding_box()
        for t in ts:
            if t.scale3d.length() < 1e-3:
                continue
            pts = [Hinv.transform_location(t.transform_location(unreal.Vector(x, y, z))) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y) for z in (mb.min.z, mb.max.z)]
            if not (max(p.z for p in pts) > 1280 and min(p.z for p in pts) < 1360 and max(p.x for p in pts) > 1720 and min(p.x for p in pts) < 2560
                    and max(p.y for p in pts) > 40 and min(p.y for p in pts) < 660):
                continue
            md = m.get_static_mesh_description(0); key = m.get_name()
            if md.get_triangle_count() > 400000:
                meshes[key] = "skipped (too many triangles)"; continue
            P = [Hinv.transform_location(t.transform_location(md.get_vertex_position(unreal.VertexID(i)))) for i in range(md.get_vertex_count())]
            nt = 0
            for ti in range(md.get_triangle_count()):
                vs = [P[md.get_vertex_instance_vertex(vi).id_value] for vi in md.get_triangle_vertex_instances(unreal.TriangleID(ti))]
                zs = [v.z for v in vs]
                if max(zs) < 1280 or min(zs) > 1360:
                    continue
                xs = [v.x for v in vs]; ys = [v.y for v in vs]
                if max(xs) < 1720 or min(xs) > 2560 or max(ys) < 40 or min(ys) > 660:
                    continue
                (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = [(v.x, v.y, v.z) for v in vs]
                den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
                if abs(den) < 1e-6:
                    continue
                nt += 1
                for gx in GX:
                    if gx < min(xs) or gx > max(xs):
                        continue
                    for gy in GY:
                        if gy < min(ys) or gy > max(ys):
                            continue
                        l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / den; l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / den; l3 = 1 - l1 - l2
                        if min(l1, l2, l3) < -1e-6:
                            continue
                        z = l1 * z1 + l2 * z2 + l3 * z3
                        k = (round(gx), round(gy))
                        if 1280 < z < 1360 and (k not in low or z < low[k][0]):
                            low[k] = (round(z, 2), key)
            meshes[key] = nt
zs = [v[0] for v in low.values()]
print("SHELL", json.dumps({"meshes": meshes, "points": len(low), "z_min": min(zs) if zs else None, "z_max": max(zs) if zs else None,
                           "below_1319": sorted([[k[0], k[1], v[0], v[1]] for k, v in low.items() if v[0] < 1319.5])[:60]}))
