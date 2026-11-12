"""MO01 Meredith's office: prepare the runtime texture sets (plain Python: numpy + Pillow; AIC images over the network).

    python prepare_textures.py [rug] [sheer]  (only those sets, merged into Material_Recipes.json)
Writes D:/AI_Modelling/hotel_eden/working/meredith_office_MO01/textures/T_MO01_* and Material_Recipes.json.
Conventions (hotel standard): BaseColor sRGB; NormalGL, ORM (R AO, G roughness, B metallic) and Height linear.
Sizes follow the owner's tiers (1K small/distant, 2K close-up, 4K only with a reason).
Colour targets are albedos judged against the reference (the reference itself is lit warm, so its pixels are not albedo).
"""
import hashlib, io, json, os, urllib.request
import numpy as np
from PIL import Image

W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
SRC = os.path.join(W, "sources"); TEX = os.path.join(W, "textures"); os.makedirs(TEX, exist_ok=True)
WS = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
PH = os.path.join(SRC, "polyhaven"); ACG = os.path.join(SRC, "ambientcg")
H = {"User-Agent": "HotelEdenMO01/1.0", "AIC-User-Agent": "HotelEdenMO01"}
REC = {}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load(p, mode="RGB"):
    im = Image.open(p)
    if im.mode in ("I;16", "I;16B", "I"):
        a = np.asarray(im, dtype=np.float32) / 65535.0
        return a if mode == "L" else np.stack([a] * 3, -1)
    return np.asarray(im.convert(mode), dtype=np.float32) / 255.0


def resize(a, w, h):
    if a.ndim == 2:
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 65535).astype(np.uint16)).resize((w, h), Image.LANCZOS), np.float32) / 65535
    return np.stack([resize(a[..., k], w, h) for k in range(a.shape[2])], -1)


def save(a, name, bits=8):
    p = os.path.join(TEX, name)
    a = np.clip(a, 0, 1)
    if bits == 16 and a.ndim == 2:
        Image.fromarray((a * 65535).astype(np.uint16)).save(p)
    else:
        Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(p)
    return {"file": name, "sha256": sha(p), "size": list(a.shape[1::-1])}


