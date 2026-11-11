"""led_ring_exits2.py IN.kicad_pcb OUT.kicad_pcb [S|M|H ...] [--only=REF,REF] (KiCad python): redraw the ROW stubs of the LED rings with the owner's lead rules of 2026-11-09:
  pad end : first piece leaves by an allowed point (side, outer corner at 45 degrees, outer end - never the edge that faces the LED body) and sticks out >= 0.15 mm beyond the pad edge;
  via end : last piece >= 0.30 mm from the via centre (0.15 mm of trace clear of the via copper);   all other legs >= 0.15 mm, directions are 45-degree multiples of the ring frame (radial / tangential)
            or ONE straight piece when the via is almost level with the pad.   NO BACKTRACKING: every leg moves toward the via in both ring axes (no hooks, no up-and-down zig-zags).
Fewest legs first, then shortest.  The via is moved along its own lane (arcs re-cut, up to 0.7 mm, away from the LED) when that saves a bend.  Clearance to foreign pads, vias and tracks is checked for every candidate."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; O = (100.0, 100.0); F = pcbnew.F_Cu; FM = pcbnew.FromMM
xy = lambda v: (v.x / NM, v.y / NM); V = lambda x, y: pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM))); nets = b.GetNetsByName(); uid = lambda t: t.m_Uuid.AsString()
RINGS = {"S": ("LED white 0201", 19.57), "M": ("LED white 0402", 17.44), "H": ("LED white 0603", 14.63)}
args_ = sys.argv[3:]; ONLY = [a.split("=", 1)[1].split(",") for a in args_ if a.startswith("--only=")]; ONLY = set(ONLY[0]) if ONLY else None
want = [a for a in args_ if not a.startswith("--")] or ["S", "M", "H"]
OUTE, VLEAD, MINLEG = 0.15, 0.15, 0.15
DEBUG = [a.split('=', 1)[1].split(',') for a in sys.argv if a.startswith('--debug=')]; DEBUG = DEBUG[0] if DEBUG else None
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F]; vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
leds = [f for f in b.GetFootprints() if f.GetLayer() == F and any(f.GetValue() == RINGS[k][0] and f.GetReference()[0] == k and abs(math.hypot(*(a - c for a, c in zip(xy(f.GetPosition()), O))) - RINGS[k][1]) < 0.1 for k in want) and (ONLY is None or f.GetReference() in ONLY)]
print("LEDs:", len(leds))
viapos = lambda: {(w.GetPosition().x, w.GetPosition().y) for w in vias}
padpos = {(p.GetPosition().x, p.GetPosition().y) for fp in b.GetFootprints() for p in fp.Pads()}
fpads = [(p.GetNetname(), xy(p.GetPosition()), max(mm(p.GetBoundingBox().GetWidth()), mm(p.GetBoundingBox().GetHeight())) / 2) for fp in b.GetFootprints() for p in fp.Pads() if p.GetLayerSet().Contains(F)]
def seg_d(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy; t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def seg_seg(a, c, e, g): return min(seg_d(a, e, g), seg_d(c, e, g), seg_d(e, a, c), seg_d(g, a, c))
kill = {}; newsegs = []; stats = []; skipped = []; bumped = []
allpads = [(p.GetNetname(), xy(p.GetPosition()), max(mm(p.GetBoundingBox().GetWidth()), mm(p.GetBoundingBox().GetHeight())) / 2) for fp in b.GetFootprints() for p in fp.Pads()]          # a via is copper on every layer: check pads of any layer
anytracks = []                                                                                                                                  # straight pieces and sampled arcs of every layer (foreign nets matter for a moved via)
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK": anytracks.append((t.GetNetname(), xy(t.GetStart()), xy(t.GetEnd()), t.GetLayer() == F, uid(t)))
    elif t.GetClass() == "PCB_ARC":
        p1, p2, p3 = xy(t.GetStart()), xy(t.GetMid()), xy(t.GetEnd())
        dd_ = 2 * (p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))
        if abs(dd_) < 1e-9: anytracks.append((t.GetNetname(), p1, p3, False, uid(t))); continue
        ux = ((p1[0] ** 2 + p1[1] ** 2) * (p2[1] - p3[1]) + (p2[0] ** 2 + p2[1] ** 2) * (p3[1] - p1[1]) + (p3[0] ** 2 + p3[1] ** 2) * (p1[1] - p2[1])) / dd_
        uy = ((p1[0] ** 2 + p1[1] ** 2) * (p3[0] - p2[0]) + (p2[0] ** 2 + p2[1] ** 2) * (p1[0] - p3[0]) + (p3[0] ** 2 + p3[1] ** 2) * (p2[0] - p1[0])) / dd_
        rr = math.hypot(p1[0] - ux, p1[1] - uy); a1, a2, a3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (p1, p2, p3))
        def unwrap(a, ref): 
            while a - ref > math.pi: a -= 2 * math.pi
            while a - ref < -math.pi: a += 2 * math.pi
            return a
        a2u = unwrap(a2, a1); a3u = unwrap(a3, a2u); n_ = max(2, int(abs(a3u - a1) / math.radians(1.0)) + 1)
        pts = [(ux + rr * math.cos(a1 + (a3u - a1) * k / n_), uy + rr * math.sin(a1 + (a3u - a1) * k / n_)) for k in range(n_ + 1)]
        for a_, c_ in zip(pts, pts[1:]): anytracks.append((t.GetNetname(), a_, c_, False, uid(t)))
WHY = []
def clear_ok(net, world, ownpad, ownvia):
    for a, c in zip(world, world[1:]):
        for w in vias:
            if w.GetNetname() != net and seg_d(xy(w.GetPosition()), a, c) < 0.335: WHY.append("via " + w.GetNetname() + " %.2f,%.2f" % xy(w.GetPosition())); return False
        for n, p, r in fpads:
            if n != net and math.hypot(p[0] - ownpad[0], p[1] - ownpad[1]) > 1e-6 and seg_d(p, a, c) < r + 0.16: WHY.append("pad " + n + " %.2f,%.2f" % p); return False
        for t in tracks:
            if t.GetNetname() != net and uid(t) not in kill and seg_seg(a, c, xy(t.GetStart()), xy(t.GetEnd())) < 0.21: WHY.append("track " + t.GetNetname() + " %.2f,%.2f" % xy(t.GetStart())); return False
        for n, q in newsegs:
            if n != net and seg_seg(a, c, q[0], q[1]) < 0.21: WHY.append("new " + n); return False
    return True
WHYV = []
def via_site_ok(net, pos, selfv):
    for w in vias:
        if w is not selfv and w.GetNetname() != net and math.hypot(pos[0] - xy(w.GetPosition())[0], pos[1] - xy(w.GetPosition())[1]) < 0.5: WHYV.append("via " + w.GetNetname()); return False
    for n, p, r in allpads:
        if n != net and math.hypot(p[0] - pos[0], p[1] - pos[1]) < r + 0.1 + 0.15 + 0.03: WHYV.append("pad " + n + " %.2f,%.2f" % p); return False
    for n, a_, c_, onF, i_ in anytracks:
        if n != net and i_ not in kill and seg_d(pos, a_, c_) < 0.33: WHYV.append("track " + n + " %.2f,%.2f-%.2f,%.2f" % (a_ + c_)); return False
    for n, q in newsegs:
        if n != net and seg_d(pos, q[0], q[1]) < 0.33: return False
    return True
def nudge(via, delta_mm, sign):
    p0 = (via.GetPosition().x, via.GetPosition().y); r = math.hypot(p0[0] / NM - O[0], p0[1] / NM - O[1]); a0 = math.atan2(p0[1] / NM - O[1], p0[0] / NM - O[0]); dth = sign * delta_mm / r
    new = V(O[0] + r * math.cos(a0 + dth), O[1] + r * math.sin(a0 + dth)); same = lambda p: abs(p.x - p0[0]) < 3000 and abs(p.y - p0[1]) < 3000
    ang = lambda p: math.atan2(p.y / NM - O[1], p.x / NM - O[0]); at = lambda m: V(O[0] + r * math.cos(m), O[1] + r * math.sin(m))
    for t in b.GetTracks():
        if t.GetNetname() != via.GetNetname() or t.GetClass() == "PCB_VIA": continue
        if t.GetClass() == "PCB_ARC":
            if same(t.GetStart()): t.SetStart(new); t.SetMid(at((ang(new) + ang(t.GetEnd())) / 2))
            elif same(t.GetEnd()): t.SetEnd(new); t.SetMid(at((ang(new) + ang(t.GetStart())) / 2))
        elif t.GetClass() == "PCB_TRACK":
            if same(t.GetStart()): t.SetStart(new)
            if same(t.GetEnd()): t.SetEnd(new)
    via.SetPosition(new)
def plan(Du, Dv, hu, hv):
    """routes from the pad centre (0,0) to (Du,Dv) in the (u, v) frame (v away from the LED body, Du >= 0) that never move away from the via: list of (legs, length, name, pts), fewest legs then shortest"""
    out = []; L = math.hypot(Du, Dv); s_ = 1 if Dv >= 0 else -1; c = math.sqrt(.5)
    allowed = [(1.0, 0.0), (c, s_ * c)] + ([(0.0, float(s_))] if abs(Dv) > 1e-6 else [])
    if Du > 0 and abs(Dv) <= 0.052 * Du and L - hu >= OUTE and L >= VLEAD: out.append((1, L, "straight", [(0.0, 0.0), (Du, Dv)]))      # nearly tangential: one piece
    exits = [("side", (1.0, 0.0), hu)]
    if Dv > 0: exits += [("corner", (c, c), hu * math.sqrt(2)), ("end", (0.0, 1.0), hv)]                                                  # outward exits only when the via lies further out
    for name, d, edge in exits:
        fits = [Du - abs(Dv)] if name == "side" and Du - abs(Dv) >= edge + OUTE else []                                                      # exact fit: one 45 into the via
        for L1 in [edge + OUTE + 0.05 * k for k in range(0, 24)] + fits:
            Q = (d[0] * L1, d[1] * L1); rem = (Du - Q[0], Dv - Q[1])
            if rem[0] < -1e-6 or rem[1] * s_ < -1e-6: continue                                                                                 # no backtracking
            if math.hypot(*rem) < 1e-6: continue
            for dd in allowed:                                                                                                                 # one more leg straight into the via
                l2 = rem[0] * dd[0] + rem[1] * dd[1]
                if l2 >= VLEAD and abs(rem[0] * dd[1] - rem[1] * dd[0]) < 1e-3: out.append((2, L1 + l2, name, [(0.0, 0.0), Q, (Du, Dv)]))
            for d2 in allowed:                                                                                                                 # two more legs
                for d3 in allowed:
                    det = d2[0] * d3[1] - d2[1] * d3[0]
                    if abs(det) < 1e-6: continue
                    l2 = (rem[0] * d3[1] - rem[1] * d3[0]) / det; l3 = (d2[0] * rem[1] - d2[1] * rem[0]) / det
                    if l2 >= MINLEG and l3 >= VLEAD: out.append((3, L1 + l2 + l3, name, [(0.0, 0.0), Q, (Q[0] + d2[0] * l2, Q[1] + d2[1] * l2), (Du, Dv)]))
    def pen(pts):
        p = 0.0
        for a_, b_, c_ in zip(pts, pts[1:], pts[2:]):
            v1 = (b_[0] - a_[0], b_[1] - a_[1]); v2 = (c_[0] - b_[0], c_[1] - b_[1]); n1, n2 = math.hypot(*v1), math.hypot(*v2)
            if n1 > 1e-9 and n2 > 1e-9 and abs(v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) < 0.1: p += 0.3          # a 90-degree turn costs like 0.3 mm more
        return p
    out = [(l_ + 1.0 * round(pen(pt_) / 0.3), ln_ + pen(pt_), nm_, pt_) for l_, ln_, nm_, pt_ in out]          # a 90-degree turn counts like one more leg: 45s beat an L
    out.sort(key=lambda x: (x[0], x[1])); return out
for f in leds:
    ref = f.GetReference(); pad = [p for p in f.Pads() if p.GetNumber() == "1"][0]; net = pad.GetNetname(); P = pad.GetPosition(); Pxy = xy(P)
    cx, cy = xy(f.GetPosition()); th = math.atan2(cy - O[1], cx - O[0]); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    hu, hv = mm(pad.GetSizeY()) / 2, mm(pad.GetSizeX()) / 2
    pr = (Pxy[0] - cx) * v[0] + (Pxy[1] - cy) * v[1]; wsg = 1 if pr > 0 else -1; v = (v[0] * wsg, v[1] * wsg)
    chain = []; frontier = [(P.x, P.y)]; seen = set(); ids = set(); vp = viapos()
    while frontier:
        k = frontier.pop()
        if k in seen: continue
        seen.add(k)
        if k != (P.x, P.y) and (k in vp or k in padpos): continue
        for t in tracks:
            if t.GetNetname() == net and uid(t) not in ids and uid(t) not in kill and ((t.GetStart().x, t.GetStart().y) == k or (t.GetEnd().x, t.GetEnd().y) == k):
                chain.append(t); ids.add(uid(t)); frontier += [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
    if not chain: continue
    ends = {(t.GetStart().x, t.GetStart().y) for t in chain} | {(t.GetEnd().x, t.GetEnd().y) for t in chain}
    Rr = RINGS[ref[0]][1]
    def ok(w):
        wx, wy = xy(w.GetPosition()); r_ = math.hypot(wx - O[0], wy - O[1]); dth = abs((math.degrees(math.atan2(wy - O[1], wx - O[0])) - math.degrees(th) + 180) % 360 - 180)
        return abs(r_ - Rr) <= 1.1 and dth < 4.2 and math.hypot(wx - Pxy[0], wy - Pxy[1]) < 1.7
    near_end = lambda w: any(abs(w.GetPosition().x - k[0]) < 0.06 * NM and abs(w.GetPosition().y - k[1]) < 0.06 * NM for k in ends)
    cand = sorted([w for w in vias if w.GetNetname() == net and near_end(w) and ok(w)], key=lambda w: math.hypot(xy(w.GetPosition())[0] - Pxy[0], xy(w.GetPosition())[1] - Pxy[1]))
    if not cand: skipped.append((ref, "no usable via")); continue
    via = cand[0]
    extra = [k for k in ends if k != (P.x, P.y) and not (abs(k[0] - via.GetPosition().x) < 0.06 * NM and abs(k[1] - via.GetPosition().y) < 0.06 * NM) and (k in vp or k in padpos)]
    if extra: skipped.append((ref, "branch to another via / pad")); continue
    kill.update({uid(t): t for t in chain})                                  # their copper no longer counts as an obstacle
    Vxy0 = xy(via.GetPosition()); d = (Vxy0[0] - Pxy[0], Vxy0[1] - Pxy[1]); Du, Dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]; sg = 1 if Du >= 0 else -1
    r0 = math.hypot(Vxy0[0] - O[0], Vxy0[1] - O[1]); a0 = math.atan2(Vxy0[1] - O[1], Vxy0[0] - O[0]); tang = (-math.sin(a0), math.cos(a0)); away = 1 if (tang[0] * u[0] + tang[1] * u[1]) * sg > 0 else -1
    best = None; WHY.clear()
    for bump in [0.0] + [0.05 * i for i in range(1, 21)]:
        if bump > 0:
            a1 = a0 + away * bump / r0; Vn = (O[0] + r0 * math.cos(a1), O[1] + r0 * math.sin(a1))
            if not via_site_ok(net, Vn, via):
                if DEBUG and ref in DEBUG: print(ref, 'bump %.2f' % bump, 'via site blocked', WHYV[-1:])
                continue
        else: Vn = Vxy0
        dd = (Vn[0] - Pxy[0], Vn[1] - Pxy[1]); Du2, Dv2 = abs(dd[0] * u[0] + dd[1] * u[1]), dd[0] * v[0] + dd[1] * v[1]
        if DEBUG and ref in DEBUG: print(ref, 'bump %.2f' % bump, 'Du %.3f Dv %.3f' % (Du2, Dv2), 'plans', len(plan(Du2, Dv2, hu, hv)))
        for legs, length, name, pts in plan(Du2, Dv2, hu, hv):
            world = [(Pxy[0] + sg * p[0] * u[0] + p[1] * v[0], Pxy[1] + sg * p[0] * u[1] + p[1] * v[1]) for p in pts]; world[0] = Pxy; world[-1] = Vn
            if clear_ok(net, world, Pxy, via):
                key = (legs, length + 1.0 * bump)
                if best is None or key < best[0]: best = (key, legs, length, name, world, bump)
                break
        if best is not None and best[1] == 1: break
    done = best is not None
    if done: _, legs, length, name, world, bump = best
    if not done:
        for t in chain: kill.pop(uid(t), None)
        skipped.append((ref, "no route even with the via bumped 0.7 mm: " + "; ".join(sorted(set(WHY))[:4]))); WHY.clear(); continue
    stats.append((ref, name, length, sum(mm(t.GetLength()) for t in chain), bump, ref[0]))
    if bump > 0:
        nudge(via, bump, away); bumped.append((ref, bump)); world[-1] = xy(via.GetPosition())       # the lane arcs and every track end on the via follow
    pieces = [P] + [V(*q) for q in world[1:-1]] + [via.GetPosition()]
    newsegs += [(net, (a_, c_)) for a_, c_ in zip(world, world[1:])]
    for q0, q1 in zip(pieces, pieces[1:]):
        if q0.x == q1.x and q0.y == q1.y: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets[net]); b.Add(t)
for k in "SMH":
    ss = [x for x in stats if x[5] == k]
    if ss: print(k, "ring:", dict(collections.Counter(x[1] for x in ss)), "new mean %.2f mm, old mean %.2f mm, %d LEDs, vias bumped %d (mean %.2f mm)" % (sum(x[2] for x in ss) / len(ss), sum(x[3] for x in ss) / len(ss), len(ss), sum(1 for x in ss if x[4] > 0), (sum(x[4] for x in ss if x[4] > 0) / max(1, sum(1 for x in ss if x[4] > 0)))))
print("left as they were:", skipped)
for t in kill.values(): b.Remove(t)
pcbnew.SaveBoard(sys.argv[2], b); print("written")
