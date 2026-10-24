"""IV02 shared leaf silhouettes and atlas layout (pure Python; used by the atlas
baker and the Blender build so texture and geometry outlines are identical).

Leaf space: a across (-0.6..0.6), b from blade base (0.05) to tip (1.0).
UV space: Blender convention, v up. Atlas 2048 x 2048, power-of-two aligned cells
so box-filtered mips never mix two islands until the block exceeds the cell.
"""
import math

ATLAS_PX = 2048
GUTTER_PX = 24          # island inset inside its cell (>= 16 px contract minimum)
HUB = (0.0, 0.25)       # vein hub just above the cordate base notch (0, 0.19); petiole joins here

# IV01 five-lobed outline (historical, kept for comparison only). Its pointed base
# read as an inverted maple leaf in the IV02 atlas review, so IV02 uses HEDERA below.
IV01 = [(0, 1), (-.12, .76), (-.28, .77), (-.51, .84), (-.47, .62),
        (-.32, .53), (-.59, .45), (-.53, .27), (-.27, .29), (0, .05),
        (.27, .29), (.53, .27), (.59, .45), (.32, .53), (.47, .62),
        (.51, .84), (.28, .77), (.12, .76)]

# IV02 juvenile Hedera helix outline: terminal lobe, two lateral pairs, cordate base.
_HALF = [(-.07, .87), (-.15, .70), (-.46, .76), (-.43, .62), (-.30, .50),
         (-.58, .43), (-.52, .29), (-.36, .15), (-.16, .09)]
HEDERA = [(0, 1.0)] + _HALF + [(0, .19)] + [(-a, b) for a, b in reversed(_HALF)]
TIP_IDX = (0, 3, 6, 14, 17)   # terminal, upper-left, lower-left, lower-right, upper-right


def _smooth(pts, k):
    """Blend radii (about the hub) toward their neighbour average: shallower lobes."""
    hx, hy = 0.0, 0.45
    pol = [(math.atan2(y - hy, x - hx), math.hypot(x - hx, y - hy)) for x, y in pts]
    n = len(pol)
    out = []
    for i, (t, r) in enumerate(pol):
        ravg = (pol[i - 1][1] + r + pol[(i + 1) % n][1]) / 3
        rr = r * (1 - k) + ravg * k
        out.append((hx + rr * math.cos(t), hy + rr * math.sin(t)))
    return out


def _densify(pts, max_len=0.17, bulge=0.025):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(a)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L > max_len:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            # bulge outward from the hub so long lobe edges read as curves
            hx, hy = 0.0, 0.45
            dx, dy = mx - hx, my - hy
            d = math.hypot(dx, dy) or 1
            out.append((mx + dx / d * bulge * L / max_len, my + dy / d * bulge * L / max_len))
    return out


def _xform(pts, wx=1.0, tip=1.0):
    return [(x * wx, 0.05 + (y - 0.05) * (tip if y > 0.6 else 1.0)) for x, y in pts]


BASES = {
    'L0': HEDERA,
    'L1': _xform(HEDERA, wx=0.84, tip=1.12),            # narrower, longer terminal lobe
    'L2': _smooth(_xform(HEDERA, wx=1.05), 0.55),       # broad, shallow lobes
    'L3': _smooth(_xform(HEDERA, wx=0.94), 0.25),       # young leaf (lighter, glossier)
}
VARIANTS = {k: _densify(v) for k, v in BASES.items()}
VEIN_TIPS = {k: [v[i] for i in TIP_IDX] for k, v in BASES.items()}
LEAF_LOOK = {
    'L0': dict(rgb=(52, 88, 30), vein=(124, 146, 84), rough=0.60),
    'L1': dict(rgb=(44, 78, 27), vein=(116, 138, 78), rough=0.62),
    'L2': dict(rgb=(62, 97, 33), vein=(134, 154, 90), rough=0.64),
    'L3': dict(rgb=(98, 134, 46), vein=(160, 178, 102), rough=0.54),
}

# Cells in UV (u0, v0, u1, v1). Leaves 1024 px; young leaf and bark strips 512 px.
CELLS = {
    'L0': (0.0, 0.5, 0.5, 1.0),
    'L1': (0.5, 0.5, 1.0, 1.0),
    'L2': (0.0, 0.0, 0.5, 0.5),
    'L3': (0.5, 0.25, 0.75, 0.5),
    'Woody': (0.75, 0.25, 1.0, 0.5),
    'Branch': (0.5, 0.0, 0.75, 0.25),
    'Petiole': (0.75, 0.0, 1.0, 0.25),
}


def inset(cell, px=GUTTER_PX):
    d = px / ATLAS_PX
    u0, v0, u1, v1 = cell
    return (u0 + d, v0 + d, u1 - d, v1 - d)


def leaf_uv_map(name):
    """Return f(a, b) -> (u, v) placing the leaf outline inside its inset cell."""
    pts = VARIANTS[name]
    amin = min(p[0] for p in pts); amax = max(p[0] for p in pts)
    bmin = min(p[1] for p in pts); bmax = max(p[1] for p in pts)
    u0, v0, u1, v1 = inset(CELLS[name])
    s = min((u1 - u0) / (amax - amin), (v1 - v0) / (bmax - bmin))
    cu = (u0 + u1) / 2 - s * (amin + amax) / 2
    cv = (v0 + v1) / 2 - s * (bmin + bmax) / 2
    return lambda a, b: (cu + s * a, cv + s * b)


def strip_uv(name, around, along):
    """Tube islands: around in 0..1 (mirrored, seamless), along in 0..1."""
    u0, v0, u1, v1 = inset(CELLS[name])
    m = 0.5 - 0.5 * math.cos(2 * math.pi * around)
    return (u0 + (u1 - u0) * m, v0 + (v1 - v0) * along)
