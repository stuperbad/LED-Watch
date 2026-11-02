"""Dog-bone fan-out for two-pad parts (R, C, inductors, indicator LEDs): the pad's stub runs straight out of the END of the pad along the component axis (away from the other pad) into a via that sits ON that axis.
For every pad whose single stub ends in a via (within --reach mm), and that does not already do this, the via is MOVED onto the axis, --d mm beyond the pad end (tried: 0.30 ... 0.60: via pad edge to pad edge 0.15 and more), the stub is
re-drawn as one straight axis piece from the pad centre into the via centre, and everything that was attached to the old via on the other layers is re-drawn from the new via centre with the fewest 0 / 45 / 90 degree pieces
(same method as via_center.py: to the first vertex W of the old route that is >= 0.2 away, bends at W at most 90 degrees, pieces >= 0.1, clearance on every layer).
The via has to clear everything of another net on every layer (pad ring 0.1, hole 0.2) and the other vias.  Pads that cannot be done are left alone (pad_exit.py then takes care of the exit direction).
usage: python pad_dogbone.py dump.json edit.json [--only R1,IND4] [--skip C1] [--d 0.30,0.35,0.42,0.5,0.6] [--tol 8]
 dump.json = copper_dump.py output;  edit.json = {"remove": [...], "add": [...]} for apply_ring_edits.py (via entries: ["via", net, [x, y]])."""
import json
import math
import re
import sys

from shapely.geometry import LineString, Point, Polygon

args = sys.argv[1:]
opt = {"--only": "", "--skip": "", "--d": "0.30,0.35,0.42,0.5,0.6", "--tol": "8", "--reach": "1.6", "--refs": r"^(R|C|IND|L)\d+$", "--min-leg": "0.1"}
pos = []
i = 0
while i < len(args):
    if args[i] in opt:
        opt[args[i]] = args[i + 1]
        i += 2
    else:
        pos.append(args[i])
        i += 1
dumpf, outf = pos
ONLY = {r for r in opt["--only"].split(",") if r}
SKIP = {r for r in opt["--skip"].split(",") if r}
import os
DEBUG = bool(os.environ.get("DBG"))
DS = [float(x) for x in opt["--d"].split(",")]
TOL, REACH, MINLEG = float(opt["--tol"]), float(opt["--reach"]), float(opt["--min-leg"])
REFRE = re.compile(opt["--refs"])
D = json.load(open(dumpf))
LAYERS = ("F.Cu", "In1.Cu", "B.Cu")
EPS = 0.004
CLR = 0.1 + 0.005
HOLE_R = 0.075

tracks = D["tracks"]
segs = [t for t in tracks if t["k"] == "seg"]
arcs = [t for t in tracks if t["k"] == "arc"]
vias = D["vias"]
obst = {L: [] for L in LAYERS}
for L in LAYERS:
    for p in D["pads"]:
        if p["layer"] == L:
            obst[L].append([Polygon(p["pts"]).buffer(0), "pad", p["net"], None])
    for t in tracks:
        if t["layer"] == L:
            obst[L].append([LineString(t["poly"]).buffer(t["w"] / 2), "trk", t["net"], None])
    for v in vias:
        obst[L].append([Point(v["p"]).buffer(v["d"] / 2), "via", v["net"], Point(v["p"])])
    for h in D["holes"]:
        obst[L].append([Point(h["p"]).buffer(h["r"] + 0.05), "hole", "", Point(h["p"])])
added = {L: [] for L in LAYERS}
gone = set()
moved = set()
dead_vias = set()
LOCAL = {L: [] for L in LAYERS}


def near(p, q, e=EPS):
    return math.hypot(p[0] - q[0], p[1] - q[1]) < e


