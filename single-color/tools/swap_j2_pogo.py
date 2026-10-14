"""Replace the Tag-Connect J2 by a 1x4 UPDI pogo pad row (1.27 mm pitch, Microchip 'UPDI connection v2' order RESET, VDD, GND, UPDI) + 2 plated 0.3 mm guide holes.
usage (KiCad python): swap_j2_pogo.py in.kicad_pcb out.kicad_pcb [cx cy [rot [holes]]]   (default: 0 deg, no guide holes)     RESET goes to U1 pad 40 (PF6)."""
import math
import sys

import pcbnew

mm = pcbnew.FromMM
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
cx0, cy0 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (92.6, 92.6)
ROTS = [int(sys.argv[5])] if len(sys.argv) > 5 else [0]
HOLES = len(sys.argv) > 6 and sys.argv[6] == "holes"
fp = {f.GetReference(): f for f in b.GetFootprints()}
j = fp["J2"]
old_pads = list(j.Pads())
old_gfx = list(j.GraphicalItems())
for p in old_pads:
    j.Remove(p)
for g in old_gfx:
    j.Remove(g)
j.SetOrientationDegrees(0)
j.SetPosition(pcbnew.VECTOR2I(0, 0))                # build the pads around the origin, move the footprint afterwards
if not b.FindNet("/RESET"):
    b.Add(pcbnew.NETINFO_ITEM(b, "/RESET"))
for p in fp["U1"].Pads():
    if p.GetNumber() == "40":
        p.SetNet(b.FindNet("/RESET"))
for num, x, net in (("1", -1.905, "/RESET"), ("2", -0.635, "VBAT"), ("3", 0.635, "GND"), ("4", 1.905, "/UPDI")):
    p = pcbnew.PAD(j)
    p.SetNumber(num)
    p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetLayerSet(p.SMDMask())
    p.SetSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    p.SetPosition(pcbnew.VECTOR2I(mm(x), 0))
    p.SetNet(b.FindNet(net))
    j.Add(p)
for num, x in (("5", -3.175), ("6", 3.175)) if HOLES else ():
    p = pcbnew.PAD(j)
    p.SetNumber("")
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetLayerSet(p.PTHMask())
    p.SetSize(pcbnew.VECTOR2I(mm(0.7), mm(0.7)))
    p.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
    p.SetPosition(pcbnew.VECTOR2I(mm(x), 0))
    j.Add(p)
s = pcbnew.PCB_SHAPE(j)
s.SetShape(pcbnew.SHAPE_T_RECT)
s.SetStart(pcbnew.VECTOR2I(mm(-3.81), mm(-0.9)))
s.SetEnd(pcbnew.VECTOR2I(mm(3.81), mm(0.9)))
s.SetLayer(pcbnew.F_SilkS)
s.SetWidth(mm(0.12))
j.Add(s)
j.SetValue("UPDI pogo row 1.27 mm: RESET VDD GND UPDI")

# ---- find a spot on the FRONT near the old J2 where pads and guide holes clear every other front pad
front = []
for ref, f in fp.items():
    if ref == "J2" or f.IsFlipped():
        continue
    boxes = [p.GetBoundingBox() for p in f.Pads()]
    if ref in ("U1", "U2", "SW1", "SW2", "Y1"):
        boxes = [f.GetBoundingBox(False)]
    for r in boxes:
        front.append((tomm(r.GetX()) - 0.4, tomm(r.GetY()) - 0.4, tomm(r.GetRight()) + 0.4, tomm(r.GetBottom()) + 0.4))
front.append((88.4, 95.9, 111.6, 104.1))                       # solar cell body
front.append((104.75, 89.25, 109.25, 94.65))                   # crystal guard
best = (0, cx0, cy0, ROTS[0]) if (len(sys.argv) > 7 and sys.argv[7] == "force") else None
for rot in ([] if best else ROTS):
    j.SetOrientationDegrees(rot)
    for xi in range(int((cx0 - 5) * 20), int((cx0 + 5) * 20), 1):
        for yi in range(int((cy0 - 5) * 20), int((cy0 + 5) * 20), 1):
            x, y = xi / 20, yi / 20
            if math.hypot(x - 100, y - 100) > 17.5:
                continue
            j.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            ok = True
            for p in j.Pads():
                r = p.GetBoundingBox()
                g = (tomm(r.GetX()) - 0.3, tomm(r.GetY()) - 0.3, tomm(r.GetRight()) + 0.3, tomm(r.GetBottom()) + 0.3)
                if any(g[0] < o[2] and o[0] < g[2] and g[1] < o[3] and o[1] < g[3] for o in front):
                    ok = False
                    break
            if ok:
                d = math.hypot(x - cx0, y - cy0) + 0.002 * rot
                if best is None or d < best[0]:
                    best = (d, x, y, rot)
if best is None:
    raise SystemExit("no front spot found")
_, x, y, rot = best
j.SetOrientationDegrees(rot)
j.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
# marker ring (User.8)
rr = mm(4.2)
m = pcbnew.PCB_SHAPE(j)
m.SetShape(pcbnew.SHAPE_T_CIRCLE)
m.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
m.SetEnd(pcbnew.VECTOR2I(mm(x) + rr, mm(y)))
m.SetLayer(pcbnew.User_8)
m.SetWidth(mm(0.2))
m.SetFilled(False)
j.Add(m)
pcbnew.SaveBoard(sys.argv[2], b)
print("J2 pogo row on the front at (%.1f, %.1f) rot %d" % (x, y, rot))
