"""fix_joints.py IN OUT [--snap 0.005] [--nets NET ...] [--include-ring] : make joints exact WITHOUT moving copper (beyond a few nanometres / micrometres).
Only two operations, both for the joints check_joints.py lists:
  ends d      two ends of one layer d <= --snap mm apart (default 5 micrometres): every end at the second point is set EXACTLY on the first one (the point with more pieces on it)
  T-on-body   an end on the side of a straight piece (<= --snap mm off its line): the host piece is cut in two at that point, so the T has a node (same width, layer, net)
  via-on-body a via centre on the side of a straight piece: cut at the via centre
  pad snap    an end within --snap of a pad position (and inside the pad): set exactly on the position
  end-in-pad  an end inside a pad: joined to the pad position by axis-parallel pieces that lie entirely inside the pad copper (no copper outside the pad changes)
Nothing else is touched; larger gaps and vias near a piece are only listed.  Default nets: every net except the LED ring nets (ROWn / COLn, arcs) and zone-only nets.
usage (KiCad python): fix_joints.py in.kicad_pcb out.kicad_pcb"""
import sys, re, math
import pcbnew
sys.path.insert(0, __file__.rsplit("/", 1)[0].rsplit("\\", 1)[0])
from check_joints import make, seg_d
args = sys.argv[1:]
snap = 0.005
nets = []
ring_ok = "--include-ring" in args
i = 2
while i < len(args):
    if args[i] == "--snap": snap = float(args[i + 1]); i += 2
    elif args[i] == "--nets":
        i += 1
        while i < len(args) and not args[i].startswith("--"): nets.append(args[i]); i += 1
    else: i += 1
SN = int(round(snap * 1e6))
b = pcbnew.LoadBoard(args[0]); mm = pcbnew.ToMM
ring = re.compile(r"^/(ROW\d+|COL\d+)$")
V = lambda p: pcbnew.VECTOR2I(int(p[0]), int(p[1]))
log = []; maxmove = 0.0
def degree(its, p, layer):
    return sum(1 for o in its if o.kind in ("trk", "arc") and o.layer == layer and (o.a == p or o.c == p)) + sum(1 for o in its if o.kind == "via" and o.p == p)
