"""MO01 books: the spine atlas shared by every book in the office (plain Python: numpy + Pillow).

    python prepare_books.py
Owner, 12 Nov 2026 (second review): "Model the books, candalabra and the clock in final game model quality and deliver
them with the room."

The library is 36 period sets (192 volumes): calf and morocco bindings with raised bands, gilt rules, fleurons and
lettering pieces; half bindings with marbled sides; Victorian publisher's cloth; vellum; and plain worn calf. Each
volume has its own spine cell, sized to the book at DENS px/m (the spine is a rounded arc, ARC x the book's thickness).
Each set has a cover swatch (its leather, cloth, marbled paper or vellum, unfaded: spines fade, sides do not) and an
edge style (plain, gilt, red sprinkled or marbled). Wear: rubbed joints and caps, scuffs, worn gilt, sun-faded spines.

Writes textures/T_MO01_Books_{BaseColor,NormalGL,ORM}.png (2048; BaseColor sRGB; ORM = AO, roughness, metallic) and
Books_Atlas.json (cells in pixels from the top-left, sizes in metres), and review-media/.../kit/MO01_Books_Atlas.png.
Sources: ambientCG Leather021 (CC0) for the grain and its mottling; lettering set in Garamond / Baskerville (Windows
fonts, rasterised into the texture). Titles are public-domain works of the 18th and 19th centuries.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
TEX = os.path.join(W, "textures"); LEA = os.path.join(W, "sources", "ambientcg", "Leather021")
WS = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers"
ATLAS, SPINE_REGION, SS, PAD, ARC = 2048, 1836, 3, 4, 1.085
SW = 96                                                  # cover / edge swatch size
FONT = {"bold": "C:/Windows/Fonts/GARABD.TTF", "reg": "C:/Windows/Fonts/GARA.TTF", "ital": "C:/Windows/Fonts/GARAIT.TTF",
        "cloth": "C:/Windows/Fonts/BASKVILL.TTF"}
FORMATS = {"folio": (0.375, 0.255, 0.055, 0.075), "quarto": (0.285, 0.222, 0.040, 0.058), "large8": (0.248, 0.160, 0.032, 0.050),
           "octavo": (0.226, 0.146, 0.027, 0.044), "12mo": (0.170, 0.106, 0.019, 0.030)}     # H, depth, thickness range
LEATHER = {"tan": (122, 78, 44), "brown": (92, 56, 32), "dark": (58, 36, 24), "oxblood": (98, 32, 26), "red": (124, 34, 30),
           "green": (44, 66, 46), "navy": (34, 40, 64), "black": (30, 28, 26), "law": (168, 128, 86), "olive": (78, 72, 44)}
CLOTH = {"green": (58, 76, 52), "maroon": (92, 36, 38), "blue": (42, 54, 86), "brown": (86, 62, 42)}
LABEL = {"red": (128, 30, 26), "black": (26, 24, 22), "green": (36, 60, 40)}
GILT, VELLUM, INK = (214, 164, 84), (214, 198, 166), (52, 36, 26)
ROM = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
SETS = [
    dict(name="Hume", fmt="octavo", style="calf", col="tan", lab=("red", "black"), lines=["HUME'S", "HISTORY", "OF", "ENGLAND"], vols=8, edge="sprinkle"),
    dict(name="Gibbon", fmt="octavo", style="calf", col="brown", lab=("black", "red"), lines=["GIBBON'S", "ROMAN", "EMPIRE"], vols=6, edge="sprinkle"),
    dict(name="Shakspeare", fmt="12mo", style="morocco", col="red", lab=(None, None), lines=["SHAK-", "SPEARE"], vols=10, edge="gilt"),
    dict(name="Spectator", fmt="12mo", style="calf", col="dark", lab=("red", None), lines=["THE", "SPEC-", "TATOR"], vols=8, edge="sprinkle"),
    dict(name="Encyclopaedia", fmt="folio", style="half", col="brown", lab=("red", "black"), lines=["ENCY-", "CLOPAE-", "DIA", "BRITAN-", "NICA"], vols=6, edge="marbled"),
    dict(name="Johnson", fmt="folio", style="calf", col="tan", lab=("red", None), lines=["JOHN-", "SON'S", "DICTION-", "ARY"], vols=2, edge="sprinkle"),
    dict(name="Blackstone", fmt="quarto", style="calf", col="law", lab=("red", "black"), lines=["BLACK-", "STONE'S", "COMMEN-", "TARIES"], vols=4, edge="plain"),
    dict(name="Waverley", fmt="octavo", style="cloth", col="green", lines=["WAVERLEY", "NOVELS"], vols=12, edge="plain"),
    dict(name="Dickens", fmt="octavo", style="cloth", col="maroon", lines=["DICKENS"], edge="plain",
         titles=[["PICKWICK", "PAPERS"], ["OLIVER", "TWIST"], ["NICHOLAS", "NICKLEBY"], ["BLEAK", "HOUSE"], ["DOMBEY", "AND SON"],
                 ["LITTLE", "DORRIT"], ["DAVID", "COPPER-", "FIELD"], ["HARD", "TIMES"]]),
    dict(name="Plutarch", fmt="octavo", style="calf", col="brown", lab=("green", "black"), lines=["PLU-", "TARCH'S", "LIVES"], vols=6, edge="sprinkle"),
    dict(name="Burke", fmt="octavo", style="calf", col="dark", lab=("green", None), lines=["BURKE'S", "WORKS"], vols=8, edge="sprinkle"),
    dict(name="Milton", fmt="12mo", style="morocco", col="navy", lab=(None, None), lines=["MILTON'S", "POEMS"], vols=3, edge="gilt"),
    dict(name="Pope", fmt="12mo", style="calf", col="tan", lab=("black", None), lines=["POPE'S", "HOMER"], vols=6, edge="sprinkle"),
    dict(name="GentMag", fmt="octavo", style="half", col="dark", lab=("red", None), lines=["GENT.", "MAG."], vols=10, years=1781, edge="marbled"),
    dict(name="AnnualRegister", fmt="octavo", style="half", col="brown", lab=("black", None), lines=["ANNUAL", "REGIS-", "TER"], vols=8, years=1790, edge="marbled"),
    dict(name="Atlas", fmt="folio", style="half", col="green", lab=(None, None), lines=["ATLAS"], vols=2, edge="marbled"),
    dict(name="Cicero", fmt="quarto", style="vellum", lines=["CICE-", "RONIS", "OPERA"], vols=4, edge="plain"),
    dict(name="Horace", fmt="12mo", style="vellum", lines=["HORA-", "TII", "OPERA"], vols=1, edge="plain"),
    dict(name="Bible", fmt="folio", style="morocco", col="black", lab=(None, None), lines=["HOLY", "BIBLE"], vols=1, edge="gilt"),
    dict(name="Austen", fmt="octavo", style="cloth", col="blue", lines=["AUSTEN"], edge="plain",
         titles=[["PRIDE", "AND", "PREJU-", "DICE"], ["EMMA"], ["PERSUA-", "SION"], ["MANS-", "FIELD", "PARK"], ["SENSE", "AND", "SENSI-", "BILITY"],
                 ["NORTH-", "ANGER", "ABBEY"]]),
    dict(name="Byron", fmt="octavo", style="morocco", col="green", lab=(None, None), lines=["BYRON'S", "WORKS"], vols=6, edge="gilt"),
    dict(name="Wordsworth", fmt="octavo", style="cloth", col="brown", lines=["WORDS-", "WORTH'S", "POEMS"], vols=4, edge="plain"),
    dict(name="Locke", fmt="octavo", style="calf", col="brown", lab=("red", None), lines=["LOCKE", "ON", "UNDER-", "STAND-", "ING"], vols=2, edge="sprinkle"),
    dict(name="Smith", fmt="octavo", style="calf", col="tan", lab=("red", "black"), lines=["SMITH'S", "WEALTH", "OF", "NATIONS"], vols=3, edge="sprinkle"),
    dict(name="Boswell", fmt="octavo", style="calf", col="oxblood", lab=("black", None), lines=["BOS-", "WELL'S", "JOHN-", "SON"], vols=4, edge="sprinkle"),
    dict(name="Camden", fmt="folio", style="calf", col="dark", lab=("red", None), lines=["CAM-", "DEN'S", "BRITAN-", "NIA"], vols=2, edge="sprinkle"),
    dict(name="Statutes", fmt="quarto", style="calf", col="law", lab=("red", "black"), lines=["STAT-", "UTES", "AT", "LARGE"], vols=8, edge="plain"),
    dict(name="Punch", fmt="quarto", style="cloth", col="maroon", lines=["PUNCH"], vols=6, years=1851, edge="plain"),
    dict(name="Lakes", fmt="quarto", style="morocco", col="green", lab=(None, None), lines=["WEST'S", "GUIDE", "TO THE", "LAKES"], vols=1, edge="gilt"),
    dict(name="Plain", fmt="octavo", style="plain", col="brown", vols=8, edge="sprinkle"),
    dict(name="Sermons", fmt="octavo", style="calf", col="dark", lab=("black", None), lines=["SER-", "MONS"], vols=4, edge="sprinkle"),
    dict(name="Rome", fmt="large8", style="calf", col="oxblood", lab=("green", "black"), lines=["HISTORY", "OF", "ROME"], vols=5, edge="sprinkle"),
    dict(name="Moliere", fmt="12mo", style="morocco", col="red", lab=(None, None), lines=["MOLIERE", "OEUVRES"], vols=6, edge="gilt"),
    dict(name="Tatler", fmt="12mo", style="calf", col="brown", lab=("red", None), lines=["THE", "TAT-", "LER"], vols=4, edge="sprinkle"),
    dict(name="PlainQ", fmt="quarto", style="plain", col="dark", vols=4, edge="plain"),
    dict(name="NatHist", fmt="large8", style="half", col="olive", lab=("black", None), lines=["NATURAL", "HISTORY"], vols=6, edge="marbled"),
]
EDGES = ["plain", "gilt", "sprinkle", "marbled"]


def s2l(c):
    c = np.asarray(c, np.float32) / 255.0 if np.max(c) > 1.0 else np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def load(p, mode="RGB"):
    return np.asarray(Image.open(p).convert(mode), np.float32) / 255.0


class Leather:
    """ambientCG Leather021: colour mottling, displacement and normal, sampled at a chosen density."""
    def __init__(self):
        b = os.path.join(LEA, "Leather021_2K-JPG")
        self.col = load(b + "_Color.jpg"); self.disp = load(b + "_Displacement.jpg", "L"); self.nrm = load(b + "_NormalGL.jpg")
        self.lum = self.col @ np.array([0.2126, 0.7152, 0.0722], np.float32); self.lum /= self.lum.mean()
        self.src_ppm = 2048 / 0.6                                     # the 2K tile taken as 0.6 m of leather

    def sample(self, rng, w, h, ppm):
        """(lum, disp, normal xy) for a w x h block at ppm pixels per metre."""
        k = self.src_ppm / ppm
        sw, sh = min(2047, max(2, int(w * k))), min(2047, max(2, int(h * k)))
        x0, y0 = rng.integers(0, 2048 - sw), rng.integers(0, 2048 - sh)
        def rs(a):
            im = Image.fromarray(a[y0:y0 + sh, x0:x0 + sw].astype(np.float32))
            return np.asarray(im.resize((w, h), Image.BILINEAR), np.float32)
        nx, ny = rs(self.nrm[..., 0] * 2 - 1), rs(self.nrm[..., 1] * 2 - 1)
        return rs(self.lum), rs(self.disp), np.stack([nx, ny], -1)


def noise(rng, w, h, cells):
    g = rng.random((cells[1] + 2, cells[0] + 2)).astype(np.float32)
    im = Image.fromarray(g).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32)


def font_fit(lines, kind, max_w, max_h, start):
    """Largest font size at which every line fits max_w and all lines fit max_h."""
    size = start
    while size > 6:
        f = ImageFont.truetype(FONT[kind], size)
        ws = [f.getbbox(t)[2] - f.getbbox(t)[0] for t in lines]
        lh = f.getbbox("HQ")[3] - f.getbbox("HQ")[1]
        if max(ws) <= max_w and len(lines) * lh * 1.32 <= max_h:
            return f, lh
        size -= 1
    return ImageFont.truetype(FONT[kind], 6), 6


def text_block(draw, lines, kind, box, start, fill=255):
    x0, y0, x1, y1 = box
    f, lh = font_fit(lines, kind, x1 - x0, y1 - y0, start)
    total = len(lines) * lh * 1.32 - lh * 0.32
    y = (y0 + y1) / 2 - total / 2
    for t in lines:
        bb = f.getbbox(t)
        draw.text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), t, font=f, fill=fill)
        y += lh * 1.32


def fleuron(draw, cx, cy, r, kind, fill=255):
    if kind == 0:                                                  # four-petal flower with a centre
        for a in range(4):
            th = a * math.pi / 2
            pts = [(cx + math.cos(th + s) * r * rr, cy + math.sin(th + s) * r * rr) for s, rr in ((0, 0.15), (0.35, 0.65), (0, 1.0), (-0.35, 0.65))]
            draw.polygon(pts, fill=fill)
        draw.ellipse([cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22], fill=fill)
    elif kind == 1:                                                # lozenge between two dots
        draw.polygon([(cx, cy - r), (cx + r * 0.55, cy), (cx, cy + r), (cx - r * 0.55, cy)], fill=fill)
        for s in (-1, 1):
            draw.ellipse([cx + s * r * 0.9 - r * 0.14, cy - r * 0.14, cx + s * r * 0.9 + r * 0.14, cy + r * 0.14], fill=fill)
    elif kind == 2:                                                # eight-point star
        pts = []
        for i in range(16):
            rr = r if i % 2 == 0 else r * 0.42
            th = i * math.pi / 8
            pts.append((cx + math.cos(th) * rr, cy + math.sin(th) * rr))
        draw.polygon(pts, fill=fill)
    else:                                                          # sprig: a stem with three leaves
        draw.line([(cx, cy - r), (cx, cy + r)], fill=fill, width=max(1, int(r * 0.12)))
        for s, yy in ((-1, -0.35), (1, 0.0), (-1, 0.35)):
            draw.ellipse([cx + s * r * 0.55 - r * 0.32, cy + yy * r - r * 0.16, cx + s * r * 0.55 + r * 0.32, cy + yy * r + r * 0.16], fill=fill)


def rules(draw, y, w, t, gap, n=2, fill=255):
    for k in range(n):
        yy = y + k * gap
        draw.rectangle([0, yy - t / 2, w, yy + t / 2], fill=fill)


def dotted(draw, y, w, r, step, fill=255):
    x = step / 2
    while x < w:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill); x += step


def marbled(rng, w, h):
    """Spanish-style marbled paper: domain-warped stripes in blue, red and stone."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) / max(w, h)
    n1, n2 = noise(rng, w, h, (5, 5)), noise(rng, w, h, (9, 9))
    v = np.sin((xx * 9 + yy * 4 + n1 * 3.5 + n2 * 1.2) * 2 * np.pi)
    v2 = np.sin((xx * 3 - yy * 11 + n2 * 4.0) * 2 * np.pi)
    a, b, c = s2l((40, 58, 96)), s2l((150, 46, 40)), s2l((196, 182, 150))
    t1 = (v * 0.5 + 0.5)[..., None]; t2 = (v2 * 0.5 + 0.5)[..., None] ** 3
    return a * (1 - t1) + c * t1 * 0.9 + (b - a) * t2 * 0.5