def s2l(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lum(lin):
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def grade(bc_srgb, target_srgb, keep_sat=1.0, contrast=1.0):
    """Move a texture's mean colour to target (sRGB 0-1) keeping its luminance pattern (in linear light)."""
    lin = s2l(bc_srgb); L = lum(lin); m = L.mean()
    rel = (L / max(m, 1e-6)) ** contrast
    chroma = lin / np.maximum(L[..., None], 1e-6)
    chroma = 1.0 + (chroma - 1.0) * keep_sat
    tl = s2l(np.asarray(target_srgb, np.float32))
    tL = lum(tl[None, None, :])[0, 0]
    tch = tl / max(tL, 1e-6)
    out = tL * rel[..., None] * tch[None, None, :] * (chroma / chroma.reshape(-1, 3).mean(0))
    return l2s(out)


def orm(ao, rough, metal=0.0):
    return np.stack([ao, rough, np.full_like(rough, metal)], -1)


def tile_set(prefix, bc, nrm, ao, rough, height, size, note, tile_m, metal=0.0):
    w, h = size
    files = dict(base_color=save(resize(bc, w, h), f"{prefix}_BaseColor.png"),
                 normal_gl=save(resize(nrm, w, h), f"{prefix}_NormalGL.png"),
                 orm=save(orm(resize(ao, w, h), resize(rough, w, h), metal), f"{prefix}_ORM.png"))
    if height is not None:
        files["height"] = save(resize(height, w, h), f"{prefix}_Height.png", 16)
    return dict(files=files, tile_m=tile_m, note=note)


# ------------------------------------------------------------------ sets
def parquet():
    d = os.path.join(PH, "herringbone_parquet")
    bc = load(os.path.join(d, "herringbone_parquet_diff_2k.png"))
    # the reference floor is a mid-dark warm brown; the source is light oak: darken, warm, keep the board variation
    bc = grade(bc, (0.36, 0.22, 0.13), keep_sat=0.9, contrast=1.15)
    ro = load(os.path.join(d, "herringbone_parquet_rough_2k.png"), "L")
    ro = np.clip(0.30 + (ro - ro.mean()) * 0.6, 0.18, 0.6)                      # waxed parquet satin
    REC["parquet"] = tile_set("T_MO01_Parquet", bc, load(os.path.join(d, "herringbone_parquet_nor_gl_2k.png")),
                              load(os.path.join(d, "herringbone_parquet_ao_2k.png"), "L"), ro,
                              load(os.path.join(d, "herringbone_parquet_disp_2k.png"), "L"), (2048, 2048),
                              "Poly Haven herringbone_parquet (CC0), graded to a mid-dark waxed walnut-brown", 3.4)


def firebrick():
    d = os.path.join(PH, "herringbone_brick")
    bc = grade(load(os.path.join(d, "herringbone_brick_diff_1k.png")), (0.30, 0.17, 0.11), keep_sat=0.8, contrast=1.1)
    ro = np.clip(load(os.path.join(d, "herringbone_brick_rough_1k.png"), "L") * 0.2 + 0.78, 0, 1)
    REC["firebrick"] = tile_set("T_MO01_FireBrick", bc, load(os.path.join(d, "herringbone_brick_nor_gl_1k.png")),
                                load(os.path.join(d, "herringbone_brick_ao_1k.png"), "L"), ro,
                                load(os.path.join(d, "herringbone_brick_disp_1k.png"), "L"), (1024, 1024),
                                "Poly Haven herringbone_brick (CC0): the reference's herringbone firebox lining; soot is added per vertex", 1.8)


def marble(aid, res, prefix, target, rough_mean, size, tile_m, note):
    d = os.path.join(ACG, aid)
    bc = load(os.path.join(d, f"{aid}_{res}_Color.jpg"))
    if target is not None:
        bc = grade(bc, target, keep_sat=0.7, contrast=1.0)
    ro = load(os.path.join(d, f"{aid}_{res}_Roughness.jpg"), "L")
    ro = np.clip(rough_mean + (ro - ro.mean()) * 0.5, 0.05, 0.6)
    REC[prefix] = tile_set(f"T_MO01_{prefix}", bc, load(os.path.join(d, f"{aid}_{res}_NormalGL.jpg")), np.ones_like(ro), ro,
                           load(os.path.join(d, f"{aid}_{res}_Displacement.jpg"), "L"), size, note, tile_m)


def velvet():
    d = "D:/AI_Modelling/hotel_eden/working/furnishings_S03/materials/velour_velvet"
    bc = load(os.path.join(d, "velour_velvet_diff_4k.png"))
    # source is red velvet; the reference drapes are a muted sage-green velvet with light sheen
    bc = grade(bc, (0.36, 0.41, 0.31), keep_sat=0.25, contrast=1.0)
    ro = load(os.path.join(d, "velour_velvet_rough_4k.png"), "L")
    REC["velvet"] = tile_set("T_MO01_Velvet", bc, load(os.path.join(d, "velour_velvet_nor_gl_4k.png")), np.ones_like(ro),
                             np.clip(ro * 0.6 + 0.35, 0, 1), None, (1024, 1024),
                             "Poly Haven velour_velvet (CC0, as on the approved S03 settee), regraded to the reference's sage green", 0.284)


def sheer():
    d = os.path.join(PH, "crepe_georgette")
    bc = load(os.path.join(d, "crepe_georgette_diff_1k.png"))
    L = lum(s2l(bc)); rel = L / L.mean()
    base = s2l(np.array([0.93, 0.91, 0.86], np.float32))
    bcw = l2s(np.clip(base[None, None, :] * (0.92 + 0.08 * rel[..., None]), 0, 1))
    ro = load(os.path.join(d, "crepe_georgette_rough_1k.png"), "L")
    REC["sheer"] = tile_set("T_MO01_Sheer", bcw, load(os.path.join(d, "crepe_georgette_nor_gl_1k.png")), np.ones_like(ro),
                            np.clip(ro * 0.3 + 0.6, 0, 1), None, (1024, 1024),
                            "Poly Haven crepe_georgette (CC0) weave, ivory; opacity 0.55 in the material", 0.261)
    REC["sheer"]["opacity"] = 0.55


def wallpaper():
    """The owner-approved PW01 damask recoloured tone-on-tone to the reference's olive-grey, at 70 % scale."""
    d = os.path.join(WS, "review-media", "passageway-walls-pw01", "textures")
    bc = load(os.path.join(d, "T_PW01_Wallpaper_BaseColor.png"))
    L = lum(s2l(bc))
    lo, hi = np.percentile(L, 8), np.percentile(L, 92)
    m = np.clip((L - lo) / (hi - lo), 0, 1)                            # 0 ground .. 1 print
    ground = s2l(np.array([0.355, 0.370, 0.285], np.float32)); motif = s2l(np.array([0.425, 0.430, 0.335], np.float32))
    fine = (L / np.maximum(lo + m * (hi - lo), 1e-6))                   # keep the paper's fine texture
    lin = (ground[None, None, :] * (1 - m[..., None]) + motif[None, None, :] * m[..., None]) * np.clip(fine, 0.85, 1.15)[..., None]
    o = load(os.path.join(d, "T_PW01_Wallpaper_ORM.png"))
    REC["wallpaper"] = dict(files=dict(base_color=save(l2s(lin), "T_MO01_Wallpaper_BaseColor.png"),
                                       normal_gl=save(load(os.path.join(d, "T_PW01_Wallpaper_NormalGL.png")), "T_MO01_Wallpaper_NormalGL.png"),
                                       orm=save(o, "T_MO01_Wallpaper_ORM.png")),
                            tile_m=[0.539 * 0.70, 0.613 * 0.70],
                            note="PW01 damask (owner-chosen corridor paper) recoloured tone-on-tone olive-grey after the reference, at 0.70 scale")


def aic(i, image_id, w_try=("1686,", "843,")):
    p = os.path.join(SRC, "aic", f"AIC_{i}.jpg")
    if not os.path.exists(p):
        for w in w_try:
            try:
                b = urllib.request.urlopen(urllib.request.Request(f"https://www.artic.edu/iiif/2/{image_id}/full/{w}/0/default.jpg", headers=H), timeout=120).read()
                open(p, "wb").write(b); break
            except Exception as e:
                print("AIC", i, w, e)
    return p


def aic_meta(i):
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.artic.edu/api/v1/artworks/{i}?fields=id,title,artist_display,date_display,image_id,is_public_domain", headers=H), timeout=60).read())["data"]
    assert r["is_public_domain"], i
    return r


def portraits():
    import mo01_spec as S
    aspect = S.AF02_OPEN[0] / S.AF02_OPEN[1]
    TWp, THp = 1024, 2048                               # four 1024 x 2048 slots? no: 2 x 2 slots in a 2048 square
    N = 2048; TW, TH = N // 2, N // 2
    atlas = np.zeros((N, N, 3), np.float32) + 0.05
    tiles = []
    for k, P in enumerate(S.PORTRAITS):
        r = aic_meta(P["aic"]); p = aic(P["aic"], r["image_id"])
        im = Image.open(p).convert("RGB"); w, h = im.size
        m = int(0.02 * min(w, h)); im = im.crop((m, m, w - m, h - m)); w, h = im.size
        if w / h > aspect:
            nw = int(h * aspect); x0 = (w - nw) // 2; box = (x0, 0, x0 + nw, h)
        else:
            nh = int(w / aspect); y0 = int((h - nh) * 0.30); box = (0, y0, w, y0 + nh)
        im = im.crop(box)
        ch = int(TH * 0.98); cw = int(ch * aspect)
        t = np.asarray(im.resize((cw, ch), Image.LANCZOS), dtype=np.float32) / 255
        c, rr = k % 2, k // 2
        x, y = c * TW + (TW - cw) // 2, rr * TH + (TH - ch) // 2
        atlas[y:y + ch, x:x + cw] = t
        tiles.append(dict(name=P["name"], aic=P["aic"], title=r["title"], artist=r["artist_display"], date=r["date_display"],
                          page=f"https://www.artic.edu/artworks/{P['aic']}", license="CC0 (Art Institute of Chicago public-domain image)",
                          sha256=sha(p), uv=[x / N, 1 - (y + ch) / N, (x + cw) / N, 1 - y / N]))
    REC["portraits"] = dict(files=dict(base_color=save(atlas, "T_MO01_Portraits_BaseColor.png")), tiles=tiles,
                            canvas_normal="EC01 T_EC01_Canvas_NormalGL.png (0.05 m tile)", varnish_roughness=0.42)


def rug():
    """The AIC 22030 Ushak at the museum's full image size (1601 x 2250), restored a little after the owner's third
    review ("larger and a bit more vibrant/less worn"): worn specks in the plain grounds repaired, the fading evened
    within each colour, and the colour lifted. The design, its guard lines and the medallion are untouched."""
    import cv2
    i = 22030
    r = aic_meta(i)
    p = os.path.join(SRC, "aic", f"AIC_{i}_full.jpg")
    if not os.path.exists(p):
        b = urllib.request.urlopen(urllib.request.Request(f"https://www.artic.edu/iiif/2/{r['image_id']}/full/1601,/0/default.jpg",
                                                          headers=H), timeout=120).read()
        open(p, "wb").write(b)
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
    # crop to the woven body: background is a flat grey; the knotted field is saturated and darker
    sat = a.max(-1) - a.min(-1)
    rows = np.where((sat > 0.12).mean(1) > 0.6)[0]; cols = np.where((sat > 0.12).mean(0) > 0.6)[0]
    y0, y1, x0, x1 = rows[0], rows[-1], cols[0], cols[-1]
    pad_x, pad_y = int(0.012 * (x1 - x0)), int(0.025 * (y1 - y0))      # shave the selvedge and the fringe roots
    body = a[y0 + pad_y:y1 - pad_y, x0 + pad_x:x1 - pad_x].copy()
    u8 = (body * 255 + 0.5).astype(np.uint8)
    lab = cv2.cvtColor(u8, cv2.COLOR_RGB2LAB).astype(np.float32)       # OpenCV Lab: L 0-255, a/b offset 128
    # 1. worn specks: only inside the large plain grounds (red field, navy border ground); small blobs only, so the
    #    thin guard lines and the motifs are never touched. Repaired by inpainting, with the pile grain put back.
    med = cv2.medianBlur(u8, 31)
    mlab = cv2.cvtColor(med, cv2.COLOR_RGB2LAB).astype(np.float32)
    grounds = np.zeros(u8.shape[:2], np.uint8)
    for ref in ([55, 161, 145], [16, 130, 122]):
        near = (np.sqrt(((mlab - np.array(ref, np.float32)) ** 2).sum(-1)) < 16).astype(np.uint8)
        near = cv2.morphologyEx(near, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
        grounds |= cv2.erode(near, np.ones((11, 11), np.uint8))
    dev = np.sqrt(((lab - mlab) ** 2 * np.array([1.0, 1.4, 1.4])).sum(-1))
    spot = cv2.morphologyEx(((dev > 14) & (grounds > 0)).astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, cc, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(spot, np.ones((3, 3), np.uint8)), connectivity=8)
    keep = np.zeros(n, bool); keep[1:] = (np.maximum(st[1:, 2], st[1:, 3]) < 48) & (st[1:, 4] < 1400)
    spot = (keep[cc] & (spot > 0)).astype(np.uint8)
    spot = cv2.dilate(spot, np.ones((5, 5), np.uint8)) & cv2.dilate(grounds, np.ones((3, 3), np.uint8))
    fixed = cv2.inpaint(u8, spot * 255, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255
    grain = np.roll(body - cv2.GaussianBlur(body, (0, 0), 2.0), (37, 53), (0, 1))
    m = cv2.GaussianBlur(spot.astype(np.float32), (0, 0), 1.5)[..., None]
    rep_ = np.clip(body * (1 - m) + (fixed + grain * 0.9) * m, 0, 1)
    # 2. even the fading: within each colour (k-means in Lab), pull the low-frequency colour 60 % towards its mean
    small = cv2.resize(rep_, (rep_.shape[1] // 4, rep_.shape[0] // 4), interpolation=cv2.INTER_AREA)
    sl = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    cv2.setRNGSeed(22030)
    _, _, cen = cv2.kmeans(sl, 9, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 4, cv2.KMEANS_PP_CENTERS)
    rl = cv2.cvtColor((rep_ * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    cls = ((rl[..., None, :] - cen[None, None]) ** 2).sum(-1).argmin(-1)
    out = rl.copy()
    for k in range(len(cen)):
        M = (cls == k).astype(np.float32)
        if M.mean() < 0.01:
            continue
        den = cv2.GaussianBlur(M, (0, 0), 40) + 1e-4
        loc = np.stack([cv2.GaussianBlur(rl[..., c] * M, (0, 0), 40) / den for c in range(3)], -1)
        corr = ((rl * M[..., None]).reshape(-1, 3).sum(0) / M.sum() - loc) * 0.6
        corr[..., 0] = np.clip(corr[..., 0], -18, 18); corr[..., 1:] = np.clip(corr[..., 1:], -10, 10)
        out += corr * M[..., None]
    # 3. a little more vibrant: chroma x1.35 (less on colours already saturated), slightly brighter
    A, B = out[..., 1] - 128, out[..., 2] - 128
    gain = 1 + 0.35 * (1 - np.clip(np.sqrt(A * A + B * B) / 90, 0, 1) * 0.5)
    L = 255 * (np.clip(out[..., 0] / 255, 0, 1) ** 0.92) * 1.05
    res = np.stack([np.clip(L, 0, 255), np.clip(A * gain + 128, 0, 255), np.clip(B * gain + 128, 0, 255)], -1).astype(np.uint8)
    res = cv2.cvtColor(res, cv2.COLOR_LAB2RGB).astype(np.float32) / 255
    h, w = res.shape[:2]
    REC["rug"] = dict(files=dict(base_color=save(resize(res, 1024, 2048), "T_MO01_Rug_BaseColor.png")),
                      crop_px=[int(x0 + pad_x), int(y0 + pad_y), int(x1 - pad_x), int(y1 - pad_y)], aspect_w_over_l=round(w / h, 4),
                      restoration=dict(worn_specks_repaired_pct=round(100 * float(spot.mean()), 1), fading_evened=0.6, chroma=1.35,
                                       note="owner, third review: larger and a bit more vibrant/less worn"),
                      size_note="1024 x 2048 (power of two for Unreal mips) from the 1307 x 1961 px woven body",
                      source=dict(aic=i, title=r["title"], artist=r["artist_display"], date=r["date_display"], image_px=[1601, 2250],
                                  page=f"https://www.artic.edu/artworks/{i}", license="CC0 (Art Institute of Chicago public-domain image)", sha256=sha(p)),
                      pile="ambientCG Carpet001 NormalGL (owner-approved rug pile, F26), tiled 6 per metre on UV1",
                      note="Woven body of a 17th-century Ushak double-ended prayer rug: red field, navy borders, central medallion (as the reference)")


def fringe():
    """Gold bullion fringe for the valance hem: an alpha card (twisted cords) with normal and AO. 512 x 128 over 0.20 x 0.05 m."""
    Wp, Hp = 512, 128
    x = np.linspace(0, 1, Wp, endpoint=False)[None, :]; y = np.linspace(0, 1, Hp)[:, None]
    n_cords = 40
    ph = x * n_cords
    cord = np.abs((ph % 1.0) - 0.5) * 2                          # 0 at cord centre .. 1 between
    width = 0.62 - 0.08 * y                                      # cords taper slightly
    alpha = (cord < width).astype(np.float32)
    alpha[: int(Hp * 0.18)] = 1.0                                # woven heading
    hgt = np.sqrt(np.clip(1 - (cord / np.maximum(width, 1e-3)) ** 2, 0, 1)) * alpha
    twist = 0.5 + 0.5 * np.sin(2 * np.pi * (y * 9 + ph * 0.5))
    hgt = hgt * (0.75 + 0.25 * twist)
    hgt[: int(Hp * 0.18)] = 0.6 + 0.2 * np.sin(2 * np.pi * x[0] * n_cords * 2)[None, :]
    gy, gx = np.gradient(hgt)
    n = np.stack([-gx * 6, gy * 6, np.ones_like(hgt)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    gold = l2s(s2l(np.array([0.70, 0.55, 0.26])) * (0.55 + 0.45 * hgt[..., None]))
    rgba = np.concatenate([gold, alpha[..., None]], -1)
    p = os.path.join(TEX, "T_MO01_Fringe_BaseColorAlpha.png"); Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").save(p)
    REC["fringe"] = dict(files=dict(base_color_alpha={"file": os.path.basename(p), "sha256": sha(p)},
                                    normal_gl=save(n * 0.5 + 0.5, "T_MO01_Fringe_NormalGL.png")), size_m=[0.20, 0.05],
                         note="procedural twisted-cord bullion fringe (alpha card), gold")


def main():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    only = [a for a in sys.argv[1:] if a in ("rug", "sheer")]
    if only:                                            # only these sets, merged into the existing recipes
        rp = os.path.join(W, "Material_Recipes.json")
        REC.update(json.load(open(rp)))
        for fn in only:
            globals()[fn]()
        json.dump(REC, open(rp, "w"), indent=1)
        print("TEXTURES OK", only)
        return
    parquet(); firebrick()
    marble("Marble018", "2K-JPG", "Marble", (0.86, 0.84, 0.79), 0.16, (2048, 2048), 1.0,
           "ambientCG Marble018 (CC0), warm statuary white, honed-polished; the mantel and hearth")
    marble("Marble016", "1K-JPG", "BlackMarble", None, 0.14, (1024, 1024), 0.6,
           "ambientCG Marble016 (CC0), black veined marble; the slip round the fire opening")
    velvet(); sheer(); wallpaper(); fringe(); portraits(); rug()
    json.dump(REC, open(os.path.join(W, "Material_Recipes.json"), "w"), indent=1)
    print("TEXTURES OK", sorted(REC))


if __name__ == "__main__":
    main()
