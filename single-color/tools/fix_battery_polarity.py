"""Swap the battery plugs' polarity: J1 / J1B pin 1 = GND, pin 2 = battery + (BATT), as on TinyCircuits' own boards (see docs/PRE-ORDER-REVIEW-2026-10-18.md, section 7).
Local rework of the B.Cu stubs around the two plugs, plus "+" / "-" marks on the back silkscreen.
usage (KiCad python): fix_battery_polarity.py in.kicad_pcb out.kicad_pcb       (run fix_gnd_zone.py afterwards)"""
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
C = 100.0                                                   # board centre in KiCad coordinates
V = pcbnew.VECTOR2I


def pt(x, y):
    return V(mm(C + x), mm(C + y))


def same(a, x, y, tol=0.02):
    return abs(tomm(a.x) - C - x) < tol and abs(tomm(a.y) - C - y) < tol


# --- 1. the pads
for ref in ("J1", "J1B"):
    f = [x for x in b.GetFootprints() if x.GetReference() == ref][0]
    for p in f.Pads():
        if p.GetNumber() == "1":
            p.SetNet(b.FindNet("GND"))
        elif p.GetNumber() == "2":
            p.SetNet(b.FindNet("/BATT"))

# --- 2. the old stubs (net, layer B.Cu, end points) are removed
OLD = [("/BATT", (-15.2, -8.4), (-16.54, -8.4)), ("/BATT", (-16.54, -8.4), (-17.42, -7.52)),
       ("GND", (-15.2, -7.4), (-14.51, -7.4)), ("GND", (-14.51, -7.4), (-14.22, -7.11)),
       ("/BATT", (-16.38, 7.62), (-15.5, 8.5)),
       ("GND", (-15.5, 9.5), (-15.29, 9.5)), ("GND", (-15.29, 9.5), (-14.47, 8.69))]
# the ground via next to J1 pad 2 (now battery +) moves next to pad 1 (now ground), 0.2 mm from a battery pad is too close
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND" and same(t.GetPosition(), -14.22, -7.11):
        t.SetPosition(pt(-14.0, -8.5))
        break
else:
    raise SystemExit("ground via at (-14.22, -7.11) not found")

kill = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK" or t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    for net, a, c in OLD:
        if t.GetNetname() == net and ((same(s, *a) and same(e, *c)) or (same(s, *c) and same(e, *a))):
            kill.append(t.m_Uuid.AsString())
assert len(kill) == len(OLD), (len(kill), len(OLD))
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in kill:
        b.Remove(t)

# --- 3. the new stubs
NEW = [("/BATT", [(-15.2, -7.4), (-17.42, -7.4), (-17.42, -7.52)]),                      # J1 pad 2 -> the battery trunk
       ("GND", [(-15.2, -8.4), (-14.1, -8.4), (-14.0, -8.5)]),                           # J1 pad 1 -> the (moved) ground via
       ("/BATT", [(-15.5, 9.5), (-17.1, 9.5), (-17.1, 7.62), (-16.38, 7.62)]),            # J1B pad 2 -> the battery trunk
       ("GND", [(-15.5, 8.5), (-14.66, 8.5), (-14.47, 8.69)])]                            # J1B pad 1 -> the existing ground stub
for net, pts in NEW:
    for a, c in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pt(*a))
        t.SetEnd(pt(*c))
        t.SetWidth(mm(0.1))
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(b.FindNet(net))
        b.Add(t)

# --- 4. polarity marks on the back silkscreen (mirrored, as everything on the back); "+" next to the battery-plus pad, "-" next to the ground pad
MARKS = [("+", -16.9, -6.2), ("-", -16.9, -9.6), ("+", -17.4, 10.9), ("-", -17.4, 7.1)]
for txt, x, y in MARKS:
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetPosition(pt(x, y))
    t.SetLayer(pcbnew.B_SilkS)
    t.SetTextSize(V(mm(1.0), mm(1.0)))
    t.SetTextThickness(mm(0.15))
    t.SetMirrored(True)
    b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b)
print("polarity swapped on J1 and J1B; wrote", sys.argv[2])
