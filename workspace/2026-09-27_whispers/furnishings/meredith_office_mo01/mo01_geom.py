"""MO01 geometry helpers (pure Python + numpy, no bpy): parts are dicts verts/faces/uv0/uv1/mat as in ec01_geom.

Mantel frame: X along the wall (0 = mantel centre), Y out of the breast face (0 = face), Z up from the floor top.
"""
import math
import numpy as np

S_ = "S"


def chaikin(ctrl, iters):
    pts = [(p[0], p[1], p[2] if len(p) > 2 else "") for p in ctrl]
    for _ in range(iters):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            q = (0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1], "")
            r = (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1], "")
            if a[2] == S_ or i == 0:
                q = None
            if b[2] == S_ or i == len(pts) - 2:
                r = None
            if q:
                out.append(q)
            if r:
                out.append(r)
            if i + 1 < len(pts) - 1 and b[2] == S_:
                out.append(b)
        out.append(pts[-1])
        ded = [out[0]]
        for p in out[1:]:
            if abs(p[0] - ded[-1][0]) > 1e-9 or abs(p[1] - ded[-1][1]) > 1e-9:
                ded.append(p)
        pts = ded
    return [(p[0], p[1]) for p in pts]


def empty():
    return dict(verts=[], faces=[], uv0=[], uv1=[], mat=[])


def add(part, verts, faces, mat=0, uv1=None):
    o = len(part["verts"])
    part["verts"] += [tuple(v) for v in verts]
    for k, f in enumerate(faces):
        part["faces"].append(tuple(i + o for i in f))
        part["mat"].append(mat)
        part["uv0"].append([(0.0, 0.0)] * len(f))
        part["uv1"].append(uv1[k] if uv1 else [(0.0, 0.0)] * len(f))


def newell(vs):
    nx = ny = nz = 0.0
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def orient(part, start=0, ref_point=None, out_dir=None):
    """Flip faces from index start on: per face against (centre - ref_point), or all of them against out_dir."""
    V = part["verts"]; F = part["faces"]
    idx = range(start, len(F))
    if out_dir is not None:
        tot = 0.0
        for i in idx:
            n = newell([V[k] for k in F[i]]); tot += n[0] * out_dir[0] + n[1] * out_dir[1] + n[2] * out_dir[2]
        flip = list(idx) if tot < 0 else []
    else:
        flip = []
        for i in idx:
            vs = [V[k] for k in F[i]]; n = newell(vs)
            c = [sum(v[j] for v in vs) / len(vs) for j in range(3)]
            d = [c[j] - ref_point[j] for j in range(3)]
            if n[0] * d[0] + n[1] * d[1] + n[2] * d[2] < 0:
                flip.append(i)
    for i in flip:
        F[i] = tuple(reversed(F[i])); part["uv0"][i] = list(reversed(part["uv0"][i])); part["uv1"][i] = list(reversed(part["uv1"][i]))
    return part


def box(part, x0, x1, y0, y1, z0, z1, mat=0, skip=()):
    """Outward-facing box quads; skip = names of faces to omit ('-y' is the wall side)."""
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4), "+y": (2, 3, 7, 6), "-x": (3, 0, 4, 7), "+x": (1, 2, 6, 5)}
    faces = [f for k, f in F.items() if k not in skip]
    add(part, P, faces, mat)


def frame_with_hole(part, x0, x1, z0, z1, hx0, hx1, hz0, hz1, y, mat=0, normal_y=1):
    """A flat vertical panel at depth y (facing +y or -y) over [x0,x1]x[z0,z1] with a rectangular hole."""
    xs = [x0, hx0, hx1, x1]; zs = [z0, hz0, hz1, z1]
    for i in range(3):
        for j in range(3):
            if i == 1 and j <= 1 and hz0 <= z0 + 1e-9:
                if j == 0:
                    continue
            if i == 1 and j == 1:
                continue
            if i == 1 and j == 0 and hz0 <= z0 + 1e-9:
                continue
            a, b, c, d = (xs[i], y, zs[j]), (xs[i + 1], y, zs[j]), (xs[i + 1], y, zs[j + 1]), (xs[i], y, zs[j + 1])
            if abs(xs[i + 1] - xs[i]) < 1e-9 or abs(zs[j + 1] - zs[j]) < 1e-9:
                continue
            f = [a, d, c, b] if normal_y > 0 else [a, b, c, d]
            n = newell(f)
            if n[1] * normal_y < 0:
                f = f[::-1]
            add(part, f, [(0, 1, 2, 3)], mat)


