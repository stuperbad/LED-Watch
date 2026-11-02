"""Straight escape lanes for the fan-out vias of a chip (default U1): the vias sit in two staggered rows right behind the pad tips, so a via of the inner row cannot leave on an inner layer except
straight out through the gap between two vias of the outer row, and the grid router cannot see that gap.  For every named net this adds a straight track on In1.Cu or B.Cu from the net's fan-out via,
straight away from the pad (the axis along which the via is displaced from its pad), to END mm beyond the outer edge of the chip's pads; the router then starts from the end of that lane, in free space.
Layer: with --parity, pads with an odd number take the first of --layers and pads with an even number the second (neighbours on different layers: 0.8 mm pitch per layer); the other layer is the fallback.
A lane is shortened (down to --min mm) until it keeps 0.1 mm clearance to all other copper; a net whose lane fits on neither layer is reported and skipped.
usage: python add_escape.py grid.json in.kicad_pcb out.kicad_pcb NET [NET ...] [--ref U1] [--end 1.0] [--min 0.4] [--layers In1.Cu,B.Cu] [--width 0.1] [--parity] [--inner-only 0.45]
 NET may be @file (one net name per line).  grid.json = tools/grid_dump.py output of in.kicad_pcb (the poly twin, so arcs are segments).
 --inner-only D: only vias that are within D mm of the pad tip get a lane (the outer row can leave on its own)."""
import json
import sys
import uuid

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

args = sys.argv[1:]
opt = {"--ref": "U1", "--end": "1.0", "--min": "0.4", "--layers": "In1.Cu,B.Cu", "--width": "0.1", "--inner-only": "9"}
flags = {"--parity"}
pos = []
fl = set()
i = 0
while i < len(args):
    if args[i] in opt:
        opt[args[i]] = args[i + 1]
        i += 2
    elif args[i] in flags:
        fl.add(args[i])
        i += 1
    else:
        pos.append(args[i])
        i += 1
grid, src, dst = pos[:3]
nets = pos[3:]
if nets and nets[0].startswith("@"):
    nets = [ln.strip() for ln in open(nets[0][1:]) if ln.strip()]
REF, END, MINL, W, INNER = opt["--ref"], float(opt["--end"]), float(opt["--min"]), float(opt["--width"]), float(opt["--inner-only"])
LAYERS = opt["--layers"].split(",")
CLR = 0.1
d = json.load(open(grid))

allp = [Polygon(p["pts"]) for p in d["pads"] if p["ref"].startswith(REF + ".") and p["layer"] == "F.Cu" and p["ref"] != REF + ".49"]
bx0 = min(g.bounds[0] for g in allp); by0 = min(g.bounds[1] for g in allp)
bx1 = max(g.bounds[2] for g in allp); by1 = max(g.bounds[3] for g in allp)
pads = [p for p in d["pads"] if p["ref"].startswith(REF + ".") and p["layer"] == "F.Cu" and p["net"] in nets]

obst = {ln: [] for ln in LAYERS}
for ln in LAYERS:
    for p in d["pads"]:
        if p["layer"] == ln:
            obst[ln].append((p["net"], Polygon(p["pts"]).buffer(0)))
    for t in d["trk"]:
        if t["layer"] == ln:
            g = LineString([(t["arc"][0], t["arc"][1]), (t["arc"][2], t["arc"][3]), (t["arc"][4], t["arc"][5])]) if "arc" in t else LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])])
            obst[ln].append((t["net"], g.buffer(t["w"] / 2)))
    for v in d["via"]:
        obst[ln].append((v["net"], Point(v["x"], v["y"]).buffer(v["d"] / 2)))
    for c in d["circles"]:
        obst[ln].append(("", Point(c["x"], c["y"]).buffer(c["r"] + 0.2)))
trees = {ln: STRtree([g for _, g in obst[ln]]) for ln in LAYERS}
placed = []
out = []
for p in sorted(pads, key=lambda q: int(q["ref"].split(".")[1])):
    pg = Polygon(p["pts"])
    net = p["net"]
    num = int(p["ref"].split(".")[1])
    cands = [v for v in d["via"] if v["net"] == net and pg.distance(Point(v["x"], v["y"])) < 1.0]
    if not cands:
        print("%s %s: no fan-out via within 1 mm" % (p["ref"], net))
        continue
    v = min(cands, key=lambda v: pg.distance(Point(v["x"], v["y"])))
    tip = pg.distance(Point(v["x"], v["y"]))
    if tip > INNER:
        print("%s %s: via %.2f mm behind the tip, outer row, no lane" % (p["ref"], net, tip))
        continue
    c = pg.centroid
    ox, oy = v["x"] - c.x, v["y"] - c.y
    if abs(ox) > abs(oy):
        u, end = ((1.0, 0.0), bx1 + END) if ox > 0 else ((-1.0, 0.0), bx0 - END)
        L = abs(end - v["x"])
    else:
        u, end = ((0.0, 1.0), by1 + END) if oy > 0 else ((0.0, -1.0), by0 - END)
        L = abs(end - v["y"])
    if L < MINL:
        print("%s %s: via already %.2f mm from the lane end, no lane" % (p["ref"], net, L))
        continue
    order = LAYERS if (("--parity" not in fl) or num % 2 == 1) else LAYERS[::-1]
    done = False
    for ln in order:
        Lc = L
        while Lc >= MINL - 1e-9:
            ls = LineString([(v["x"], v["y"]), (v["x"] + u[0] * Lc, v["y"] + u[1] * Lc)])
            bad = False
            for k in trees[ln].query(ls.buffer(0.5)):
                nm, og = obst[ln][int(k)]
                if nm != net and og.distance(ls) < CLR + W / 2:
                    bad = True
                    break
            if not bad:
                for nm, (pl, og) in placed:
                    if pl == ln and nm != net and og.distance(ls) < CLR + W / 2:
                        bad = True
                        break
            if not bad:
                out.append((net, ln, (v["x"], v["y"]), (v["x"] + u[0] * Lc, v["y"] + u[1] * Lc), Lc, p["ref"]))
                placed.append((net, (ln, ls.buffer(W / 2))))
                print("%s %s: lane on %s, %.2f mm%s" % (p["ref"], net, ln, Lc, "" if Lc >= L - 1e-9 else " (short of %.2f)" % L))
                done = True
                break
            Lc -= 0.1
        if done:
            break
    if not done:
        print("%s %s: NO lane fits" % (p["ref"], net))

txt = ""
for net, ln, a, b, L, r_ in out:
    txt += '\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %g)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (a[0], a[1], b[0], b[1], W, ln, net, uuid.uuid4())
s = open(src, encoding="utf8").read()
k = s.rindex("\t(embedded_fonts")
open(dst, "w", encoding="utf8").write(s[:k] + txt + s[k:])
print("lanes:", len(out))
