"""MO01 Meredith's office (Level 3 lake office, room MO): shared dimensions in metres.

Owner, 12 Nov 2026: "Use the attached reference image to model the interior of Meredith's office. The layout is not
identical but use the reference as close as possible. Same rules as the executive corridor. This is a hero room so it
must be high quality game assets. Do not model the furniture. That will be done separately. You can place temporary
furniture to test the layout. Blender first until I receive it."
Reference: inbox/attachments/2026-11-12/1000001595-010029-1e3d4362.png (copied to the review media as MO01_Reference.png).

Room from the MS02 survey (12 Nov): clear x 17.1-25.7, plan y 0.3-6.7, floor top Z 9.004, ceiling Z 13.2 (4.196 m).
North wall y 0.3: lake windows W3-07 (glass x 18.225-19.975) and W3-06 (22.225-23.975), sill 10.138, pointed-arch apex
12.587, with the approved I06 interior stone surrounds standing up to 60 mm proud. East wall x 25.7: windows E13
LAKE-INNER W-0 (glass y 1.675-3.425) and W-1 (4.575-6.325), sill 9.938, apex 12.287. South wall y 6.7: the EC01
carved double door D-MO-24 (door case x 22.65-25.25, leaves 23.15-24.75, head 2.41, leaves swing into the office).
West wall x 17.1: solid.

Owner, 12 Nov 2026 (second review): "Add a couple of the Executive Corridor's sconces into the room for lighting. Let's
see the single swag.Keep the wallpaper colour. Model the books, candalabra and the clock in final game model quality
and deliver them with the room. Keep the windows."

Owner, 12 Nov 2026 (third review): "Just make the area rug larger and a bit more vibrant/less worn. Remove the temporary
furniture. In the corner straight across from the door, remove the temp stuff and add in a copy of the ferns from the
lobby, scaled down to fit the room."

Composition after the reference, seen from the east looking west: the fireplace on a chimney breast on the west wall
with an alcove bookcase to its right (north), the two lake windows with a portrait between them on the right (north)
wall, a full bookcase wall with a library ladder rail on the left (south) wall. Heights are above the floor top.
"""
FL = 9.004
CEIL = 4.196
ROOM = dict(x0=17.1, x1=25.7, y0=0.3, y1=6.7)
FLOOR_T = 0.004                    # parquet on the host floor (as EC01 boards)

# wall finish: EC01 dado system (mahogany) + damask paper + painted plaster cornice
SKIRT_TOP = 0.20
DADO_RAIL = (0.86, 0.95)
PAPER = (0.95, 3.66)
PICTURE_RAIL = 3.30                # small picture-rail bead (the reference portrait hangs from a rail)
CORNICE = (3.66, CEIL)             # EC01 cornice profile, painted
DADO_PANEL = (0.28, 0.78)          # raised dado panels (EC01 Raise loop)

# chimney breast (west wall) and fireplace
BREAST = dict(x0=17.1, x1=17.62, y0=3.25, y1=5.75)        # 0.52 deep, 2.50 wide
FIRE_C = (BREAST["y0"] + BREAST["y1"]) / 2                 # mantel centre line (plan y 4.50)
MANTEL = dict(width=2.00, shelf_top=1.32, shelf_t=0.075, shelf_proj=0.30, shelf_over=0.06,
              leg_w=0.27, leg_d=0.22, plinth_h=0.13, frieze=(1.00, 1.245), corbel=(0.70, 1.245),
              open_w=1.02, open_h=0.96, slip_w=0.075)
FIREBOX = dict(depth=0.42, back_w=0.62, front_w=0.87, h=0.82)   # brick lined, splayed cheeks
HEARTH = dict(depth=0.55, width=2.20, t=0.035)

# built-in bookcases (mahogany): lower cupboards with panelled doors, open shelves above, fluted pilasters
CASE = dict(base_h=0.92, base_d=0.46, top_t=0.035, upper_d=0.33, height=3.42, cornice_h=0.20, plinth_h=0.11,
            pil_w=0.11, shelf_t=0.028, shelf_pitch=0.36, door_rail=0.075)
CASE_SOUTH = dict(x0=17.1, x1=22.50, y_wall=6.7, n_bays=6)     # stops 0.15 m short of the D-MO-24 door case
CASE_ALCOVE = dict(y0=0.3, y1=BREAST["y0"], x_wall=17.1, n_bays=3)
LADDER_RAIL_Z = 2.30

