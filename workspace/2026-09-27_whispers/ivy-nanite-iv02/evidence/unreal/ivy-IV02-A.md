# #113 IV02-A: Blender opaque ivy prototype and facade export (packet IV02-r2)

Specialist: blender-artist seat. Lock `asset:ivy-IV02-source`. This milestone covers
export readiness only: the ivy source and FBX and the read-only MS02 facade fixture FBX.
Unreal import, appearance, performance and PCG belong to #114 and are **NOT RUN** here.

Route: separate headless Blender 5.2.1 LTS processes (`--factory-startup --disable-autoexec`),
external working folder `D:/AI_Modelling/hotel_eden/working/ivy_IV02/`. No live Blender and
no Unreal editor were used, nothing was written under `Content/`, and the master was never saved.
The delivered copy is `SourceAssets/HotelEden/IV02/`. Every path below is relative to that folder.

## What IV02-r2 changed, and what the new comparison found

The r1 verifier blocked closure for two reasons. The facade round trip compared only counts,
bounds, slot order and UV layer names, and nothing had been delivered to Whispers.

The new per-corner work exposed a real facade defect, not only a gap in the evidence. All 62 source
objects carry custom split normals, and 53 also have sharp edges. The r1 `export_facade.py`
rebuilt the clipped fixture from positions and UVs only, so Blender re-averaged the normals
across hard corners. On intact source polygons, 6,897 corners were more than 1° away from the
source's own normals, with a maximum of 167°. The worst cases were plinth bases
(`E01_E_A08_BASE_*`), corner pedestals and window structures, which would have shaded as soft
blobs in Unreal.

**Repair.** `scripts/export_facade.py` now does the following for each source object:
1. Reads the object's evaluated `corner_normals` and moves them to world space (inverse-transpose).
2. Carries them through the bisect clip as a loop layer.
3. Re-applies them to the fixture with `normals_split_custom_set`.

No geometry, UV, material or selection logic changed. The re-export has the same 59,617
vertices, 117,668 triangles, slot order and bounds. The FBX hash changed to `df553515…` and the
size to 16,606,892 B. Measured on 347,129 corners of 115,702 intact source polygons, the fixture
now matches the source normals with a maximum of 0.040° (custom-normal encoding precision) and
zero UV0/UV1 difference (`qa/facade_baseline.json` → `source_fidelity`). The ivy `.blend` and
ivy FBX are byte-identical to r1.

## A1 Source preservation — PASS

- The master `D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend` is unchanged:
  - 2,671,407,245 B, mtime 2026-10-19 22:44:44.3937821 +08.
  - SHA-256 `4ea301be7d39a0a8f463547194bb174b660870e9b99091469899fdd1cb7ad5ff`, identical in four
    records: r1 before/after (`qa/master_before.txt`, `qa/master_after.txt`) and r2 before at
    10:05:10Z and after at 10:10:33Z (`qa/master_before_r2.txt`, `qa/master_after_r2.txt`). The r2
    pair spans all three r2 master processes (re-export and two baseline runs).
  - Each process reports `master_is_dirty_in_memory: false` and `saved_blend: false`.
- The live crop selection equals the frozen 62 names, and all six landmarks survive clipping
  (`qa/facade_export.json` → `selection_matches_frozen`, `landmarks`). That file records the crop
  box, per-object world matrices, the source→fixture matrix (translation −3.55, −1.8, 0) and the
  Unreal conversion (cm = (X, −Y, Z) × 100, rotations conjugated by diag(1,−1,1)).
- The ivy `.blend` reopens with editable `IV02_Stems` (CURVES, 53 curves / 463 points) and GN
  `IV02_IvyGrowth` (82 nodes). Its evaluation equals the 33,516-triangle export. It holds 11
  objects, 1 material and no hotel data (`qa/reopen_verify.json`). Unchanged since r1 (same SHA-256).

## A2 Geometry/look — PASS for export readiness (accepted by the r1 verifier, unchanged)

- The triangulated export has 33,516 triangles and 21,793 vertices: about 233 open, opaque,
  single-sided cordate leaves (blade 5.2–8.3 cm, cupped), arched petioles, 3 woody stems,
  50 branches/twigs and a young leaf on every tip. No vertex lies behind the wall plane
  (`qa/ivy_build.json`).
- Comparisons: `qa/A2_compare_close.png` and `qa/A2_compare_wall_scale.png` show the reference,
  the accepted IV01 and the actual FBX on the MS02 bay. Close views are in `renders/IV02_*close*.png`.
