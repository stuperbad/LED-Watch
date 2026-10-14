"""Move the two buttons (mirror-symmetric) the smallest amount that clears every other part.  usage (KiCad python): nudge_buttons.py in out"""
import math
import sys

import pcbnew
from plc import *

b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
s1, s2 = fp["SW1"], fp["SW2"]
x0, y0 = tomm(s1.GetPosition().x), tomm(s1.GetPosition().y)
best = None
for dxi in range(0, 31):
    for dyi in range(0, 21):
        dx, dy = dxi * 0.05, -dyi * 0.05
        place(s1, x0 + dx, y0 + dy, 0)
        place(s2, 200 - (x0 + dx), y0 + dy, 0)
        if conflicts(fp, "SW1", [SOLAR_BODY], [], 0.25) or conflicts(fp, "SW2", [SOLAR_BODY], [], 0.25):
            continue
        d = math.hypot(dx, dy)
        if best is None or d < best[0]:
            best = (d, dx, dy)
d, dx, dy = best
place(s1, x0 + dx, y0 + dy, 0)
place(s2, 200 - (x0 + dx), y0 + dy, 0)
print("buttons: SW1 (%.2f, %.2f) -> (%.2f, %.2f); SW2 mirrored; moved %.2f mm (inward %.2f, up %.2f)" % (x0, y0, x0 + dx, y0 + dy, d, dx, -dy))
pcbnew.SaveBoard(sys.argv[2], b)
