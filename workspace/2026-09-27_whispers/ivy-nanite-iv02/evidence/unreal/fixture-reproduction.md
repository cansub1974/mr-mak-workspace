# IV02 — opaque static Nanite ivy

Revision IV02-r1, 24 October 2026; #114 delivery revised by IV02-r2, 25 October 2026. **Status 25 Oct 2026: IV02-A (#113) delivered and verified; IV02-B (#114) Unreal fixture built and measured, awaiting independent verification and Jason's visual verdict (B6). B5 target acceptance is NOT RUN/pending. IV02-B delivery (B7) is the committed report `docs/verification/ivy-IV02-B.md` plus the hashed local index `Saved/IV02/evidence_index.json`; no Workspace tab is part of IV02-B. The prototype is not accepted and no kit/PCG work is authorised.**

Live packets: [#113 — Blender source/export](https://github.com/cansub1974/Whispers/issues/113) and [#114 — Unreal prototype/measurement](https://github.com/cansub1974/Whispers/issues/114). Both read back OPEN and `needs-triage`; #114 is natively blocked by #113. No assignment, issue claim or editor/resource lock was acquired by this session. IssueBridge and the lead own triage/assignment; publication alone does not authorize execution under an assigned specialist contract.

Jason requested a reusable opaque ivy kit and reproducible placement/performance workflow, starting with one existing Hotel Eden facade section. The current increment is the prototype only. The complete kit and PCG rollout depend on its measured result and Jason's visual verdict.

## Source and constraints

- Authoritative hotel: `D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend`. Read-only dependency for IV02; no architecture edits and no second hotel `.blend`.
- A separate background Blender opened the master and produced `evidence/master-inventory.json`; it saved no `.blend`. Installed Blender: 5.2.1 LTS, hash 9e2066aef7ef. Some user add-ons logged compatibility errors, but the inventory completed and the process exited 0. Use `--factory-startup --disable-autoexec` for subsequent independent background inspections.
- New ivy source belongs in `D:/AI_Modelling/hotel_eden/working/ivy_IV02/`. The ivy `.blend` retains only ivy curves, Geometry Nodes, leaf sources, materials and export meshes. The facade is exported from a read-only master process to a fixture FBX; it is never saved into an ivy or hotel copy `.blend`.
- Blender → Unreal changes require two linked issues under the current project workflow. Blender and Unreal work have different role profiles and evidence. Neither issue is complete without independent verification and scoped remote delivery.
- The historical asset template still names MS01. The current owner instruction, master README and quality directive supersede that reference: **MS02 only**.

## Observed baseline

Live identity, engine and rendering are recorded in the evidence links in the Workspace tab. UE 5.8.2, CL 56702186, D3D12/SM6; project `D:/Unreal Projects/Whispers 5.8/Whispers.uproject`; editor PID 70640, bridge 1.4.8, protocol 2, binary built 24 October 13:20:22. Open map `/Game/Whispers/World/EdenE2K/L_EdenE2K`, PIE/simulate stopped, zero dirty packages at inspection. The Git checkout contains unrelated modifications; cleanliness in the editor is not Git cleanliness.

Live editor cvars: Epic scalability (all queried groups 3), TSR (`r.AntiAliasingMethod=4`), screen percentage 100, VSync 0, frame cap 0, Nanite 1, VSM 1, Substrate 1, experimental Nanite Foliage 1, Nanite ray tracing mode 1, hardware Lumen 1, texture pool 3000 MB. These are **editor readbacks**, not a frozen benchmark configuration or a measured frame-time baseline. Output resolution has not been established for the new fixture.

Host: Radeon RX 7900 XTX, 24,560 MiB dedicated VRAM reported by D3D12; AMD driver 32.0.21042.62, Adrenalin 2026.04.17; Ryzen 9 7900X, 12 cores / 24 threads; 67,816,374,272 bytes installed RAM. WMI's 32-bit AdapterRAM truncates VRAM; use the engine adapter log instead.

### Performance proposal to the lead — not agreed

Historical IV01 knowledge names an RTX 3060 / 60 FPS direction. It does not specify a current complete target platform or an ivy allocation. Propose RTX 3060 **12 GB desktop**, Ryzen 5 5600, 32 GB RAM, 1920×1080 output, High scalability, TSR at fixed 100% render percentage, dynamic resolution off, Development build, D3D12/SM6. These CPU/RAM/VRAM/settings are proposed, not facts about Jason's target machine.

Proposed full-coverage incremental allocation: paired median GPU delta ≤ 1.0 ms; total frame p95 ≤ 16.67 ms and p99 ≤ 20.0 ms; traversal p99 ≤ 25 ms and no repeatable ivy-attributable frame > 50 ms; additional resident GPU memory ≤ 256 MiB. Repeated differences inside the observed variation are inconclusive. These thresholds require a recorded lead decision; do not certify against this proposal. Host results remain workstation-only, regardless of how fast they are.

## Sourcing decision

Fab was authenticated; `list_library` reported 92 records (including duplicate representations). Owned-title searches ivy/vine/climber each returned zero. A complete title inventory was examined; the metadata shortlist is in `evidence/fab-shortlist.json`:

- **Sharur's Normandy Village + PCG Plants**, owned ID `901d90cacd2346b1896d45431d502119`. Metadata explicitly mentions wall ivy. Current compatibility flag is false. Leaf geometry, opacity, atlas and source availability remain unverified. Do not import the entire pack merely to inspect one asset.
- **Dark Ruins Megascans Sample**, owned ID `aafa85a424d04402b654171e43e63d52`. Compatible flag true; metadata does not establish suitable ivy. This is a pack to inspect, not a proven ivy match.
- **Existing local assets**: `/Game/Whispers/Presentation/Environment/HotelEden/FG02/Meshes/SM_FG02_Ivy_Left` and `_Right`; historical IV01 editable source/generator under `workspace/2026-09-27_whispers/ivy/`; MS02 ivy materials in MM01. Inspect reuse before fresh authoring. Historical appearance approval applies to IV01 only.

The local Megascans UAssets index contains an empty assets array. This does not prove that all Quixel entitlements are absent; it describes the checked local index and Fab service results only. No imports, purchases, claims or licence acceptance occurred. If a pack download is large, show the owner its exact selection and size before importing. Shipped sourced assets go in Whispers `docs/credits-log.md` with their provenance.

## Required rollout

1. The lead finalizes and queues the paired prototype packets through IssueBridge. No packet is promoted while consequential choices or its required locks are unresolved.
2. The Blender artist inspects owned/local candidates, exports a bounded existing facade fixture, and authors or adapts **one** open-surface ivy patch. Its own export evidence is independently verified before the tech artist starts the dependent import.
3. The technical artist builds the isolated test map, captures the no-ivy baseline, verifies import/shading/shadows, and runs the A–D suite. Retain all raw captures and exact settings. The acceptance ledger records absent evidence as NOT RUN, never zero milliseconds.
4. After technical evidence and Jason's visual decision, the lead writes the kit/PCG continuation against the accepted prototype. This increment does not authorize hotel-wide installation.

## Evidence and acceptance status

Environment/sourcing/source inspection: collected. IV02-A facade export and prototype mesh: delivered and verified (#113). IV02-B Unreal import, material comparison, Preserve Area retention, A–D captures, percentiles and streaming hitches: delivered on the workstation and awaiting independent verification; the ledger is `docs/verification/ivy-IV02-B.md`. RTX 3060 target/budget acceptance (B5), Jason's visual acceptance (B6), PCG and final coverage: **NOT RUN / pending**.

No technical pass or failure can be inferred from the environment inspection. The prototype and full workflow are **not accepted**. Old IV01 timing numbers are historical and are excluded from IV02 results.

## Reproduce read-only inspection

From the Workspace repository, run:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --factory-startup --disable-autoexec --background 'D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend' --python 'C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/ivy-nanite-iv02/inspect_master.py'
```

This writes JSON only. Verify source size/mtime/hash before and after; never save the master during inspection. For editor readbacks use the project MCP routes in `docs/agents/ue-mcp-toolchain.md`. Check dirty packages before VibeUE `execute_python_code`, which otherwise auto-saves them.

## Technical sources

- [Epic: working with Nanite-enabled content](https://dev.epicgames.com/documentation/unreal-engine/working-with-naniteenabled-content): Preserve Area, aggregate geometry and overdraw inspection.
- [Epic: Substrate materials](https://dev.epicgames.com/documentation/unreal-engine/overview-of-substrate-materials-in-unreal-engine): the enabled material framework requires an explicitly documented opaque foliage equivalent or verified legacy conversion.
- [Epic: Virtual Shadow Maps](https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine): VSM inspection and normal Nanite shadow route. Fallback geometry is not a VSM shadow proxy.

Local code/readback wins over assumptions about the installed build. The lighting guide describes `r.RayTracing.Nanite.Mode=1` as offline-only while the current project sets it to 1 for E2K. Record the discrepancy for the lead; freeze the actual test route and measure its traversal costs. Do not silently change global settings to make an ivy result pass.

## IV02-B Unreal fixture (#114) — README

Test-only fixture for the prototype measurement. Nothing here is shipping content or a hotel placement. Results and the acceptance ledger are in `docs/verification/ivy-IV02-B.md`.

### Assets

| Path | Kind | Notes |
| --- | --- | --- |
| `/Game/Whispers/Presentation/Environment/HotelEden/IV02/Meshes/SM_Ivy_WallPatch_Prototype` | ivy (shipping-candidate root) | Imported from `SourceAssets/HotelEden/IV02/exports/SM_Ivy_WallPatch_Prototype.fbx`. Nanite on, shape preservation NONE, no collision primitives, no navigation, slot `IvyAtlas` → `MI_Ivy_DefaultLit`. |
| `.../Meshes/SM_Ivy_WallPatch_Prototype_PreserveArea` | ivy variant | Duplicate of the same imported geometry; the only intended difference is Nanite shape preservation `PRESERVE_AREA` (readback). |
| `.../Materials/M_Ivy_DefaultLit`, `M_Ivy_TwoSidedFoliage`, `MI_*` | materials | Opaque, two-sided flag, no WPO/opacity/mask. Atlas base colour × `BaseTint` × tip lift (vertex colour B) × cavity (vertex colour R, also AmbientOcclusion: artistic only). Foliage variant adds SubsurfaceColor = base × `TransmissionTint` × `TransmissionStrength`. |
| `.../Textures/T_Ivy_Atlas_BaseColor` (sRGB, Default), `_Normal` (linear, NormalMap, **Flip Green** for the OpenGL source), `_Roughness` (linear, Grayscale) | textures | 2048². |
| `/Game/Whispers/Tests/HotelEden/IV02/SM_IV02_FacadeBay` | imported fixture | Exactly the IV02-A FBX (117,668 tris, six source slots restored to the source names). Kept for import evidence; **not drawn**: its translucent glass slot forces the whole mesh off Nanite. |
| `.../SM_IV02_FacadeBay_Opaque` | test-only | Same geometry minus the 40 glass triangles, Nanite on, five opaque slots mapped read-only to `MM01/Instances/MI_HE_HE_PBR01_*`; complex-as-simple collision for the support traces. |
| `.../SM_IV02_FacadeBay_Glass` | test-only | The 40 glass triangles, non-Nanite, hotel `MI_HE_HE_PBR01_Glass` (the hotel also draws glass through separate meshes). Opaque + Glass reproduce every source corner exactly. |
| `.../Validation/SM_IV02_AxisMarkers` | validation | Proves Unreal cm = (X, −Y, Z) × 100. |
| `.../E_IV02_Configuration` | enum | A (facade only), B (bay 0 ivy), C (32 bays), D (C + second jittered layer). |
| `.../BP_IV02_Benchmark` | test Blueprint | Owns the facade array, ivy instance sets, configuration, seed 24024, camera bookmarks and route autoplay. All components **Static**, no tick, ivy no collision. Functions: `ApplyConfiguration`, `RebuildInstances`, `PrepareFixture`, `IV02Config(ConfigIndex, PreserveArea)`, `IV02View(Index)`, `IV02Route()`. |
| `.../BP_IV02_GameMode` | test game mode | GameModeBase, no default pawn. |
| `.../LS_IV02_CameraRoute` | level sequence | 44 s, 30 fps: distant → courtyard → approach → oblique → 0.45 m → dense overlap → pull-out along the wall. |
| `.../L_IvyPrototype` | test map | Non-World-Partition. |

### Unreal-only test parts (no Blender counterpart)

- `IV02_Benchmark` (BP instance) with frozen transform arrays from `iv02_fixture.py`: 32 bays at X = k × 904 cm, k = −15…16 (bay 0 at the origin); ivy patches at yaw −90 (patch +X → fixture −Y, out of the wall).
- Placement manifest `Saved/IV02/fixture/placement_manifest.json`: **B = 2 patches per bay** (not the packet's initial 4). Measured by dense footprint traces (5 cm grid over the rigid occupied footprint, depth ±1.5 cm, normal ≤ 10°, brick/limestone only): the only supporting surface is the 102 cm brick strip right of the grand window (x 276–378 cm, z 55–420 cm). `strip_low` rooted on the plinth ledge top (z 55.0), `strip_high` at z 236 (top 418.97 < 420 crop; 1.5 cm overlap). Lateral support window xc 316–322 cm, frozen at 319. The 60 cm strip between the window lights and the corner returns fail. C = 64, D = 128 (second layer jittered ±3 cm x, 0–2 cm z, seed 24024). All 130 placements pass.
- Cameras `IV02_Cam_FirstPerson` (0.45 m), `IV02_Cam_Oblique` (3.0 m, 48° to the wall; reframed after pass 1 because the window frame hid the strip), `IV02_Cam_Courtyard` (15 m), `IV02_Cam_Distant` (60 m), `IV02_Cam_DenseOverlap` (1.2 m at the patch junction); FOV 90°, no aspect constraint; `IV02_Cam_Route` + `IV02_RouteSequence` (not auto-played).
- Lighting (lighting-authoring.md identity; audit clean, 2 lights): `IV02_Sun` directional, Movable, 75,000 lux (the E2K physical sun level), Allow MegaLights **off**, identity `Eden.Exterior.Sun.01` / `Light.Zone.Eden.Exterior` / `Light.Role.Celestial` (no profile, the documented celestial exception); `Lamppost_Exterior_01` = `BP_Light_Lamppost` + `DA_LightProfile_Lamppost`, `Eden.Exterior.Lamppost.01` / `Light.Role.Exterior` (MegaLights, ray-traced shadows per the profile); `IV02_SkyAtmosphere`; `IV02_SkyLight` (real-time capture); `IV02_PPV_FixedExposure` (unbound, histogram min = max = fixed EV100). No zone volume: an uncovered fixture stays Active.
- Lighting presets (driver/fixture): `front` sun pitch −35 yaw 60, EV100 14.5 (all timing runs); `back` (contre-jour along the wall) pitch −12 yaw 178, EV100 12.5; `local` sun 0 lux, sky 0.02, lamppost on, EV100 3.0.
- `IV02_Ground`: engine plane, `MI_HE_HE_PBR01_Interior`, Static.
- `PrepareFixture` re-asserts the authored sun after BeginPlay and sets the HUD context `UI.HUD.Context.Hidden`. Reason (finding for the lighting owner, not changed here): the lighting Director drives every light on a `WhispersLightComponent` owner from its profile, so a profile-less celestial sun drops to 0 lux / 2700 K; E2K hides this because Ultra Dynamic Sky rewrites its sun each frame.

### Build mode and its limits

- Measurement runs are **Standalone Game, uncooked** (`UnrealEditor.exe Whispers.uproject /Game/Whispers/Tests/HotelEden/IV02/L_IvyPrototype -game ...`, CSV metadata `[config] Development`). Packaged Development was not used: a scoped cook/package needs shared Config/target changes outside this task. Shaders come from the shared DDC (a `prep_shaders` run touches every configuration first); uncooked loading and editor-only data are present.
- The editor was **closed** during the timing suite; Insights and visual runs are diagnostic only.
- Workstation only (RX 7900 XTX / Ryzen 9 7900X). No RTX 3060 result exists; target acceptance is NOT RUN.
- Debug view modes (Nanite overdraw/mask, VSM) do not apply in the `-game` process; they were captured in the editor viewport (`iv02_editor_vis.py`).

### Reproduce

1. Editor (empty dirty list), Python: `iv02_import.schedule()`, `iv02_mesh_setup.schedule()`, `iv02_materials.build()`, `iv02_blueprint.build_shell(); build_graphs()`, `iv02_defer.schedule("new_level")`, `iv02_glass.schedule(); finalize(); schedule_opaque(); finalize_opaque()`, then `iv02_fixture.base(); survey(); ivy(); lights(); game_mode(); cameras(); route()`; `WhispersLighting.audit_lights.run()`.
2. Close the editor; `python Content/Python/WhispersTests/IV02/iv02_launch.py prep|visual|timing|insights|video`.
3. `python .../analyze_runs.py`, `compare_import.py`, `compare_visual.py stills|video|index`.
4. `python Content/Python/WhispersTests/IV02/temporal_review.py` (offline, reads the route PNG dumps; writes `Saved/IV02/analysis/temporal_review/`).

### Lessons (verified)

- Whole-frame difference statistics do not show changes to small, thin geometry. Measure Preserve Area retention on ivy pixels with a no-ivy baseline subtracted. Measured on config C: with Preserve Area off, the ivy is almost gone at 60 m (18 px against 1,043 px with it on), and Preserve Area on shows ×1.67 at 15 m. All timing runs used Preserve Area off, so a kit decision needs a timed run with it on.
- A fixed-timestep route dump captures one frame after the sequence ends, so the view cuts to a fixed camera. Remove that frame before running temporal pop checks.

### Manual review

Open `L_IvyPrototype`, select `IV02_Benchmark`, set `Configuration` (A–D), `UsePreserveArea`, `StartBookmark` (0 first person, 1 oblique, 2 courtyard, 3 distant, 4 dense) or `AutoPlayRoute`, then Play. In PIE the console accepts `ke * IV02View 3`, `ke * IV02Config 2 0` and `ke * IV02Route`. Inspect leaves, the window exclusion, the corner pedestal and the plinth ledge.


# IV02 continuation — gated design, not an implementation assignment

Do not expand until the prototype export/import, rendering, measured performance and Jason's visual criterion pass. Record the accepted asset hashes, material route, coverage/settings and performance budget in the continuation packet. A success at a lower coverage or on the RX 7900 XTX does not certify the full hotel or RTX 3060.

## Kit and wall material

Produce `SM_Ivy_WallPatch_*` (dense centre, sparse edge and transitions), `SM_Ivy_PillarWrap_*` (explicit two-plane/corner anchors and footprint), and `SM_Ivy_HangingDangle_*` (top attachment pivot). Each variant uses the same exported frame and documented bounds; corner and hanging assets have their own attachment metadata rather than being rotated wall patches that penetrate the building. Keep editable curves/GN and realized export copies, atlas, masks and shared material instances. Re-run clean FBX and Unreal attribute checks for every variant. Avoid adding thickness across all leaves merely for uniformity.

Start the masonry underlayer with color, roughness and normal blending in a separate IV02 material variant; original hotel materials stay read-only unless a later contract expressly authorizes their replacement. POM is deferred. A POM experiment requires matched close/oblique distance views, explicit local application bounds, artifact inspection and paired frame/GPU measurements; adopt only if the lead records a useful visual gain within the agreed allocation. It does not replace large ivy silhouettes or ledge geometry.

## Placement data contract

The PCG continuation owns only an ivy layer and its placement metadata. Define facade-local metre coordinates from the imported bay anchors, inclusion polygons, separate exclusion polygons for every window/door and opening, wall height bands, corner anchor pairs and ledge top attachment curves. Include source/master revision and transform, generating actor/level, mesh footprint/support sample offsets, outward axis, growth/up vector, seed, spacing, maximum overlaps and per-region coverage. Record named geometry or collision query filters; visibility/collision presence alone cannot identify a valid host wall.

Use mesh sampling or bounded facade-directed ray queries against explicitly included host components. Compute surface frame with +X outward and +Z projected from world/growth-up; handle near-horizontal normals using ledge rules rather than an unstable cross-product. Apply small wall offset in cm. A matching centre normal is only a candidate: sample the patch footprint at corners, edge midpoints and stem anchors; reject where support distance or normal deviation exceeds the contracted tolerance, where an exclusion intersects any occupied leaf/stem footprint, or where the patch crosses unsupported recesses. Tolerances are tuned against actual patch geometry and frozen in the continuation acceptance contract before rollout. Split patches or use the specific corner asset where surfaces turn; do not pretend a rigid patch deforms to fit.

Separate wall, corner and ledge PCG subgraphs. Walls use footprint support and facade inclusion/exclusion; corners require both anchor surfaces, correct handedness and minimum supported wrap; ledges require an actual top-support sample and hanging-direction clearance. Check dangling mesh intersection along its full extent, not just its pivot. Preserve all hotel geometry and runtime door/light/audio identities. No actor proliferation or per-frame regeneration.

Use deterministic seed 24024 plus persistent region/instance IDs and local streams per rule, so regenerating one region does not randomize unrelated regions. Apply minimum spacing and explicit geometric/projection overlap caps before instancing. Record rejection reasons/counts. Generate twice and compare transform/mesh hashes; a moving window exclusion must deterministically remove affected instances. PCG graph parameters, intermediate masks and final instance transforms remain inspectable.

Use appropriate static ISM/HISM/component grouping by mesh/material and spatial region. Inspect world/local bounds, frustum/occlusion culling, Nanite behavior and memory in the actual build; do not assume instance distance settings cull Nanite the same way as conventional LOD meshes. Measure the result. Bounds should contain leaves/petioles without an excessive margin. No WPO means no wind expansion. Keep collision/nav off for ivy; fixtures/support query geometry remain separate from runtime ivy collision.

## Coverage and integration evidence

The lead issues the complete kit/PCG packet only after prototype results identify its accepted technical route. A separate approved hotel placement touch list resolves actual source levels and their current instance transform; historical L_Eden coordinates are not substituted for the current E2K placement. Master/Unreal architecture stays unchanged. If a future task introduces placed ivy into the master, its ivy layer and placed Unreal layer must match and the task must hold the appropriate master write lock; this prototype does neither.

Re-run A–D at final atlas/material/PCG coverage using the same camera/settings protocol. Include an actual representative full-coverage hotel view or clearly documented coverage stress environment with measured projected/shadow coverage. Do not multiply the cost of one patch by the patch count. Repeat first-person/oblique/courtyard/distant/densest overlap views and traversal/streaming runs. Compare original no-ivy state against final generated coverage with the same hotel/lighting state. Final material complexity, overlap, VSM cache behavior, ray-tracing scene cost and streaming can change the result nonlinearly.

The final ledger records every user criterion PASS/FAIL/NOT RUN, agreed budget, target hardware gaps, literal visual findings, raw capture hashes, run variation and ms deltas. Jason's visual decision and independent technical verification remain separate. Deliver scoped commits, asset credits and explicit local large-file manifests. An import, shader compile, triangle count or attractive image cannot substitute for this evidence.
