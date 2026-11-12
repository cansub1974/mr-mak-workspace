"""MO01 Meredith's office into Whispers 5.8 (live editor, ue-mcp bridge run_python_file, which does not auto-save).

    python ue_bridge.py run install_mo01.py <stage>

Owner, 12 Nov 2026: "Sync the corridor lights in MS02 to match Unreal. Then port the Blender model of Meredith's office into
the Unreal Hotel Edn 2k level. Beautiful game quality, moody lighting. Simple colliders."
L_EdenE2K shows L_HotelEden_Building through the HotelEden Level Instance, so the office goes into the Building level (as EC01).
One stage per call; state in review-media/hotel-unreal-mo01/MO01_Install_State.json:

  checkpoint     copy L_HotelEden_Building (map + external actors/objects) and DefaultGameplayTags.ini to Saved/MCP/HotelMO01
  textures       import the runtime textures (BaseColor sRGB; NormalGL -> TC_Normalmap, green flipped; ORM / AO masks)
  materials      M_MO01_Surface (opaque) and M_MO01_Translucent: the EC01 surface graph rebuilt from the Blender graphs plus a
                 UV1 tiling scale (Blender Mapping nodes), vertex-colour soot and opacity; one instance per Blender material.
                 The EC01 woods and brass reuse the EC01 instances; the fire cards use the lobby's M_HE_FireplaceFlame.
  meshes         import the FBXs (legacy importer, normals + tangents, UCX, vertex colours), slots, Nanite, simple collision
  fixtures       gameplay tags (zone MeredithOffice, group MeredithOffice) and DA_LightProfile_MO01_WindowFill
  open_building  load L_HotelEden_Building (refuses with unsaved packages)
  place          in the open Building level: MO01_MeredithOffice (one ISM per asset), the ten light fixtures with identity,
                 the fire (cards + crackle), the office light zone and its portals; LM01's generic room lamp and box for
                 this room are retired with restore records; save
  update         in the open Building level: move instances that no longer match the current export (after a master rebuild); save
  look           in the open Building level: MO01_OfficeLook, the office's post volume (Lumen final gather, exposure); save
  verify         in the open Building level: read everything back
  open_e2k       load L_EdenE2K
  world          in L_EdenE2K: read the office back through the HotelEden Level Instance
"""
import unreal, json, math, shutil, collections, sys, re
from pathlib import Path

STAGE = sys.argv[1] if len(sys.argv) > 1 else "verify"
CARD = Path("C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers")
REC = CARD / "review-media/hotel-unreal-mo01"
MAN = json.loads((REC / "Export_Manifest.json").read_text())
SRC = Path(MAN["export_root"])
SF = REC / "MO01_Install_State.json"
st = json.loads(SF.read_text()) if SF.exists() else {}
HE = "/Game/Whispers/Presentation/Environment/HotelEden"
D = HE + "/MO01"; DMI = D + "/Materials"
EC = HE + "/EC01"
BUILDING = "/Game/Whispers/World/HotelEden/L_HotelEden_Building"
E2K = "/Game/Whispers/World/EdenE2K/L_EdenE2K"
ACTOR = "MO01_MeredithOffice"; FOLDER = "Hotel Eden/Meredith office MO01"; TAG = "HotelEden_MO01"
LIGHT_FOLDER = "Lighting/Hotel/MeredithOffice"; ZONE_FOLDER = "Lighting/Zones/Hotel"
ZONE = "Light.Zone.Hotel.MeredithOffice"; GROUP = "Light.Group.MeredithOffice"
ROLES = {"Fireplace": "Light.Role.Fire", "WindowFill": "Light.Role.Fill", "PictureLight": "Light.Role.Practical", "WallSconce": "Light.Role.Practical"}
FIXTURES = {"Fireplace": "/Game/Whispers/World/Lighting/Fixtures/BP_Light_Fireplace",
            "WindowFill": "/Game/Whispers/World/Lighting/Fixtures/BP_Light_WindowFill",
            "PictureLight": "/Game/Whispers/World/Lighting/Fixtures/BP_Light_WallSconce",
            "WallSconce": EC + "/BP_EC01_WallSconce_S06"}
PROFILES = "/Game/Whispers/World/Lighting/Profiles"
MO_WINDOWFILL = PROFILES + "/DA_LightProfile_MO01_WindowFill"
FLAME = HE + "/Fireplace/M_HE_FireplaceFlame"
lib = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem); es = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); fl = unreal.SubobjectDataBlueprintFunctionLibrary
assert unreal.Paths.get_project_file_path().replace("\\", "/").endswith("Whispers 5.8/Whispers.uproject")
assert not ed.get_game_world(), "stop Play first"


def bkey(name):
    """A Blender material name without its re-append suffix (.001, .002 ...)."""
    return re.sub(r"\.\d{3}$", "", name)


def save_state():
    SF.write_text(json.dumps(st, indent=1, default=str))


def P(*a):
    print("MO01", *a)


def T(r):
    return unreal.Transform(unreal.Vector(*r["translation_cm"]), unreal.Quat(*r["rotation_quat"]).rotator(), unreal.Vector(*r["scale"]))


def TJ(t):
    return {"translation_cm": [t.translation.x, t.translation.y, t.translation.z],
            "rotation_quat": [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w], "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z]}


def dirty():
    return [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]


def world():
    return ed.get_editor_world()


def acts():
    return list(unreal.GameplayStatics.get_all_actors_of_class(world(), unreal.Actor))


def by_label(label):
    return next((a for a in acts() if a.get_actor_label() == label), None)


def tag(name):
    t = unreal.GameplayTag(); assert t.import_text('(TagName="%s")' % name), name; return t


def tags(*names):
    c = unreal.GameplayTagContainer(); assert c.import_text("(GameplayTags=(%s))" % ",".join('(TagName="%s")' % n for n in names)); return c


def tag_name(t):
    s = t.export_text(); return s.split('"')[1] if '"' in s else ""


# ================================================================================================= checkpoint
def checkpoint():
    content = Path(unreal.Paths.project_content_dir()); ck = Path(unreal.Paths.project_saved_dir()) / "MCP/HotelMO01/Checkpoint"
    ck.mkdir(parents=True, exist_ok=True); out = {}
    rel = BUILDING.replace("/Game/", ""); name = "L_HotelEden_Building"; dst = ck / name; dst.mkdir(exist_ok=True)
    if not (dst / (name + ".umap")).exists():
        shutil.copy2(content / (rel + ".umap"), dst / (name + ".umap"))
    for kind in ("__ExternalActors__", "__ExternalObjects__"):
        src = content / kind / rel
        if src.exists() and not (dst / kind).exists():
            shutil.copytree(src, dst / kind)
    ini = Path(unreal.Paths.project_config_dir()) / "DefaultGameplayTags.ini"
    if not (ck / ini.name).exists():
        shutil.copy2(ini, ck / ini.name)
    out[name] = {"folder": str(dst), "umap_bytes": (dst / (name + ".umap")).stat().st_size,
                 "external_actor_files": sum(1 for _ in (dst / "__ExternalActors__").rglob("*.uasset")) if (dst / "__ExternalActors__").exists() else 0}
    out["ini"] = str(ck / ini.name)
    st["checkpoint"] = out; save_state(); P("checkpoint", json.dumps(out))


# ================================================================================================= textures
def textures():
    rows = MAN["textures"]; tasks = []
    for r in rows:
        if lib.does_asset_exist(f"{r['dest']}/{r['id']}"):
            continue
        t = unreal.AssetImportTask(); t.filename = str(SRC / r["file"]); t.destination_path = r["dest"]; t.destination_name = r["id"]
        t.automated = True; t.save = False; t.replace_existing = True; tasks.append(t)
    if tasks:
        tools.import_asset_tasks(tasks)
    out = {}
    for r in rows:
        path = f"{r['dest']}/{r['id']}"; tex = unreal.load_asset(path); assert tex, path
        k = r["kind"]
        tex.set_editor_property("srgb", k == "color")
        tex.set_editor_property("compression_settings", {"color": unreal.TextureCompressionSettings.TC_DEFAULT,
                                                         "normal_gl": unreal.TextureCompressionSettings.TC_NORMALMAP,
                                                         "masks": unreal.TextureCompressionSettings.TC_MASKS}[k])
        if k == "normal_gl":
            tex.set_editor_property("flip_green_channel", True)            # OpenGL sources; Unreal is DirectX
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP)
        else:
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        assert lib.save_loaded_asset(tex, only_if_is_dirty=False), path
        out[r["id"]] = {"path": path, "size": [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()], "srgb": tex.get_editor_property("srgb"),
                        "compression": str(tex.get_editor_property("compression_settings")), "kind": k}
    st["textures"] = out; save_state(); P("textures", len(out))


