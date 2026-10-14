"""copy position / rotation / side of the listed refs from one board to another.  usage (KiCad python): copy_positions.py src.kicad_pcb dst_in.kicad_pcb dst_out.kicad_pcb ref1,ref2,..."""
import sys

import pcbnew

a = pcbnew.LoadBoard(sys.argv[1])
b = pcbnew.LoadBoard(sys.argv[2])
fa = {f.GetReference(): f for f in a.GetFootprints()}
fb = {f.GetReference(): f for f in b.GetFootprints()}
for r in sys.argv[4].split(","):
    s, d = fa[r], fb[r]
    if s.IsFlipped() != d.IsFlipped():
        d.Flip(d.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    d.SetOrientationDegrees(s.GetOrientationDegrees())
    d.SetPosition(s.GetPosition())
pcbnew.SaveBoard(sys.argv[3], b)
print("copied", len(sys.argv[4].split(",")), "parts")
