"""MO01 Meredith's office: fetch the CC0 sources (plain Python; network). Records Sources.json with URLs, licences and
SHA-256 hashes in the working folder.

    python fetch_sources.py
Owner, 12 Nov 2026: "Use the attached reference image to model the interior of Meredith's office ... Same rules as the
executive corridor. This is a hero room so it must be high quality game assets."
"""
import hashlib, io, json, os, sys, urllib.request, zipfile

W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
SRC = os.path.join(W, "sources")
UA = {"User-Agent": "mr-mak-workspace asset fetch"}
POLYHAVEN = {                      # id: (resolution, maps)
    "herringbone_parquet": ("2k", ["Diffuse", "nor_gl", "Rough", "AO", "Displacement"]),
    "herringbone_brick": ("1k", ["Diffuse", "nor_gl", "Rough", "AO", "Displacement"]),
    "crepe_georgette": ("1k", ["Diffuse", "nor_gl", "Rough"]),
}
AMBIENTCG = {"Marble018": "2K-JPG", "Marble016": "1K-JPG",
             "Leather021": "2K-JPG"}            # worn calf: grain and wear for the book spines (second review)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=120).read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    """Re-runs keep what is already recorded and on disk, and fetch only what is missing."""
    rp = os.path.join(W, "Sources.json")
    rec = json.load(open(rp)) if os.path.exists(rp) else {"polyhaven": {}, "ambientcg": {}, "local": {}}
    for aid, (res, maps) in POLYHAVEN.items():
        if aid in rec["polyhaven"] and all(os.path.exists(f["path"]) for f in rec["polyhaven"][aid]["files"].values()):
            continue
        d = os.path.join(SRC, "polyhaven", aid); os.makedirs(d, exist_ok=True)
        files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        info = json.loads(get(f"https://api.polyhaven.com/info/{aid}"))
        rec["polyhaven"][aid] = {"page": f"https://polyhaven.com/a/{aid}", "license": "CC0", "authors": info.get("authors"), "files": {}}
        for m in maps:
            node = files.get(m, {}).get(res, {})
            f = node.get("png") or node.get("jpg")
            if not f:
                print("missing", aid, m, res); continue
            b = get(f["url"]); p = os.path.join(d, os.path.basename(f["url"]))
            open(p, "wb").write(b)
            rec["polyhaven"][aid]["files"][m] = {"path": p, "url": f["url"], "sha256": sha(b)}
            print("ok", aid, m, len(b))
    for aid, res in AMBIENTCG.items():
        d = os.path.join(SRC, "ambientcg", aid)
        if aid in rec["ambientcg"] and os.path.isdir(d) and os.listdir(d):
            continue
        os.makedirs(d, exist_ok=True)
        url = f"https://ambientcg.com/get?file={aid}_{res}.zip"
        b = get(url)
        zipfile.ZipFile(io.BytesIO(b)).extractall(d)
        rec["ambientcg"][aid] = {"page": f"https://ambientcg.com/view?id={aid}", "license": "CC0", "url": url, "zip_sha256": sha(b),
                                 "files": sorted(os.listdir(d))}
        print("ok", aid, len(b))
    vel = "D:/AI_Modelling/hotel_eden/working/furnishings_S03/materials/velour_velvet"
    rec["local"]["velour_velvet"] = {"path": vel, "note": "Poly Haven velour_velvet (CC0), already used by the approved S03 settee",
                                     "files": sorted(os.listdir(vel))}
    car = "C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/approved-media/rug-r01-concept/source"
    rec["local"]["Carpet001"] = {"path": car, "note": "ambientCG Carpet001 (CC0), the owner-approved rug pile material (F26)"}
    json.dump(rec, open(rp, "w"), indent=1)
    print("SOURCES OK")


if __name__ == "__main__":
    main()
