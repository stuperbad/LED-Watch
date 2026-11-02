"""Make the traces of two-pad parts (R, C, inductors, indicator LEDs) leave their pads the way the owner wants them: straight out of the END of the pad, along the component axis (away from the other pad),
never out of the side, the corner or the inner end, and then only 0 / 45 / 90 degree pieces.  (Two pads of a part = the traces leave the two opposite ends of the component.)
For every pad of such a part on F.Cu / B.Cu (a via inside the pad is left alone):
  * the stubs that start at the pad are followed to their first fixed point W (a via centre, another pad, a junction, an arc, the end of the net, or a vertex --reach mm away),
  * a pad whose stubs already leave along the axis (<= --tol degrees) and are clean is left as it is,
  * otherwise the stubs are removed and re-drawn:  ONE axis piece from the pad centre to P1 (>= --ext beyond the pad end), and from P1 one octilinear path per stub to its W (bends at most 90 degrees, the first one
    20-90 degrees off the axis unless the axis is itself octilinear, every piece >= --min-seg, the last piece at least --min-seg, clearance to everything of another net as in via_center.py, 0.12 from the own pad after
    the axis piece, 0.12 between the paths of one pad except within 0.3 of P1);  the shortest total wins.
Pads that cannot be done are reported and left alone.
usage: python pad_exit.py dump.json edit.json [--only R1,IND4] [--skip C1] [--tol 25] [--ic U4] [--min-seg 0.12] [--ext 0.2,0.3,0.4] [--reach 1.2] [--kmax 5]
 dump.json = copper_dump.py output;  edit.json = {"remove": [...], "add": [...]} for apply_ring_edits.py"""
import json
import math
import re
import sys

from shapely.geometry import LineString, Point, Polygon

args = sys.argv[1:]
opt = {"--only": "", "--skip": "", "--tol": "25", "--min-seg": "0.12", "--ext": "0.2,0.3,0.4", "--reach": "1.2", "--kmax": "5", "--own": "0.12", "--refs": r"^(R|C|IND|L)\d+$", "--ic": "", "--snap": "15", "--min-first-turn": "12", "--zz": "0.35"}
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
TOL, MINSEG, REACH, KMAX, OWN = float(opt["--tol"]), float(opt["--min-seg"]), float(opt["--reach"]), int(opt["--kmax"]), float(opt["--own"])
SNAP, MINFT = float(opt["--snap"]), float(opt["--min-first-turn"])
ZZ = float(opt["--zz"])
EXT = [float(x) for x in opt["--ext"].split(",")]
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


def near(p, q, e=EPS):
    return math.hypot(p[0] - q[0], p[1] - q[1]) < e


def direction(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def turn(d1, d2):
    return abs(((d2 - d1 + 180) % 360) - 180)


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))


LOCAL = []
CUR = {}


def clear(L, net, a, b, skip_poly=None):
    band = LineString([a, b]).buffer(0.05)
    for g, kind, n, ctr in LOCAL:
        if n == net:
            continue
        if g.distance(band) < CLR:
            return False
        if kind == "via" and ctr.distance(band) < HOLE_R + 0.2 + 0.005:
            return False
        if kind == "hole" and ctr.distance(band) < 0.2 + 0.005 + (g.exterior.distance(ctr) - 0.05):
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


DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]


def ang_diff(a, b):
    return abs(((a - b + 180) % 360) - 180)


def solve2(P, V, da, db):
    det = da[0] * db[1] - da[1] * db[0]
    if abs(det) < 1e-9:
        return None
    dx, dy = V[0] - P[0], V[1] - P[1]
    return (dx * db[1] - dy * db[0]) / det, (da[0] * dy - da[1] * dx) / det