# ================================================================================================= materials
def new_material(path, blend, two_sided, translucent):
    name = path.split("/")[-1]; folder = path.rsplit("/", 1)[0]
    m = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    assert m, path
    mel.delete_all_material_expressions(m)
    m.set_editor_property("two_sided", two_sided)
    m.set_editor_property("blend_mode", blend)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    if translucent:
        try:
            m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)          # "Surface ForwardShading"
        except Exception as e:
            P("translucency lighting mode not set", e)
    for flag, v in (("used_with_instanced_static_meshes", True), ("used_with_nanite", not translucent), ("used_with_static_lighting", False)):
        try:
            m.set_editor_property(flag, v)
        except Exception:
            pass
    return m


def build_parent(path, translucent):
    """The EC01 surface graph (fix_ec01_assets.build_surface, itself rebuilt from the Blender graphs) plus: WoodUVScale on the
    second UV (Blender's Mapping node), UseVertexColor (FireBrick soot), and opacity (constant or the BaseColor alpha) to
    Opacity and Opacity Mask. Opaque parent: one-sided, instances override two-sided / masked; translucent parent: two-sided,
    surface forward shading."""
    M = new_material(path, unreal.BlendMode.BLEND_TRANSLUCENT if translucent else unreal.BlendMode.BLEND_OPAQUE, translucent, translucent)
    pos = [0]

    def E(cls, **props):
        pos[0] += 1
        e = mel.create_material_expression(M, cls, -1800 + (pos[0] % 7) * 250, -1300 + (pos[0] // 7) * 140)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def C(a, ao, b, bi):
        assert mel.connect_material_expressions(a, ao, b, bi), (a.get_name(), ao, b.get_name(), bi)

    def switch(name, default, t, f, out_t="", out_f=""):
        s = E(unreal.MaterialExpressionStaticSwitchParameter, parameter_name=name, default_value=default)
        C(t, out_t, s, "True"); C(f, out_f, s, "False"); return s

    def scalar(name, v):
        return E(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=v)

    def vector(name, v):
        return E(unreal.MaterialExpressionVectorParameter, parameter_name=name, default_value=unreal.LinearColor(*v))

    def texp(name, default, sampler, uv):
        t = E(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name=name, texture=unreal.load_asset(default), sampler_type=sampler)
        C(uv, "", t, "UVs"); return t

    def const3(v):
        return E(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(v[0], v[1], v[2], 1.0))

    def const(v):
        return E(unreal.MaterialExpressionConstant, r=v)

    def strength(normal_tex, sname, sdefault):
        l = E(unreal.MaterialExpressionLinearInterpolate); C(const3((0, 0, 1)), "", l, "A"); C(normal_tex, "RGB", l, "B")
        C(scalar(sname, sdefault), "", l, "Alpha")
        n = E(unreal.MaterialExpressionNormalize); C(l, "", n, "VectorInput"); return n

    def reorient(base, detail):
        ins = []
        for nm in ("B", "D"):
            ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
        c = E(unreal.MaterialExpressionCustom, code="float3 t = B + float3(0, 0, 1); float3 u = D * float3(-1, -1, 1); "
                                                   "return normalize(t * dot(t, u) / t.z - u);",
              output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3, description="ReorientedNormalBlend", inputs=ins)
        C(base, "", c, "B"); C(detail, "", c, "D"); return c

    def ao_factor(mask_tex, sname, sdefault):
        l = E(unreal.MaterialExpressionLinearInterpolate, const_a=1.0); C(mask_tex, "R", l, "B"); C(scalar(sname, sdefault), "", l, "Alpha")
        return l

    TXE = lambda n: f"{EC}/Textures/T_EC01_{n}"
    tc = [E(unreal.MaterialExpressionTextureCoordinate, coordinate_index=i) for i in range(3)]
    bake_uv = switch("UseUVT", True, tc[1], tc[0])
    wood0 = switch("UseUVT", True, tc[2], tc[1])
    wsc = vector("WoodUVScale", (1, 1, 0, 0))
    wmask = E(unreal.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False); C(wsc, "", wmask, "")
    wood_uv = E(unreal.MaterialExpressionMultiply); C(wood0, "", wood_uv, "A"); C(wmask, "", wood_uv, "B")
    main_uv = switch("MainOnWoodUV", False, wood_uv, bake_uv)
    COLOR, MASKS, NORMAL = (unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
                            unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tint = vector("BaseColorTint", (1, 1, 1, 1))
    bct = texp("BaseColor", TXE("Mahogany_BaseColor"), COLOR, main_uv)
    bcm = E(unreal.MaterialExpressionMultiply); C(bct, "RGB", bcm, "A"); C(tint, "", bcm, "B")
    bc = switch("UseBaseColorTexture", True, bcm, tint)
    orm = texp("ORM", TXE("Mahogany_ORM"), MASKS, main_uv)
    ao = switch("UseORM", True, ao_factor(orm, "AOToBaseColor", 0.5), const(1.0))
    rough = switch("RoughnessFromORM", True, orm, scalar("Roughness", 0.5), out_t="G")
    metal = switch("MetallicFromORM", False, orm, scalar("Metallic", 0.0), out_t="B")
    main_n = switch("UseNormalMap", True, strength(texp("Normal", TXE("Mahogany_NormalGL"), NORMAL, main_uv), "NormalStrength", 1.0),
                    const3((0, 0, 1)))
    trim_n = strength(texp("TrimNormal", TXE("Trim_NormalGL"), NORMAL, bake_uv), "TrimNormalStrength", 1.0)
    grain_n = strength(texp("GrainNormal", TXE("MahoganyGrainBump_NormalGL"), NORMAL, wood_uv), "GrainStrength", 0.25)
    n1 = switch("UseTrimLayer", False, reorient(trim_n, grain_n), main_n)
    trim_ao = switch("UseTrimLayer", False, ao_factor(texp("TrimORM", TXE("Trim_ORM"), MASKS, bake_uv), "TrimAOToBaseColor", 0.6), const(1.0))
    det = strength(texp("DetailNormal", TXE("Canvas_NormalGL"), NORMAL, wood_uv), "DetailNormalStrength", 0.35)
    nrm = switch("UseDetailNormal", False, reorient(n1, det), n1)
    vc = E(unreal.MaterialExpressionVertexColor)
    vcm = switch("UseVertexColor", False, vc, const3((1, 1, 1)), out_t="")
    m1 = E(unreal.MaterialExpressionMultiply); C(bc, "", m1, "A"); C(ao, "", m1, "B")
    m2 = E(unreal.MaterialExpressionMultiply); C(m1, "", m2, "A"); C(trim_ao, "", m2, "B")
    m3 = E(unreal.MaterialExpressionMultiply); C(m2, "", m3, "A"); C(vcm, "", m3, "B")
    op = scalar("Opacity", 1.0)
    opt = E(unreal.MaterialExpressionMultiply); C(bct, "A", opt, "A"); C(op, "", opt, "B")
    opacity = switch("UseOpacityFromTexture", False, opt, op)
    P_ = unreal.MaterialProperty
    for e, prop in ((m3, P_.MP_BASE_COLOR), (rough, P_.MP_ROUGHNESS), (metal, P_.MP_METALLIC), (nrm, P_.MP_NORMAL),
                    (opacity, P_.MP_OPACITY), (opacity, P_.MP_OPACITY_MASK)):
        assert mel.connect_material_property(e, "", prop), prop
    mel.layout_material_expressions(M); mel.recompile_material(M)
    assert lib.save_loaded_asset(M, only_if_is_dirty=False)
    return M


def TX(n):
    return f"{D}/Textures/{n}"


EC_MI = {"M_EC01_Mahogany": EC + "/Materials/MI_EC01_Mahogany", "M_EC01_MahoganyTrim": EC + "/Materials/MI_EC01_MahoganyTrim",
         "M_EC01_FiguredVeneer": EC + "/Materials/MI_EC01_FiguredVeneer", "M_EC01_HardwareBrass": EC + "/Materials/MI_EC01_HardwareBrass",
         "M_HE_FireplaceFlame": FLAME}


def WOOD(pre, scale, ns=1.0, extra=None):
    p = {"switches": {"MainOnWoodUV": True}, "textures": {"BaseColor": TX(pre + "_BaseColor"), "ORM": TX(pre + "_ORM"), "Normal": TX(pre + "_NormalGL")},
         "scalars": {"AOToBaseColor": 0.5, "NormalStrength": ns}, "vectors": {"WoodUVScale": [scale[0], scale[1], 0.0, 0.0]}}
    for k, v in (extra or {}).items():
        p.setdefault(k, {}).update(v)
    return p


def BAKED(pre, metal, uvt=False):
    return {"switches": {"UseUVT": uvt, "MetallicFromORM": metal}, "textures": {"BaseColor": TX(pre + "_BaseColor"), "ORM": TX(pre + "_ORM"),
                                                                              "Normal": TX(pre + "_NormalGL")},
            "scalars": {"AOToBaseColor": 0.5, "NormalStrength": 1.0}}


def PLAIN(rgb, r, metal=0.0, uvt=True):
    return {"switches": {"UseUVT": uvt, "UseBaseColorTexture": False, "UseORM": False, "RoughnessFromORM": False, "UseNormalMap": False},
            "vectors": {"BaseColorTint": list(rgb) + [1.0]}, "scalars": {"Roughness": r, "Metallic": metal}}


def DETAIL(bc, det, s, r):
    return {"switches": {"UseORM": False, "RoughnessFromORM": False, "UseNormalMap": False, "UseDetailNormal": True},
            "textures": {"BaseColor": bc, "DetailNormal": det}, "scalars": {"Roughness": r, "DetailNormalStrength": s}}


def DRAPE(fab, key, folds=None, sheer=False):
    """Blender: BaseColor = fabric(UV1) x mix(1, fold AO(UV0), 0.8); roughness = fabric ORM.G; normal = Bump(fabric weave
    normal's Blue, 0.6 mm, 0.35) over the baked fold normal (UV0) -> the trim layer: fold normal on UV0 reoriented with the
    baked weave bump on UV1 at 0.35; the fold AO into the colour at 0.8."""
    p = {"switches": {"MainOnWoodUV": True, "UseNormalMap": False, "UseTrimLayer": True},
         "textures": {"BaseColor": TX(fab + "_BaseColor"), "ORM": TX(fab + "_ORM"), "TrimNormal": TX(f"T_MO01_{folds or key}_NormalGL"),
                      "TrimORM": TX(f"T_MO01_{key}_AO"), "GrainNormal": TX(("T_MO01_SheerBump" if sheer else "T_MO01_VelvetBump") + "_NormalGL")},
         "scalars": {"AOToBaseColor": 0.0, "TrimAOToBaseColor": 0.8, "TrimNormalStrength": 1.0, "GrainStrength": 0.35}}
    if sheer:
        p["scalars"]["Opacity"] = 0.55
    return p


TWO = {"two_sided": True}
SPEC = {   # Blender material -> (instance name, parent "opaque"/"translucent", parameters, base-property overrides)
    "M_MO01_Wallpaper": ("MI_MO01_Wallpaper", "opaque", WOOD("T_MO01_Wallpaper", (2.65041, 2.33046)), {}),
    "M_MO01_Parquet": ("MI_MO01_Parquet", "opaque", WOOD("T_MO01_Parquet", (0.29412, 0.29412)), {}),
    "M_MO01_MarbleHearth": ("MI_MO01_MarbleHearth", "opaque", WOOD("T_MO01_Marble", (1.0, 1.0)), {}),
    "M_MO01_PelmetVelvet": ("MI_MO01_PelmetVelvet", "opaque", WOOD("T_MO01_Velvet", (3.52113, 3.52113)), {}),
    "M_MO01_FireBrick": ("MI_MO01_FireBrick", "opaque", WOOD("T_MO01_FireBrick", (0.55556, 0.55556), extra={"switches": {"UseVertexColor": True}}), {}),
    "M_MO01_PaintedPlaster": ("MI_MO01_PaintedPlaster", "opaque",
                              {"switches": {"UseBaseColorTexture": False, "UseORM": False, "RoughnessFromORM": False, "UseNormalMap": False, "UseTrimLayer": True},
                               "vectors": {"BaseColorTint": [0.74, 0.70, 0.62, 1.0]},
                               "textures": {"TrimNormal": f"{EC}/Textures/T_EC01_Trim_NormalGL", "TrimORM": f"{EC}/Textures/T_EC01_Trim_ORM"},
                               "scalars": {"Roughness": 0.55, "TrimAOToBaseColor": 0.35, "TrimNormalStrength": 1.0, "GrainStrength": 0.0}}, {}),
    "M_MO01_BreastPlaster": ("MI_MO01_BreastPlaster", "opaque", PLAIN((0.62, 0.58, 0.50), 0.85), {}),
    "M_MO01_Ceiling": ("MI_MO01_Ceiling", "opaque", PLAIN((0.76, 0.72, 0.64), 0.9), {}),
    "M_MO01_FireboxIron": ("MI_MO01_FireboxIron", "opaque", PLAIN((0.03, 0.028, 0.026), 0.7, metal=0.6), {}),
    "M_MO01_Rug": ("MI_MO01_Rug", "opaque", DETAIL(TX("T_MO01_Rug_BaseColor"), TX("T_MO01_RugPile_NormalGL"), 0.8, 0.95), {}),
    "M_MO01_Portraits": ("MI_MO01_Portraits", "opaque", DETAIL(TX("T_MO01_Portraits_BaseColor"), f"{EC}/Textures/T_EC01_Canvas_NormalGL", 0.35, 0.42), {}),
    "M_MO01_Books": ("MI_MO01_Books", "opaque", BAKED("T_MO01_Books", True), {}),
    "M_MO01_Candelabra": ("MI_MO01_Candelabra", "opaque", BAKED("T_MO01_Candelabra", True), {}),
    "M_MO01_Clock": ("MI_MO01_Clock", "opaque", BAKED("T_MO01_Clock", True), {}),
    "M_MO01_Mantel": ("MI_MO01_Mantel", "opaque", BAKED("T_MO01_Mantel", False), {}),
    "M_MO01_ClockDial": ("MI_MO01_ClockDial", "opaque", {"switches": {"UseUVT": False, "UseORM": False, "RoughnessFromORM": False, "UseNormalMap": False},
                                                         "textures": {"BaseColor": TX("T_MO01_ClockDial_BaseColor")}, "scalars": {"Roughness": 0.28}}, {}),
    "M_MO01_ClockGlass": ("MI_MO01_ClockGlass", "translucent", {**PLAIN((0.95, 0.95, 0.93), 0.04, uvt=False), "scalars": {"Roughness": 0.04, "Opacity": 0.12}},
                          {"two_sided": False}),
    "M_MO01_DrapeSide_L": ("MI_MO01_DrapeSide_L", "opaque", DRAPE("T_MO01_Velvet", "DrapeSide_L"), TWO),
    "M_MO01_DrapeSide_R": ("MI_MO01_DrapeSide_R", "opaque", DRAPE("T_MO01_Velvet", "DrapeSide_R"), TWO),
    "M_MO01_Swag_N": ("MI_MO01_Swag_N", "opaque", DRAPE("T_MO01_Velvet", "Swag_N"), TWO),
    "M_MO01_Swag_E": ("MI_MO01_Swag_E", "opaque", DRAPE("T_MO01_Velvet", "Swag_E"), TWO),
    "M_MO01_Tail_N": ("MI_MO01_Tail_N", "opaque", DRAPE("T_MO01_Velvet", "Tail_N"), TWO),
    "M_MO01_Tail_E": ("MI_MO01_Tail_E", "opaque", DRAPE("T_MO01_Velvet", "Tail_E"), TWO),
    "M_MO01_Sheer": ("MI_MO01_Sheer", "translucent", DRAPE("T_MO01_Sheer", "Sheer", folds="SheerFolds", sheer=True), {}),
    "M_MO01_Fringe": ("MI_MO01_Fringe", "opaque",
                      {"switches": {"UseORM": False, "RoughnessFromORM": False, "MetallicFromORM": False, "UseOpacityFromTexture": True},
                       "textures": {"BaseColor": TX("T_MO01_Fringe_BaseColorAlpha"), "Normal": TX("T_MO01_Fringe_NormalGL")},
                       "scalars": {"Roughness": 0.45, "Metallic": 0.7, "NormalStrength": 1.0, "Opacity": 1.0}},
                      {"two_sided": True, "blend": "masked", "clip": 0.5}),
    # FUR-024 P03 (the lobby palm) and the approved G01 grate: hotel-wide assets in their own folders
    "M_HE_Palm_P03 | pinnate leaflets": ("MI_HE_Palm_P03_Leaflets", "opaque",
                                         {"switches": {"UseUVT": False}, "textures": {"BaseColor": f"{HE}/P03/Textures/T_HE_Palm_P03_Leaf_BaseColor",
                                                                                      "ORM": f"{HE}/P03/Textures/T_HE_Palm_P03_Leaf_ORM",
                                                                                      "Normal": f"{HE}/P03/Textures/T_HE_Palm_P03_Leaf_NormalGL"},
                                          "scalars": {"AOToBaseColor": 0.0, "NormalStrength": 1.0}}, TWO),
    "M_HE_Palm_P03 | matte aged ivory ceramic": ("MI_HE_Palm_P03_Planter", "opaque",
                                                 {"switches": {"UseUVT": False}, "textures": {"BaseColor": f"{HE}/P03/Textures/T_HE_Palm_P03_Pot_BaseColor",
                                                                                              "ORM": f"{HE}/P03/Textures/T_HE_Palm_P03_Pot_ORM",
                                                                                              "Normal": f"{HE}/P03/Textures/T_HE_Palm_P03_Pot_BakedNormalGL"},
                                                  "scalars": {"AOToBaseColor": 0.0, "NormalStrength": 1.0}}, {}),
    "M_HE_Palm_P03 | slender olive green cane": ("MI_HE_Palm_P03_Cane", "opaque", PLAIN((0.075, 0.14, 0.05), 0.83, uvt=False), {}),
    "M_HE_Palm_P03 | soil": ("MI_HE_Palm_P03_Soil", "opaque", PLAIN((0.065, 0.05, 0.032), 0.93, uvt=False), {}),
    "M_HE_Palm_P03 | tapered frond rachis": ("MI_HE_Palm_P03_Rachis", "opaque", PLAIN((0.07, 0.145, 0.05), 0.76, uvt=False), TWO),
    "M_HE_Grate_G01_BAKED": ("MI_HE_Grate_G01", "opaque",
                                 {"switches": {"UseUVT": False, "MetallicFromORM": True}, "textures": {"BaseColor": f"{HE}/G01/Textures/T_HE_Grate_G01_BaseColor",
                                                                                                      "ORM": f"{HE}/G01/Textures/T_HE_Grate_G01_ORM",
                                                                                                      "Normal": f"{HE}/G01/Textures/T_HE_Grate_G01_Normal_GL"},
                                  "scalars": {"AOToBaseColor": 0.0, "NormalStrength": 1.0}}, {}),
}


def mi_folder(bname):
    return f"{HE}/P03/Materials" if "Palm_P03" in bname else (f"{HE}/G01/Materials" if "Grate_G01" in bname else DMI)


def materials():
    parents = {"opaque": build_parent(DMI + "/M_MO01_Surface", False), "translucent": build_parent(DMI + "/M_MO01_Translucent", True)}
    out = {}
    needed = {bkey(n) for n in MAN["materials"]}
    missing = sorted(needed - set(SPEC) - set(EC_MI))
    assert not missing, ("no instance spec for", missing)
    for bname, (miname, parent, p, ov) in SPEC.items():
        folder = mi_folder(bname); path = f"{folder}/{miname}"
        mi = unreal.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(miname, folder, unreal.MaterialInstanceConstant,
                                                                                          unreal.MaterialInstanceConstantFactoryNew())
        assert mi, path
        mel.set_material_instance_parent(mi, parents[parent])
        mel.clear_all_material_instance_parameters(mi)
        for k, v in p.get("switches", {}).items():
            mel.set_material_instance_static_switch_parameter_value(mi, k, bool(v))
        for k, v in p.get("scalars", {}).items():          # setters return False on this build even when they apply: read back
            mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
            assert abs(mel.get_material_instance_scalar_parameter_value(mi, k) - float(v)) < 1e-5, (miname, k)
        for k, v in p.get("vectors", {}).items():
            mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v))
            g = mel.get_material_instance_vector_parameter_value(mi, k); assert abs(g.r - v[0]) + abs(g.g - v[1]) + abs(g.b - v[2]) < 1e-4, (miname, k)
        for k, v in p.get("textures", {}).items():
            t = unreal.load_asset(v); assert t, (miname, v)
            mel.set_material_instance_texture_parameter_value(mi, k, t)
            assert mel.get_material_instance_texture_parameter_value(mi, k) == t, (miname, k)
        o = mi.get_editor_property("base_property_overrides")
        if "two_sided" in ov:
            o.set_editor_property("override_two_sided", True); o.set_editor_property("two_sided", bool(ov["two_sided"]))
        if ov.get("blend") == "masked":
            o.set_editor_property("override_blend_mode", True); o.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
            o.set_editor_property("override_opacity_mask_clip_value", True); o.set_editor_property("opacity_mask_clip_value", float(ov.get("clip", 0.5)))
        mi.set_editor_property("base_property_overrides", o)
        mel.update_material_instance(mi); assert lib.save_loaded_asset(mi, only_if_is_dirty=False), path
        got = {k: mel.get_material_instance_static_switch_parameter_value(mi, k) for k in p.get("switches", {})}
        assert all(got[k] == bool(v) for k, v in p.get("switches", {}).items()), (miname, got)
        ob = mi.get_editor_property("base_property_overrides")
        out[bname] = {"path": path, "parent": parents[parent].get_path_name(), **p, "overrides": ov,
                      "read": {"two_sided": ob.get_editor_property("two_sided") if ob.get_editor_property("override_two_sided") else None,
                               "blend": str(ob.get_editor_property("blend_mode")) if ob.get_editor_property("override_blend_mode") else None}}
    for bname, path in EC_MI.items():
        assert unreal.load_asset(path), path
        out[bname] = {"path": path, "reused": True}
    st["materials"] = {"parents": {k: v.get_path_name() for k, v in parents.items()}, "instances": out}; save_state()
    P("materials", len(out), "on", [v.get_name() for v in parents.values()])


def mat_for(bname):
    return unreal.load_asset(st["materials"]["instances"][bkey(bname)]["path"])


# ================================================================================================= meshes
def translucent_slots(r):
    return [s for s in r["slots"] if bkey(s) in SPEC and SPEC[bkey(s)][1] == "translucent"]


def meshes():
    unreal.SystemLibrary.execute_console_command(world(), "Interchange.FeatureFlags.Import.FBX 0")
    out = {}
    try:
        tasks = []
        for ident, r in MAN["resources"].items():
            t = unreal.AssetImportTask(); t.filename = str(SRC / r["file"]); t.destination_path = r["dest"]; t.destination_name = ident
            t.automated = True; t.save = False; t.replace_existing = True
            o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
            o.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH; d = o.static_mesh_import_data
            d.combine_meshes = True; d.auto_generate_collision = False; d.one_convex_hull_per_ucx = True; d.build_nanite = False
            d.convert_scene = True; d.convert_scene_unit = True; d.force_front_x_axis = False; d.generate_lightmap_u_vs = False
            d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
            d.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE if r["vertex_colors"] else unreal.VertexColorImportOption.IGNORE
            t.options = o; tasks.append(t)
        tools.import_asset_tasks(tasks)
    finally:
        unreal.SystemLibrary.execute_console_command(world(), "Interchange.FeatureFlags.Import.FBX 1")
    norm = lambda x: "".join(ch if ch.isalnum() else "_" for ch in x)
    for ident, r in MAN["resources"].items():
        path = f"{r['dest']}/{ident}"; mesh = unreal.load_asset(path); assert mesh, path
        slots = [str(s.material_slot_name) for s in mesh.static_materials]
        mapping = []
        for i, sname in enumerate(slots):
            j = next((k for k, n in enumerate(r["slots"]) if n == sname), None)
            if j is None:
                j = next((k for k, n in enumerate(r["slots"]) if norm(n) == norm(sname)), None)
            if j is None:
                j = next((k for k, n in enumerate(r["slots"]) if norm(sname).startswith(norm(n)[:20]) and k not in mapping), i)
            mapping.append(j); mesh.set_material(i, mat_for(r["slots"][j]))
        used = [k for k, n in enumerate(r["slot_triangles"]) if n > 0]          # the FBX drops slots no face uses
        assert sorted(mapping) == used, (ident, slots, r["slots"], r["slot_triangles"])
        body = mesh.get_editor_property("body_setup")
        ucx = len(body.get_editor_property("agg_geom").get_editor_property("convex_elems")) if body else 0
        assert ucx == r["ucx"], (ident, "UCX", ucx, r["ucx"])
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)   # boxes only, or none
        b = smes.get_lod_build_settings(mesh, 0); b.use_full_precision_u_vs = True; b.recompute_normals = False; b.recompute_tangents = False
        smes.set_lod_build_settings(mesh, 0, b)
        ns = mesh.get_editor_property("nanite_settings")
        ns.enabled = r["triangles"] >= 200 and not translucent_slots(r) and r["kind"] != "fire"
        ns.explicit_tangents = ns.enabled
        ns.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
        ns.fallback_percent_triangles = 1.0 if r["kind"] in ("collider_part",) else 0.25
        smes.set_nanite_settings(mesh, ns, True)
        assert lib.save_loaded_asset(mesh, only_if_is_dirty=False), path
        bb = mesh.get_bounding_box(); e = r["bounds_cm_ue"]
        actual = [[bb.min.x, bb.min.y, bb.min.z], [bb.max.x, bb.max.y, bb.max.z]]
        err = max(abs(actual[i][j] - e[i][j]) for i in range(2) for j in range(3))
        tris = mesh.get_static_mesh_description(0).get_triangle_count()
        out[ident] = {"path": path, "slots": slots, "slot_map": mapping, "bounds_err_cm": err, "triangles": tris, "source_triangles": r["triangles"],
                      "ucx": ucx, "nanite": ns.enabled, "uv_channels": smes.get_num_uv_channels(mesh, 0), "translucent": translucent_slots(r)}
        assert err < 1.0, (ident, "bounds", actual, e)
        assert r["triangles"] - r.get("degenerate_triangles", 0) - 2 <= tris <= r["triangles"] + 2, (ident, tris, r["triangles"])
        assert out[ident]["uv_channels"] == len(r["uv_layers"]), (ident, out[ident]["uv_channels"], r["uv_layers"])
    st["meshes"] = out; save_state(); P("meshes", len(out), "nanite", sum(1 for v in out.values() if v["nanite"]))


