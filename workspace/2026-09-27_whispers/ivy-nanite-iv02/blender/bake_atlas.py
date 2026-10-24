"""IV02 S3: paint the padded 2048^2 ivy atlas (base colour sRGB, tangent normal
OpenGL +Y linear, roughness linear) from the shared leaf outlines.

Run with system Python 3 (numpy, Pillow):  python bake_atlas.py <ivy_IV02 root>
Deterministic: seed 24024. Writes textures/ and qa/atlas_report.json.
"""
import sys, json, math, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivy_shapes as S

ROOT = Path(sys.argv[1])
TEX = ROOT / 'textures'; TEX.mkdir(exist_ok=True)
QA = ROOT / 'qa'; QA.mkdir(exist_ok=True)
N = S.ATLAS_PX
rng = np.random.default_rng(24024)

base = np.zeros((N, N, 3), np.float32)
height = np.zeros((N, N), np.float32)
rough = np.zeros((N, N), np.float32)
owner = np.full((N, N), -1, np.int16)        # which island each texel belongs to (cell)
footprint = np.zeros((N, N), np.int16) - 1   # actual UV footprint (mask) per island
names = list(S.CELLS)


def cell_px(cell):
    u0, v0, u1, v1 = cell
    return int(round(u0 * N)), int(round((1 - v1) * N)), int(round(u1 * N)), int(round((1 - v0) * N))


def value_noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    gh, gw = int(h / scale) + 3, int(w / scale) + 3
    g = r.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((int(gw * scale), int(gh * scale)), Image.BICUBIC)
    return np.asarray(img, np.float32)[:h, :w] / 255.0


def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy)), t


for idx, name in enumerate(names):
    x0, y0, x1, y1 = cell_px(S.CELLS[name])
    h, w = y1 - y0, x1 - x0
    owner[y0:y1, x0:x1] = idx
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    u = (xs + 0.5) / N; v = 1 - (ys + 0.5) / N
    if name.startswith('L'):
        f = S.leaf_uv_map(name)
        # invert the affine map: u = cu + s*a, v = cv + s*b
        (ua, va), (ub, vb) = f(0, 0), f(1, 1)
        s = ub - ua
        a = (u - ua) / s; b = (v - va) / s
        look = S.LEAF_LOOK[name]
        hub = S.HUB
        vein = np.zeros_like(a); t_along = np.zeros_like(a)
        for tx, ty in S.VEIN_TIPS[name]:
            d, t = seg_dist(a, b, hub[0], hub[1], tx, ty)
            width = 0.015 * (1 - 0.7 * t)
            vein = np.maximum(vein, np.exp(-(d / width) ** 2))
            # secondary veins branching from each main vein
            for k in (0.35, 0.6):
                mx, my = hub[0] + (tx - hub[0]) * k, hub[1] + (ty - hub[1]) * k
                ang = math.atan2(ty - hub[1], tx - hub[0])
                for sgn in (-1, 1):
                    ex = mx + 0.18 * math.cos(ang + sgn * 0.7); ey = my + 0.18 * math.sin(ang + sgn * 0.7)
                    d2, t2 = seg_dist(a, b, mx, my, ex, ey)
                    vein = np.maximum(vein, 0.55 * np.exp(-(d2 / (0.010 * (1 - 0.6 * t2))) ** 2))
        mott = value_noise(h, w, 22, 24024 + idx)
        fine = value_noise(h, w, 5, 24124 + idx)
        r = np.hypot(a - hub[0], b - hub[1])
        rgb = np.array(look['rgb'], np.float32)[None, None, :]
        col = rgb * (0.86 + 0.20 * mott[..., None] + 0.06 * fine[..., None]) * (1.04 - 0.10 * np.clip(r, 0, 0.8)[..., None])
        col = col * (1 - 0.75 * vein[..., None]) + np.array(look['vein'], np.float32) * 0.75 * vein[..., None]
        # mask (actual geometric silhouette) with 4x supersampling
        poly = [(((ua + s * pa) * N - x0) * 4, ((1 - (va + s * pb)) * N - y0) * 4) for pa, pb in S.VARIANTS[name]]
        im = Image.new('L', (w * 4, h * 4), 0); ImageDraw.Draw(im).polygon(poly, fill=255)
        mask = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        # subtle darker rim just inside the silhouette (no rim outside, so dilation is continuous)
        inner = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
        rim = np.clip((1 - inner) * 2, 0, 1) * (mask > 0.5)
        col *= (1 - 0.12 * rim[..., None])
        base[y0:y1, x0:x1] = col
        height[y0:y1, x0:x1] = -0.55 * vein + 0.25 * mott + 0.05 * fine
        rough[y0:y1, x0:x1] = look['rough'] + 0.10 * vein + 0.06 * (mott - 0.5)
        footprint[y0:y1, x0:x1][mask > 0.0] = idx
    else:
        iu0, iv0, iu1, iv1 = S.inset(S.CELLS[name])
        around = np.clip((u - iu0) / (iu1 - iu0), 0, 1)
        streak = value_noise(h, 2 * w, 3, 24200 + idx)[:, :w]
        streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((w, 4)).resize((w, h)), np.float32) / 255
        mott = value_noise(h, w, 30, 24300 + idx)
        ridge = 0.5 + 0.5 * np.sin(around * math.pi * 14 + 3 * streak)
        if name == 'Woody':
            rgb = np.array((78, 64, 46), np.float32); rr = 0.86
        elif name == 'Branch':
            rgb = np.array((84, 76, 48), np.float32); rr = 0.78
        else:
            rgb = np.array((70, 86, 40), np.float32); rr = 0.60
        col = rgb * (0.80 + 0.25 * streak[..., None] + 0.10 * mott[..., None]) * (0.85 + 0.15 * ridge[..., None])
        if name == 'Petiole':  # faint red-purple flush, typical of ivy petioles
            col = col * (1 - 0.25 * mott[..., None]) + np.array((92, 52, 46), np.float32) * 0.25 * mott[..., None]
        base[y0:y1, x0:x1] = col
        height[y0:y1, x0:x1] = 0.6 * ridge * (1.0 if name == 'Woody' else 0.4) + 0.2 * streak
        rough[y0:y1, x0:x1] = rr + 0.06 * (streak - 0.5)
        fp = (u >= iu0) & (u <= iu1) & (v >= iv0) & (v <= iv1)
        footprint[y0:y1, x0:x1][fp] = idx

