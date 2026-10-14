"""Fill the front slots that real parts vacated (filigree symmetry) with no-net dummy parts, and tag parts that moved front->back.
usage (KiCad python): add_dummies.py base.kicad_pcb final.kicad_pcb out.kicad_pcb
 - base = the working board (parts already moved), final = Y43_final (original front positions)
 - dummies: 0402 cap slots -> '100n' (C63..), 0402 resistor slots -> '10k' (R61..), same BOM lines as the real C10 / R20 parts; ring on User.7
 - parts that are on the BACK in base but on the FRONT in final get a ring on User.10 (MARK_moved_front_to_back)
Idempotent: skips if C63 already exists."""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
base = pcbnew.LoadBoard(sys.argv[1])
fin = pcbnew.LoadBoard(sys.argv[2])
bf = {f.GetReference(): f for f in base.GetFootprints()}
ff = {f.GetReference(): f for f in fin.GetFootprints()}
if "C63" in bf:
    raise SystemExit("dummies already present")
en = base.GetEnabledLayers()
en.AddLayer(pcbnew.User_10)
base.SetEnabledLayers(en)
base.SetLayerName(pcbnew.User_10, "MARK_moved_front_to_back")


def ring(f, layer, extra=0.0):
    xs0, ys0, xs1, ys1 = [], [], [], []
    for p in f.Pads():
        r = p.GetBoundingBox()
        xs0.append(r.GetX()); ys0.append(r.GetY()); xs1.append(r.GetRight()); ys1.append(r.GetBottom())
    cx, cy = (min(xs0) + max(xs1)) // 2, (min(ys0) + max(ys1)) // 2
    rad = int(math.hypot(max(xs1) - min(xs0), max(ys1) - min(ys0)) / 2) + mm(0.35 + extra)
    s = pcbnew.PCB_SHAPE(f)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetStart(pcbnew.VECTOR2I(cx, cy))
    s.SetEnd(pcbnew.VECTOR2I(cx + rad, cy))
    s.SetLayer(layer)
    s.SetWidth(mm(0.2))
    s.SetFilled(False)
    f.Add(s)


# 1) tag the parts that moved front -> back
moved = [r for r, f in bf.items() if f.IsFlipped() and r in ff and not ff[r].IsFlipped()]
for r in moved:
    ring(bf[r], pcbnew.User_10, 0.45)
print("moved front->back:", sorted(moved))

# 2) dummies in the vacated front slots (C54's 0805 slot is the programming-pad pocket: skipped)
slots = [r for r in moved if r != "C54"] + [r for r in ("C30", "C31") if r in bf and not bf[r].IsFlipped() and
        math.hypot(tomm(bf[r].GetPosition().x) - tomm(ff[r].GetPosition().x), tomm(bf[r].GetPosition().y) - tomm(ff[r].GetPosition().y)) > 3]
ic, ir = 63, 61
made = []
for r in sorted(slots, key=lambda s: (s[0], int(s[1:]))):
    src = ff[r]
    d = pcbnew.Cast_to_FOOTPRINT(src.Duplicate(False))
    if r[0] == "C":
        ref, val = "C%d" % ic, "100n"
        ic += 1
    else:
        ref, val = "R%d" % ir, "10k"
        ir += 1
    d.SetReference(ref)
    d.SetValue(val)
    for p in d.Pads():
        p.SetNetCode(0)
    base.Add(d)
    ring(d, pcbnew.User_7)
    made.append((ref, r))
print("dummies:", ", ".join("%s (slot of %s)" % m for m in made))
pcbnew.SaveBoard(sys.argv[3], base)
