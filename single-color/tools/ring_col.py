"""Re-draw the F.Cu stub between each ring LED's COL pad (pad 2, the outer pad) and the anode arc of its column as one straight piece along the pad axis (radially outward), which meets the arc square.
For every COL stub of the S / M / H rings: the ray from the pad centre straight away from the board centre (100, 100) is intersected with the same-net F.Cu copper (the arc, as a polyline in the poly twin);
the first hit that is roughly perpendicular to the ray and 0.3..1.3 mm beyond the pad centre is the new end.  The new piece replaces the old stub pieces when it clears every other-net item
(tracks 0.205 centre to centre, pad outlines 0.155, via centres 0.335, a via hole needs 0.2 to copper) including the new ROW stubs of ring_stubs.py (pass its edit file with --edit).  Otherwise the old stub stays and the pad is reported.
Stubs that are not a plain 1..3 piece chain (a trunk is attached, a junction) are left alone.
usage: python ring_col.py grid.json stubs.json out_edit.json [--edit row_edit.json] [--tol 3.0] [--keep REF,REF]
  --tol: a stub whose first piece is already within TOL degrees of the pad axis and ends on the arc is left alone."""
import json
import math
import sys

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

args = sys.argv[1:]
opt = {"--edit": "", "--tol": "3.0", "--keep": ""}
pos = []
i = 0
while i < len(args):
    if args[i] in opt:
        opt[args[i]] = args[i + 1]
        i += 2
    else:
        pos.append(args[i])
        i += 1
gridf, stubf, outf = pos
TOL = float(opt["--tol"])
R_TRK, R_PAD, R_VIA = 0.205, 0.155, 0.335
G = json.load(open(gridf))
S = json.load(open(stubf))
E = json.load(open(opt["--edit"])) if opt["--edit"] else {"remove": [], "add": []}
KEEP = {r for r in opt["--keep"].split(",") if r}
cols = [s for s in S if s["net"].startswith("/COL") and s["ref"] not in KEEP]
dead = set()
for s in cols:
    for a, b in s["pieces"]:
        dead.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
        dead.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
for l, n, a, b in E["remove"]:
    dead.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
    dead.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
obst = []
net_lines = {}
for p in G["pads"]:
    if p["layer"] == "F.Cu":
        obst.append([Polygon(p["pts"]).buffer(0), R_PAD, p["net"]])
for t in G["trk"]:
    if t["layer"] == "F.Cu":
        k = (round(t["x1"], 3), round(t["y1"], 3), round(t["x2"], 3), round(t["y2"], 3))
        ls = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])])
        if k not in dead:
            obst.append([ls, R_TRK + (t["w"] - 0.1) / 2, t["net"]])
            net_lines.setdefault(t["net"], []).append((ls, (t["x2"] - t["x1"], t["y2"] - t["y1"])))
for v in G["via"]:
    obst.append([Point(v["x"], v["y"]), R_VIA, v["net"]])
for c in G["circles"]:
    obst.append([Point(c["x"], c["y"]), c["r"] + 0.25, ""])
for l, n, a, b in E["add"]:
    obst.append([LineString([tuple(a), tuple(b)]), R_TRK, n])

rem, add, rep = [], [], []
for s in sorted(cols, key=lambda s: s["ref"]):
    net, C = s["net"], tuple(s["center"])
    A = math.radians(s["ringA"])
    uo = (math.sin(A), -math.cos(A))
    if not s["ok"] or not (1 <= len(s["pieces"]) <= 3):
        rep.append((s["ref"], net, "skipped: %d pieces / %s" % (len(s["pieces"]), s["why"])))
        continue
    ray = LineString([(C[0] + uo[0] * 0.3, C[1] + uo[1] * 0.3), (C[0] + uo[0] * 1.6, C[1] + uo[1] * 1.6)])
    hits = []
    for ls, d in net_lines.get(net, []):
        if ray.distance(ls) > 0.012:
            continue
        x = ray.intersection(ls)
        if x.is_empty or x.geom_type != "Point":
            x = nearest_points(ray, ls)[0]
        dl = math.hypot(*d)
        if dl < 1e-9:
            continue
        cosang = abs((d[0] * uo[0] + d[1] * uo[1]) / dl)
        if cosang > 0.45:
            continue
        hits.append((x.distance(Point(C)), (x.x, x.y)))
    if not hits:
        # the arc ends a fraction of a degree short of the pad: radial piece to the arc radius, then a tiny concentric arc to the old end
        E = tuple(s["endpoint"])
        rE = math.hypot(E[0] - 100.0, E[1] - 100.0)
        bE = math.degrees(math.atan2(E[0] - 100.0, -(E[1] - 100.0)))
        dB = ((bE - s["ringA"] + 180) % 360) - 180
        rP = math.hypot(C[0] - 100.0, C[1] - 100.0)
        if not (0.3 < rE - rP < 1.3 and abs(dB) < 2.0):
            rep.append((s["ref"], net, "no arc hit (end %.2f deg away, r %.2f)" % (dB, rE)))
            continue
        Q = (100.0 + rE * math.sin(A), 100.0 - rE * math.cos(A))
        Bm = math.radians(s["ringA"] + dB / 2)
        M = (100.0 + rE * math.sin(Bm), 100.0 - rE * math.cos(Bm))
        ls = LineString([C, Q])
        ls2 = LineString([Q, E])
        if any(n != net and (g.distance(ls) < req - 1e-6 or g.distance(ls2) < req - 1e-6) for g, req, n in obst):
            rep.append((s["ref"], net, "radial + arc blocked, old stub kept"))
            continue
        for a, b in s["pieces"]:
            rem.append(["F.Cu", net, [a[0], a[1]], [b[0], b[1]]])
        add.append(["F.Cu", net, [C[0], C[1]], [Q[0], Q[1]]])
        add.append(["F.Cu", net, "arc", [Q[0], Q[1]], [M[0], M[1]], [E[0], E[1]]])
        obst.append([ls, R_TRK, net])
        obst.append([ls2, R_TRK, net])
        rep.append((s["ref"], net, "radial + %.2f deg arc" % abs(dB)))
        continue
    dist, Q = min(hits)
    # already straight and radial?
    first_dir = None
    a, b = s["pieces"][0]
    if len(s["pieces"]) == 1:
        d = (b[0] - a[0], b[1] - a[1])
        if math.hypot(*d) > 1e-6:
            ang = math.degrees(math.atan2(d[1], d[0]))
            ref = math.degrees(math.atan2(uo[1], uo[0]))
            if abs(((ang - ref + 180) % 360) - 180) < TOL or abs(((ang - ref) % 360)) < TOL:
                rep.append((s["ref"], net, "already radial"))
                continue
    ls = LineString([C, Q])
    ok = True
    for g, req, n in obst:
        if n == net:
            continue
        if g.distance(ls) < req - 1e-6:
            ok = False
            break
    if not ok:
        rep.append((s["ref"], net, "radial piece (%.2f) blocked, old stub kept" % dist))
        continue
    for a, b in s["pieces"]:
        rem.append(["F.Cu", net, [a[0], a[1]], [b[0], b[1]]])
    add.append(["F.Cu", net, [C[0], C[1]], [Q[0], Q[1]]])
    obst.append([ls, R_TRK, net])
    rep.append((s["ref"], net, "radial %.2f mm (was %d pieces)" % (dist, len(s["pieces"]))))
for r in rep:
    print(*r)
print("radial %d of %d" % (len(add), len(cols)))
json.dump({"remove": rem, "add": add}, open(outf, "w"))
