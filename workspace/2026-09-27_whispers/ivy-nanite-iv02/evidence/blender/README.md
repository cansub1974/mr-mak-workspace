# IV02-A — Blender ivy prototype and facade export (#113)

Revision IV02-r1, 24 October 2026. Specialist: Claude (blender-artist), IssueBridge run
a73d1b4e95de4d978416221717050f65. Lock held: `asset:ivy-IV02-source`. Isolated headless Blender
5.2.1 LTS (9e2066aef7ef), `--factory-startup --disable-autoexec`, one process per step. No live
Blender session, no Unreal editor work.

**Status: implemented and self-tested. Awaiting independent verification (A1–A5) and the delivery
owner's copy into Whispers `SourceAssets/HotelEden/IV02/`.** This proves export readiness only. It
does not certify Unreal appearance, performance or PCG placement (#114). Jason's visual verdict
belongs to the Unreal milestone.

## Deliverables (external folder `D:/AI_Modelling/hotel_eden/working/ivy_IV02/`)

| File | Bytes | SHA-256 (first 16) |
| --- | --- | --- |
| `IV02_Ivy_Prototype.blend` (curves + GN + leaf sources + atlas, packed) | 5,261,497 | `08cdfdbe454e3ab7` |
| `exports/SM_Ivy_WallPatch_Prototype.fbx` | 2,709,916 | `b6dfd5744cf8cb34` |
| `exports/SM_IV02_FacadeBay.fbx` | 16,623,148 | `fb89f46d20ca08ec` |
| `exports/IV02_AxisMarkers.fbx` (diagnostic basis markers, not a game asset) | 18,124 | `27ccb7f2d7a8e7cd` |
| `textures/T_Ivy_Atlas_BaseColor.png` (sRGB) | 1,823,752 | `ee942486f8dfabc2` |
| `textures/T_Ivy_Atlas_Normal.png` (linear, OpenGL +Y) | 1,832,412 | `0ea4a54a7246d2b1` |
| `textures/T_Ivy_Atlas_Roughness.png` (linear) | 473,132 | `960973872ddddf29` |
| `exports/facade-textures/*.png` (11 original MS02 images, raw packed bytes) | see `facade_export.json` | per file |

Full hashes for all 60 files: `IV02_file_manifest.json`. No file is 50 MB or larger, so nothing is
kept local for size. Scripts are mirrored in `../../blender/`.

## Steps run

1. **S1 source audit.** Fab cache (ue-mcp `fab.status` / `fab.list_cached`, read-only): 0 cached
   assets. The lead's same-day authenticated audit (`../fab-shortlist.json`) found no owned ivy by
   title; Normandy (wall ivy in its description) is flagged incompatible (UE 5.6 only) and could only
   be inspected by a whole-pack import, which needs the owner's shortlist approval. VibeUE
   `FabService.get_asset` was not called: it runs through editor Python, which auto-saves dirty
   packages, and this packet grants no editor lock. IV01 (mesh-only Python generator, two materials,
   no curves/GN) and FG02 (grown on gate geometry, gate atlas, two-sided) do not meet the contract.
   **Decision: author one new patch, adapting the IV01 leaf method.**
2. **S2 facade extraction** (`export_facade.py`, master opened read-only). The live selection
   recomputed from the crop box matches the frozen 62 names exactly. Every object is evaluated,
   transformed to world, clipped by six bisect planes, merged and translated by −anchor
   (3.55, 1.8, 0). All six contract landmarks keep faces after clipping. Original UV layers are kept
   by index (UVMap = BakeAtlas, UV1 = SurfaceMetres). The master materials sample SurfaceMetres via
   per-object `he_uv1*` affine properties; all 62 are identity, so UV1 is exactly what they sample.
3. **S3 atlas and patch** (`bake_atlas.py`, `build_ivy.py`, seed 24024). See below.
4. **S4 reopen/render QA** (`reopen_verify.py`) and facade review on the read-only master
   (`review_master.py`).
5. **S5 clean round trip** (`roundtrip.py`) in an empty factory-startup process.

## Acceptance

### A1 Source preservation — PASS (self-test)

- MS02 before (09:25:48Z) and after all five master processes (09:47:46Z): 2,671,407,245 bytes,
  mtime 2026-10-19 22:44:44.3937821 +08:00, SHA-256
  `4ea301be7d39a0a8f463547194bb174b660870e9b99091469899fdd1cb7ad5ff` both times
  (`master_before.txt`, `master_after.txt`). No other file in `master_MS02/` changed.
- Fixture names, per-object source/clipped face counts, clipped bounds, world matrices and
  `he_uv` properties: `facade_export.json`. Source→fixture matrix = translation (−3.55, −1.8, 0);
  fixture→Unreal = (X, −Y, Z) × 100 cm, rotations conjugated by diag(1, −1, 1).
- Ivy `.blend` reopened clean: collections `IV02_SourceCurves` (`IV02_Stems`, CURVES, 53 curves /
  463 points, attributes radius/ivy_leafy/ivy_root_offset/ivy_woody), `IV02_LeafSources` (4 leaf
  meshes), `IV02_GrowthGN` (`IV02_IvyGrowth`, 82 nodes; evaluates to 33,516 triangles on reopen =
  export copy), `IV02_Export`. 11 objects, one material, no `P_*` objects and no HE materials
  (`reopen_verify.json`).

### A2 Geometry and look — implemented; Jason's verdict deferred to the Unreal milestone

Actual triangulated export: **33,516 triangles, 21,793 vertices**. About 233 leaves (one petiole per
leaf): blades 21,312 tris, petioles 5,592, stems 6,612 (3 woody stems, 50 branches/twigs; tubes of
6 sides, 8.5 mm root radius measured). Leaves are open, single-sided, opaque, with geometric
five-lobed cordate silhouettes (28–34 outline points), modest cupping, outward tip lean and arched
petioles; a young leaf terminates every tip. Zero vertices behind the wall plane. Blade triangles
covered from the front and three 35° obliques: 14.6% (natural overlap, no buried layer).
Renders: `renders/IV02_front_full`, `front_close`, `oblique_close`, `side_close`, `side_root`,
`first_person_1p7m`; on the actual MS02 bay with master materials: `IV02_facade_*`.
Comparisons beside the supplied reference and accepted IV01: `A2_compare_wall_scale.jpg`,
`A2_compare_close.jpg` (crops approximate comparable wall scale).

Visible defects found and repaired, in order:

1. IV01 outline read as a pointed-base, maple-like leaf → new cordate Hedera outline, veins from the
   petiole notch.
2. 124 zero-area triangles where the vein hub coincided with the notch point → hub moved above it.
3. Sparse single band, then a lopsided clump from random-walk drift → three target-steered woody
   stems with lateral branches.
4. Jagged kinks in stems → smooth Catmull-Rom curves, lower wander.
5. Bare twig ends → young terminal leaf on every curve end.
6. Petioles stuck straight out like pins → arched petiole.
7. Whitish sheen under grazing sun → roughness raised ~0.1; flat blades → more cupping.
8. Rigid straight centre stem → more wander, weaker steering.
9. Under-filled footprint → wider stem region (now 80.6 × 183.0 cm of the 100 × 200 nominal).
10. Leaves larger, sparser and bluer than reference/IV01 → 25% smaller leaves (blade 5.2–8.3 cm),
    denser spacing, warmer palette.
11. Review renders showed flat untextured facade → review copies now carry the `he_uv` properties.

Remaining, recorded mismatches (not hidden): the reference is a continuous mature mat while this is
one open starting patch (coverage is the kit/PCG layer's job); reference leaves read rounder and less
lobed; the reference has warm low-sun grading; at ≤ 0.5 m the straight outline segments of a leaf are
visible. Thickness was not added (contract: only after the first-person comparison shows a benefit).

### A3 Asset attributes — PASS (self-test)

- Frame: origin (0, 0, 0) at the lower central attachment on X = 0, identity object matrix, +X out
  of the wall, +Z up, width on Y. Tight bounds X 0.19–7.90 cm, Y −40.21–40.43 cm,
  Z −0.002–182.97 cm (root ring 0.02 mm below origin); inside the nominal 0–25 × ±50 × 0–200 cm.
- One slot `IvyAtlas`; one UV map `UVMap`; no collision objects or UCX.
- Atlas 2048², power-of-two cells (leaves 1024 px; young leaf, woody, branch and petiole 512 px).
  Every UV corner lies inside its cell inset by 16 px; measured footprint-to-foreign-cell gutter
  23–24 px; colour/normal fields painted analytically beyond the silhouette (continuous dilation).
  Box-filtered mips first mix islands at mip 10–11 (cells are aligned); at 10 m on 1080p the sampled
  mip is about 6.
- Base colour sRGB, normal linear OpenGL +Y (**Unreal: Flip Green Channel**), roughness linear;
  authored variation (leaf luma σ ≈ 12 of 255, roughness 0.55–0.65 mean per leaf variant, σ ≈ 0.03).
  No alpha.
- `Color` CORNER FLOAT_COLOR, exported linear: R cavity (32 cosine rays, 8 cm, patch + wall plane;
  median 0.72), G growth along the stem network (root 0 → 1; median 0.51), B base→tip per leaf and
  stem (median 0.33), A = 1. Channel correlations |r| ≤ 0.16 (`ivy_build.json`, `mask_RGB_strip.jpg`).

### A4 FBX round trip — PASS (self-test)

Empty factory-startup process, import settings recorded (`fbx_roundtrip.json`).
- Ivy: 33,516/33,516 triangles, 21,793/21,793 vertices, 100,548 corners compared in preserved loop
  order. Max position error 3.5e-8 m; normal 0.0°; UV 0.0; colour 0.0 (tolerances 1e-4 m, 1°, 1e-5,
  1/255). Corner data are seam-free per vertex (no vertex needs splitting: 21,793 unique
  vertex/normal/UV/colour keys). Bounds deviation ≤ 5e-7 cm (tolerance 1 cm or 2%). Pivot 0.0 cm.
- Axis markers: origin, +X 0.25 m, +Y 0.5 m, +Z 2 m all reimport with 0.0 cm error.
- Facade (IV02-r2 per-corner comparison, `fbx_roundtrip.json` → `facade_per_corner`): baseline
  `facade_baseline.py` re-runs `export_facade.py` in scratch and triangulates the evaluated clipped
  fixture exactly as io_scene_fbx does (Whispers `SourceAssets/HotelEden/IV02/qa/facade_baseline.npz`).
  `roundtrip_facade.py` reimports in a clean process: 59,617/59,617 vertices, 117,668/117,668
  triangles, 353,004/353,004 corners; identity correspondence (vertex order and per-triangle corner
  vertex indices equal), material index per triangle equal. Position ≤ 4.4e-7 m; corner normals max
  0.037° (p99 0.025°, 0 over 1°); UV0 `UVMap` (BakeAtlas) and UV1 (SurfaceMetres) max error 0.0
  (tolerance 1e-5); 133,084 unique vertex/normal/UV0/UV1 keys after split. Slot order preserved,
  bounds within 5e-5 cm. Renders `IV02_facade_roundtrip_clay_wide/plinth`, `_uv1_checker`.
- **r2 repair:** all 62 source objects carry custom split normals; r1 rebuilt the fixture from
  positions/UVs only (6,897 intact corners > 1° from source, max 167°: plinths, pedestals, window
  frames re-averaged). `export_facade.py` now carries each object's evaluated corner normals through
  the clip and re-applies them; fixture vs source on 347,129 intact corners: max 0.040°, UVs exact
  (`facade_baseline.json` → `source_fidelity`). New facade FBX SHA-256 `df553515…`, 16,606,892 B;
  master hash unchanged before/after r2 (`master_*_r2.txt`).
- Images `IV02_roundtrip_front/oblique` show the reimported mesh (atlas reassigned from `textures/`
  because the FBX strips texture paths).

### A5 Reproduction and delivery — delivered to Whispers (IV02-r2); independent verification pending

Delivered by the specialist to Whispers `SourceAssets/HotelEden/IV02/` with `docs/verification/ivy-IV02-A.md` and the credits entry; receipt in issue #113.

Generator, atlas baker, export settings (in `ivy_build.json` / `facade_export.json`), provenance,
manifests and this hand-off exist at named paths. Reproduce from `D:/AI_Modelling/hotel_eden/working/ivy_IV02`:

```
python scripts/bake_atlas.py .
blender --factory-startup --disable-autoexec -b --python scripts/build_ivy.py -- <root>
blender --factory-startup --disable-autoexec -b <MS02> --python scripts/export_facade.py -- <facade-selection.json> <root>/exports
blender --factory-startup --disable-autoexec -b <root>/IV02_Ivy_Prototype.blend --python scripts/reopen_verify.py -- <root>
blender --factory-startup --disable-autoexec -b --python scripts/roundtrip.py -- <root>
blender --factory-startup --disable-autoexec -b <MS02> --python scripts/review_master.py -- <facade-selection.json> <root>
python scripts/compose_review.py <root> <Workspace ivy (IV01) folder>
```

Provenance: all ivy geometry and textures are original, procedurally authored in this task (no Fab,
Quixel or third-party content). The facade and its 11 textures are the existing MS02 hotel assets.

## Findings for the lead / #114

1. **Rigid footprint vs the contracted anchor.** The flat brick pier at the anchor X 3.55 is about
   0.75 m wide between window surrounds that stand 0.28–0.44 m proud. At root Z 0.55 only 15/25
   footprint samples are supported there. The best fully supported pier in the fixture is source
   X 6.725 (25/25 supported, 25/25 clear of the 7.9 cm depth); the review renders use it
   (`facade_review.json`). The only ivy/facade intersections there are 9 root-ring triangles meeting
   the plinth top at the attachment point.
2. The fixture FBX keeps the original UVs; Unreal materials should sample UV channel 1
   (SurfaceMetres) for brick/limestone/iron and UV 0 (BakeAtlas) for relief maps, matching master.
3. Vertex colours were exported linear (`colors_type='LINEAR'`); verify the importer's vertex-colour
   handling (sRGB vs linear) in #114 before using the masks.
