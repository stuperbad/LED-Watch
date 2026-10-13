"""
Straight fan-out stubs for the signal pads of a QFN/QFP (default U1): each pad gets a short track straight out from the package edge, so that
the router can never box a pad in by turning a neighbour's wire sideways right at the chip.
usage: python add_stubs.py grid.json in.kicad_pcb out.kicad_pcb [REF=U1] [length_mm=1.0] [width=0.1] [--via]
--via: dogbone fan-out instead of plain stubs: stub + through via at its end, lengths alternate (0.35 / 0.65 mm from the pad edge) so the vias form two staggered rows
grid.json = tools/grid_dump.py output of in.kicad_pcb.  Pads of GND / no net / already connected by a track are skipped; a stub is shortened until it
keeps 0.2 mm from the copper of other nets (min 0.3 mm), otherwise it is skipped.
"""
import json
import math
import sys
import uuid

from shapely.geometry import LineString, Polygon
from shapely.strtree import STRtree

VIA = "--via" in sys.argv
argv = [a for a in sys.argv if a != "--via"]
grid, src, dst = argv[1:4]
ref = argv[4] if len(argv) > 4 else "U1"
length = float(argv[5]) if len(argv) > 5 else 1.0
width = float(argv[6]) if len(argv) > 6 else 0.1
VIA_D, VIA_DRILL = 0.30, 0.15
CLR = 0.2
d = json.load(open(grid))

pads = [p for p in d["pads"] if p["ref"].startswith(ref + ".") and p["layer"] == "F.Cu"]
polys = {p["ref"]: Polygon(p["pts"]).buffer(0) for p in pads}
cx = sum(g.centroid.x for g in polys.values()) / len(polys)
cy = sum(g.centroid.y for g in polys.values()) / len(polys)

# every other copper item on F.Cu (and through holes) as obstacles
obst = []
for p in d["pads"]:
    if p["layer"] == "F.Cu" and not p["ref"].startswith(ref + "."):
        obst.append((p["net"], Polygon(p["pts"]).buffer(0)))
    elif p["layer"] == "F.Cu":
        obst.append((p["net"], Polygon(p["pts"]).buffer(0)))        # the chip's own pads (net checked below)
for t in d["trk"]:
    if t.get("layer") == "F.Cu" and "arc" not in t:
        obst.append((t["net"], LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2)))
for v in d["via"]:
    from shapely.geometry import Point
    obst.append((v["net"], Point(v["x"], v["y"]).buffer(v["d"] / 2)))
for c in d["circles"]:
    from shapely.geometry import Point
    obst.append(("", Point(c["x"], c["y"]).buffer(c["r"] + 0.28)))
tree = STRtree([g for _, g in obst])
connected = set()
for t in d["trk"]:
    if t.get("layer") == "F.Cu" and "arc" not in t:
        ls = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])])
        for r_, g in polys.items():
            if g.distance(ls) < 0.01:
                connected.add(r_)

out = []
vias = []
placed = []          # (net, geometry) of stubs / vias placed in this run


def outward(g):
    c = g.centroid
    minx, miny, maxx, maxy = g.bounds
    dx, dy = c.x - cx, c.y - cy
    if abs(dx) > abs(dy):
        ux, uy = (1.0, 0.0) if dx > 0 else (-1.0, 0.0)
        return ux, uy, (maxx - 0.05 if dx > 0 else minx + 0.05), c.y
    ux, uy = (0.0, 1.0) if dy > 0 else (0.0, -1.0)
    return ux, uy, c.x, (maxy - 0.05 if dy > 0 else miny + 0.05)


todo = []
for r_, g in sorted(polys.items()):
    p = next(q for q in pads if q["ref"] == r_)
    net = p["net"]
    if not net or net == "GND" or r_ in connected:
        continue
    ux, uy, sx, sy = outward(g)
    todo.append((r_, net, ux, uy, sx, sy))

if VIA:
    # dogbone: alternate stub lengths along each package side; try several stagger pairs per side, keep the first that fits every pin of the side
    from shapely.geometry import Point
    sides = {}
    for t in todo:
        sides.setdefault((t[2], t[3]), []).append(t)

    def try_side(lst, pair):
        res, pl = [], []
        for n, (r_, net, ux, uy, sx, sy) in enumerate(lst):
            order = [pair[n % 2], pair[(n + 1) % 2]]
            ok = False
            for L in order:
                ls = LineString([(sx, sy), (sx + ux * L, sy + uy * L)])
                pv = Point(sx + ux * L, sy + uy * L)
                bad = False
                for k in tree.query(pv.buffer(0.5)):
                    nm, og = obst[int(k)]
                    if nm != net and (og.distance(pv) < 0.28 or og.distance(ls) < 0.15):
                        bad = True
                        break
                if not bad:
                    for nm, og in placed + pl:
                        if nm != net and (og.distance(pv) < 0.28 or og.distance(ls) < 0.15 or (og.geom_type == "Point" and og.distance(pv) < 0.45)):
                            bad = True
                            break
                if not bad:
                    res.append((r_, net, (sx, sy), (sx + ux * L, sy + uy * L), L))
                    pl.append((net, ls.buffer(width / 2)))
                    pl.append((net, pv))
                    ok = True
                    break
            if not ok:
                res.append((r_, net, None, None, 0))      # no dogbone for this pad
        return res, pl

    for key, lst in sides.items():
        lst.sort(key=lambda t: (t[5] if key[0] == 0 else t[4]))      # along the edge
        best = None
        for pair in [(0.35, 0.65), (0.30, 0.50), (0.30, 0.55), (0.35, 0.55), (0.40, 0.70), (0.30, 0.60)]:
            res, pl = try_side(lst, pair)
            nfail = sum(1 for r in res if r[2] is None)
            if best is None or nfail < best[0]:
                best = (nfail, res, pl, pair)
            if nfail == 0:
                break
        nfail, res, pl, pair = best
        placed.extend(pl)
        for r_, net, a, b, L in res:
            if a is None:
                print("no dogbone for", r_, net)
            else:
                out.append((r_, net, a, b, L))
                vias.append((net, b))
else:
    for r_, net, ux, uy, sx, sy in todo:
        best = 0.0
        L = length
        while L >= 0.3 - 1e-9:
            ls = LineString([(sx, sy), (sx + ux * L, sy + uy * L)])
            bad = False
            for k in tree.query(ls.buffer(CLR + width / 2 + 0.01)):
                nm, og = obst[int(k)]
                if nm == net:
                    continue
                if og.distance(ls) < CLR + width / 2:
                    bad = True
                    break
            if not bad:
                best = L
                break
            L -= 0.1
        if best:
            out.append((r_, net, (sx, sy), (sx + ux * best, sy + uy * best), best))

txt = ""
for r_, net, a, b, L in out:
    txt += '\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %g)\n\t\t(layer "F.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (a[0], a[1], b[0], b[1], width, net, uuid.uuid4())
for net, pt in vias:
    txt += '\t(via\n\t\t(at %.4f %.4f)\n\t\t(size %g)\n\t\t(drill %g)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (pt[0], pt[1], VIA_D, VIA_DRILL, net, uuid.uuid4())
s = open(src, encoding="utf8").read()
k = s.rindex("\t(embedded_fonts")
open(dst, "w", encoding="utf8").write(s[:k] + txt + s[k:])
print("stubs:", len(out), "of", len(polys), "pads;", ", ".join("%s %.1f" % (r_, L) for r_, _, _, _, L in out))
