"""Rebuild the In2 ground-plane zone outline from the CURRENT board outline (inset 0.4 mm, strap slots cut out) and refill all zones.
usage (KiCad python): fix_gnd_zone.py in.kicad_pcb out.kicad_pcb"""
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
zs = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.In2_Cu]
assert len(zs) == 1, len(zs)
z = zs[0]
bb = z.GetBoundingBox()
print("old In2 zone outline bbox: x %.2f..%.2f  y %.2f..%.2f" % (tomm(bb.GetX()), tomm(bb.GetRight()), tomm(bb.GetY()), tomm(bb.GetBottom())))
ol = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(ol, True)
try:
    ol.Deflate(mm(0.4), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 10000)
except Exception:
    ol.Inflate(-mm(0.4), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 10000)
z.SetOutline(ol)
nb = z.GetBoundingBox()
print("new In2 zone outline bbox: x %.2f..%.2f  y %.2f..%.2f, %d outline(s), %d hole(s) in the first" % (tomm(nb.GetX()), tomm(nb.GetRight()), tomm(nb.GetY()), tomm(nb.GetBottom()), ol.OutlineCount(), ol.HoleCount(0)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
