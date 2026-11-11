"""led_s_exits.py IN.kicad_pcb OUT.kicad_pcb (KiCad python): redraw the ROW stubs of the seconds LEDs after the owner's pad-exit rule of 2026-11-09:
the pad has 8 attachment points (4 corners, 4 edge middles); the three on the edge that faces the LED body are not allowed (so the outer pad of a turned seconds LED leaves by its outer end, its two outer corners or its two sides);
the first piece out of the pad sticks out at least 1.5 trace widths (0.16 mm) beyond the pad edge, then 45-degree snapped legs (45 degrees to the radial / tangential direction of the ring) to the via.
Of the allowed exits (side, outer corner at 45 degrees, outer end) the shortest route wins.  The COL stub (radial, from the inner end of the inner pad) is left as it is."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; O = (100.0, 100.0); F = pcbnew.F_Cu; FM = pcbnew.FromMM
xy = lambda v: (v.x / NM, v.y / NM); V = lambda x, y: pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM))); nets = b.GetNetsByName(); uid = lambda t: t.m_Uuid.AsString()
OUT = 0.16
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F]; vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
leds = [f for f in b.GetFootprints() if f.GetLayer() == F and f.GetValue() == "LED white 0201" and abs(math.hypot(*(a - c for a, c in zip(xy(f.GetPosition()), O))) - 19.57) < 0.1]
kill = {}; add = []; stats = []
for f in leds:
    pad = [p for p in f.Pads() if p.GetNumber() == "1"][0]; net = pad.GetNetname(); P = pad.GetPosition(); Pxy = xy(P)
    cx, cy = xy(f.GetPosition()); th = math.atan2(cy - O[1], cx - O[0]); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    hu, hv = mm(pad.GetSizeY()) / 2, mm(pad.GetSizeX()) / 2
    chain = []; frontier = [(P.x, P.y)]; seen = set(); ids = set()
    while frontier:
        k = frontier.pop()
        if k in seen: continue
        seen.add(k)
        for t in tracks:
            if t.GetNetname() == net and uid(t) not in ids and ((t.GetStart().x, t.GetStart().y) == k or (t.GetEnd().x, t.GetEnd().y) == k):
                chain.append(t); ids.add(uid(t)); frontier += [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
    ends = {(t.GetStart().x, t.GetStart().y) for t in chain} | {(t.GetEnd().x, t.GetEnd().y) for t in chain}
    via = [w for w in vias if w.GetNetname() == net and (w.GetPosition().x, w.GetPosition().y) in ends]
    if not via: print("no via for", f.GetReference()); continue
    via = via[0]; Vxy = xy(via.GetPosition()); d = (Vxy[0] - Pxy[0], Vxy[1] - Pxy[1]); Du, Dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]
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
        if best is None or length < best[0] - 1e-6: best = (length, name, pts)
    length, name, pts = best
    world = [Pxy if i == 0 else (Pxy[0] + sg * p[0] * u[0] + p[1] * v[0], Pxy[1] + sg * p[0] * u[1] + p[1] * v[1]) for i, p in enumerate(pts)]
    # the last point is the via centre exactly, the first the pad centre exactly
    pieces = [P] + [V(*q) for q in world[1:-1]] + [via.GetPosition()]
    for t in chain: kill[uid(t)] = t
    add.append((net, pieces)); stats.append((f.GetReference(), name, length, sum(mm(t.GetLength()) for t in chain)))
import collections
print("exits chosen:", dict(collections.Counter(s[1] for s in stats)), " new mean %.2f mm  old mean %.2f mm" % (sum(s[2] for s in stats) / len(stats), sum(s[3] for s in stats) / len(stats)))
for t in kill.values(): b.Remove(t)
for net, pcs in add:
    for q0, q1 in zip(pcs, pcs[1:]):
        if q0.x == q1.x and q0.y == q1.y: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets[net]); b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b); print("written")
