"""led_ring_exits.py IN.kicad_pcb OUT.kicad_pcb [S|M|H ...] (KiCad python; default S M H): redraw the ROW stubs of the seconds (turned, ROW pad outside) / minute / hour (ROW pad inside) LEDs after the owner's pad-exit rule of 2026-11-09:
the pad has 8 attachment points (4 corners, 4 edge middles); the three on the edge that faces the LED body are not allowed (so the outer pad of a turned seconds LED leaves by its outer end, its two outer corners or its two sides);
the first piece out of the pad sticks out at least 1.5 trace widths (0.16 mm) beyond the pad edge, then 45-degree snapped legs (45 degrees to the radial / tangential direction of the ring) to the via.
Of the allowed exits (side, outer corner at 45 degrees, outer end) the shortest route wins.  The COL stub (radial, from the inner end of the inner pad) is left as it is."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; O = (100.0, 100.0); F = pcbnew.F_Cu; FM = pcbnew.FromMM
xy = lambda v: (v.x / NM, v.y / NM); V = lambda x, y: pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM))); nets = b.GetNetsByName(); uid = lambda t: t.m_Uuid.AsString()
OUT = 0.16
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F]; vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
RINGS = {"S": ("LED white 0201", 19.57), "M": ("LED white 0402", 17.44), "H": ("LED white 0603", 14.63)}
args_ = [a for a in sys.argv[3:]]
PADN = "2" if "--col" in args_ else "1"                       # --col: redraw the COL stubs (pad 2) instead of the ROW stubs
only_short = "--short" in args_                            # with --col: only stubs whose first piece is shorter than 0.15 mm beyond the pad
ONLY = [a.split("=", 1)[1].split(",") for a in args_ if a.startswith("--only=")]; ONLY = set(ONLY[0]) if ONLY else None      # --only=M59,M4,...: just these LEDs
WIDE = "--wide" in args_                                    # accept a via up to 1.6 mm from the pad and 4 degrees away (sector-end minute LEDs)
want = [a for a in args_ if not a.startswith("--")] or ["S", "M", "H"]
leds = [f for f in b.GetFootprints() if f.GetLayer() == F and any(f.GetValue() == RINGS[k][0] and f.GetReference()[0] == k and abs(math.hypot(*(a - c for a, c in zip(xy(f.GetPosition()), O))) - RINGS[k][1]) < 0.1 for k in want) and (ONLY is None or f.GetReference() in ONLY)]
print("LEDs:", len(leds))
viapos = {(w.GetPosition().x, w.GetPosition().y) for w in vias}
padpos = {(p.GetPosition().x, p.GetPosition().y) for fp in b.GetFootprints() for p in fp.Pads()}
kill = {}; add = []; stats = []; skipped = []
foreign_pads = [(p.GetNetname(), xy(p.GetPosition()), max(mm(p.GetSizeX()), mm(p.GetSizeY())) / 2 * 1.0) for fp in b.GetFootprints() for p in fp.Pads() if p.GetLayerSet().Contains(F)]
foreign_vias = [(w.GetNetname(), xy(w.GetPosition())) for w in vias]
def seg_d(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy; t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def seg_seg(a, c, e, g):
    return min(seg_d(a, e, g), seg_d(c, e, g), seg_d(e, a, c), seg_d(g, a, c))
def clear_ok(net, world, ownpad, mine):
    for a, c in zip(world, world[1:]):
        for n, p in foreign_vias:
            if n != net and seg_d(p, a, c) < 0.335: return False
        for n, p, r in foreign_pads:
            if n != net and math.hypot(p[0] - ownpad[0], p[1] - ownpad[1]) > 1e-6 and seg_d(p, a, c) < r + 0.16: return False
        for t in tracks:
            if t.GetNetname() != net and uid(t) not in kill and seg_seg(a, c, xy(t.GetStart()), xy(t.GetEnd())) < 0.21: return False
        for n, q in newsegs:
            if n != net and seg_seg(a, c, q[0], q[1]) < 0.21: return False
    return True
newsegs = []
for f in leds:
    pad = [p for p in f.Pads() if p.GetNumber() == PADN][0]; net = pad.GetNetname(); P = pad.GetPosition(); Pxy = xy(P)
    cx, cy = xy(f.GetPosition()); th = math.atan2(cy - O[1], cx - O[0]); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    hu, hv = mm(pad.GetSizeY()) / 2, mm(pad.GetSizeX()) / 2
    pr = (Pxy[0] - cx) * v[0] + (Pxy[1] - cy) * v[1]; wsg = 1 if pr > 0 else -1; v = (v[0] * wsg, v[1] * wsg)          # v now points away from the LED body
    chain = []; frontier = [(P.x, P.y)]; seen = set(); ids = set()
    while frontier:
        k = frontier.pop()
        if k in seen: continue
        seen.add(k)
        if k != (P.x, P.y) and (k in viapos or k in padpos): continue
        for t in tracks:
            if t.GetNetname() == net and uid(t) not in ids and ((t.GetStart().x, t.GetStart().y) == k or (t.GetEnd().x, t.GetEnd().y) == k):
                chain.append(t); ids.add(uid(t)); frontier += [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
    ends = {(t.GetStart().x, t.GetStart().y) for t in chain} | {(t.GetEnd().x, t.GetEnd().y) for t in chain}
    Rr = RINGS[f.GetReference()[0]][1]
    if PADN == "1":
        def ok(w):
            wx, wy = xy(w.GetPosition()); r_ = math.hypot(wx - O[0], wy - O[1]); dth = abs((math.degrees(math.atan2(wy - O[1], wx - O[0])) - math.degrees(th) + 180) % 360 - 180)
            return abs(r_ - Rr) <= 1.1 and dth < (4.0 if WIDE else 3.2) and math.hypot(wx - Pxy[0], wy - Pxy[1]) < (1.6 if WIDE else 1.3)
        near_end = lambda w: any(abs(w.GetPosition().x - k[0]) < 0.06 * NM and abs(w.GetPosition().y - k[1]) < 0.06 * NM for k in ends)
        via = sorted([w for w in vias if w.GetNetname() == net and near_end(w) and ok(w)], key=lambda w: math.hypot(xy(w.GetPosition())[0] - Pxy[0], xy(w.GetPosition())[1] - Pxy[1]))
        if not via: print("no usable via next to", f.GetReference(), "- stub left as it is"); skipped.append(f.GetReference()); continue
        via = via[0]; Vxy = xy(via.GetPosition()); tgt_nm = via.GetPosition()
        extra = [k for k in ends if k != (P.x, P.y) and not (abs(k[0] - via.GetPosition().x) < 0.06 * NM and abs(k[1] - via.GetPosition().y) < 0.06 * NM) and (k in viapos or k in padpos)]
        if extra: print("branch to another via / pad at", [(round(k[0] / NM, 2), round(k[1] / NM, 2)) for k in extra], "next to", f.GetReference(), "- stub left as it is"); skipped.append(f.GetReference()); continue
    else:
        cnt = collections.Counter()
        for t in chain: cnt[(t.GetStart().x, t.GetStart().y)] += 1; cnt[(t.GetEnd().x, t.GetEnd().y)] += 1
        leaves = [k for k, c in cnt.items() if c == 1 and k != (P.x, P.y)]
        if len(leaves) != 1 or not chain: print("COL stub of", f.GetReference(), "has", len(leaves), "far ends - left as it is"); skipped.append(f.GetReference()); continue
        if only_short:
            t0 = [t for t in chain if (t.GetStart().x, t.GetStart().y) == (P.x, P.y) or (t.GetEnd().x, t.GetEnd().y) == (P.x, P.y)][0]; e0 = t0.GetEnd() if (t0.GetStart().x, t0.GetStart().y) == (P.x, P.y) else t0.GetStart()
            d0 = (e0.x / NM - Pxy[0], e0.y / NM - Pxy[1]); L0 = math.hypot(*d0); du0, dv0 = d0[0] * u[0] + d0[1] * u[1], d0[0] * v[0] + d0[1] * v[1]
            tt = min(hu / abs(du0) if abs(du0) > 1e-9 else 1e9, hv / abs(dv0) if abs(dv0) > 1e-9 else 1e9) * L0
            if L0 - tt >= 0.145: continue
        class _T: pass
        tgt_nm = pcbnew.VECTOR2I(leaves[0][0], leaves[0][1]); Vxy = xy(tgt_nm)
    d = (Vxy[0] - Pxy[0], Vxy[1] - Pxy[1]); Du, Dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]
    sg = 1 if Du >= 0 else -1; Du = abs(Du)
    best = None
    for name, dirv, edge in (("side", (1.0, 0.0), hu), ("corner", (math.sqrt(.5), math.sqrt(.5)), hu * math.sqrt(2)), ("end", (0.0, 1.0), hv)):
        L1 = edge + OUT; Q = (dirv[0] * L1, dirv[1] * L1); ru, rv = Du - Q[0], Dv - Q[1]
        if ru < -1e-6: continue
        a_ = abs(rv); s_ = 1 if rv >= 0 else -1
        pts = [(0.0, 0.0), Q]
        if a_ <= ru + 1e-9:
            if ru - a_ > 0.02: pts.append((Q[0] + ru - a_, Q[1]))
        else:
            pts.append((Q[0] + ru, Q[1] + s_ * ru))
        pts.append((Du, Dv))
        length = sum(math.hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(pts, pts[1:]))
        w_ = [Pxy if i == 0 else (Pxy[0] + sg * p[0] * u[0] + p[1] * v[0], Pxy[1] + sg * p[0] * u[1] + p[1] * v[1]) for i, p in enumerate(pts)]
        if not clear_ok(net, w_, Pxy, None): continue
        if best is None or length < best[0] - 1e-6: best = (length, name, pts)
    if best is None: print("no clear route for", f.GetReference(), "- stub left as it is"); skipped.append(f.GetReference()); continue
    length, name, pts = best
    world = [Pxy if i == 0 else (Pxy[0] + sg * p[0] * u[0] + p[1] * v[0], Pxy[1] + sg * p[0] * u[1] + p[1] * v[1]) for i, p in enumerate(pts)]
    # the last point is the via centre exactly, the first the pad centre exactly
    pieces = [P] + [V(*q) for q in world[1:-1]] + [tgt_nm]
    for t in chain: kill[uid(t)] = t
    newsegs += [(net, (a_, c_)) for a_, c_ in zip(world, world[1:])]
    add.append((net, pieces)); stats.append((f.GetReference(), name, length, sum(mm(t.GetLength()) for t in chain), f.GetReference()[0]))
import collections
for k in want:
    ss = [x for x in stats if x[4] == k]
    if ss: print(k, "ring: exits", dict(collections.Counter(x[1] for x in ss)), " new mean %.2f mm  old mean %.2f mm  (%d LEDs)" % (sum(x[2] for x in ss) / len(ss), sum(x[3] for x in ss) / len(ss), len(ss)))
for t in kill.values(): b.Remove(t)
for net, pcs in add:
    for q0, q1 in zip(pcs, pcs[1:]):
        if q0.x == q1.x and q0.y == q1.y: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets[net]); b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b); print("written")
