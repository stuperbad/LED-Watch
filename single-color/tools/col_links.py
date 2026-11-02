"""Shorter link between the series resistor of each column and its column trunk at the hour ring.
polar_route.py ties the resistor pad (R_k+1 pad 1, bearing 30k-5.3, radius 14.7) to the hour-ring anode arc (radius 16.31) with a long radial piece, and the arc then runs on to the trunk base (the radial
trunk through the minute / second rings starts on the arc at bearing 30k-1.9) and to the hour LED stub (bearing 30k): a V of about 2.5 mm where about 1.9 mm is enough.
For every column this tool
  * finds the resistor pad C, the trunk base T (inner end of the long radial piece on the arc) and the chain of pieces that runs from C to the arc (the resistor link, up to its vertex M on the arc),
  * removes that chain and the part of the arc (or of the straight pieces that stand for it) between M and T; whatever lies beyond T towards the LED, or before M, is kept (a piece that crosses T is cut at T),
  * draws a new link C -> T: it leaves the pad straight out of its end (radially outward, the component axis), then 0 / 45 / 90 degree pieces with bends of at most 90 degrees, each piece >= --min-seg,
    clear of everything of another net (track 0.205, pad 0.155, via 0.335) and 0.17 from its own pad and 0.15 from the column's remaining copper except within 0.35 of T.
Columns that do not have this structure are reported and left alone.
usage: python col_links.py dump.json edit.json [--min-seg 0.15] [--only 3,4]     dump.json = copper_dump.py output;  edit.json for apply_ring_edits.py"""
import json
import math
import sys

from shapely.geometry import LineString, Point, Polygon

args = sys.argv[1:]
opt = {"--min-seg": "0.15", "--only": "", "--own": "0.17", "--ext": "0.2,0.3,0.4,0.5", "--debug": ""}
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
MINSEG, OWN = float(opt["--min-seg"]), float(opt["--own"])
EXT = [float(x) for x in opt["--ext"].split(",")]
ONLY = {int(x) for x in opt["--only"].split(",") if x}
DEBUG = {int(x) for x in opt.get("--debug", "").split(",") if x}
D = json.load(open(dumpf))
R_TRK, R_PAD, R_VIA = 0.205, 0.155, 0.335
RC = 16.31
tracks = [t for t in D["tracks"] if t["layer"] == "F.Cu"]


def rad(p):
    return math.hypot(p[0] - 100.0, p[1] - 100.0)


def bear(p):
    return math.degrees(math.atan2(p[0] - 100.0, -(p[1] - 100.0))) % 360


def rel(b, theta):
    return ((b - theta + 180) % 360) - 180


def pol(r, b):
    a = math.radians(b)
    return (100.0 + r * math.sin(a), 100.0 - r * math.cos(a))


def near(p, q, e=0.01):
    return math.hypot(p[0] - q[0], p[1] - q[1]) < e


def on_circle(p):
    return abs(rad(p) - RC) < 0.03


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]


def ang_diff(a, b):
    return abs(((a - b + 180) % 360) - 180)


def solve2(P, V, da, db):
    det = da[0] * db[1] - da[1] * db[0]
    if abs(det) < 1e-9:
        return None
    dx, dy = V[0] - P[0], V[1] - P[1]
    return (dx * db[1] - dy * db[0]) / det, (da[0] * dy - da[1] * dx) / det


