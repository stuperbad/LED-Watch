"""After shrink_od.py: put the flank/ornament resistors back at the SAME lateral offset from their hour LED (translate along the hour axis instead of their own radial).
usage (KiCad python): fix_flank.py in.kicad_pcb out.kicad_pcb shift_mm"""
import math
import re
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
shift = float(sys.argv[3])
flank = re.compile(r"^R(20|21|57|58|59|6[1-7])$")
for f in b.GetFootprints():
    if flank.match(f.GetReference()):
        p = f.GetPosition()
        x, y = tomm(p.x) - 100, tomm(p.y) - 100
        r = math.hypot(x, y)
        r0 = r + shift                                              # undo the radial shift
        ox, oy = x * r0 / r, y * r0 / r
        ang = math.degrees(math.atan2(ox, -oy)) % 360               # clock angle of the original position
        hour = round(ang / 30.0) * 30.0
        hx, hy = math.sin(math.radians(hour)), -math.cos(math.radians(hour))
        nx, ny = ox - shift * hx, oy - shift * hy
        f.SetPosition(pcbnew.VECTOR2I(mm(100 + nx), mm(100 + ny)))
        print(f.GetReference(), "hour axis %3d  moved (%.2f, %.2f) -> (%.2f, %.2f)" % (hour, x, y, nx, ny))
pcbnew.SaveBoard(sys.argv[2], b)