def paths_from(L, net, P1, ua, W, next_dir, own_poly, same_new, P1pt, first_ok, init_dir=None):
    """best octilinear path P1 -> W (list of vertices, P1 first) under the rules, or None.  first_ok = allowed first-piece direction indices"""
    best = [None]
    P1_ = Point(P1)

    def seg_ok(a, b):
        if not clear(L, net, a, b):
            return False
        ls = LineString([a, b])
        if own_poly.distance(ls) < OWN - 1e-6:
            return False
        for g in same_new:
            if g.distance(ls) < 0.12 and min(P1_.distance(Point(a)), P1_.distance(Point(b))) > 0.3 and ls.distance(P1_) > 0.3:
                return False
        return True

    axis_ls = LineString([CUR["C"], P1]) if CUR.get("C") else None

    def self_ok(pts):
        segs_ = [LineString([a, b]) for a, b in zip(pts[:-1], pts[1:])]
        for i1 in range(len(segs_)):
            for j1 in range(i1 + 2, len(segs_)):
                if segs_[i1].distance(segs_[j1]) < 0.2:
                    return False
        if axis_ls is not None:
            for sg in segs_[1:]:
                if sg.distance(axis_ls) < 0.2 and sg.distance(Point(P1)) > 0.01:
                    return False
        return True

    def dfs(path, dirs, kmax):
        P = path[-1]
        nd = len(dirs) - (1 if init_dir is not None else 0)
        if nd + 2 == kmax:
            if nd == 0 and init_dir is None:
                pairs = [(k1, (k1 + t2) % 8) for k1 in first_ok for t2 in (-1, 0, 1)]
            else:
                d0 = dirs[-1]
                pairs = [((d0 + t1) % 8, ((d0 + t1) + t2) % 8) for t1 in (-1, 1) for t2 in (-1, 1)]
            for da, db in pairs:
                # a zig-zag (two bends of opposite sign) needs a middle piece of at least ZZ mm
                if da != db:
                    sol_ = solve2(P, W, DIRS[da], DIRS[db])
                    if sol_ and ((db - da) % 8 in (1, 7)) and ((da - (dirs[-1] if dirs else (init_dir if init_dir is not None else da))) % 8 in (1, 7)):
                        s1 = (da - (dirs[-1] if dirs else da)) % 8
                        s2 = (db - da) % 8
                        if dirs and s1 != s2 and sol_[0] < ZZ:
                            continue
                if da == db:
                    sol = None
                    # a single straight piece (octilinear): only when W lies on that ray
                    dx, dy = W[0] - P[0], W[1] - P[1]
                    ln = math.hypot(dx, dy)
                    if ln >= MINSEG and abs(dx * DIRS[da][1] - dy * DIRS[da][0]) < 1e-4 and dx * DIRS[da][0] + dy * DIRS[da][1] > 0:
                        pts = path + [W]
                        Lq = plen(pts)
                        if (best[0] is None or Lq < best[0][0]) and seg_ok(P, W):
                            if next_dir is None or turn(da * 45, next_dir) <= 90.01:
                                best[0] = (Lq, pts)
                    continue
                sol = solve2(P, W, DIRS[da], DIRS[db])
                if not sol or sol[0] < MINSEG or sol[1] < MINSEG:
                    continue
                Q = (P[0] + DIRS[da][0] * sol[0], P[1] + DIRS[da][1] * sol[0])
                pts = path + [Q, W]
                Lq = plen(pts)
                if best[0] is not None and Lq >= best[0][0]:
                    continue
                if next_dir is not None and turn(db * 45, next_dir) > 90.01:
                    continue
                if not (seg_ok(P, Q) and seg_ok(Q, W)):
                    continue
                if not self_ok(pts):
                    continue
                best[0] = (Lq, pts)
            return
        nxt = first_ok if (nd == 0 and init_dir is None) else [(dirs[-1] + 1) % 8, (dirs[-1] - 1) % 8]
        for dd in nxt:
            for ln in [MINSEG + 0.08 * j for j in range(6)]:
                if dirs and ((dd - dirs[-1]) % 8 in (1, 7)) and len(dirs) >= 2 and (((dirs[-1] - dirs[-2]) % 8) != ((dd - dirs[-1]) % 8)) and plen([path[-2], path[-1]]) < ZZ:
                    continue
                Q = (P[0] + DIRS[dd][0] * ln, P[1] + DIRS[dd][1] * ln)
                if best[0] is not None and plen(path + [Q]) >= best[0][0]:
                    break
                if not seg_ok(P, Q):
                    break
                dfs(path + [Q], dirs + [dd], kmax)

    for kmax in range(2, KMAX + 1):
        dfs([P1], [init_dir] if init_dir is not None else [], kmax)
        if best[0] is not None and kmax >= 3:
            break
    return best[0]


