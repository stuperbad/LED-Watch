"""Open up a window of inner-layer copper around a chip so the breakout can be routed again as one problem, WITHOUT destroying the long lanes that merely pass through:
for every net of the given list (or every net that has a signal pad on REF), the straight In1.Cu / B.Cu tracks inside the window rectangle are cut off at the window edge (the part outside stays,
the part inside goes), arcs that touch the window are listed and deleted whole (rare: the long lanes are far from the chip), and then the vias that no track/pad of their net touches any more are deleted.
F.Cu copper, fan-out vias and pad stubs are never touched.
usage (KiCad python): rip_window.py in.kicad_pcb out.kicad_pcb x0,y0,x1,y1 [--ref U1] [--layers In1.Cu,B.Cu] [--skip-nets=GND,VBAT,...] [--nets=@file] [--keep-x-lt=96.6]
 --keep-x-lt: ignore everything left of this x (the crystal corridor side).  Prints the nets that were opened."""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
X0, Y0, X1, Y1 = (float(v) for v in sys.argv[3].split(","))
REF, LAYERS, SKIP, NETS, KEEPX = "U1", {"In1.Cu", "B.Cu"}, {"GND", "VBAT", ""}, None, None
for a in sys.argv[4:]:
    if a.startswith("--ref="):
        REF = a[6:]
    elif a.startswith("--layers="):
        LAYERS = set(a[9:].split(","))
    elif a.startswith("--skip-nets="):
        SKIP = set(a[12:].split(","))
    elif a.startswith("--nets="):
        NETS = set(ln.strip() for ln in open(a[8:].lstrip("@")) if ln.strip())
    elif a.startswith("--keep-x-lt="):
        KEEPX = float(a[12:])
b = pcbnew.LoadBoard(src)
if NETS is None:
    NETS = set(p.GetNetname() for f in b.GetFootprints() if f.GetReference() == REF for p in f.Pads()) - SKIP
V = pcbnew.VECTOR2I


def clip(p, q):
    """Liang-Barsky: parameters (t0, t1) of the part of segment p->q inside the window, or None"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - X0), (dx, X1 - p[0]), (-dy, p[1] - Y0), (dy, Y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return None
        else:
            t = qq / pp
            if pp < 0:
                if t > t1:
                    return None
                t0 = max(t0, t)
            else:
                if t < t0:
                    return None
                t1 = min(t1, t)
    return (t0, t1) if t1 - t0 > 1e-9 else None


def arc_points(s, m, e, n=60):
    ax, ay = s; bx, by = m; cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [s, e]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(py - uy, px - ux) for px, py in (s, m, e))
    nn = lambda x: x % (2 * math.pi)
    ccw = nn(am - a0) < nn(a1 - a0)
    sw = nn(a1 - a0) if ccw else -nn(a0 - a1)
    return [(ux + r * math.cos(a0 + sw * i / n), uy + r * math.sin(a0 + sw * i / n)) for i in range(n + 1)]


todo_remove, todo_add, opened = [], [], {}
for t in list(b.GetTracks()):
    c = t.GetClass()
    if c == "PCB_VIA" or t.GetNetname() not in NETS or b.GetLayerName(t.GetLayer()) not in LAYERS:
        continue
    s, e = (tomm(t.GetStart().x), tomm(t.GetStart().y)), (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
    if c == "PCB_ARC":
        pts = arc_points(s, (tomm(t.GetMid().x), tomm(t.GetMid().y)), e)
        if any(X0 <= x <= X1 and Y0 <= y <= Y1 and (KEEPX is None or x >= KEEPX) for x, y in pts):
            todo_remove.append(t); opened[t.GetNetname()] = opened.get(t.GetNetname(), 0) + 1
            print("arc deleted:", t.GetNetname(), b.GetLayerName(t.GetLayer()), "start (%.2f, %.2f) end (%.2f, %.2f)" % (s + e))
        continue
    r = clip(s, e)
    if r is None:
        continue
    if KEEPX is not None and max(s[0], e[0]) < KEEPX:
        continue
    t0, t1 = r
    todo_remove.append(t)
    opened[t.GetNetname()] = opened.get(t.GetNetname(), 0) + 1
    L = math.hypot(e[0] - s[0], e[1] - s[1])
    for (a0, a1) in ((0.0, t0), (t1, 1.0)):
        if (a1 - a0) * L > 0.02:
            p0 = (s[0] + (e[0] - s[0]) * a0, s[1] + (e[1] - s[1]) * a0)
            p1 = (s[0] + (e[0] - s[0]) * a1, s[1] + (e[1] - s[1]) * a1)
            n = pcbnew.PCB_TRACK(b)
            n.SetStart(V(mm(p0[0]), mm(p0[1]))); n.SetEnd(V(mm(p1[0]), mm(p1[1])))
            n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNetCode(t.GetNetCode())
            todo_add.append(n)
for t in todo_remove:
    b.Remove(t)
for n in todo_add:
    b.Add(n)
# vias that nothing touches any more (not on a pad of their net)
pads = [p for f in b.GetFootprints() for p in f.Pads()]
tr = list(b.GetTracks())
gone = []
EPS = 0.03
for v in tr:
    if v.GetClass() != "PCB_VIA" or v.GetNetname() not in NETS:
        continue
    q = (tomm(v.GetPosition().x), tomm(v.GetPosition().y))
    if not (X0 <= q[0] <= X1 and Y0 <= q[1] <= Y1):
        continue
    used = False
    for o in tr:
        if o is v or o.GetClass() == "PCB_VIA" or o.GetNetname() != v.GetNetname():
            continue
        for pt in (o.GetStart(), o.GetEnd()):
            if math.hypot(tomm(pt.x) - q[0], tomm(pt.y) - q[1]) < EPS:
                used = True
    if not used and any(p.GetNetname() == v.GetNetname() and p.HitTest(v.GetPosition(), 0) for p in pads):
        used = True
    if not used:
        gone.append(v)
for v in gone:
    b.Remove(v)
print("tracks cut:", dict(sorted(opened.items())))
print("orphan vias removed:", len(gone))
pcbnew.SaveBoard(dst, b)
