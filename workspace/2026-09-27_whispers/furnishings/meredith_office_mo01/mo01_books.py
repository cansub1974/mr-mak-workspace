"""MO01 books: game meshes for the bookcases and the mantel (Blender), from Books_Atlas.json (prepare_books.py).

Owner, 12 Nov 2026 (second review): "Model the books, candalabra and the clock in final game model quality and deliver
them with the room."

Module frame = the bookcase run frame: X along the wall (run U, which is the viewer's LEFT when facing the shelves), Y
towards the room (run N), Z up from the shelf top. A book standing at x0 occupies x in [x0, x0 + T]; its spine crown is
at y = 0 and its fore-edge at y = -D.
  spine   a rounded arc (4 segments, bulge 0.18 T) over the full height; UV: the volume's own spine cell
  covers  the two board faces (UV: the set's cover swatch); boards 2.5 mm (folio 3.5 mm) with 3 mm squares
  head    board edges, the spine cap and the page block 3 mm down (UV: the set's edge swatch)
  full    (stacks and the mantel) also the tail and the fore-edge
About 27 triangles a book (full about 50). One material, M_MO01_Books, on the shared 2K atlas.
Shelf rows: unique row modules per bay width and shelf class (multi-volume sets in order, gaps, a leaning volume,
small flat stacks), instanced across the bays so that no module repeats beside or above itself.
"""
import json, math, os
import numpy as np
import bmesh, bpy
from mathutils import Vector, Matrix

W = "D:/AI_Modelling/hotel_eden/working/meredith_office_MO01"
BULGE, SQUARE = 0.18, 0.003
# bookcase geometry (build_mo01 / mo01_spec): bay widths and the clear height above each shelf at its front lip
BAYS = {"South": (5.40 - 7 * 0.11) / 6, "Alcove": (2.95 - 4 * 0.11) / 3}
SHELF_Z = [0.955, 1.343, 1.703, 2.063, 2.423, 2.783]
CLEAR = [0.348, 0.320, 0.320, 0.320, 0.320, 0.417]
ROW_CLASS = ["low", "mid", "mid", "mid", "mid", "top"]
VARIANTS = {("South", "low"): 3, ("South", "mid"): 6, ("South", "top"): 3, ("Alcove", "low"): 2, ("Alcove", "mid"): 4, ("Alcove", "top"): 2}
FMT_OK = {"low": ("quarto", "large8", "octavo", "12mo"), "mid": ("quarto", "large8", "octavo", "12mo"), "top": ("folio", "quarto", "octavo", "large8")}
FMT_WEIGHT = {"low": {"quarto": 3, "large8": 2, "octavo": 3, "12mo": 1}, "mid": {"quarto": 1, "large8": 2, "octavo": 5, "12mo": 3},
              "top": {"folio": 4, "quarto": 3, "octavo": 1, "large8": 1}}


class Atlas:
    def __init__(self):
        self.j = json.load(open(os.path.join(W, "Books_Atlas.json")))
        self.n = self.j["atlas"]
        self.by_id = {d["id"]: d for d in self.j["designs"]}
        self.sets = {}
        for d in self.j["designs"]:
            self.sets.setdefault(d["set"], []).append(d)

    def uv(self, rect, fu, fv):
        x, y, w, h = rect
        return ((x + fu * w) / self.n, 1 - (y + (1 - fv) * h) / self.n)


class Mesh:
    """Accumulates faces with per-corner UVs; each face is wound to face a wanted direction."""
    def __init__(self):
        self.v, self.f, self.uv = [], [], []

    def face(self, pts, uvs, want):
        pts = [Vector(p) for p in pts]
        n = Vector()
        for a, b in zip(pts, pts[1:] + pts[:1]):
            n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
        if n.dot(Vector(want)) < 0:
            pts, uvs = pts[::-1], uvs[::-1]
        o = len(self.v)
        self.v += pts; self.f.append(tuple(range(o, o + len(pts)))); self.uv.append(list(uvs))

    def transform(self, start, M):
        for i in range(start, len(self.v)):
            self.v[i] = M @ self.v[i]

    def obj(self, name, mat, c):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], self.f)
        lay = me.uv_layers.new(name="UV0_Bake")
        lay.data.foreach_set("uv", np.array([c_ for f in self.uv for uv in f for c_ in uv], np.float32))
        me.materials.append(mat)
        me.validate(); me.update()
        # weld coincident corners (UVs stay per corner), then smooth the rounded spines and keep the box edges sharp
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.to_mesh(me); bm.free()
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        me.set_sharp_from_angle(angle=math.radians(32))
        me.update()
        ob = bpy.data.objects.new(name, me); c.objects.link(ob)
        return ob


