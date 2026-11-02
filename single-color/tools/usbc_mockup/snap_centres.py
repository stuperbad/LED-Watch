"""snap_centres.py in.kicad_pcb out.kicad_pcb [x0] : move track ends that sit inside a same-net pad or via (not at its centre) onto the centre.
Applies to the USB-C block parts only (REFS below) and every via at x >= x0 (default 95) except ring nets; every piece that shared the old end point moves with it.
A piece that would stop being 0/45/90 degrees gets one elbow (first leg keeps the old direction where possible). KiCad python."""
import sys, math, re
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
x0 = float(sys.argv[3]) if len(sys.argv) > 3 else 95.0
REFS = {"J2", "U5", "U4", "L1", "L2", "D50"} | {"C%d" % i for i in range(50, 57)} | {"R%d" % i for i in list(range(50, 57)) + list(range(68, 73))}
ring = re.compile(r"^/(COL\d+|ROW\d+)$")
SKIP = {(105.975, 97.535)}   # snapping these made DRC errors (tracks crossing / clearance); left for hand editing
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
xy = lambda p: (tomm(p.x), tomm(p.y))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [(f.GetReference(), p) for f in b.GetFootprints() for p in f.Pads() if f.GetReference() in REFS and p.GetNumber() != "SH" and p.GetNetCode() > 0]
moves = {}   # (layer, net, old point) -> centre
for t in tracks:
    if ring.match(t.GetNetname()):
        continue
    L = t.GetLayer()
    for e in (t.GetStart(), t.GetEnd()):
        if tomm(e.x) < x0:
            continue
        for ref, p in pads:
            if p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(L) and p.HitTest(e):
                c = xy(p.GetPosition())
                if math.hypot(c[0] - tomm(e.x), c[1] - tomm(e.y)) > 0.005:
                    if (round(tomm(e.x), 3), round(tomm(e.y), 3)) not in SKIP:
                        moves[(L, t.GetNetCode(), (round(tomm(e.x), 3), round(tomm(e.y), 3)))] = (c, ref + "." + p.GetNumber())
        for v in vias:
            if v.GetNetCode() == t.GetNetCode() and v.IsOnLayer(L) and not ring.match(v.GetNetname()):
                c = xy(v.GetPosition())
                d = math.hypot(c[0] - tomm(e.x), c[1] - tomm(e.y))
                if 0.005 < d < tomm(v.GetWidth(L)) / 2:
                    if (round(tomm(e.x), 3), round(tomm(e.y), 3)) not in SKIP:
                        moves[(L, t.GetNetCode(), (round(tomm(e.x), 3), round(tomm(e.y), 3)))] = (c, "via")
print("end points to snap:", len(moves))


def ang_ok(a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    if math.hypot(dx, dy) < 1e-4:
        return True
    r = math.degrees(math.atan2(dy, dx)) % 45
    return min(r, 45 - r) < 0.05


def elbow(a, c, first_dir):
    dx, dy = c[0] - a[0], c[1] - a[1]
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    ax, ay = abs(dx), abs(dy)
    if ax >= ay:
        cands = [(a[0] + sx * (ax - ay), a[1]), (a[0] + sx * ay, a[1] + sy * ay)]
    else:
        cands = [(a[0], a[1] + sy * (ay - ax)), (a[0] + sx * ax, a[1] + sy * ax)]
    best = None
    for e in cands:
        d = math.hypot(e[0] - a[0], e[1] - a[1])
        if d < 1e-4:
            return None
        ang = math.degrees(math.atan2(e[1] - a[1], e[0] - a[0]))
        score = abs(((ang - first_dir) + 180) % 360 - 180)
        if best is None or score < best[0]:
            best = (score, e)
    return best[1]


new, kill, left = [], [], []
for (L, net, old), (c, what) in moves.items():
    at = []
    for t in tracks:
        if t.GetLayer() != L or t.GetNetCode() != net:
            continue
        s, e = xy(t.GetStart()), xy(t.GetEnd())
        for here, other in ((s, e), (e, s)):
            if math.hypot(here[0] - old[0], here[1] - old[1]) < 0.011:
                at.append((t, other, here))
    if len(at) != 1:
        left.append((what, net, old, c, "%d pieces meet here" % len(at)))
        continue
    t, other, here = at[0]
    first = round(math.degrees(math.atan2(here[1] - other[1], here[0] - other[0])) / 45) * 45
    if ang_ok(other, c):
        if math.hypot(c[0] - other[0], c[1] - other[1]) < 0.2 and math.hypot(here[0] - other[0], here[1] - other[1]) >= 0.2:
            left.append((what, net, old, c, "would leave a stub shorter than 0.2 mm"))
            continue
        kill.append(t)
        new.append((L, net, t.GetWidth(), other, c))
        print("  %-8s %s: (%.3f,%.3f)->(%.3f,%.3f)" % (what, t.GetNetname(), old[0], old[1], c[0], c[1]))
        continue
    el = elbow(other, c, first)
    if el is None or math.hypot(el[0] - other[0], el[1] - other[1]) < 0.2 or math.hypot(c[0] - el[0], c[1] - el[1]) < 0.2:
        left.append((what, net, old, c, "needs a corner shorter than 0.2 mm; move by hand"))
        continue
    kill.append(t)
    new.append((L, net, t.GetWidth(), other, el))
    new.append((L, net, t.GetWidth(), el, c))
    print("  %-8s %s: (%.3f,%.3f)->(%.3f,%.3f) +corner" % (what, t.GetNetName() if False else t.GetNetname(), old[0], old[1], c[0], c[1]))
print("left for hand editing: %d" % len(left))
for x in left:
    print("   LEFT", x)
for t in kill:
    b.Remove(t)
for L, net, w, a, c in new:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(a)); t.SetEnd(V(c)); t.SetWidth(w); t.SetLayer(L); t.SetNetCode(net)
    b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b)
print("pieces replaced", len(kill), "created", len(new))
