"""Re-draw the F.Cu stub between each ring LED's ROW pad (pad 1) and its lane via so that it leaves the pad straight out of the pad's end (along the pad / component axis, i.e. radially inward)
and then only uses 0 / 45 / 90 degree pieces, every bend at most 45 degrees (135 degree corners), to reach the via.   The vias (and everything else) stay where they are.
For every stub all candidate paths are enumerated:  pad centre -> axis piece (a free angle, the pad axis) -> k octilinear pieces (k = 2..K) whose directions each turn by exactly +-45 degrees from the
previous one (the first one turns by at most 45 degrees from the axis); all but the last two lengths come from a coarse set, the last two are solved so that the path ends exactly on the via centre.
A candidate must clear every other-net item on F.Cu (tracks 0.205 centre to centre, pad outlines 0.155, via centres 0.335 (hole clearance 0.2), the numbers octo_tidy.py uses nearly), must not come back within 0.14 of itself and (after the axis piece) must stay --own (0.22) mm from its own pad, so it never runs over or hugs the pad,
and no piece may be shorter than --min-seg.  Fewest pieces first (k is deepened one level past the first success), then the shortest path wins; it becomes an obstacle for the stubs after it.
A stub with no candidate is left as it is and reported.
usage: python ring_stubs.py grid.json stubs.json edit.json [--keep REF,REF,...] [--only REF,...] [--min-seg 0.10] [--kmax 6] [--net ROW] [--sector A0,A1] [--snap 22.5] [--snap-pen 0.03] [--first-turn 45] [--prior edit.json] [--ext 0.25,...] [--own 0.22] [--min-first-turn 20] [--exit-rot 0,90,-90]
 --prior: edit file(s) (comma separated) of an earlier run; their new pieces count as obstacles and their removed pieces are gone (a second, relaxed run for the stubs the first one could not do)
 --sector: only the stubs whose ring bearing is in [A0, A1) degrees (so that sectors can run in parallel; stubs near a sector border are checked against each other by the DRC afterwards)
 grid.json  = tools/grid_dump.py output of the poly twin of the board (arcs as segments);  stubs.json = the stub extraction (tools/ring_extract.py);
 edit.json  = {"remove": [[layer, net, a, b], ...], "add": [...]}, applied by apply_tidy.py (KiCad python)."""
import json
import math
import sys

from shapely.geometry import LineString, Point, Polygon

args = sys.argv[1:]
opt = {"--keep": "", "--only": "", "--min-seg": "0.20", "--kmax": "6", "--net": "ROW", "--sector": "", "--snap": "0", "--first-turn": "50", "--snap-pen": "0.03", "--prior": "", "--ext": "0.25,0.30,0.40,0.50,0.60", "--own": "0.22", "--min-first-turn": "20", "--exit-rot": "0"}
pos = []
i = 0
while i < len(args):
    if args[i] in opt:
        opt[args[i]] = args[i + 1]
        i += 2
    else:
        pos.append(args[i])
        i += 1
gridf, stubf, outf = pos
KEEP = {r for r in opt["--keep"].split(",") if r}
ONLY = {r for r in opt["--only"].split(",") if r}
MINSEG, KMAX = float(opt["--min-seg"]), int(opt["--kmax"])
SNAP = float(opt["--snap"])
FIRST_TURN = float(opt["--first-turn"])
SNAP_PEN = float(opt["--snap-pen"])
OWN = float(opt["--own"])
MIN_FIRST_TURN = float(opt["--min-first-turn"])
R_TRK, R_PAD, R_VIA = 0.205, 0.155, 0.335
SELF = 0.14
G = json.load(open(gridf))
S = json.load(open(stubf))
redo_all = [s for s in S if s["net"].startswith("/" + opt["--net"]) and s["ref"] not in KEEP and (not ONLY or s["ref"] in ONLY)]
if opt["--sector"]:
    a0, a1 = (float(x) for x in opt["--sector"].split(","))
    redo = [s for s in redo_all if a0 <= s["ringA"] % 360 < a1]
else:
    redo = redo_all

# ---------------------------------------------------------------- obstacles on F.Cu (the stubs that are going to be re-drawn are left out)
dead = set()
for s in redo_all:
    for a, b in s["pieces"]:
        dead.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
        dead.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
