"""cleanup1.py OWNER.pcb DRAFT.pcb OUT.pcb : the cleanup pass on a COPY of the owner's static layout.
1 dangling GND via, 2 C50 / R68 row + shared GND via, 3 R68.1 CC1 exit along the axis, 4 R72.1 SBU via on the pad axis and its two dead spurs, 5 generic chain clean (micro pieces, ends off centre)"""
import sys, math
import pcbnew
from editlib import *
import cleanlib
e = Ed(sys.argv[1]); b = e.b
draft = pcbnew.LoadBoard(sys.argv[2])
dkeys = {cleanlib.key(draft, t) for t in draft.GetTracks() if t.GetClass() == "PCB_TRACK"}
okeys = {cleanlib.key(b, t) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"} - dkeys
print("owner-added pieces:", len(okeys))

def find_via(x, y, tol=0.006):
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and abs(tomm(t.GetPosition().x) - x) < tol and abs(tomm(t.GetPosition().y) - y) < tol: return t
    raise SystemExit("via not found %s" % ((x, y),))

# 1. dangling GND via
e.rm_via((107.715, 92.126))

# 2. C50 onto R68's row, GND via on that row, one straight piece each side
e.move("C50", tomm(e.part("C50").GetPosition().x), 93.37)
find_via(108.95, 93.35).SetPosition(V(108.95, 93.37))
for a, c in [((108.43, 93.36), (108.94, 93.36)), ((108.94, 93.36), (108.95, 93.35)), ((108.97, 93.37), (108.95, 93.35)), ((108.94, 93.36), (108.95, 93.35))]:
    try: e.rm_seg(a, c, "B.Cu")
    except SystemExit: pass
# leftovers of the two pad links (their ends are whatever the owner drew): list what still touches the via or the two GND pads
g1, g2 = e.padxy("C50", 2), e.padxy("R68", 2)
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "GND" and b.GetLayerName(t.GetLayer()) == "B.Cu":
        s, c = (tomm(t.GetStart().x), tomm(t.GetStart().y)), (tomm(t.GetEnd().x), tomm(t.GetEnd().y))
        if 108.3 < s[0] < 109.7 and 93.2 < s[1] < 93.5 and 108.3 < c[0] < 109.7 and 93.2 < c[1] < 93.5:
            b.Remove(t); e.grave.append(t); e.log.append("rm GND link piece %s-%s" % (s, c))
e.poly([g1, (108.95, 93.37)], "GND"); e.poly([g2, (108.95, 93.37)], "GND")

# 3. R68.1 CC1: leave east along the pad axis, 45 degrees south-east, then south into the via at (111.1, 94.01)
p1 = e.padxy("R68", 1); print("R68.1", p1)
for a, c in [((110.51, 93.37), (110.51, 93.69)), ((110.51, 93.69), (110.83, 94.01)), ((110.83, 94.01), (111.1, 94.01))]:
    e.rm_seg(a, c, "B.Cu")
x1 = p1[0] + 0.30; d = 0.29
e.poly([p1, (x1, p1[1]), (x1 + d, p1[1] + d), (x1 + d, 94.01)], "/CC1")
print("CC1 new via approach", (x1 + d, 94.01), "via at (111.1, 94.01)")

# 4. R72.1 SBU: via onto the pad axis, straight piece, two dead spurs removed
via = find_via(109.15, 102.475); via.SetPosition(V(109.2, 102.475))
for a, c in [((109.15, 101.86), (109.15, 102.475)), ((109.15, 102.51), (109.17, 102.53)), ((109.15, 102.475), (109.195, 102.475)), ((109.195, 102.475), (109.21, 102.49)), ((109.15, 102.475), (109.15, 102.51))]:
    e.rm_seg(a, c, "B.Cu")
e.rm_seg((109.485, 102.475), (109.15, 102.475), "In1.Cu")
e.poly([e.padxy("R72", 1), (109.2, 102.475)], "/SBU")
e.poly([(109.485, 102.475), (109.2, 102.475)], "/SBU", "In1.Cu")

# 5. generic: micro pieces and ends off a pad / via centre, only chains with owner pieces, only inside the corner
rep, grave = cleanlib.clean_chains(b, okeys, (103.0, 89.0, 113.6, 108.5), skip={('/COL3_MCU', 'F.Cu')}, skip_ends={(112.37, 98.25)}); e.grave += grave
for r in rep: print(r)

# 6. SBU jitter the generic pass must not touch (it sits 0.2 mm hole-clearance tight against the CC1 via): done as two local edits
#    (a) three pieces at x = 110.923 / 110.925 -> one vertical at x = 110.925, the lower 45 degree piece meets it exactly
for a, c2 in [((110.923, 96.823), (110.923, 95.993)), ((110.923, 95.993), (110.925, 95.991)), ((110.925, 95.991), (110.925, 95.509)), ((111.34, 97.24), (110.923, 96.823))]:
    e.rm_seg(a, c2, "B.Cu")
e.poly([(111.34, 97.24), (110.925, 96.825), (110.925, 95.509)], "/SBU")      # x = 110.925 is the upper piece's own x: it is exactly 0.325 mm from the CC1 via, the hole-clearance limit
#    (b) the via end: move the vertical onto the via centre x = 109.7, the 45 degree piece before it meets it at (109.7, 95.8)
for a, c2 in [((110.15, 95.35), (109.72, 95.78)), ((109.72, 95.78), (109.72, 95.92)), ((109.72, 95.92), (109.7, 95.94))]:
    e.rm_seg(a, c2, "B.Cu")
e.poly([(110.15, 95.35), (109.7, 95.8), (109.7, 95.94)], "/SBU")

pcbnew.SaveBoard(sys.argv[3], b)
print("\n".join(e.log[-30:]))
