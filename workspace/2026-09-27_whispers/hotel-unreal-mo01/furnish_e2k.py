"""Meredith's office furniture in L_EdenE2K, placed as in the MS02 master (ue-mcp run_python_file; one stage per call).

    python ue_bridge.py run furnish_e2k.py plan | apply | verify

Owner, 12 Nov 2026: "Add them to Meredith's office Blender file and place them like in the reference image. Then check to see
that they are placed in the right spot in the Unreal file. Get rid of the textureless desk thing. The office needs to be
finished."
The pieces (FUR-106 sofa, FUR-107 desk, FUR-108 swivel chair) are E2K PersistentLevel actors placed by the session that made
them (folder Furniture/Office_MO). Their meshes are the approved game meshes MS02 now uses, so the master's placement
(mo01_spec.FURNITURE, in hotel-local cm) is applied through the HotelEden Level Instance:
  * desk at (2030, 400) on the rug, yaw 180: its drawer side faces the fire; the chair and Meredith's seven Life desk
    advertisements (Life_Manager_*_SL8) move with it as one rigid group, so their approach/use relations are unchanged
    (npc-life-temp-props.md: "the Smart Object definition and anchors move to the real furniture unchanged");
  * sofa at (2110, 122) on the parquet, yaw 0: back to the north wall under the portrait between the lake windows;
  * TMP_Life_Manager_Desk_SL8 and TMP_Life_Manager_ChairSeat_SL8 (the grey Life blocks) are deleted, with records.
Guards (docs/agents/ue-mcp-toolchain.md): the E2K forest is checked before the save; only the touched actor packages are
saved, and only if they are the only dirty ones. State: review-media/hotel-unreal-mo01/Furniture_E2K.json.
"""
import unreal, json, sys, os, importlib.util
# Superseded on 13 Nov 2026 by desk_chair_e2k.py (desk and chesterfield scaled, AWhispersSwivelDeskChair, the journal): this
# 12 Nov install would put the old layout back, and the spec no longer carries its chair keys. Kept as the record of that install.
raise SystemExit("furnish_e2k.py is superseded by desk_chair_e2k.py (13 Nov 2026)")
STAGE = sys.argv[1] if len(sys.argv) > 1 else "plan"
CARD = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
REC = CARD + "/review-media/hotel-unreal-mo01"
spec_ = importlib.util.spec_from_file_location("mo01_spec", CARD + "/furnishings/meredith_office_mo01/mo01_spec.py")
S = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(S)
SF = REC + "/Furniture_E2K.json"
st = json.load(open(SF)) if os.path.exists(SF) else {}
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); es = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K", W.get_name()
assert not ed.get_game_world(), "stop Play first"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"]))
Hinv = H.inverse()
TMP = ("TMP_Life_Manager_Desk_SL8", "TMP_Life_Manager_ChairSeat_SL8")


def acts():
    return {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor)}


def dirty():
    return sorted(p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())


def TJ(t):
    return {"t": [t.translation.x, t.translation.y, t.translation.z], "q": [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w],
            "s": [t.scale3d.x, t.scale3d.y, t.scale3d.z], "yaw": t.rotation.rotator().yaw}


def local(a):
    return unreal.MathLibrary.compose_transforms(a.get_actor_transform(), Hinv)


def T(cm, yaw, scale=(1, 1, 1)):
    return unreal.Transform(unreal.Vector(*cm), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), unreal.Vector(*scale))


def forest():
    """docs/agents/ue-mcp-toolchain.md: E2K_TestVegetation keeps its graph; no partition cell is TO_DELETE_ or at the origin."""
    A = list(unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor))
    vol = next((a for a in A if a.get_actor_label() == "E2K_TestVegetation"), None); g = None
    if vol:
        pcg = next((c for c in vol.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "PCGComponent"), None)
        gi = pcg.get_editor_property("graph_instance") if pcg else None
        g = gi.get_editor_property("graph").get_name() if gi and gi.get_editor_property("graph") else None
    cells = [a for a in A if a.get_class().get_name().startswith("PCGPartition")]
    r = {"graph": g, "cells": len(cells), "to_delete": sum(1 for a in cells if a.get_actor_label().startswith("TO_DELETE")),
         "at_origin": sum(1 for a in cells if a.get_actor_location().length() < 1.0)}
    r["ok"] = r["graph"] == "PCG_E2K_Vegetation" and r["cells"] == 64 and r["to_delete"] == 0 and r["at_origin"] == 0
    return r


