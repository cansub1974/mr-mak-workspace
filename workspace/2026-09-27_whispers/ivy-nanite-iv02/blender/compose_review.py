"""Compose A2 comparison boards: supplied/accepted references beside the actual exported mesh."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(sys.argv[1]); IV01 = Path(sys.argv[2])
QA = ROOT / 'qa'; REN = ROOT / 'renders'
try:
    font = ImageFont.truetype('arial.ttf', 26)
except OSError:
    font = ImageFont.load_default()
def panel(img, box, h, label):
    im = Image.open(img).convert('RGB').crop(box)
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    out = Image.new('RGB', (im.width, h + 44), (24, 24, 24)); out.paste(im, (0, 44))
    ImageDraw.Draw(out).text((10, 8), label, fill=(235, 235, 235), font=font)
    return out
def board(panels, path):
    W = sum(p.width for p in panels) + 12 * (len(panels) - 1); H = max(p.height for p in panels)
    b = Image.new('RGB', (W, H), (12, 12, 12)); x = 0
    for p in panels:
        b.paste(p, (x, 0)); x += p.width + 12
    b.save(path, optimize=True); return path
ref = IV01 / 'references' / 'Entrance_Close_Reference.png'
iv01 = IV01 / 'previews' / 'Entrance_Close.png'
H = 900
# wall-scale: ivy on a pier beside a window, roughly 1 x 2 m of wall in each crop
board([panel(ref, (1680, 100, 2140, 1250), H, 'Supplied reference (Hotel Eden entrance)'),
       panel(iv01, (1080, 60, 1400, 900), H, 'IV01 accepted render (historical context)'),
       panel(REN / 'IV02_facade_first_person.png', (640, 0, 1240, 1080), H, 'IV02 exported FBX on MS02 bay (actual mesh)')],
      QA / 'A2_compare_wall_scale.png')
# close: leaf shape, stems and petioles
board([panel(ref, (640, 380, 980, 900), H, 'Reference, close crop'),
       panel(REN / 'IV02_front_close.png', (200, 200, 1400, 1400), H, 'IV02 exported mesh, front close'),
       panel(REN / 'IV02_oblique_close.png', (200, 100, 1400, 1500), H, 'IV02 oblique close')],
      QA / 'A2_compare_close.png')
print('IV02_BOARDS done')
