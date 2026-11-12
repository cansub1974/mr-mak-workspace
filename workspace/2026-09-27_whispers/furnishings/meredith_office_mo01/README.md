# MO01 Meredith's office (Level 3 lake office)

The owner's request, 12 Nov 2026: "Use the attached reference image to model the interior of Meredith's office. The layout is not
identical but use the reference as close as possible. Same rules as the executive corridor. This is a hero room so it
must be high quality game assets. Do not model the furniture. That will be done separately. You can place temporary
furniture to test the layout. Blender first until I receive it."

Second review, 12 Nov 2026: "Add a couple of the Executive Corridor's sconces into the room for lighting. Let's see the
single swag.Keep the wallpaper colour. Model the books, candalabra and the clock in final game model quality and
deliver them with the room. Keep the windows."

Third review, 12 Nov 2026: "Just make the area rug larger and a bit more vibrant/less worn. Remove the temporary furniture. In the corner
straight across from the door, remove the temp stuff and add in a copy of the ferns from the lobby, scaled down to fit
the room."

- **Reference:** `inbox/attachments/2026-11-12/1000001595-010029-1e3d4362.png`, copied as
  `review-media/meredith-office-mo01/MO01_Reference.png`.
- **Master:** the MS02 master, saved in place. Unreal comes later, after the owner has accepted it in Blender.
- **Review tab:** `meredith-office-mo01-review.html`.

## The room (MS02 survey, `survey_mo01.py` → `Survey_MO01.json`)

- **Size:** x 17.1–25.7 by plan y 0.3–6.7 (8.6 × 6.4 m), floor Z 9.004, ceiling Z 13.2 (4.196 m).
- **North wall (lake):** windows W3-07 and W3-06.
- **East wall:** windows E13 LAKE-INNER W-0 and W-1.
- **Windows:** all four are 1.75 m of glass with a mullion, in slightly pointed arched heads. The approved I06 stone
  surrounds stand up to 65 mm proud, outer half-width 1.067 m, and the stone sills project 0.13 m.
  - **North:** springing 2.606 m and apex 3.766 m above the floor; sill 1.136 m.
  - **East:** springing 2.346 m and apex 3.466 m; sill 0.936 m.
- **South wall:** the EC01 carved double door D-MO-24, which opens into the office.
- **West wall:** solid.

## Layout after the reference (seen from the east, looking west)

- **West wall:** a chimney breast (0.52 deep, 2.50 wide, centred on plan y 4.50) carries the fireplace, with the large
  portrait and a brass picture light above it. A three-bay alcove bookcase fills the wall to its north.
- **North wall:** the two lake windows, with a portrait between them.
- **South wall:** a six-bay bookcase wall with a brass ladder rail and a rolling library ladder. It stops 0.15 m short
  of the door case.
