"""placelib.py : geometry and rule checks for back-side placements (shared by place_view.py and place_sa.py).  DETAIL.json from rework_dump.py."""
import json, math
NOM = [(91.67, 80.42, 108.33, 96.58), (91.67, 103.42, 108.33, 119.58)]
TALL = {"L1": 2.5, "L2": 2.5, "C54": 1.25, "U5": 1.55}
FIXED = {"J1", "J1B", "BZ1", "J2", "MECH2", "MECH3"}
def rotv(dx, dy, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return dx * c - dy * s, dx * s + dy * c
class Lib:
    def __init__(self, detail): self.D = json.load(open(detail)) if isinstance(detail, str) else detail
    def place(self, r, pos):
        d = self.D[r]; x, y, rot = pos; a = rot - d["rot"]; pads = []; sw = round(a / 90) % 2
        for p in d["pads"]:
            cx, cy = rotv(p["cx"], p["cy"], a); hx, hy = (p["hy"], p["hx"]) if sw else (p["hx"], p["hy"]); pads.append((p["n"], p["net"], x + cx, y + cy, hx, hy))
        b = d["body"]; cs = [rotv(px, py, a) for px in (b[0], b[2]) for py in (b[1], b[3])]
        return pads, (x + min(c[0] for c in cs), y + min(c[1] for c in cs), x + max(c[0] for c in cs), y + max(c[1] for c in cs))
    def all(self, POS): return {r: self.place(r, POS.get(r, [self.D[r]["x"], self.D[r]["y"], self.D[r]["rot"]])) for r in self.D}
def gap(a, b):
    dx = max(abs(a[2] - b[2]) - a[4] - b[4], 0); dy = max(abs(a[3] - b[3]) - a[5] - b[5], 0); return math.hypot(dx, dy)
def overlap(A, B, m=0.0): return A[0] < B[2] - m and B[0] < A[2] - m and A[1] < B[3] - m and B[1] < A[3] - m
def checks(G, only=None, min_gap=0.2):
    """list of (kind, text, size) violations; only = set of refs to examine (pairs with at least one of them)"""
    out = []; refs = sorted(G)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if only is not None and a not in only and b not in only: continue
            if a in FIXED and b in FIXED: continue
            A, B = G[a][1], G[b][1]
            if a in ("MECH2", "MECH3") or b in ("MECH2", "MECH3"): continue
            if overlap(A, B, 0.001): out.append(("courtyard", "%s / %s" % (a, b), min(A[2], B[2]) - max(A[0], B[0])))
            if abs((A[0] + A[2]) / 2 - (B[0] + B[2]) / 2) - (A[2] - A[0] + B[2] - B[0]) / 2 > 3 or abs((A[1] + A[3]) / 2 - (B[1] + B[3]) / 2) - (A[3] - A[1] + B[3] - B[1]) / 2 > 3: continue
            for p in G[a][0]:
                for q in G[b][0]:
                    if p[1] and p[1] == q[1]: continue
                    g = gap(p, q)
                    if g < min_gap: out.append(("padgap", "%.2f %s.%s / %s.%s" % (g, a, p[0], b, q[0]), min_gap - g))
    for r, (pads, body) in G.items():
        if r in FIXED or (only is not None and r not in only): continue
        for bt in NOM:
            if overlap(body, bt, 0.0): out.append(("battery", "%s inside the nominal battery body" % r, min(body[3] - bt[1], bt[3] - body[1]) if body[1] < bt[3] and body[3] > bt[1] else 0.1))
        for cx in (body[0], body[2]):
            for cy in (body[1], body[3]):
                if math.hypot(cx - 100, cy - 100) > 20.55: out.append(("edge", "%s too close to the board edge" % r, 0.5)); break
            else: continue
            break
    return out
