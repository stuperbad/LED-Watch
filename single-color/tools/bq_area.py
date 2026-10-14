"""Place the BQ25570 support parts + both inductors on the back around U4, choosing U4's rotation by total weighted pin distance.
usage (KiCad python): bq_area.py in.kicad_pcb out.kicad_pcb"""
import math
import sys

import pcbnew
from plc import *

b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
U4 = fp["U4"]
PARTS = [("L1", 3.0), ("L2", 3.0), ("C52", 3.0), ("C53", 3.0), ("C50", 2.5), ("C54", 2.5), ("C51", 1.5),
         ("R50", 1.0), ("R51", 1.0), ("R52", 1.0), ("R53", 1.0), ("R54", 1.0), ("R55", 1.0), ("R56", 1.0)]
NAMES = [p for p, _ in PARTS]
X0, X1, Y0, Y1 = 90.0, 113.6, 94.0, 106.0
GUARD = None
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.F_Cu:
        bb = z.GetBoundingBox()
        GUARD = (tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom()))


def run(urot):
    place(U4, 100.0, 100.0, urot)
    upins = {}
    for p in U4.Pads():
        if p.GetNetname() and p.GetNetname() != "GND":
            upins.setdefault(p.GetNetname(), []).append((tomm(p.GetPosition().x), tomm(p.GetPosition().y)))
    obs = []
    for ref, g in fp.items():
        if ref in NAMES or not g.IsFlipped() and not any(pb[4] for pb in pad_boxes(g)):
            continue
        for a_ in pad_boxes(g):
            if g.IsFlipped() or a_[4]:
                obs.append(a_[:4])
    obs += list(CELLS) + ([GUARD] if GUARD else [])
    placed = []
    total = 0.0
    for ref, w in PARTS:
        f = fp[ref]
        set_side(f, True)
        cands = []
        for rot in (0, 90, 180, 270):
            place(f, 0.0, 0.0, rot)
            offs = [(p.GetNetname(), tomm(p.GetPosition().x), tomm(p.GetPosition().y)) for p in f.Pads()]
            rel = [pb[:4] for pb in pad_boxes(f)]
            for xi in range(int(X0 * 5), int(X1 * 5)):
                for yi in range(int(Y0 * 5), int(Y1 * 5)):
                    x, y = xi / 5, yi / 5
                    d = 0.0
                    for net, dx, dy in offs:
                        if net in upins:
                            d += min(math.hypot(x + dx - ux, y + dy - uy) for ux, uy in upins[net])
                    cands.append((d * w, rot, x, y, rel))
        cands.sort(key=lambda c: c[0])
        ok = False
        for d, rot, x, y, rel in cands:
            boxes = [(r[0] + x, r[1] + y, r[2] + x, r[3] + y) for r in rel]
            if any(inter(bx, o, 0.3) for bx in boxes for o in obs):
                continue
            place(f, x, y, rot)
            if conflicts(fp, ref, [], [GUARD] if GUARD else [], 0.3):
                continue
            obs += boxes
            placed.append((ref, x, y, rot, d / w))
            total += d
            ok = True
            break
        if not ok:
            return 1e9, placed
    return total, placed


best = None
for urot in (0, 90, 180, 270):
    t, pl = run(urot)
    print("U4 rot %3d: weighted distance %.1f" % (urot, t))
    if best is None or t < best[0]:
        best = (t, urot)
t, urot = best
t, pl = run(urot)
print("chosen U4 rotation", urot)
for ref, x, y, rot, d in pl:
    print("  %-4s (%.2f, %.2f) rot %3d   pin distance sum %.1f mm" % (ref, x, y, rot, d))
pcbnew.SaveBoard(sys.argv[2], b)