pads_by_ref = {}
for p in D["pads"]:
    if p["layer"] in ("F.Cu", "B.Cu") and p["hole"] == 0:
        pads_by_ref.setdefault(p["ref"].split(".")[0], []).append(p)

rem, add, rep = [], [], []
groups = []
def targets():
    """yield (ref, layer, pad, pad centre, outward unit vector): two-pad parts (axis = away from the other pad) or, with --ic REF, the pads of that IC (axis = straight out of the package edge, the exposed pad is skipped)"""
    if opt["--ic"]:
        rf = opt["--ic"]
        ps = pads_by_ref.get(rf, [])
        if not ps:
            return
        cs = [Polygon(p["pts"]).centroid for p in ps]
        cx = sum(c.x for c in cs) / len(cs)
        cy = sum(c.y for c in cs) / len(cs)
        areas = [Polygon(p["pts"]).area for p in ps]
        for p, c, a in zip(ps, cs, areas):
            if a > 0.5 * max(areas) and a > 1.0:
                continue
            dx, dy = c.x - cx, c.y - cy
            u = (math.copysign(1.0, dx), 0.0) if abs(dx) > abs(dy) else (0.0, math.copysign(1.0, dy))
            yield rf, p["layer"], p, (c.x, c.y), u
        return
    for ref in sorted(pads_by_ref):
        ps = pads_by_ref[ref]
        if not REFRE.match(ref) or len(ps) != 2 or ps[0]["layer"] != ps[1]["layer"]:
            continue
        if (ONLY and ref not in ONLY) or ref in SKIP:
            continue
        cs = [Polygon(p["pts"]).centroid for p in ps]
        for i in (0, 1):
            ax = (cs[i].x - cs[1 - i].x, cs[i].y - cs[1 - i].y)
            al = math.hypot(*ax)
            yield ref, ps[0]["layer"], ps[i], (cs[i].x, cs[i].y), (ax[0] / al, ax[1] / al)


