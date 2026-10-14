"""Strap slots to 2.5 mm + silkscreen: weekday letters (S M T W T F S, week starts Sunday) in the seconds row, minute numbers 0..55 between the minute and
second rows, hour numbers 12/3/6/9 just inside the hour LEDs.  All text unrotated.
usage (KiCad python): add_silk.py in.kicad_pcb out.kicad_pcb"""
import math
import re
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
SLOT_H = 2.5
TH = 0.1
NUM = (0.6, 0.8)           # width, height of the numerals
NUM2 = (0.5, 0.8)          # two-digit numbers
PC, SC = 0.12, 0.05        # silk-to-pad and silk-to-silk clearance
LET = (0.6, 0.8)           # narrower weekday letters

# ---------------- 1. strap slots -------------------------------------------------------------------------------------------------
old = []
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        ps = d.GetPolyShape()
        o = ps.Outline(0)
        xs = [tomm(o.CPoint(i).x) for i in range(o.PointCount())]
        ys = [tomm(o.CPoint(i).y) for i in range(o.PointCount())]
        if max(ys) - min(ys) < 3:                                  # a slot (the outline is much taller)
            old.append((d, (min(xs), max(xs), (min(ys) + max(ys)) / 2), d.GetWidth()))
assert len(old) == 2, len(old)
for d, _, _ in old:
    b.Remove(d)
for _, (x0, x1, yc), w in old:
    r = SLOT_H / 2
    pts = []
    n = 24
    for i in range(n + 1):                                         # right cap, top to bottom
        a = -math.pi / 2 + math.pi * i / n
        pts.append((x1 - r + r * math.cos(a), yc + r * math.sin(a)))
    for i in range(n + 1):                                         # left cap, bottom to top
        a = math.pi / 2 + math.pi * i / n
        pts.append((x0 + r + r * math.cos(a), yc + r * math.sin(a)))
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in pts:
        ps.Append(mm(x), mm(y))
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyShape(ps)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(w)
    b.Add(s)
print("slots: height %.2f mm, width %.2f mm" % (SLOT_H, old[0][1][1] - old[0][1][0]))
slotboxes = [(x0, yc - SLOT_H / 2, x1, yc + SLOT_H / 2) for _, (x0, x1, yc), _w in old]

# ---------------- 2. obstacles on the front ---------------------------------------------------------------------------------------
fps = list(b.GetFootprints())
pads = []                                                         # (cx, cy, w, h, angle_deg)
silk = []                                                         # axis-aligned boxes
ring = re.compile(r"^(H|M|S)\d+$")
radii = {"H": [], "M": [], "S": []}
for f in fps:
    if f.IsFlipped():
        continue
    for p in f.Pads():
        if not p.IsOnLayer(pcbnew.F_Cu):
            continue
        sz = p.GetSize()
        ang = p.GetOrientationDegrees() if hasattr(p, "GetOrientationDegrees") else 0.0
        pads.append((tomm(p.GetPosition().x), tomm(p.GetPosition().y), tomm(sz.x), tomm(sz.y), ang))
        if ring.match(f.GetReference()):
            cx, cy = tomm(p.GetPosition().x) - 100, tomm(p.GetPosition().y) - 100
            hw = max(tomm(sz.x), tomm(sz.y)) / 2
            radii[f.GetReference()[0]].append((math.hypot(cx, cy) - hw, math.hypot(cx, cy) + hw))
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS:
            r = g.GetBoundingBox()
            silk.append((tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom())))
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.F_SilkS:
        r = d.GetBoundingBox()
        silk.append((tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom())))
rH_in = min(a for a, _ in radii["H"])
rM_out = max(b_ for _, b_ in radii["M"])
rS_in = min(a for a, _ in radii["S"])
rS = sum((a + b_) / 2 for a, b_ in radii["S"]) / len(radii["S"])
print("hour inner pad edge %.2f | minute outer %.2f | second inner %.2f | second row centre %.2f" % (rH_in, rM_out, rS_in, rS))
R_EDGE = 21.0 - 0.35


def rect_overlap_pad(bx, pad, clr):
    """axis-aligned box bx (x0,y0,x1,y1) vs rotated rectangular pad, with clearance clr (separating axes)"""
    cx, cy, w, h, ang = pad
    hw, hh = w / 2 + clr, h / 2 + clr
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -math.sin(a), math.cos(a)
    bcx, bcy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    bw, bh = (bx[2] - bx[0]) / 2, (bx[3] - bx[1]) / 2
    dx, dy = cx - bcx, cy - bcy
    for ax, ay in ((1, 0), (0, 1), (ux, uy), (vx, vy)):
        ra = bw * abs(ax) + bh * abs(ay)
        rb = hw * abs(ax * ux + ay * uy) + hh * abs(ax * vx + ay * vy)
        if abs(dx * ax + dy * ay) > ra + rb:
            return False
    return True


def box_hit(a, c, m=0.0):
    return a[0] - m < c[2] and c[0] < a[2] + m and a[1] - m < c[3] and c[1] < a[3] + m


placed = []
labels = []