- Eleven visible defects were repaired in r1. Recorded remaining mismatches: the reference is a
  mature continuous mat (this is one open patch), its leaves are rounder, it has warm grading,
  and leaf outline segments are visible at ≤ 0.5 m. Jason's subjective verdict is reserved for
  the Unreal milestone.

## A3 Asset attributes — PASS (unchanged)

- **Frame.** Origin (0,0,0) on X = 0, identity matrix, +X out of the wall, +Z up.
- **Bounds.** Tight bounds X 0.19–7.90, Y −40.21–40.43, Z −0.002–182.97 cm, inside the nominal 25 × 100 × 200 cm.
- **Material and collision.** One slot `IvyAtlas`, one `UVMap`, no collision.
- **Atlas.** 2048², all UV corners inside a 16 px inset, gutters 23–24 px.
- **Maps.** BaseColor sRGB, Normal linear OpenGL +Y (Unreal: flip green), Roughness linear, no alpha (`qa/atlas_report.json`).
- **Vertex colour.** `Color` CORNER, exported linear: R cavity, G growth, B tip, A = 1. Channel |r| ≤ 0.16 (`qa/mask_RGB_strip.png`, `renders/IV02_mask_*.png`).
- **Facade.** Six slots in source order: Limestone, Brick, Interior, Limestone | relief 00, Glass, Iron.
  - The 11 original textures are copied as raw bytes (`exports/facade-textures/`).
  - The facade samples UV1 `SurfaceMetres` through per-object `he_uv1*` affines, all identity, plus UV0 `BakeAtlas` for relief.
- **Envelope.** Tight size 904.0 × 280.00002 × 440.00003 cm. The `within_envelope: false` flag comes
  from float32 rounding on clip planes that sit exactly on the 280 × 440 cm box edges (0.0002 mm
  over). The geometry is clipped to the contracted box.

## A4 FBX round trip — PASS (both FBXs)

All reimports ran in a fresh factory-startup process with an empty scene and nothing saved.

**Ivy** (`scripts/roundtrip.py`, `qa/fbx_roundtrip.json` → `ivy`):

| Check | Result |
| --- | --- |
| Triangles | 33,516 / 33,516 |
| Vertices | 21,793 / 21,793 |
| Corners compared | 100,548, loop order preserved |
| Max position error | 3.5e-8 m |
| Normal, UV and colour error | 0 |
| Tolerances | 1e-4 m / 1° / 1e-5 / 1/255 |
| Unique split keys | 21,793 |
| Bounds deviation | ≤ 5.4e-7 cm |
| Pivot | 0.0 cm |
| Axis markers | 0.0 cm |

**Facade** (new in r2):
- **Baseline.** `scripts/facade_baseline.py` re-runs `export_facade.py` unchanged in a scratch
  folder. It then triangulates the evaluated, clipped fixture exactly as io_scene_fbx does
  (`new_from_object` + default `bmesh.ops.triangulate`) and dumps per-corner positions, corner
  normals, UVMap and UV1 to `qa/facade_baseline.npz` (SHA-256 `792fdf2b…`).
- **Comparison.** `scripts/roundtrip_facade.py` reimports the delivered FBX and compares every
  corner (`qa/fbx_roundtrip.json` → `facade_per_corner`).

| Check | Result |
| --- | --- |
| Vertices | 59,617 / 59,617 |
| Triangles | 117,668 / 117,668 |
| Corners | 353,004 / 353,004 |
| Correspondence | identity: vertex order and per-triangle corner vertex indices equal the baseline; 0 unmatched |
| Material index per triangle | equal |
| Max position error | 4.4e-7 m (tolerance 1e-4) |
| Corner normals (custom normals imported) | max 0.037°, p99 0.025°, mean 0.0066°, 0 over 1° (353,004 samples) |
| UV0 `UVMap` (source BakeAtlas) | max error 0.0, 353,004 samples (tolerance 1e-5) |
| UV1 `UV1` (source SurfaceMetres) | max error 0.0, 353,004 samples (tolerance 1e-5) |
| Split accounting | 133,084 unique (vertex, normal, UV0, UV1) corner keys: the engine vertex count after splitting |
| Bounds deviation | ≤ 4.8e-5 cm; slot order preserved |

Images of the actual reimported facade mesh are `renders/IV02_facade_roundtrip_clay_wide.png`,
`renders/IV02_facade_roundtrip_clay_plinth.png` (crisp plinth and pedestal corners, which is the
repaired shading) and `renders/IV02_facade_roundtrip_uv1_checker.png` (continuous metre-scale
UV1). The ivy round-trip images are `renders/IV02_roundtrip_front.png` and `renders/IV02_roundtrip_oblique.png`.

## A5 Reproduction and delivery

