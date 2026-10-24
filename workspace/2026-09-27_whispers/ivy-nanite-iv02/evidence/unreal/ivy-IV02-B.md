# #114 IV02-B: Unreal facade prototype and measured Nanite validation (packet IV02-r2)

Specialist: tech-artist seat (Claude, IssueBridge run 96a9e41123904fdf81ed6d7117d56591). Locks: `editor:whispers`,
`asset:Content/Whispers/Presentation/Environment/HotelEden/IV02`, `map:/Game/Whispers/Tests/HotelEden/IV02/L_IvyPrototype`,
`asset:ivy-IV02-evidence`. Fixture README: `docs/features/hotel-eden-ivy-iv02.md` → "IV02-B Unreal fixture (#114) — README".

**Status (25 Oct 2026, packet IV02-r2).** Built, imported, measured on the workstation and handed to independent
verification. IV02-r2 (lead decision, 25 Oct) makes this committed report plus the hashed local index
`Saved/IV02/evidence_index.json` the B7 delivery; no Workspace tab is required. Not accepted:
B5 target acceptance is NOT RUN/pending (no agreed budget, no RTX 3060) and B6 is Jason's verdict. No kit/PCG
continuation or hotel installation is claimed.

Baseline: Whispers HEAD `44e30b7` at claim; UE **5.8.4-58902052** (the packet observed 5.8.2); ue-mcp bridge API 2;
editor PID 36788 at claim (later closed for timing and relaunched); D3D12 SM6; RX 7900 XTX (driver 32.0.21042.62,
Adrenalin 2026.04.17), Ryzen 9 7900X, 64 GB. Local evidence root `Saved/IV02/` (never committed; index with sizes and
SHA-256 in `Saved/IV02/evidence_index.json`).

## Acceptance ledger

| AC | Result | Evidence (local paths under `Saved/IV02/` unless stated) |
| --- | --- | --- |
| B1 Import | **PASS (technical), with 2 recorded Unreal-side repairs** | `import/import_result.json`, `import/readback.json`, `import/compare_import.json`, `materials/*`, `fixture/fixture_state_after_reopen.json` |
| B2 Fixture / reproduction | **PASS (technical)**; patch count revised to the measured support (B = 2) | `fixture/support_survey.json`, `fixture/placement_manifest.json`, `fixture/fixture_state_after_reopen.json`, `evidence/lighting/audit-20261024-221451.json`, README in `docs/features/hotel-eden-ivy-iv02.md` |
| B3 Rendering | **Evidence delivered; literal findings below.** Visual acceptance is Jason's (B6) | `runs/visual/shots/*`, `runs/visual/sheets/*`, `evidence/editor_vis/*`, `runs/video_cfgC_PA*/*.mp4`, `runs/video_cfgC_PA_side_by_side.mp4`, `analysis/visual_pairs.json`, `analysis/video_pa.json`, `analysis/temporal_review/*` (direct temporal review, 25 Oct) |
| B4 Performance evidence | **Delivered (workstation series)** | `runs/timing_r{1,2,3}_{A,B,C,D}/` (raw CSV, driver log, run manifest, memreport, game log), `analysis/summary.{json,md}`, `traces/insights_{A..D}.utrace` |
| B5 Budget | **NOT RUN / pending.** No recorded lead decision on the proposed budget and no RTX 3060 run. Workstation numbers are compared with the *proposal* for information only | this report, "B5" |
| B6 Visual gate | **Pending: Jason's verdict.** Not self-approved; IV01 approval does not apply | "Manual review" below |
| B7 Delivery | **Delivered per IV02-r2:** Whispers scoped commits on `origin/main` (receipts in the issue comments) and the complete hashed local index (1794 files, `--check` clean). Workspace tab out of scope (finding 5, resolved). Independent verification pending | this report, "B7"; `evidence_index.json` |

## B1 Import

Sources: the 6 import inputs match `SourceAssets/HotelEden/IV02/qa/IV02_file_manifest.json` byte-for-byte (SHA-256); the
delivered set is 69/69 matching. Import route: Interchange (`Interchange.FeatureFlags.Import.FBX = 1` on this build),
`InterchangeGenericAssetsPipeline` with recompute normals **off** (custom split normals kept), MikkTSpace tangents,
vertex colour Replace, no materials/collision/LODs generated, combine all, deferred on a Slate post-tick.

