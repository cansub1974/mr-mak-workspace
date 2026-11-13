# MO01 Meredith's office into Unreal (Whispers 5.8, L_EdenE2K)

Owner, 12 November 2026: "Sync the corridor lights in MS02 to match Unreal. Then port the Blender model of Meredith's
office into the Unreal Hotel Edn 2k level. Beautiful game quality, moody lighting. Simple colliders."

The office went from the MS02 master into `L_HotelEden_Building`, which `L_EdenE2K` shows through the `HotelEden` Level
Instance (as EC01). Not committed.

## The corridor lights in MS02 (first part of the request)

- **Before:** MS02's twelve EC01 sconce lights were still the install's downward Spots (400 lm, 70/40°, 400 cm).
  Unreal has had point lights on `DA_LightProfile_EC01_Sconce` since the owner's review of 11 November.
- **Now:** each of the twelve lights is a Point light in place, at the same position (the flame + 4.5 cm).
  - **Values:** 1,400 lm, 2,700 K, 3 cm source, 520 cm reach.
  - **Identity:** type, lumens and profile updated.
- **Script:** `furnishings/executive_corridor_ec01/sync_lights_ms02.py -- --save`.
  - **Guard:** every other object, mesh and light was inventoried before and after; none changed.
  - **Record:** `review-media/executive-corridor-ec01/build/Lights_Sync_MS02.json`.
- **Rebuild-safe:** `ec01_spec.LIGHT_RULE`, `build_ec01.py` and `check_ec01.py` now use the point rule, so a rebuild
  keeps it. `check_ec01.py` on the saved master: lights OK, 158 objects, 241,710 triangles, unchanged.

## Run order

1. **Survey** (read-only): `blender -b <MS02> --python survey_mo01_master.py` writes the material graphs
   (`MO01_Blender_Materials.json`) and the object survey (`MO01_Master_Survey.json`).
2. **Export** (headless, never saves the master): `blender -b <MS02> --python export_mo01.py`.
   - **Writes:** one FBX per asset to `D:/Unreal Projects/Whispers 5.8/SourceAssets/HotelEden/MO01/meshes`, the textures,
     and `review-media/hotel-unreal-mo01/Export_Manifest.json`.
3. **Install:** `python ue_bridge.py run install_mo01.py <stage>`, through the ue-mcp bridge's `run_python_file`, which
   doesn't save other sessions' dirty packages.
   - **Stages:** `checkpoint`, `textures`, `materials`, `meshes`, `fixtures`, `open_building`, `place`, `verify`,
     `look`, `open_e2k`, `world`. After a master rebuild, `update` moves the instances that changed.
   - **State:** `review-media/hotel-unreal-mo01/MO01_Install_State.json`.
4. **Collision:** in the Whispers repo, `python tools/hotel/reapply_hotel_collision.py`. It reports OK.
5. **Play:** `python ue_bridge.py run pie_mo01.py start | view <Name> | lights | stop`.
   - **Captures:** `../hotel-unreal-passageways/ue_mcp.py capture <png> game`. The editor window must not be
     minimized: restore it without activating it (`ShowWindow` 4), then minimize it again.

## What is in Unreal

- **Assets:** `/Game/Whispers/Presentation/Environment/HotelEden/MO01`, plus two hotel-wide folders:
  - `HotelEden/P03`: the FUR-024 P03 palm, the first time it is in Unreal (the lobby pair is not yet);
  - `HotelEden/G01`: the approved G01 grate and fuel.
- **Textures:** 61. BaseColor is sRGB. NormalGL imports as `TC_Normalmap` with green flipped. ORM and AO are masks.
- **Meshes:** 88 imported once each, 48 of them Nanite.
  - Not Nanite: under 200 triangles, the sheer and the clock (their translucent slots), and the flame cards.
  - Two-UV meshes carry channel 0 `UVT` (the tangent UV, the EC01 lesson), then 1 `UV0_Bake` and 2 `UV1_Wood`.
- **Reused:** EC01's `SM_HE_AF02_Frame` (the portrait frames) and `BP_EC01_WallSconce_S06` (the two sconces).
  - **Check:** both fingerprints match the EC01 export exactly.
  - **Materials:** EC01's mahogany, moulding, veneer and brass instances; the lobby fireplace's `M_HE_FireplaceFlame` and
    crackle loop.
