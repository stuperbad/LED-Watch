"""Shrink the board to a new diameter by moving every LED-ring part radially inward (angles unchanged) and replacing the outline.
usage (KiCad python): shrink_od.py in.kicad_pcb out.kicad_pcb new_outline_board.kicad_pcb shift_mm
 ring parts: H/M/S LEDs, column resistors R1-R12, flank/dummy resistors R20 R21 R57-R59 R61-R67
 outline: Edge.Cuts shapes copied from new_outline_board (the planner's board at the new diameter)"""
import math
import re
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
ref_board = pcbnew.LoadBoard(sys.argv[3])
shift = float(sys.argv[4])
ring = re.compile(r"^(H|M|S)\d+$|^R([1-9]|1[0-2])$|^R(20|21|57|58|59|6[1-7])$")
n = 0
for f in b.GetFootprints():
    if ring.match(f.GetReference()):
        p = f.GetPosition()
        x, y = tomm(p.x) - 100.0, tomm(p.y) - 100.0
        r = math.hypot(x, y)
        k = (r - shift) / r
        f.SetPosition(pcbnew.VECTOR2I(mm(100.0 + x * k), mm(100.0 + y * k)))
        n += 1
new_edges = [(d.GetPolyShape(), d.GetWidth()) for d in ref_board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
old_edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
for d in old_edges:
    b.Remove(d)
for poly, w in new_edges:
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyShape(poly)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(w)
    b.Add(s)
pcbnew.SaveBoard(sys.argv[2], b)
print("moved", n, "ring parts inward by", shift, "mm; outline replaced")
