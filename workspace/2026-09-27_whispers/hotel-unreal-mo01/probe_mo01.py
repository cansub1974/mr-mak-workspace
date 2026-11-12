"""Read-only census for the MO01 port (ue-mcp run_python_file; no saves, no edits).
Writes review-media/hotel-unreal-mo01/Unreal_Probe.json: lighting catalog (fixtures, profiles, flicker, moods), reusable
assets (EC01 sconce prefab and instances, AF02, P03 palm, G01 grate), gameplay tags, the HotelEden Level Instance transform,
and every actor/instance in the hotel level inside Meredith's office (hotel-local x 1710-2570, y 30-670, z 900-1320 cm).
"""
import unreal, json, math
OUT = r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/Unreal_Probe.json"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
reg = unreal.AssetRegistryHelpers.get_asset_registry()
lib = unreal.EditorAssetLibrary
res = {"world": ed.get_editor_world().get_name()}
assert not ed.get_game_world(), "Play is running"


def props(o, names):
    d = {}
    for n in names:
        try:
            v = o.get_editor_property(n)
            d[n] = v.export_text() if hasattr(v, "export_text") else (v.get_path_name() if hasattr(v, "get_path_name") else str(v))
        except Exception as e:
            d[n] = "ERR " + str(e)[:50]
    return d


def assets(path, recursive=True):
    return [(str(a.asset_name), str(a.asset_class_path.asset_name), str(a.package_name)) for a in reg.get_assets_by_path(path, recursive=recursive)]


L = "/Game/Whispers/World/Lighting"
res["fixtures"] = assets(L + "/Fixtures")
res["profiles"] = [a for a in assets(L + "/Profiles")]
res["flicker"] = [a[0] for a in assets(L + "/Flicker")]
res["moods"] = [a[0] for a in assets(L + "/Moods")]
PF = ["FixtureType", "IntensityLumens", "TemperatureK", "SourceRadiusCm", "AttenuationRadiusCm", "ShadowMethod", "bCastShadows",
      "bAllowMegaLights", "bUseEmissive", "EmissiveScalarParam", "EmissiveColorParam", "AllowedFlickerPatterns", "DefaultFlicker",
      "SupportedFaults", "DefaultRole", "SourceWidthCm", "SourceHeightCm", "BarnDoorAngle", "OuterConeAngleDegrees", "InnerConeAngleDegrees"]
res["profile_values"] = {}
for name, cls, pkg in res["profiles"]:
    if cls.endswith("Profile") or "Profile" in name:
        p = unreal.load_asset(pkg)
        if p:
            res["profile_values"][name] = props(p, PF)
# every fixture blueprint's components (class + light class) and its WhispersLight template profile
res["fixture_components"] = {}
ds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); fl = unreal.SubobjectDataBlueprintFunctionLibrary
for name, cls, pkg in res["fixtures"]:
    if cls != "Blueprint":
        continue
    bp = unreal.load_asset(pkg); rows = {}
    for h in ds.k2_gather_subobject_data_for_blueprint(bp):
        o = fl.get_object_for_blueprint(fl.get_data(h), bp)
        if isinstance(o, unreal.ActorComponent):
            r = o.get_class().get_name()
            if o.get_class().get_name() == "WhispersLightComponent":
                try:
                    r += " profile=" + (o.get_editor_property("Profile").get_name() if o.get_editor_property("Profile") else "None")
                except Exception:
                    pass
            rows[str(fl.get_variable_name(fl.get_data(h)))] = r
    res["fixture_components"][name] = rows
# reusable assets
want = {}
for a in reg.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")):
    n = str(a.asset_name)
    if any(k in n for k in ("Palm_P03", "Palm", "Grate_G01", "G01", "AF02", "Sconce_S06")):
        want.setdefault(n, []).append(str(a.package_name))
res["meshes_named"] = want
res["ec01_assets"] = [a for a in assets("/Game/Whispers/Presentation/Environment/HotelEden/EC01") if a[1] in ("Blueprint", "Material", "MaterialInstanceConstant")]
res["hoteleden_folders"] = sorted({a[2].split("/")[6] for a in assets("/Game/Whispers/Presentation/Environment/HotelEden") if len(a[2].split("/")) > 7})
# tags
res["tags"] = {t: unreal.GameplayTagService.has_tag(t) for t in ("Light.Zone.Hotel.MeredithOffice", "Light.Zone.Hotel.ExecutiveCorridor",
                                                                 "Light.Zone.Hotel.Level3Rooms", "Light.Role.Fire", "Light.Role.Fill",
                                                                 "Light.Role.Practical", "Light.Group.ExecutiveSconces")}
