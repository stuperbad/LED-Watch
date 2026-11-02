"""Remove the leftover tails of old routes that end in a dangling via (typical after a pad was re-assigned and the router joined the new route to the old copper by touching its side).
For each given via position: delete the via; for every track that ended there, cut the track at the nearest point where other copper of its net touches its side (that other copper is moved to the cut
point, so the junction is a real one), or delete the track if nothing touches it.
usage (KiCad python): trim_tails.py in.kicad_pcb out.kicad_pcb "[(x,y),...]"      (positions of the dangling vias from the DRC report)"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
pts = eval(sys.argv[3])


def d(a, b_):
    return math.hypot(a[0] - b_[0], a[1] - b_[1])


def seg_point(p, a, c):
    """closest point on segment a-c to p, and its distance"""
    dx, dy = c[0] - a[0], c[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    q = (a[0] + t * dx, a[1] + t * dy)
    return q, d(p, q), t


ALL = list(b.GetTracks())
TRASH = []
for (x, y) in pts:
    vias = [t for t in ALL if t.GetClass() == "PCB_VIA" and abs(tomm(t.GetPosition().x) - x) < 0.05 and abs(tomm(t.GetPosition().y) - y) < 0.05]
    if not vias:
        print("no via at", x, y)
        continue
    via = vias[0]
    net = via.GetNetCode()
    TRASH.append(via)
    tracks = [t for t in ALL if t not in TRASH and t.GetClass() == "PCB_TRACK" and t.GetNetCode() == net]
    tails = [t for t in tracks if min(d((tomm(t.GetStart().x), tomm(t.GetStart().y)), (x, y)), d((tomm(t.GetEnd().x), tomm(t.GetEnd().y)), (x, y))) < 0.05]
    for t in tails:
        s = (tomm(t.GetStart().x), tomm(t.GetStart().y))
        e = (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
        far, near = (e, s) if d(s, (x, y)) < d(e, (x, y)) else (s, e)       # near = the end at the via
        w = tomm(t.GetWidth())
        # other copper of the net (same layer) touching the side of t
        best = None
        for o in tracks:
            if o is t or o.GetLayer() != t.GetLayer():
                continue
            for end in ("Start", "End"):
                p = getattr(o, "Get" + end)()
                pp = (tomm(p.x), tomm(p.y))
                q, dist, tt = seg_point(pp, far, near)
                if dist <= (w + tomm(o.GetWidth())) / 2 + 0.01 and d(q, far) > 0.02 and d(pp, far) > 0.02:
                    if best is None or d(q, near) < best[0]:
                        best = (d(q, near), q, o, end)
        if best is None:
            TRASH.append(t)
            print("removed tail", [round(v, 3) for v in far], "->", [round(v, 3) for v in near])
            continue
        _, q, o, end = best
        newnear = pcbnew.VECTOR2I(mm(q[0]), mm(q[1]))
        if near == s:
            t.SetStart(newnear)
        else:
            t.SetEnd(newnear)
        getattr(o, "Set" + end)(newnear)
        print("cut tail at", [round(v, 3) for v in q], "(was to", [round(v, 3) for v in near], ")")
for t in TRASH:
    b.Remove(t)
pcbnew.SaveBoard(sys.argv[2], b)
