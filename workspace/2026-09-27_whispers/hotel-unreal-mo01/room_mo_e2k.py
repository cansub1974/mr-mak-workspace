"""Make room.eden.mo cover the whole of Meredith's office, so her new desk and chair are in her office (ue-mcp; one stage per call).

    python ue_bridge.py run room_mo_e2k.py plan | apply | register | verify      (Play stopped)

Owner, 12 Nov 2026: "yes I do want Meredith to sit and use the new desk and chair".
Measured in Play (probe_rooms.py): the room volume Room_MO_Office_166 (#166) covers only the east third of the office (hotel-local
x 2209-2581), where the grey TMP desk stood. The desk group now stands after the owner's reference in front of the fire (x 1930-2080),
where the registry resolves the overlapping generic room.eden.level3rooms_lamp_04; Life then treats Meredith's own desk as another
room with no route and offers it nothing (staged in the office she sat once, then had zero candidates). Fix, as #197 / #215 did:
  apply     the volume takes the office interior from the MS02 master (mo01_spec.ROOM: x 17.1-25.7 m, y 0.3-6.7 m, inset 2 cm), its
            height, rotation, id, anchors and other properties unchanged; BuildRoomBrush; only its actor package is saved;
  register  scoped update of the committed export Services/WhispersMind/cards/world/world-registry.json: only room.eden.mo's frame,
            extent and bounds change (anchors, doors, lights and every edge are kept; its door stays on the boundary). A copy of the
            file before the change is kept in review-media/hotel-unreal-mo01/world-registry.before.json.
State: review-media/hotel-unreal-mo01/Room_MO_E2K.json.
"""
import unreal, json, sys, os, shutil, importlib.util
STAGE = sys.argv[1] if len(sys.argv) > 1 else "plan"
CARD = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
REC = CARD + "/review-media/hotel-unreal-mo01"
SF = REC + "/Room_MO_E2K.json"
REGISTRY = os.path.join(os.path.abspath(unreal.Paths.project_dir()), "Services/WhispersMind/cards/world/world-registry.json")
st = json.load(open(SF)) if os.path.exists(SF) else {}
spec_ = importlib.util.spec_from_file_location("mo01_spec", CARD + "/furnishings/meredith_office_mo01/mo01_spec.py")
S = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(S)
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); W = ed.get_editor_world()
assert W.get_name() == "L_EdenE2K", W.get_name()
assert not ed.get_game_world(), "stop Play first"
I = json.load(open(REC + "/MO01_Install_State.json"))["world"]["instance"]
H = unreal.Transform(unreal.Vector(*I["translation_cm"]), unreal.Quat(*I["rotation_quat"]).rotator(), unreal.Vector(*I["scale"])); Hinv = H.inverse()
ROOM = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.WhispersRoomVolume) if str(a.room_id) == "room.eden.mo")
assert ROOM.get_actor_label() == "Room_MO_Office_166", ROOM.get_actor_label()
R = S.ROOM; INSET = 2.0
CX, CY = (R["x0"] + R["x1"]) * 50.0, (R["y0"] + R["y1"]) * 50.0            # hotel-local cm (plan y = Unreal hotel-local y)
EX, EY = (R["x1"] - R["x0"]) * 50.0 - INSET, (R["y1"] - R["y0"]) * 50.0 - INSET


def V(v):
    return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]


def dirty():
    return sorted(p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())


def forest():
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


def snap():
    t = ROOM.get_actor_transform()
    return {"world": V(t.translation), "local": V(Hinv.transform_location(t.translation)), "yaw": round(t.rotation.rotator().yaw, 4),
            "box_extent": V(ROOM.box_extent), "anchors": [str(a.id) for a in ROOM.anchors]}


def inside(frame, extent, p):
    l = frame.inverse_transform_location(p)
    return abs(l.x) <= extent.x and abs(l.y) <= extent.y and abs(l.z) <= extent.z


if STAGE == "plan":
    st["before"] = snap(); st["package"] = ROOM.get_package().get_name(); st["dirty_before"] = dirty(); st["forest_before"] = forest()
    reg = json.load(open(REGISTRY, encoding="utf-8")); st["registry_before"] = next(r for r in reg["rooms"] if r["roomId"] == "room.eden.mo")
    st["target_local"] = {"centre": [CX, CY, st["before"]["local"][2]], "extent": [EX, EY, st["before"]["box_extent"][2]]}
    json.dump(st, open(SF, "w"), indent=1); print("PLAN", json.dumps({k: st[k] for k in ("before", "target_local", "dirty_before")}))
