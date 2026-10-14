"""Put the two LiPo outlines (User.2) back to the original positions (y 80.5-96.5 / 103.5-119.5, x 91.75-108.25) - the piezo is no longer between them."""
import sys

import pcbnew

mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for d in b.GetDrawings():
    if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.User_2:
        up = pcbnew.ToMM(d.GetBoundingBox().GetY()) < 100
        y0, y1 = (80.5, 96.5) if up else (103.5, 119.5)
        d.SetStart(pcbnew.VECTOR2I(mm(91.75), mm(y0)))
        d.SetEnd(pcbnew.VECTOR2I(mm(108.25), mm(y1)))
        n += 1
pcbnew.SaveBoard(sys.argv[2], b)
print("restored", n, "outlines")