# ================================================================================================= fixtures (tags, profile)
def fixtures():
    r = {}
    unreal.GameplayTagService.add_tags([ZONE], "Hotel Eden Level 3: Meredith's office (MO01, 12 Nov 2026), off the executive corridor.")
    unreal.GameplayTagService.add_tags([GROUP], "The light fixtures of Meredith's office (MO01), addressable together.")
    r["tags"] = {t: unreal.GameplayTagService.has_tag(t) for t in (ZONE, GROUP) + tuple(set(ROLES.values()))}
    assert all(r["tags"].values()), r["tags"]
    # moody window light: the catalog WindowFill is 3,000 lm of 5,500 K per window; the office takes 500 lm of cool 6,200 K
    # lake light through each sheer (its source the size of the glass), so the fire, sconces and picture light carry the room
    if not lib.does_asset_exist(MO_WINDOWFILL):
        assert lib.duplicate_asset(PROFILES + "/DA_LightProfile_WindowFill", MO_WINDOWFILL)
    p = unreal.load_asset(MO_WINDOWFILL)
    for k, v in (("IntensityLumens", 500.0), ("TemperatureK", 6200.0), ("SourceWidthCm", 170.0), ("SourceHeightCm", 240.0), ("AttenuationRadiusCm", 700.0)):
        p.set_editor_property(k, v)
    # shadowless, as the lobby's fill profiles: the rect sits just under the ceiling inside the reveal, and its ray-traced
    # shadows grazing the ceiling read as dark speckle (measured in Play: gone with the fills off, not Lumen or MegaLights)
    p.set_editor_property("bCastShadows", False); p.set_editor_property("ShadowMethod", unreal.WhispersLightShadowMethod.NONE)
    assert lib.save_loaded_asset(p, only_if_is_dirty=False)
    r["window_fill_profile"] = {k: str(p.get_editor_property(k)) for k in ("FixtureType", "IntensityLumens", "TemperatureK", "SourceWidthCm",
                                                                          "SourceHeightCm", "AttenuationRadiusCm", "ShadowMethod", "bCastShadows",
                                                                          "bAllowMegaLights")}
    st["fixtures"] = r; save_state(); P("fixtures", json.dumps(r))


