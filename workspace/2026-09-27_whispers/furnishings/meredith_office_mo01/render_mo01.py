"""MO01 review renders (inside build_mo01.py -- --render[=views], or on the saved master:
    blender -b --factory-startup <MS02> --python render_mo01.py -- [--views=a,b] [--samples=N] [--exposure=E] [--night]

Lighting: the office's own game-rule lights (Fireplace, four WindowFill, PictureLight, two WallSconce) plus a daylight
sky seen through the windows (Day), or the fire, picture light and sconces only (--night). Every other light in the master is
switched off for the render and restored. Objects far from the office are hidden from rendering (restored) to keep the
BVH small. Writes review-media/meredith-office-mo01/build/MO01_<view>[_Night].png and Render_Receipt.json.
"""
import bpy, json, math, os, sys, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(WS, "review-media", "meredith-office-mo01", "build")
FL = 9.004
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
# name: (camera plan xy, eye height, target plan xy, target height, lens mm, resolution)
VIEWS = {
    "Ref_Match": ((25.10, 6.05), 1.55, (17.6, 2.9), 1.45, 17, (1920, 1080)),
    "Fireplace": ((20.6, 4.5), 1.50, (17.6, 4.5), 1.70, 26, (1600, 1000)),
    "Windows_North": ((21.1, 5.3), 1.60, (21.1, 0.3), 2.10, 19, (1600, 1000)),
    "Bookcase_South": ((20.4, 1.6), 1.60, (19.6, 6.7), 1.80, 20, (1600, 1000)),
    "Window_Close": ((20.15, 1.75), 1.65, (19.1, 0.3), 2.45, 26, (1300, 1300)),
    "Mantel_Close": ((18.75, 3.85), 1.35, (17.62, 4.5), 1.10, 32, (1400, 1100)),
    "Door_East": ((19.2, 1.6), 1.60, (24.6, 6.2), 1.55, 20, (1600, 1000)),
    "Plan_Top": ((21.4, 3.5), 4.12, (21.4, 3.5), 0.0, "ORTHO:9.4", (1600, 1200)),     # orthographic, just under the ceiling
    "Mantel_Props": ((19.05, 4.62), 1.62, (17.62, 4.50), 1.66, 30, (1600, 1000)),      # second review: garniture and sconces
    "Books_Close": ((19.75, 5.05), 1.62, (18.35, 6.70), 1.85, 26, (1400, 1100)),
    "Swag_N": ((19.45, 2.55), 1.70, (19.10, 0.30), 2.95, 24, (1300, 1300)),
    "Candelabra_Close": ((18.42, 4.98), 1.78, (17.79, 5.34), 1.58, 38, (1200, 1200)),
    "Corner_Palm": ((23.95, 5.75), 1.60, (24.85, 1.00), 1.45, 22, (1300, 1300)),        # third review: from the door, across
    "Rug": ((23.35, 2.25), 1.65, (20.9, 4.1), 0.0, 24, (1600, 1000)),                  # the larger, restored rug
}
KEEP = (13.5, 29.5, -2.5, 10.5)               # plan box kept for rendering