# Normal from height, computed per cell so gradients never cross an island boundary.
nrm = np.zeros((N, N, 3), np.float32)
for idx, name in enumerate(names):
    x0, y0, x1, y1 = cell_px(S.CELLS[name])
    hh = height[y0:y1, x0:x1]
    gy, gx = np.gradient(hh)
    k = 3.0 if name.startswith('L') else 6.0
    nx, ny = -gx * k, gy * k          # image rows grow downward; +Y (green) = up in UV v (OpenGL)
    n = np.stack((nx, ny, np.ones_like(hh)), -1)
    nrm[y0:y1, x0:x1] = n / np.linalg.norm(n, axis=-1, keepdims=True)
unused = owner < 0
base[unused] = (50, 80, 35); nrm[unused] = (0, 0, 1); rough[unused] = 0.6

bc8 = np.clip(base, 0, 255).astype(np.uint8)
n8 = np.clip((nrm * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)
r8 = np.clip(rough * 255 + 0.5, 0, 255).astype(np.uint8)
files = {'T_Ivy_Atlas_BaseColor.png': Image.fromarray(bc8, 'RGB'),
         'T_Ivy_Atlas_Normal.png': Image.fromarray(n8, 'RGB'),
         'T_Ivy_Atlas_Roughness.png': Image.fromarray(r8, 'L')}
out = {}
for fn, im in files.items():
    im.save(TEX / fn, optimize=True)
    out[fn] = hashlib.sha256((TEX / fn).read_bytes()).hexdigest()
Image.fromarray(((footprint + 1) * 30).astype(np.uint8)).save(QA / 'atlas_footprint_ids.png')

# Gutter: distance (px) from each island's footprint to any texel owned by another cell.
gut = {}
for idx, name in enumerate(names):
    # cells are axis-aligned rectangles, so the nearest foreign texel lies across the cell border
    x0, y0, x1, y1 = cell_px(S.CELLS[name])
    yy, xx = np.nonzero(footprint == idx)
    gut[name] = int(min((xx - x0).min(), (x1 - 1 - xx).min(), (yy - y0).min(), (y1 - 1 - yy).min()))

# Mip bleed: box mips; first level where a block containing this island's footprint mixes another cell.
mips = {}
for idx, name in enumerate(names):
    first = None
    for m in range(0, 12):
        bsz = 2 ** m
        o = owner.reshape(N // bsz, bsz, N // bsz, bsz)
        f = (footprint == idx).reshape(N // bsz, bsz, N // bsz, bsz).any(axis=(1, 3))
        mixed = (o != idx).any(axis=(1, 3))
        if np.any(f & mixed):
            first = m; break
    mips[name] = first

stats = {}
for idx, name in enumerate(names):
    fp = footprint == idx
    stats[name] = {'footprint_px': int(fp.sum()),
                   'base_mean_srgb': [round(float(c), 1) for c in base[fp].mean(0)],
                   'roughness_mean': round(float(rough[fp].mean()), 3),
                   'roughness_std': round(float(rough[fp].std()), 3),
                   'base_luma_std': round(float(base[fp].mean(1).std()), 2)}
rep = {'resolution': [N, N], 'seed': 24024, 'cells_uv': S.CELLS, 'inset_px': S.GUTTER_PX,
       'files_sha256': out,
       'colour_spaces': {'BaseColor': 'sRGB', 'Normal': 'linear, tangent space, OpenGL +Y (green up). Unreal: enable Flip Green Channel', 'Roughness': 'linear (single channel)'},
       'no_alpha': True,
       'gutter_px_min_to_foreign_cell': gut,
       'first_mip_with_cross_island_mixing': mips,
       'island_stats': stats,
       'texel_density_note': 'leaf cells ~976 px per ~0.14 m leaf at mip 0; at 10 m on 1080p/90deg (~0.0104 m/px) the sampled mip is ~6, blocks 64 px, inside every cell'}
(QA / 'atlas_report.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
print('IV02_ATLAS', out, gut, mips)