rem, add, rep = [], [], []
added = []                                   # [geometry, req, net] new links so far
for k in range(12):
    if ONLY and k not in ONLY:
        continue
    net = "/COL%d" % k
    theta = 30.0 * k
    mine = [t for t in tracks if t["net"] == net]
    rp = [p for p in D["pads"] if p["net"] == net and p["layer"] == "F.Cu" and p["ref"].startswith("R") and rad(Polygon(p["pts"]).centroid.coords[0]) < 15.5]
    if len(rp) != 1:
        rep.append((net, "no single resistor pad"))
        continue
    rp = rp[0]
    C = tuple(Polygon(rp["pts"]).centroid.coords[0])
    # exact pad centre: the centroid of the polygon is the pad centre for these symmetric pads
    # trunk: the long radial straight piece that starts on the circle
    trunk = [t for t in mine if t["k"] == "seg" and RC - 0.2 < min(rad(t["a"]), rad(t["b"])) < RC + 0.3 and max(rad(t["a"]), rad(t["b"])) > 19.5
             and abs(rel(bear(t["a"]), bear(t["b"]))) < 0.9]
    if len(trunk) != 1:
        rep.append((net, "no single trunk piece (%d)" % len(trunk)))
        continue
    tr = trunk[0]
    T = tr["a"] if rad(tr["a"]) < rad(tr["b"]) else tr["b"]
    bt = rel(bear(T), theta)
    # the trunk base may be a dog-leg to the circle (COL6): follow short pieces from T to the circle
    base_pcs = []
    if abs(rad(T) - RC) > 0.003:
        cur = T
        for _ in range(3):
            nx = [t for t in mine if t["k"] == "seg" and t is not tr and (near(t["a"], cur) or near(t["b"], cur)) and t not in base_pcs]
            if len(nx) != 1:
                break
            base_pcs.append(nx[0])
            cur = nx[0]["b"] if near(nx[0]["a"], cur) else nx[0]["a"]
            if abs(rad(cur) - RC) <= 0.003:
                break
        if abs(rad(cur) - RC) > 0.003:
            rep.append((net, "trunk base does not reach the circle"))
            continue
        T = cur
        bt = rel(bear(T), theta)
    # resistor link: shortest path of straight pieces from the resistor pad to the circle (Dijkstra over shared vertices; the pieces of other branches are left alone)
    import heapq
    padpoly = Polygon(rp["pts"]).buffer(0)
    cand = [t for t in mine if t["k"] == "seg" and t is not tr and t not in base_pcs]
    key = lambda q: (round(q[0] / 0.01), round(q[1] / 0.01))
    adj = {}
    for t in cand:
        adj.setdefault(key(t["a"]), []).append((t, t["b"]))
        adj.setdefault(key(t["b"]), []).append((t, t["a"]))
    pq = []
    for t in cand:
        ina = padpoly.distance(Point(t["a"])) < 0.01
        inb = padpoly.distance(Point(t["b"])) < 0.01
        if ina != inb:
            far = t["b"] if ina else t["a"]
            heapq.heappush(pq, (math.hypot(t["b"][0] - t["a"][0], t["b"][1] - t["a"][1]), id(t), [t], far))
    inside = [t for t in cand if padpoly.distance(Point(t["a"])) < 0.01 and padpoly.distance(Point(t["b"])) < 0.01]   # stubs from the pad centre to the pad corner: dead once the link is re-drawn
    M = None
    chain = []
    visited = set()
    while pq:
        d, _, pcs, cur = heapq.heappop(pq)
        if on_circle(cur) and rad(cur) > 0:
            M, chain = cur, pcs
            break
        kk = key(cur)
        if kk in visited:
            continue
        visited.add(kk)
        for t, far in adj.get(kk, []):
            if t in pcs or padpoly.distance(Point(far)) < 0.01:
                continue
            heapq.heappush(pq, (d + math.hypot(far[0] - cur[0], far[1] - cur[1]), id(t), pcs + [t], far))
    chain = chain + inside
    if M is None:
        rep.append((net, "resistor link does not reach the circle (%d pieces)" % len(chain)))
        continue
    bm = rel(bear(M), theta)
    if not bm < bt - 0.2:
        rep.append((net, "link meets the circle at %.1f, trunk at %.1f: nothing to shorten" % (bm, bt)))
        continue
    # circle items (arcs and straight pieces on the circle) between M and T
    cuts = []
    for t in mine:
        if t in chain or t is tr or t in base_pcs:
            continue
        pts = t["poly"]
        if not all(on_circle(p) for p in pts):
            continue
        b0, b1 = rel(bear(t["a"]), theta), rel(bear(t["b"]), theta)
        lo, hi = min(b0, b1), max(b0, b1)
        if hi <= bm + 1e-6 or lo >= bt - 1e-6:
            continue
        cuts.append((t, lo, hi))
    # remove: link chain + cut circle items; re-add what lies outside (bm, bt)
    for t in chain:
        rem.append(["F.Cu", net, [t["a"][0], t["a"][1]], [t["b"][0], t["b"][1]]])
    for t, lo, hi in cuts:
        if t["k"] == "arc":
            rem.append(["F.Cu", net, "arc", list(t["a"]), list(t["b"])])
        else:
            rem.append(["F.Cu", net, list(t["a"]), list(t["b"])])
        ends = {round(b0_, 6): pp for b0_, pp in ((rel(bear(t["a"]), theta), tuple(t["a"])), (rel(bear(t["b"]), theta), tuple(t["b"])))}

        def snap(x, special):
            """exact coordinates for a cut end: the piece's own end point, the trunk base T or the link vertex M"""
            for bb, pp in ends.items():
                if abs(bb - x) < 1e-6:
                    return pp
            return special
        for (x0, x1) in ((lo, min(hi, bm)), (max(lo, bt), hi)):
            if x1 - x0 < 0.05:
                continue
            p0 = snap(x0, tuple(M) if abs(x0 - bm) < 1e-6 else tuple(T) if abs(x0 - bt) < 1e-6 else pol(RC, theta + x0))
            p1 = snap(x1, tuple(M) if abs(x1 - bm) < 1e-6 else tuple(T) if abs(x1 - bt) < 1e-6 else pol(RC, theta + x1))
            if t["k"] == "arc":
                add.append(["F.Cu", net, "arc", list(p0), list(pol(RC, theta + (x0 + x1) / 2)), list(p1)])
            else:
                add.append(["F.Cu", net, list(p0), list(p1)])
    # new link C -> T
    others = []                               # copper of other nets on F.Cu
    removed = {id(t) for t in chain} | {id(t) for t, _, _ in cuts}
    for p in D["pads"]:
        if p["layer"] == "F.Cu" and p["net"] != net:
            others.append([Polygon(p["pts"]).buffer(0), R_PAD])
    for t in tracks:
        if t["net"] != net:
            others.append([LineString(t["poly"]), R_TRK + (t["w"] - 0.1) / 2])
    for v in D["vias"]:
        if v["net"] != net:
            others.append([Point(v["p"]), R_VIA])
    for g, req, n_ in added:
        if n_ != net:
            others.append([g, req])
    keep_same = [LineString(t["poly"]) for t in mine if id(t) not in removed and padpoly.distance(LineString(t["poly"])) > 0.01]   # (branches that leave the resistor pad on their own are not in the way of the link)
    ownpad = Polygon(rp["pts"]).buffer(0)
    Tp = Point(T)
    cache = {}

    def seg_ok(a, b, first=False):
        key = (round(a[0], 4), round(a[1], 4), round(b[0], 4), round(b[1], 4), first)
        if key in cache:
            return cache[key]
        ls = LineString([a, b])
        ok = all(g.distance(ls) >= req - 1e-6 for g, req in others)
        if ok and not first:
            ok = ownpad.distance(ls) >= OWN - 1e-6
        if ok:
            # the column's own remaining copper: keep 0.15 away from it except near T
            for g in keep_same:
                d = g.distance(ls)
                if d < 0.15 - 1e-6:
                    # allowed only where the piece is within 0.35 of T
                    near_t = min(Point(a).distance(Tp), Point(b).distance(Tp)) < 0.35 or ls.distance(Tp) < 0.35
                    if not near_t:
                        ok = False
                        break
        cache[key] = ok
        return ok

    # exit axis: radially outward from the resistor pad end
    bC = bear(C)
    u = (math.sin(math.radians(bC)), -math.cos(math.radians(bC)))
    ua = math.degrees(math.atan2(u[1], u[0])) % 360
    hl = rp_len = 0.0
    xs = [q[0] for q in rp["pts"]]
    ys = [q[1] for q in rp["pts"]]
    # half length of the pad along the axis
    hl = max((q[0] - C[0]) * u[0] + (q[1] - C[1]) * u[1] for q in rp["pts"])
    first = [kk for kk in range(8) if 20 - 1e-6 <= ang_diff(kk * 45, ua) <= 90 + 1e-6]
    best = [None]

    def dfs(path, dirs, kmax):
        P = path[-1]
        nd = len(dirs)
        if nd + 2 == kmax:
            if nd == 0:
                pairs = [(k1, (k1 + t2) % 8) for k1 in first for t2 in (-1, 1)]
            else:
                d0 = dirs[-1]
                pairs = [((d0 + t1) % 8, ((d0 + t1) + t2) % 8) for t1 in (-1, 1) for t2 in (-1, 1)]
            for da, db in pairs:
                sol = solve2(P, T, DIRS[da], DIRS[db])
                if not sol or sol[0] < MINSEG or sol[1] < MINSEG:
                    continue
                Q = (P[0] + DIRS[da][0] * sol[0], P[1] + DIRS[da][1] * sol[0])
                pts = path + [Q, T]
                L = plen(pts)
                if best[0] is not None and L >= best[0][0]:
                    continue
                if not (seg_ok(P, Q) and seg_ok(Q, T)):
                    continue
                best[0] = (L, pts)
            return
        nxt = first if nd == 0 else [(dirs[-1] + 1) % 8, (dirs[-1] - 1) % 8]
        for dd in nxt:
            for ln in [MINSEG + 0.1 * j for j in range(5)]:
                Q = (P[0] + DIRS[dd][0] * ln, P[1] + DIRS[dd][1] * ln)
                if best[0] is not None and plen(path + [Q]) >= best[0][0]:
                    break
                if not seg_ok(P, Q):
                    break
                dfs(path + [Q], dirs + [dd], kmax)

    if k in DEBUG:
        print('DEBUG', net, 'C', C, 'T', T, 'M', M, 'u', u, 'ua', round(ua, 1), 'first', first, 'hl', round(hl, 3), 'cuts', [(round(lo, 2), round(hi, 2), t['k']) for t, lo, hi in cuts], 'chain', len(chain))
        for e1 in EXT:
            P1 = (C[0] + u[0] * (hl + e1), C[1] + u[1] * (hl + e1))
            print('   e1', e1, 'axis piece ok', seg_ok(C, P1, True), 'P1', P1)
    res = None
    for kmax in range(2, 6):
        best[0] = None
        for e1 in EXT:
            P1 = (C[0] + u[0] * (hl + e1), C[1] + u[1] * (hl + e1))
            if seg_ok(C, P1, True):
                dfs([C, P1], [], kmax)
        if best[0] is not None and (res is None or best[0][0] < res[0]):
            res = best[0]
        if res is not None and kmax >= 3:
            break
    if res is None:
        # undo the removals of this column
        for _ in range(len(chain) + len(cuts)):
            rem.pop()
        n_add = sum(1 for _ in cuts)
        rep.append((net, "no clean link path"))
        # drop the re-added parts of this column
        add[:] = [e for e in add if e[1] != net]
        continue
    pts = res[1]
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
    for a, b in zip(mrg[:-1], mrg[1:]):
        add.append(["F.Cu", net, [a[0], a[1]], [b[0], b[1]]])
        added.append([LineString([a, b]), R_TRK, net])
    old = plen([C] + [t["b"] if near(t["a"], C, 0.3) else t["a"] for t in chain]) + 0
    rep.append((net, "linked: %d pieces, %.2f mm (old link %.2f + arc %.2f)" % (len(mrg) - 1, plen(mrg), sum(math.hypot(t["b"][0] - t["a"][0], t["b"][1] - t["a"][1]) for t in chain), sum(plen(t["poly"]) for t, lo, hi in cuts))))
for r in rep:
    print(*r)
json.dump({"remove": rem, "add": add}, open(outf, "w"))