def targets(A):
    """New hotel-local transforms: the desk group (desk, chair, Life desk advertisements) rigidly, the sofa on its own."""
    F = S.FURNITURE
    desk_old = local(A["Desk_Pedestal_MO"]); desk_new = T(F["desk"]["cm"], F["desk"]["yaw"])
    out = {"Desk_Pedestal_MO": desk_new}
    group = ["Chair_Swivel_MO"] + sorted(l for l in A if l.startswith("Life_Manager_") and l.endswith("_SL8"))
    assert len(group) == 8, group
    for l in group:
        rel = unreal.MathLibrary.compose_transforms(local(A[l]), unreal.MathLibrary.invert_transform(desk_old))
        out[l] = unreal.MathLibrary.compose_transforms(rel, desk_new)
    # the master's chair: 100 cm off the sitter side, yaw +90 to the desk; the Life advertisements: 100 cm, 89.6 cm up, yaw 180
    ch = unreal.MathLibrary.compose_transforms(T(F["chair"]["rel_desk_cm"], F["chair"]["rel_yaw"]), desk_new)
    assert (ch.translation - out["Chair_Swivel_MO"].translation).length() < 0.05, "the chair's relation differs from the master's"
    out["Sofa_Chesterfield_MO"] = T(F["sofa"]["cm"], F["sofa"]["yaw"])
    return out


if STAGE == "plan":
    A = acts(); out = targets(A)
    st["plan"] = {l: {"from_local": TJ(local(A[l])), "to_local": TJ(t)} for l, t in out.items()}
    st["plan_tmp"] = {l: (TJ(local(A[l])) if l in A else None) for l in TMP}
    st["forest_before"] = forest(); st["dirty_before"] = dirty()
    json.dump(st, open(SF, "w"), indent=1)
    print("PLAN", json.dumps({l: [round(v, 1) for v in r["to_local"]["t"]] + [round(r["to_local"]["yaw"], 1)] for l, r in st["plan"].items()}),
          "forest", st["forest_before"], "dirty", st["dirty_before"])

elif STAGE == "apply":
    assert not st.get("applied"), "already applied; inspect before re-running"
    d0 = dirty(); assert not d0, ("unrelated unsaved packages; stop", d0)
    f0 = forest(); assert f0["ok"], ("E2K forest check failed before editing; restart the editor", f0)
    A = acts(); out = targets(A)
    pkgs = {}
    moved = []
    for l, t in out.items():
        a = A[l]; a.modify()
        a.set_actor_transform(unreal.MathLibrary.compose_transforms(t, H), False, False)
        pkgs[a.get_package().get_name()] = a.get_package()
        moved.append(l)
    deleted = []
    for l in TMP:
        a = A.get(l)
        if a is None:
            continue
        rec = {"label": l, "package": a.get_package().get_name(), "world": TJ(a.get_actor_transform()), "local": TJ(local(a)),
               "mesh": a.static_mesh_component.static_mesh.get_path_name(), "scale": [a.get_actor_scale3d().x, a.get_actor_scale3d().y, a.get_actor_scale3d().z],
               "hidden_in_game": a.get_editor_property("hidden"), "collision": str(a.static_mesh_component.get_collision_profile_name())}
        pkgs[a.get_package().get_name()] = a.get_package()
        assert es.destroy_actor(a), l
        deleted.append(rec)
    st["deleted"] = deleted; json.dump(st, open(SF, "w"), indent=1)                 # restore records before saving
    d1 = dirty(); extra = sorted(set(d1) - set(pkgs))
    f1 = forest()
    assert f1["ok"] and not extra, ("not saving", f1, extra)
    assert unreal.EditorLoadingAndSavingUtils.save_packages(list(pkgs.values()), True)
    st.update(applied=True, moved=moved, saved_packages=sorted(pkgs), forest_at_save=f1, dirty_after=dirty())
    json.dump(st, open(SF, "w"), indent=1)
    print("APPLIED", len(moved), "moved;", [r["label"] for r in deleted], "deleted;", len(pkgs), "packages saved; dirty after", st["dirty_after"])

elif STAGE == "verify":
    A = acts(); res = {}
    for l, p in st["plan"].items():
        a = A[l]; t = local(a); w = p["to_local"]
        e = (t.translation - unreal.Vector(*w["t"])).length()
        dy = abs(((t.rotation.rotator().yaw - w["yaw"]) + 180) % 360 - 180)
        res[l] = {"err_cm": round(e, 3), "yaw_err": round(dy, 3), "local": [round(v, 1) for v in [t.translation.x, t.translation.y, t.translation.z]], "yaw": round(t.rotation.rotator().yaw, 2)}
        assert e < 0.1 and dy < 0.05, (l, res[l])
    gone = [l for l in TMP if l in A]
    files = {}
    content = unreal.Paths.project_content_dir()
    for r in st.get("deleted", []):
        f = content + r["package"].replace("/Game/", "") + ".uasset"
        files[r["label"]] = os.path.exists(f)
    st["verify"] = {"actors": res, "tmp_still_present": gone, "tmp_files_on_disk": files, "dirty": dirty(), "forest": forest()}
    json.dump(st, open(SF, "w"), indent=1)
    assert not gone and not any(files.values()), (gone, files)
    print("VERIFIED", json.dumps(st["verify"])[:2500])
else:
    raise SystemExit("unknown stage " + STAGE)
