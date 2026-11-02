"""Drop whole pad groups from a pad_exit.py edit file.   usage: python filter_groups.py in.json out.json --drop-names R52.1,C31.1 | --drop-near x,y,r [--drop-near x,y,r ...]
A group is dropped when its name is listed or when one of its added pieces comes within r mm of a given point (used to throw out the pads whose new route made a sharp corner)."""
import json
import math
import sys

args = sys.argv[1:]
inf, outf = args[0], args[1]
names, near = set(), []
i = 2
while i < len(args):
    if args[i] == "--drop-names":
        names |= {x for x in args[i + 1].split(",") if x}
        i += 2
    elif args[i] == "--drop-near":
        x, y, r = (float(v) for v in args[i + 1].split(","))
        near.append((x, y, r))
        i += 2
    else:
        i += 1
E = json.load(open(inf))
rem, add, dropped = [], [], []
for g in E["groups"]:
    bad = g["name"] in names
    for e in g["add"]:
        if e[2] == "arc":
            pts = [e[3], e[5]]
        else:
            pts = [e[2], e[3]]
        for (x, y, r) in near:
            for a, b in zip([pts[0]], [pts[1]]):
                # distance from the point to the piece
                dx, dy = b[0] - a[0], b[1] - a[1]
                L2 = dx * dx + dy * dy
                t = 0 if L2 == 0 else max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
                if math.hypot(a[0] + t * dx - x, a[1] + t * dy - y) <= r:
                    bad = True
    if bad:
        dropped.append(g["name"])
        continue
    rem += g["remove"]
    add += g["add"]
json.dump({"remove": rem, "add": add}, open(outf, "w"))
print("kept %d groups, dropped %d: %s" % (len(E["groups"]) - len(dropped), len(dropped), ",".join(dropped)))
