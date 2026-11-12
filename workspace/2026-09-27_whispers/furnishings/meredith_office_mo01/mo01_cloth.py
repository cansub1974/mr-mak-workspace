"""MO01 drapery by cloth simulation (Blender): the curtains and sheers. Called by mo01_drapes.build().

Owner, 12 Nov 2026 (second review): "Let's see the single swag." The swag and its tails are tailored shapes, built
procedurally in mo01_drapes.py; the curtains and sheer hang behind them, inside the arch:
  sides   velvet curtains hung inside the arch, their heading following the pelmet (hidden by the swag and tails)
  sheer   ivory sheer across the glass, its heading following the pelmet
Each is a flat fabric panel (the rest shape, cut so that its top follows the pelmet) whose pinned heading is animated
from the flat into pinch pleats (shape key "Gather"), then the cloth settles under gravity against the wall, the floor
and the stone sill. The high poly is the settled grid; the low poly is every k-th column / row of the same grid (same
parametrisation), so the tangent-space bake carries the fine folds. UV1 is the flat fabric in metres.
Frame: X along the wall (0 = window centre, + to the right seen from the room), Y out of the wall face, Z up from the
floor top. Surveyed arches: two-centred, outer half-width 1.067 m; N springing 2.606 / apex 3.766; E 2.346 / 3.466.
"""
import math
import numpy as np
import bpy

FL = 9.004
A_HALF = 1.067
ARCH = {"N": dict(spring=11.61 - FL, apex=12.77 - FL), "E": dict(spring=11.35 - FL, apex=12.47 - FL)}
SILL = {"N": dict(top=10.14 - FL, bot=10.04 - FL), "E": dict(top=9.94 - FL, bot=9.84 - FL)}
SILL_PROJ = 0.13
PELMET = dict(inset=0.05, drop=0.03, h=0.045, front=0.29)        # the arched velvet board (build_mo01.pelmet)
Y_SHEER, Y_SIDE, Y_SWAG, Y_TAIL = 0.165, 0.215, 0.300, 0.322
HEM = 0.012
SWAG_T0, TAIL_T1 = 0.27, 0.31                                    # swag ends and tail tops along the arch (t)
SIDE_IN, SIDE_W = 0.40, 0.58                                     # curtain leading edge and hung width (inside the arch)


def arch_xz(kind, t):
    """Point on the surround's outer arch, t in [0, 1] from the left springing over the apex to the right springing."""
    a = A_HALF; zs = ARCH[kind]["spring"]; rise = ARCH[kind]["apex"] - zs
    c = (rise * rise - a * a) / (2 * a); R = a + c
    th_apex = math.atan2(rise, -c)
    if t <= 0.5:
        th = math.pi + (th_apex - math.pi) * (t / 0.5)
        return (c + R * math.cos(th), zs + R * math.sin(th))
    x, z = arch_xz(kind, 1 - t)
    return (-x, z)


def pelmet_xz(kind, t, top=False):
    """The pelmet board's line (as build_mo01.pelmet): bottom face, or its top edge with top=True."""
    x, z = arch_xz(kind, t)
    return x * (1 - PELMET["inset"] / A_HALF), z - PELMET["drop"] + (PELMET["h"] if top else 0.0)


def pelmet_z_at(kind, x, top=False):
    """Height of the pelmet line above plan offset x (|x| <= its half-width)."""
    ts = np.linspace(0, 0.5, 400)
    P = np.array([pelmet_xz(kind, t, top) for t in ts])          # x rising from -half to 0
    return np.interp(-np.abs(np.asarray(x, float)), P[:, 0], P[:, 1])


def arc_points(kind, t0, t1, n, top=True):
    """n points evenly spaced in arc length along the pelmet line between t0 and t1 (the arcs are circular in t)."""
    ts = np.linspace(t0, t1, 600)
    P = np.array([pelmet_xz(kind, t, top) for t in ts])
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    s = np.linspace(0, L[-1], n)
    return np.stack([np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])], -1), L[-1]


def colliders(kind, c):
    objs = []
    for nm, loc, rot, scl in (("COL_Wall", (0, -0.002, 2.0), (math.pi / 2, 0, 0), (6, 6, 1)), ("COL_Floor", (0, 1.5, -0.002), (0, 0, 0), (6, 6, 1))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.scale = scl; o.name = nm
        objs.append(o)
    sl = SILL[kind]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, SILL_PROJ / 2, (sl["top"] + sl["bot"]) / 2)); o = bpy.context.active_object
    o.scale = (2 * A_HALF, SILL_PROJ, sl["top"] - sl["bot"]); o.name = "COL_Sill"; objs.append(o)
    for o in objs:
        for u in list(o.users_collection):
            u.objects.unlink(o)
        c.objects.link(o)
        o.modifiers.new("col", "COLLISION"); o.collision.thickness_outer = 0.004; o.collision.cloth_friction = 8.0
        o.hide_render = True
    return objs