# ================================================================================================= place
def component(a, cls, name, parent_h):
    h, reason = ds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent_h, new_class=cls)); assert not str(reason), str(reason)
    ds.rename_subobject(h, unreal.Text(name)); return fl.get_associated_object(fl.get_data(h))


def mesh_path(res):
    if res in MAN["reuse"]:
        return MAN["reuse"][res]["path"]
    return st["meshes"][res]["path"]


def place_actor(rec):
    assert by_label(ACTOR) is None, "MO01 actor already present; inspect before re-placing"
    a = es.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0)); a.set_actor_label(ACTOR)
    a.tags = [unreal.Name(TAG)]; a.set_folder_path(unreal.Name(FOLDER))
    hs = ds.k2_gather_subobject_data_for_instance(a)
    root_h, reason = ds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=unreal.SceneComponent)); assert not str(reason)
    ds.rename_subobject(root_h, unreal.Text("Scene"))
    fl.get_associated_object(fl.get_data(root_h)).set_mobility(unreal.ComponentMobility.STATIC)
    groups = collections.defaultdict(list)
    for p in MAN["placements"]:
        groups[p["resource"]].append(p)
    comps = {}
    for res, rows in sorted(groups.items()):
        ucx = MAN["resources"][res]["ucx"] if res in MAN["resources"] else 0
        kind = MAN["resources"][res]["kind"] if res in MAN["resources"] else "reuse"
        name = res.replace("SM_MO01_", "").replace("SM_HE_", "").replace("SM_EC01_", "").replace("-", "_")
        c = component(a, unreal.InstancedStaticMeshComponent, name, root_h); c.set_mobility(unreal.ComponentMobility.STATIC)
        c.set_static_mesh(unreal.load_asset(mesh_path(res)))
        if ucx > 0:
            c.set_collision_profile_name("BlockAll"); c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        else:
            c.set_collision_profile_name("NoCollision"); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if kind == "fire":
            c.set_editor_property("cast_shadow", False)
        ids = c.add_instances([T(p) for p in rows], True, True, False); assert len(ids) == len(rows), (res, len(ids))
        comps[name] = {"resource": res, "instances": len(rows), "collision": "block (UCX boxes)" if ucx else "none"}
    rec["actor"] = {"label": ACTOR, "components": comps, "instances": sum(v["instances"] for v in comps.values())}