- **Every window** (the hotel's own Gothic windows, kept): a painted arched architrave; a single swag with pleated
  tails and bullion fringe, hung from an arched velvet pelmet; sage velvet curtains and ivory sheers hung inside the
  arch behind them.
- **Mantel:** a five-light brass candelabrum at each end, five volumes left of centre and an arch-top clock right of
  centre, as in the reference. Two of the corridor's S06 sconces flank the over-mantel portrait.
- **Floor:** the Ushak rug, 5.30 × 3.53 m, long axis towards the fireplace (x 18.65–23.95, plan y 2.18–5.72). It stops
  0.48 m short of the hearth and clears the library ladder's feet and the door leaves' swing.
- **North-east corner** (straight across from the door): a copy of the lobby's stair palm, FUR-024 P03, on the master's
  own meshes. It stands at the approved P03's own size (2.57 m tall; the lobby pair is at 2×), planter at plan
  (24.74, 1.14), turned 12.5°. Every frond is 30 mm or more off the walls, cornice, curtains, sheers, tails and pelmets;
  the build measures this on the placed vertices and stops if it fails.
- **No furniture:** the TEMP layout-test furniture was removed at the third review. The furniture comes separately.
- **Books:** every open shelf, from 20 instanced row modules.

## Run order

1. `fetch_sources.py`: downloads the CC0 sources and writes `Sources.json` in the working folder.
2. `prepare_textures.py`: writes `T_MO01_*` and `Material_Recipes.json`.
3. `prepare_books.py`: the book atlas `T_MO01_Books_*` and `Books_Atlas.json`. `prepare_props.py`: the clock dial.
4. Blender, `build_kit_mo01.py -- --only=<kit>` for each kit: `mantel`, `drapes`, `books`, then `candelabra,clock`.
   - The kit files are `kit/MO01_Kit_<kit>.blend` (the props kit is `MO01_Kit_candelabra_clock.blend`); each also
     holds its high poly. `--preview` adds quick EEVEE looks; build the final kits without it, so that no preview
     scaffolding is saved into them.
   - The books kit also writes `kit/Books_Rows.json` (the row modules and their layout).
5. `build_mo01.py` (Blender, on the master): `-- [--save] [--render[=views]]`.
6. `render_mo01.py` (Blender, on the saved master): `-- [--views=…] [--night]`, then `check_mo01.py` and
   `compare_mo01.py`.

The working folder is `D:/AI_Modelling/hotel_eden/working/meredith_office_MO01/` (sources, textures, kit). Receipts
are in `review-media/meredith-office-mo01/build/`.

## Sources (all CC0 or already approved)

- **Floor:** Poly Haven herringbone_parquet, graded to a waxed mid-dark brown. 3.4 m tile, 2K.
- **Firebox:** Poly Haven herringbone_brick, with soot added per vertex. 1.8 m tile, 1K.
- **Marble:** ambientCG Marble018 (warm statuary) for the mantel and hearth; Marble016 (black) for the slip.
- **Curtains:** Poly Haven velour_velvet (as on the approved S03 settee), regraded to sage.
- **Sheers:** Poly Haven crepe_georgette weave, ivory.
- **Wallpaper:** the PW01 damask (the owner's corridor paper), recoloured tone-on-tone olive-grey at 0.70 scale.
- **Rug:** AIC 22030, a 17th-century Ushak double-ended prayer rug (CC0), from the museum's full image (1601 × 2250),
  with the approved ambientCG Carpet001 pile. Restored a little (`prepare_textures.py rug`): worn specks in the plain
  red field and navy ground are repaired (small blobs only, so guard lines and motifs are untouched), the fading is
  evened within each colour, and the chroma is lifted × 1.35. Texture 1024 × 2048 (power of two, so Unreal builds mips).
- **Corner palm:** FUR-024 P03, approved 4 Oct 2026 (`approved-media/plant-p03/`), the master's own LP01 meshes.
- **Portraits:** AIC 102777 (Blackburn), 59787 (Copley) and 72375 (Sully), CC0, in the approved AF02 frame.
- **Mantel carving:** the EC01 scanned height fields, from Poly Haven ornate_mirror_01 and ClassicConsole_01 (CC0).
- **Reused from EC01:** the mahogany, figured veneer, trim sheet, brass and canvas maps.
- **Reused approved assets:** the G01 grate and fuel, at uniform scale 0.66; the EC01 S06 sconce (its own mesh, shared).
- **Books:** ambientCG Leather021 (CC0) for the leather grain and mottling; lettering set in Garamond and Baskerville
  (Windows fonts, rasterised into the texture); public-domain 18th- and 19th-century titles.
- **Candelabra and clock:** the EC01 aged brass and mahogany, box-projected on the high poly and baked; the dial is drawn
  by `prepare_props.py` (maker's line EDEN & SON, LONDON).

## Game assets

- **Mantel** (`SM_MO01_Mantel`): a 5.7M-tri high poly (shelf, bed mould, frieze, scanned crest and rosettes, S-scroll
  consoles with scanned acanthus and volutes, plinths, black slip) baked onto about 714 low triangles.
  - **Maps:** 4K BaseColor and NormalGL, 2K ORM.
  - **Why 4K:** the hero piece is seen within a metre and carries carving.
- **Curtains and sheers:** made by cloth simulation (`mo01_cloth.py`). Each is a flat panel cut so that its top follows
  the pelmet; the pinned heading is animated into pinch pleats, then the cloth settles under gravity against the
  wall, floor and stone sill.
  - **High poly:** the settled grid.
  - **Low poly:** every 3rd column and 5th–6th row of the same grid.
  - **Maps:** 1K normal and 512 AO per piece; colour comes from the tiling velvet and sheer on UV1.
  - **Pieces:** side panels L/R and the sheer; the east windows reuse them at a Z scale of about 0.90.
- **Swag and tails** (`mo01_drapes.py`): tailored surfaces, not simulated. The swag morphs from the pelmet's arch into a
  catenary hem in four soft folds gathered into its ends; the tails are three knife pleats with a stepped hem. One
  swag per arch (N, E); the right tail mirrors the left and shares its maps. 1K normal (tails 512) and AO, velvet on
  UV1, bullion fringe cards along the hems.
- **Books** (`prepare_books.py`, `mo01_books.py`): 36 sets, 192 volumes, one 2K atlas (BaseColor, NormalGL, ORM with
  the gilt as metal). A book is about 29 triangles: a rounded spine, the boards, and a sunk page block at the head.
  Row modules per bay width and shelf class (South 12, Alcove 8) hold runs of sets in volume order, gaps, a leaning
  volume and the odd flat stack. They are placed so that no module sits beside or above itself. The mantel carries
  five volumes of one set.
- **Candelabra** (`mo01_props.py`, `SM_MO01_Candelabra`, placed twice): lathe-turned brass body, four S-scroll arms
  with curled brackets, five part-burnt candles. High poly with gadroons, beaded rings and wax drips. 1K baked set;
  the brass tarnishes in the recesses.
- **Clock** (`SM_MO01_Clock`): arch-top mahogany case, moulded plinth, brass bun feet, bezel, frets and finial, blued
  hands at 10:09. Sections: baked case (1K), the dial (1K) and the glass (translucent, opacity 0.12).
- **Procedural architecture (geometry plus tiling or trim-sheet maps, no unique bake):**
  - the dado (EC01 system), skirting, dado rail and cornice (EC01 profile at 0.56);
  - the window architraves (EC01 Architrave at 0.70);
  - the door architrave;
  - the bookcases. Their shared meshes are the pilaster, cupboard door, shelf and knob.
- **Collision:** UCX boxes for the chimney breast, mantel and both bookcases. Trim, drapes and the rug have none.
- **Lights:** game-rule fixtures with identity properties (`mo01_*`):
  - Fireplace: Point, 1,500 lm, 1,900 K, Candle flicker.
  - WindowFill: four Rect lights inside the glass, 500 lm, 6,200 K, shadowless: the Unreal profile
    `DA_LightProfile_MO01_WindowFill` (owner, 12 Nov: "moody lighting"; it was 3,000 lm of 5,500 K).
  - PictureLight: the WallSconce rule, a Spot of 400 lm at 2,700 K.
  - WallSconce.01–02: two EC01 S06 sconces on the chimney breast with the corridor's Unreal profile
    `DA_LightProfile_EC01_Sconce` (Point, 1,400 lm, 2,700 K, 3 cm source, 520 cm). The fittings cast no shadow on
    their own light.
  - Zone `Light.Zone.Hotel.MeredithOffice`.
- **Corner palm** (`MO01 | Decoration`): five objects on the lobby palms' own P03 meshes under a placement empty with
  the FUR-024 identity. 38,464 triangles, no new mesh or texture. Two-sided leaves, as in the lobby.
- **No TEMP furniture:** removed at the third review, with its materials. The night renders use only the room's own
  lights (fire, picture light, sconces).

## Lessons

- **Cloth pins:** with a rest shape key, Blender pins the cloth to the rest shape, so the heading spreads flat. Instead,
  start from the flat cloth and animate only the pinned row into the gathered heading. Then let it settle.
- **Material slots:** create a mesh's material slots before setting face material indices. Without slots, a modifier
  applied with `new_from_object` clamps the indices to 0. Here that baked the black slip white.
- **Face orientation:** orient each face group by its own direction (front, sides, caps). A single inside point
  misjudges S-curves.
- **Inventory guard:** it catches appended helper objects. Remove the appended objects after taking their meshes, and
  don't exclude shared approved meshes (the AF02 frame) from the hash.
- **Swags:** a simulated swag hangs as a flat sheet with one fold. Its look comes from regular folds that run into the
  pleated ends, so it is a tailored surface. Avoid cusped fold profiles: they render as seam lines.
- **Run frame:** run U is the viewer's left when facing the wall. Spine lettering and dials must read left to right,
  so their u runs along -U, and volume I goes at the +U end.
- **Restoring a museum rug:** repair wear only inside the large plain grounds and only as small blobs. The first pass,
  which inpainted every strong deviation, wiped the medallion's detail and broke the guard lines.
- **Corner planting:** fit a plant to a corner by searching yaw and position against the walls and the window
  dressing's bounding boxes (a 2D grid with prefix sums per yaw is fast). A 1.7 m canopy needs its planter about 0.9 m
  out of a corner flanked by curtains.
- **Bake slots:** a mesh with separately textured sections (the clock's dial and glass) bakes only into its slot 0
  (`bake(..., slots=[0])`). Otherwise every slot writes into the same image.
- **Re-appending kits:** purge the previous build's orphaned `M_MO01_*` materials and `T_MO01_*` images first, so the
  re-appended data keeps its names instead of gaining `.001`.
- **Bake names:** the drapes kit baked the sheer's fold normal as `T_MO01_Sheer_NormalGL.png`, the tiling weave's name,
  so the sheer tiled its fold map. The bake is `T_MO01_SheerFolds_NormalGL.png` now (`mo01_drapes.fold_name`); the kit was
  repointed by `fix_sheer_kit.py` without re-baking.
- **Clearance from the hotel shell:** the paper stands 3 mm off the walls and the ceiling plane 10 mm under the shell
  (`PAPER_OFF`, `CEIL_DROP`). 1 mm read fine in Cycles; in Unreal the ceiling looked wrong.
- **Unreal port:** `../../hotel-unreal-mo01/README.md`.
