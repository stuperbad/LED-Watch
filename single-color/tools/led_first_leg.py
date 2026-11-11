"""led_first_leg.py IN.kicad_pcb OUT.kicad_pcb [M H S] (KiCad python): give every LED pad whose first track piece sticks out less than 0.15 mm beyond the pad edge (owner's rule 2026-11-09: 1.5 trace widths) a longer first piece.
The first corner moves along the pad exit direction to the nearest point (>= edge + 0.16 mm) from which the old second piece's far end is reached at a multiple of 45 degrees in the ring frame (radial / tangential);
the two pieces are replaced, everything after them stays.  Skipped when the corner joins more than two pieces, or when the new corner would come closer than 0.21 mm to foreign copper."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; O = (100.0, 100.0); F = pcbnew.F_Cu; FM = pcbnew.FromMM
xy = lambda v: (v.x / NM, v.y / NM); uid = lambda t: t.m_Uuid.AsString(); nets = b.GetNetsByName()
RINGS = {"S": "LED white 0201", "M": "LED white 0402", "H": "LED white 0603"}
want = sys.argv[3:] or ["M", "H", "S"]
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F]; vias = [(w.GetNetname(), xy(w.GetPosition())) for w in b.GetTracks() if w.GetClass() == "PCB_VIA"]
pads = [(p.GetNetname(), xy(p.GetPosition()), max(mm(p.GetSizeX()), mm(p.GetSizeY())) / 2) for fp in b.GetFootprints() for p in fp.Pads() if p.GetLayerSet().Contains(F)]
def seg_d(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L2 = dx * dx + dy * dy; t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def seg_seg(a, c, e, g): return min(seg_d(a, e, g), seg_d(c, e, g), seg_d(e, a, c), seg_d(g, a, c))
done = 0; skipped = []; replace = []
for f in b.GetFootprints():
    r = f.GetReference()
    if f.GetLayer() != F or r[0] not in want or not r[1:].isdigit() or f.GetValue() != RINGS[r[0]]: continue
    cx, cy = xy(f.GetPosition()); th = math.atan2(cy - O[1], cx - O[0]); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    for p in f.Pads():
        if not p.GetNumber(): continue
        P = p.GetPosition(); Pxy = xy(P); hu, hv = mm(p.GetSizeY()) / 2, mm(p.GetSizeX()) / 2
        first = [t for t in tracks if t.GetNetname() == p.GetNetname() and ((t.GetStart().x, t.GetStart().y) == (P.x, P.y) or (t.GetEnd().x, t.GetEnd().y) == (P.x, P.y))]
        if len(first) != 1: continue
        t0 = first[0]; A = t0.GetEnd() if (t0.GetStart().x, t0.GetStart().y) == (P.x, P.y) else t0.GetStart(); Axy = xy(A)
        d = (Axy[0] - Pxy[0], Axy[1] - Pxy[1]); L0 = math.hypot(*d)
        if L0 < 1e-6: continue
        d = (d[0] / L0, d[1] / L0); du, dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]
        tt = min(hu / abs(du) if abs(du) > 1e-9 else 1e9, hv / abs(dv) if abs(dv) > 1e-9 else 1e9)
        if L0 - tt >= 0.145: continue
        at_A = [t for t in tracks if t is not t0 and t.GetNetname() == p.GetNetname() and uid(t) != uid(t0) and ((t.GetStart().x, t.GetStart().y) == (A.x, A.y) or (t.GetEnd().x, t.GetEnd().y) == (A.x, A.y))]
        if len(at_A) != 1: skipped.append((r, p.GetNumber(), "corner has %d other pieces" % len(at_A))); continue
        t1 = at_A[0]; B = t1.GetEnd() if (t1.GetStart().x, t1.GetStart().y) == (A.x, A.y) else t1.GetStart(); Bxy = xy(B)
        best = None; L = tt + 0.16
        while L < L0 + 1.2:
            Ap = (Pxy[0] + d[0] * L, Pxy[1] + d[1] * L); e = (Bxy[0] - Ap[0], Bxy[1] - Ap[1]); le = math.hypot(*e)
            if le > 0.12:
                ang = math.degrees(math.atan2(e[0] * v[0] + e[1] * v[1], e[0] * u[0] + e[1] * u[1])) % 45; off = min(ang, 45 - ang)
                if off < 0.6:
                    ok = True
                    for a_, c_ in ((Pxy, Ap), (Ap, Bxy)):
                        for n, q in vias:
                            if n != p.GetNetname() and seg_d(q, a_, c_) < 0.335: ok = False
                        for n, q, rr in pads:
                            if n != p.GetNetname() and math.hypot(q[0] - Pxy[0], q[1] - Pxy[1]) > 1e-6 and seg_d(q, a_, c_) < rr + 0.16: ok = False
                        for t in tracks:
                            if t.GetNetname() != p.GetNetname() and seg_seg(a_, c_, xy(t.GetStart()), xy(t.GetEnd())) < 0.21: ok = False
                    if ok: best = Ap; break
            L += 0.005
        if best is None: skipped.append((r, p.GetNumber(), "no 45-degree solution / clearance")); continue
        replace.append((t0, t1, p.GetNetname(), P, best, B)); done += 1
for t0, t1, net, P, Ap, B in replace:
    b.Remove(t0); b.Remove(t1); Apn = pcbnew.VECTOR2I(int(round(Ap[0] * NM)), int(round(Ap[1] * NM)))
    for q0, q1 in ((P, Apn), (Apn, B)):
        t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets[net]); b.Add(t)
print("first pieces lengthened:", done, " skipped:", len(skipped)); print(skipped[:40])
pcbnew.SaveBoard(sys.argv[2], b)