def wl_of(a):
    return next(c for c in a.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "WhispersLightComponent")


def set_identity(a, lid, zone, role, group, profile=None):
    """One field per write, re-finding the component each time (#237: a write re-runs construction and replaces it)."""
    fields = [("LightId", unreal.Name(lid)), ("ZoneTag", tag(zone)), ("RoleTag", tag(role)), ("GroupTags", tags(group))]
    if profile:
        fields.insert(0, ("Profile", unreal.load_asset(profile)))
    for name, value in fields:
        w = wl_of(a); w.modify(); w.set_editor_property(name, value)
    w = wl_of(a)
    got = {"id": str(w.get_editor_property("LightId")), "zone": tag_name(w.get_editor_property("ZoneTag")), "role": tag_name(w.get_editor_property("RoleTag")),
           "groups": w.get_editor_property("GroupTags").export_text(), "profile": w.get_editor_property("Profile").get_name() if w.get_editor_property("Profile") else None}
    assert got["id"] == lid and got["zone"] == zone and got["role"] == role and group in got["groups"], (a.get_actor_label(), got)
    if profile:
        assert got["profile"] == profile.split("/")[-1], got
    return got


def light_comp(a):
    return a.get_components_by_class(unreal.LightComponent)[0]


def place_lights(rec):
    rows = []
    # the two EC01 S06 sconces (their prefab carries the light at the flame + 4.5 cm and the EC01 profile)
    cls = unreal.load_asset(FIXTURES["WallSconce"]).generated_class()
    for p in MAN["sconces"]:
        idt = p["identity"]; lid = idt["mo01_LightId"]; label = f"WallSconce_MeredithOffice_{lid[-2:]}"
        assert by_label(label) is None, label
        t = T(p); a = es.spawn_actor_from_class(cls, t.translation, t.rotation.rotator()); assert a, label
        a.set_actor_scale3d(t.scale3d); a.set_actor_label(label); a.set_folder_path(unreal.Name(LIGHT_FOLDER)); a.tags = [unreal.Name(TAG)]
        got = set_identity(a, lid, ZONE, ROLES["WallSconce"], GROUP)
        lc = light_comp(a); e = (lc.get_world_location() - unreal.Vector(*p["light_world"]["translation_cm"])).length()
        assert e < 0.5, (label, e)
        rows.append({"label": label, **got, "light_err_cm": e, "class": "BP_EC01_WallSconce_S06"})
    # catalog fixtures at the master's light positions; spot / rect turned so their light axis (+X) is the Blender light's -Z
    for L in MAN["lights"]:
        idt = L["identity"]; fx = idt["mo01_Fixture"]; lid = idt["mo01_LightId"]
        label = f"{fx}_MeredithOffice_{lid[-2:]}"
        assert by_label(label) is None, label
        cls = unreal.load_asset(FIXTURES[fx]).generated_class()
        loc = unreal.Vector(*L["location_ue"])
        a = es.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0)); assert a, label
        a.set_actor_label(label); a.set_folder_path(unreal.Name(LIGHT_FOLDER)); a.tags = [unreal.Name(TAG)]
        if "rotation" in L:
            want = unreal.Transform(unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=L["rotation"]["pitch"], yaw=L["rotation"]["yaw"]))
            rel = light_comp(a).get_relative_transform(); rel = unreal.Transform(unreal.Vector(0, 0, 0), rel.rotation.rotator())
            # world = rel * actor (Unreal applies the left transform first) -> actor = rel^-1 * want
            act = unreal.MathLibrary.compose_transforms(unreal.MathLibrary.invert_transform(rel), want)
            a.set_actor_rotation(act.rotation.rotator(), False)
        got = set_identity(a, lid, ZONE, ROLES[fx], GROUP, MO_WINDOWFILL if fx == "WindowFill" else None)
        lc = light_comp(a)
        fwd = lc.get_forward_vector()
        row = {"label": label, **got, "class": a.get_class().get_name(), "light_world_cm": [round(lc.get_world_location().x, 1), round(lc.get_world_location().y, 1),
                                                                                           round(lc.get_world_location().z, 1)],
               "forward": [round(fwd.x, 3), round(fwd.y, 3), round(fwd.z, 3)]}
        if "rotation" in L:
            d = L["rotation"]["dir_ue"]
            row["dir_err"] = round(math.degrees(math.acos(max(-1, min(1, fwd.x * d[0] + fwd.y * d[1] + fwd.z * d[2])))), 3)
            assert row["dir_err"] < 0.5, row
        rows.append(row)
    rec["lights"] = rows


