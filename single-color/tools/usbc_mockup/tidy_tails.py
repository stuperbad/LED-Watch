"""tidy_tails.py in.kicad_pcb out.kicad_pcb : (1) delete zero-length tracks; (2) a free-ended track that runs past a via of its own net (via within 0.05 mm of the track line, track continuing 0.15 mm or more beyond it)
is cut at the via, the via is moved onto the track line and the track pieces on the via end follow. KiCad python."""
import sys, math
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
xy = lambda p: (tomm(p.x), tomm(p.y))
grave = []
n0 = 0
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetLength() == 0:
        b.Remove(t); grave.append(t); n0 += 1
print("zero-length tracks deleted:", n0)
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
ends = lambda t: (xy(t.GetStart()), xy(t.GetEnd()))
for t in tracks:
    s, e = ends(t)
    for free, other in ((s, e), (e, s)):
        # free end: no pad, no other track of the same net and layer ends here
        if any(p.IsOnLayer(t.GetLayer()) and p.HitTest(V(free)) for p in pads):
            continue
        if any(o is not t and o.GetLayer() == t.GetLayer() and o.GetNetCode() == t.GetNetCode() and any(math.hypot(q[0] - free[0], q[1] - free[1]) < 0.02 for q in ends(o)) for o in tracks):
            continue
        if any(v.GetNetCode() == t.GetNetCode() and math.hypot(xy(v.GetPosition())[0] - free[0], xy(v.GetPosition())[1] - free[1]) < 0.2 for v in vias):
            continue
        dx, dy = free[0] - other[0], free[1] - other[1]
        L = math.hypot(dx, dy)
        for v in vias:
            if v.GetNetCode() != t.GetNetCode():
                continue
            c = xy(v.GetPosition())
            u = ((c[0] - other[0]) * dx + (c[1] - other[1]) * dy) / L
            if 0.05 < u < L - 0.15:
                foot = (other[0] + dx * u / L, other[1] + dy * u / L)
                if math.hypot(c[0] - foot[0], c[1] - foot[1]) < 0.05:
                    print("tail of %s track cut at the via (%.3f,%.3f); via moved to (%.3f,%.3f)" % (t.GetNetname(), c[0], c[1], foot[0], foot[1]))
                    for o in tracks:
                        if o is t:
                            continue
                        for setter, getter in ((o.SetStart, o.GetStart), (o.SetEnd, o.GetEnd)):
                            if v.IsOnLayer(o.GetLayer()) and o.GetNetCode() == t.GetNetCode() and math.hypot(xy(getter())[0] - c[0], xy(getter())[1] - c[1]) < 0.02:
                                setter(V(foot))
                    v.SetPosition(V(foot))
                    if free == s:
                        t.SetStart(V(foot))
                    else:
                        t.SetEnd(V(foot))
                    break
pcbnew.SaveBoard(sys.argv[2], b)
