"""Make every straight track that ends on a via end AT the via centre.
A track end that lies inside the via pad but not at its centre (a trace that touches the via ring from the side, or only just reaches the ring) looks like a trace that leaves the via at a tangent, and the
owner wants every trace to run straight into the via centre.   For each such end: the chain of straight pieces that starts there is followed to its first fixed point (a pad, another via, a junction,
an arc, the end of the net) or at most --reach vertices; for the first vertices W (k = 1..) the pieces from the via centre C to W are re-drawn with the fewest 0 / 45 / 90 degree pieces (one piece when
C->W is octilinear, otherwise the two-piece dogleg, diagonal first or straight first, each leg at least --min-leg), if they clear every other-net item on the layer (track 0.205 centre distance,
pad outline 0.155, via 0.335, hole 0.25) and the bend at W is at most 90 degrees.  Best = most pieces removed relative to added, then smallest change of length.  Ends that cannot be fixed are reported.
Arc ends are only reported.
usage: python via_center.py dump.json edit.json [--thr 0.03] [--short 0.12] [--lateral 0.06] [--min-leg 0.1] [--reach 5] [--only-net N,N] [--skip-net N,N]
 dump.json = copper_dump.py output;  edit.json = {"remove": [[layer, net, a, b], ...], "add": [...]} for apply_ring_edits.py (KiCad python)."""
import json
import math
import sys

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

args = sys.argv[1:]
opt = {"--lateral": "0.06", "--short": "0.12", "--thr": "0.03", "--min-leg": "0.1", "--reach": "5", "--only-net": "", "--skip-net": ""}
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
THR, MINLEG, REACH = float(opt["--thr"]), float(opt["--min-leg"]), int(opt["--reach"])
SHORT = float(opt["--short"])
LATERAL = float(opt["--lateral"])
ONLY = {n for n in opt["--only-net"].split(",") if n}
SKIP = {n for n in opt["--skip-net"].split(",") if n}
D = json.load(open(dumpf))
R_TRK, R_PAD, R_VIA, R_HOLE = 0.205, 0.155, 0.335, 0.25
LAYERS = ("F.Cu", "In1.Cu", "B.Cu")
EPS = 0.004

tracks = D["tracks"]
segs = [t for t in tracks if t["k"] == "seg"]
arcs = [t for t in tracks if t["k"] == "arc"]
vias = D["vias"]


def near(p, q, e=EPS):
    return math.hypot(p[0] - q[0], p[1] - q[1]) < e


# ---------------------------------------------------------------- obstacle geometry per layer (everything; same-net items are skipped by name)
# entries: [polygon (copper outline), kind, net, centre point or None];  a new piece is a 0.1 wide band minus the pad of the via it starts at (inside that pad the via copper rules)
CLR = 0.1 + 0.005
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
gone = set()                                  # ids of straight pieces being removed (not obstacles any more, same net anyway)
HOLE_R = 0.075


def clear(L, net, a, b, C):
    band = LineString([a, b]).buffer(0.05).difference(Point(C).buffer(0.15))
    if band.is_empty:
        return True
    for g, kind, n, ctr in obst[L] + added[L]:
        if n == net:
            continue
        if g.distance(band) < CLR:
            return False
        if kind == "via" and ctr.distance(band) < HOLE_R + 0.2 + 0.005:
            return False
        if kind == "hole" and ctr.distance(band) < 0.2 + 0.005 + (g.exterior.distance(ctr) - 0.05):
            return False
    return True


# ---------------------------------------------------------------- connectivity helpers
def at_vertex(L, net, P, skip):
    """same-net things touching vertex P other than the straight pieces in `skip`: returns (pieces, others)"""
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
    """another same-net piece ending on the interior of straight piece t"""
    ls = LineString([t["a"], t["b"]])
    for u in segs + arcs:
        if u is t or id(u) in excl or u["layer"] != L or u["net"] != net:
            continue
        for q in (u["a"], u["b"]):
            if ls.distance(Point(q)) < 0.01 and not near(q, t["a"], 0.03) and not near(q, t["b"], 0.03):
                return True
    return False