def place_fire(rec):
    """The lobby fireplace's crackle (S_HE_FireplaceCrackle_Loop through SA_HE_Fireplace, volume 0.6) at the office grate."""
    label = "MO01_Fireplace_Crackle"; assert by_label(label) is None, label
    a = es.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(*MAN["fire"]["sound_ue"])); a.set_actor_label(label)
    a.set_folder_path(unreal.Name(FOLDER)); a.tags = [unreal.Name(TAG)]
    ac = a.get_component_by_class(unreal.AudioComponent)
    ac.set_editor_property("sound", unreal.load_asset(HE + "/Fireplace/S_HE_FireplaceCrackle_Loop"))
    ac.set_editor_property("attenuation_settings", unreal.load_asset(HE + "/Fireplace/SA_HE_Fireplace"))
    ac.set_editor_property("volume_multiplier", 0.6)
    rec["fire"] = {"crackle": label, "cards": "MO01_MeredithOffice/FireCards (M_HE_FireplaceFlame)", "sound_cm": MAN["fire"]["sound_ue"]}


# light zone: the office as its own zone (as the LM01 lit rooms and EC01), replacing LM01's generic room lamp and box here
ZBOX = (1710, 2570, 30, 670, 905, 1315)              # the room's interior, LM01's Level 3 room band
LM01_RETIRE = ("LM01_RoomLamp_Level3Rooms_Lamp_04", "LM01_Zone_Level3Rooms_Lamp_04")


