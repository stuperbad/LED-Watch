"""Cut the sharp corners found by check_angles.py: where exactly two pieces of copper (straight tracks and/or arcs) of one net and layer meet at a point that is not a pad or a via and the angle
between them is below MIN degrees, both pieces are shortened by D mm (an arc along its own circle) and the two new ends are joined by a short straight track.  The corner becomes two obtuse bends
(each about (180 + angle) / 2 degrees).  Corners with a pad, a via or a third piece of copper are only reported.
usage (KiCad python): fix_angles.py in.kicad_pcb out.kicad_pcb [MIN_DEG=89.5] [D_MM=0.4] [--skip="[(x,y),...]"] [--only-near=x,y,half]
Run the DRC afterwards: the new piece lies inside the old corner, so it only ever moves away from copper on the outside, but not necessarily from copper inside the wedge."""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
MIN, D = 89.5, 0.4
SKIP, NEAR = [], None
pos = []
for a in sys.argv[3:]:
    if a.startswith("--skip="):
        SKIP = eval(a[7:])
    elif a.startswith("--only-near="):
        NEAR = [float(v) for v in a[12:].split(",")]
    else:
        pos.append(float(a))
if pos:
    MIN = pos[0]
if len(pos) > 1:
    D = pos[1]
b = pcbnew.LoadBoard(src)
EPS = 0.01


def P(p):
    return (tomm(p.x), tomm(p.y))


def V(p):
    return pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))


def circle(s, m, e):
    ax, ay = s; bx, by = m; cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


class Item:
    """one track or arc; end(w) = point, out(w) = unit direction leaving that end along the item, cut(w, d) = (new end point, apply())"""

    def __init__(self, t):
        self.t = t
        self.arc = t.GetClass() == "PCB_ARC"
        self.s, self.e = P(t.GetStart()), P(t.GetEnd())
        if self.arc:
            self.m = P(t.GetMid())
            self.c, self.r = circle(self.s, self.m, self.e)

    def end(self, w):
        return self.s if w == 0 else self.e

    def far(self, w):
        return self.e if w == 0 else self.s

    def out(self, w):
        p = self.end(w)
        if not self.arc:
            q = self.far(w)
        else:
            # tangent: direction toward the arc interior, from the neighbour on the circle
            a0 = math.atan2(p[1] - self.c[1], p[0] - self.c[0])
            am = math.atan2(self.m[1] - self.c[1], self.m[0] - self.c[0])
            sweep = (am - a0 + math.pi) % (2 * math.pi) - math.pi
            sgn = 1 if sweep > 0 else -1
            a1 = a0 + sgn * 0.02
            q = (self.c[0] + self.r * math.cos(a1), self.c[1] + self.r * math.sin(a1))
        n = math.hypot(q[0] - p[0], q[1] - p[1]) or 1
        return ((q[0] - p[0]) / n, (q[1] - p[1]) / n)

    def length(self):
        if not self.arc:
            return math.hypot(self.e[0] - self.s[0], self.e[1] - self.s[1])
        a0 = math.atan2(self.s[1] - self.c[1], self.s[0] - self.c[0])
        a2 = math.atan2(self.e[1] - self.c[1], self.e[0] - self.c[0])
        am = math.atan2(self.m[1] - self.c[1], self.m[0] - self.c[0])
        s1 = (am - a0 + math.pi) % (2 * math.pi) - math.pi
        sgn = 1 if s1 > 0 else -1
        sw = (a2 - a0) * sgn % (2 * math.pi)
        return sw * self.r

    def cut(self, w, d):
        """shorten at end w by d mm; returns the new end point"""
        p = self.end(w)
        if not self.arc:
            u = self.out(w)
            q = (p[0] + u[0] * d, p[1] + u[1] * d)
            (self.t.SetStart if w == 0 else self.t.SetEnd)(V(q))
            return q
        a0 = math.atan2(p[1] - self.c[1], p[0] - self.c[0])
        am = math.atan2(self.m[1] - self.c[1], self.m[0] - self.c[0])
        sweep = (am - a0 + math.pi) % (2 * math.pi) - math.pi
        sgn = 1 if sweep > 0 else -1
        a1 = a0 + sgn * d / self.r
        q = (self.c[0] + self.r * math.cos(a1), self.c[1] + self.r * math.sin(a1))
        o = self.far(w)
        ao = math.atan2(o[1] - self.c[1], o[0] - self.c[0])
        span = (ao - a1) * sgn % (2 * math.pi)          # from q to the far end, going on the way the arc goes
        amid = a1 + sgn * span / 2
        mid = (self.c[0] + self.r * math.cos(amid), self.c[1] + self.r * math.sin(amid))
        if w == 0:
            self.t.SetStart(V(q))
        else:
            self.t.SetEnd(V(q))
        self.t.SetMid(V(mid))
        return q


items = [Item(t) for t in b.GetTracks() if t.GetClass() in ("PCB_TRACK", "PCB_ARC")]
via_pts = [P(t.GetPosition()) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
ends = {}
for it in items:
    for w in (0, 1):
        p = it.end(w)
        ends.setdefault((it.t.GetNetname(), it.t.GetLayer(), round(p[0] / 0.02), round(p[1] / 0.02)), []).append((it, w, p))

rep, new, trash = [], [], []
seen = set()
for key, lst in list(ends.items()):
    net, layer, kx, ky = key
    cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cand += ends.get((net, layer, kx + dx, ky + dy), [])
    p0 = lst[0][2]
    cand = [c for c in cand if math.hypot(c[2][0] - p0[0], c[2][1] - p0[1]) < EPS]
    ids = tuple(sorted(id(c[0]) for c in cand))
    if len(cand) != 2 or len(set(ids)) != 2 or ids in seen:
        continue
    seen.add(ids)
    (A, wa, _), (B, wb, _) = cand
    if NEAR and not (abs(p0[0] - NEAR[0]) <= NEAR[2] and abs(p0[1] - NEAR[1]) <= NEAR[2]):
        continue
    if any(math.hypot(p0[0] - x, p0[1] - y) < 0.05 for x, y in SKIP):
        continue
    ua, ub = A.out(wa), B.out(wb)
    ang = math.degrees(math.acos(max(-1, min(1, ua[0] * ub[0] + ua[1] * ub[1]))))
    if ang >= MIN:
        continue
    v0 = V(p0)
    if any(math.hypot(p0[0] - q[0], p0[1] - q[1]) < 0.3 for q in via_pts) or any(pd.HitTest(v0, mm(0.1)) for pd in pads):
        rep.append((ang, p0, "left: pad/via")); continue
    la, lb = A.length(), B.length()
    d = min(D, 0.45 * la, 0.45 * lb)
    if d < 0.08:
        rep.append((ang, p0, "left: pieces too short")); continue
    qa = A.cut(wa, d)
    qb = B.cut(wb, d)
    nt = pcbnew.PCB_TRACK(b)
    nt.SetStart(V(qa)); nt.SetEnd(V(qb)); nt.SetWidth(A.t.GetWidth()); nt.SetLayer(A.t.GetLayer()); nt.SetNetCode(A.t.GetNetCode())
    new.append(nt)
    rep.append((ang, p0, "cut %.2f%s" % (d, " (arc)" if A.arc or B.arc else "")))
for t in new:
    b.Add(t)
for ang, p, what in sorted(rep):
    print(f"{ang:5.1f} deg at ({p[0]:.3f}, {p[1]:.3f})  {what}")
print(len([r for r in rep if r[2].startswith("cut")]), "corners cut,", len([r for r in rep if r[2].startswith("left")]), "left alone")
pcbnew.SaveBoard(dst, b)
