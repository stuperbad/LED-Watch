"""exitchk.py BOARD : two-pad parts (R, C, small LEDs, inductors, diodes): does the first piece that leaves each pad run along the part axis, away from the other pad (<= 25 degrees)?"""
import pcbnew, sys, math, collections
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
bad = []; n = 0
for f in b.GetFootprints():
    pads = [p for p in f.Pads() if p.GetNumber() not in ("MP",) and p.GetNetname() != "" or p.GetNumber() in ("1", "2")]
    pads = [p for p in f.Pads() if p.GetNumber() in ("1", "2")]
    if len(pads) != 2 or len(list(f.Pads())) > 3: continue
    lay = f.GetLayer()
    for p, q in ((pads[0], pads[1]), (pads[1], pads[0])):
        pc = p.GetPosition(); qc = q.GetPosition()
        ax = (pc.x - qc.x, pc.y - qc.y); L = math.hypot(*ax)
        if L == 0: continue
        ax = (ax[0] / L, ax[1] / L)
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetLayer() != lay or t.GetNetname() != p.GetNetname(): continue
            for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                if (e.x, e.y) == (pc.x, pc.y):
                    d = (o.x - e.x, o.y - e.y); dl = math.hypot(*d)
                    if dl == 0: continue
                    ang = math.degrees(math.acos(max(-1, min(1, (d[0] * ax[0] + d[1] * ax[1]) / dl))))
                    n += 1
                    if ang > 25: bad.append((f.GetReference(), p.GetNumber(), b.GetLayerName(lay), round(ang, 1), (round(mm(e.x), 3), round(mm(e.y), 3)), (round(mm(o.x), 3), round(mm(o.y), 3))))
print("pad exits checked:", n, " more than 25 degrees off the part axis:", len(bad))
for r in sorted(bad): print("  %s.%s %s  %s deg  from %s to %s" % r)