def direction(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def turn(d1, d2):
    return abs(((d2 - d1 + 180) % 360) - 180)


def octo(P, Q):
    dx, dy = Q[0] - P[0], Q[1] - P[1]
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return []
    if abs(dx) < 1e-4 or abs(dy) < 1e-4 or abs(abs(dx) - abs(dy)) < 1e-4:
        return [[P, Q]]
    m = min(abs(dx), abs(dy))
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    k1 = (P[0] + sx * m, P[1] + sy * m)
    k2 = (Q[0] - sx * m, Q[1] - sy * m)
    return [[P, k1, Q], [P, k2, Q]]


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


edits_remove, edits_add, report = [], [], []
dirs_at = {}                                  # (via index, layer) -> directions of the pieces already leaving the centre
for vi, v in enumerate(vias):
    n, C = v["net"], tuple(v["p"])
    if (ONLY and n not in ONLY) or n in SKIP:
        continue
    for L in LAYERS:
        ends = []
        for t in segs:
            if t["layer"] != L or t["net"] != n:
                continue
            for q, o in ((t["a"], t["b"]), (t["b"], t["a"])):
                d = math.hypot(q[0] - C[0], q[1] - C[1])
                if d > 0.2:
                    continue
                if math.hypot(o[0] - C[0], o[1] - C[1]) <= 0.2:
                    continue                      # a piece that lies inside the via pad (dead stub or the via's own inner tail)
                # a vertex of a chain (another piece of the net ends here too) is not the start of a chain
                others, _oth = at_vertex(L, n, q, {id(t)})
                if others or _oth and d > THR:
                    continue
                if d <= THR:
                    dirs_at.setdefault((vi, L), []).append(direction(C, o))
                ends.append((t, q, o, d))
        for t, E, O, d in ends:
            # chain from E
            if id(t) in gone:
                continue
            pcs = [t]
            verts = [E, O]
            excl = {id(t)}
            ok = True
            if interior_touch(L, n, t, excl):
                report.append((n, L, C, "first piece has another piece joined to its side"))
                continue
            while len(verts) - 1 < REACH:
                P = verts[-1]
                nxt, oth = at_vertex(L, n, P, excl)
                if oth or len(nxt) != 1 or interior_touch(L, n, nxt[0], excl) or id(nxt[0]) in gone or any(near(P, (ea[2][0], ea[2][1]), 0.02) or near(P, (ea[3][0], ea[3][1]), 0.02) for ea in edits_add if ea[0] == L and ea[1] == n):
                    break
                u = nxt[0]
                Q = u["b"] if near(u["a"], P) else u["a"]
                if math.hypot(Q[0] - C[0], Q[1] - C[1]) < 0.12 and len(verts) > 1:
                    pass
                pcs.append(u)
                excl.add(id(u))
                verts.append(Q)
                if math.hypot(Q[0] - C[0], Q[1] - C[1]) > 3.0:
                    break
            # short pieces among the first ones (up to the first vertex 0.35 or more from the via centre)
            last_short = 0
            for j in range(len(verts) - 1):
                if plen([verts[j], verts[j + 1]]) < SHORT:
                    last_short = j + 1
                if math.hypot(verts[j + 1][0] - C[0], verts[j + 1][1] - C[1]) >= 0.35:
                    break
            if d <= THR and not last_short:
                continue
            # an end that is only a little beside the centre line (<= --lateral): just prolong the piece along its own direction to the foot of the centre (ends within lateral of C)
            if d > THR and not last_short:
                dx, dy = E[0] - O[0], E[1] - O[1]
                ln = math.hypot(dx, dy)
                if ln > 1e-6:
                    ux, uy = dx / ln, dy / ln
                    along = (C[0] - O[0]) * ux + (C[1] - O[1]) * uy
                    foot = (O[0] + ux * along, O[1] + uy * along)
                    lat = math.hypot(foot[0] - C[0], foot[1] - C[1])
                    if lat <= LATERAL and along > ln - 0.001 and along - ln <= 0.2:
                        edits_remove.append([L, n, [t["a"][0], t["a"][1]], [t["b"][0], t["b"][1]]])
                        gone.add(id(t))
                        edits_add.append([L, n, [O[0], O[1]], [foot[0], foot[1]]])
                        added[L].append([LineString([O, foot]).buffer(0.05), "trk", n, None])
                        dirs_at.setdefault((vi, L), []).append(direction(C, O))
                        report.append((n, L, C, "fixed: prolonged (%.3f beside the centre)" % lat))
                        continue
            best = None
            for k in range(max(1, last_short), len(verts)):
                W = verts[k]
                if math.hypot(W[0] - C[0], W[1] - C[1]) < 0.2:
                    continue
                old_len = plen(verts[:k + 1])
                nxt_dir = direction(verts[k], verts[k + 1]) if k + 1 < len(verts) else None
                for cand in octo(C, W):
                    legs = list(zip(cand[:-1], cand[1:]))
                    if any(math.hypot(b[0] - a[0], b[1] - a[1]) < MINLEG for a, b in legs):
                        continue
                    if nxt_dir is not None and turn(direction(*legs[-1]), nxt_dir) > 90.01:
                        continue
                    # first piece must not lie on top of another piece leaving the via
                    fd = direction(*legs[0])
                    if any(turn(fd, dd) < 30 for dd in dirs_at.get((vi, L), [])):
                        continue
                    if not all(clear(L, n, a, b, C) for a, b in legs):
                        continue
                    sc = (len(legs) - k, abs(plen(cand) - old_len), k)
                    if best is None or sc < best[0]:
                        best = (sc, k, cand)
            if best is None:
                report.append((n, L, C, "no clean path (chain %d pieces)" % len(pcs)))
                continue
            _, k, cand = best
            for u in pcs[:k]:
                edits_remove.append([L, n, [u["a"][0], u["a"][1]], [u["b"][0], u["b"][1]]])
                gone.add(id(u))
            for a, b in zip(cand[:-1], cand[1:]):
                edits_add.append([L, n, [a[0], a[1]], [b[0], b[1]]])
                added[L].append([LineString([a, b]).buffer(0.05), "trk", n, None])
            dirs_at.setdefault((vi, L), []).append(direction(cand[0], cand[1]))
            report.append((n, L, C, "fixed: %d old pieces -> %d" % (k, len(cand) - 1)))
n_fix = sum(1 for r in report if r[3].startswith("fixed"))
for r in report:
    if not r[3].startswith("fixed"):
        print(r[0], r[1], "(%.3f, %.3f)" % r[2], r[3])
print("fixed %d, not fixed %d" % (n_fix, len(report) - n_fix))
for a in arcs:
    for q in (a["a"], a["b"]):
        for v in vias:
            if v["net"] == a["net"] and THR < math.hypot(q[0] - v["p"][0], q[1] - v["p"][1]) <= 0.152:
                print("ARC end off the via centre:", a["net"], a["layer"], "(%.3f, %.3f)" % tuple(v["p"]))
json.dump({"remove": edits_remove, "add": edits_add}, open(outf, "w"))