def actor_record(a):
    r = {"label": a.get_actor_label(), "class": a.get_class().get_path_name(), "folder": str(a.get_folder_path()), **TJ(a.get_actor_transform())}
    for c in a.get_components_by_class(unreal.ActorComponent):
        cn = c.get_class().get_name()
        if cn == "WhispersLightComponent":
            r["light"] = {k: (c.get_editor_property(k).export_text() if hasattr(c.get_editor_property(k), "export_text") else
                              (c.get_editor_property(k).get_path_name() if hasattr(c.get_editor_property(k), "get_path_name") else str(c.get_editor_property(k))))
                          for k in ("LightId", "ZoneTag", "RoleTag", "GroupTags", "Profile")}
        if isinstance(c, unreal.LightComponent):
            r.setdefault("light_components", []).append({"name": c.get_name(), "class": cn, **TJ(c.get_relative_transform()),
                                                         "intensity": c.get_editor_property("intensity")})
    if a.get_class().get_name() == "WhispersLightZoneVolume":
        e = a.get_editor_property("BoxExtent")
        r["zone"] = {"tag": tag_name(a.get_editor_property("ZoneTag")), "extent": [e.x, e.y, e.z], "never_dormant": a.get_editor_property("bNeverDormant")}
    return r


def place_zone(rec):
    retired = []
    for label in LM01_RETIRE:
        a = by_label(label); assert a, label
        retired.append(actor_record(a))
    rec["retired_lm01"] = retired; save_state()                # restore records first
    for label in LM01_RETIRE:
        assert es.destroy_actor(by_label(label)), label
    vcls = unreal.load_class(None, "/Script/WhispersLighting.WhispersLightZoneVolume")
    pcls = unreal.load_class(None, "/Script/WhispersLighting.WhispersLightPortalActor")
    x0, x1, y0, y1, z0, z1 = ZBOX
    name = "MO01_Zone_MeredithOffice"; assert by_label(name) is None, name
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); e = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
    v = es.spawn_actor_from_class(vcls, unreal.Vector(*c), unreal.Rotator(0, 0, 0)); v.set_actor_label(name)
    v.set_editor_property("BoxExtent", unreal.Vector(*e)); v.set_editor_property("ZoneTag", tag(ZONE))
    v.set_editor_property("bNeverDormant", False); v.call_method("EnsureZoneGeometry"); v.set_folder_path(unreal.Name(ZONE_FOLDER))
    vol = {"label": name, "center": c, "extent": e, "zone": tag_name(v.get_editor_property("ZoneTag"))}
    pors = []
    # the lake windows: lit from outside, as LM01's lit rooms (sightline only)
    pname = "MO01_Portal_Office_Exterior"; assert by_label(pname) is None, pname
    pa = es.spawn_actor_from_class(pcls, unreal.Vector(2310, 30, 1120), unreal.Rotator(0, 0, 0)); pa.set_actor_label(pname)
    po = pa.get_editor_property("Portal")
    po.set_editor_property("ZoneA", tag(ZONE)); po.set_editor_property("ZoneB", tag("Light.Zone.Eden.Exterior"))
    po.set_editor_property("bSightlineOnly", True); po.set_editor_property("bOpen", True); pa.set_folder_path(unreal.Name(ZONE_FOLDER))
    pors.append({"label": pname, "a": ZONE, "b": "Light.Zone.Eden.Exterior", "pos": [2310, 30, 1120]})
    # the office door: EC01's portal pointed at LM01's Level3Rooms; it now names the office's own zone
    old = by_label("EC01_Portal_Office_Level3Rooms"); assert old, "EC01 office-door portal missing"
    po = old.get_editor_property("Portal"); before = tag_name(po.get_editor_property("ZoneB"))
    old.modify(); po.set_editor_property("ZoneB", tag(ZONE)); old.set_actor_label("EC01_Portal_Office_MeredithOffice")
    pors.append({"label": "EC01_Portal_Office_MeredithOffice", "was": {"label": "EC01_Portal_Office_Level3Rooms", "b": before},
                 "a": tag_name(po.get_editor_property("ZoneA")), "b": tag_name(po.get_editor_property("ZoneB"))})
    rec["zone"] = {"volume": vol, "portals": pors}


def settle():
    a = by_label(ACTOR); a.modify(); cs = a.get_components_by_class(unreal.SceneComponent)
    scene = next(c for c in cs if c.get_name() == "Scene")
    for c in sorted(cs, key=lambda c: 0 if c == a.root_component else (1 if c == scene else 2)):
        c.modify(); c.set_mobility(unreal.ComponentMobility.STATIC)
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        if c.get_attach_parent() != scene:
            c.attach_to_component(scene, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)


def place():
    w = world(); assert w.get_name() == "L_HotelEden_Building", w.get_name()
    d0 = dirty(); assert not d0, ("unrelated unsaved packages; stop", d0)
    rec = st.setdefault("place", {})
    assert not rec.get("saved"), "already installed; inspect before re-running"
    place_actor(rec); save_state()
    place_lights(rec); save_state()
    place_fire(rec); save_state()
    place_zone(rec); save_state()
    settle()
    assert unreal.EditorLoadingAndSavingUtils.save_current_level()
    rec["saved"] = True; rec["dirty_after_save"] = dirty(); save_state()
    P("placed", json.dumps({"components": len(rec["actor"]["components"]), "instances": rec["actor"]["instances"], "lights": len(rec["lights"]),
                            "zone": rec["zone"]["volume"]["label"], "retired": [r["label"] for r in rec["retired_lm01"]],
                            "dirty_after_save": rec["dirty_after_save"]}))