# the HotelEden level instance in this world
W = ed.get_editor_world()
acts = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
li = [a for a in acts if a.get_class().get_name().startswith("LevelInstance") or "LevelInstance" in a.get_class().get_name()]
res["level_instances"] = [{"label": a.get_actor_label(), "class": a.get_class().get_name(),
                           "t": [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z],
                           "r": [a.get_actor_rotation().roll, a.get_actor_rotation().pitch, a.get_actor_rotation().yaw],
                           "s": [a.get_actor_scale3d().x, a.get_actor_scale3d().y, a.get_actor_scale3d().z],
                           } for a in li]
for row, a in zip(res["level_instances"], li):
    try:
        row["level"] = str(a.get_editor_property("world_asset"))
    except Exception:
        row["level"] = None
H = next((a for a in li if a.get_actor_label() == "HotelEden" and a.get_class().get_name() == "LevelInstance"), None) or     next((a for a in li if a.get_actor_label() == "HotelEden"), None)
Ht = H.get_actor_transform() if H else unreal.Transform()
Hinv = Ht.inverse()
BOX = (1710, 2570, 30, 670, 900, 1320)


def local_box(corners):
    pts = [Hinv.transform_location(c) for c in corners]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def corners(o, e):
    return [unreal.Vector(o.x + sx * e.x, o.y + sy * e.y, o.z + sz * e.z) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def hit(b):
    return b[1] > BOX[0] and b[0] < BOX[1] and b[3] > BOX[2] and b[2] < BOX[3] and b[5] > BOX[4] and b[4] < BOX[5]


inside = []
for a in acts:
    if a == H:
        continue
    lvl = a.get_level().get_outer().get_name() if a.get_level() else None
    try:
        o, e = a.get_actor_bounds(False)
    except Exception:
        continue
    if e.length() < 1e-3:
        b = local_box([a.get_actor_location()])
    else:
        b = local_box(corners(o, e))
    if not hit(b):
        continue
    row = {"label": a.get_actor_label(), "class": a.get_class().get_name(), "level": lvl, "folder": str(a.get_folder_path()),
           "local_bounds": [round(x, 1) for x in b], "comps": []}
    big = (b[1] - b[0]) > 1500 or (b[3] - b[2]) > 1500
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            n = c.get_instance_count(); m = c.static_mesh
            if m is None or n == 0:
                continue
            mb = m.get_bounding_box(); hits = []
            for i in range(n):
                t = c.get_instance_transform(i, True)
                cs = [t.transform_location(unreal.Vector(x, y, z)) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y) for z in (mb.min.z, mb.max.z)]
                bb = local_box(cs)
                if hit(bb) and t.scale3d.length() > 1e-3:
                    hits.append((i, [round(x) for x in bb]))
            if hits:
                row["comps"].append({"comp": c.get_name(), "mesh": m.get_name(), "instances": n, "inside": len(hits), "sample": hits[:4],
                                     "collision": str(c.get_collision_enabled())})
        elif isinstance(c, unreal.StaticMeshComponent) and c.static_mesh:
            mb = c.static_mesh.get_bounding_box(); t = c.get_world_transform()
            bb = local_box([t.transform_location(unreal.Vector(x, y, z)) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y)
                            for z in (mb.min.z, mb.max.z)])
            if hit(bb):
                row["comps"].append({"comp": c.get_name(), "mesh": c.static_mesh.get_name(), "bounds": [round(x) for x in bb],
                                     "visible": c.is_visible(), "collision": str(c.get_collision_enabled())})
        elif isinstance(c, unreal.LightComponent):
            row["comps"].append({"comp": c.get_name(), "light": c.get_class().get_name()})
    if row["comps"] or not big:
        inside.append(row)
res["hotel_transform"] = {"t": [Ht.translation.x, Ht.translation.y, Ht.translation.z], "r": str(Ht.rotation.rotator()), "s": str(Ht.scale3d)}
res["inside_office"] = inside
json.dump(res, open(OUT, "w"), indent=1, default=str)
print("PROBE OK", res["world"], "fixtures", len(res["fixtures"]), "profiles", len(res["profiles"]), "inside", len(inside))