def book(M, A, d, x0, full=False, setback=0.0):
    """Add one standing book whose low-X side is at x0. Returns the vertex index where it starts."""
    start = len(M.v)
    T, D, H = d["T"], d["D"], d["H"]
    bt = 0.0035 if d["fmt"] == "folio" else 0.0025
    o = SQUARE
    b = BULGE * T
    R = (T * T / 4 + b * b) / (2 * b); th = math.asin((T / 2) / R)
    cx, y0 = x0 + T / 2, -setback
    # arc from the +X side (u = 0, the viewer's left) to the -X side (u = 1)
    arc = [(cx + R * math.sin(th - 2 * th * k / 4), y0 - R + R * math.cos(th - 2 * th * k / 4)) for k in range(5)]
    yj = y0 - b                                                      # joint line (the boards' front edges)
    yf = y0 - D                                                      # fore-edge
    sp, cov, edg = d["cell"], A.j["covers"][d["set"]], A.j["edges"][d["edge"]]
    for k in range(4):
        (xa, ya), (xb, yb) = arc[k], arc[k + 1]
        mx, my = (xa + xb) / 2 - cx, (ya + yb) / 2 - (y0 - R)
        M.face([(xa, ya, 0), (xb, yb, 0), (xb, yb, H), (xa, ya, H)],
               [A.uv(sp, k / 4, 0), A.uv(sp, (k + 1) / 4, 0), A.uv(sp, (k + 1) / 4, 1), A.uv(sp, k / 4, 1)], (mx, my, 0))
    for xs, want in ((x0, (-1, 0, 0)), (x0 + T, (1, 0, 0))):           # covers
        M.face([(xs, yj, 0), (xs, yf, 0), (xs, yf, H), (xs, yj, H)],
               [A.uv(cov, 0, 0), A.uv(cov, 1, 0), A.uv(cov, 1, 1), A.uv(cov, 0, 1)], want)
    ends = [(H, 1)] + ([(0.0, -1)] if full else [])
    for zc, sgn in ends:                                             # head (and tail): cap, board edges, sunk page block
        zp = zc - sgn * o
        M.face([(x, y, zc) for x, y in arc], [A.uv(cov, 0.1 + 0.8 * k / 4, 0.1 + 0.1 * (k % 2)) for k in range(5)], (0, 0, sgn))
        for xa, xb in ((x0, x0 + bt), (x0 + T - bt, x0 + T)):
            M.face([(xa, yj, zc), (xb, yj, zc), (xb, yf, zc), (xa, yf, zc)], [A.uv(cov, 0, 0), A.uv(cov, 0.05, 0), A.uv(cov, 0.05, 1), A.uv(cov, 0, 1)], (0, 0, sgn))
        xi0, xi1, yi = x0 + bt, x0 + T - bt, yf + o
        M.face([(xi0, yj, zp), (xi1, yj, zp), (xi1, yi, zp), (xi0, yi, zp)], [A.uv(edg, 0, 0), A.uv(edg, 0, 1), A.uv(edg, 1, 1), A.uv(edg, 1, 0)], (0, 0, sgn))
        for xw, want in ((xi0, (1, 0, 0)), (xi1, (-1, 0, 0))):
            M.face([(xw, yj, zp), (xw, yi, zp), (xw, yi, zc), (xw, yj, zc)], [A.uv(cov, 0, 0), A.uv(cov, 1, 0), A.uv(cov, 1, 0.04), A.uv(cov, 0, 0.04)], want)
        M.face([(xi0, yj, zp), (xi1, yj, zp), (xi1, yj, zc), (xi0, yj, zc)], [A.uv(cov, 0, 0), A.uv(cov, 1, 0), A.uv(cov, 1, 0.04), A.uv(cov, 0, 0.04)], (0, -1, 0))
        M.face([(xi0, yi, zp), (xi1, yi, zp), (xi1, yi, zc), (xi0, yi, zc)], [A.uv(edg, 0, 0), A.uv(edg, 1, 0), A.uv(edg, 1, 0.04), A.uv(edg, 0, 0.04)], (0, 1, 0))
    if full:                                                         # fore-edge: page block and board edges
        M.face([(x0 + bt, yf + o, o), (x0 + T - bt, yf + o, o), (x0 + T - bt, yf + o, H - o), (x0 + bt, yf + o, H - o)],
               [A.uv(edg, 0, 0), A.uv(edg, 0, 1), A.uv(edg, 1, 1), A.uv(edg, 1, 0)], (0, -1, 0))
        for xa, xb, xw, inward in ((x0, x0 + bt, x0 + bt, 1), (x0 + T - bt, x0 + T, x0 + T - bt, -1)):
            M.face([(xa, yf, 0), (xb, yf, 0), (xb, yf, H), (xa, yf, H)], [A.uv(cov, 0, 0), A.uv(cov, 0.05, 0), A.uv(cov, 0.05, 1), A.uv(cov, 0, 1)], (0, -1, 0))
            M.face([(xw, yf, 0), (xw, yf + o, o), (xw, yf + o, H - o), (xw, yf, H)],                  # board's inner face at the squares
                   [A.uv(cov, 0, 0), A.uv(cov, 0.02, 0), A.uv(cov, 0.02, 1), A.uv(cov, 0, 1)], (inward, 0, 0))
    return start