# ================================================================================================= verify
def verify(through=None):
    H = through or unreal.Transform()
    out = {"world": world().get_name()}
    A = {a.get_actor_label(): a for a in acts()}
    a = A.get(ACTOR); assert a, "MO01 actor missing"
    comps = {c.get_name(): c for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent)}
    groups = collections.defaultdict(list)
    for p in MAN["placements"]:
        groups[p["resource"]].append(p)
    worst = 0.0; n = 0
    for res, rows in groups.items():
        name = res.replace("SM_MO01_", "").replace("SM_HE_", "").replace("SM_EC01_", "").replace("-", "_")
        c = comps[name]; assert c.get_instance_count() == len(rows), (name, c.get_instance_count(), len(rows))
        for i, p in enumerate(rows):
            want = H.transform_location(unreal.Vector(*p["translation_cm"]))
            got = c.get_instance_transform(i, True).translation
            worst = max(worst, (got - want).length()); n += 1
    out["placements"] = n; out["worst_placement_err_cm"] = round(worst, 3)
    assert worst < 0.5, worst
    L = []
    for lab, x in A.items():
        if lab.endswith(tuple(f"_MeredithOffice_{k:02d}" for k in range(1, 10))) and str(x.get_folder_path()) == LIGHT_FOLDER:
            w = wl_of(x)
            L.append({"label": lab, "id": str(w.get_editor_property("LightId")), "zone": tag_name(w.get_editor_property("ZoneTag")),
                      "role": tag_name(w.get_editor_property("RoleTag")), "profile": w.get_editor_property("Profile").get_name()})
    out["lights"] = sorted(L, key=lambda r: r["label"]); assert len(L) == 8 and all(r["zone"] == ZONE for r in L), L
    out["zone"] = {"volume": "MO01_Zone_MeredithOffice" in A, "portal_exterior": "MO01_Portal_Office_Exterior" in A,
                   "door_portal": "EC01_Portal_Office_MeredithOffice" in A, "lm01_retired": not any(l in A for l in LM01_RETIRE)}
    out["crackle"] = "MO01_Fireplace_Crackle" in A
    out["dirty"] = dirty()
    return out


# ================================================================================================= update (after a master rebuild)
def update():
    """Move every ISM instance that no longer matches the current export (12 Nov: the ceiling plane 10 mm and the paper 3 mm
    off the hotel shell, after the 1 mm ceiling z-fought the shell's timber in Unreal); meshes unchanged. Save."""
    w = world(); assert w.get_name() == "L_HotelEden_Building", w.get_name()
    d0 = dirty(); assert not d0, ("unrelated unsaved packages; stop", d0)
    a = by_label(ACTOR); assert a
    comps = {c.get_name(): c for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent)}
    groups = collections.defaultdict(list)
    for p in MAN["placements"]:
        groups[p["resource"]].append(p)
    moved = []
    for res, rows in groups.items():
        c = comps[res.replace("SM_MO01_", "").replace("SM_HE_", "").replace("SM_EC01_", "").replace("-", "_")]
        assert c.get_instance_count() == len(rows), (res, c.get_instance_count(), len(rows))
        for i, p in enumerate(rows):
            t = c.get_instance_transform(i, True); want = T(p)
            if (t.translation - want.translation).length() > 0.05:
                if not moved:
                    a.modify()
                c.modify(); assert c.update_instance_transform(i, want, True, True, True), (res, i)
                moved.append({"resource": res, "name": p["name"], "from_cm": [t.translation.x, t.translation.y, t.translation.z],
                              "to_cm": p["translation_cm"]})
    if moved:
        assert unreal.EditorLoadingAndSavingUtils.save_current_level()
    st.setdefault("updates", []).append({"moved": moved, "dirty_after_save": dirty()}); save_state()
    P("update", len(moved), "instances moved", json.dumps([m["resource"] for m in moved]))


# ================================================================================================= look (the office's post volume)
LOOK = {"lumen_final_gather_quality": 2.0, "auto_exposure_bias": -0.5, "local_exposure_shadow_contrast_scale": 0.9, "vignette_intensity": 0.45}


def look():
    """MO01_OfficeLook: a post volume over the office only (priority 3, above the hotel's HotelEden_InteriorLook at 2; 50 cm
    blend at the door). It overrides four things: Lumen final-gather quality 2 (the indirectly lit ceiling showed final-gather
    noise at 1), exposure bias -0.5 EV (the interior look's auto exposure, -10..20 EV, would lift the room out of its mood),
    slightly deeper local shadow contrast, and a little more vignette. Everything else stays the interior look's. Save."""
    w = world(); assert w.get_name() == "L_HotelEden_Building", w.get_name()
    d0 = dirty(); assert not d0, ("unrelated unsaved packages; stop", d0)
    label = "MO01_OfficeLook"; a = by_label(label)
    x0, x1, y0, y1, z0, z1 = ZBOX
    if a is None:
        a = es.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), unreal.Rotator(0, 0, 0))
        a.set_actor_label(label); a.set_folder_path(unreal.Name(FOLDER)); a.tags = [unreal.Name(TAG)]
    a.modify()
    b = a.get_actor_bounds(False)[1]                                   # the default brush's half size
    a.set_actor_scale3d(unreal.Vector((x1 - x0) / 2 / b.x * a.get_actor_scale3d().x, (y1 - y0) / 2 / b.y * a.get_actor_scale3d().y,
                                      (z1 - z0) / 2 / b.z * a.get_actor_scale3d().z))
    a.set_editor_property("unbound", False); a.set_editor_property("priority", 3.0); a.set_editor_property("blend_radius", 50.0)
    a.set_editor_property("blend_weight", 1.0)
    s_ = a.get_editor_property("settings")
    for k, v in LOOK.items():
        s_.set_editor_property("override_" + k, True); s_.set_editor_property(k, v)
    a.set_editor_property("settings", s_)
    assert unreal.EditorLoadingAndSavingUtils.save_current_level()
    o, e = a.get_actor_bounds(False)
    got = {k: a.get_editor_property("settings").get_editor_property(k) for k in LOOK}
    st["look"] = {"label": label, "priority": 3.0, "blend_radius": 50.0, "settings": got, "bounds_cm": [[o.x - e.x, o.y - e.y, o.z - e.z], [o.x + e.x, o.y + e.y, o.z + e.z]],
                  "dirty_after_save": dirty()}
    save_state(); P("look", json.dumps(st["look"]))


# ================================================================================================= dispatch
if STAGE == "checkpoint":
    checkpoint()
elif STAGE == "textures":
    textures()
elif STAGE == "materials":
    materials()
elif STAGE == "meshes":
    meshes()
elif STAGE == "fixtures":
    fixtures()
elif STAGE in ("open_building", "open_e2k"):
    d = dirty(); assert not d, ("unsaved packages; not switching maps", d)
    assert les.load_level(BUILDING if STAGE == "open_building" else E2K)
    P("opened", world().get_name(), "dirty", len(dirty()))
elif STAGE == "place":
    place()
elif STAGE == "update":
    update()
elif STAGE == "look":
    look()
elif STAGE == "verify":
    r = verify(); st["verify"] = r; save_state(); P("verify", json.dumps(r))
elif STAGE == "world":
    w = world(); assert w.get_name() == "L_EdenE2K", w.get_name()
    H = next(a for a in acts() if a.get_actor_label() == "HotelEden" and a.get_class().get_name() == "LevelInstance")
    r = verify(H.get_actor_transform()); r["instance"] = TJ(H.get_actor_transform()); st["world"] = r; save_state(); P("world", json.dumps(r))
else:
    raise SystemExit("unknown stage " + STAGE)