def direction(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def turn(d1, d2):
    return abs(((d2 - d1 + 180) % 360) - 180)


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


def clear(L, net, a, b, disc=None):
    band = LineString([a, b]).buffer(0.05)
    if disc is not None:
        band = band.difference(Point(disc).buffer(0.15))
        if band.is_empty:
            return True
    for g, kind, n, ctr in LOCAL[L]:
        if n == net:
            continue
        if kind == "via" and ctr is not None and tuple(ctr.coords[0]) in dead_vias:
            continue
        if g.distance(band) < CLR:
            return False
        if kind == "via" and ctr.distance(band) < HOLE_R + 0.2 + 0.005:
            return False
        if kind == "hole" and ctr.distance(band) < 0.2 + 0.005 + (g.exterior.distance(ctr) - 0.05):
            return False
    return True


def via_ok(P, net, ignore_pts=()):
    disc = Point(P).buffer(0.15)
    for L in LAYERS:
        for g, kind, n, ctr in LOCAL[L]:
            if n == net:
                continue
            if kind == "via" and ctr is not None and tuple(ctr.coords[0]) in dead_vias:
                continue
            if g.distance(disc) < CLR:
                if DEBUG:
                    print("      via blocked by", L, kind, n, [round(c, 3) for c in g.centroid.coords[0]], round(g.distance(disc), 3))
                return False
            if g.distance(Point(P)) < HOLE_R + 0.2 + 0.005 and kind != "hole":
                if DEBUG:
                    print("      hole clearance blocked by", L, kind, n, [round(c, 3) for c in g.centroid.coords[0]])
                return False
            if kind == "hole" and g.distance(Point(P)) < 0.2 + 0.005 + HOLE_R:
                return False
    return True


def at_vertex(L, net, P, skip):
    pcs, oth = [], 0
    for t in segs:
        if t["layer"] != L or t["net"] != net or id(t) in skip:
            continue
        if near(t["a"], P) or near(t["b"], P):
            pcs.append(t)
    for t in arcs:
        if t["layer"] == L and t["net"] == net and (near(t["a"], P, 0.02) or near(t["b"], P, 0.02)):
            oth += 1
    for v in vias:
        if v["net"] == net and near(v["p"], P, 0.03):
            oth += 1
    for p in D["pads"]:
        if p["layer"] == L and p["net"] == net and Polygon(p["pts"]).buffer(0).distance(Point(P)) < 0.01:
            oth += 1
    return pcs, oth


def interior_touch(L, net, t, excl):
    ls = LineString([t["a"], t["b"]])
    for u in segs + arcs:
        if u is t or id(u) in excl or u["layer"] != L or u["net"] != net:
            continue
        for q in (u["a"], u["b"]):
            if ls.distance(Point(q)) < 0.01 and not near(q, t["a"], 0.03) and not near(q, t["b"], 0.03):
                return True
    return False


def octo(P, Q):
    dx, dy = Q[0] - P[0], Q[1] - P[1]
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return []
    if abs(dx) < 1e-4 or abs(dy) < 1e-4 or abs(abs(dx) - abs(dy)) < 1e-4:
        return [[P, Q]]
    m = min(abs(dx), abs(dy))
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    return [[P, (P[0] + sx * m, P[1] + sy * m), Q], [P, (Q[0] - sx * m, Q[1] - sy * m), Q]]


def walk(L, net, start_piece, from_pt, excl, limit=8):
    """chain of straight pieces from from_pt along start_piece through degree-2 vertices: (pieces, vertices incl. from_pt) up to the first fixed point or limit pieces"""
    pcs = [start_piece]
    far = start_piece["b"] if near(start_piece["a"], from_pt, 0.25) and not near(start_piece["b"], from_pt, 0.25) else start_piece["a"]
    if near(start_piece["a"], from_pt, 0.25) and near(start_piece["b"], from_pt, 0.25):
        far = start_piece["b"] if math.hypot(start_piece["b"][0] - from_pt[0], start_piece["b"][1] - from_pt[1]) > math.hypot(start_piece["a"][0] - from_pt[0], start_piece["a"][1] - from_pt[1]) else start_piece["a"]
    verts = [from_pt, far]
    ex = set(excl) | {id(start_piece)}
    while len(pcs) < limit:
        P = verts[-1]
        nxt, oth = at_vertex(L, net, P, ex)
        nxt = [x for x in nxt if id(x) not in {id(y) for y in pcs}]
        if oth or len(nxt) != 1 or interior_touch(L, net, nxt[0], ex | {id(y) for y in pcs}) or id(nxt[0]) in gone:
            break
        u2 = nxt[0]
        Q = u2["b"] if near(u2["a"], P) else u2["a"]
        pcs.append(u2)
        verts.append(Q)
    return pcs, verts


def redraw(L, net, Vn, pcs, verts, tag):
    """new path from Vn to a vertex of `verts` that is within 1.5 mm (first >= 0.2 away), or to a point on a long old piece (which is then cut there, the rest stays).
    returns (k_full, cand, split) : the first k_full old pieces are replaced; split = (J, far end) of a cut piece or None"""
    best = None
    cands = []                                # (k_full, W, next_dir, split, old_len)
    for k in range(1, len(verts)):
        W = verts[k]
        nxt_dir = direction(verts[k], verts[k + 1]) if k + 1 < len(verts) else None
        if 0.2 <= math.hypot(W[0] - Vn[0], W[1] - Vn[1]) <= 1.5:
            cands.append((k, W, nxt_dir, None, plen(verts[:k + 1])))
        A_, B_ = verts[k - 1], verts[k]
        ln = plen([A_, B_])
        if ln > 1.2:
            dd = ((B_[0] - A_[0]) / ln, (B_[1] - A_[1]) / ln)
            for sdist in (0.3, 0.45, 0.6, 0.8, 1.0, 1.3):
                if sdist > ln - 0.3:
                    continue
                J = (A_[0] + dd[0] * sdist, A_[1] + dd[1] * sdist)
                if math.hypot(J[0] - Vn[0], J[1] - Vn[1]) < 0.2:
                    continue
                cands.append((k - 1, J, direction(A_, B_), (J, B_), plen(verts[:k]) + sdist))
            break                               # nothing beyond a long piece is touched
    for k_full, W, nxt_dir, split, old_len in cands:
        for cand in octo(Vn, W):
            legs = list(zip(cand[:-1], cand[1:]))
            if any(math.hypot(b[0] - a[0], b[1] - a[1]) < MINLEG for a, b in legs):
                continue
            if nxt_dir is not None and turn(direction(*legs[-1]), nxt_dir) > 90.01:
                continue
            if not all(clear(L, net, a, b, disc=Vn) for a, b in legs):
                continue
            sc = (len(legs) - k_full - (1 if split else 0), abs(plen(cand) - old_len), k_full)
            if best is None or sc < best[0]:
                best = (sc, k_full, cand, split)
    return None if best is None else (best[1], best[2], best[3])


pads_by_ref = {}
for p in D["pads"]:
    if p["layer"] in ("F.Cu", "B.Cu") and p["hole"] == 0:
        pads_by_ref.setdefault(p["ref"].split(".")[0], []).append(p)

rem, add, rep = [], [], []
for ref in sorted(pads_by_ref):
    ps = pads_by_ref[ref]
    if not REFRE.match(ref) or len(ps) != 2 or ps[0]["layer"] != ps[1]["layer"]:
        continue
    if (ONLY and ref not in ONLY) or ref in SKIP:
        continue
    L = ps[0]["layer"]
    cs = [Polygon(p["pts"]).centroid for p in ps]
    for i in (0, 1):
        p = ps[i]
        net, name = p["net"], p["ref"]
        poly = Polygon(p["pts"]).buffer(0)
        C = (cs[i].x, cs[i].y)
        o = cs[1 - i]
        ax = (C[0] - o.x, C[1] - o.y)
        al = math.hypot(*ax)
        u = (ax[0] / al, ax[1] / al)
        ua = math.degrees(math.atan2(u[1], u[0]))
        if any(near(v["p"], C, 0.3) and v["net"] == net for v in vias):
            continue
        touching = [t for t in segs if t["layer"] == L and t["net"] == net and (poly.distance(Point(t["a"])) < 0.01 or poly.distance(Point(t["b"])) < 0.01)]
        inside = [t for t in touching if poly.distance(Point(t["a"])) < 0.01 and poly.distance(Point(t["b"])) < 0.01]
        seeds = [t for t in touching if t not in inside]
        if len(seeds) != 1:
            continue
        t0 = seeds[0]
        ina = poly.distance(Point(t0["a"])) < 0.01
        start = t0["a"] if ina else t0["b"]
        excl = {id(x) for x in inside} | {id(t0)}
        pcs, verts = walk(L, net, t0, start, excl)
        end = verts[-1]
        V = next((v for v in vias if v["net"] == net and near(v["p"], end, 0.03)), None)
        if V is None or id(V) in moved or plen(verts) > REACH + 0.5 or not (pcs and verts):
            continue
        # verts[0] is the inside end of the seed; the stub as drawn: pad centre -> verts[1] ... -> V
        Vp = tuple(V["p"])
        # already a clean dog bone? (the via lies on the axis line within TOL degrees and the stub is a single piece)
        dv = math.hypot(Vp[0] - C[0], Vp[1] - C[1])
        if turn(direction(C, Vp), ua) <= TOL and len(pcs) == 1 and not inside:
            continue
        hl = max((q[0] - C[0]) * u[0] + (q[1] - C[1]) * u[1] for q in p["pts"])
        # everything else attached to the old via (other layers and further pieces on this layer)
        stub_ids = {id(x) for x in pcs} | {id(x) for x in inside}
        others = []
        okall = True
        for Lx in LAYERS:
            for t in segs:
                if t["layer"] != Lx or t["net"] != net or id(t) in stub_ids or id(t) in gone:
                    continue
                for q, oq in ((t["a"], t["b"]), (t["b"], t["a"])):
                    if math.hypot(q[0] - Vp[0], q[1] - Vp[1]) <= 0.2 and math.hypot(oq[0] - Vp[0], oq[1] - Vp[1]) > 0.2:
                        oth_here, oth = at_vertex(Lx, net, q, {id(t)})
                        if oth_here and not near(q, Vp, 0.03):
                            continue          # a vertex of a longer chain
                        others.append((Lx, t, q))
            for t in arcs:
                if t["layer"] == Lx and t["net"] == net and (math.hypot(t["a"][0] - Vp[0], t["a"][1] - Vp[1]) <= 0.2 or math.hypot(t["b"][0] - Vp[0], t["b"][1] - Vp[1]) <= 0.2):
                    okall = False
        if not okall:
            rep.append((name, net, "skipped: an arc ends at the via"))
            continue
        # local obstacles
        for Lx in LAYERS:
            LOCAL[Lx][:] = [x for x in obst[Lx] + added[Lx] if x[0].distance(Point(C)) < 7.0]
        done = None
        why = []
        for d in DS:
            Vn = (C[0] + u[0] * (hl + d), C[1] + u[1] * (hl + d))
            dead_vias.add(tuple(Vp))
            vo = via_ok(Vn, net)
            co = clear(L, net, C, Vn, disc=Vn)
            ok = vo and co
            if not ok:
                why.append('d%.2f:%s' % (d, 'via' if not vo else 'stub'))
                dead_vias.discard(tuple(Vp))
                continue
            plans = []
            for Lx, t, q in others:
                pcs2, verts2 = walk(Lx, net, t, q, stub_ids)
                # walk starts at q (the end at the via); the vertex list begins with q
                verts2 = [q] + [v for v in verts2[1:]]
                r = redraw(Lx, net, Vn, pcs2, verts2, name)
                if r is None:
                    ok = False
                    why.append('d%.2f:redraw %s' % (d, Lx))
                    break
                plans.append((Lx, pcs2, verts2, r))
            dead_vias.discard(tuple(Vp))
            if not ok:
                continue
            done = (Vn, plans, d)
            break
        if done is None:
            rep.append((name, net, "no clean dog bone (" + " ".join(why) + ")"))
            continue
        Vn, plans, d = done
        # ---- edits
        for x in pcs + inside:
            rem.append([L, net, [x["a"][0], x["a"][1]], [x["b"][0], x["b"][1]]])
            gone.add(id(x))
        rem.append(["via", net, [Vp[0], Vp[1]]])
        add.append(["via", net, [Vn[0], Vn[1]]])
        add.append([L, net, [C[0], C[1]], [Vn[0], Vn[1]]])
        added[L].append([LineString([C, Vn]).buffer(0.05), "trk", net, None])
        for Lx, pcs2, verts2, (k, cand, split) in plans:
            for x in pcs2[:k + (1 if split else 0)]:
                rem.append([Lx, net, [x["a"][0], x["a"][1]], [x["b"][0], x["b"][1]]])
                gone.add(id(x))
            if split:
                add.append([Lx, net, [split[0][0], split[0][1]], [split[1][0], split[1][1]]])
            for a, b in zip(cand[:-1], cand[1:]):
                add.append([Lx, net, [a[0], a[1]], [b[0], b[1]]])
                added[Lx].append([LineString([a, b]).buffer(0.05), "trk", net, None])
        moved.add(id(V))
        dead_vias.add(tuple(Vp))
        added["F.Cu"].append([Point(Vn).buffer(0.15), "via", net, Point(Vn)])
        added["In1.Cu"].append([Point(Vn).buffer(0.15), "via", net, Point(Vn)])
        added["B.Cu"].append([Point(Vn).buffer(0.15), "via", net, Point(Vn)])
        rep.append((name, net, "via moved onto the axis (%.2f beyond the pad end), %d connection(s) re-drawn on other layers" % (d, len(plans))))
for r in rep:
    print(*r)
print("done %d, left %d" % (sum(1 for r in rep if r[2].startswith("via moved")), sum(1 for r in rep if not r[2].startswith("via moved"))))
json.dump({"remove": rem, "add": add}, open(outf, "w"))