# windows: arched architrave round the approved surrounds, curtains after the reference
ARCH_W = 0.10                      # EC01 Architrave profile, painted
CURTAIN = dict(stack=0.42, gap_wall=0.08, valance_drop=0.42, sheer_gap=0.05, hem_clear=0.012)

# portraits (AF02 frame, uniform scale) and the picture light
AF02_OUTER = (0.9384, 1.0940)
AF02_OPEN = (0.557, 0.709)
AF02_DEPTH = 0.127
PORTRAITS = [  # name, wall, along (plan), centre z, scale, AIC id
    dict(name="OverMantel", wall="W_breast", along=FIRE_C, z=2.48, scale=1.45, aic=102777),   # 6 cm clear of the clock
    dict(name="BetweenWindows", wall="N", along=21.10, z=2.05, scale=1.25, aic=59787),
    dict(name="AlcoveCase", wall="W_alcove", along=(0.3 + 3.25) / 2, z=2.12, scale=0.78, aic=72375),
]

# rug (AIC 22030 Ushak, CC0), third review: larger (was 3.88 x 2.59 m), restored a little (prepare_textures.rug).
# Long axis along x (towards the fireplace); the width follows the woven body's aspect (0.667). x 18.65-23.95 clears the
# hearth (front x 18.17) and the library ladder's feet (x <= 18.56); y 2.18-5.72 clears the D-MO-24 leaf swing (y >= 5.9).
RUG = dict(cx=21.30, cy=3.95, l=5.30, t=0.009)

# third review: the lobby's stair palm ("the ferns from the lobby", FUR-024 P03, LP01 at 2x scale) in the north-east
# corner, straight across from the door. Scale 1.0 is the approved P03 at its own size (2.57 m tall, half the lobby's
# 2x). Position and yaw from a clearance search over the canopy: every frond stays 30 mm or more off the walls, curtains,
# sheers, tails and pelmets of W3-06 and E13 W-0, and under the cornice. The meshes are the master's own (shared).
PALM = dict(asset="FUR-024", revision="P03", source_placement="LP01 | East stair palm | placement",
            cx=24.74, cy=1.14, yaw_deg=12.5, scale=1.0, min_clear=0.03)

# Furniture (owner, 12 Nov 2026: "D:\\Unreal Projects\\Whispers 5.8\\Saved\\Renders\\ there are blender files in there for the sofa,
# the desk and the chair. Copy them over to where you keep all the other models and add them to the approved furniture list.
# Add them to Meredith's office Blender file and place them like in the reference image. Then check to see that they are
# placed in the right spot in the Unreal file. Get rid of the textureless desk thing."). The approved game assets FUR-106-108
# (approved-media/*/<rev>_Game.blend) are the very meshes Unreal imported, so one set of numbers places both. Placements are in
# Unreal hotel-local cm and degrees of yaw (Blender = conv x 0.01); after the reference: the desk in front of the fire with the
# chair between it and the fire (the desk's drawer / kneehole side, its local +X, faces west), the chesterfield centred under
# the portrait between the lake windows with its back to the wall (its back is its local -Y). The chair keeps the relation
# the Unreal office had (100 cm off the desk's sitter side, turned 90 deg), as Meredith's seven Life desk advertisements do.
# 13 Nov 2026 (owner): "The desk and the sofa need to be about 20 percent larger. They are hero pieces." - the desk wider and
# deeper only (its 77 cm height kept so she works at a normal height; owner's choice), the chesterfield 20% all round with its
# back where it stood. "Meredith's chair needs to be rotated about 70 degrees perpendicular to the desk when she is not in it"
# - the chair is AWhispersSwivelDeskChair in Unreal: its working pose square to the desk at dock_cm, empty it rests rolled
# rest_roll_cm back and its seat turned rest_yaw towards the door side (+y); the master shows the empty (rest) pose. "Place the
# same journal that is on the reception desk on Meredith's desk right where she is writing" - the LP01 ledger (shared mesh).
# Applied by ms02_desk_chair.py from the Unreal install record (Desk_Chair_E2K.json), so both stay one set of numbers.
RUG_TOP_CM = round((FL + FLOOR_T + 0.009) * 100, 2)                  # 901.7 cm hotel-local (the rug's top): the desk group stands on it
FURNITURE = dict(
    desk=dict(fur="FUR-107", blend="approved-media/desk-pedestal-pd01/PD01_Game.blend", objects=["SM_DeskPedestal"],
              cm=(2030.0, 400.0, RUG_TOP_CM), yaw=180.0, scale=(1.2, 1.2, 1.0), unreal="Desk_Pedestal_MO"),
    chair=dict(fur="FUR-108", blend="approved-media/chair-swivel-sw01/SW01_Game.blend", objects=["SM_ChairSwivel_Base", "SM_ChairSwivel_Seat"],
               dock_cm=(1942.0, 400.0, RUG_TOP_CM), dock_yaw=0.0, rest_yaw=70.0, rest_roll_cm=30.0, seat_z_cm=24.2,
               mesh_yaw=-90.0, unreal="Chair_Swivel_MO (AWhispersSwivelDeskChair)"),
    sofa=dict(fur="FUR-106", blend="approved-media/sofa-chesterfield-cf01/CF01_Game.blend", objects=["SM_SofaChesterfield"],
              cm=(2110.0, 132.45, 900.8), yaw=0.0, scale=(1.2, 1.2, 1.2), unreal="Sofa_Chesterfield_MO"),
    journal=dict(source="LP01 | Reception guest ledger | SM_HotelEden_OpenLedger_DP02", cm=(2018.6, 416.98, 978.7), yaw=289.932,
                 pen_rest_cm=(1993.0, 405.0, 982.5), unreal="Journal_Ledger_MO"),
)
# Meredith's six seated Life desk advertisements (Life_Manager_*_SL8, E2K, 13 Nov 2026): at the chair's rest seat point + 40 cm,
# facing the rest yaw; Use 40 cm below (the pelvis point), Approach 40 cm in front (she stands there, back to the chair).
# StandLean no longer advertises (it stood at the old chair centre). Their PresentationOverlay is Overlay_MO_DeskChair.
LIFE_DESK_REST = dict(seat_point_cm=(1913.03, 402.82, 951.3), yaw=70.0, approach_cm=40.0)