- **Materials,** rebuilt from the Blender node graphs (owner, 11 Nov: "USE THE MATERIAL FROM BLENDER IN A SMART MANNER"):
  - **Parents:** `M_MO01_Surface` (opaque) and `M_MO01_Translucent` (two-sided, Surface ForwardShading). They are EC01's
    `M_EC01_Surface` graph plus:
    - `WoodUVScale` for Blender's Mapping nodes (wallpaper 2.65 × 2.33 per m, parquet 1/3.4 m, brick 1/1.8 m, pelmet
      velvet 1/0.284 m);
    - `UseVertexColor` for the firebox soot;
    - opacity, from a constant or the BaseColor alpha.
  - **Instances:** 31. Instance overrides give two-sided for the drapery and palm leaves, masked for the fringe, and a
    one-sided clock glass.
  - **Drapery:** the baked fold normal (UV0) is reoriented with the weave bump (UV1, strength 0.35). Blender bumps the
    drapes with the weave normal map's Blue channel at 0.6 mm; that is baked to `T_MO01_VelvetBump_NormalGL` and
    `T_MO01_SheerBump_NormalGL`. The fold AO goes into the colour at 0.8, as Blender's Mix.
- **`MO01_MeredithOffice`** (outliner `Hotel Eden/Meredith office MO01`): 89 instanced components and 233 instances.
  - **Collision (simple):** five UCX boxes in all: one each for the chimney breast, mantel and both bookcases, and one round
    the palm's planter. Everything else has none: books, ornaments, trim, drapery, rug, fronds.
- **Fire:**
  - three crossed flame cards over the G01 fuel with the hotel's procedural `M_HE_FireplaceFlame` (Unreal only, as the
    lobby fireplace's);
  - `MO01_Fireplace_Crackle`: the lobby's `S_HE_FireplaceCrackle_Loop` through `SA_HE_Fireplace` at 0.6.