DEV = [0.0]
def split_arcs():
    """cut every arc at each via centre / piece end of its net and layer that lies on its body (within 3 micrometres): same circle, same copper, a node at every join"""
    n_cut = 0; maxdev = 0.0
    arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC" and ring.match(t.GetNetname() or "")]
    allt = [t for t in b.GetTracks()]
    for a in arcs:
        n = a.GetNetname(); layer = a.GetLayer(); c = a.GetCenter(); R = a.GetRadius()
        ang = lambda q: math.atan2(q.y - c.y, q.x - c.x)
        a0, am, a1 = ang(a.GetStart()), ang(a.GetMid()), ang(a.GetEnd())
        ccw = lambda x, y: (y - x) % (2 * math.pi)
        dirn = 1 if ccw(a0, am) <= ccw(a0, a1) else -1
        span = ccw(a0, a1) if dirn == 1 else (2 * math.pi - ccw(a0, a1)) % (2 * math.pi)
        theta = lambda q: (ccw(a0, ang(q)) if dirn == 1 else (2 * math.pi - ccw(a0, ang(q))) % (2 * math.pi))
        cand = {}
        for t in allt:
            if t.GetNetname() != n or t is a: continue
            pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else ([t.GetStart(), t.GetEnd()] if t.GetLayer() == layer else [])
            for q in pts:
                dq = math.hypot(q.x - c.x, q.y - c.y)
                if t.GetClass() == "PCB_VIA":
                    # a via whose copper circle the arc runs through: cut the arc at the foot of the perpendicular (exactly on the arc, so no copper moves);
                    # that point is inside the via's circle, which is how U enters a via
                    if abs(dq - R) > t.GetWidth(pcbnew.B_Cu) // 2 * 0.98: continue
                    q = pcbnew.VECTOR2I(int(round(c.x + (q.x - c.x) * R / dq)), int(round(c.y + (q.y - c.y) * R / dq)))
                elif abs(dq - R) > 3000: continue
                th = theta(q)
                if th * R < 3000 or (span - th) * R < 3000 or th > span: continue
                cand[(q.x, q.y)] = th
        if not cand: continue
        pts = sorted(cand.items(), key=lambda kv: kv[1])
        st0, en0 = (a.GetStart().x, a.GetStart().y), (a.GetEnd().x, a.GetEnd().y)          # copies: SetEnd below would change a live reference
        chain = [(st0, 0.0)] + [(k, th) for k, th in pts] + [(en0, span)]
        orig = [(c.x + R * math.cos(a0 + dirn * span * k / 400), c.y + R * math.sin(a0 + dirn * span * k / 400)) for k in range(401)]
        width = a.GetWidth(); net = a.GetNet(); first = True
        for (p0, t0), (p1, t1) in zip(chain, chain[1:]):
            tm = (t0 + t1) / 2; am_ = a0 + dirn * tm
            mid = pcbnew.VECTOR2I(int(round(c.x + R * math.cos(am_))), int(round(c.y + R * math.sin(am_))))
            maxdev = max(maxdev, abs(math.hypot(mid.x - c.x, mid.y - c.y) - R) / 1e6)
            P0, P1 = pcbnew.VECTOR2I(int(p0[0]), int(p0[1])), pcbnew.VECTOR2I(int(p1[0]), int(p1[1]))
            if first: a.SetStart(P0); a.SetMid(mid); a.SetEnd(P1); first = False; new_arcs = [a]
            else:
                na = pcbnew.PCB_ARC(b); na.SetLayer(layer); na.SetWidth(width); na.SetNet(net); na.SetStart(P0); na.SetMid(mid); na.SetEnd(P1); b.Add(na); new_arcs.append(na)
            n_cut += 1
        n_cut -= 1
        # check: every point of the original arc is within 3.5 micrometres of one of the new arcs (the new arcs pass exactly through the via centres, which sit up to a few tens of nm off the old circle), and the spans add up
        tot = 0.0
        for na in new_arcs:
            cc = na.GetCenter(); RR = na.GetRadius(); maxdev = max(maxdev, abs(RR - R) / 1e6, math.hypot(cc.x - c.x, cc.y - c.y) / 1e6 if False else 0)
        for (x, y) in orig[::8]:
            best = 9e18
            for na in new_arcs:
                cc = na.GetCenter(); RR = na.GetRadius(); a_ = lambda q: math.atan2(q.y - cc.y, q.x - cc.x); s0, sm, s1 = a_(na.GetStart()), a_(na.GetMid()), a_(na.GetEnd())
                cw = lambda u, v: (v - u) % (2 * math.pi); dd = 1 if cw(s0, sm) <= cw(s0, s1) else -1; sp_ = cw(s0, s1) if dd == 1 else (2 * math.pi - cw(s0, s1)) % (2 * math.pi)
                th_ = a_(pcbnew.VECTOR2I(int(x), int(y))) if False else math.atan2(y - cc.y, x - cc.x)
                rel = cw(s0, th_) if dd == 1 else (2 * math.pi - cw(s0, th_)) % (2 * math.pi)
                if rel <= sp_ + 1e-9: best = min(best, abs(math.hypot(x - cc.x, y - cc.y) - RR))
            DEV[0] = max(DEV[0], best)
            if best > 3500: raise SystemExit('arc split check failed on %s: a point of the original arc is %.1f nm from the new arcs' % (n, best))
    return n_cut, maxdev
if ring_ok:
    cuts, dev = split_arcs(); log.append("arcs: %d cuts at via centres / piece ends on arc bodies (arc copper moved by at most %.4f mm to pass exactly through them)" % (cuts, DEV[0] / 1e6)); maxmove = max(maxmove, DEV[0] / 1e6)
