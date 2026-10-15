"""Replace every track arc by short straight segments (what grid_dump.py / grid_route2.py can read).   usage (KiCad python): arcs_to_segments.py in.kicad_pcb out.kicad_pcb"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
# ---- the poly twin: every arc becomes short straight segments
arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC"]
for a in arcs:
    s, m, e = a.GetStart(), a.GetMid(), a.GetEnd()
    ax, ay, bx, by, cx2, cy2 = (tomm(v) for v in (s.x, s.y, m.x, m.y, e.x, e.y))
    d = 2 * (ax * (by - cy2) + bx * (cy2 - ay) + cx2 * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy2) + (bx * bx + by * by) * (cy2 - ay) + (cx2 * cx2 + cy2 * cy2) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx2 - bx) + (bx * bx + by * by) * (ax - cx2) + (cx2 * cx2 + cy2 * cy2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = math.atan2(ay - uy, ax - ux), math.atan2(by - uy, bx - ux), math.atan2(cy2 - uy, cx2 - ux)
    # sweep direction from start through mid to end
    def norm(x):
        while x < 0:
            x += 2 * math.pi
        while x >= 2 * math.pi:
            x -= 2 * math.pi
        return x
    ccw = norm(am - a0) < norm(a1 - a0)
    sweep = norm(a1 - a0) if ccw else -norm(a0 - a1)
    n = max(2, int(abs(sweep) / math.radians(1.5)))
    pts = [(ux + r * math.cos(a0 + sweep * i / n), uy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]
    pts[0], pts[-1] = (ax, ay), (cx2, cy2)
    for i in range(n):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(pts[i + 1][0]), mm(pts[i + 1][1])))
        t.SetWidth(a.GetWidth())
        t.SetLayer(a.GetLayer())
        t.SetNet(a.GetNet())
        b.Add(t)
    b.Remove(a)
pcbnew.SaveBoard(sys.argv[2], b)
print("wrote", sys.argv[2], "(%d arcs converted)" % len(arcs))
