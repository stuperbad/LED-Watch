"""Dump every copper item of a board for tools/grid_route.py.   usage (KiCad python): grid_dump.py in.kicad_pcb out.json
mm, KiCad coordinates.  pads: per copper layer polygon + net; vias; tracks (segments only: use the poly board); edge cuts as point lists."""
import json
import math
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
mm = lambda v: v / 1e6
LAYERS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
d = {"pads": [], "trk": [], "via": [], "edge": [], "circles": [], "nets": {}}
for f in b.GetFootprints():
    for p in f.Pads():
        net = p.GetNetname()
        hole = mm(p.GetDrillSize().x) if p.GetDrillSize().x else 0
        for ln, lid in LAYERS.items():
            if not p.IsOnLayer(lid):
                continue
            poly = p.GetEffectivePolygon(lid)
            if not poly.OutlineCount():
                continue
            o = poly.COutline(0)
            d["pads"].append({"layer": ln, "net": net, "hole": hole, "ref": f.GetReference() + "." + p.GetNumber(),
                              "pts": [(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())]})
        if p.GetDrillSize().x:
            q = p.GetPosition()
            d["circles"].append({"x": mm(q.x), "y": mm(q.y), "r": mm(p.GetDrillSize().x) / 2, "net": net, "kind": "hole"})
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        d["via"].append({"x": mm(p.x), "y": mm(p.y), "net": t.GetNetname(), "d": mm(t.GetWidth(pcbnew.F_Cu)), "drill": mm(t.GetDrillValue())})
    elif t.GetClass() == "PCB_TRACK":
        s, e = t.GetStart(), t.GetEnd()
        d["trk"].append({"x1": mm(s.x), "y1": mm(s.y), "x2": mm(e.x), "y2": mm(e.y), "layer": t.GetLayerName(), "w": mm(t.GetWidth()), "net": t.GetNetname()})
    elif t.GetClass() == "PCB_ARC":
        s, e, m = t.GetStart(), t.GetEnd(), t.GetMid()
        d["trk"].append({"arc": [mm(s.x), mm(s.y), mm(m.x), mm(m.y), mm(e.x), mm(e.y)], "layer": t.GetLayerName(), "w": mm(t.GetWidth()), "net": t.GetNetname()})
for g in b.GetDrawings():
    if g.GetLayerName() != "Edge.Cuts":
        continue
    sh = g.GetShape()
    if sh == pcbnew.SHAPE_T_CIRCLE:
        c = g.GetCenter()
        d["edge"].append({"kind": "circle", "x": mm(c.x), "y": mm(c.y), "r": mm(g.GetRadius())})
    elif sh == pcbnew.SHAPE_T_ARC:
        c = g.GetCenter()
        s, m, e = g.GetStart(), g.GetArcMid(), g.GetEnd()
        d["edge"].append({"kind": "arc", "pts": [mm(s.x), mm(s.y), mm(m.x), mm(m.y), mm(e.x), mm(e.y)]})
    elif sh == pcbnew.SHAPE_T_SEGMENT:
        s, e = g.GetStart(), g.GetEnd()
        d["edge"].append({"kind": "seg", "pts": [mm(s.x), mm(s.y), mm(e.x), mm(e.y)]})
    elif sh == pcbnew.SHAPE_T_RECT:
        s, e = g.GetStart(), g.GetEnd()
        d["edge"].append({"kind": "rect", "pts": [mm(s.x), mm(s.y), mm(e.x), mm(e.y)]})
    elif sh == pcbnew.SHAPE_T_POLY:
        ps = g.GetPolyShape()
        for k in range(ps.OutlineCount()):
            o = ps.COutline(k)
            d["edge"].append({"kind": "poly", "pts": [(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())]})
    else:
        d["edge"].append({"kind": "other", "shape": int(sh)})
d["keepouts"] = []
for zs in [list(b.Zones())] + [list(f.Zones()) for f in b.GetFootprints()]:
    for z in zs:
        if z.GetIsRuleArea():
            o = z.Outline().COutline(0)
            d["keepouts"].append({"pts": [(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())],
                                  "vias": bool(z.GetDoNotAllowVias()), "tracks": bool(z.GetDoNotAllowTracks()), "pads": bool(z.GetDoNotAllowPads())})
bb = b.GetBoardEdgesBoundingBox()
d["bbox"] = [mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())]
json.dump(d, open(sys.argv[2], "w"))
print("pads", len(d["pads"]), "vias", len(d["via"]), "tracks", len(d["trk"]), "edge", len(d["edge"]), "bbox", d["bbox"])
