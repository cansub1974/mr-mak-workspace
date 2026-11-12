"""MO01: the owner's reference beside the build's matching view (plain Python, Pillow).

    python compare_mo01.py [build_view.png [out_name.png "right-hand label"]]
Writes review-media/meredith-office-mo01/build/MO01_Reference_vs_Build.png (both images at the same height, labelled), or
out_name.png with its own label (the Unreal comparison: UE capture, MO01_Reference_vs_Unreal.png).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RM = os.path.join(HERE, "..", "..", "review-media", "meredith-office-mo01")
ref = Image.open(os.path.join(RM, "MO01_Reference.png")).convert("RGB")
bld = Image.open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RM, "build", "MO01_Ref_Match.png")).convert("RGB")
H = 900
ref = ref.resize((round(ref.width * H / ref.height), H), Image.LANCZOS)
bld = bld.resize((round(bld.width * H / bld.height), H), Image.LANCZOS)
gap, band = 16, 54
out = Image.new("RGB", (ref.width + bld.width + gap, H + band), (24, 23, 21))
out.paste(ref, (0, band)); out.paste(bld, (ref.width + gap, band))
d = ImageDraw.Draw(out)
try:
    f = ImageFont.truetype("arial.ttf", 28)
except Exception:
    f = ImageFont.load_default()
d.text((12, 12), "Reference (owner, 12 Nov 2026)", fill=(235, 228, 214), font=f)
LABEL = sys.argv[3] if len(sys.argv) > 3 else "MO01 build in MS02 (Blender, game meshes, approved furniture FUR-106 to FUR-108)"
d.text((ref.width + gap + 12, 12), LABEL, fill=(235, 228, 214), font=f)
p = os.path.join(RM, "build", sys.argv[2] if len(sys.argv) > 2 else "MO01_Reference_vs_Build.png")
out.save(p)
print("COMPARE", p, out.size)
