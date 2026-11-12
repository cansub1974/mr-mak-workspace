"""Read-only, second census for the MO01 port: E2K office furniture (transform, mesh bounds, package), the LM01 room lamp and
its zone box, the EC01 office-door portal, fixture defaults, post-process / look volumes, and assets that may hold the G01
grate. Writes review-media/hotel-unreal-mo01/Unreal_Probe_B.json."""
import unreal, json
OUT = r"C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/review-media/hotel-unreal-mo01/Unreal_Probe_B.json"
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); reg = unreal.AssetRegistryHelpers.get_asset_registry()
W = ed.get_editor_world(); acts = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
H = next(a for a in acts if a.get_actor_label() == "HotelEden" and a.get_class().get_name() == "LevelInstance")
Hinv = H.get_actor_transform().inverse()
res = {}


def tl(v):
    p = Hinv.transform_location(v); return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]


def tagname(t):
    s = t.export_text() if t else ""; return s.split('"')[1] if '"' in s else s


def mesh_local_corners(c):
    mb = c.static_mesh.get_bounding_box(); t = c.get_world_transform()
    pts = [Hinv.transform_location(t.transform_location(unreal.Vector(x, y, z))) for x in (mb.min.x, mb.max.x) for y in (mb.min.y, mb.max.y) for z in (mb.min.z, mb.max.z)]
    return [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in pts]


rows = []
for a in acts:
    lab = a.get_actor_label()
    if lab in ("Sofa_Chesterfield_MO", "Chair_Swivel_MO", "TMP_Life_Manager_Desk_SL8", "TMP_Life_Manager_ChairSeat_SL8") or str(a.get_folder_path()).startswith("Furniture/Office_MO"):
        r = {"label": lab, "class": a.get_class().get_name(), "package": a.get_package().get_name(), "folder": str(a.get_folder_path()),
             "local_loc": tl(a.get_actor_location()), "world_rot": str(a.get_actor_rotation()), "tags": [str(t) for t in a.tags], "comps": []}
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh:
                r["comps"].append({"comp": c.get_name(), "mesh": c.static_mesh.get_path_name(), "corners_local": mesh_local_corners(c),
                                   "visible": c.is_visible(), "hidden_in_game": c.get_editor_property("hidden_in_game")})
        rows.append(r)
res["e2k_office_furniture"] = rows
# lights and zone actors in the hotel level near the office, plus the EC01 portals
L = []
for a in acts:
    lab = a.get_actor_label()
    if not (lab.startswith(("LM01_RoomLamp_Level3Rooms", "LM01_Zone_Level3Rooms", "EC01_Portal", "LM01_Portal", "L6_Portal")) or "Lamp_04" in lab):
        continue
    r = {"label": lab, "class": a.get_class().get_name(), "package": a.get_package().get_name(), "folder": str(a.get_folder_path()),
         "local_loc": tl(a.get_actor_location())}
    for c in a.get_components_by_class(unreal.ActorComponent):
        cn = c.get_class().get_name()
        if cn == "WhispersLightComponent":
            r["light"] = {k: (tagname(c.get_editor_property(k)) if "Tag" in k and k != "GroupTags" else str(c.get_editor_property(k)))
                          for k in ("LightId", "ZoneTag", "RoleTag", "GroupTags", "Profile", "CircuitId") if hasattr(c, "get_editor_property")}
        if cn == "WhispersLightPortalComponent":
            r["portal"] = {"a": tagname(c.get_editor_property("ZoneA")), "b": tagname(c.get_editor_property("ZoneB")),
                           "sight": c.get_editor_property("bSightlineOnly"), "open": c.get_editor_property("bOpen")}
    if a.get_class().get_name() == "WhispersLightZoneVolume":
        r["zone"] = {"tag": tagname(a.get_editor_property("ZoneTag")), "extent": str(a.get_editor_property("BoxExtent")),
                     "never_dormant": a.get_editor_property("bNeverDormant")}
    L.append(r)
res["lighting_actors"] = L
# all zone volumes whose box contains the office centre (hotel-local 2140, 350, 1100)
inside = []
for a in acts:
    if a.get_class().get_name() != "WhispersLightZoneVolume":
        continue
    o = tl(a.get_actor_location()); e = a.get_editor_property("BoxExtent")
    if abs(o[0] - 2140) <= e.x and abs(o[1] - 350) <= e.y and abs(o[2] - 1100) <= e.z:
        inside.append({"label": a.get_actor_label(), "tag": tagname(a.get_editor_property("ZoneTag")), "origin": o, "extent": [e.x, e.y, e.z]})
res["zones_containing_office_centre"] = inside
# post-process and look volumes
pp = []
for a in acts:
    cn = a.get_class().get_name()
    if "PostProcess" in cn or "Look" in cn or "Look" in str(a.get_folder_path()):
        r = {"label": a.get_actor_label(), "class": cn, "folder": str(a.get_folder_path()), "level": a.get_level().get_outer().get_name()}
        try:
            r["unbound"] = a.get_editor_property("unbound"); r["priority"] = a.get_editor_property("priority")
            s = a.get_editor_property("settings")
            r["exposure"] = {k: str(s.get_editor_property(k)) for k in ("override_auto_exposure_bias", "auto_exposure_bias", "override_auto_exposure_method",
                                                                        "auto_exposure_method", "override_auto_exposure_min_brightness",
                                                                        "auto_exposure_min_brightness", "override_auto_exposure_max_brightness",
                                                                        "auto_exposure_max_brightness")}
            o, e = a.get_actor_bounds(False); r["bounds_world"] = [str(o), str(e)]
        except Exception as ex:
            r["err"] = str(ex)[:80]
        pp.append(r)
res["post_process"] = pp
# assets that may be the G01 grate / fireplace parts, and the furniture folder
def assets(path):
    return [(str(a.asset_name), str(a.asset_class_path.asset_name)) for a in reg.get_assets_by_path(path, recursive=True)]
res["fireplace_folder"] = assets("/Game/Whispers/Presentation/Environment/HotelEden/Fireplace")[:80]
res["furniture_folder_meshes"] = [a for a in assets("/Game/Whispers/Presentation/Environment/HotelEden/Furniture") if a[1] == "StaticMesh"][:120]
p = unreal.load_asset("/Game/Whispers/World/Lighting/Profiles/DA_LightProfile_Fireplace")
res["fireplace_profile_all"] = {n: str(p.get_editor_property(n)) for n in dir(p) if not n.startswith("_") and n[0].isupper()} if p else None
json.dump(res, open(OUT, "w"), indent=1, default=str)
print("PROBE B OK", len(rows), "furniture;", len(L), "lighting actors;", len(inside), "zones at office centre;", len(pp), "post-process")