obst = []                                    # [geometry, required distance, net]
for p in G["pads"]:
    if p["layer"] == "F.Cu":
        obst.append([Polygon(p["pts"]).buffer(0), R_PAD, p["net"]])
for t in G["trk"]:
    if t["layer"] == "F.Cu":
        if (round(t["x1"], 3), round(t["y1"], 3), round(t["x2"], 3), round(t["y2"], 3)) in dead:
            continue
        obst.append([LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]), R_TRK + (t["w"] - 0.1) / 2, t["net"]])
for v in G["via"]:
    obst.append([Point(v["x"], v["y"]), R_VIA, v["net"]])
for c in G["circles"]:
    obst.append([Point(c["x"], c["y"]), c["r"] + 0.05 + 0.2, ""])
added = []                                   # stubs made so far [geometry, req, net]
for pf in [f for f in opt["--prior"].split(",") if f]:
    P_ = json.load(open(pf))
    for l, n, a, b in P_["add"]:
        added.append([LineString([tuple(a), tuple(b)]), R_TRK, n])
    for l, n, a, b in P_["remove"]:
        dead.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
        dead.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
    obst[:] = [o for o in obst if not (isinstance(o[0], LineString) and len(o[0].coords) == 2 and (round(o[0].coords[0][0], 3), round(o[0].coords[0][1], 3), round(o[0].coords[1][0], 3), round(o[0].coords[1][1], 3)) in dead and o[2].startswith("/" + opt["--net"]))]

DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]
FREE = [MINSEG + 0.1 * k for k in range(5)]
EXT = [float(x) for x in opt["--ext"].split(",")]


def ang_diff(a, b):
    return abs(((a - b + 180) % 360) - 180)


def solve2(P, V, da, db):
    det = da[0] * db[1] - da[1] * db[0]
    if abs(det) < 1e-9:
        return None
    dx, dy = V[0] - P[0], V[1] - P[1]
    return (dx * db[1] - dy * db[0]) / det, (da[0] * dy - da[1] * dx) / det


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


def search(s):
    res = None
    for rot in [float(x) for x in opt["--exit-rot"].split(",")]:
        r = search1(s, rot)
        if r is not None and (res is None or r[0] < res[0]):
            res = r
    return res