def remove(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def cloth_grid(name, start, rest, pin, c, mass=0.35, bend=6.0, stiff=30.0, frames=90, gather_frames=30, self_collide=False):
    """Flat cloth (rest) whose pinned vertices (pin: (nv, nu) bool, or a list of pinned rows) are animated into their
    hung positions (start) over gather_frames, then settle. start/rest: (nv, nu, 3), row 0 = top.
    Returns the settled (nv, nu, 3) positions."""
    nv, nu = rest.shape[:2]
    if not isinstance(pin, np.ndarray):
        m = np.zeros((nv, nu), bool); m[list(pin)] = True; pin = m
    co = rest.reshape(-1, 3)
    r, cc = np.meshgrid(np.arange(nv - 1), np.arange(nu - 1), indexing="ij")
    a = (r * nu + cc).ravel()
    q = np.stack([a, a + 1, a + nu + 1, a + nu], -1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co)); me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.loops.add(len(q) * 4); me.loops.foreach_set("vertex_index", q.astype(np.int32).ravel())
    me.polygons.add(len(q)); me.polygons.foreach_set("loop_start", np.arange(0, 4 * len(q), 4, dtype=np.int32))
    me.update(calc_edges=True); me.validate()
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    ob.shape_key_add(name="Basis")
    kg = ob.shape_key_add(name="Gather")
    g = np.where(pin[..., None], start, rest)
    kg.data.foreach_set("co", g.reshape(-1, 3).astype(np.float32).ravel())
    kg.value = 0.0; kg.keyframe_insert("value", frame=1)
    kg.value = 1.0; kg.keyframe_insert("value", frame=gather_frames)
    vg = ob.vertex_groups.new(name="pin")
    vg.add([int(i) for i in np.flatnonzero(pin.ravel())], 1.0, "REPLACE")
    m = ob.modifiers.new("cloth", "CLOTH"); st = m.settings
    st.quality = 10; st.mass = mass; st.air_damping = 2.0
    st.tension_stiffness = stiff; st.compression_stiffness = stiff; st.shear_stiffness = stiff * 0.6; st.bending_stiffness = bend
    st.tension_damping = 8; st.compression_damping = 8; st.bending_damping = 1.0
    st.vertex_group_mass = "pin"
    cs = m.collision_settings
    cs.collision_quality = 4; cs.distance_min = 0.004
    cs.use_self_collision = self_collide
    if self_collide:
        cs.self_distance_min = 0.003; cs.self_friction = 5.0
    m.point_cache.frame_start = 1; m.point_cache.frame_end = frames
    sc = bpy.context.scene; sc.frame_start = 1; sc.frame_end = frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg); tm = ev.to_mesh()
    out = np.zeros(len(tm.vertices) * 3, np.float32); tm.vertices.foreach_get("co", out)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    sc.frame_set(1)
    return out.reshape(nv, nu, 3)


def resample(P, ku, kv):
    nv, nu = P.shape[:2]
    cols = sorted(set(list(range(0, nu, ku)) + [nu - 1])); rows = sorted(set(list(range(0, nv, kv)) + [nv - 1]))
    return P[np.ix_(rows, cols)], np.array(rows), np.array(cols)


def pleat_top(nu, width, n_folds, depth, flat_len):
    s = np.linspace(0, flat_len, nu)
    return s * width / flat_len, depth * np.sin(n_folds * 2 * np.pi * s / flat_len)


def side_cloth(side, c, res=(84, 150), kind="N"):
    """Velvet curtain hung inside the arch: leading edge SIDE_IN, outer edge SIDE_IN + SIDE_W, heading 15 mm under the
    pelmet line (so it rises towards the crown), gathered 2.2 into 8 pinch pleats, to the floor. The pleats stay behind
    the pelmet front (0.29) and the swag (0.30)."""
    Wp, gather = SIDE_W, 2.2
    flat = Wp * gather
    nu, nv = res
    x_rail, y_head = pleat_top(nu, Wp, 8, 0.045, flat)
    xs = side * (SIDE_IN + x_rail)
    ztop = pelmet_z_at(kind, xs) - 0.015
    s = np.linspace(0, flat, nu)
    f = np.linspace(0, 1, nv)[:, None]
    Z = ztop[None, :] - f * (ztop[None, :] - HEM)
    start = np.zeros((nv, nu, 3)); rest = np.zeros((nv, nu, 3))
    start[..., 0] = xs[None, :]; start[..., 1] = Y_SIDE + 0.03 + y_head[None, :]; start[..., 2] = Z
    rest[..., 0] = side * (SIDE_IN + s)[None, :]; rest[..., 1] = Y_SIDE + 0.03; rest[..., 2] = Z
    P = cloth_grid(f"SIM_Side_{side}", start, rest, [0], c, mass=0.45, bend=8.0, stiff=40.0, frames=110, gather_frames=35)
    return P, rest


def sheer_cloth(c, res=(150, 110), kind="N"):
    """Ivory sheer across the glass, its heading 30 mm under the pelmet line, gathered 2.0 into 22 folds."""
    Wp, gather = 1.84, 2.0
    flat = Wp * gather
    nu, nv = res
    x_rail, y_head = pleat_top(nu, Wp, 22, 0.018, flat)
    xs = -Wp / 2 + x_rail
    ztop = pelmet_z_at(kind, xs) - 0.030
    s = np.linspace(0, flat, nu)
    f = np.linspace(0, 1, nv)[:, None]
    Z = ztop[None, :] - f * (ztop[None, :] - HEM - 0.004)
    start = np.zeros((nv, nu, 3)); rest = np.zeros((nv, nu, 3))
    start[..., 0] = xs[None, :]; start[..., 1] = Y_SHEER + y_head[None, :]; start[..., 2] = Z
    rest[..., 0] = (-flat / 2 + s)[None, :]; rest[..., 1] = Y_SHEER; rest[..., 2] = Z
    P = cloth_grid("SIM_Sheer", start, rest, [0], c, mass=0.08, bend=0.6, stiff=15.0, frames=110, gather_frames=35)
    return P, rest
