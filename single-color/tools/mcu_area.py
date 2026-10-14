"""Re-place the MCU surroundings: U1 (x=100, y=91.6, 180 deg), crystal block, one decoupling cap per supply pin pair, and regenerate the crystal guard zone.
usage (KiCad python): mcu_area.py in.kicad_pcb out.kicad_pcb"""
import math
import sys

import pcbnew
from plc import *

b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
place(fp["U1"], 100.0, 91.6, 180)
# crystal block: Y1 centred on the XTAL pins, load caps one above, one below
x1, y1 = pad_pos(fp["U1"], 34)
x2, y2 = pad_pos(fp["U1"], 35)
yc = round((y1 + y2) / 2 / 0.05) * 0.05
place(fp["Y1"], 94.55, yc, 90)
place(fp["C20"], 92.5, yc - 1.125, 270)
place(fp["C21"], 92.5, yc + 1.125, 90)
# guard zone around the crystal block
boxes = [pb for r in ("Y1", "C20", "C21") for pb in pad_boxes(fp[r])]
GM = 0.5
g = (min(a[0] for a in boxes) - GM, min(a[1] for a in boxes) - GM, max(a[2] for a in boxes) + GM, max(a[3] for a in boxes) + GM)
zone = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.F_Cu][0]
ol = zone.Outline()
ol.RemoveAllContours()
ol.NewOutline()
ch = 0.5
for (px, py) in ((g[0] + ch, g[1]), (g[2] - ch, g[1]), (g[2], g[1] + ch), (g[2], g[3] - ch), (g[2] - ch, g[3]), (g[0] + ch, g[3]), (g[0], g[3] - ch), (g[0], g[1] + ch)):
    ol.Append(mm(px), mm(py))
GUARD = g
print("crystal guard box: x %.2f..%.2f  y %.2f..%.2f" % (g[0], g[2], g[1], g[3]))
# decoupling: one cap per VBAT/GND pin pair, placed as near the pair as possible (front or back)
pairs = {"C10": (14, 15), "C11": (28, 29), "C12": (42, 43)}
front_keep = [SOLAR_BODY, GUARD]
back_keep = [GUARD]
report = []
CAPS = set(pairs)
obs = {"F": [], "B": []}
for ref, g in fp.items():
    if ref in CAPS:
        continue
    for a_ in pad_boxes(g):
        obs["B" if g.IsFlipped() else "F"].append(a_[:4])
        if a_[4]:
            obs["F" if g.IsFlipped() else "B"].append(a_[:4])
obs["F"] += [SOLAR_BODY, GUARD]
obs["B"] += list(CELLS) + [GUARD]


def free(side, boxes):
    return not any(inter(bx, o, 0.3) for bx in boxes for o in obs[side])


for cap, (vp, gp) in pairs.items():
    f = fp[cap]
    V, G = pad_pos(fp["U1"], vp), pad_pos(fp["U1"], gp)
    cands = []
    for back in (False,):
        set_side(f, back)
        for rot in (0, 90, 180, 270):
            place(f, 0.0, 0.0, rot)
            off = {p.GetNetname(): (tomm(p.GetPosition().x), tomm(p.GetPosition().y)) for p in f.Pads()}
            rel = [pb[:4] for pb in pad_boxes(f)]
            for xi in range(int((V[0] - 6.0) * 20), int((V[0] + 6.0) * 20)):
                for yi in range(int((V[1] - 6.0) * 20), int((V[1] + 6.0) * 20)):
                    x, y = xi / 20, yi / 20
                    d = math.hypot(x + off["VBAT"][0] - V[0], y + off["VBAT"][1] - V[1]) + math.hypot(x + off["GND"][0] - G[0], y + off["GND"][1] - G[1]) + (1.2 if back else 0.0)
                    cands.append((d, back, rot, x, y, rel))
    cands.sort(key=lambda c: c[0])
    for d, back, rot, x, y, rel in cands:
        boxes = [(r[0] + x, r[1] + y, r[2] + x, r[3] + y) for r in rel]
        if not free("B" if back else "F", boxes):
            continue
        set_side(f, back)
        place(f, x, y, rot)
        if conflicts(fp, cap, [SOLAR_BODY, GUARD], [GUARD], 0.3):
            continue
        report.append((cap, "back" if back else "front", x, y, rot, (d - (1.2 if back else 0.0)) / 2))
        for a_ in pad_boxes(f):
            obs["B" if back else "F"].append(a_[:4])
        break
pcbnew.SaveBoard(sys.argv[2], b)
for r in report:
    print("%s -> %s (%.2f, %.2f) rot %d, pads about %.1f mm from the pin pair" % r)