def text_box(txt, size, x, y):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size[0]), mm(size[1])))
    t.SetTextThickness(mm(TH))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetTextAngleDegrees(0)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    r = t.GetEffectiveTextShape().BBox()                       # the real ink extents, not the padded text box
    hw = TH / 2
    return t, (tomm(r.GetX()) - hw, tomm(r.GetY()) - hw, tomm(r.GetRight()) + hw, tomm(r.GetBottom()) + hw)


DBG = {}


def feasible(bx):
    far = max(math.hypot(x - 100, y - 100) for x in (bx[0], bx[2]) for y in (bx[1], bx[3]))
    if far > R_EDGE:
        DBG['edge'] = DBG.get('edge', 0) + 1
        return False
    if any(box_hit(bx, s, SC) for s in silk + placed + slotboxes):
        DBG['silk'] = DBG.get('silk', 0) + 1
        return False
    cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    for p in pads:
        if abs(p[0] - cx) < 4 and abs(p[1] - cy) < 4 and rect_overlap_pad(bx, p, PC):
            DBG['pad'] = DBG.get('pad', 0) + 1
            return False
    return True


def put_label(txt, size, target_deg, r_list, tangential_deg, tag):

    """radius candidates in order of preference, tangential offsets in order; the first feasible radius wins, then the smallest tangential shift"""
    best = None
    for dr in r_list:
        for dt in tangential_deg:
            ang = math.radians(target_deg + dt)
            x, y = 100 + dr * math.sin(ang), 100 - dr * math.cos(ang)
            t, bx = text_box(txt, size, x, y)
            if feasible(bx):
                cost = abs(dt)
                if best is None or cost < best[0]:
                    best = (cost, t, bx, dr, dt)
        if best:
            break
    if best is None:
        print("  NO ROOM for", tag, txt)
        return False
    _, t, bx, dr, dt = best
    b.Add(t)
    placed.append(bx)
    labels.append((tag, txt, round(dr, 2), round(dt, 2)))
    return True


def frange(a, c, s):
    n = int(round((c - a) / s))
    return [a + i * s for i in range(n + 1)]


# hour numbers, inside the hour LEDs: 12 and 6 hug the LED on the 12-6 axis; 3 and 9 sit exactly on the 3-9 axis, centred in the free interval
for deg, txt in ((0, "12"), (180, "6")):
    put_label(txt, NUM if len(txt) == 1 else NUM2, deg, frange(rH_in - 0.55, rH_in - 3.0, -0.05), [0], "hour")
for sign, txt in ((1, "3"), (-1, "9")):
    runs = []
    for i in range(int(round((rH_in - 0.2) / 0.02)) + 1):
        r_ = rH_in - 0.2 - i * 0.02
        t_, bx_ = text_box(txt, NUM, 100 + sign * r_, 100.0)
        if feasible(bx_):
            runs.append(r_)
        elif runs:
            break                                              # first blocked radius after the free run next to the LED
    if not runs:
        print("  NO ROOM for hour", txt)
        continue
    r_mid = (max(runs) + min(runs)) / 2
    t_, bx_ = text_box(txt, NUM, 100 + sign * r_mid, 100.0)
    b.Add(t_)
    placed.append(bx_)
    labels.append(("hour", txt, round(r_mid, 2), 0.0))
    print("  free interval for %s: radius %.2f..%.2f -> centred at %.2f" % (txt, min(runs), max(runs), r_mid))
# minute numbers between the minute and second rows: at the 5-minute angle first, then clockwise into the gap
rmid = (rM_out + rS_in) / 2
for k in range(12):
    txt = "0" if k == 0 else str(5 * k)
    put_label(txt, NUM if len(txt) == 1 else NUM2, 30 * k, [rmid, rmid - 0.1, rmid + 0.1, rmid - 0.2, rmid + 0.2], [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], "minute")
# the seven mode LEDs double as weekday lights: SET-S TMR-M ALM-T BAT-W FUN-T CFG-F LCK-S  (week starts Sunday)
WK = {"SET": "S", "TMR": "M", "ALM": "T", "BAT": "W", "FUN": "T", "CFG": "F", "LCK": "S"}
lab = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetText() in WK]
assert len(lab) == 7, len(lab)
LW = 0.5
for d in lab:
    d.SetText(d.GetText() + "-" + WK[d.GetText()])
    d.SetTextSize(pcbnew.VECTOR2I(mm(LW), mm(0.8)))
    d.SetTextThickness(mm(TH))
boxes = sorted((d.GetEffectiveTextShape().BBox() for d in lab), key=lambda r: r.GetX())
gaps = [tomm(boxes[i + 1].GetX() - boxes[i].GetRight()) for i in range(6)]
print("mode labels now e.g. %s; widths %.2f mm; smallest gap between neighbours %.2f mm" % (lab[0].GetText(), tomm(boxes[0].GetWidth()), min(gaps)))
for l in labels:
    print("  %-8s %-3s radius %.2f  tangential shift %+.1f deg" % l)
pcbnew.SaveBoard(sys.argv[2], b)
