"""Add the owner's three Meredith's office pieces to the approved furniture library (plain Python).

    python register_furniture.py

Owner, 12 Nov 2026: "D:\\Unreal Projects\\Whispers 5.8\\Saved\\Renders\\ there are blender files in there for the sofa, the
desk and the chair. Copy them over to where you keep all the other models and add them to the approved furniture list."
Writes approved-media/<slug>/Approval.json and README_Approved.md (from each package's Package_Info.json, written by
package_furniture.py) and the FUR-106/107/108 entries in furnishings/register.json (also listed in additional_requirement_ids).
Re-running replaces these three entries only.
"""
import json, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); CARD = os.path.abspath(os.path.join(HERE, "..", ".."))
EVIDENCE = ("D:\\Unreal Projects\\Whispers 5.8\\Saved\\Renders\\ there are blender files in there for the sofa, the desk and the chair. "
            "Copy them over to where you keep all the other models and add them to the approved furniture list.")
DATE = "2026-11-12"
PIECES = [
    dict(id="FUR-106", rev="CF01", slug="sofa-chesterfield-cf01", name="Meredith's office Chesterfield sofa", unreal="SofaChesterfield/SM_SofaChesterfield",
         dims=[1.945, 1.045, 0.760], brief="Chestnut leather Chesterfield, deep-buttoned back and rolled arms, baked from a 1.9M-triangle Tripo model "
         "to a 25k-triangle game mesh (4K colour and normal, 2K ORM).", previews=["sofa_chestnut_front.png", "sofa_chestnut_close.png", "low_front.png", "low_close.png"],
         texture="One 4K BaseColor and NormalGL, 2K ORM; player-close hero furniture."),
    dict(id="FUR-107", rev="PD01", slug="desk-pedestal-pd01", name="Meredith's office mahogany pedestal desk", unreal="DeskPedestal/SM_DeskPedestal",
         dims=[1.014, 1.919, 0.770], brief="Mahogany pedestal desk with a leather top: drawers and kneehole on the sitter's side, from the Tripo desk "
         "(16k triangles), 4K colour and 2K ORM (no normal map in the bake).", previews=["game_front.png", "game_sitter.png", "desk_mahogany_front.png", "desk_leather_top.png"],
         texture="4K BaseColor, 2K ORM; player-close hero furniture."),
    dict(id="FUR-108", rev="SW01", slug="chair-swivel-sw01", name="Meredith's office leather swivel desk chair", unreal="ChairSwivel/BP_SwivelChair",
         dims=[0.807, 0.800, 1.009], brief="Tufted leather swivel desk chair on a five-spoke base, baked from a 2M-triangle Tripo model: base (5k) and "
         "seat (21k) as two meshes, the seat 24.2 cm up (BP_SwivelChair). 4K colour and normal, 2K ORM.",
         previews=["low_front.png", "split_close.png", "split_swivel35.png"], texture="4K BaseColor and NormalGL, 2K ORM; player-close."),
]
UE = "/Game/Whispers/Presentation/Environment/HotelEden/Furniture/"