for rnd in range(40):
    A = make(b); changed = 0; touched = set()
    for n in sorted(set(A.items)):
        if not n or (nets and n not in nets) or (not nets and ((ring.match(n) and not ring_ok) or n in A.zone_nets)): continue
        its, comps, out = A.joints(n)
        for pdo in A.pads[n]:                                  # an end a few micrometres from a pad position: exactly on it
            for o in its:
                if o.kind not in ("trk", "arc") or id(o.obj) in touched: continue
                if not (pdo.tht or pdo.obj.IsOnLayer(o.layer)): continue
                for which in ("a", "c"):
                    e = getattr(o, which); d = math.hypot(e[0] - pdo.p[0], e[1] - pdo.p[1])
                    if 0 < d <= SN and pdo.obj.HitTest(pcbnew.VECTOR2I(*e)):
                        for q in its:
                            if q.kind in ("trk", "arc") and q.layer == o.layer and id(q.obj) not in touched:
                                if q.a == e: q.obj.SetStart(V(pdo.p)); touched.add(id(q.obj))
                                if q.c == e: q.obj.SetEnd(V(pdo.p)); touched.add(id(q.obj))
                        maxmove = max(maxmove, d / 1e6); changed += 1; log.append("%s: end snapped onto pad %s (%.4f mm)" % (n, pdo.name, d / 1e6))
        for k, e, desc, ia, ib, ex in out:
            if k.startswith("ends") and ex["d"] <= SN:
                o, q, ea, eb = ex["a"], ex["b"], ex["ea"], ex["eb"]
                if id(o.obj) in touched or id(q.obj) in touched: continue
                tgt, src = (ea, eb) if degree(its, ea, o.layer) >= degree(its, eb, q.layer) else (eb, ea)
                for p in its:                                  # every end of this layer exactly at src moves to tgt
                    if p.kind in ("trk", "arc") and p.layer == o.layer and not id(p.obj) in touched:
                        if p.a == src: p.obj.SetStart(V(tgt)); touched.add(id(p.obj))
                        if p.c == src: p.obj.SetEnd(V(tgt)); touched.add(id(p.obj))
                touched.add(id(o.obj)); touched.add(id(q.obj))
                maxmove = max(maxmove, ex["d"] / 1e6); changed += 1; log.append("%s: ends snapped (%.4f mm) at (%.4f, %.4f)" % (n, ex["d"] / 1e6, mm(tgt[0]), mm(tgt[1])))
            elif k == "via-near" and ex.get("foot_in"):
                h = ex["host"]
                if h.kind != "trk" or id(h.obj) in touched: continue
                at = ex["foot"]; t = h.obj; old_end = t.GetEnd()
                new = pcbnew.PCB_TRACK(b); new.SetLayer(t.GetLayer()); new.SetWidth(t.GetWidth()); new.SetNet(t.GetNet())
                new.SetStart(V(at)); new.SetEnd(old_end); t.SetEnd(V(at)); b.Add(new)
                touched.add(id(t)); changed += 1; log.append("%s: piece cut at the foot of its via (%.4f, %.4f), inside the via circle" % (n, mm(at[0]), mm(at[1])))
            elif k in ("T-on-body", "via-on-body") and ex["off"] <= SN:
                h = ex["host"]
                if h.kind != "trk" or id(h.obj) in touched: continue
                at = ex["at"]; t = h.obj; old_end = t.GetEnd()
                new = pcbnew.PCB_TRACK(b); new.SetLayer(t.GetLayer()); new.SetWidth(t.GetWidth()); new.SetNet(t.GetNet())
                new.SetStart(V(at)); new.SetEnd(old_end); t.SetEnd(V(at)); b.Add(new)
                touched.add(id(t)); maxmove = max(maxmove, ex["off"] / 1e6); changed += 1; log.append("%s: %s cut at (%.4f, %.4f) (%.4f mm off the line)" % (n, k, mm(at[0]), mm(at[1]), ex["off"] / 1e6))
            elif k == "end-in-pad":
                pad, pc, end = ex["pad"], ex["piece"], ex["end"]
                if id(pc.obj) in touched: continue
                tgt = pad.p
                for legs in (((end[0], tgt[1]),), ((tgt[0], end[1]),)):          # end -> corner -> pad position, axis-parallel legs
                    pts = [end] + [l for l in legs] + [tgt]
                    ok = True
                    for a, c in zip(pts, pts[1:]):
                        n_s = max(2, int(math.hypot(c[0] - a[0], c[1] - a[1]) / 5000))
                        for t in range(1 if a == end else 0, n_s + 1):
                            x = a[0] + (c[0] - a[0]) * t / n_s; y = a[1] + (c[1] - a[1]) * t / n_s; hw = pc.w / 2
                            for dx, dy in (((0, 0), (hw, 0), (-hw, 0)) if a[0] == c[0] else ((0, 0), (0, hw), (0, -hw))):
                                if not pad.obj.HitTest(pcbnew.VECTOR2I(int(x + dx), int(y + dy))): ok = False
                    if ok:
                        for a, c in zip(pts, pts[1:]):
                            if a == c: continue
                            new = pcbnew.PCB_TRACK(b); new.SetLayer(pc.obj.GetLayer()); new.SetWidth(pc.obj.GetWidth()); new.SetNet(pc.obj.GetNet()); new.SetStart(V(a)); new.SetEnd(V(c)); b.Add(new)
                        touched.add(id(pc.obj)); changed += 1; log.append("%s: end inside %s joined to the pad position through the pad (no copper outside the pad)" % (n, pad.name)); break
    if not changed: break
print("passes:", rnd + 1, " operations:", len(log), " largest copper displacement: %.4f mm" % maxmove)
for l in log: print("  ", l)
pcbnew.SaveBoard(args[1], b)