elif STAGE == "apply":
    assert st.get("before"), "plan first"
    d0 = dirty(); pkg = ROOM.get_package(); assert pkg.get_name() not in d0, ("the room volume has unsaved changes; stop", d0)
    f0 = forest(); assert f0["ok"], ("E2K forest check failed; restart the editor", f0)
    t0 = ROOM.get_actor_transform(); z_local = Hinv.transform_location(t0.translation).z
    ROOM.modify()
    ROOM.set_actor_location_and_rotation(H.transform_location(unreal.Vector(CX, CY, z_local)), t0.rotation.rotator(), False, False)
    ROOM.set_editor_property("box_extent", unreal.Vector(EX, EY, ROOM.box_extent.z))
    ROOM.build_room_brush()
    d1 = dirty(); extra = sorted(set(d1) - set(d0) - {pkg.get_name()})
    f1 = forest(); assert f1["ok"] and not extra, ("not saving", f1, extra)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([pkg], True)
    st.update(applied=True, after=snap(), saved_packages=[pkg.get_name()], others_unsaved_left=d0, forest_at_save=f1, dirty_after=dirty())
    json.dump(st, open(SF, "w"), indent=1); print("APPLIED", json.dumps(st["after"]), "dirty after", st["dirty_after"])
elif STAGE == "register":
    assert st.get("applied"), "apply first"
    frame, extent = ROOM.get_actor_transform(), ROOM.box_extent
    reg_text = open(REGISTRY, encoding="utf-8").read(); reg = json.loads(reg_text)
    keep = REC + "/world-registry.before.json"
    if not os.path.exists(keep):
        shutil.copyfile(REGISTRY, keep)
    entry = next(r for r in reg["rooms"] if r["roomId"] == "room.eden.mo")
    for a in entry["anchors"]:                                   # every kept anchor must still be inside the room
        p = unreal.Vector(**a["transform"]["translation"]); p.z += 1.0
        assert inside(frame, extent, p), ("anchor outside the new room", a["id"])
    corners = [frame.transform_location(unreal.Vector(extent.x * x, extent.y * y, extent.z * z)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    q = frame.rotation
    entry.update({"frame": {"rotation": {k: round(getattr(q, k), 9) for k in "xyzw"}, "scale3D": {"x": 1.0, "y": 1.0, "z": 1.0},
                            "translation": {k: round(v, 5) for k, v in zip("xyz", frame.translation.to_tuple())}},
                  "extent": {k: round(v, 5) for k, v in zip("xyz", extent.to_tuple())},
                  "bounds": {"isValid": 1, "min": {k: round(min(getattr(p, k) for p in corners), 5) for k in "xyz"},
                             "max": {k: round(max(getattr(p, k) for p in corners), 5) for k in "xyz"}}})
    # keep the file's own formatting (indent and line endings) so the diff is the one record
    nl = "\r\n" if "\r\n" in reg_text else "\n"
    indent = 2 if reg_text.startswith("{" + nl + "  \"") else (4 if reg_text.startswith("{" + nl + "    \"") else 2)
    out = json.dumps(reg, indent=indent, ensure_ascii=True, sort_keys=reg_text.find('"aliases"') < reg_text.find('"rooms"'))
    if nl == "\r\n":
        out = out.replace("\n", "\r\n")
    if reg_text.endswith(nl):
        out += nl
    open(REGISTRY, "w", encoding="utf-8", newline="").write(out)
    st["registry_after"] = {k: entry[k] for k in ("frame", "extent", "bounds")}; json.dump(st, open(SF, "w"), indent=1)
    print("REGISTERED", json.dumps(st["registry_after"]))
elif STAGE == "verify":
    frame, extent = ROOM.get_actor_transform(), ROOM.box_extent
    pts = {"new_chair": (1930.0, 400.0), "new_desk": (2030.0, 400.0), "old_chair": (2390.9, 355.4), "door_inside": (2395.0, 640.0),
           "fire": (1760.0, 350.0), "corridor_outside": (2395.0, 760.0)}
    res = {k: inside(frame, extent, H.transform_location(unreal.Vector(x, y, 991.0))) for k, (x, y) in pts.items()}
    st["verify"] = {"inside": res, "dirty": dirty(), "volume": snap()}; json.dump(st, open(SF, "w"), indent=1)
    assert all(v for k, v in res.items() if k != "corridor_outside") and not res["corridor_outside"], res
    print("VERIFIED", json.dumps(st["verify"]))
else:
    raise SystemExit("unknown stage " + STAGE)
