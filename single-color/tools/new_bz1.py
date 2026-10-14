"""Replace the placeholder piezo BZ1 by the real Murata PKMCS0909E4000-R1 footprint (from Murata's flyer, 'Dimensions and Land pattern'):
  body 9.0 x 9.0 x 1.9 max; two terminals 3.2 wide on opposite sides; recommended land pattern: 10.0 mm over the outer pad edges, 7.4 mm between the
  inner edges, 3.4 mm long (pad 1.3 x 3.4 at x = +-4.35).  The sound leaves through two slots under the other two edges (keep them open); the small
  vent hole is in the lid.  Tolerance +-0.2 mm.
usage (KiCad python): new_bz1.py in.kicad_pcb out.kicad_pcb [lib.pretty]
The new footprint keeps the old one's position / rotation / side / nets and its User.9 marker ring."""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
old = [f for f in b.GetFootprints() if f.GetReference() == "BZ1"][0]
pos, rot, back = old.GetPosition(), old.GetOrientationDegrees(), old.IsFlipped()
nets = {p.GetNumber(): p.GetNetname() for p in old.Pads()}

f = pcbnew.FOOTPRINT(b)
f.SetFPID(pcbnew.LIB_ID("LEDWatch", "Piezo_Murata_PKMCS0909E4000-R1_9x9mm"))
f.SetReference("BZ1")
f.SetValue("PKMCS0909E4000-R1")
f.SetLibDescription("Murata PKMCS0909E4000-R1 piezo sounder 9x9x1.9, external drive; land pattern per Murata flyer (10.0 / 7.4 / 3.4)")
f.SetAttributes(pcbnew.FP_SMD)
for num, x in (("1", -4.35), ("2", 4.35)):
    p = pcbnew.PAD(f)
    p.SetNumber(num)
    p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetLayerSet(p.SMDMask())
    p.SetSize(pcbnew.VECTOR2I(mm(1.3), mm(3.4)))
    p.SetPosition(pcbnew.VECTOR2I(mm(x), 0))
    f.Add(p)


def rect(layer, x0, y0, x1, y1, w):
    s = pcbnew.PCB_SHAPE(f)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
    s.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    f.Add(s)


def line(layer, x0, y0, x1, y1, w):
    s = pcbnew.PCB_SHAPE(f)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
    s.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    f.Add(s)


rect(pcbnew.F_CrtYd, -5.2, -4.7, 5.2, 4.7, 0.05)                    # courtyard: pads + 0.2, body + 0.2
rect(pcbnew.F_Fab, -4.5, -4.5, 4.5, 4.5, 0.1)                       # body
line(pcbnew.F_SilkS, -3.5, -4.75, 3.5, -4.75, 0.12)                 # silk only along the two slot edges, clear of the pads
line(pcbnew.F_SilkS, -3.5, 4.75, 3.5, 4.75, 0.12)
b.Add(f)
f.SetPosition(pos)
f.SetOrientationDegrees(rot)
if back:
    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(rot)
for p in f.Pads():
    p.SetNet(b.FindNet(nets[p.GetNumber()]))
# marker ring on User.9 (new parts)
ring = pcbnew.PCB_SHAPE(f)
ring.SetShape(pcbnew.SHAPE_T_CIRCLE)
ring.SetStart(pos)
ring.SetEnd(pcbnew.VECTOR2I(pos.x + mm(6.4), pos.y))
ring.SetLayer(pcbnew.User_9)
ring.SetWidth(mm(0.2))
ring.SetFilled(False)
f.Add(ring)
b.Remove(old)
pcbnew.SaveBoard(sys.argv[2], b)
print("BZ1 replaced: pads 1.3 x 3.4 at +-4.35, courtyard 10.4 x 9.4; position (%.2f, %.2f) rot %.0f %s" % (tomm(pos.x), tomm(pos.y), rot, "back" if back else "front"))
