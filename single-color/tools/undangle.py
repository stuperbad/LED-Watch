"""Replace dangling dogbone vias (a via the router only used as a junction on F.Cu) by a short F.Cu segment to the next track end.
usage (KiCad python): undangle.py in.kicad_pcb out.kicad_pcb "[(x,y),...]"   (positions of the dangling vias, from the DRC report)"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
pts = eval(sys.argv[3])
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vs = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
for (vx, vy) in pts:
    v = [x for x in vs if abs(tomm(x.GetPosition().x) - vx) < 0.01 and abs(tomm(x.GetPosition().y) - vy) < 0.01][0]
    net = v.GetNetname()
    ends = []
    for t in tr:
        if t.GetNetname() != net or t.GetLayer() != pcbnew.F_Cu:
            continue
        for p in (t.GetStart(), t.GetEnd()):
            d = math.hypot(tomm(p.x) - vx, tomm(p.y) - vy)
            if 0.02 < d < 0.3:
                ends.append((d, p, t))
    ends.sort(key=lambda e: e[0])
    d, p, t0 = ends[0]
    seg = pcbnew.PCB_TRACK(b)
    seg.SetStart(v.GetPosition())
    seg.SetEnd(p)
    seg.SetWidth(t0.GetWidth())
    seg.SetLayer(pcbnew.F_Cu)
    seg.SetNet(b.FindNet(net))
    b.Add(seg)
    b.Remove(v)
    print("via %s at (%.3f, %.3f) -> joined to a track end %.3f mm away" % (net, vx, vy, d))
pcbnew.SaveBoard(sys.argv[2], b)
