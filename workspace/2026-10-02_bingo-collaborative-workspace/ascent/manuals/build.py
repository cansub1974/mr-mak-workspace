"""Build the BCW + Ascent manuals: wrap each body fragment with styles and a contents list, then print to PDF with Edge.
Usage: python build.py <output folder>"""
import html, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1])
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CSS = (HERE / "manual.css").read_text(encoding="utf-8")
DOCS = [("user-manual.body.html", "BCW-User-Manual", "BCW and the Ascent: User Manual"),
        ("admin-manual.body.html", "BCW-Administrator-Manual", "BCW and the Ascent: Administrator Manual")]

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", text)).lower()).strip("-")

def build(src, stem, title):
    body = (HERE / src).read_text(encoding="utf-8")
    toc, seen = [], set()
    def anchor(m):
        level, attrs, inner = m.group(1), m.group(2), m.group(3)
        s = slug(inner)
        while s in seen: s += "-x"
        seen.add(s)
        toc.append((level, s, re.sub(r"<[^>]+>", "", inner)))
        return f'<h{level} id="{s}"{attrs}>{inner}</h{level}>'
    body = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", anchor, body, flags=re.S)
    items, open2 = [], False
    for level, s, text in toc:
        if level == "2":
            if open2: items.append("</ol></li>")
            items.append(f'<li><a href="#{s}">{text}</a><ol>'); open2 = True
        else:
            items.append(f'<li><a href="#{s}">{text}</a></li>')
    if open2: items.append("</ol></li>")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{CSS}</style></head>
<body><main>
{body.replace('<!--TOC-->', '<nav class="toc"><h2 class="toc-title">Contents</h2><ol>' + ''.join(items) + '</ol></nav>')}
</main></body></html>"""
    OUT.mkdir(parents=True, exist_ok=True)
    out_html = OUT / f"{stem}.html"
    out_html.write_text(page, encoding="utf-8")
    pdf = OUT / f"{stem}.pdf"
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", out_html.as_uri()], check=True, capture_output=True, timeout=180)
    print(out_html, len(re.sub(r"<[^>]+>", " ", body).split()), "words;", pdf.name, pdf.stat().st_size // 1024, "KB")

for d in DOCS:
    build(*d)