- **Lights** (`lighting-authoring.md`; folder `Lighting/Hotel/MeredithOffice`; zone `Light.Zone.Hotel.MeredithOffice`;
  group `Light.Group.MeredithOffice`; the ids are the master's):

  | Fixture | Ids | Fixture asset and profile |
  | --- | --- | --- |
  | Two sconces | `Hotel.MeredithOffice.WallSconce.01-02` | `BP_EC01_WallSconce_S06`, the corridor's profile (Point, 1,400 lm) |
  | Fireplace | `.Fireplace.01` | `BP_Light_Fireplace` (1,500 lm, 1,900 K, role Fire) |
  | Picture light | `.PictureLight.01` | `BP_Light_WallSconce` (Spot, 400 lm), turned to the master's aim, 75° down |
  | Window fill | `.WindowFill.01-04` | `BP_Light_WindowFill` on `DA_LightProfile_MO01_WindowFill`: 500 lm, 6,200 K, 170 × 240 cm, shadowless |
- **Why the window fill is low:** the catalog's 3,000 lm of 5,500 K flattened the room. No mood drives the fills, so
  they also burn at night. Their ray-traced shadows grazed the ceiling as dark speckle (measured below), so the profile
  is shadowless, as the lobby's fill profiles are. The master's rule matches: 500 lm, `use_shadow` off.
- **Zone:**
  - `MO01_Zone_MeredithOffice`, the room's interior (x 1710–2570, y 30–670, z 905–1315 cm);
  - `MO01_Portal_Office_Exterior`, a sightline-only portal to `Eden.Exterior` (the windows glow from outside, as LM01's lit
    rooms do);
  - the EC01 door portal, retargeted (`EC01_Portal_Office_MeredithOffice`, was `..._Level3Rooms`).
- **LM01 lamp retired:** LM01's generic lamp for this room (`LM01_RoomLamp_Level3Rooms_Lamp_04`, 4,000 lm) and its box
  were retired. Their full records are in the state file under `place.retired_lm01`.
- **`MO01_OfficeLook`:** a post volume over the office only, priority 3, above the hotel's interior look at 2, with a
  50 cm blend.
  - Lumen final-gather quality 2.
  - Exposure bias −0.5 EV: the interior look's auto exposure (−10 to 20 EV) would lift the room out of its mood.
  - Local shadow contrast 0.9.
  - Vignette 0.45.

## Changed in the master on the way (MS02, saved in place)

- **Sheer weave:** the sheers had tiled their own fold map.
  - **Cause:** the drapes kit baked the sheer's fold normal as `T_MO01_Sheer_NormalGL.png`, the name of the tiling crepe
    weave, so both of the material's normal nodes read the fold bake.
  - **Fix:** the bake is now `T_MO01_SheerFolds_NormalGL.png` (`mo01_drapes.fold_name`). The weave was regenerated with
    `prepare_textures.py sheer`, the kit repointed (`fix_sheer_kit.py`), and MO01 rebuilt.
  - **Backups:** the kit and the overwritten file are in `meredith_office_MO01/backups/`.
- **Clearances:** the office's ceiling plane is now 10 mm under the hotel shell's ceiling (it was 1 mm), and the paper
  stands 3 mm off the walls (`PAPER_OFF`, `CEIL_DROP`).
- **Window fill:** the rule is the Unreal profile's: 500 lm, 6,200 K, shadowless.

## Checks

| Check | Result |
| --- | --- |
| Building (open) and E2K through `HotelEden` | 233 placements at 0.0 cm; 8 lights with id, zone, role, group, profile; zone, portals, crackle present; nothing unsaved |
| Light aims | Picture light and window fills within 0.0° of the Blender lights |
| Meshes | 88: bounds within 1 cm, triangles, UV channels, UCX counts all asserted |
| Hotel collision guard | reapply + check: OK (978,012 collision triangles) |
| Play | Director: 8 lights registered, Active in the office, zone covered |
| MS02 reopened | MO01 251 objects, 170,461 triangles, 93 unique meshes, 80 images packed, none missing; EC01 lights OK |
| Export vs Unreal | only the ceiling and paper placements changed after the first install; `update` moved exactly those nine |

Captures: `review-media/hotel-unreal-mo01/captures/UE_MO01_*.png`, in Play. The `diag_*` files are the ceiling diagnosis.

## Furniture, and Meredith at her desk (12 Nov, later)

Owner: "there are blender files in there for the sofa, the desk and the chair. Copy them over to where you keep all the
other models and add them to the approved furniture list. Add them to Meredith's office Blender file and place them like
in the reference image. Then check to see that they are placed in the right spot in the Unreal file. Get rid of the
textureless desk thing." Then: "yes I do want Meredith to sit and use the new desk and chair".

- **Approved list:** FUR-106 chesterfield (CF01), FUR-107 pedestal desk (PD01) and FUR-108 swivel chair (SW01) in
  `approved-media/` (`furnishings/meredith_office_mo01/package_furniture.py`, `register_furniture.py`).
- **MS02:** `mo01_spec.FURNITURE`, placed by `build_mo01.py` from the approved game Blender files, in hotel-local cm.
- **E2K (`furnish_e2k.py plan | apply | verify`):** the session that made them had placed them in E2K. The desk, chair
  and Meredith's seven `Life_Manager_*_SL8` advertisements moved as one rigid group to the master's placement; the sofa
  on its own; `TMP_Life_Manager_Desk_SL8` and `TMP_Life_Manager_ChairSeat_SL8` were deleted (restore records in
  `Furniture_E2K.json`). The imported assets were already sound, so nothing was reimported.
- **Meredith (measured, then fixed):**
  - `chair_collision_e2k.py`: her slots approach the chair's centre and seat her 40 cm under it, as authored against the
    `NoCollision` grey block. The chair's `Base` and `Seat` blocked pawns and cut the dynamic navmesh, which put that
    point on the chair top. On the placed chair they now ignore `Pawn` and don't affect navigation; they still block the
    camera, visibility and physics. The Blueprint asset is unchanged. The player can walk through the chair.
  - `room_mo_e2k.py`: `Room_MO_Office_166` (`room.eden.mo`) covered only x 2209-2581 (the grey block's end of the
    room). The registry resolves the smallest containing room, so in front of the fire she was in
    `room.eden.level3rooms_lamp_04` and Life offered her desk nothing. The volume now spans the office interior
    (`mo01_spec.ROOM`, inset 2 cm) and its one record in `Services/WhispersMind/cards/world/world-registry.json` matches
    (frame, extent, bounds; 8 lines; anchors, doors, lights and edges kept). The previous file is
    `world-registry.before.json`.
  - `pie_desk_smoke.py arm | isolate | stage | check | stop`, with `pie_meredith.py`: the smoke slot redirect (#219),
    so `WhispersContinue.sav` and its backups were proved unchanged. Staged on the office floor, she walked to the
    desk, sat and ran write, type and read in turn. Captures `UE_MO01_Meredith_At_Desk*.png`.
  - `continue_meredith_office.py` (13 Nov; the owner chose "Option 2, walk her back to her office"): my earlier Play
    tests without the smoke slot had saved her at the kitchen's north-west end (`room.eden.l1_northwest`, Life edges
    blocked by #215; Population "unreachable: no complete navigation path"). `backup` copied the slot and `.bak1-3` to
    `Saved/SaveGames/_before_mo01_office_20261113/` (hashes equal). One deliberate Play on the Continue slot (restored
    from candidate 0, not redirected) moved only her body onto the office floor at (2250, 520); Life chose
    `desk.write`, sat, then `desk.type`; the quit commit wrote it. The slot and all three backups now hold
    `room.eden.mo`, outcome `arrived`, body at the seat, action `desk.type` Loop. A redirected check Play continued
    from it: she restored seated at the desk (`desk.write` Loop) and `verify_file` showed no slot file changed.
    Captures `UE_MO01_Meredith_After_Continue*.png`; state `Continue_Meredith_Office.json`. The game clock in the
    save moved on about 12 game minutes (10:12 to 10:24); nothing else was staged.

## Hero desk, swivel chair and journal (13 Nov 2026)

Owner: "The desk and the sofa need to be about 20 percent larger. They are hero pieces. Meredith's chair needs to be rotated
about 70 degrees perpendicular to the desk when she is not in it. When she goes to sit in it she will stand in front of the chair
with her back to it. She will sit down. The chair and her will rotate so that she and the chair are square to the desk. The chair
and her will then move inwards to the desk so that she is sitting comfortably close ... Her hands must work at the level of the
desk plus the width of a journal. Place the same journal that is on the reception desk on Meredith's desk right where she is
writing". The owner chose the desk wider and deeper only (77 cm kept) and the chesterfield 20% all round.

- **Code (Whispers repo; built, editor restarted once with the owner's permission after saving the other session's three
  desk textures as asked):**
  - `AWhispersSwivelDeskChair` (WhispersLife);
  - the held seat in `UWhispersBodyComponent`;
  - `bHoldSeatBetweenActivities` and `bSeatAtRest` on `AWhispersReceptionOverlay`;
  - no stand-up for a seat conversation in a held chair.

  See `docs/features/npc-body.md`, "Held seat and the swivel desk chair".
- `desk_chair_e2k.py` stages:
  - `scale`: the desk x (1.2, 1.2, 1.0); the chesterfield x 1.2, back kept.
  - `chair`: the BP chair replaced with the new class, the same meshes and materials; working pose at hotel-local
    (1942, 400) facing the desk; rest 30 cm back, seat turned 70 deg.
  - `life`: the six seated `Life_Manager_*_SL8` at the rest seat point (1913.0, 402.8, 951.3), yaw 70, Approach 40 cm in
    front, presentation `Overlay_MO_DeskChair`; StandLean stops advertising.
  - `overlay_so`: Life claims the overlay's own Smart Object, so it got `SO_Manager_DeskChair`. Its slot is 40 cm below
    the overlay root, so the overlay root stands 40 cm above the seat point.
  - `activities`: the chair sit-down and stand-up montages, 3.2 s and 3.6 s.
  - `journal 1993 405`: the UI01 LP01 ledger mesh with its PenRest under her pen, all corners on the desk.
- `ms02_desk_chair.py` (furnishings/meredith_office_mo01): the master matches from the same record. `mo01_spec.FURNITURE`
  and `build_mo01.build_furniture` carry the new layout; `furnish_e2k.py` is marked superseded.
- **Play (`pie_chair_smoke.py`, test slot every time):**
  - **Restore:** her Continue restores pulled in.
  - **Between desk jobs:** a finished job holds her seated, and the next job on the chair continues in Loop (`held=1`).
  - **Leaving** (a `come` move to the player): roll out (pelvis x 1945 to 1915), turn 70, then the stand-up.
  - **Returning:** she turns her back to the chair, sits (Enter 3 s), swivels (1.6 s), rolls in (1.3 s).
  - **Working:** pelvis 24 cm from the desk edge; wrists about 988 cm against a page at 982.5.

  Captures `UE_MO01_Chair_*.png` and `captures/sequence/`.
- **Lessons:**
  - Moving the Life objects is not enough with a presentation overlay: Body checked the slot of the overlay's Smart
    Object.
  - Python cannot edit a Smart Object slot's offset, so move the frame to the slot.
  - Git Bash rewrites `/Game/...` arguments unless `MSYS_NO_PATHCONV=1`.
  - The player pawn parked by the office door blocks her way out.

## Sheers behind the sage curtains (13 Nov 2026)

Owner: "The sage curtains should not have the white translucent curtains clipping through them. Please fix those."

- **The cause:** the sheer and the side curtains were simulated apart (`mo01_cloth.py`). The settled sheer stood up to
  16 cm in front of the curtain it hangs behind (218 of 1020 game-mesh vertices, worst at the hem).
- **The fix:** `furnishings/meredith_office_mo01/fix_sheer_mo01.py` reruns from the settled simulation it keeps
  (`Sheer_Simulated_Original.npy`).
  - Ray casts on the curtain faces find every fold layer along the depth line through each sheer vertex and four points
    round it, for the N and E Z scales. The vertex goes at least 1.5 cm behind the rear-most layer.
  - Each push fades over 10 cm, so the open middle moves at most 3.6 cm, at the curtain edges.
  - Bounds: 2 cm off the wall, and in front of the sill.
  - The shared `SM_MO01_Sheer` (4 windows) is saved in the master and exported as `export_mo01` does.
- **Unreal:** `sheer_fix_ue.py` reimports it with `install_mo01`'s FBX options, material and build settings. Bounds
  match the manifest (0 cm), with 1900 triangles and 3 UVs.
- **Checked:** captures `UE_MO01_Curtains_*.png` (Play, test slot).
- **Left as found:** a tiny bright fleck low on one north curtain is a gap in the curtain's own folds.
- **Lesson:** a vertex-neighbourhood test against a coarse game mesh misses rows. Ray-cast the faces.

## Found, not changed

- **A desk normal map in progress:** `T_DeskPedestal_N` (new) and `T_DeskPedestal_BC` / `_ORM` were unsaved in the
  editor from another session; left as found.
- **Window fill zone warning:** the four `Hotel.MeredithOffice.WindowFill` fixtures stand outside the glass, so the
  director logs that they are in `Light.Zone.Hotel.Level3Passages`; they are never demoted, so the room is unaffected.
- **Fire flicker:** the fire light is steady by default. Flicker comes from moods (`CandlelitDinner`) or the GM; the
  flame cards themselves move.
- **Knob UVs:** `SM_MO01_CaseKnob`'s UVs are created empty in `build_mo01.py`, so they differ between builds. It has no
  normal map and the brass reads the same.
- **OC02:** `L_HotelEden_OC02` does not have the office; EC01 had gone into both.

## Lessons

- **A real chair under a Life seat:** a seat authored against a `NoCollision` stand-in keeps its approach at the seat.
  A solid replacement needs to let pawns through, or the slot needs a reachable approach beside it.
- **Life rooms come from the registry export, not the volumes:** `ResolveRoom` picks the smallest containing record in
  `world-registry.json`. A volume edit needs its record updated too (scoped, as #197 and #215 did).
- **Play tests use the smoke slot:** `WhispersTests.smoke_slot.arm` before Play. Without it a test writes the owner's
  Continue save.

- **Where speckle on a ceiling comes from:** before tuning Lumen, switch the suspects off one at a time in Play: the
  `MegaLights.Enable` and `Lumen.DiffuseIndirect.Allow` cvars, then each light group. Here it was a rect fill's
  ray-traced shadows at a grazing angle, not GI.
- **Measure the shell before blaming z-fighting:** the hotel's interior shell over this room is four flat triangles at
  exactly 1320 cm. A vertex scan finds nothing over a room crossed by large triangles: interpolate the triangles at a
  grid instead.
- **The bridge's default timeout is 30 s:** pass `timeoutMs` on `run_python_file`. A timed-out call may still finish, so
  read the state back before retrying.
- **Bake names must not reuse a source map's name:** the sheer's fold bake overwrote its tiling weave and nothing
  failed.
- **FBX drops unused material slots:** check slot mapping against the slots that have triangles.