def row_plan(rng, width, clear, cls, usage, A):
    """Books for one shelf: runs of consecutive volumes of a set, with gaps, a leaning book and the odd flat stack."""
    ok = [s for s, ds in A.sets.items() if ds[0]["fmt"] in FMT_OK[cls] and ds[0]["H"] <= clear - 0.012]
    plan, x = [], 0.004
    last_set = None
    while True:
        room = width - 0.004 - x
        if room < 0.02:
            break
        r = rng.random()
        if r < 0.07 and room > 0.10 and plan and plan[-1]["kind"] == "up":
            g = float(rng.uniform(0.03, 0.06))
            # the next book leans back against the previous one into this gap
            plan.append(dict(kind="gap", x=x, w=g)); x += g
            continue
        if r < 0.13 and cls != "top" and room > 0.30 and not any(p["kind"] == "flat" for p in plan):
            cand = [d for s in ok for d in A.sets[s] if d["H"] < min(room - 0.01, 0.30) and d["fmt"] in ("octavo", "quarto", "large8")]
            if cand:
                n = int(rng.integers(2, 5)); z = 0.0; stack = []
                idx = rng.permutation(len(cand))
                for i in idx[:n]:
                    d = cand[i]
                    if z + d["T"] > clear - 0.03:
                        break
                    stack.append((d["id"], z, float(rng.uniform(-0.006, 0.006)))); z += d["T"]
                wmax = max(A.by_id[i]["H"] for i, _, _ in stack)
                plan.append(dict(kind="flat", x=x + 0.006, stack=stack, w=wmax)); x += wmax + 0.012
                continue
        weights = []
        for s in ok:
            fw = FMT_WEIGHT[cls][A.sets[s][0]["fmt"]]
            weights.append(fw / (1 + 2.5 * usage.get(s, 0)) * (0.15 if s == last_set else 1))
        weights = np.array(weights) / sum(weights)
        s = ok[int(rng.choice(len(ok), p=weights))]
        vols = A.sets[s]
        k0 = int(rng.integers(0, max(1, len(vols) - 1)))
        n = int(rng.integers(2, 9)) if len(vols) > 2 else len(vols)
        run = vols[k0:k0 + n]
        fit, w_ = [], 0.0                                           # as many of the run as fit, then shelved so that
        for d in run:                                               # vol. I is on the viewer's left (+X)
            if w_ + d["T"] + 0.003 > width - 0.004 - x:
                break
            fit.append(d); w_ += d["T"] + 0.003
        placed = 0
        for d in fit[::-1]:
            if d["T"] > width - 0.004 - x:
                break
            lean = plan and plan[-1]["kind"] == "gap" and placed == 0
            plan.append(dict(kind="up", id=d["id"], x=x, setback=float(rng.uniform(0.0, 0.008)), lean=bool(lean)))
            x += d["T"] + float(rng.uniform(0.0004, 0.003)); placed += 1
        if placed == 0:
            # nothing from that set fits: close the row with the thinnest fitting volume, or stop
            thin = [d for s_ in ok for d in A.sets[s_] if d["T"] <= width - 0.004 - x]
            if not thin:
                break
            d = min(thin, key=lambda d_: d_["T"])
            plan.append(dict(kind="up", id=d["id"], x=x, setback=0.002, lean=False)); x += d["T"] + 0.001
        usage[s] = usage.get(s, 0) + 1; last_set = s
    # a book after a gap tips over into it, about its low-X bottom edge, until its head rests on the book before the gap
    for i, p in enumerate(plan):
        if p["kind"] == "up" and p.get("lean") and i >= 1 and plan[i - 1]["kind"] == "gap":
            g = plan[i - 1]["w"]; d = A.by_id[p["id"]]
            p["angle"] = math.asin(min(0.5, (g - 0.001) / d["H"]))
    return plan


