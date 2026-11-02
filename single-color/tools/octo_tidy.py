"""Tidy the router's output: re-draw every NEW chain of straight track pieces with the fewest bends, using only 0 / 45 / 90 degree pieces, wherever that keeps the clearances.
NEW = a straight piece that is not in the reference board (the board before the re-route), so the owner's own copper is never touched.  A chain = new pieces of one net and one layer between two fixed
points (via centre, pad, an end where copper that is not part of the chain touches, a junction of 3+ pieces).  Fixed points never move.  Each chain is walked greedily: from the current vertex the
farthest later vertex that can be reached by one straight piece or a two-piece dogleg (diagonal first or straight first) is taken, if the piece clears every other net by the DRC rules and does not
enter an exclusion rectangle; otherwise the original piece stays.  Result: staircase jogs and 0.05 mm steps disappear, every bend is 135 degrees.
usage: python octo_tidy.py grid_new.json grid_ref.json in.kicad_pcb out.kicad_pcb [--exclude "x0,y0,x1,y1@In1,B;..."]     (system python + shapely; the KiCad python is called to edit the board)
 grid_*.json = tools/grid_dump.py output of the board (poly twin) and of the reference (poly twin).  in.kicad_pcb = the board with TRUE arcs that is edited."""
import json
import math
import os
import subprocess
import sys
import tempfile

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

args = sys.argv[1:]
EXC = ""
if "--exclude" in args:
    i = args.index("--exclude")
    EXC = args[i + 1]
    del args[i:i + 2]
gnew, gref, src, dst = args[:4]
HERE = os.path.dirname(os.path.abspath(__file__))
KPY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
W = 0.1
R_TRK, R_PAD, R_VIA = 0.205, 0.155, 0.33            # centre of the new piece to: other-net track centre / pad outline / other-net via centre
D = json.load(open(gnew))
R = json.load(open(gref))


def key(t):
    a, b = (round(t["x1"], 3), round(t["y1"], 3)), (round(t["x2"], 3), round(t["y2"], 3))
    return (t["layer"], t["net"]) + tuple(sorted([a, b]))


ref_keys = {key(t) for t in R["trk"] if "arc" not in t}
new = [t for t in D["trk"] if "arc" not in t and key(t) not in ref_keys]
print("new straight pieces:", len(new))

# ---------------------------------------------------------------- obstacles per layer
LAYERS = ("F.Cu", "In1.Cu", "B.Cu")
obst = {L: [] for L in LAYERS}          # (geometry, required distance)
for L in LAYERS:
    for p in D["pads"]:
        if p["layer"] == L:
            obst[L].append((Polygon(p["pts"]).buffer(0), R_PAD, p["net"], "pad"))
    for t in D["trk"]:
        if t["layer"] == L:
            g = LineString([(t["arc"][0], t["arc"][1]), (t["arc"][2], t["arc"][3]), (t["arc"][4], t["arc"][5])]) if "arc" in t else LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])])
            obst[L].append((g, R_TRK + (t["w"] - W) / 2, t["net"], "trk"))
    for v in D["via"]:
        obst[L].append((Point(v["x"], v["y"]), R_VIA, v["net"], "via"))
    for c in D["circles"]:
        obst[L].append((Point(c["x"], c["y"]), c["r"] + 0.05 + 0.2 + 0.005, "", "hole"))
for rect in [r for r in EXC.split(";") if r.strip()]:
    rr, _, lay = rect.partition("@")
    x0, y0, x1, y1 = (float(v) for v in rr.split(","))
    ls = [{"F": "F.Cu", "In1": "In1.Cu", "B": "B.Cu"}[x] for x in lay.split(",")] if lay else list(LAYERS)
    for L in ls:
        obst[L].append((Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), 0.055, "<excl>", "excl"))
trees = {L: STRtree([o[0] for o in obst[L]]) for L in LAYERS}


def clear(L, net, a, b, own_new):
    ls = LineString([a, b])
    for k in trees[L].query(ls.buffer(0.7)):
        g, req, n, kind = obst[L][int(k)]
        if n == net and kind != "excl":
            continue
        if id(g) in own_new:
            continue
        if g.distance(ls) < req - 1e-6:
            return False
    return True


# ---------------------------------------------------------------- chains of new pieces
EPS = 0.004
def pk(p):
    return (round(p[0] / EPS), round(p[1] / EPS))


by = {}
for t in new:
    by.setdefault((t["net"], t["layer"]), []).append(t)
vias = {}
for v in D["via"]:
    vias.setdefault(v["net"], []).append((v["x"], v["y"]))
padsn = {}
for p in D["pads"]:
    padsn.setdefault((p["net"], p["layer"]), []).append(Polygon(p["pts"]).buffer(0))
others = {}
for t in D["trk"]:
    others.setdefault((t["net"], t["layer"]), []).append(t)


def is_fixed(net, L, pt, members):
    """pt (x, y) of a chain end / vertex: via centre, pad, or touched by copper of the net that is not a member of the chain"""
    for (vx, vy) in vias.get(net, []):
        if math.hypot(vx - pt[0], vy - pt[1]) < 0.2:
            return True
    p0 = Point(pt)
    for g in padsn.get((net, L), []):
        if g.distance(p0) < 0.03:
            return True
    for t in others.get((net, L), []):
        if id(t) in members:
            continue
        g = LineString([(t["arc"][0], t["arc"][1]), (t["arc"][2], t["arc"][3]), (t["arc"][4], t["arc"][5])]) if "arc" in t else LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])])
        if g.distance(p0) < 0.06:
            return True
    return False


