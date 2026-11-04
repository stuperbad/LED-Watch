"""check_joints.py BOARD [NET ...] [--list] : does KiCad's select-connected command (U, last press) reach the whole net?  Finds the joints where it stops.

Rules taken from KiCad's source (pcbnew/tools/pcb_selection_tool.cpp, selectAllConnectedTracks), read 2026-11-04:
  * the walk moves from point to point; tracks and arcs are indexed by their START and END point as integer nanometres: two pieces are connected
    when a start / end point is EXACTLY equal (no tolerance) and they share a copper layer;
  * a via is entered when a point is exactly on its centre or inside its copper circle (any copper layer); every piece end inside that circle is taken along;
  * a pad is entered only when a point is exactly on the pad's position; a piece that merely crosses or ends inside a pad is not followed;
  * a piece that ends on the SIDE of another piece (T) is not followed, a piece that overlaps another is not followed.
DRC / ratsnest use real copper overlap, so they call such a net connected while U stops.
Output per net: the number of separate pieces in the walk model (1 = U reaches everything), and for each pair of pieces that touch in copper but are not joined in the walk: where, and what kind
  T-on-body      an end lies on the side of a piece of the same net / layer                (fix: split that piece at the point: no copper changes)
  ends 0.000x    two ends on one layer a few nanometres to micrometres apart                (fix: make them equal)
  ends 0.0xx     two ends further apart but still overlapping copper                       (fix needs an end to move: listed)
  end-in-pad     an end inside a pad but not on its position                               (listed)
  via-on-body    a via centre lies on the side of a piece                                  (fix: split the piece at the via centre)
  via-near       a piece passes a via with no end inside its circle                         (listed)
Arcs are walked by their end points only (a via sitting on the body of an arc is not seen): the LED ring nets ROWn / COLn are therefore not reliable here.
usage (KiCad python): check_joints.py board.kicad_pcb [NET ...] [--list]     no net = summary line per net with more than one piece; --list prints every joint
Zone-only nets (GND with its plane) are skipped unless named.   `make(board)` is also imported by fix_joints.py.   Written 2026-11-04 after the owner saw VBAT split when pressing U."""
import sys, math, collections, types
import pcbnew
mm = pcbnew.ToMM

def seg_d(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(p[0] - a[0], p[1] - a[1]), 0.0
    u = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy), u

class It: pass

