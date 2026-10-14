"""Placement MOCK of the proposed re-layout (no routing).  usage (KiCad python): mock_move.py in_marked.kicad_pcb out.kicad_pcb A|B
A = 5x5 magnetic buzzer (front, left of the MCU) + MOSFET/diode/pull-down on the back;  B = 9x9 piezo on the back.
Common: BQ25570 support parts, MCU/IMU decoupling moved to the back next to their chips; dummy parts kept but tagged (delete them in KiCad when agreed)."""
import math
import sys

import pcbnew


class box:
    def __init__(self, x0, y0, x1, y1):
        self.r = (x0, y0, x1, y1)

    def intersects(self, o):
        a, b = self.r, o.r
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


mm = pcbnew.FromMM
tomm = pcbnew.ToMM
src, dst, opt = sys.argv[1], sys.argv[2], sys.argv[3]
b = pcbnew.LoadBoard(src)
fp = {f.GetReference(): f for f in b.GetFootprints()}
CRYSTAL = box(104.75, 89.25, 109.25, 94.65)
LIB = "C:/Program Files/KiCad/10.0/share/kicad/footprints/"


def bbox(f, infl=0.25):
    xs0, ys0, xs1, ys1 = [], [], [], []
    for p in f.Pads():
        r = p.GetBoundingBox()
        xs0.append(tomm(r.GetX()))
        ys0.append(tomm(r.GetY()))
        xs1.append(tomm(r.GetX() + r.GetWidth()))
        ys1.append(tomm(r.GetY() + r.GetHeight()))
    return box(min(xs0) - infl, min(ys0) - infl, max(xs1) + infl, max(ys1) + infl)


def to_back(f):
    if not f.IsFlipped():
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)


def setpos(f, x, y, rot=0.0):
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    f.SetOrientationDegrees(rot)


occ_back = [bbox(fp[r], 0.5) for r in ("J1", "J1B", "L1", "L2", "U4")]
occ_front_extra = []


def free_back(g, x, y):
    if math.hypot(x - 100, y - 100) > 20.4:
        return False
    return not any(g.intersects(o) for o in occ_back) and not g.intersects(CRYSTAL)


def place_back(ref, tx, ty, rots=(0, 90), maxr=9.0):
    f = fp[ref]
    to_back(f)
    r = 0.0
    while r <= maxr:
        n = max(1, int(2 * math.pi * r / 0.3))
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = round((tx + r * math.cos(a)) / 0.05) * 0.05, round((ty + r * math.sin(a)) / 0.05) * 0.05
            for rot in rots:
                setpos(f, x, y, rot)
                g = bbox(f)
                if free_back(g, x, y):
                    occ_back.append(g)
                    return tomm(f.GetPosition().x), tomm(f.GetPosition().y), rot
        r += 0.15
    raise RuntimeError("no room for " + ref)


log = []
if opt == "D":
    occ_back[:] = [box(95.0, 95.0, 105.0, 105.0), box(92, 79.5, 108, 94.5), box(92, 105.5, 108, 120.5)]       # piezo, upper cell, lower cell (16 x 15)
    log.append(("J1", place_back("J1", 82.0, 100.0, rots=(90,))))
    log.append(("J1B", place_back("J1B", 118.0, 100.0, rots=(270,))))
    log.append(("U4", place_back("U4", 88.5, 100.0, rots=(0,))))
    log.append(("L2", place_back("L2", 88.5, 94.8, rots=(0,))))
    log.append(("L1", place_back("L1", 88.5, 105.2, rots=(0,))))
if opt == "C":
    to_back(fp["U2"])
    setpos(fp["U2"], 100.0, 108.9, 0)
    occ_back.append(bbox(fp["U2"], 0.3))
# --- decoupling next to the pins (back, straight under the pin pair)
if opt == "D":
    setpos(fp["C30"], 98.8, 107.15, 0)            # IMU caps stay on the front, right beside U2
    setpos(fp["C31"], 101.2, 107.15, 0)