for ref, L, p, C, u in targets():
    if True:
        net = p["net"]
        name = p["ref"]
        poly = Polygon(p["pts"]).buffer(0)
        ua = math.degrees(math.atan2(u[1], u[0]))
        if any(near(v["p"], C, 0.3) and v["net"] == net for v in vias):
            continue
        # stubs: straight pieces of the net that touch the pad
        touching = [t for t in segs if t["layer"] == L and t["net"] == net and (poly.distance(Point(t["a"])) < 0.01 or poly.distance(Point(t["b"])) < 0.01)]
        inside = [t for t in touching if poly.distance(Point(t["a"])) < 0.01 and poly.distance(Point(t["b"])) < 0.01]
        seeds = [t for t in touching if t not in inside]
        if not seeds:
            continue
        chains = []
        okc = True
        for t in seeds:
            ina = poly.distance(Point(t["a"])) < 0.01
            far = t["b"] if ina else t["a"]
            pcs = [t]
            excl = {id(x) for x in inside} | {id(x) for x in seeds}
            verts = [far]
            if interior_touch(L, net, t, excl):
                okc = False
                break
            term = None
            split = None
            if plen([t["a"], t["b"]]) > 1.6:
                # a long first piece: cut it 0.8 mm from the pad end, the rest stays
                inn = t["a"] if ina else t["b"]
                dd = (far[0] - inn[0], far[1] - inn[1])
                dl = math.hypot(*dd)
                Wc = (inn[0] + dd[0] / dl * 0.8, inn[1] + dd[1] / dl * 0.8)
                split = (far, Wc)
                verts = [Wc]
                term = "cut"
            while term is None:
                P = verts[-1]
                nxt, oth = at_vertex(L, net, P, excl)
                nxt = [x for x in nxt if id(x) not in {id(y) for y in pcs}]
                if oth == 1 and len(nxt) == 1 and plen([nxt[0]["a"], nxt[0]["b"]]) < 0.08:
                    # a micro piece between the chain and a via: take it into the chain, the via centre is the terminal
                    vv = next((v for v in vias if v["net"] == net and (near(v["p"], nxt[0]["a"], 0.03) or near(v["p"], nxt[0]["b"], 0.03))), None)
                    if vv is not None and id(nxt[0]) not in gone:
                        pcs.append(nxt[0])
                        verts.append(tuple(vv["p"]))
                        term = "fixed"
                        break
                if oth or len(nxt) != 1 or interior_touch(L, net, nxt[0], excl | {id(y) for y in pcs}) or id(nxt[0]) in gone or any(near(P, (ea[2][0], ea[2][1]), 0.02) or near(P, (ea[3][0], ea[3][1]), 0.02) for ea in add if ea[0] == L and ea[1] == net):
                    term = "fixed"
                    break
                if math.hypot(P[0] - C[0], P[1] - C[1]) >= REACH:
                    term = "cut"
                    break
                u2 = nxt[0]
                Q = u2["b"] if near(u2["a"], P) else u2["a"]
                if plen([P, Q]) > 1.6:
                    term = "cut"
                    break
                pcs.append(u2)
                verts.append(Q)
                if len(pcs) > 8:
                    break
            chains.append((pcs, verts, term, split))
        if not okc or not chains:
            rep.append((name, net, "skipped: stub with a branch on its side"))
            continue
        # does the pad already comply?
        exits = []
        for pcs, verts, term, split in chains:
            d0 = direction(C, verts[0] if not split else split[0])
            exits.append(turn(d0, ua))
        clean = all(e <= TOL for e in exits) and len(chains) == 1 and not inside
        if clean:
            # also require that the first piece after the exit is not tiny
            pcs, verts, term, split = chains[0]
            if all(plen([a, b]) >= 0.1 for a, b in zip([C] + verts[:-1], verts)):
                continue
        # ---- plan the re-draw
        reach_ = max([math.hypot(w[0][0] - C[0], w[0][1] - C[1]) for w in []] + [3.5])
        hl = max((q[0] - C[0]) * u[0] + (q[1] - C[1]) * u[1] for q in p["pts"])
        removed_ids = {id(x) for x in inside}
        for pcs, verts, term, split in chains:
            removed_ids |= {id(x) for x in pcs}
        # the terminals
        Ws = []
        for pcs, verts, term, split in chains:
            W = verts[-1]
            # the next old piece beyond a cut vertex
            nxt_dir = None
            if term == "cut":
                nx, _ = at_vertex(L, net, W, {id(x) for x in pcs} | {id(x) for x in inside} | {id(x) for x in seeds})
                if split:
                    nxt_dir = direction(split[1], split[0])
                elif len(nx) == 1:
                    O2 = nx[0]["b"] if near(nx[0]["a"], W) else nx[0]["a"]
                    nxt_dir = direction(W, O2)
            Ws.append((W, nxt_dir))
        LOCAL[:] = [o for o in obst[L] + added[L] if o[0].distance(Point(C)) < max(3.5, max(math.hypot(w[0][0] - C[0], w[0][1] - C[1]) for w in Ws) + 1.5)]
        best_total = None
        hw = max(abs((q[0] - C[0]) * (-u[1]) + (q[1] - C[1]) * u[0]) for q in p["pts"])
        k0 = int(round((ua % 360) / 45.0)) % 8
        dev0 = ang_diff(k0 * 45, ua)
        modes = [("axis", None)]
        if SNAP > 0 and 1e-6 < dev0 <= SNAP and hl * math.tan(math.radians(dev0)) <= 0.4 * hw:
            modes.append(("snap", k0))
        for e1 in EXT:
          for mode, kk0 in modes:
            if mode == "axis":
                P1 = (C[0] + u[0] * (hl + e1), C[1] + u[1] * (hl + e1))
                pen = 0.0
                init = None
            else:
                ln0 = (hl + e1) / math.cos(math.radians(dev0))
                P1 = (C[0] + DIRS[kk0][0] * ln0, C[1] + DIRS[kk0][1] * ln0)
                pen = 0.03 * dev0
                init = kk0
            if not clear(L, net, C, P1):
                continue
            # allowed first directions from P1 (axis mode): straight on when the axis is octilinear, or a bend of MINFT..90 degrees
            first_ok = []
            for kk in range(8):
                tr_ = ang_diff(kk * 45, ua)
                if tr_ < 1e-6 or MINFT - 1e-6 <= tr_ <= 90 + 1e-6:
                    first_ok.append(kk)
            res = []
            same_new = []
            okall = True
            used_first = []
            for W, nd in sorted(Ws, key=lambda w: math.hypot(w[0][0] - P1[0], w[0][1] - P1[1])):
                if math.hypot(W[0] - P1[0], W[1] - P1[1]) < 0.05:
                    okall = False
                    break
                # the paths of one pad must leave P1 at least 90 degrees apart (no 45-degree forks, no overlapping pieces)
                fo = [k_ for k_ in first_ok if all(ang_diff(k_ * 45, d_ * 45) >= 90 - 1e-6 for d_ in used_first)]
                if init is not None and used_first and any(ang_diff(init * 45, d_ * 45) < 90 - 1e-6 for d_ in used_first):
                    okall = False
                    break
                if not fo and init is None:
                    okall = False
                    break
                CUR["C"] = C
                r = paths_from(L, net, P1, ua, W, nd, poly, same_new, P1, fo, init)
                if r is None:
                    okall = False
                    break
                dd_ = direction(r[1][0], r[1][1])
                used_first.append(int(round((dd_ % 360) / 45.0)) % 8)
                res.append(r)
                for a_, b_ in zip(r[1][:-1], r[1][1:]):
                    same_new.append(LineString([a_, b_]))
            if not okall:
                continue
            total = plen([C, P1]) + sum(r[0] for r in res) + pen
            if best_total is None or total < best_total[0]:
                best_total = (total, P1, res)
        if best_total is None:
            rep.append((name, net, "no clean exit path"))
            continue
        _, P1, res = best_total
        g_r0, g_a0 = len(rem), len(add)
        old_len = sum(plen([a["a"], a["b"]]) for pcs, _, _, _ in chains for a in pcs)
        for pcs, verts, term, split in chains:
            for x in pcs:
                rem.append([L, net, [x["a"][0], x["a"][1]], [x["b"][0], x["b"][1]]])
            if split:
                add.append([L, net, [split[1][0], split[1][1]], [split[0][0], split[0][1]]])
        for x in inside:
            rem.append([L, net, [x["a"][0], x["a"][1]], [x["b"][0], x["b"][1]]])
        # axis piece (merged with a straight first piece when collinear) and the paths
        newp = []
        # collect pieces: C->P1, then each path; merge collinear neighbours per path
        segs_new = [(C, P1)]
        for r in res:
            pts = r[1]
            for a, b in zip(pts[:-1], pts[1:]):
                segs_new.append((a, b))
        # merge the axis piece with a collinear continuation when there is exactly one path
        if len(res) == 1:
            pts = [C] + res[0][1]
            mrg = [pts[0]]
            for q in pts[1:]:
                if len(mrg) >= 2:
                    a, c = mrg[-2], mrg[-1]
                    cr = (c[0] - a[0]) * (q[1] - c[1]) - (c[1] - a[1]) * (q[0] - c[0])
                    dt = (c[0] - a[0]) * (q[0] - c[0]) + (c[1] - a[1]) * (q[1] - c[1])
                    if abs(cr) < 1e-9 and dt > 0:
                        mrg[-1] = q
                        continue
                mrg.append(q)
            segs_new = list(zip(mrg[:-1], mrg[1:]))
        for a, b in segs_new:
            add.append([L, net, [a[0], a[1]], [b[0], b[1]]])
            added[L].append([LineString([a, b]).buffer(0.05), "trk", net, None])
        gone |= removed_ids
        groups.append({"name": name, "remove": rem[g_r0:], "add": add[g_a0:]})
        rep.append((name, net, "re-drawn: %d stub(s), %d pieces, %.2f mm (was %.2f)" % (len(chains), len(segs_new), sum(plen([a, b]) for a, b in segs_new), old_len)))
for r in rep:
    print(*r)
print("re-drawn %d, left %d" % (sum(1 for r in rep if r[2].startswith("re-drawn")), sum(1 for r in rep if not r[2].startswith("re-drawn"))))
json.dump({"remove": rem, "add": add, "groups": groups}, open(outf, "w"))