def make(b):
    LN = lambda l: b.GetLayerName(l)
    pt = lambda p: (p.x, p.y)                      # integer nanometres
    items = collections.defaultdict(list); pads = collections.defaultdict(list)
    for t in b.GetTracks():
        o = It(); o.obj = t; o.net = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            o.kind = "via"; o.p = pt(t.GetPosition()); o.r = t.GetWidth(pcbnew.B_Cu) // 2; o.layer = None; o.w = t.GetWidth(pcbnew.B_Cu)
        else:
            o.kind = "arc" if t.GetClass() == "PCB_ARC" else "trk"; o.a = pt(t.GetStart()); o.c = pt(t.GetEnd()); o.layer = t.GetLayer(); o.w = t.GetWidth()
        items[o.net].append(o)
    for f in b.GetFootprints():
        for p in f.Pads():
            o = It(); o.kind = "pad"; o.obj = p; o.p = pt(p.GetPosition()); o.name = f.GetReference() + "." + p.GetNumber(); o.net = p.GetNetname(); o.tht = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            pads[o.net].append(o)
    def walk(n):
        its = items[n]; ps = pads[n]
        par = list(range(len(its)))
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        def uni(a, c): par[find(a)] = find(c)
        bypos = collections.defaultdict(list)
        for i, o in enumerate(its):
            if o.kind in ("trk", "arc"): bypos[o.a].append(i); bypos[o.c].append(i)
        for pos, lst in bypos.items():
            for x in range(len(lst)):
                for y in range(x + 1, len(lst)):
                    if its[lst[x]].layer == its[lst[y]].layer and lst[x] != lst[y]: uni(lst[x], lst[y])
        for i, o in enumerate(its):
            if o.kind != "via": continue
            for j, q in enumerate(its):
                if q.kind in ("trk", "arc"):
                    for e in (q.a, q.c):
                        if (e[0] - o.p[0]) ** 2 + (e[1] - o.p[1]) ** 2 <= o.r * o.r: uni(i, j)
        for o in ps:
            hits = [i for i in bypos.get(o.p, []) if o.tht or o.obj.IsOnLayer(its[i].layer)]
            for k in range(1, len(hits)): uni(hits[0], hits[k])
            for i, q in enumerate(its):
                if q.kind == "via" and q.p == o.p and hits: uni(i, hits[0])
        return its, ps, find
    def touching(o, q):
        if o.kind == "via" and q.kind == "via": return math.hypot(o.p[0] - q.p[0], o.p[1] - q.p[1]) - o.r - q.r
        if o.kind == "via": q, o = o, q
        if q.kind == "via":
            d, _ = seg_d(q.p, o.a, o.c); return d - q.r - o.w / 2
        if o.layer != q.layer: return None
        best = 9e18
        for e in (o.a, o.c): best = min(best, seg_d(e, q.a, q.c)[0])
        for e in (q.a, q.c): best = min(best, seg_d(e, o.a, o.c)[0])
        return best - o.w / 2 - q.w / 2
    def classify(o, q, i, j):
        """returns (kind, point, text, i, j, extra) ; extra = dict used by the fixer"""
        if o.kind == "via" or q.kind == "via":
            v, t = (o, q) if o.kind == "via" else (q, o)
            if t.kind == "via": return ("via-via", v.p, "two vias overlap", i, j, {})
            dd, u = seg_d(v.p, t.a, t.c)
            if dd / 1e6 < 0.002 and 0.001 < u < 0.999: return ("via-on-body", v.p, "via centre on the side of a %s piece" % LN(t.layer), i, j, dict(host=t, at=v.p, off=dd))
            ex = {}
            if t.kind == "trk" and dd < v.r * 0.98:
                foot = (int(round(t.a[0] + (t.c[0] - t.a[0]) * u)), int(round(t.a[1] + (t.c[1] - t.a[1]) * u)))
                ex = dict(host=t, foot=foot, foot_in=((foot[0] - v.p[0]) ** 2 + (foot[1] - v.p[1]) ** 2 <= v.r * v.r and 0.001 < u < 0.999))
            return ("via-near", v.p, "a %s piece passes %.3f mm from the via centre, no end inside its circle" % (LN(t.layer), dd / 1e6), i, j, ex)
        best = None
        for ea in (o.a, o.c):
            for eb in (q.a, q.c):
                d = math.hypot(ea[0] - eb[0], ea[1] - eb[1])
                if best is None or d < best[0]: best = (d, ea, eb)
        d, ea, eb = best
        for e, host, mine in ((o.a, q, o), (o.c, q, o), (q.a, o, q), (q.c, o, q)):
            dd, u = seg_d(e, host.a, host.c)
            if 0.001 < u < 0.999 and dd < max(mine.w, host.w) / 2 and dd <= d and min(math.hypot(e[0] - host.a[0], e[1] - host.a[1]), math.hypot(e[0] - host.c[0], e[1] - host.c[1])) > 10000:
                return ("T-on-body", e, "%s end on the side of a piece %s-%s, %.4f mm off its line" % (LN(mine.layer), (round(mm(host.a[0]), 3), round(mm(host.a[1]), 3)), (round(mm(host.c[0]), 3), round(mm(host.c[1]), 3)), dd / 1e6), i, j, dict(host=host, mine=mine, at=e, off=dd))
        if d < max(o.w, q.w):
            return ("ends %.4f" % (d / 1e6), ea, "%s ends (%.4f, %.4f) and (%.4f, %.4f)" % (LN(o.layer), mm(ea[0]), mm(ea[1]), mm(eb[0]), mm(eb[1])), i, j, dict(a=o, b=q, ea=ea, eb=eb, d=d))
        return ("overlap", ea, "%s pieces overlap" % LN(o.layer), i, j, {})
    def joints(n):
        its, ps, find = walk(n)
        comps = collections.defaultdict(list)
        for i in range(len(its)): comps[find(i)].append(i)
        out = []
        if len(comps) > 1:
            for i in range(len(its)):
                for j in range(i + 1, len(its)):
                    if find(i) == find(j): continue
                    d = touching(its[i], its[j])
                    if d is None or d > 0: continue
                    out.append(classify(its[i], its[j], i, j))
            for o in ps:
                for i, q in enumerate(its):
                    if q.kind not in ("trk", "arc"): continue
                    lay = o.tht or o.obj.IsOnLayer(q.layer)
                    for e in (q.a, q.c):
                        if lay and e != o.p and o.obj.HitTest(pcbnew.VECTOR2I(*e)):
                            others = [k for k, r in enumerate(its) if find(k) != find(i) and r.kind in ("trk", "arc") and (r.a == o.p or r.c == o.p) and (o.tht or o.obj.IsOnLayer(r.layer))]
                            if others: out.append(("end-in-pad", e, "%s: a %s end is %.3f mm off the pad position" % (o.name, LN(q.layer), math.hypot(e[0] - o.p[0], e[1] - o.p[1]) / 1e6), i, others[0], dict(pad=o, piece=q, end=e)))
        return its, comps, out
    zone_nets = {z.GetNetname() for z in b.Zones() if not z.GetIsRuleArea()}
    return types.SimpleNamespace(b=b, items=items, pads=pads, joints=joints, walk=walk, LN=LN, zone_nets=zone_nets)

if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    LIST = "--list" in sys.argv
    b = pcbnew.LoadBoard(argv[0]); want = set(argv[1:])
    A = make(b); LN = A.LN
    res = {}
    for n in sorted(set(A.items)):
        if not n or (want and n not in want) or (n in A.zone_nets and not want): continue
        res[n] = A.joints(n)
    if want or LIST:
        for n, (its, comps, out) in res.items():
            print("=== %s: %d piece(s) in the U-walk model, %d joint(s) that only touch" % (n, len(comps), len(out)))
            for k, e, desc, i, j, ex in sorted(out, key=lambda s: (s[1][0], s[1][1])): print("   %-14s at (%.4f, %.4f)  %s" % (k, mm(e[0]), mm(e[1]), desc))
            if len(comps) > 1:
                for r, m in sorted(comps.items(), key=lambda x: -len(x[1])):
                    t = [its[i] for i in m if its[i].kind in ("trk", "arc")]
                    print("      piece of %3d items%s" % (len(m), ("  e.g. %s (%.3f, %.3f)-(%.3f, %.3f)" % (LN(t[0].layer), mm(t[0].a[0]), mm(t[0].a[1]), mm(t[0].c[0]), mm(t[0].c[1]))) if t else ""))
    else:
        print("%-16s %7s %7s" % ("net", "pieces", "joints"))
        tot = 0
        for n, (its, comps, out) in sorted(res.items(), key=lambda x: -len(x[1][1])):
            if len(comps) > 1: print("%-16s %7d %7d" % (n, len(comps), len(out))); tot += 1
        print("nets that U does not walk as one piece:", tot, "of", len(res))
