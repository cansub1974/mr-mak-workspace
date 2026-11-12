"""MO01 mantel props: the clock's enamel dial (plain Python: numpy + Pillow).

    python prepare_props.py
Owner, 12 Nov 2026 (second review): "Model the books, candalabra and the clock in final game model quality and deliver
them with the room."
Writes textures/T_MO01_ClockDial_BaseColor.png (1024, sRGB): warm white enamel with a little age, a minute track,
Roman hours (IIII for four, as on period clocks) set radially, two winding holes, and the maker's line EDEN & SON / LONDON.
The hands are geometry (mo01_props.py). UV: planar over the dial, u = 0.5 + x / 2r, v = 0.5 + z / 2r.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TEX = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01/textures"
N, SS = 1024, 3
ROMAN = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def main():
    S = N * SS; c = S / 2; R = S / 2 * 0.985
    rng = np.random.default_rng(9)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rr = np.hypot(xx - c, yy - c) / R
    base = np.array([236, 230, 214], np.float32) / 255
    img = np.ones((S, S, 3), np.float32) * base
    img *= (1 - 0.06 * np.clip(rr - 0.55, 0, 1) ** 1.5)[..., None]               # age towards the rim
    n = np.asarray(Image.fromarray(rng.random((40, 40)).astype(np.float32)).resize((S, S), Image.BICUBIC))
    img *= (0.985 + 0.03 * n)[..., None]
    ink = Image.new("L", (S, S), 0); d = ImageDraw.Draw(ink)
    def circle(r, w):
        d.ellipse([c - r * R, c - r * R, c + r * R, c + r * R], outline=255, width=int(w * SS))
    circle(0.935, 2.0); circle(0.885, 1.4); circle(0.69, 1.6); circle(0.655, 1.0)
    for k in range(60):                                                          # minute track
        a = math.radians(k * 6)
        r0, r1 = (0.885, 0.935) if k % 5 else (0.86, 0.935)
        w = 1.4 if k % 5 else 3.0
        d.line([(c + math.sin(a) * r0 * R, c - math.cos(a) * r0 * R), (c + math.sin(a) * r1 * R, c - math.cos(a) * r1 * R)], fill=255, width=int(w * SS))
    f = ImageFont.truetype("C:/Windows/Fonts/BASKVILL.TTF", int(0.135 * R))
    for k, t in enumerate(ROMAN):                                                # hours, set radially (feet to the centre)
        tile = Image.new("L", (int(0.5 * R), int(0.25 * R)), 0); td = ImageDraw.Draw(tile)
        bb = td.textbbox((0, 0), t, font=f)
        td.text(((tile.width - (bb[2] - bb[0])) / 2 - bb[0], (tile.height - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=255)
        rot = tile.rotate(-k * 30, resample=Image.BICUBIC, expand=True)
        a = math.radians(k * 30); rm = 0.775
        px, py = c + math.sin(a) * rm * R, c - math.cos(a) * rm * R
        ink.paste(255, (int(px - rot.width / 2), int(py - rot.height / 2)), rot)
    fs = ImageFont.truetype("C:/Windows/Fonts/BASKVILL.TTF", int(0.075 * R))
    for t, y in (("EDEN & SON", c - 0.30 * R), ("LONDON", c + 0.26 * R)):
        bb = d.textbbox((0, 0), t, font=fs)
        d.text((c - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), t, font=fs, fill=255)
    a = np.asarray(ink, np.float32)[..., None] / 255
    img = img * (1 - 0.92 * a) + np.array([22, 20, 18], np.float32) / 255 * 0.92 * a
    holes = Image.new("L", (S, S), 0); hd = ImageDraw.Draw(holes)
    brass = Image.new("L", (S, S), 0); bd = ImageDraw.Draw(brass)
    for ang in (120, 240):                                                       # winding holes at IIII and VIII
        aa = math.radians(ang); px, py = c + math.sin(aa) * 0.40 * R, c - math.cos(aa) * 0.40 * R
        bd.ellipse([px - 0.055 * R, py - 0.055 * R, px + 0.055 * R, py + 0.055 * R], fill=255)
        hd.ellipse([px - 0.035 * R, py - 0.035 * R, px + 0.035 * R, py + 0.035 * R], fill=255)
    bd.ellipse([c - 0.05 * R, c - 0.05 * R, c + 0.05 * R, c + 0.05 * R], fill=255)
    b = np.asarray(brass, np.float32)[..., None] / 255; h = np.asarray(holes, np.float32)[..., None] / 255
    img = img * (1 - b) + np.array([176, 132, 64], np.float32) / 255 * b
    img = img * (1 - h) + np.array([10, 9, 8], np.float32) / 255 * h
    img[rr > 1.0] = np.array([176, 132, 64], np.float32) / 255                   # outside the dial: brass (under the bezel)
    out = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((N, N), Image.LANCZOS)
    os.makedirs(TEX, exist_ok=True)
    out.save(os.path.join(TEX, "T_MO01_ClockDial_BaseColor.png"))
    print("DIAL OK")


if __name__ == "__main__":
    main()