def setup(night):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = int(next((a.split("=")[1] for a in ARGS if a.startswith("--samples=")), 48))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["look"].enum_items]
    sc.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in looks else "None"
    sc.view_settings.exposure = float(next((a.split("=")[1] for a in ARGS if a.startswith("--exposure=")), 2.6 if night else 1.4))
    sc.render.image_settings.file_format = "PNG"
    saved = {"hide_render": {}, "world": sc.world, "camera": sc.camera}
    bpy.context.view_layer.update()            # parented objects built in this session need evaluated world matrices
    for o in bpy.data.objects:
        far = False
        if o.type in ("MESH", "CURVE") and o.data is not None:
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            xs = [v.x for v in bb]; ys = [-v.y for v in bb]; zs = [v.z for v in bb]
            far = max(xs) < KEEP[0] or min(xs) > KEEP[1] or max(ys) < KEEP[2] or min(ys) > KEEP[3] or max(zs) < 8.5 or min(zs) > 14.5
        mine = o.name.startswith("Light | Hotel.MeredithOffice")
        light_off = o.type == "LIGHT" and not mine
        if night and mine and ("WindowFill" in o.name):
            light_off = True
        hide = far or light_off or bool(o.get("mo01_collider")) or bool(o.get("ec01_collider")) or o.name.startswith("UCX_")
        if hide and not o.hide_render:
            saved["hide_render"][o.name] = o.hide_render; o.hide_render = True
    w = bpy.data.worlds.get("MO01 review sky") or bpy.data.worlds.new("MO01 review sky")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    if night:
        bg.inputs["Color"].default_value = (0.02, 0.025, 0.05, 1); bg.inputs["Strength"].default_value = 0.05
    else:
        bg.inputs["Color"].default_value = (0.78, 0.86, 1.0, 1); bg.inputs["Strength"].default_value = 1.6
    sc.world = w
    return saved


def restore(saved):
    for n, v in saved["hide_render"].items():
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = v
    sc = bpy.context.scene
    sc.world = saved["world"]; sc.camera = saved["camera"]
    w = bpy.data.worlds.get("MO01 review sky")
    if w and w.users == 0:
        bpy.data.worlds.remove(w)
    for nm in ("MO01 review camera",):
        o = bpy.data.objects.get(nm)
        if o:
            d = o.data; bpy.data.objects.remove(o, do_unlink=True)
            if d and d.users == 0:
                (bpy.data.cameras if isinstance(d, bpy.types.Camera) else bpy.data.lights).remove(d)


def render_all(views=None, night=None):
    night = ("--night" in ARGS) if night is None else night
    os.makedirs(OUT, exist_ok=True)
    views = views or list(VIEWS)
    saved = setup(night)
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("MO01 review camera"); co = bpy.data.objects.new("MO01 review camera", cam)
    sc.collection.objects.link(co); sc.camera = co
    rec = {"views": {}, "night": night, "exposure": sc.view_settings.exposure, "samples": sc.cycles.samples,
           "lights": "MO01 game-rule lights only" + (" (no WindowFill)" if night else " + daylight sky"),
           "hidden_far_objects": len(saved["hide_render"])}
    for v in views:
        (cx, cy), eh, (tx, ty), th, lens, res = VIEWS[v]
        if isinstance(lens, str) and lens.startswith("ORTHO"):
            cam.type = "ORTHO"; cam.ortho_scale = float(lens.split(":")[1]); cam.clip_start = 0.01
        else:
            cam.type = "PERSP"; cam.lens = lens; cam.clip_start = 0.05
        co.location = (cx, -cy, FL + eh)
        d = Vector((tx, -ty, FL + th)) - co.location
        co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler() if v != "Plan_Top" else (0.0, 0.0, 0.0)
        sc.render.resolution_x, sc.render.resolution_y = res
        path = os.path.join(OUT, f"MO01_{v}{'_Night' if night else ''}.png")
        sc.render.filepath = path
        t = time.time(); bpy.ops.render.render(write_still=True)
        rec["views"][v] = dict(file=os.path.basename(path), seconds=round(time.time() - t, 1), camera=[cx, cy, eh], target=[tx, ty, th], lens=lens)
        print("RENDERED", v, round(time.time() - t, 1), flush=True)
    restore(saved)
    rp = os.path.join(OUT, "Render_Receipt.json")
    old = json.load(open(rp)) if os.path.exists(rp) else {}
    old["Night" if night else "Day"] = rec
    json.dump(old, open(rp, "w"), indent=1)
    return rec


if __name__ == "__main__":
    vs = next((a.split("=", 1)[1].split(",") for a in ARGS if a.startswith("--views=")), None)
    render_all(vs)