**Reproduction.** Run each script with Blender 5.2.1 LTS,
`--factory-startup --disable-autoexec -b`; the usage line is in each docstring.
- Ivy: `build_ivy.py`, `ivy_shapes.py` and `bake_atlas.py` (seed 24024) produce the `.blend`,
  atlas and ivy FBX.
- Facade: `export_facade.py` reads the master, `facade-selection.json` (Workspace evidence) and
  the facade FBX.
- Checks: `reopen_verify.py`, `roundtrip.py`, `facade_baseline.py`, `roundtrip_facade.py`,
  `review_master.py`, `compose_review.py`.
- Manifest: `make_manifest.py` (system Python).

FBX export settings are recorded in `qa/facade_export.json` → `fbx.settings` and
`qa/ivy_build.json`.

**Provenance.** The ivy geometry, atlas and masks are original procedural work for this project.
The facade fixture and its 11 textures are existing Hotel Eden MS02/PBR01 assets, copied
unmodified (see `docs/credits-log.md`, 2026-10-24 IV02 entry).

**Delivery set.** 69 files listed in `qa/IV02_file_manifest.json`, plus the manifest itself;
166,674,915 B in total. Excluded are `*.blend1` backups, `logs/` and scratch. The largest file is
`qa/ivy_export_reference.json` at 22,148,492 B. **Kept local (size): none.** No file is 50 MB or
larger. Every delivered file was byte-compared (size and SHA-256) against the manifest after
copying: 0 mismatches, 0 extra files.