| Check | Contract | Measured in Unreal | Result |
| --- | --- | --- | --- |
| Ivy tight bounds | Blender X 0.19–7.90, Y −40.21–40.43, Z −0.002–182.97 cm → Unreal (X, −Y, Z) | X 0.190–7.902, Y −40.428–40.207, Z −0.002–182.972 cm | PASS (≪ 1 cm) |
| Pivot / frame | origin at lower centre on X = 0, +X out, +Z up | origin (0,0,0); `SM_IV02_AxisMarkers`: +X marker to 26 cm, +Y marker to **−51** cm, +Z marker to 201 cm → Unreal = (X, −Y, Z) | PASS |
| Ivy topology | 33,516 tris / 21,793 verts | source model 33,516 / 21,793; Nanite 33,516 tris | PASS |
| Ivy per-corner round trip | positions 1e-4 m, normals 1°, UV 1e-5, colour 1/255 | 100,548/100,548 corners matched: position ≤ 8.5e-6 cm, normals ≤ 9.5e-6°, UV ≤ 3.0e-8, colour ≤ 1.0/255 against the **linear** reference (sRGB-encoded comparison is 74/255 off, so the linear interpretation is the one stored); R/G/B channel correlations 0.09–0.16 | PASS |
| Ivy material slot | exactly one `IvyAtlas` | `IvyAtlas` → `MI_Ivy_DefaultLit` | PASS |
| Ivy collision / navigation | none | 0 simple primitives; `has_navigation_data` false; component NoCollision | PASS |
| Ivy Nanite | standard Nanite, no WPO, no voxel/assembly | enabled; shape preservation NONE (`_PreserveArea` variant: PRESERVE_AREA); `VOXELIZE` not used; materials have no WPO input | PASS |
| Atlas textures | BC sRGB, Normal linear (OpenGL → flip green), Roughness linear | BC sRGB/Default; Normal linear/NormalMap/**Flip Green**; Roughness linear/Grayscale; all 2048² | PASS |
| Facade bounds | tight 904.0 × 280.0 × 440.0 cm | X −449.0–455.0, Y −60.0–220.0, Z −20.0–420.0 cm | PASS |
| Facade per-corner round trip | as above | 353,004/353,004 corners: position ≤ 7.1e-4 cm, normals ≤ 0.0022°, UV0/UV1 ≤ 3.6e-6, material index equal on 117,668/117,668 triangles | PASS |
| Facade slots | six source names in source order | Interchange sanitised them (`HE_PBR01___Glass`) → **repaired** to the source names (`HE PBR01 \| Glass` …); `imported_material_slot_name` keeps the sanitised name (read-only) | PASS after repair |
| Facade materials | existing hotel instances, originals unchanged | `MM01/Instances/MI_HE_HE_PBR01_{Limestone,Brick,Interior,Limestone_relief_00,Glass,Iron}` read-only; the 11 delivered facade textures are byte-identical to the sources of the `OPT01` textures those instances use | PASS |
| Facade collision | test-only | complex-as-simple (inspection traces) | PASS |

**Unreal-side repair (in scope, recorded):** with the translucent glass slot present the engine logs *Invalid material
[MI_HE_HE_PBR01_Glass] used on Nanite static mesh* and the Nanite mask view shows the **whole facade on the non-Nanite
fallback** (`evidence/editor_vis/` before/after). The hotel splits glass into separate meshes (52 of the 69 `OPT01` glass
meshes are non-Nanite). The fixture therefore draws `SM_IV02_FacadeBay_Opaque` (imported geometry minus the 40 glass
triangles, Nanite, five opaque slots) plus `SM_IV02_FacadeBay_Glass` (the 40 triangles, non-Nanite, hotel glass). Per-corner
check: opaque 352,884/352,884 and glass 120/120 corners equal the source (normals ≤ 0.0022°), together 117,668 triangles.
`SM_IV02_FacadeBay` itself stays exactly as imported. After the split the reopen log has no Nanite material warning and
Map Check reports 0 errors / 0 warnings.

**Substrate route (installed build, read back from generated HLSL, `materials/*_nanite_basepass_header.txt`):**
`r.Substrate = 1`, `r.Substrate.ProjectGBufferFormat = 0`. Both ivy materials compile with `SUBSTRATE_ENABLED 1`,
`SUBSTRATE_GBUFFER_FORMAT 0` (Blendable GBuffer), `MATERIAL_IS_SUBSTRATE 0`, `MATERIALBLENDING_SOLID 1`, `MATERIAL_TWOSIDED 1`,
`USES_WORLD_POSITION_OFFSET 0`. Default Lit = `MATERIAL_SHADINGMODEL_DEFAULT_LIT`; Two Sided Foliage =
`MATERIAL_SHADINGMODEL_TWOSIDED_FOLIAGE`, shading model id 6 with back-face lighting (`GetShadingModelRequiresBackfaceLighting`),
SubsurfaceColor written to `PixelMaterialInputs.Subsurface`. So on this project the legacy shading models are encoded
directly in the blendable GBuffer; no Substrate slab graph is involved. Compile diagnostics: 0 errors, 3 textures
referenced; pixel instructions 225 (DL) / 239 (TSF). No project setting was changed (a session-only
`r.DumpShaderDebugInfo` was set and reset to 0).

Source defects returned: **none**. IV02-A exports matched the contract.

## B2 Fixture and reproduction

- `L_IvyPrototype` is non-World-Partition (created with `new_level(..., is_partitioned_world=False)` on a deferred
  post-tick; world partition readback `None`). Saved, closed with the editor, reopened: Map Check 0/0, every component,
  mesh, mobility, instance count, bookmark and light identity read back unchanged (`fixture/fixture_state_after_reopen.json`).
- Facade: 32 bays of the extracted MS02 geometry (window exclusion, corner pedestal/shaft and plinth ledge visible in
  `runs/visual/shots/*view1*`, `*view4*`), identical in A–D. Instances: A 0, B 2, C 64, D 128 ivy patches.
- **Patch count revised from the packet's 4 to 2 per bay (measured).** Dense footprint traces (5 cm grid over the rigid
  80.6 × 183 cm occupied footprint; depth ±1.5 cm of the wall plane, normal ≤ 10°, brick/limestone only) find one
  supporting surface: the 102 cm brick strip right of the grand window (x 276–378, z 55–420 cm). The 60 cm strip between
  the window lights and the corner returns fail (cross frames/glass or protrusions). Two stacked placements fit
  (low on the plinth ledge z 55.0; high at z 236, top 418.97 < 420, 1.5 cm overlap); lateral window xc 316–322 cm, frozen
  at 319. All 130 placements (B 2, C 64, D extra 64) pass with 0 failures, re-checked after the facade split.
- D's second layer: same supported footprints jittered dx ±3 cm, dz 0–2 / −2–0 cm, seed 24024 (stress of overlap, not
  a hotel prediction). C/D are a representative stress setup, not a full-hotel prediction.
- Lights: audit 2 lights, 0 errors, 0 warnings, after placement and again after reopen.
- Cameras (frozen; full transforms in `fixture/fixture_state_after_reopen.json` and every driver log): first person
  (319, −49, 150) yaw 90; oblique (126, −230, 170) p 8.41 y 47.93 (**reframed** after visual pass 1: from (40, −110, 165) the
  window frame and pilaster hid the strip); courtyard (319, −1500, 150) p 2.67 y 90; distant (319, −6000, 160) p 0.57 y 90;
  dense (300, −120, 200) p 17.47 y 80.70. FOV 90°, aspect unconstrained, project default near clip.
- Other fixture repairs during the build, each re-verified: profile-less celestial sun driven to 0 lux by the lighting
  Director (fixture re-asserts it; finding below); stale per-instance overrides after Blueprint changes (instance
  replaced); components switched to **Static** mobility (hotel parity; Preserve Area moved to `*_PA` components because
  Static meshes cannot be swapped at runtime).

## B3 Rendering (literal findings; no visual verdict claimed)

- **Default Lit vs Two Sided Foliage** (config B, presets front / back / local, views 0.45 m / oblique / dense;
  `runs/visual/sheets/cfgB_*`, pixel statistics `analysis/visual_pairs.json`): the two are hard to tell apart in all
  three lighting conditions. Mean absolute difference 0.19–1.14 /255, 0.04–2.3 % of pixels differ by more than 8/255
  (these include TSR temporal noise between separate captures). Reason: the wall is directly behind the leaves, so light
  from behind is blocked; the contre-jour preset (sun along the wall, EV100 12.5) lights edges and grazing faces only.
  Two Sided Foliage's transmission is an artistic approximation, not physically correct transmission; it adds 14 pixel
  instructions and was not separately timed (all timing runs use Default Lit).
- **Preserve Area on/off** (config C; stills at oblique/courtyard/distant and the 44 s route as a fixed-timestep frame dump,
  660 frames each, `runs/video_cfgC_PA{0,1}/*.mp4`, side by side `runs/video_cfgC_PA_side_by_side.mp4`): every 5th frame
  compared, mean difference 0.17/255, at most 0.32 % of pixels differ by > 8/255; temporal activity (mean frame-to-frame
  difference) 8.58 vs 8.59. Those whole-frame statistics hide the ivy, which is a small share of the frame; the direct
  temporal review below supersedes the earlier "no retention difference" reading. Mesh readback
  tradeoff: Preserve Area grows the render bounds to X −0.14–11.68, Z −3.70–183.05 cm (vs 0.19–7.90, 0–182.97) — its
  coarse clusters extend 1.4 mm behind the wall plane and 3.7 cm below the root — and changes the fallback (3,716 vs
  3,831 tris).
- **Direct temporal review of the route (rework after verification, 25 Oct; `Content/Python/WhispersTests/IV02/temporal_review.py`,
  output `analysis/temporal_review/`):** all three MP4s decode without errors (h264, 660 frames, 15 fps, 44.0 s; side by
  side 3840×1080). Looked at: a contact sheet of the side-by-side video every 2 s (`sbs_every2s_sheet.jpg`), 8 consecutive
  frames at mid range (14 s) and at 0.45 m (30 s) for each setting, and the lossless PNG frames at 60 m (6–7 s).
  - **Retention: Preserve Area keeps ivy visible at distance; without it the ivy disappears.** Ivy-green pixels
    (G > R+10 and G > B+10, minus the same view's config A count as baseline) in the fixed stills: oblique 3 m
    37,615 off / 37,296 on (equal); courtyard 15 m 5,581 off / 9,344 on (×1.67); distant 60 m **18 off / 1,043 on** — with
    Preserve Area off, the 60 m view is almost the same as A (`still_view3_distant_60m_A_PA0_PA1_crop.jpg`,
    `still_view2_courtyard_15m_A_PA0_PA1_crop.jpg`). Along the route, PA on has more green pixels than off for most
    of the first 15 s (distant/approach, +500 to +3,066 px); after that the two are about the same (route has no A
    baseline, so these are only absolute differences).
  - **Popping / shimmer:** no ivy pop, flicker or shimmer found in the consecutive-frame strips, with either setting.
    The second-difference residual (|F[t] − (F[t−1]+F[t+1])/2|) is the same for off and on (mean 6.876 vs 6.880 /255,
    largest per-frame difference 0.042/255). Its value is dominated by parallax, so it cannot detect shimmer below about
    2/255. The single flagged frame (43.87 s, both settings) is a **capture artefact, not ivy**: the last dumped frame is
    after the sequence ends, and the view cuts to a fixed camera (`end_route_last2_PA0.jpg`).
  - Missing evidence: Preserve Area was not timed (all timing runs use Preserve Area off), and the route was not captured for
    B/D or A. A Preserve Area cost/benefit decision for the kit needs a timed PA-on run.
- **Nanite overdraw** (editor viewport, `evidence/editor_vis/cfg{A,B,D}_dense_nanite_overdraw.png`,
  `cfgD_distant_nanite_overdraw.png`): the facade itself shows layered architecture overdraw in A; one ivy layer (B) is
  mostly low; D's second layer creates hot spots where leaves of the two layers coincide. No zero-overdraw claim.
- **Shadows:** ivy casts real VSM shadows from the sun (`evidence/editor_vis/cfgD_dense_vsm_vpage.png`, lit shots show
  leaf shadows on brick); the lamppost (MegaLights, ray-traced shadows per its profile) is a separate local-light route.
  VSM cache visualisation shows every page tinted "Dynamic Invalidated" in editor and PIE, before and after switching the
  fixture to Static mobility (`r.Shadow.Virtual.Cache 1`, `Cache.StaticSeparate 0` project settings); recorded, cause not
  asserted. Fallback mesh settings (auto target, 3,831 tris) are separate from VSM.
- **Simplified shadow casters (E): not run** — GPU evidence does not identify VSM shadow rendering as material
  (`GPU/ShadowDepths` delta ≤ 0.01 ms in every view).
- Not run: POM, voxel foliage, masked/translucent leaves (out of scope by contract).

## B4 Performance evidence (workstation series)

Route: Standalone Game, uncooked (`UnrealEditor.exe Whispers.uproject /Game/Whispers/Tests/HotelEden/IV02/L_IvyPrototype -game
-windowed -ResX=1920 -ResY=1080 -WinX=-1920 -WinY=0 -nosplash -NoLoadingScreen -csvGpuStats -abslog=... -IV02Plan=<run>
-ExecCmds="py import WhispersTests.IV02.iv02_autorun"`; exact command line, plan, host state before/after and artefact
hashes in each `runs/<run>/run_manifest.json`). Packaged Development was not used (a scoped cook/package needs shared
Config/target changes). The editor was **closed** for the 12 timing runs. Startup settings applied and read back per run
(`driver_log.json`): `r.SetRes 1920x1080wf` (viewport read back 1920×1080), VSync 0, `t.MaxFPS` 0, `scalability 2`
(High: all `sg.*` = 2, `sg.ResolutionQuality` 87 by the scalability preset while `r.ScreenPercentage` = 100 is read back),
TSR (`r.AntiAliasingMethod 4`), dynamic resolution off, `t.IdleWhenNotForeground 0`. Lighting preset `front`, Default
Lit, Preserve Area off. Measurement: CSV Profiler with GPU stats; one process per (repetition, configuration); orders
r1 A→B→C→D, r2 D→C→B→A, r3 B→A→D→C. Per process: traversal 1 (cold: first route after process start, nothing warmed
away), traversal 2 (warm), then for each fixed view a 30 s warm-up capture and a 120 s steady capture (1 s gap), then
`memreport -full`. A shader/DDC preparation run (`runs/prep_shaders`) touched every configuration first; no recook or
geometry change between paired runs. Insights CPU+GPU+frame traces are separate diagnostic runs
(`traces/insights_*.utrace`, ~0.9 GB each, recorded but not used for the numbers below).

Stabilisation (from the warm-up captures, not assumed): texture streaming pool settles during warm-up and is constant
through every steady capture with `PendingStreamInData` 0; `NaniteStreaming/RootAllocationMB` constant at 16; shader count
constant (≈481) and `PSO/PSOMisses` 0 throughout steady captures.

Bound regime: **render-thread bound in every capture** (RT ≈ 4.3–5.2 ms, GPU 3.0–3.8 ms, game thread ≈ 1.2 ms;
CPU and GPU times overlap and are not summed). Sample counts: ≈ 69,000–80,000 frames per steady view per configuration
(3 × 120 s pooled), ≈ 26,000–27,000 per traversal type.

Pooled raw percentiles (3 repetitions pooled, nearest-rank; ms):

| capture | cfg | n | frame p50 | p95 | p99 | max | GT p50 | RT p50 | RHI p50 | GPU p50 | GPU p95 | NaniteVis p50 | NaniteBase p50 | ShadowDepths p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| traversal1_cold | A | 26563 | 4.94 | 6.05 | 7.80 | 38.66 | 1.27 | 4.87 | 1.74 | 3.55 | 3.86 | 0.230 | 0.163 | 0.310 |
| traversal1_cold | B | 26256 | 5.01 | 6.09 | 7.74 | 42.99 | 1.28 | 4.94 | 1.77 | 3.64 | 3.92 | 0.236 | 0.165 | 0.310 |
| traversal1_cold | C | 26219 | 5.04 | 6.13 | 7.83 | 41.35 | 1.28 | 4.96 | 1.73 | 3.65 | 3.94 | 0.235 | 0.164 | 0.310 |
| traversal1_cold | D | 26068 | 5.05 | 6.06 | 7.84 | 47.65 | 1.27 | 4.98 | 1.74 | 3.69 | 3.96 | 0.239 | 0.165 | 0.307 |
| traversal2_warm | A | 26945 | 4.91 | 5.95 | 7.18 | 32.40 | 1.27 | 4.83 | 1.75 | 3.55 | 3.85 | 0.230 | 0.162 | 0.310 |
| traversal2_warm | B | 26759 | 4.97 | 5.92 | 6.99 | 31.92 | 1.23 | 4.89 | 1.74 | 3.64 | 3.90 | 0.236 | 0.164 | 0.310 |
| traversal2_warm | C | 26749 | 4.99 | 5.91 | 7.19 | 35.45 | 1.23 | 4.90 | 1.70 | 3.66 | 3.92 | 0.236 | 0.164 | 0.310 |
| traversal2_warm | D | 26491 | 5.03 | 5.99 | 7.24 | 30.58 | 1.25 | 4.95 | 1.75 | 3.68 | 3.95 | 0.238 | 0.164 | 0.307 |
| view0_first_person_045m | A | 74030 | 4.81 | 5.57 | 6.01 | 34.34 | 1.18 | 4.80 | 1.62 | 3.39 | 3.46 | 0.229 | 0.223 | 0.380 |
| view0_first_person_045m | B | 71609 | 4.99 | 5.73 | 6.15 | 31.76 | 1.16 | 4.97 | 1.63 | 3.61 | 3.68 | 0.245 | 0.246 | 0.387 |
| view0_first_person_045m | C | 71255 | 5.01 | 5.77 | 6.22 | 30.08 | 1.17 | 5.00 | 1.62 | 3.64 | 3.71 | 0.245 | 0.245 | 0.388 |
| view0_first_person_045m | D | 70159 | 5.09 | 5.83 | 6.28 | 30.45 | 1.19 | 5.08 | 1.63 | 3.73 | 3.80 | 0.259 | 0.248 | 0.379 |
| view1_oblique_3m | A | 70135 | 5.11 | 5.82 | 6.44 | 58.61 | 1.16 | 5.09 | 1.70 | 3.75 | 3.82 | 0.265 | 0.170 | 0.311 |
| view1_oblique_3m | B | 69718 | 5.15 | 5.80 | 6.38 | 35.65 | 1.12 | 5.13 | 1.71 | 3.79 | 3.85 | 0.268 | 0.172 | 0.310 |
| view1_oblique_3m | C | 69195 | 5.19 | 5.81 | 6.41 | 34.73 | 1.15 | 5.17 | 1.68 | 3.82 | 3.89 | 0.269 | 0.171 | 0.310 |
| view1_oblique_3m | D | 68831 | 5.21 | 5.86 | 6.44 | 34.34 | 1.14 | 5.19 | 1.70 | 3.84 | 3.90 | 0.270 | 0.172 | 0.304 |
| view2_courtyard_15m | A | 75598 | 4.52 | 6.68 | 8.16 | 36.16 | 1.18 | 4.49 | 1.75 | 3.29 | 3.36 | 0.216 | 0.108 | 0.292 |
| view2_courtyard_15m | B | 75690 | 4.50 | 6.70 | 8.20 | 32.43 | 1.16 | 4.47 | 1.74 | 3.30 | 3.36 | 0.217 | 0.109 | 0.292 |
| view2_courtyard_15m | C | 74677 | 4.56 | 6.81 | 8.28 | 32.07 | 1.18 | 4.53 | 1.76 | 3.34 | 3.40 | 0.218 | 0.109 | 0.292 |
| view2_courtyard_15m | D | 75120 | 4.55 | 6.85 | 8.22 | 33.24 | 1.16 | 4.51 | 1.73 | 3.34 | 3.41 | 0.217 | 0.109 | 0.291 |
| view3_distant_60m | A | 79706 | 4.29 | 6.07 | 7.44 | 36.24 | 1.17 | 4.28 | 1.76 | 3.01 | 3.07 | 0.202 | 0.079 | 0.275 |
| view3_distant_60m | B | 79573 | 4.30 | 5.99 | 7.28 | 33.55 | 1.16 | 4.29 | 1.76 | 3.00 | 3.07 | 0.202 | 0.079 | 0.278 |
| view3_distant_60m | C | 79729 | 4.29 | 6.02 | 7.35 | 32.51 | 1.15 | 4.28 | 1.75 | 3.01 | 3.07 | 0.202 | 0.080 | 0.276 |
| view3_distant_60m | D | 79014 | 4.35 | 5.98 | 7.26 | 32.98 | 1.18 | 4.34 | 1.79 | 3.01 | 3.07 | 0.202 | 0.080 | 0.273 |
| view4_dense_overlap | A | 71494 | 5.02 | 5.72 | 6.30 | 35.93 | 1.15 | 4.99 | 1.72 | 3.66 | 3.72 | 0.231 | 0.210 | 0.334 |
| view4_dense_overlap | B | 70592 | 5.08 | 5.77 | 6.36 | 45.26 | 1.12 | 5.06 | 1.73 | 3.73 | 3.79 | 0.234 | 0.220 | 0.334 |
| view4_dense_overlap | C | 69930 | 5.14 | 5.78 | 6.35 | 32.45 | 1.14 | 5.11 | 1.71 | 3.76 | 3.82 | 0.234 | 0.220 | 0.333 |
| view4_dense_overlap | D | 69750 | 5.15 | 5.77 | 6.33 | 33.09 | 1.15 | 5.13 | 1.72 | 3.78 | 3.85 | 0.235 | 0.222 | 0.327 |

Paired deltas against A (same repetition, same capture; r1 / r2 / r3):

| capture | cfg | frame p50 | frame p95 | frame p99 | GPU p50 | GPU p95 | NaniteVis p50 | ShadowDepths p50 | VRAM MB p50 |
|---|---|---|---|---|---|---|---|---|---|
| traversal1_cold | B | +0.04 / +0.08 / +0.08 | -0.05 / +0.04 / +0.12 | -0.27 / +0.15 / +0.02 | +0.08 / +0.10 / +0.08 | +0.05 / +0.07 / +0.06 | +0.01 / +0.01 / +0.01 | -0.00 / -0.00 / +0.00 | -2.22 / -0.16 / +13.12 |
| traversal1_cold | C | +0.07 / +0.13 / +0.11 | +0.02 / +0.10 / +0.10 | -0.06 / +0.20 / -0.07 | +0.10 / +0.11 / +0.10 | +0.07 / +0.08 / +0.08 | +0.00 / +0.01 / +0.00 | -0.00 / -0.00 / +0.00 | +0.66 / +3.41 / +2.53 |
| traversal1_cold | D | +0.11 / +0.15 / +0.09 | -0.10 / +0.08 / +0.04 | -0.07 / +0.31 / -0.04 | +0.14 / +0.14 / +0.14 | +0.09 / +0.11 / +0.11 | +0.01 / +0.01 / +0.01 | -0.00 / -0.00 / -0.00 | +3.28 / -2.62 / +2.88 |
| traversal2_warm | B | +0.07 / +0.08 / +0.04 | -0.11 / +0.04 / -0.05 | -0.53 / +0.12 / -0.10 | +0.09 / +0.09 / +0.08 | +0.05 / +0.06 / +0.05 | +0.01 / +0.01 / +0.01 | -0.00 / -0.00 / +0.00 | +1.56 / -3.94 / +13.12 |
| traversal2_warm | C | +0.06 / +0.09 / +0.09 | -0.04 / -0.06 / -0.04 | -0.12 / +0.22 / -0.03 | +0.11 / +0.11 / +0.11 | +0.07 / +0.08 / +0.07 | +0.01 / +0.01 / +0.01 | +0.00 / +0.00 / +0.00 | +4.19 / +2.62 / -1.00 |
| traversal2_warm | D | +0.11 / +0.14 / +0.12 | +0.02 / +0.05 / +0.04 | +0.05 / +0.20 / -0.06 | +0.12 / +0.13 / +0.15 | +0.08 / +0.10 / +0.11 | +0.01 / +0.01 / +0.01 | -0.00 / -0.00 / -0.00 | +6.56 / -6.16 / -0.91 |
| view0_first_person_045m | B | +0.17 / +0.17 / +0.18 | +0.12 / +0.19 / +0.15 | +0.10 / +0.19 / +0.12 | +0.23 / +0.22 / +0.21 | +0.23 / +0.22 / +0.21 | +0.02 / +0.02 / +0.02 | +0.01 / +0.01 / +0.01 | +1.31 / -4.19 / +14.12 |
| view0_first_person_045m | C | +0.20 / +0.20 / +0.21 | +0.15 / +0.22 / +0.23 | +0.10 / +0.26 / +0.27 | +0.26 / +0.25 / +0.24 | +0.25 / +0.25 / +0.24 | +0.02 / +0.02 / +0.02 | +0.01 / +0.01 / +0.01 | +2.94 / +1.38 / -1.00 |
| view0_first_person_045m | D | +0.29 / +0.28 / +0.28 | +0.25 / +0.23 / +0.28 | +0.20 / +0.28 / +0.34 | +0.34 / +0.35 / +0.33 | +0.33 / +0.34 / +0.32 | +0.03 / +0.03 / +0.03 | -0.01 / +0.00 / -0.01 | +6.56 / -6.41 / -0.91 |
| view1_oblique_3m | B | +0.02 / +0.04 / +0.04 | -0.05 / -0.02 / +0.03 | -0.07 / -0.06 / -0.04 | +0.03 / +0.05 / +0.03 | +0.03 / +0.05 / +0.03 | +0.00 / +0.00 / +0.00 | -0.00 / -0.00 / -0.00 | +1.56 / -4.19 / +13.12 |
| view1_oblique_3m | C | +0.05 / +0.10 / +0.08 | -0.04 / -0.00 / -0.01 | -0.03 / -0.02 / -0.02 | +0.06 / +0.09 / +0.06 | +0.06 / +0.08 / +0.07 | +0.00 / +0.00 / +0.00 | -0.00 / -0.00 / -0.00 | +3.94 / +2.38 / -1.00 |
| view1_oblique_3m | D | +0.09 / +0.11 / +0.10 | +0.05 / +0.01 / +0.05 | +0.09 / +0.00 / -0.05 | +0.08 / +0.10 / +0.09 | +0.08 / +0.10 / +0.09 | +0.01 / +0.01 / +0.01 | -0.01 / -0.01 / -0.01 | +6.81 / -5.88 / -0.91 |
| view2_courtyard_15m | B | -0.06 / +0.00 / -0.01 | +0.05 / +0.02 / -0.05 | +0.04 / +0.02 / +0.09 | +0.00 / +0.02 / +0.00 | -0.00 / +0.02 / +0.00 | +0.00 / +0.00 / +0.00 | -0.00 / +0.00 / -0.00 | +1.56 / -4.19 / +7.88 |
| view2_courtyard_15m | C | +0.01 / +0.03 / +0.09 | +0.12 / +0.25 / +0.01 | +0.05 / +0.23 / +0.10 | +0.04 / +0.06 / +0.05 | +0.04 / +0.05 / +0.04 | +0.00 / +0.00 / +0.00 | -0.00 / +0.00 / -0.00 | +3.94 / +2.38 / -6.00 |
| view2_courtyard_15m | D | +0.02 / +0.03 / +0.04 | +0.13 / +0.31 / +0.04 | +0.05 / +0.13 / +0.02 | +0.05 / +0.06 / +0.05 | +0.05 / +0.05 / +0.05 | +0.00 / +0.00 / -0.00 | -0.00 / -0.00 / -0.00 | +6.81 / +0.66 / -2.62 |
| view3_distant_60m | B | -0.00 / +0.03 / +0.01 | -0.04 / -0.10 / -0.12 | -0.15 / -0.16 / -0.18 | -0.01 / +0.00 / -0.01 | -0.01 / +0.00 / -0.01 | +0.00 / +0.00 / +0.00 | +0.00 / +0.01 / +0.00 | +1.31 / +4.19 / +4.44 |
| view3_distant_60m | C | -0.00 / -0.01 / +0.02 | -0.13 / +0.07 / -0.09 | -0.24 / +0.10 / -0.15 | -0.01 / +0.01 / +0.00 | -0.01 / +0.01 / +0.00 | +0.00 / +0.00 / +0.00 | +0.00 / +0.00 / +0.00 | +3.69 / +2.38 / -9.94 |
| view3_distant_60m | D | +0.02 / +0.16 / -0.00 | -0.12 / -0.10 / -0.08 | -0.13 / -0.33 / -0.14 | -0.00 / +0.01 / -0.00 | -0.00 / +0.01 / -0.00 | +0.00 / +0.00 / +0.00 | -0.00 / -0.00 / +0.00 | +6.56 / +0.66 / -6.31 |
| view4_dense_overlap | B | +0.05 / +0.08 / +0.07 | +0.01 / +0.08 / +0.04 | +0.02 / +0.11 / +0.04 | +0.06 / +0.08 / +0.08 | +0.07 / +0.08 / +0.07 | +0.00 / +0.00 / +0.00 | -0.00 / -0.00 / -0.00 | +1.31 / +4.19 / +4.44 |
| view4_dense_overlap | C | +0.09 / +0.12 / +0.14 | +0.00 / +0.07 / +0.11 | -0.00 / +0.09 / +0.05 | +0.10 / +0.11 / +0.11 | +0.10 / +0.10 / +0.10 | +0.00 / +0.00 / +0.00 | -0.00 / -0.00 / -0.00 | +3.69 / +3.69 / -9.69 |
| view4_dense_overlap | D | +0.11 / +0.14 / +0.14 | -0.01 / +0.06 / +0.08 | -0.05 / +0.05 / +0.06 | +0.11 / +0.13 / +0.14 | +0.12 / +0.14 / +0.13 | +0.00 / +0.00 / +0.00 | -0.01 / -0.01 / -0.01 | +6.56 / +0.66 / -6.06 |

Largest per-pass GPU deltas (p50, r1/r2/r3): the ivy cost is mainly **MegaLights** (the lamppost's ray-traced lighting)
and the **ray-tracing scene** (`r.RayTracing.Nanite.Mode = 1` puts full-detail Nanite ivy into the RT scene), not Nanite
rasterisation or VSM:

- view0_first_person_045m B: MegaLights +0.188/+0.190/+0.185; ShadowProjection +0.027/+0.030/+0.027; NaniteBasePass +0.024/+0.024/+0.023; DistanceFieldShadows -0.020/-0.021/-0.023; TemporalSuperResolution +0.016/+0.021/+0.019
- view0_first_person_045m C: MegaLights +0.189/+0.189/+0.183; RayTracingScene +0.042/+0.042/+0.042; ShadowProjection +0.026/+0.030/+0.027; NaniteBasePass +0.024/+0.021/+0.023; TemporalSuperResolution +0.015/+0.023/+0.018
- view0_first_person_045m D: MegaLights +0.241/+0.232/+0.234; RayTracingScene +0.047/+0.047/+0.047; DistanceFieldShadows -0.033/-0.033/-0.034; NaniteVisBuffer +0.030/+0.030/+0.030; NaniteBasePass +0.023/+0.030/+0.026
- view1_oblique_3m B: LumenSceneUpdate +0.010/+0.013/+0.006; ShadowProjection +0.012/+0.012/+0.012; RayTracingScene +0.011/+0.010/+0.011; DistanceFieldShadows -0.003/-0.006/-0.006; TranslucentLighting n/a/n/a/+0.006
- view1_oblique_3m C: RayTracingScene +0.041/+0.041/+0.041; LumenSceneUpdate +0.010/+0.012/+0.006; ShadowProjection +0.012/+0.011/+0.010; MegaLights +0.005/+0.006/+0.011; DistanceFieldShadows -0.005/-0.006/-0.008
- view1_oblique_3m D: MegaLights +0.058/+0.061/+0.063; RayTracingScene +0.046/+0.046/+0.046; LumenSceneUpdate +0.014/+0.016/+0.014; DistanceFieldShadows -0.012/-0.014/-0.015; Lights -0.014/-0.015/-0.014
- view2_courtyard_15m B: Translucency -0.011/-0.008/-0.007; RayTracingScene +0.010/+0.010/+0.010; SkyAtmosphere +0.007/+0.004/+0.005; TemporalSuperResolution -0.003/+0.006/n/a; TranslucentLighting +0.005/+0.001/n/a
- view2_courtyard_15m C: RayTracingScene +0.039/+0.039/+0.039; Translucency -0.012/+0.002/n/a; TemporalSuperResolution -0.002/+0.008/+0.004; SkyAtmosphere +0.008/n/a/+0.002; TranslucentLighting +0.006/n/a/-0.003
- view2_courtyard_15m D: RayTracingScene +0.044/+0.044/+0.044; Lights -0.019/-0.023/-0.021; MegaLights +0.011/+0.016/+0.009; DistanceFieldShadows -0.011/-0.012/-0.011; Translucency n/a/n/a/-0.008
- view3_distant_60m B: MegaLights -0.010/-0.009/-0.014; TemporalSuperResolution -0.003/+0.006/-0.002; ShadowDepths n/a/+0.005/+0.002; FrontLayerTranslucencyGBuffer n/a/n/a/-0.005; DistanceFieldShadows +0.002/+0.004/+0.002
- view3_distant_60m C: TemporalSuperResolution -0.003/+0.009/+0.001; ShadowDepths n/a/+0.004/n/a; MegaLights -0.004/n/a/+0.002; TranslucentLighting +0.003/n/a/+0.001; SkyAtmosphere +0.003/n/a/-0.001
- view3_distant_60m D: TemporalSuperResolution -0.008/+0.007/-0.001; MegaLights +0.002/n/a/-0.005; RayTracingScene +0.003/+0.003/+0.004; DistanceFieldShadows -0.003/-0.003/n/a; TranslucentLighting +0.002/-0.003/+0.002
- view4_dense_overlap B: MegaLights +0.052/+0.052/+0.046; DistanceFieldShadows -0.018/-0.019/-0.018; ShadowProjection +0.016/+0.016/+0.016; RayTracingScene +0.011/+0.011/+0.012; NaniteBasePass +0.009/+0.011/+0.010
- view4_dense_overlap C: MegaLights +0.052/+0.053/+0.057; RayTracingScene +0.041/+0.041/+0.041; DistanceFieldShadows -0.018/-0.020/-0.020; ShadowProjection +0.015/+0.015/+0.014; NaniteBasePass +0.010/+0.010/+0.009
- view4_dense_overlap D: MegaLights +0.091/+0.090/+0.091; RayTracingScene +0.046/+0.046/+0.046; DistanceFieldShadows -0.027/-0.028/-0.028; NaniteBasePass +0.010/+0.015/+0.010; LumenSceneUpdate n/a/n/a/+0.011

Stutter (`analysis/summary.md`, all repetitions): cold traversals have 15–24 frames > 2 × median in **every**
configuration including A (first-use), and 0–2 frames > 33.3 ms (worst 47.6 ms in D r3, 43.9 D r2, 43.0 B r2, 38.7 A r1);
warm traversals 2–5 frames > 2 × median, at most one frame > 33.3 ms. No frame > 50 ms in any B/C/D capture; the only
one is A r3 oblique (58.6 ms). Isolated ≈ 30 ms frames occur about once per capture in every configuration including A.
Memory: local VRAM ≈ 3.69 GB in all configurations; paired differences −10…+14 MB with no consistent sign, i.e. inside
run-to-run variation (inconclusive, not a cost). `RayTracingGeometry/TotalResidentSizeMB` 9.9 in all configurations;
GPU scene instances 69 / 71 / 133 / 197 (A/B/C/D). Counters not emitted on this build/route are reported N/A, never 0:
a separate `GPU/VirtualShadowMaps` pass (VSM work is inside `GPU/ShadowDepths`/`ShadowProjection`), VSM page counts,
CPU clock/temperature (host load and power plan only, in the run manifests).

No linear extrapolation from a patch to the hotel is made: C/D cover 32 bays of one facade crop only.

## B5 Budget (NOT RUN / pending)

No recorded lead decision accepts the proposed budget, and no RTX 3060 run exists, so target acceptance is **NOT RUN**.
For information only, the workstation series against the *proposal*: worst paired median GPU delta +0.35 ms (D, 0.45 m)
vs ≤ 1.0 ms; worst steady frame p95 6.85 ms / p99 8.28 ms vs ≤ 16.67 / ≤ 20.0 ms; worst traversal p99 7.84 ms vs ≤ 25 ms;
no ivy-attributable frame > 50 ms; additional VRAM not distinguishable from noise vs ≤ 256 MiB. These RX 7900 XTX numbers
cannot certify an RTX 3060; the scene is render-thread bound here, and the dominant ivy cost (MegaLights / RT scene)
scales with GPU ray-tracing throughput.

## B6 Visual gate (Jason)

Pending. Review set: `runs/visual/sheets/cfg{A,B,C,D}_front_DL.jpg` (all five views per configuration),
`cfgB_{front,back,local}_{DL,TSF}.jpg`, `cfgC_front_DL_PA{0,1}.jpg`, the route videos, and the reference comparisons
from IV02-A (`SourceAssets/HotelEden/IV02/qa/A2_compare_*.png`). Rejected/superseded evidence is kept:
`runs/superseded_visual_pass1_nonNanite_facade` (non-Nanite facade, wrong oblique framing), `runs/superseded_prep_pass*`,
`evidence/editor_vis/superseded_*`, `evidence/editor_vis/cfgD_dense_vsm_cache_movable_components.png`.

Manual review: open `L_IvyPrototype`, select `IV02_Benchmark`, choose `Configuration` (A–D), `UsePreserveArea`,
`StartBookmark` (0 first person, 1 oblique, 2 courtyard, 3 distant, 4 dense) or `AutoPlayRoute`, press Play; in PIE
`ke * IV02View 3`, `ke * IV02Config 2 0`, `ke * IV02Route`. Inspect leaves, window exclusion, corner pedestal and ledge.

## Findings for the lead

1. **Lighting system (not changed; outside the touch list):** a celestial sun with `WhispersLightComponent` identity and no
   profile is driven to 0 lux / 2700 K at BeginPlay (the Director drives every light on the owner from the profile). E2K
   hides this because Ultra Dynamic Sky rewrites its sun each frame; any other level with a celestial-tagged sun goes dark.
2. **Glass on Nanite:** a translucent slot forces a whole mixed mesh onto the non-Nanite fallback (17 of the hotel's 69
   `OPT01` glass meshes are flagged Nanite; worth a check in the hotel).
3. **Patch support:** this bay supports only 2 rigid 1 × 2 m patches; the kit continuation needs narrower patches or
   corner/pillar variants to cover the 60 cm strips and returns.
4. **Cost drivers:** with this project's lighting, ivy cost is MegaLights + RT scene (`r.RayTracing.Nanite.Mode = 1`), not
   Nanite raster or VSM. Relevant to the RTX 3060 target and to the lighting guide's note that mode 1 is "offline-only".
5. **Scope conflict (B7), resolved by IV02-r2:** the IV02-r1 touch list included the Workspace IV02 tab, outside the
   job's Whispers-only workspace; verification on 25 Oct failed B7 for that reason alone. The lead's IV02-r2 decision
   (25 Oct) removed the tab from IV02-B scope: this report plus `Saved/IV02/evidence_index.json` are the delivery. The
   Workspace tab was not written and is not required.
6. Baseline drift: engine 5.8.4-58902052 (packet: 5.8.2-56702186).

## B7 Delivery

Delivered paths (scoped commit; SHA in the hand-off comment): `Content/Whispers/Presentation/Environment/HotelEden/IV02/**`
(9 packages), `Content/Whispers/Tests/HotelEden/IV02/**` (9 packages incl. `L_IvyPrototype.umap`; non-WP, no external actor
packages), `Content/Python/WhispersTests/IV02/*.py`, `docs/features/hotel-eden-ivy-iv02.md`, `docs/verification/ivy-IV02-B.md`,
the IV02 row of `docs/credits-log.md`. Largest committed file 8.6 MB (`SM_IV02_FacadeBay`; `SM_IV02_FacadeBay_Opaque` 6.5 MB).

Kept local (size), under `Saved/` (never committed): 12 distant-view CSVs of 53–55 MB each
(`runs/timing_r*_*/csv/*__view3_distant_60m.csv`) and 4 Insights traces of 0.91–0.92 GB (`traces/insights_{A,B,C,D}.utrace`);
the whole `Saved/IV02` set is indexed with sizes and SHA-256 in `Saved/IV02/evidence_index.json`.

Evidence index (IV02-r2 reconciliation, 25 Oct). The earlier index listed 473 files (8.30 GB) but omitted the 1,320
lossless route frames `runs/video_cfgC_PA{0,1}/shots/*.png` (3.16 GB) that the MP4s and the B3 temporal review are built
from, and the scratch `report_body.md`. All 473 earlier files re-hashed identical; nothing was recaptured. The index is
now generated by `Content/Python/WhispersTests/IV02/build_evidence_index.py`: **1,794 files, 11,460,553,184 bytes**,
every file under `Saved/IV02` except the index itself. Verify with
`python Content/Python/WhispersTests/IV02/build_evidence_index.py --check` (exit 0: every row present, size and SHA-256
equal, no unindexed file). Index file SHA-256 at delivery:
`d76299f8a8041fcb7d8d2a8fddf77379185a48fd9e85ab6a938e5d90e9fbcab8`.

Delivery commits: `c9b1b16` (fixture, assets, scripts, report), `2b8dcfc` (B3 temporal-review correction), and the
IV02-r2 reconciliation commit (this B7 text and the index builder; SHA in the hand-off comment).

Not claimed: full kit, PCG, hotel installation, RTX 3060 performance, visual acceptance.

