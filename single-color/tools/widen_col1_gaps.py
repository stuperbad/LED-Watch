"""Widen the 0.100 mm gaps where /COL1 runs between /BUZ_A (left) and /BUZ_B (right) on the back copper (JLCDFM marks 0.1 mm as danger):
BUZ_A's vertical stretch moves 0.05 mm left, BUZ_B's 0.05 mm right (vertex moves only, so every joint stays connected).
usage (KiCad python): widen_col1_gaps.py in.kicad_pcb out.kicad_pcb"""
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
C = 100.0


def pt(x, y):
    return pcbnew.VECTOR2I(mm(C + x), mm(C + y))


def at(p, x, y, tol=0.01):
    return abs(tomm(p.x) - C - x) < tol and abs(tomm(p.y) - C - y) < tol


MOVES = {"/BUZ_A": [((-7.125, -13.215), (-7.175, -13.215)), ((-7.125, -8.515), (-7.175, -8.515))],
         "/BUZ_B": [((-6.725, -9.665), (-6.675, -9.665)), ((-6.725, -8.349), (-6.675, -8.349)), ((-6.875, -8.199), (-6.825, -8.199))]}
n = 0
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK" or t.GetLayer() != pcbnew.B_Cu or t.GetNetname() not in MOVES:
        continue
    for old, new in MOVES[t.GetNetname()]:
        if at(t.GetStart(), *old):
            t.SetStart(pt(*new)); n += 1
        if at(t.GetEnd(), *old):
            t.SetEnd(pt(*new)); n += 1
print("moved", n, "track ends (expected 12)")
pcbnew.SaveBoard(sys.argv[2], b)
