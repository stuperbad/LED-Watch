"""via_lead_audit.py BOARD [x0,y0,x1,y1] (KiCad python): the first piece of every trace that ends on a via centre: length from the via centre (rule of 2026-11-09: at least via radius + 1.5 trace widths = 0.31 mm, i.e. 0.16 mm of straight trace clear of the via copper).
Prints per layer how many leads are short, the worst ones, and the LED ring stubs separately."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6
win = tuple(map(float, sys.argv[2].split(","))) if len(sys.argv) > 2 else (0, 0, 1e9, 1e9)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]; tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
byend = collections.defaultdict(list)
for t in tracks: byend[(t.GetLayer(), t.GetStart().x, t.GetStart().y)].append(t); byend[(t.GetLayer(), t.GetEnd().x, t.GetEnd().y)].append(t)
tot = short = 0; bad = []; ring = collections.Counter()
for v in vias:
    x, y = v.GetPosition().x / NM, v.GetPosition().y / NM
    if not (win[0] <= x <= win[2] and win[1] <= y <= win[3]): continue
    for L in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        for t in byend.get((L, v.GetPosition().x, v.GetPosition().y), []):
            tot += 1; ln = mm(t.GetLength())
            r = math.hypot(x - 100, y - 100); ringv = (v.GetNetname().startswith("/ROW") and 14 < r < 21)
            if ln < 0.305:
                short += 1; bad.append((round(ln, 2), v.GetNetname(), b.GetLayerName(L), (round(x, 2), round(y, 2))))
                if ringv: ring["short ring-ROW leads"] += 1
            if ringv: ring["ring-ROW leads"] += 1
print("leads on via centres:", tot, " shorter than 0.305 mm:", short); print(dict(ring)); print(sorted(bad)[:25])