**Not run here:** Unreal import, material conversion, Nanite/VSM behaviour, performance, PCG (#114).

## Path inventory

`SourceAssets/HotelEden/IV02/` (bytes, SHA-256 prefix):

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `exports/facade-textures/T_HE_Brick_BC.png` | 1,617,396 | `9e1b22f3773383f4…` |
| `exports/facade-textures/T_HE_Brick_N.png` | 5,470,448 | `aa68fc7b76715ca8…` |
| `exports/facade-textures/T_HE_Brick_ORM.png` | 1,182,455 | `9c2e3306b8b86deb…` |
| `exports/facade-textures/T_HE_Iron_BC.png` | 131,394 | `69de637980c5aeb8…` |
| `exports/facade-textures/T_HE_Iron_N.png` | 495,946 | `f39da2d984aee91c…` |
| `exports/facade-textures/T_HE_Iron_ORM.png` | 1,025,514 | `bd47da3054a6acc4…` |
| `exports/facade-textures/T_HE_Limestone_BC.png` | 5,847,169 | `7e3ce551486788f2…` |
| `exports/facade-textures/T_HE_Limestone_N.png` | 5,961,128 | `e8234dbb5516a97b…` |
| `exports/facade-textures/T_HE_Limestone_ORM.png` | 2,430,734 | `f976ca651e609866…` |
| `exports/facade-textures/T_HE_Relief_00_AO.png` | 7,635,816 | `7b08937df1f416aa…` |
| `exports/facade-textures/T_HE_Relief_00_N.png` | 20,062,710 | `20bb74e4d2a93ada…` |
| `exports/IV02_AxisMarkers.fbx` | 18,124 | `27ccb7f2d7a8e7cd…` |
| `exports/SM_IV02_FacadeBay.fbx` | 16,606,892 | `df5535150b8c4c35…` |
| `exports/SM_Ivy_WallPatch_Prototype.fbx` | 2,709,916 | `b6dfd5744cf8cb34…` |
| `IV02_Ivy_Prototype.blend` | 5,261,497 | `08cdfdbe454e3ab7…` |
| `qa/A2_compare_close.png` | 2,693,823 | `aba659c18be5392a…` |
| `qa/A2_compare_wall_scale.png` | 1,717,503 | `a870781488923482…` |
| `qa/atlas_BaseColor_preview.png` | 761,661 | `1ff94fd9fc5bd60a…` |
| `qa/atlas_footprint_ids.png` | 20,867 | `a8011e3e8ee84b3c…` |
| `qa/atlas_Normal_preview.png` | 762,922 | `ba1da092f9e8ac1d…` |
| `qa/atlas_report.json` | 2,842 | `308c1fca9013c03c…` |
| `qa/atlas_Roughness_preview.png` | 268,205 | `fc7fe144fa04023a…` |
| `qa/facade_baseline.json` | 17,445 | `bf9d84b4864e04da…` |
| `qa/facade_baseline.npz` | 13,597,812 | `792fdf2bbb7097af…` |
| `qa/facade_export.json` | 140,146 | `129d1b5950d5cfb6…` |
| `qa/facade_review.json` | 26,588 | `4efa149e350dbb54…` |
| `qa/fbx_roundtrip.json` | 7,659 | `4db9c72ed055fc06…` |
| `qa/ivy_build.json` | 6,985 | `9199e47e3ca537aa…` |
| `qa/ivy_export_reference.json` | 22,148,492 | `5f66e362bd9310cd…` |
| `qa/mask_RGB_strip.png` | 262,179 | `a3600dc1ea99661f…` |
| `qa/master_after.txt` | 210 | `b75a8b55e9fca32d…` |
| `qa/master_after_r2.txt` | 210 | `c53414c36e1248ac…` |
| `qa/master_before.txt` | 210 | `ed279fdf45c82856…` |
| `qa/master_before_r2.txt` | 210 | `f3b2b9e5965306eb…` |
| `qa/reopen_verify.json` | 2,400 | `2a9fd8ec8972f142…` |
| `renders/IV02_facade_bay_wide.png` | 2,410,853 | `dbadd21450085c1c…` |
| `renders/IV02_facade_close.png` | 3,938,495 | `c7ab96111c1ed752…` |
| `renders/IV02_facade_first_person.png` | 2,878,492 | `3ae0a87bc985a40a…` |
| `renders/IV02_facade_oblique.png` | 3,863,634 | `e38f8cd623d92357…` |
| `renders/IV02_facade_roundtrip_clay_plinth.png` | 1,334,959 | `e303e1d78bdaaebc…` |
| `renders/IV02_facade_roundtrip_clay_wide.png` | 1,375,854 | `6f41fe8ffd48e709…` |
| `renders/IV02_facade_roundtrip_uv1_checker.png` | 1,463,422 | `300ac6fb885d51bc…` |
| `renders/IV02_first_person_1p7m.png` | 2,531,251 | `1f230d93852a8c21…` |
| `renders/IV02_front_close.png` | 3,873,586 | `3ea60cdeca5b2e79…` |
| `renders/IV02_front_full.png` | 2,083,834 | `e59b3d6f047b8920…` |
| `renders/IV02_mask_B.png` | 723,495 | `c0a02bef81513e15…` |
| `renders/IV02_mask_G.png` | 685,518 | `a4726bcc0013cd9d…` |
| `renders/IV02_mask_R.png` | 731,040 | `f46dafc136e6d689…` |
| `renders/IV02_oblique_close.png` | 3,439,938 | `ea5f4750698bfcc6…` |
| `renders/IV02_roundtrip_front.png` | 1,961,519 | `cd68f6732e330fa7…` |
| `renders/IV02_roundtrip_oblique.png` | 1,962,273 | `1984b946e9416904…` |
| `renders/IV02_side_close.png` | 2,583,521 | `d434c5808e8c28a1…` |
| `renders/IV02_side_root.png` | 2,876,280 | `d93728e88a92939d…` |
| `renders/IV02_unlit_basecolor_close.png` | 2,823,683 | `f945af57c8d63f2e…` |
| `scripts/bake_atlas.py` | 8,938 | `70845572453f04ae…` |
| `scripts/build_ivy.py` | 33,448 | `79b8621bccbc6a17…` |
| `scripts/compose_review.py` | 1,907 | `e3c3677ad2ceb291…` |
| `scripts/export_facade.py` | 13,137 | `425a7ac7a36ff834…` |
| `scripts/facade_baseline.py` | 7,618 | `902b2f03b8d2fc64…` |
| `scripts/ivy_shapes.py` | 4,637 | `563bc43722639e68…` |
| `scripts/make_manifest.py` | 1,178 | `366f5b9db812ad96…` |
| `scripts/probe.py` | 1,631 | `049edf78ac631a14…` |
| `scripts/reopen_verify.py` | 7,911 | `b702d281850ee64c…` |
| `scripts/review_master.py` | 8,069 | `e77b8fe42d1a043d…` |
| `scripts/roundtrip.py` | 10,973 | `5e9b4d958806e4c7…` |
| `scripts/roundtrip_facade.py` | 9,017 | `23fd246e10955913…` |
| `textures/T_Ivy_Atlas_BaseColor.png` | 1,823,752 | `ee942486f8dfabc2…` |
| `textures/T_Ivy_Atlas_Normal.png` | 1,832,412 | `0ea4a54a7246d2b1…` |
| `textures/T_Ivy_Atlas_Roughness.png` | 473,132 | `960973872ddddf29…` |
| `qa/IV02_file_manifest.json` | (the manifest itself) | — |

Also delivered: `docs/verification/ivy-IV02-A.md` (this file) and the IV02 row in `docs/credits-log.md`.
