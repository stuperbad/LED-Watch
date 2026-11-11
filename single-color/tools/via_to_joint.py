"""via_to_joint.py IN OUT [--fix] (KiCad python): ring-lane vias whose In2 arcs end 0.003 - 0.6 mm away from the via centre (the via is not on the arc joint).  Lists them; with --fix the via (and every F.Cu / B.Cu track end on it) moves onto the joint."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); NM = 1e6; mm = pcbnew.ToMM; fix = "--fix" in sys.argv
arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC"]; vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]; tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
moved = []
for v in vias:
    n = v.GetNetname()
    if not (n.startswith("/ROW") or n.startswith("/COL")): continue
    ends = [p for a in arcs if a.GetNetname() == n for p in (a.GetStart(), a.GetEnd())]
    if not ends: continue
    vx, vy = v.GetPosition().x, v.GetPosition().y
    best = min(ends, key=lambda p: math.hypot(p.x - vx, p.y - vy)); d = math.hypot(best.x - vx, best.y - vy) / NM
    if 0.003 < d < 0.6: moved.append((n, round(mm(vx), 3), round(mm(vy), 3), round(d, 3), best, v))
print("ring vias off their arc joint:", len(moved)); print([(m[0], m[1], m[2], m[3]) for m in moved][:30])
if fix:
    for n, x, y, d, J, v in moved:
        p0 = v.GetPosition(); same = lambda p: abs(p.x - p0.x) < 3000 and abs(p.y - p0.y) < 3000
        for t in tr:
            if t.GetNetname() != n: continue
            if same(t.GetStart()): t.SetStart(J)
            if same(t.GetEnd()): t.SetEnd(J)
        v.SetPosition(J)
    pcbnew.SaveBoard(sys.argv[2], b); print("moved", len(moved))
