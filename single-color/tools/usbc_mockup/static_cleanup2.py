"""cleanup2.py MAIN.pcb PASS1.pcb OUT.pcb : second cleanup pass directly on the main board.
Explicit: C54.1 (+3V3) and R69.2 (GND) leave their pads along the part axis. Generic: chains the owner changed after pass 1 (micro pieces, ends off a pad / via centre, U5.4 ISET end)."""
import sys, math
import pcbnew
from editlib import *
import cleanlib

e = Ed(sys.argv[1]); b = e.b
p1 = pcbnew.LoadBoard(sys.argv[2])
k1 = {cleanlib.key(p1, t) for t in p1.GetTracks() if t.GetClass() == "PCB_TRACK"}
okeys = {cleanlib.key(b, t) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"} - k1
print("pieces changed since pass 1:", len(okeys))

# 1. C54.1 +3V3: north out of the pad end (pad spans y 99.15 - 100.15), west along y = 98.95 to the +3V3 vertical at x = 103.125 (T junction at a vertex)
s = e.padxy("C54", 1)
for a, c in [((104.05, 99.65), (103.13, 98.73)), ((103.13, 98.73), (103.13, 98.72)), ((103.125, 98.725), (103.13, 98.72)), ((103.13, 98.72), (102.203, 98.72)), ((103.125, 100.285), (103.125, 98.725))]:
    e.rm_seg(a, c, "B.Cu")
e.poly([s, (s[0], 98.95), (103.125, 98.95)], "+3V3")
e.poly([(103.125, 100.285), (103.125, 98.95), (103.125, 98.72), (102.203, 98.72)], "+3V3")

# 2. R69.2 GND: left as the owner drew it. A north exit needs the corridor between the +3V3 piece (y 97.37) and the VBUS diagonal, which is 0.1 mm wide after clearances, and a dog-bone via cannot go there (the solar cell pad SC1+ covers x >= 109.5 on F.Cu).

# 3. generic chains (owner's pieces changed after pass 1)
rep, grave = cleanlib.clean_chains(b, okeys, (103.0, 89.0, 113.6, 108.5), skip={('/COL3_MCU', 'F.Cu')}, skip_ends={(112.37, 98.25)}); e.grave += grave
for r in rep: print(r)

# 4. VBUS at U5.6: the pad centre is at y = 103.56 (U5 moved 0.01 in y), the horizontal and the junction at x = 111.15 sat at 103.55: move the junction onto 103.56 (all pieces at it are straight, none changes direction)
for a, c in [((110.13, 103.56), (110.14, 103.55)), ((110.14, 103.55), (111.15, 103.55)), ((111.15, 102.95), (111.15, 103.55)), ((111.15, 103.55), (111.15, 103.85))]:
    e.rm_seg(a, c, "B.Cu")
e.poly([(110.13, 103.56), (111.15, 103.56)], "VBUS"); e.poly([(111.15, 102.95), (111.15, 103.56), (111.15, 103.85)], "VBUS")

pcbnew.SaveBoard(sys.argv[3], b)
print("\n".join(e.log))
