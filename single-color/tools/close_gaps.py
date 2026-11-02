"""Close the small gaps between pieces of one net: a straight track whose end touches nothing (no other piece of its net, no via, no pad) but stops less than --max mm from another piece of the same net on
the same layer (two butted round end caps: a 'waist' in the trace, joined only by the overlap of the two caps).  The piece is prolonged along its own direction to the centre line of the other piece
(at most --max beyond its end); when its line does not meet that piece within --max the gap is reported and left alone.
usage: python close_gaps.py dump.json edit.json [--max 0.2]      dump.json = copper_dump.py output, edit.json for apply_ring_edits.py"""
import json
import math
import sys

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

args = sys.argv[1:]
MAXG = 0.2
if "--max" in args:
    i = args.index("--max")
    MAXG = float(args[i + 1])
    del args[i:i + 2]
dumpf, outf = args
D = json.load(open(dumpf))
tracks = D["tracks"]


def touches(t, q):
    for u in tracks:
        if u is t or u["layer"] != t["layer"] or u["net"] != t["net"]:
            continue
        if LineString(u["poly"]).distance(Point(q)) < 0.012:
            return True
    for v in D["vias"]:
        if v["net"] == t["net"] and math.hypot(v["p"][0] - q[0], v["p"][1] - q[1]) < 0.16:
            return True
    for p in D["pads"]:
        if p["layer"] == t["layer"] and p["net"] == t["net"] and Polygon(p["pts"]).buffer(0).distance(Point(q)) < 0.012:
            return True
    return False


rem, add, rep = [], [], []
used = set()
for t in tracks:
    if t["k"] != "seg" or id(t) in used:
        continue
    for q, o in ((t["a"], t["b"]), (t["b"], t["a"])):
        if touches(t, q):
            continue
        dx, dy = q[0] - o[0], q[1] - o[1]
        ln = math.hypot(dx, dy)
        if ln < 1e-6:
            continue
        ux, uy = dx / ln, dy / ln
        ray = LineString([q, (q[0] + ux * MAXG, q[1] + uy * MAXG)])
        best = None
        for u in tracks:
            if u is t or u["layer"] != t["layer"] or u["net"] != t["net"]:
                continue
            ul = LineString(u["poly"])
            if ray.distance(ul) > 0.006:
                continue
            x = ray.intersection(ul)
            if x.is_empty or x.geom_type != "Point":
                pt = nearest_points(ray, ul)[0]            # collinear / grazing: the point of the ray closest to the other piece
            else:
                pt = x
            d = math.hypot(pt.x - q[0], pt.y - q[1])
            if best is None or d < best[0]:
                best = (d, (pt.x, pt.y), u)
        if best is None:
            # two free ends that point at each other's line near a corner: both pieces are prolonged to the crossing point of their lines
            done = False
            for u in tracks:
                if done or u is t or id(u) in used or u["k"] != "seg" or u["layer"] != t["layer"] or u["net"] != t["net"]:
                    continue
                for q2, o2 in ((u["a"], u["b"]), (u["b"], u["a"])):
                    if math.hypot(q2[0] - q[0], q2[1] - q[1]) > MAXG or touches(u, q2):
                        continue
                    d1 = (q[0] - o[0], q[1] - o[1])
                    d2 = (q2[0] - o2[0], q2[1] - o2[1])
                    det = d1[0] * d2[1] - d1[1] * d2[0]
                    if abs(det) < 1e-9:
                        continue
                    rx, ry = q2[0] - q[0], q2[1] - q[1]
                    s1 = (rx * d2[1] - ry * d2[0]) / det
                    s2 = (rx * d1[1] - ry * d1[0]) / det
                    X = (q[0] + d1[0] * s1, q[1] + d1[1] * s1)
                    if s1 < -1e-6 or s2 < -1e-6:
                        continue
                    if math.hypot(X[0] - q[0], X[1] - q[1]) > MAXG or math.hypot(X[0] - q2[0], X[1] - q2[1]) > MAXG:
                        continue
                    rem.append([t["layer"], t["net"], [t["a"][0], t["a"][1]], [t["b"][0], t["b"][1]]])
                    add.append([t["layer"], t["net"], [o[0], o[1]], [X[0], X[1]]])
                    rem.append([u["layer"], u["net"], [u["a"][0], u["a"][1]], [u["b"][0], u["b"][1]]])
                    add.append([u["layer"], u["net"], [o2[0], o2[1]], [X[0], X[1]]])
                    used.add(id(t))
                    used.add(id(u))
                    rep.append((t["net"], t["layer"], q, "closed at the corner (%.3f + %.3f)" % (math.hypot(X[0] - q[0], X[1] - q[1]), math.hypot(X[0] - q2[0], X[1] - q2[1]))))
                    done = True
                    break
            if done:
                break
            near = min((LineString(u["poly"]).distance(Point(q)) for u in tracks if u is not t and u["layer"] == t["layer"] and u["net"] == t["net"]), default=9)
            if near < MAXG:
                rep.append((t["net"], t["layer"], q, "gap %.3f, line does not meet the other piece" % near))
            continue
        rem.append([t["layer"], t["net"], [t["a"][0], t["a"][1]], [t["b"][0], t["b"][1]]])
        add.append([t["layer"], t["net"], [o[0], o[1]], [best[1][0], best[1][1]]])
        used.add(id(t))
        used.add(id(best[2]))
        rep.append((t["net"], t["layer"], q, "closed, prolonged %.3f" % best[0]))
        break
for r in rep:
    print(r[0], r[1], "(%.3f, %.3f)" % tuple(r[2]), r[3])
print("closed %d, left %d" % (sum(1 for r in rep if r[3].startswith("closed")), sum(1 for r in rep if not r[3].startswith("closed"))))
json.dump({"remove": rem, "add": add}, open(outf, "w"))
