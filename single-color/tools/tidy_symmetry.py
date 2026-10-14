"""Snap hand-placed parts onto the clock's lines of symmetry and a 0.05 mm grid, without creating overlaps.
usage (KiCad python): tidy_symmetry.py in.kicad_pcb out.kicad_pcb part1,part2,...   (the parts that were moved by hand)
Rules, each applied per part and reverted if the part would then overlap another part (pads, 0.3 mm margin) or a LiPo outline:
 1. rotation within 20 deg of a multiple of 90 -> that multiple
 2. |x-100| < 0.45 -> x = 100 (12-6 axis);  |y-100| < 0.3 -> y = 100 (3-9 axis)
 3. mirror pairs about x = 100 / equal rows, equal columns for clusters (tolerance given per rule below)
 4. everything moved -> 0.05 mm grid"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
moved = sys.argv[3].split(",")
fp = {f.GetReference(): f for f in b.GetFootprints()}
CELLS = [(91.59, 78.77, 108.41, 95.08), (91.59, 104.92, 108.41, 121.23)]
log = []


def pad_boxes(f):
    out = []
    for p in f.Pads():
        r = p.GetBoundingBox()
        out.append((tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()), p.HasHole()))
    return out


def inter(a, c, m):
    return a[0] - m < c[2] and c[0] < a[2] + m and a[1] - m < c[3] and c[1] < a[3] + m


def court(f):
    poly = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if poly.OutlineCount() == 0:
        return None
    r = poly.BBox()
    return (tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()))


def conflicts(ref):
    f = fp[ref]
    mine = pad_boxes(f)
    bad = set()
    cm = court(f)
    for o, g in fp.items():
        if o != ref and g.IsFlipped() == f.IsFlipped() and cm is not None:
            co = court(g)
            if co is not None and inter(cm, co, 0.0):
                bad.add(o)
    for o, g in fp.items():
        if o == ref:
            continue
        for a in mine:
            for c in pad_boxes(g):
                if (f.IsFlipped() != g.IsFlipped()) and not (a[4] or c[4]):
                    continue
                if inter(a, c, 0.3):
                    bad.add(o)
    if f.IsFlipped():
        for a in mine:
            if any(inter(a, c, 0.0) for c in CELLS):
                bad.add("LiPo outline")
    return bad


def state(ref):
    f = fp[ref]
    return tomm(f.GetPosition().x), tomm(f.GetPosition().y), f.GetOrientationDegrees()


def put(ref, x=None, y=None, rot=None):
    f = fp[ref]
    cx, cy, cr = state(ref)
    nx, ny, nr = (cx if x is None else x), (cy if y is None else y), (cr if rot is None else rot)
    base_bad = conflicts(ref)
    f.SetPosition(pcbnew.VECTOR2I(mm(nx), mm(ny)))
    f.SetOrientationDegrees(nr)
    new_bad = conflicts(ref) - base_bad
    if new_bad:
        f.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
        f.SetOrientationDegrees(cr)
        log.append("  skipped %s -> (%.2f, %.2f, rot %.0f): would overlap %s" % (ref, nx, ny, nr, sorted(new_bad)))
        return False
    return True


before = {r: state(r) for r in moved}
# 1. rotations
for r in moved:
    x, y, rot = state(r)
    nr = round(rot / 90.0) * 90.0
    if abs(rot - nr) > 0.01 and abs(rot - nr) <= 20:
        put(r, rot=nr % 360 if nr % 360 <= 180 else nr % 360 - 360)
# C13 matches its neighbours C10-C12 (vertical 0402)
if "C13" in moved and "C10" in moved:
    put("C13", rot=state("C10")[2])
# 2. axes
for r in moved:
    x, y, rot = state(r)
    if abs(x - 100) < 0.45 and abs(x - 100) > 0.005:
        put(r, x=100.0)
    x, y, rot = state(r)
    if abs(y - 100) < 0.3 and abs(y - 100) > 0.005:
        put(r, y=100.0)
# 3a. mirror pairs about x = 100
for a, c in (("C30", "C31"), ("SW1", "SW2")):
    if a in moved and c in moved:
        xa, ya, _ = state(a)
        xc, yc, _ = state(c)
        d = (xc - xa) / 2
        y = round((ya + yc) / 2 / 0.05) * 0.05
        put(a, x=100 - d, y=y)
        put(c, x=100 + d, y=y)
# inductors: mirror about U4 (x), same row
if all(r in moved for r in ("L1", "L2")):
    s1, s2 = state("L1"), state("L2")
    for d in (7.7, 7.6, 7.5, 7.4, 7.3, 7.2, 7.1, 7.0):
        n0 = len(log)
        ok1 = put("L2", x=100 - d, y=100.0)
        ok2 = put("L1", x=100 + d, y=100.0)
        if ok1 and ok2:
            del log[n0:]
            break
        for r, st in (("L1", s1), ("L2", s2)):                      # undo and try a smaller pitch
            fp[r].SetPosition(pcbnew.VECTOR2I(mm(st[0]), mm(st[1])))
            fp[r].SetOrientationDegrees(st[2])
        del log[n0:]
# connectors: mirror about the 3-9 axis
if all(r in moved for r in ("J1", "J1B")):
    xs = (state("J1")[0] + state("J1B")[0]) / 2
    ya, yb = state("J1")[1], state("J1B")[1]
    d = (yb - ya) / 2
    put("J1", x=xs, y=100 - d)
    put("J1B", x=xs, y=100 + d)
# crystal block: Y1 centred between its two load caps, caps in one column
if all(r in moved for r in ("Y1", "C20", "C21")):
    yc = (state("C20")[1] + state("C21")[1]) / 2
    xc = (state("C20")[0] + state("C21")[0]) / 2
    put("C20", x=xc)
    put("C21", x=xc)
    put("Y1", y=yc)
# 3b. clusters: equal rows / columns (tolerance in mm), per group


def cluster(refs, axis, tol):
    vals = sorted((state(r)[axis], r) for r in refs if r in moved)
    groups, cur = [], []
    for v, r in vals:
        if cur and v - cur[-1][0] > tol:
            groups.append(cur)
            cur = []
        cur.append((v, r))
    if cur:
        groups.append(cur)
    for g in groups:
        if len(g) > 1:
            m = round(sum(v for v, _ in g) / len(g) / 0.05) * 0.05
            for v, r in g:
                put(r, **({"x": m} if axis == 0 else {"y": m}))


bq = ["C50", "C51", "C52", "C53", "C54", "R50", "R51", "R52", "R53", "R54", "R55", "R56"]
cluster(bq, 0, 0.3)
cluster(bq, 1, 0.55)
mcu_caps = ["C10", "C11", "C12", "C13"]
cluster(mcu_caps, 0, 0.3)
cluster(mcu_caps, 1, 0.3)
# 4. grid
for r in moved:
    x, y, rot = state(r)
    put(r, x=round(x / 0.05) * 0.05, y=round(y / 0.05) * 0.05)
after = {r: state(r) for r in moved}
for r in moved:
    a, c = before[r], after[r]
    d = math.hypot(a[0] - c[0], a[1] - c[1])
    if d > 0.005 or abs(a[2] - c[2]) > 0.5:
        print("%-5s (%.2f, %.2f) rot %4.0f -> (%.2f, %.2f) rot %4.0f   moved %.2f mm" % (r, a[0], a[1], a[2], c[0], c[1], c[2], d))
for l in log:
    print(l)
pcbnew.SaveBoard(sys.argv[2], b)