def octo(P, Q):
    dx, dy = Q[0] - P[0], Q[1] - P[1]
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
        return [[P, Q]]
    m = min(abs(dx), abs(dy))
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    k1 = (P[0] + sx * m, P[1] + sy * m)          # diagonal first
    k2 = (Q[0] - sx * m, Q[1] - sy * m)          # straight first
    return [[P, k1, Q], [P, k2, Q]]


def poly_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


def dist_poly(p, pts):
    return min(LineString([a, b]).distance(Point(p)) for a, b in zip(pts[:-1], pts[1:]))


remove, add = [], []
n_chain = n_changed = 0
for (net, L), lst in by.items():
    members = {id(t) for t in lst}
    ends = {}
    for t in lst:
        for p in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            ends.setdefault(pk(p), []).append((t, p))
    used = set()
    for t0 in lst:
        if id(t0) in used:
            continue
        # walk to one end of the chain
        def other_end(t, p):
            a, b = (t["x1"], t["y1"]), (t["x2"], t["y2"])
            return b if pk(p) == pk(a) else a
        start_t, start_p = t0, (t0["x1"], t0["y1"])
        seen = {id(t0)}
        cur_t, cur_p = t0, (t0["x1"], t0["y1"])
        while True:                              # go backwards along the chain from start_p
            nxt = [x for x in ends.get(pk(cur_p), []) if x[0] is not cur_t]
            if len(nxt) != 1 or is_fixed(net, L, cur_p, members) or id(nxt[0][0]) in seen:
                break
            cur_t = nxt[0][0]
            seen.add(id(cur_t))
            cur_p = other_end(cur_t, cur_p)
        # now walk forward from cur_p along cur_t
        chain = [cur_t]
        pts = [cur_p, other_end(cur_t, cur_p)]
        seen = {id(cur_t)}
        while True:
            end_p = pts[-1]
            nxt = [x for x in ends.get(pk(end_p), []) if x[0] is not chain[-1]]
            if len(nxt) != 1 or is_fixed(net, L, end_p, members) or id(nxt[0][0]) in seen:
                break
            nt = nxt[0][0]
            seen.add(id(nt))
            chain.append(nt)
            pts.append(other_end(nt, end_p))
        for t in chain:
            used.add(id(t))
        if len(pts) < 3 or any(abs(t["w"] - W) > 1e-6 for t in chain):
            continue
        n_chain += 1
        own = {id(g) for g, _r, n_, k_ in obst[L] if False}
        # the chain's own pieces are obstacles of the same net, which clear() ignores
        out = [pts[0]]
        i, n = 0, len(pts) - 1
        while i < n:
            took = False
            for j in range(n, i, -1):
                cands = octo(pts[i], pts[j])
                orig_len = poly_len(pts[i:j + 1])
                best = None
                for cand in cands:
                    if all(clear(L, net, a, b, own) for a, b in zip(cand[:-1], cand[1:])):
                        dev = max(dist_poly(q, pts[i:j + 1]) for q in cand[1:-1]) if len(cand) > 2 else 0.0
                        ln = poly_len(cand)
                        if ln <= orig_len * 1.12 + 0.05 and dev <= 0.6:
                            sc = (ln, dev)
                            if best is None or sc < best[0]:
                                best = (sc, cand)
                if best:
                    out.extend(best[1][1:])
                    i = j
                    took = True
                    break
            if not took:
                out.append(pts[i + 1])
                i += 1
        # drop repeated points / merge collinear neighbours
        clean = [out[0]]
        for p in out[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-6:
                clean.append(p)
        mrg = [clean[0]]
        for p in clean[1:]:
            if len(mrg) >= 2:
                a, c = mrg[-2], mrg[-1]
                cr = (c[0] - a[0]) * (p[1] - c[1]) - (c[1] - a[1]) * (p[0] - c[0])
                dt = (c[0] - a[0]) * (p[0] - c[0]) + (c[1] - a[1]) * (p[1] - c[1])
                if abs(cr) < 1e-9 and dt > 0:
                    mrg[-1] = p
                    continue
            mrg.append(p)
        old_bends = len(pts) - 2
        if len(mrg) - 2 >= old_bends and poly_len(mrg) >= poly_len(pts) - 1e-6:
            continue
        n_changed += 1
        for t in chain:
            remove.append((t["layer"], t["net"], (round(t["x1"], 4), round(t["y1"], 4)), (round(t["x2"], 4), round(t["y2"], 4))))
        for a, b in zip(mrg[:-1], mrg[1:]):
            add.append((L, net, a, b))
print("chains:", n_chain, "re-drawn:", n_changed, "| pieces removed", len(remove), "added", len(add))
tmp = os.path.join(tempfile.mkdtemp(), "edit.json")
json.dump({"remove": remove, "add": add}, open(tmp, "w"))
r = subprocess.run([KPY, os.path.join(HERE, "apply_tidy.py"), src, dst, tmp], capture_output=True, text=True)
print([l for l in r.stdout.splitlines() if not l.startswith(("swig", "Adding"))][-3:])