else:
    log.append(("C11", place_back("C11", 98.4, 95.4)))
    log.append(("C12", place_back("C12", 103.7, 92.4, rots=(90,))))
    log.append(("C30", place_back("C30", 98.4, 108.9, rots=(90,))))
    log.append(("C31", place_back("C31", 101.6, 108.9, rots=(90,))))
# --- BQ25570 support parts around U4
u4 = fp["U4"]
U4X, U4Y = tomm(u4.GetPosition().x), tomm(u4.GetPosition().y)
pads = [(p.GetNetname(), tomm(p.GetPosition().x), tomm(p.GetPosition().y)) for p in u4.Pads()]
for ref in ("C52", "C53", "C50", "C54", "C51", "R50", "R51", "R52", "R53", "R54", "R55", "R56"):
    nets = {p.GetNetname() for p in fp[ref].Pads()} - {"GND"}
    pts = [(x, y) for n, x, y in pads if n in nets and n != "GND"]
    if not pts:
        pts = [(100, 100)]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    d = math.hypot(cx - U4X, cy - U4Y) or 1
    log.append((ref, place_back(ref, cx + (cx - U4X) / d * 2.2, cy + (cy - U4Y) / d * 2.2)))

# --- new buzzer parts
def new_fp(ref, value, lib, name, side_back, x, y, rot):
    f = pcbnew.FootprintLoad(LIB + lib, name)
    f.SetReference(ref)
    f.SetValue(value)
    b.Add(f)
    if side_back:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    setpos(f, x, y, rot)
    fp[ref] = f
    return f


def generic_buzzer(ref, value, w, h, padw, padh, padx, x, y, back):
    f = pcbnew.FOOTPRINT(b)
    f.SetReference(ref)
    f.SetValue(value)
    for i, sx in enumerate((-1, 1)):
        p = pcbnew.PAD(f)
        p.SetNumber(str(i + 1))
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetLayerSet(p.SMDMask())
        p.SetSize(pcbnew.VECTOR2I(mm(padw), mm(padh)))
        p.SetPosition(pcbnew.VECTOR2I(mm(sx * padx), 0))
        f.Add(p)
    for lay in (pcbnew.F_CrtYd, pcbnew.F_SilkS):
        s = pcbnew.PCB_SHAPE(f)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(mm(-w / 2), mm(-h / 2)))
        s.SetEnd(pcbnew.VECTOR2I(mm(w / 2), mm(h / 2)))
        s.SetLayer(lay)
        s.SetWidth(mm(0.05 if lay == pcbnew.F_CrtYd else 0.12))
        f.Add(s)
    b.Add(f)
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    if back:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp[ref] = f
    return f



