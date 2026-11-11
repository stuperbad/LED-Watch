"""rework_verify.py BOARD DETAIL.json POS.json (KiCad python) : do the pad centres of the moved parts match what place_view / placelib predicted?"""
import sys, json, math, pcbnew
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0] if False else ".")
from placelib import Lib
b = pcbnew.LoadBoard(sys.argv[1]); L = Lib(sys.argv[2]); POS = json.load(open(sys.argv[3])); mm = pcbnew.ToMM; bad = 0
for r, p in POS.items():
    if r not in L.D: continue
    f = b.FindFootprintByReference(r); pads, _ = L.place(r, p)
    for n, net, x, y, hx, hy in pads:
        act = [(mm(q.GetPosition().x), mm(q.GetPosition().y)) for q in f.Pads() if q.GetNumber() == n]
        if not any(math.hypot(x - ax, y - ay) < 0.01 for ax, ay in act): bad += 1; print("MISMATCH", r, n, (round(x, 3), round(y, 3)), [(round(a, 3), round(c, 3)) for a, c in act])
print("pad mismatches:", bad)