reg_p = os.path.join(HERE, "..", "register.json")
reg = json.load(open(reg_p, encoding="utf-8"))
seq = max(i.get("approval_sequence", 0) for i in reg["items"])
for P in PIECES:
    base = f"approved-media/{P['slug']}"
    info = json.load(open(os.path.join(CARD, base, "Package_Info.json"), encoding="utf-8"))
    tris = sum(o["triangles"] for o in info["objects"].values())
    approval = {"date": DATE, "revision": P["rev"], "assets": [P["id"]], "evidence": EVIDENCE,
                "scope": "The game assets as made and imported into Unreal on 12 Nov 2026 (the export FBX and maps in exports/, the same meshes as "
                         f"{UE}{P['unreal']}), their Tripo bake sources, and the Blender game file built from that FBX. Placement in Meredith's office is "
                         "recorded separately (MO01).",
                "files": [{"path": k, **v} for k, v in sorted(info["files"].items())]}
    json.dump(approval, open(os.path.join(CARD, base, "Approval.json"), "w", encoding="utf-8"), indent=2)
    readme = f"""# {P['id']} · {P['name']} · {P['rev']} (approved)

Owner, 12 November 2026: "{EVIDENCE}"

{P['brief']}

- **Game file:** `{P['rev']}_Game.blend`. The export FBX imported at metres, identity transform, base centre at the origin, on
  the export maps. Size {P['dims'][0]:.3f} × {P['dims'][1]:.3f} × {P['dims'][2]:.3f} m; {tris:,} triangles.
- **Unreal:** `{UE}{P['unreal']}`, imported from the same FBX (Nanite, one simple box collider, its MI on
  `M_HE_Master_PBR`).
- **Sources:** `{P['rev']}_Bake_Source.blend` (the high-to-low bake){"; `PD01_Tripo_Source.blend` (the Tripo source)" if P["rev"] == "PD01" else ""}.
- **Exports:** `exports/`, the FBX and maps as imported.
- **Previews:** `previews/`, the bake session's renders.
- **Working copy** of the full bake folder: `D:/AI_Modelling/hotel_eden/working/furnishings_MO01_furniture/`.
- **Textures:** {P['texture']}
- **Placed** in Meredith's office (MO01) in the MS02 master and in L_EdenE2K, after the reference.
"""
    open(os.path.join(CARD, base, "README_Approved.md"), "w", encoding="utf-8").write(readme)
    seq += 1
    entry = {"id": P["id"], "name": P["name"], "family": "Meredith's office furniture", "rooms": ["Meredith's Office"], "priority": 7,
             "status": "Approved", "revision": P["rev"], "approved_revision": P["rev"],
             "revisions": [{"revision": P["rev"], "status": "Approved", "source": f"{base}/{P['rev']}_Bake_Source.blend",
                            "previews": [f"{base}/previews/{x}" for x in P["previews"]], "guide": f"{base}/README_Approved.md",
                            "checks": f"{base}/Package_Info.json",
                            "notes": "Made by another session from a Tripo model and imported into Unreal (Furniture/Office_MO); copied into the library and approved by the owner.",
                            "approval": {"date": DATE, "evidence": EVIDENCE, "scope": approval["scope"]}}],
             "references": ["R15"], "brief": P["brief"], "proposed_optional": False, "dimensions_m": P["dims"], "quantity": 1,
             "placement_status": "Placed in Meredith's office (MO01): the MS02 master and L_EdenE2K, after the owner's reference.",
             "source": f"{base}/{P['rev']}_Bake_Source.blend", "previews": [f"{base}/previews/{x}" for x in P["previews"]],
             "next_action": "Use the approved game asset; in Unreal it is already imported and placed.",
             "texture_budget": {"viewing_role": "Player-close hero furniture", "starting_resolution": 4096, "status": P["texture"],
                                "rule": "Owner policy: 1K small/distant, 2K close-up, 4K detailed important with justification"},
             "production": {"revision": P["rev"], "model": f"{base}/{P['rev']}_Game.blend", "unreal": UE + P["unreal"], "triangles": tris,
                            "review": "meredith-office-mo01-review.html#furniture", "receipt": f"{base}/Approval.json"},
             "receipt": f"{base}/Approval.json", "approval_sequence": seq}
    reg["items"] = [i for i in reg["items"] if i["id"] != P["id"]] + [entry]
    if P["id"] not in reg.setdefault("additional_requirement_ids", []):
        reg["additional_requirement_ids"].append(P["id"])
    print("REGISTERED", P["id"], P["rev"], tris, "tris", len(approval["files"]), "files")
reg["updated"] = DATE
json.dump(reg, open(reg_p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(reg_p, "a", encoding="utf-8").write("\n")