def place_j2():
    """J2 (Tag-Connect) to the back: pads clear of back parts, its 3 alignment holes clear of every front pad, the solar cell body and the buzzer pocket"""
    j = fp["J2"]
    to_back(j)
    front = []
    for ref, f in fp.items():
        if ref == "J2" or f.IsFlipped():
            continue
        for p in f.Pads():
            r = p.GetBoundingBox()
            front.append(box(tomm(r.GetX()) - 0.35, tomm(r.GetY()) - 0.35, tomm(r.GetX() + r.GetWidth()) + 0.35, tomm(r.GetY() + r.GetHeight()) + 0.35))
    for ref in ("SW1", "SW2", "U1", "U2", "Y1"):
        r = fp[ref].GetBoundingBox(False)
        front.append(box(tomm(r.GetX()) - 0.3, tomm(r.GetY()) - 0.3, tomm(r.GetX() + r.GetWidth()) + 0.3, tomm(r.GetY() + r.GetHeight()) + 0.3))
    front.append(box(92.6 - 3.2, 92.3 - 3.2, 92.6 + 3.2, 92.3 + 3.2))   # buzzer pocket (option A)
    best = None
    for rot in (0, 90, 180, 270):
        j.SetOrientationDegrees(rot)
        for xi in range(860, 1141, 5):
            for yi in range(860, 1141, 5):
                x, y = xi / 10, yi / 10
                j.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                ok = True
                for p in j.Pads():
                    r = p.GetBoundingBox()
                    g = box(tomm(r.GetX()) - 0.3, tomm(r.GetY()) - 0.3, tomm(r.GetX() + r.GetWidth()) + 0.3, tomm(r.GetY() + r.GetHeight()) + 0.3)
                    cxm, cym = (g.r[0] + g.r[2]) / 2, (g.r[1] + g.r[3]) / 2
                    if math.hypot(cxm - 100, cym - 100) > 20.0 or not free_back(g, cxm, cym):
                        ok = False
                        break
                    if p.GetDrillSizeX() > 0 and any(g.intersects(o) for o in front):
                        ok = False
                        break
                if ok:
                    dd = math.hypot(x - 100, y - 92)
                    if best is None or dd < best[0]:
                        best = (dd, x, y, rot)
    if best is None:
        raise RuntimeError("no place for J2")
    _, x, y, rot = best
    setpos(j, x, y, rot)
    for p in j.Pads():
        r = p.GetBoundingBox()
        occ_back.append(box(tomm(r.GetX()) - 0.3, tomm(r.GetY()) - 0.3, tomm(r.GetX() + r.GetWidth()) + 0.3, tomm(r.GetY() + r.GetHeight()) + 0.3))
    log.append(("J2", (x, y, rot)))


if opt == "D":
    generic_buzzer("BZ1", "9x9 piezo PKMCS0909E4000-R1, PLACEHOLDER pads", 9.4, 9.4, 3.2, 3.2, 4.1, 100.0, 100.0, True)
    marks = ["BZ1", "IND7"]
elif opt == "C":
    # 5x5 buzzer between the buttons (front), U2 on the back, buttons nudged 0.7 mm apart
    setpos(fp["SW1"], tomm(fp["SW1"].GetPosition().x) - 0.7, tomm(fp["SW1"].GetPosition().y), fp["SW1"].GetOrientationDegrees())
    setpos(fp["SW2"], tomm(fp["SW2"].GetPosition().x) + 0.7, tomm(fp["SW2"].GetPosition().y), fp["SW2"].GetOrientationDegrees())
    generic_buzzer("BZ1", "5x5 magnetic buzzer (FUET-5020 class), PLACEHOLDER pads", 5.4, 5.4, 1.4, 2.2, 2.0, 100.0, 109.3, False)
    for ref, val, lib, name, tx, ty in (("Q1", "N-MOSFET logic level SOT-23", "Package_TO_SOT_SMD.pretty", "SOT-23", 104.0, 112.5), ("D1", "Schottky flyback SOD-123", "Diode_SMD.pretty", "D_SOD-123", 107.0, 111.0), ("R60", "100k gate pull-down", "Resistor_SMD.pretty", "R_0402_1005Metric", 101.5, 113.0)):
        new_fp(ref, val, lib, name, True, 0, 0, 0)
        log.append((ref, place_back(ref, tx, ty)))
    marks = ["BZ1", "Q1", "D1", "R60", "U2"]
elif opt == "A":
    # programming pads and the 22 uF are out of the left pocket (J2 -> back, nothing else on the front there)
    place_j2()
    generic_buzzer("BZ1", "5x5 magnetic buzzer (FUET-5020 class), PLACEHOLDER pads", 5.4, 5.4, 1.4, 2.2, 2.0, 92.6, 92.3, False)
    q = new_fp("Q1", "N-MOSFET logic level SOT-23", "Package_TO_SOT_SMD.pretty", "SOT-23", True, 91.0, 94.6, 0)
    d1 = new_fp("D1", "Schottky flyback SOD-123", "Diode_SMD.pretty", "D_SOD-123", True, 94.2, 94.4, 0)
    r = new_fp("R60", "100k gate pull-down", "Resistor_SMD.pretty", "R_0402_1005Metric", True, 92.8, 96.4, 0)
    for ref, sub in (("Q1", 0), ("D1", 0), ("R60", 0)):
        occ_back.append(bbox(fp[ref], 0.3))
    marks = ["BZ1", "Q1", "D1", "R60"]