def search1(s, rot):
    net, C, V = s["net"], tuple(s["center"]), tuple(s["via"])
    A = math.radians(s["ringA"] - rot)      # rot = 0: out of the pad end along the axis (inward); +-90: out of the side of the pad (the pad's own tangent)
    u = (-math.sin(A), math.cos(A))                       # inward, screen coordinates (y down)
    ua = math.degrees(math.atan2(u[1], u[0])) % 360
    hl = s["size"][0 if abs(rot) < 1 else 1] / 2
    first = [k for k in range(8) if MIN_FIRST_TURN - 1e-6 <= ang_diff(k * 45, ua) <= FIRST_TURN + 1e-6]
    local = [o for o in obst + added if o[2] != net and o[0].distance(Point(C)) < 3.2]
    own = [Polygon(p["pts"]).buffer(0) for p in G["pads"] if p["layer"] == "F.Cu" and p["ref"] == s["ref"] + "." + s["pad"]]
    cache = {}

    def seg_ok(a, b, first=False):
        """first = the piece that leaves the pad centre: it is allowed to cover the stub's own pad; every later piece keeps OWN mm (edge of the centre line) away from it"""
        key = (round(a[0], 4), round(a[1], 4), round(b[0], 4), round(b[1], 4), first)
        if key in cache:
            return cache[key]
        ls = LineString([a, b])
        ok = all(o[0].distance(ls) >= o[1] - 1e-6 for o in local)
        if ok and not first:
            ok = all(g.distance(ls) >= OWN - 1e-6 for g in own)
        cache[key] = ok
        return ok

    result = None
    first_hit = None
    for kmax in range(2, KMAX + 1):
        best = [None]

        def dfs(path, dirs, snapped=False, pen=0.0):
            P = path[-1]
            n_done = len(dirs)
            if n_done + 2 == kmax + (1 if snapped else 0):
                if n_done == 0:
                    pairs = [(k1, (k1 + t2) % 8) for k1 in first for t2 in (-1, 1)]
                else:
                    d0 = dirs[-1]
                    pairs = [((d0 + t1) % 8, ((d0 + t1) + t2) % 8) for t1 in (-1, 1) for t2 in (-1, 1)]
                for da, db in pairs:
                    sol = solve2(P, V, DIRS[da], DIRS[db])
                    if not sol or sol[0] < MINSEG or sol[1] < MINSEG:
                        continue
                    Q = (P[0] + DIRS[da][0] * sol[0], P[1] + DIRS[da][1] * sol[0])
                    pts = path + [Q, V]
                    L = plen(pts) + pen
                    if best[0] is not None and L >= best[0][0]:
                        continue
                    if not (seg_ok(P, Q) and seg_ok(Q, V)):
                        continue
                    segs = [LineString([a, b]) for a, b in zip(pts[:-1], pts[1:])]
                    if any(segs[i1].distance(segs[j1]) < SELF for i1 in range(len(segs)) for j1 in range(i1 + 2, len(segs))):
                        continue
                    best[0] = (L, pts)
                return
            if n_done == 0:
                nxt = first
            else:
                nxt = [(dirs[-1] + 1) % 8, (dirs[-1] - 1) % 8]
            for nd in nxt:
                for ln in FREE:
                    Q = (P[0] + DIRS[nd][0] * ln, P[1] + DIRS[nd][1] * ln)
                    if best[0] is not None and plen(path + [Q]) + pen >= best[0][0]:
                        break
                    if not seg_ok(P, Q):
                        break
                    dfs(path + [Q], dirs + [nd], snapped, pen)

        for e1 in EXT:
            P1 = (C[0] + u[0] * (hl + e1), C[1] + u[1] * (hl + e1))
            if seg_ok(C, P1, True):
                dfs([C, P1], [])
            # the axis piece snapped to the nearest 45 degree direction when that is within SNAP degrees of the axis: it is the first octilinear piece
            k0 = int(round(ua / 45.0)) % 8
            if SNAP > 0 and ang_diff(k0 * 45, ua) <= SNAP and ang_diff(k0 * 45, ua) > 1e-6:
                P1s = (C[0] + DIRS[k0][0] * (hl + e1), C[1] + DIRS[k0][1] * (hl + e1))
                if seg_ok(C, P1s, True):
                    dfs([C, P1s], [k0], True, SNAP_PEN * ang_diff(k0 * 45, ua))
        if best[0] is not None:
            if result is None or best[0][0] < result[0]:
                result = best[0]
            if first_hit is None:
                first_hit = kmax
            elif kmax > first_hit:
                break
    return result


edits_remove, edits_add, report = [], [], []
for s in sorted(redo, key=lambda s: s["ref"]):
    best = search(s)
    net = s["net"]
    if best is None:
        report.append((s["ref"], net, "NO PATH"))
        continue
    pts = best[1]
    mrg = [pts[0]]
    for p in pts[1:]:
        if len(mrg) >= 2:
            a, c = mrg[-2], mrg[-1]
            cr = (c[0] - a[0]) * (p[1] - c[1]) - (c[1] - a[1]) * (p[0] - c[0])
            dt = (c[0] - a[0]) * (p[0] - c[0]) + (c[1] - a[1]) * (p[1] - c[1])
            if abs(cr) < 1e-9 and dt > 0:
                mrg[-1] = p
                continue
        mrg.append(p)
    for a, b in s["pieces"]:
        edits_remove.append(["F.Cu", net, [a[0], a[1]], [b[0], b[1]]])
    for a, b in zip(mrg[:-1], mrg[1:]):
        edits_add.append(["F.Cu", net, [a[0], a[1]], [b[0], b[1]]])
        added.append([LineString([a, b]), R_TRK, net])
    old = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in s["pieces"])
    report.append((s["ref"], net, "ok %d pieces, %.2f mm (was %.2f)" % (len(mrg) - 1, plen(pts), old)))
    print(*report[-1], flush=True)
for r in report:
    if r[2] == "NO PATH":
        print(*r)
bad = [r for r in report if r[2] == "NO PATH"]
print("redrawn %d, no path %d" % (len(report) - len(bad), len(bad)))
json.dump({"remove": edits_remove, "add": edits_add}, open(outf, "w"))