def draw_spine(st, vol_idx, w, h, rng, lea, ppm):
    """One spine at SS: returns linear colour, height (mm), roughness, metallic (each (H, W))."""
    Wd, Hd = w * SS, h * SS
    style = st["style"]
    gilt = Image.new("L", (Wd, Hd), 0); gd = ImageDraw.Draw(gilt)
    lab = Image.new("L", (Wd, Hd), 0); ld = ImageDraw.Draw(lab)
    lab2 = Image.new("L", (Wd, Hd), 0); l2d = ImageDraw.Draw(lab2)
    ink = Image.new("L", (Wd, Hd), 0); idr = ImageDraw.Draw(ink)
    blind = Image.new("L", (Wd, Hd), 0); bd = ImageDraw.Draw(blind)
    hgt = np.zeros((Hd, Wd), np.float32)
    u = np.linspace(-1, 1, Wd)[None, :]; v = np.linspace(0, 1, Hd)[:, None]
    t = max(2.0, SS * 1.0)                                         # rule thickness: ~1 px final
    if style == "cloth":
        base = s2l(CLOTH[st["col"]])
    elif style == "vellum":
        base = s2l(VELLUM)
    else:
        base = s2l(LEATHER[st["col"]])
    base = base * rng.uniform(0.94, 1.06)
    vol = vol_idx + 1
    if "titles" in st:
        title = st["titles"][vol_idx]; vtxt = None
    else:
        title = st.get("lines", []); vtxt = (str(st["years"] + vol_idx) if st.get("years") else ROM[vol_idx] if st.get("vols", 1) > 1 else None)
    m = 0.10 * Wd                                                  # side margin (the joints curve away)
    if style in ("calf", "morocco", "half", "plain", "vellum"):
        nb = 5 if st["fmt"] != "12mo" else 4
        head, tail = 0.085 * Hd, 0.075 * Hd
        bands = [head + i * (Hd - head - tail) / (nb - 1) for i in range(nb)]
        bh = 0.0085 * ppm * SS * (0.8 if style == "vellum" else 1.0)
        rr = (np.arange(Hd, dtype=np.float32))[:, None]
        for y in bands:
            prof = np.clip(1 - ((rr - y) / (bh / 2)) ** 2, 0, 1) ** 0.6
            hgt += prof * (0.6 if style == "vellum" else 1.4)
            if style in ("calf", "morocco", "half"):
                if st["name"] in ("Hume", "Gibbon", "Plutarch", "Smith", "Rome", "Encyclopaedia") or style == "morocco":
                    dotted(gd, y, Wd, t * 0.9, t * 3.2)
                rules(gd, y - bh * 0.62, Wd, t, 0, n=1); rules(gd, y + bh * 0.62, Wd, t, 0, n=1)
            elif style == "plain":
                rules(bd, y - bh * 0.6, Wd, t, 0, n=1); rules(bd, y + bh * 0.6, Wd, t, 0, n=1)
        panels = [(bands[i] + bh * 0.8, bands[i + 1] - bh * 0.8) for i in range(nb - 1)]
        if style != "vellum":
            rules(gd if style != "plain" else bd, head * 0.45, Wd, t, t * 2.2)
            rules(gd if style != "plain" else bd, Hd - tail * 0.45, Wd, t, -t * 2.2)
        lab_cols = st.get("lab", (None, None))
        fl_kind = int(rng.integers(0, 4)) if vol_idx == 0 or "fl" not in st else st["fl"]
        st.setdefault("fl", fl_kind)
        for i, (a, b) in enumerate(panels):
            ph = b - a
            if i == 0 and title:
                box = (m * 0.9, a + ph * 0.10, Wd - m * 0.9, b - ph * 0.10)
                if style == "vellum":
                    text_block(idr, title, "ital", (m * 0.6, a + ph * 0.06, Wd - m * 0.6, b - ph * 0.06), int(ph * 0.4))
                elif lab_cols[0]:
                    ld.rectangle([m * 0.55, a + ph * 0.06, Wd - m * 0.55, b - ph * 0.06], fill=255)
                    rules(gd, a + ph * 0.06 + t, Wd, t * 0.8, 0, n=1); rules(gd, b - ph * 0.06 - t, Wd, t * 0.8, 0, n=1)
                    text_block(gd, title, "bold", (m * 1.05, a + ph * 0.13, Wd - m * 1.05, b - ph * 0.13), int(ph * 0.4))
                else:
                    text_block(gd, title, "bold", box, int(ph * 0.4))
            elif i == 1 and vtxt and style != "vellum":
                if lab_cols[1]:
                    cy = (a + b) / 2; rh = min(ph * 0.42, Wd * 0.45)
                    l2d.ellipse([m * 0.9, cy - rh, Wd - m * 0.9, cy + rh], fill=255)
                    text_block(gd, [vtxt], "bold", (m * 1.6, cy - rh * 0.6, Wd - m * 1.6, cy + rh * 0.6), int(rh))
                else:
                    text_block(gd, [vtxt], "bold", (m * 1.2, a + ph * 0.3, Wd - m * 1.2, b - ph * 0.3), int(ph * 0.3))
            elif i == 1 and vtxt and style == "vellum":
                text_block(idr, [vtxt], "ital", (m, a + ph * 0.3, Wd - m, b - ph * 0.3), int(ph * 0.3))
            elif style in ("calf", "morocco", "half") and not (i == 1 and vtxt):
                r_ = min(Wd * 0.26, ph * 0.22)
                fleuron(gd, Wd / 2, (a + b) / 2, r_, st["fl"])
                if style == "morocco" or st["fmt"] in ("folio", "quarto"):
                    gd.rectangle([m * 0.8, a + ph * 0.12, Wd - m * 0.8, b - ph * 0.12], outline=255, width=int(t))
            elif style == "plain":
                fleuron(bd, Wd / 2, (a + b) / 2, min(Wd * 0.22, ph * 0.18), 1)
    elif style == "cloth":
        rules(gd, Hd * 0.035, Wd, t, t * 2.4, n=3)
        rules(gd, Hd * 0.955, Wd, t, -t * 2.4, n=3)
        author = st["lines"] if "titles" in st else None
        tl = title if "titles" in st else st["lines"]
        y = Hd * 0.09
        if author:
            text_block(gd, author, "cloth", (m, y, Wd - m, y + Hd * 0.05), int(Hd * 0.03)); y += Hd * 0.07
            rules(gd, y, Wd, t * 0.8, 0, n=1); y += Hd * 0.015
        text_block(gd, tl, "cloth", (m, y, Wd - m, y + Hd * 0.026 * (len(tl) + 1)), int(Hd * 0.035))
        y += Hd * 0.026 * (len(tl) + 1) + Hd * 0.02
        if vtxt:
            text_block(gd, [vtxt] if st.get("years") else ["VOL.", vtxt], "cloth", (m, y, Wd - m, y + Hd * 0.06), int(Hd * 0.03))
        fleuron(gd, Wd / 2, Hd * 0.62, min(Wd * 0.3, Hd * 0.05), (vol_idx + 2) % 4)
        text_block(gd, ["LONDON"], "cloth", (m * 0.7, Hd * 0.86, Wd - m * 0.7, Hd * 0.90), int(Hd * 0.02))
    # sample masks
    G = np.asarray(gilt, np.float32) / 255; L1 = np.asarray(lab, np.float32) / 255; L2 = np.asarray(lab2, np.float32) / 255
    I = np.asarray(ink, np.float32) / 255; B = np.asarray(blind, np.float32) / 255
    lum, disp, nrm = lea.sample(rng, Wd, Hd, ppm * SS)
    if style == "cloth":
        yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
        weave = (np.sin(xx * 2 * np.pi / (SS * 1.4)) * np.sin(yy * 2 * np.pi / (SS * 1.4))) * 0.5 + 0.5
        lum = 0.92 + 0.16 * weave * (0.7 + 0.3 * lum); disp = 0.5 + 0.35 * (weave - 0.5); nrm = nrm * 0.25
    elif style == "vellum":
        lum = 0.9 + 0.1 * lum; nrm = nrm * 0.35
    col = base[None, None, :] * (lum ** 0.75)[..., None]
    # sun fading of the spine (sides are not faded) and wear
    fade = st.setdefault("fade", float(rng.uniform(0.04, 0.28)))
    gray = (col @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    col = col * (1 - fade) + (gray * 1.25 + s2l((150, 120, 80)) * 0.15) * fade
    wear = noise(rng, Wd, Hd, (3, 18)) * noise(rng, Wd, Hd, (6, 40))
    joint = np.clip((np.abs(u) - 0.80) / 0.20, 0, 1) ** 1.5
    caps = np.clip(1 - np.minimum(v, 1 - v) / 0.035, 0, 1)
    rub = np.clip((wear - 0.45) * 3.0, 0, 1) * (0.35 + 0.65 * np.maximum(caps, joint))
    rub = np.maximum(rub, caps * 0.6)
    if style == "vellum":
        dirt = noise(rng, Wd, Hd, (4, 12)) * (0.4 + 0.6 * v)
        col = col * (1 - 0.25 * dirt[..., None]) * (1 - 0.3 * joint[..., None])
    else:
        rubbed = col * 0.70 + gray * 0.55 + s2l((120, 96, 70)) * 0.12
        col = col * (1 - rub[..., None]) + rubbed * rub[..., None]
        col = col * (1 - 0.38 * joint[..., None])
    # lettering pieces
    for M_, c_ in ((L1, st.get("lab", (None, None))[0]), (L2, st.get("lab", (None, None))[1])):
        if c_:
            lc = s2l(LABEL[c_]) * (0.9 + 0.2 * lum[..., None] ** 0.5)
            col = col * (1 - M_[..., None]) + lc * M_[..., None]
            hgt += M_ * 0.25
    # gilt (impressed, partly worn), ink, blind tooling
    gw = np.clip(G * (1 - np.clip((wear - 0.55) * 4, 0, 1) * (0.5 + 0.5 * rub)), 0, 1)
    gc = s2l(GILT) * (0.85 + 0.25 * noise(rng, Wd, Hd, (8, 30))[..., None])
    col = col * (1 - gw[..., None]) + gc * gw[..., None]
    col = col * (1 - 0.75 * I[..., None]) + s2l(INK) * 0.75 * I[..., None]
    col = col * (1 - 0.25 * B[..., None])
    hgt += -0.15 * G - 0.18 * B + (disp - 0.5) * (0.25 if style not in ("cloth", "vellum") else 0.12)
    rough = {"cloth": 0.86, "vellum": 0.62}.get(style, 0.56 if style != "morocco" else 0.48)
    R = np.full((Hd, Wd), rough, np.float32) + 0.08 * (noise(rng, Wd, Hd, (6, 30)) - 0.5)
    R = R - 0.10 * rub * (style not in ("cloth", "vellum")) + 0.06 * caps
    R = R * (1 - np.maximum(L1, L2)) + 0.46 * np.maximum(L1, L2)
    R = R * (1 - gw) + 0.30 * gw
    Mt = gw * 0.95
    return col, hgt, R, Mt, nrm


def swatch(st, rng, lea, kind="cover"):
    """96 x 96 cover swatch (unfaded) at ~400 px/m, or an edge swatch."""
    w = h = SW * SS
    if kind == "cover":
        if st["style"] == "half":
            col = marbled(rng, w, h); hgt = np.zeros((h, w), np.float32); R = np.full((h, w), 0.6, np.float32); nrm = np.zeros((h, w, 2), np.float32)
        else:
            lum, disp, nrm = lea.sample(rng, w, h, 400 * SS)
            if st["style"] == "cloth":
                yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
                weave = (np.sin(xx * 2 * np.pi / (SS * 1.2)) * np.sin(yy * 2 * np.pi / (SS * 1.2))) * 0.5 + 0.5
                lum = 0.94 + 0.12 * weave; disp = 0.5 + 0.3 * (weave - 0.5); nrm = nrm * 0.2
                base = s2l(CLOTH[st["col"]]); R = np.full((h, w), 0.86, np.float32)
            elif st["style"] == "vellum":
                base = s2l(VELLUM); lum = 0.9 + 0.1 * lum; R = np.full((h, w), 0.62, np.float32); nrm = nrm * 0.35
            else:
                base = s2l(LEATHER[st["col"]]); R = np.full((h, w), 0.52, np.float32)
            col = base[None, None, :] * (lum ** 0.75)[..., None]
            hgt = (disp - 0.5) * 0.2
        return col, hgt, R, np.zeros((h, w), np.float32), nrm
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lines = 0.5 + 0.5 * np.sin(yy * 2 * np.pi / (SS * 0.9) + noise(rng, w, h, (2, 30)) * 6)
    if kind == "gilt":
        col = s2l(GILT)[None, None] * (0.9 + 0.1 * lines[..., None]); R = np.full((h, w), 0.32, np.float32); Mt = np.full((h, w), 0.9, np.float32)
    elif kind == "sprinkle":
        sp = (rng.random((h, w)) > 0.93).astype(np.float32)
        col = s2l((206, 188, 152))[None, None] * (0.9 + 0.1 * lines[..., None])
        col = col * (1 - 0.8 * sp[..., None]) + s2l((150, 48, 36)) * 0.8 * sp[..., None]; R = np.full((h, w), 0.7, np.float32); Mt = np.zeros((h, w), np.float32)
    elif kind == "marbled":
        col = marbled(rng, w, h) * (0.9 + 0.1 * lines[..., None]); R = np.full((h, w), 0.65, np.float32); Mt = np.zeros((h, w), np.float32)
    else:
        col = s2l((214, 198, 160))[None, None] * (0.86 + 0.14 * lines[..., None]); R = np.full((h, w), 0.75, np.float32); Mt = np.zeros((h, w), np.float32)
    return col, (lines - 0.5) * 0.05, R, Mt, np.zeros((h, w, 2), np.float32)


def down(a):
    """Box-filter an (H*SS, W*SS[, C]) array to (H, W[, C])."""
    H, Wd = a.shape[0] // SS, a.shape[1] // SS
    return a.reshape(H, SS, Wd, SS, *a.shape[2:]).mean((1, 3))


def pack(cells, width, height, pad):
    """Shelf packing, tallest first. cells: list of (key, w, h). Returns {key: (x, y)} or None if it overflows."""
    order = sorted(cells, key=lambda c: -c[2])
    x = y = 0; row_h = 0; out = {}
    for key, w, h in order:
        if x + w + pad > width:
            x = 0; y += row_h + pad; row_h = 0
        if y + h + pad > height:
            return None
        out[key] = (x + pad // 2, y + pad // 2); x += w + pad; row_h = max(row_h, h)
    return out


def main():
    rng = np.random.default_rng(1812)
    lea = Leather()
    designs = []
    for si, st in enumerate(SETS):
        H, D, t0, t1 = FORMATS[st["fmt"]]
        n = len(st["titles"]) if "titles" in st else st.get("vols", 1)
        tset = rng.uniform(t0, t1)
        for k in range(n):
            T = float(np.clip(tset * rng.uniform(0.9, 1.1), t0 * 0.9, t1 * 1.05))
            designs.append(dict(id=f"{st['name']}_{k + 1:02d}", set=st["name"], set_index=si, vol=k + 1, fmt=st["fmt"], style=st["style"],
                                H=round(H * rng.uniform(0.99, 1.01), 4), D=round(D, 4), T=round(T, 4), edge=st.get("edge", "plain")))
    ppm = 1150.0
    while True:
        cells = [(d["id"], max(8, int(round(d["T"] * ARC * ppm))), int(round(d["H"] * ppm))) for d in designs]
        pos = pack(cells, ATLAS, SPINE_REGION, PAD)
        if pos:
            break
        ppm *= 0.97
    print("spine density", round(ppm, 1), "px/m;", len(designs), "volumes in", len(SETS), "sets")
    col = np.zeros((ATLAS, ATLAS, 3), np.float32) + s2l((40, 28, 20)); hgt = np.zeros((ATLAS, ATLAS), np.float32)
    R = np.full((ATLAS, ATLAS), 0.6, np.float32); Mt = np.zeros((ATLAS, ATLAS), np.float32); NX = np.zeros((ATLAS, ATLAS, 2), np.float32)

    def put(x, y, c, h_, r_, m_, n_):
        hh, ww = h_.shape
        p = PAD // 2
        sl = (slice(y - p, y + hh + p), slice(x - p, x + ww + p))
        col[sl] = np.pad(c, ((p, p), (p, p), (0, 0)), mode="edge"); hgt[sl] = np.pad(h_, p, mode="edge")
        R[sl] = np.pad(r_, p, mode="edge"); Mt[sl] = np.pad(m_, p, mode="edge"); NX[sl] = np.pad(n_, ((p, p), (p, p), (0, 0)), mode="edge")

    for d, (key, w, h) in zip(designs, cells):
        st = SETS[d["set_index"]]
        c_, h_, r_, m_, n_ = draw_spine(st, d["vol"] - 1, w, h, rng, lea, ppm)
        x, y = pos[key]
        put(x, y, down(c_), down(h_), down(r_), down(m_), down(n_))
        d["cell"] = [x, y, w, h]
    # cover swatches (one per set) and edge swatches, in the band under the spines
    sx, sy = 0, SPINE_REGION + PAD
    swatches = {}
    for si, st in enumerate(SETS):
        if sx + SW + PAD > ATLAS:
            sx = 0; sy += SW + PAD
        c_, h_, r_, m_, n_ = swatch(st, rng, lea)
        put(sx + PAD // 2, sy + PAD // 2, down(c_), down(h_), down(r_), down(m_), down(n_))
        swatches[st["name"]] = [sx + PAD // 2, sy + PAD // 2, SW, SW]; sx += SW + PAD
    edges = {}
    for e in EDGES:
        if sx + SW + PAD > ATLAS:
            sx = 0; sy += SW + PAD
        c_, h_, r_, m_, n_ = swatch(None, rng, lea, kind=e)
        put(sx + PAD // 2, sy + PAD // 2, down(c_), down(h_), down(r_), down(m_), down(n_))
        edges[e] = [sx + PAD // 2, sy + PAD // 2, SW, SW]; sx += SW + PAD
    assert sy + SW + PAD <= ATLAS, sy
    # normal (GL: +Y up the texture) from the height in mm plus the leather's own normal; AO from the cavity
    s = ppm / 1000.0
    gy, gx = np.gradient(hgt)
    n = np.stack([-gx * s + NX[..., 0] * 0.6, gy * s + NX[..., 1] * 0.6, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    blur = np.asarray(Image.fromarray(hgt).resize((ATLAS // 8, ATLAS // 8), Image.BILINEAR).resize((ATLAS, ATLAS), Image.BICUBIC), np.float32)
    ao = np.clip(1 - np.clip(blur - hgt, 0, None) * 0.5, 0.55, 1)
    os.makedirs(TEX, exist_ok=True)
    Image.fromarray((l2s(col) * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEX, "T_MO01_Books_BaseColor.png"))
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEX, "T_MO01_Books_NormalGL.png"))
    orm = np.stack([ao, np.clip(R, 0.05, 1), np.clip(Mt, 0, 1)], -1)
    Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEX, "T_MO01_Books_ORM.png"))
    info = dict(atlas=ATLAS, spine_ppm=round(ppm, 2), arc=ARC, pad=PAD, formats=FORMATS, designs=designs, covers=swatches, edges=edges,
                sets=[dict(name=s_["name"], fmt=s_["fmt"], style=s_["style"], edge=s_.get("edge"), fade=round(s_.get("fade", 0), 3)) for s_ in SETS],
                note="cells are [x, y, w, h] in pixels from the atlas's top-left; UV v = 1 - y / atlas")
    json.dump(info, open(os.path.join(W, "Books_Atlas.json"), "w"), indent=1)
    prev = Image.open(os.path.join(TEX, "T_MO01_Books_BaseColor.png")).resize((1024, 1024), Image.LANCZOS)
    out = os.path.join(WS, "review-media", "meredith-office-mo01", "kit"); os.makedirs(out, exist_ok=True)
    prev.save(os.path.join(out, "MO01_Books_Atlas.png"))
    print("BOOKS ATLAS OK", len(designs), "designs; swatch rows end at", sy + SW + PAD)


if __name__ == "__main__":
    main()
