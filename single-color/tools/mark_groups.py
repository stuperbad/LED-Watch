"""Tag footprints with a ring on a User layer that moves with the part.  usage (KiCad python): mark_groups.py in.kicad_pcb out.kicad_pcb
User.4 MCU decoupling + crystal, User.5 BQ25570 support parts, User.6 IMU decoupling, User.7 dummy (no-net) parts, User.8 programming pads (J2), User.9 new parts (mock). User.1-3 already hold the solar-cell and LiPo outlines"""
import math
import sys

import pcbnew

GROUPS = {
    pcbnew.User_4: ("MARK_MCU_decoupling_crystal", ["C10", "C11", "C12", "C20", "C21", "Y1"]),
    pcbnew.User_5: ("MARK_BQ25570_support", ["C50", "C51", "C52", "C53", "C54", "R50", "R51", "R52", "R53", "R54", "R55", "R56"]),
    pcbnew.User_6: ("MARK_IMU_decoupling", ["C30", "C31"]),
    pcbnew.User_7: ("MARK_DUMMY_no_net", ["C60", "C61", "C62", "R57", "R58", "R59"]),
    pcbnew.User_8: ("MARK_programming_J2", ["J2"]),
}
b = pcbnew.LoadBoard(sys.argv[1])
en = b.GetEnabledLayers()
for lay, (name, _) in GROUPS.items():
    en.AddLayer(lay)
b.SetEnabledLayers(en)
for lay in GROUPS:
    b.SetLayerVisible(lay, True) if hasattr(b, "SetLayerVisible") else None
byref = {f.GetReference(): f for f in b.GetFootprints()}
n = 0
for lay, (name, refs) in GROUPS.items():
    b.SetLayerName(lay, name)
    for r in refs:
        f = byref[r]
        bb = f.GetBoundingBox(False)
        c = bb.GetCenter()
        rad = math.hypot(bb.GetWidth(), bb.GetHeight()) / 2 + pcbnew.FromMM(0.35)
        s = pcbnew.PCB_SHAPE(f)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetStart(c)
        s.SetEnd(pcbnew.VECTOR2I(c.x + int(rad), c.y))
        s.SetLayer(lay)
        s.SetWidth(pcbnew.FromMM(0.2))
        s.SetFilled(False)
        f.Add(s)
        n += 1
pcbnew.SaveBoard(sys.argv[2], b)
print("marked", n, "footprints")
