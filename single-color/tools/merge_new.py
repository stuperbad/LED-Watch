"""
Merge autorouter output onto the real (arc) polar board.
  base_poly   = board with the polar copper as short segments (what the autorouter saw)
  routed_poly = base_poly after ImportSpecctraSES (the session echoes the fixed polar wires, slightly rounded, plus the new routing)
  base_arc    = the same polar copper drawn with true arcs
Every track/via in routed_poly that does NOT match an item of base_poly (same layer, ends within TOL) is copied onto base_arc.
usage: python merge_new.py base_poly routed_poly base_arc out
"""
import sys
import pcbnew
from pcbnew import VECTOR2I as V

TOL = 4000      # 4 um in nm
base_poly, routed_poly, base_arc, out = sys.argv[1:5]
A = pcbnew.LoadBoard(base_poly)
B = pcbnew.LoadBoard(routed_poly)
C = pcbnew.LoadBoard(base_arc)


def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (t.GetLayer(), s.x, s.y, e.x, e.y)


segs = [(t.GetLayer(), t.GetStart(), t.GetEnd(), t.GetNetname()) for t in A.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t.GetPosition() for t in A.GetTracks() if t.GetClass() == "PCB_VIA"]
# spatial hash on start points
from collections import defaultdict
grid = defaultdict(list)
for i, (l, s, e, _n) in enumerate(segs):
    grid[(s.x // 2000000, s.y // 2000000)].append(i)
    grid[(e.x // 2000000, e.y // 2000000)].append(i)


def near(p, q):
    return abs(p.x - q.x) <= TOL and abs(p.y - q.y) <= TOL


def _pt_seg(p, a, b):
    ax, ay, bx, by = a.x, a.y, b.x, b.y
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p.x - ax) * dx + (p.y - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return ((p.x - qx) ** 2 + (p.y - qy) ** 2) ** 0.5


def on_polar(p, l, net):
    """is point p (nm) on a polar segment of layer l (within 30 um, same net)?"""
    for gx in (p.x // 2000000 - 1, p.x // 2000000, p.x // 2000000 + 1):
        for gy in (p.y // 2000000 - 1, p.y // 2000000, p.y // 2000000 + 1):
            for i in grid.get((gx, gy), []):
                l2, s2, e2, n2 = segs[i]
                if l2 == l and n2 == net and _pt_seg(p, s2, e2) <= 30000:
                    return True
    return False


def known_seg(t):
    """duplicate of polar copper (the session echoes it, re-split): both ends lie on a polar segment of the same layer"""
    return on_polar(t.GetStart(), t.GetLayer(), t.GetNetname()) and on_polar(t.GetEnd(), t.GetLayer(), t.GetNetname())


via_set = {(v.x // 2000, v.y // 2000) for v in vias}
n_new_t = n_new_v = 0
for t in B.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        if known_seg(t):
            continue
        nt = pcbnew.PCB_TRACK(C)
        nt.SetStart(t.GetStart()); nt.SetEnd(t.GetEnd()); nt.SetWidth(t.GetWidth()); nt.SetLayer(t.GetLayer())
        net = C.FindNet(t.GetNetname())
        if net:
            nt.SetNet(net)
        C.Add(nt); n_new_t += 1
    elif t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        if any((p.x // 2000 + dx, p.y // 2000 + dy) in via_set for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        nv = pcbnew.PCB_VIA(C)
        nv.SetPosition(p); nv.SetViaType(pcbnew.VIATYPE_THROUGH); nv.SetDrill(t.GetDrill())
        nv.SetWidth(pcbnew.F_Cu, t.GetWidth(pcbnew.F_Cu))
        net = C.FindNet(t.GetNetname())
        if net:
            nv.SetNet(net)
        C.Add(nv); n_new_v += 1
if list(C.Zones()):
    pcbnew.ZONE_FILLER(C).Fill(C.Zones())          # the ground plane / guard must be re-filled around the new copper
pcbnew.SaveBoard(out, C)
print(f"new tracks {n_new_t}, new vias {n_new_v} -> {out}")