def sweep_open(path, prof, closed=False):
    """Sweep a profile [(w, h)] along a horizontal path [(x, y)]: w offsets to the LEFT of the path, h is height.
    Returns verts, faces (quads)."""
    n = len(path)
    def off(i, w):
        if closed:
            p0, p1, p2 = path[i - 1], path[i], path[(i + 1) % n]
        else:
            p0 = path[i - 1] if i > 0 else None; p1 = path[i]; p2 = path[i + 1] if i < n - 1 else None
        t0 = norm2((p1[0] - p0[0], p1[1] - p0[1])) if p0 else None
        t1 = norm2((p2[0] - p1[0], p2[1] - p1[1])) if p2 else None
        t0 = t0 or t1; t1 = t1 or t0
        n0 = (-t0[1], t0[0]); n1 = (-t1[1], t1[0])
        m = norm2((n0[0] + n1[0], n0[1] + n1[1])); c = m[0] * n1[0] + m[1] * n1[1]
        k = w / max(c, 0.2)
        return (p1[0] + m[0] * k, p1[1] + m[1] * k)
    verts, idx = [], []
    for w, h in prof:
        idx.append([])
        for i in range(n):
            x, y = off(i, w); idx[-1].append(len(verts)); verts.append((x, y, h))
    faces = []
    segs = range(n if closed else n - 1)
    for k in range(len(prof) - 1):
        for i in segs:
            j = (i + 1) % n
            faces.append((idx[k][i], idx[k][j], idx[k + 1][j], idx[k + 1][i]))
    return verts, faces


def norm2(v):
    L = math.hypot(v[0], v[1])
    return (v[0] / L, v[1] / L) if L > 1e-12 else None


# ------------------------------------------------------------------ mantel profiles (w = projection beyond the base line, h = height)
# shelf edge: fillet, ovolo, fillet, cavetto back under to the bed line; heights relative to the shelf bottom
SHELF_EDGE = [(0.000, 0.000, S_), (0.030, 0.000, S_), (0.036, 0.004, ""), (0.040, 0.012, S_), (0.040, 0.016, S_), (0.046, 0.026, ""),
              (0.052, 0.044, ""), (0.050, 0.060, S_), (0.046, 0.066, S_), (0.046, 0.075, S_), (0.000, 0.075, S_)]
# bed moulding under the shelf (cyma reversa), heights below the shelf bottom
BED = [(0.000, -0.050, S_), (0.004, -0.050, S_), (0.010, -0.040, ""), (0.016, -0.026, ""), (0.024, -0.012, ""), (0.030, -0.006, S_),
       (0.030, 0.000, S_), (0.000, 0.000, S_)]
# bead at the frieze bottom
BEAD = [(0.000, -0.020, S_), (0.006, -0.018, ""), (0.012, -0.010, ""), (0.012, 0.000, ""), (0.006, 0.008, ""), (0.000, 0.010, S_)]


def corbel_outline(z0, z1, n=60, base=0.024, bot=(0.07, 0.042, 0.055), top=(0.80, 0.112, 0.16), crown=0.075):
    """S-scroll console seen from the side: (y_out, z) of its front edge from the bottom scroll to the top scroll.
    y = base + a small bump low (bottom scroll) + a big rounded bump high (top scroll), easing to `crown` at the top
    where it meets the shelf. bot/top = (centre t, amplitude, width)."""
    H = z1 - z0
    pts = []
    for k in range(n + 1):
        t = k / n
        y = base + bot[1] * math.exp(-((t - bot[0]) / bot[2]) ** 2) + top[1] * math.exp(-((t - top[0]) / top[2]) ** 2)
        if t > top[0]:
            y = max(y, crown * min(1.0, (t - top[0]) / (1 - top[0]) * 1.4))
        pts.append((y, z0 + t * H))
    return pts


def volute(cx, cz, r0, turns=1.6, n=48, sign=1):
    """Spiral (y, z) points around (cx, cz) shrinking from r0: the scroll eyes on the console sides."""
    out = []
    for k in range(n + 1):
        t = k / n
        a = sign * 2 * math.pi * turns * t
        r = r0 * (1 - 0.72 * t)
        out.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return out
