"""cleanlib.py : rebuild chains of track pieces that have micro pieces or ends off a pad / via centre, only chains that contain pieces of the owner's added set"""
import math
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
MICRO, MAXMOVE = 0.05, 0.12
def xy(p): return (tomm(p.x), tomm(p.y))
def rd(p): return (round(p[0], 4), round(p[1], 4))
def key(b, t): return (b.GetLayerName(t.GetLayer()), t.GetNetname(), tuple(sorted([rd(xy(t.GetStart())), rd(xy(t.GetEnd()))])))
def snap8(dx, dy):
    a = round(math.degrees(math.atan2(dy, dx)) / 45) * 45
    return (round(math.cos(math.radians(a))), round(math.sin(math.radians(a))))
def inter(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9: return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


CLR, HOLE = 0.10, 0.20
def _dseg(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
def _seg_seg(a, c, e, f):
    best = min(_dseg(a, e, f), _dseg(c, e, f), _dseg(e, a, c), _dseg(f, a, c))
    # crossing segments
    def ccw(p, q, r): return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    if (ccw(a, e, f) * ccw(c, e, f) < 0) and (ccw(a, c, e) * ccw(a, c, f) < 0): return 0.0
    return best
def margins(b, polyline, width, net, layer, skip_ids):
    """worst (smallest) slack against the rules for a polyline of this width: track-track / track-pad / track-via copper >= CLR edge to edge, track edge to via hole >= HOLE"""
    worst = 9.0
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    for q0, q1 in zip(polyline, polyline[1:]):
        for t in b.GetTracks():
            if id(t) in skip_ids or t.GetNetname() == net: continue
            if t.GetClass() == "PCB_VIA":
                c = xy(t.GetPosition()); d = _dseg(c, q0, q1)
                worst = min(worst, d - width / 2 - tomm(t.GetWidth(layer)) / 2 - CLR if t.IsOnLayer(layer) else 9, d - width / 2 - tomm(t.GetDrillValue()) / 2 - HOLE)
            elif t.GetClass() == "PCB_TRACK" and t.GetLayer() == layer:
                a, c = xy(t.GetStart()), xy(t.GetEnd()); worst = min(worst, _seg_seg(q0, q1, a, c) - width / 2 - tomm(t.GetWidth()) / 2 - CLR)
        for p in pads:
            if p.GetNetname() == net or not p.IsOnLayer(layer): continue
            bb = p.GetBoundingBox(); R = (tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
            if max(q0[0], q1[0]) < R[0] - 1 or min(q0[0], q1[0]) > R[2] + 1 or max(q0[1], q1[1]) < R[1] - 1 or min(q0[1], q1[1]) > R[3] + 1: continue
            n = max(2, int(math.hypot(q1[0] - q0[0], q1[1] - q0[1]) / 0.02)); dmin = 9
            for i in range(n + 1):
                px = q0[0] + (q1[0] - q0[0]) * i / n; py = q0[1] + (q1[1] - q0[1]) * i / n
                dmin = min(dmin, math.hypot(max(R[0] - px, 0, px - R[2]), max(R[1] - py, 0, py - R[3])))
            worst = min(worst, dmin - width / 2 - CLR)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetDrillSizeX() > 0:
                c = xy(p.GetPosition()); worst = min(worst, _dseg(c, q0, q1) - width / 2 - tomm(p.GetDrillSizeX()) / 2 - HOLE)
    return worst

def clean_chains(b, owner_keys, box, skip=(), skip_ends=(), ends_too=True):
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    def anchor(pt, net, layer):
        P = pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1])); best = None
        for v in vias:
            if v.GetNetname() == net and v.IsOnLayer(layer):
                c = xy(v.GetPosition()); d = math.hypot(c[0] - pt[0], c[1] - pt[1])
                if d <= tomm(v.GetWidth(layer)) / 2 and (best is None or d < best[0]): best = (d, c)
        for p in pads:
            if p.GetNetname() == net and p.IsOnLayer(layer) and p.GetNumber() != "SH" and p.HitTest(P):
                c = xy(p.GetPosition()); d = math.hypot(c[0] - pt[0], c[1] - pt[1])
                if best is None or d < best[0]: best = (d, c)
        return best
    allp = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    inbox = lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
    done = set(); report = []; grave = []
    for t0 in list(allp):
        if id(t0) in done or id(t0) in {id(g) for g in grave}: continue
        net, layer = t0.GetNetname(), t0.GetLayer()
        if key(b, t0) not in owner_keys: continue
        if (t0.GetNetname(), b.GetLayerName(t0.GetLayer())) in skip: continue
        gids = {id(g) for g in grave}
        def here(pt):
            return [u for u in allp if id(u) not in gids and u.GetNetname() == net and u.GetLayer() == layer and (rd(xy(u.GetStart())) == pt or rd(xy(u.GetEnd())) == pt)]
        chain = [t0]; done.add(id(t0))
        for side in (0, 1):
            cur = t0; pt = rd(xy(cur.GetStart() if side == 0 else cur.GetEnd()))
            while True:
                h = here(pt); a = anchor(pt, net, layer)
                if len(h) != 2 or (a and a[0] < 0.002): break
                u = [x for x in h if x is not cur][0]
                if id(u) in done: break
                done.add(id(u)); chain = [u] + chain if side == 0 else chain + [u]
                s, e = rd(xy(u.GetStart())), rd(xy(u.GetEnd())); pt = e if s == pt else s; cur = u
        pts = [xy(chain[0].GetStart()), xy(chain[0].GetEnd())]
        if len(chain) > 1:
            s2, e2 = xy(chain[1].GetStart()), xy(chain[1].GetEnd())
            if rd(pts[0]) in (rd(s2), rd(e2)): pts.reverse()
        for u in chain[1:]:
            s, e = xy(u.GetStart()), xy(u.GetEnd()); pts.append(e if rd(pts[-1]) == rd(s) else s)
        lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        a0, a1 = anchor(pts[0], net, layer), anchor(pts[-1], net, layer)
        off0 = a0 and a0[0] > 0.004; off1 = a1 and a1[0] > 0.004
        micro_owner = any(lens[i] < MICRO and key(b, chain[i]) in owner_keys for i in range(len(chain)))
        end_owner = (off0 and key(b, chain[0]) in owner_keys) or (off1 and key(b, chain[-1]) in owner_keys)
        if not (micro_owner or (end_owner and ends_too)): continue
        if not any(inbox(p) for p in pts): continue
        lines = []
        for i in range(len(pts) - 1):
            if lens[i] < MICRO and len(pts) > 2: continue
            d = snap8(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); mid = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
            if lines and abs(lines[-1][1][0] * d[1] - lines[-1][1][1] * d[0]) < 1e-9 and (lines[-1][1][0] * d[0] + lines[-1][1][1] * d[1]) > 0:
                (pm, dm, wl) = lines[-1]; w = lens[i]
                lines[-1] = (((pm[0] * wl + mid[0] * w) / (wl + w), (pm[1] * wl + mid[1] * w) / (wl + w)), dm, wl + w)
            else: lines.append((mid, d, lens[i]))
        F0 = a0[1] if a0 else pts[0]; F1 = a1[1] if a1 else pts[-1]
        tag = (net, b.GetLayerName(layer), tuple(round(v, 3) for v in pts[0]), tuple(round(v, 3) for v in pts[-1]))
        if any((round(p[0], 3), round(p[1], 3)) in skip_ends for p in (pts[0], pts[-1])): report.append(("left alone (listed)",) + tag); continue
        if not lines: report.append(("skip: only micro pieces",) + tag); continue
        L = [list(l[:2]) for l in lines]; L[0][0] = F0; L[-1][0] = F1
        newpts = [F0]; ok = True
        for i in range(len(L) - 1):
            v = inter(L[i][0], L[i][1], L[i + 1][0], L[i + 1][1])
            if v is None: ok = False; break
            newpts.append(v)
        if not ok: report.append(("skip: parallel lines",) + tag); continue
        newpts.append(F1)
        if len(L) == 1:
            dx, dy = F1[0] - F0[0], F1[1] - F0[1]
            if math.hypot(dx, dy) > 1e-6 and abs(dx * L[0][1][1] - dy * L[0][1][0]) > 0.004: report.append(("skip: one line cannot join both ends",) + tag); continue
        def dseg(p, a, c):
            dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy
            u = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
            return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
        moved = max([min(dseg(q, newpts[i], newpts[i + 1]) for i in range(len(newpts) - 1)) for q in pts[1:-1]] or [0])
        if moved > MAXMOVE: report.append(("skip: a corner would move %.3f" % moved,) + tag); continue
        w = chain[0].GetWidth(); net_obj = chain[0].GetNet()
        wmm = tomm(w); cids = {id(u) for u in chain}
        slack_old = margins(b, pts, wmm, net, layer, cids); slack_new = margins(b, newpts, wmm, net, layer, cids)
        if slack_new < min(0.0, slack_old) - 0.0025 or (slack_new < -0.0025 and slack_new < slack_old - 0.0025):
            report.append(("skip: would tighten a clearance (slack %.3f -> %.3f)" % (slack_old, slack_new),) + tag); continue
        for u in chain: b.Remove(u); grave.append(u)
        for q0, q1 in zip(newpts, newpts[1:]):
            if math.hypot(q1[0] - q0[0], q1[1] - q0[1]) < 1e-6: continue
            nt = pcbnew.PCB_TRACK(b); nt.SetLayer(layer); nt.SetWidth(w); nt.SetNet(net_obj)
            nt.SetStart(pcbnew.VECTOR2I(mm(q0[0]), mm(q0[1]))); nt.SetEnd(pcbnew.VECTOR2I(mm(q1[0]), mm(q1[1]))); b.Add(nt)
        report.append(("rebuilt %d -> %d pieces, corners moved max %.3f" % (len(chain), len(newpts) - 1, moved),) + tag)
    return report, grave