# lighting under the game rules (Whispers docs/features/lighting-authoring.md, fixture catalog v1)
ZONE = "Light.Zone.Hotel.MeredithOffice"
LIGHTS = dict(
    Fireplace=dict(type="Point", lumens=1500, temperature_k=1900, source_radius_cm=25, attenuation_radius_cm=700,
                   shadows="Ray Tracing", role="Light.Role.Fire", flicker="Candle"),
    # Unreal port (owner, 12 Nov: "moody lighting"): the office's own WindowFill profile, cool lake light through the sheers at
    # 500 lm (the catalog's 3,000 lm of 5,500 K flattened the room; with no mood driving it, it burns at night too), so the fire, sconces and picture light carry it
    WindowFill=dict(type="Rect", lumens=500, temperature_k=6200, attenuation_radius_cm=700, shadows="None",   # shadowless, as the lobby fills
                    role="Light.Role.Fill", profile="/Game/Whispers/World/Lighting/Profiles/DA_LightProfile_MO01_WindowFill",
                    note="just inside the glass, facing the room; time-of-day mood driven"),
    PictureLight=dict(type="Spot", lumens=400, temperature_k=2700, outer_cone_deg=70, inner_cone_deg=40, source_radius_cm=3,
                      attenuation_radius_cm=400, shadows="Ray Tracing", role="Light.Role.Practical", direction="down",
                      rule="WallSconce (catalog v1): a brass picture light over the mantel portrait, as in the reference"),
    WallSconce=dict(type="Point", lumens=1400, temperature_k=2700, source_radius_cm=3, attenuation_radius_cm=520,
                    shadows="Ray Tracing", role="Light.Role.Practical", allow_megalights=True,
                    profile="/Game/Whispers/World/Lighting/Profiles/DA_LightProfile_EC01_Sconce",
                    rule="the Executive Corridor's S06 sconce with the corridor's own Unreal profile (Point 1,400 lm, after "
                         "the owner found the catalog's downward spot too dark); the fitting casts no shadow on its own light"),
)
LIGHT_ID = "Hotel.MeredithOffice.{fixture}.{n:02d}"

# second review: two EC01 S06 sconces flanking the over-mantel portrait on the chimney breast (plan y, flame height)
SCONCES = [dict(along=3.45, flame_z=2.20), dict(along=5.55, flame_z=2.20)]
# mantel garniture after the reference (plan y along the breast face; d = out from the breast face to the item's centre,
# or to the books' spines): candelabra at the ends, the books left of centre, the clock right of centre
MANTEL_PROPS = dict(candelabra=[dict(along=5.34, d=0.17), dict(along=3.66, d=0.17)], books=dict(centre=4.85, d=0.215),
                    clock=dict(along=4.36, d=0.15))