else:
    generic_buzzer("BZ1", "9x9 piezo PKMCS0909E4000-R1, PLACEHOLDER pads", 9.4, 9.4, 3.2, 3.2, 4.1, 101.0, 114.2, True)
    occ_back.append(box(101.0 - 4.9, 114.2 - 4.9, 101.0 + 4.9, 114.2 + 4.9))
    marks = ["BZ1"]
    to_back(fp["C54"]) if not fp["C54"].IsFlipped() else None

if opt == "D":
    # LiPo outlines (User.2): 16.66 x 16.16 mm, moved apart so a 9.4 mm piezo fits between them (10 mm gap)
    rects = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.User_2 and d.GetClass() == "PCB_SHAPE"]
    for d in rects:
        bb = d.GetBoundingBox()
        up = tomm(bb.GetY()) < 100
        y0, y1 = (78.84, 95.0) if up else (105.0, 121.16)
        d.SetStart(pcbnew.VECTOR2I(mm(91.67), mm(y0)))
        d.SetEnd(pcbnew.VECTOR2I(mm(108.33), mm(y1)))
    # 7th indicator: ALM after TMR  (SET TMR ALM BAT FUN CFG LCK), 3.4 mm pitch centred on x=100
    ind6 = fp["IND6"]
    ind7 = pcbnew.Cast_to_FOOTPRINT(ind6.Duplicate(False))
    ind7.SetReference("IND7")
    b.Add(ind7)
    for pd in ind7.Pads():
        pd.SetNet(b.FindNet("/ROW11" if pd.GetNumber() == "1" else "/COL6"))
    fp["IND7"] = ind7
    order = ["IND1", "IND2", "IND7", "IND3", "IND4", "IND5", "IND6"]
    names = ["SET", "TMR", "ALM", "BAT", "FUN", "CFG", "LCK"]
    texts = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetText() in ("SET", "TMR", "BAT", "FUN", "CFG", "LCK")]
    tmpl = texts[0]
    alm = pcbnew.PCB_TEXT(b)
    alm.SetText("ALM")
    alm.SetLayer(tmpl.GetLayer())
    alm.SetTextSize(tmpl.GetTextSize())
    alm.SetTextThickness(tmpl.GetTextThickness())
    b.Add(alm)
    texts.append(alm)
    byname = {t.GetText(): t for t in texts}
    for k, (r, nm) in enumerate(zip(order, names)):
        x = 100.0 + (k - 3) * 3.4
        setpos(fp[r], x, 104.82, 0)
        byname[nm].SetPosition(pcbnew.VECTOR2I(mm(x), mm(106.04)))
en = b.GetEnabledLayers()
en.AddLayer(pcbnew.User_9)
b.SetEnabledLayers(en)
b.SetLayerName(pcbnew.User_9, "MARK_BUZZER_new_parts")
for ref in marks:
    f = fp[ref]
    g = bbox(f, 0.0).r
    c = pcbnew.VECTOR2I(mm((g[0] + g[2]) / 2), mm((g[1] + g[3]) / 2))
    rad = mm(math.hypot(g[2] - g[0], g[3] - g[1]) / 2 + 0.35)
    s = pcbnew.PCB_SHAPE(f)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetStart(c)
    s.SetEnd(pcbnew.VECTOR2I(c.x + int(rad), c.y))
    s.SetLayer(pcbnew.User_9)
    s.SetWidth(mm(0.2))
    s.SetFilled(False)
    f.Add(s)
for ref, (x, y, rot) in log:
    pass
for t in list(b.GetTracks()):
    b.Remove(t)
pcbnew.SaveBoard(dst, b)
print("saved", dst)
for ref, (x, y, rot) in log:
    print("  %-4s -> back (%.2f, %.2f) rot %d" % (ref, x, y, rot))
