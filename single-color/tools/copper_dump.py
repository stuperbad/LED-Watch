"""Dump the copper of a board for the clean-up tools (via_center.py, ...): straight tracks and ARCS apart (a grid_dump poly twin cannot tell which pieces are arcs), vias, pads per layer.
usage (KiCad python): copper_dump.py in.kicad_pcb out.json
 tracks: {k: 'seg'|'arc', net, layer, a, b, [m], w, poly: [(x, y), ...]} (poly = centre line, arcs tessellated)   vias: {p, net, d, drill}   pads: {ref, net, layer, pts, hole}"""
import json
import math
import sys

import pcbnew

mm = lambda v: v / 1e6
LAY = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "In1.Cu", pcbnew.In2_Cu: "In2.Cu", pcbnew.B_Cu: "B.Cu"}
b = pcbnew.LoadBoard(sys.argv[1])
out = {"tracks": [], "vias": [], "pads": [], "holes": []}
for t in b.GetTracks():
    c = t.GetClass()
    if c == "PCB_VIA":
        out["vias"].append({"p": (mm(t.GetPosition().x), mm(t.GetPosition().y)), "net": t.GetNetname(), "d": 0.3, "drill": mm(t.GetDrillValue())})
        continue
    L = LAY.get(t.GetLayer())
    if L is None:
        continue
    a = (mm(t.GetStart().x), mm(t.GetStart().y))
    e = (mm(t.GetEnd().x), mm(t.GetEnd().y))
    if c == "PCB_ARC":
        m = (mm(t.GetMid().x), mm(t.GetMid().y))
        # circle through the three points
        ax, ay = a
        bx, by = m
        cx, cy = e
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
        r = math.hypot(ax - ux, ay - uy)
        a0, a1, am = (math.atan2(p[1] - uy, p[0] - ux) for p in (a, e, m))
        # sweep direction from start to end through the mid point
        def norm(x):
            return (x + 2 * math.pi) % (2 * math.pi)
        s1 = norm(a1 - a0)
        sm = norm(am - a0)
        sweep = s1 if sm < s1 else s1 - 2 * math.pi
        n = max(4, int(abs(sweep) * r / 0.15))
        poly = [(ux + r * math.cos(a0 + sweep * i / n), uy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]
        out["tracks"].append({"k": "arc", "net": t.GetNetname(), "layer": L, "a": a, "b": e, "m": m, "w": mm(t.GetWidth()), "poly": poly})
    else:
        out["tracks"].append({"k": "seg", "net": t.GetNetname(), "layer": L, "a": a, "b": e, "w": mm(t.GetWidth()), "poly": [a, e]})
for f in b.GetFootprints():
    for p in f.Pads():
        n = p.GetNetname()
        hole = mm(p.GetDrillSize().x) if p.GetDrillSize().x else 0
        for lid, ln in LAY.items():
            if not p.IsOnLayer(lid):
                continue
            poly = p.GetEffectivePolygon(lid)
            if not poly.OutlineCount():
                continue
            o = poly.COutline(0)
            out["pads"].append({"ref": f.GetReference() + "." + p.GetNumber(), "net": n, "layer": ln, "hole": hole,
                                "pts": [(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())]})
        if p.GetDrillSize().x:
            out["holes"].append({"p": (mm(p.GetPosition().x), mm(p.GetPosition().y)), "r": mm(p.GetDrillSize().x) / 2})
json.dump(out, open(sys.argv[2], "w"))
print("tracks", len(out["tracks"]), "vias", len(out["vias"]), "pads", len(out["pads"]))