def row_mesh(name, plan, A, mat, c):
    M = Mesh()
    for p in plan:
        if p["kind"] == "up":
            d = A.by_id[p["id"]]
            s0 = book(M, A, d, p["x"], setback=p["setback"])
            if p.get("angle"):
                piv = Vector((p["x"], 0, 0))
                R = Matrix.Translation(piv) @ Matrix.Rotation(-p["angle"], 4, "Y") @ Matrix.Translation(-piv)
                M.transform(s0, R)
        elif p["kind"] == "flat":
            for bid, z, dy in p["stack"]:
                d = A.by_id[bid]
                s0 = book(M, A, d, 0.0, full=True, setback=0.0)
                # lie it on its side: its thickness becomes height, its height runs along X; spine still faces +Y
                R = Matrix.Translation((p["x"] + d["H"], dy, z)) @ Matrix.Rotation(math.radians(-90), 4, "Y")
                M.transform(s0, R)
    return M.obj(name, mat, c)


def material(K):
    """Books atlas: BaseColor, NormalGL and ORM (B = gilt metal) on UV0."""
    m = bpy.data.materials.get("M_MO01_Books") or bpy.data.materials.new("M_MO01_Books")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs["Surface"])
    def tx(suffix, data):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = K.img(os.path.join(K.TEX, f"T_MO01_Books_{suffix}.png"), data)
        t.interpolation = "Linear"
        u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "UV0_Bake"; nt.links.new(u.outputs["UV"], t.inputs["Vector"])
        return t
    bc, nm, orm = tx("BaseColor", False), tx("NormalGL", True), tx("ORM", True)
    sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(orm.outputs["Color"], sp.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.5
    nt.links.new(bc.outputs["Color"], mx.inputs["A"]); nt.links.new(sp.outputs["Red"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"]); nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
    n = nt.nodes.new("ShaderNodeNormalMap"); n.uv_map = "UV0_Bake"; nt.links.new(nm.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    return m


def layout(rng):
    """Variant per (case, bay, row): never the same module beside (same row, next bay) or above/below (same bay)."""
    out = {}
    for case, nb in (("South", 6), ("Alcove", 3)):
        for k in range(nb):
            for r in range(6):
                if case == "Alcove" and k == 1 and r in (2, 3):
                    continue                                               # the small portrait hangs here
                cls = ROW_CLASS[r]; nv = VARIANTS[(case, cls)]
                bad = {out.get((case, k - 1, r)), out.get((case, k, r - 1)), out.get((case, k, r + 1))}
                choices = [i for i in range(nv) if i not in bad] or list(range(nv))
                # spread the use evenly
                use = {i: sum(1 for (c_, _, r_), v in out.items() if c_ == case and ROW_CLASS[r_] == cls and v == i) for i in choices}
                lo = min(use.values()); pick = [i for i in choices if use[i] == lo]
                out[(case, k, r)] = int(pick[int(rng.integers(0, len(pick)))])
    return out


MANTEL_SET = "Rome"


def build(K):
    A = Atlas()
    mat = material(K)
    c = K.coll("MO01 | Low")
    rng = np.random.default_rng(4412)
    usage, rows, info = {}, {}, {"rows": {}, "mantel": None}
    for (case, cls), nv in VARIANTS.items():
        width = BAYS[case]
        clear = CLEAR[ROW_CLASS.index(cls)] if cls != "mid" else CLEAR[1]
        for i in range(nv):
            plan = row_plan(rng, width, clear, cls, usage, A)
            nm = f"SM_MO01_BookRow_{case}_{cls}_{i:02d}"
            ob = row_mesh(nm, plan, A, mat, c)
            ob["mo01_row"] = json.dumps(dict(case=case, cls=cls, width=round(width, 4), clear=clear))
            rows[nm] = ob
            info["rows"][nm] = dict(books=sum(1 for p in plan if p["kind"] == "up") + sum(len(p["stack"]) for p in plan if p["kind"] == "flat"),
                                    tris=K.tris(ob), filled=round(max((p["x"] + (A.by_id[p["id"]]["T"] if p["kind"] == "up" else p["w"])) for p in plan if p["kind"] != "gap"), 3),
                                    sets=sorted({A.by_id[p["id"]]["set"] for p in plan if p["kind"] == "up"}))
    # the mantel: five volumes of one set standing against the overmantel wall
    M = Mesh(); x = 0.0
    for d in A.sets[MANTEL_SET][:5][::-1]:                          # vol. I on the viewer's left (+X)
        book(M, A, d, x, full=False, setback=0.0); x += d["T"] + 0.0008
    mob = M.obj("SM_MO01_Books_Mantel", mat, c)
    mob["mo01_width"] = round(x, 4)
    info["mantel"] = dict(set=MANTEL_SET, books=5, width=round(x, 4), tris=K.tris(mob))
    info["layout"] = {f"{a}|{b}|{r}": v for (a, b, r), v in layout(np.random.default_rng(77)).items()}
    K.INFO["books"] = info
    json.dump(info, open(os.path.join(K.KIT, "Books_Rows.json"), "w"), indent=1)
    return dict(rows=rows, mantel=mob)
