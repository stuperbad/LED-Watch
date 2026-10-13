"""
Small grid router for the connections the polar router and freerouting leave open.   (system python: numpy, shapely, PIL)
usage: python grid_route.py grid.json in.kicad_pcb out.kicad_pcb NET [NET ...]  [--res 0.05] [--clr 0.10] [--w 0.10] [--via-cost 60] [--layers F,In1,B]
 grid.json = tools/grid_dump.py output of in.kicad_pcb.  Every named net is joined into one piece: the closest pair of its pieces is connected with an A* search
 over (layer, x, y) cells (8 directions, vias between layers), obstacles = every other net's copper inflated by clearance + half track (+ raster margin);
 vias use a larger inflation (hole to copper 0.2 mm, JLCPCB).  Existing copper is never moved.  Result: tracks + vias appended to out.kicad_pcb.
Routing layers: F.Cu, In1.Cu, B.Cu (In2.Cu is the ground plane: obstacles only, vias pass through it).
"""
import heapq
import json
import math
import sys
import time
import uuid

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

args = sys.argv[1:]
opt = {"--res": 0.05, "--clr": 0.10, "--w": 0.10, "--via-cost": 60.0, "--layers": "F,In1,B", "--in2-cost": 2.5, "--edge": 0.3, "--margin": 0.03}
pos = []
i = 0
while i < len(args):
    if args[i] in opt:
        opt[args[i]] = type(opt[args[i]])(args[i + 1])
        i += 2
    else:
        pos.append(args[i])
        i += 1
GRID, SRC, DST = pos[0], pos[1], pos[2]
NETS = pos[3:]
if NETS and NETS[0].startswith("@"):      # @file: one net name per line (git-bash rewrites a leading / in arguments)
    NETS = [ln.strip() for ln in open(NETS[0][1:]) if ln.strip()]
RES, CLR, W, VIA_COST, EDGE, MARGIN = opt["--res"], opt["--clr"], opt["--w"], opt["--via-cost"], opt["--edge"], opt["--margin"]
ALL_LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
LNAME = {"F": "F.Cu", "In1": "In1.Cu", "B": "B.Cu", "In2": "In2.Cu"}
ROUTE = [LNAME[x] for x in opt["--layers"].split(",")]
LI = {n: k for k, n in enumerate(ALL_LAYERS)}
VIA_D, VIA_DRILL = 0.30, 0.15
INF_T = CLR + W / 2 + MARGIN            # track centre to other copper
INF_V = 0.2 + VIA_DRILL / 2 + MARGIN     # via centre to other copper (hole to copper 0.2)
INF_VP = CLR + VIA_D / 2 + MARGIN        # via centre to copper (pad clearance)
INF_V = max(INF_V, INF_VP)
INF_TV = CLR + VIA_D / 2 + MARGIN        # track centre to an existing via of another net

d = json.load(open(GRID))
x0, y0 = d["bbox"][0] - 1.0, d["bbox"][1] - 1.0
Wc = int((d["bbox"][2] - d["bbox"][0] + 2.0) / RES) + 1
Hc = int((d["bbox"][3] - d["bbox"][1] + 2.0) / RES) + 1
print("grid", Wc, "x", Hc, "cells,", len(NETS), "nets", flush=True)

netid = {}


def nid(name):
    if not name:
        return 99999          # copper without a net (unused pins, NPTH rings, dummies) is an obstacle for everybody
    if name not in netid:
        netid[name] = len(netid) + 1
    return netid[name]


def px(x, y):
    return ((x - x0) / RES, (y - y0) / RES)


def paint(stack, geom, owner, layer):
    """write `owner` into stack[layer] where geom covers; a cell claimed by two different nets becomes -1"""
    if geom.is_empty:
        return
    minx, miny, maxx, maxy = geom.bounds
    ax, ay = max(0, int((minx - x0) / RES) - 1), max(0, int((miny - y0) / RES) - 1)
    bx, by = min(Wc, int((maxx - x0) / RES) + 2), min(Hc, int((maxy - y0) / RES) + 2)
    if bx <= ax or by <= ay:
        return
    im = Image.new("1", (bx - ax, by - ay), 0)
    dr = ImageDraw.Draw(im)
    polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
    for pg in polys:
        if pg.geom_type != "Polygon":
            continue
        dr.polygon([((x - x0) / RES - ax, (y - y0) / RES - ay) for x, y in pg.exterior.coords], fill=1)
        for hole in pg.interiors:
            dr.polygon([((x - x0) / RES - ax, (y - y0) / RES - ay) for x, y in hole.coords], fill=0)
    m = np.array(im, dtype=bool)
    sl = stack[layer][ay:by, ax:bx]
    free = m & (sl == 0)
    clash = m & (sl != 0) & (sl != owner)
    sl[free] = owner
    sl[clash] = -1


def item_geoms(it):
    """(layer index, shapely geometry, net) pieces of one dumped item for the connectivity test (no inflation)"""
    out = []
    return out


# ---- items
tstack = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]   # inflated for tracks
vstack = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]   # inflated for via centres
cstack = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]   # raw copper (net ids), for sources / targets
items = []   # (net, layer, geom)
for p in d["pads"]:
    g = Polygon(p["pts"]).buffer(0)
    items.append((p["net"], LI[p["layer"]], g, "pad", "pad" + p["ref"]))
for v in d["via"]:
    g = Point(v["x"], v["y"]).buffer(v["d"] / 2, 8)
    for ln in range(4):
        items.append((v["net"], ln, g, "via", "via%.4f,%.4f" % (v["x"], v["y"])))
for t in d["trk"]:
    if "arc" in t:
        sx, sy, mx, my, ex, ey = t["arc"]
        g = LineString([(sx, sy), (mx, my), (ex, ey)]).buffer(t["w"] / 2, 4)
    else:
        g = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 4)
    items.append((t["net"], LI[t["layer"]], g, "trk", None))
t0 = time.time()
for net, ln, g, kind, gid in items:
    o = nid(net)
    for st, inf in ((tstack, INF_TV if kind == "via" else INF_T), (vstack, INF_V)):
        paint(st, g.buffer(inf, 4), o, ln)
    paint(cstack, g, o, ln)
    if kind == "via":      # hole to hole >= 0.2 mm for every pair of vias, same net or not
        paint(vstack, Point(g.centroid.x, g.centroid.y).buffer(VIA_DRILL + 0.2 + MARGIN, 8), -1, ln)
print("rasterised", len(items), "items in %.0f s" % (time.time() - t0), flush=True)

# drilled holes (PTH / NPTH): hole edge to a track 0.28 mm (JLCPCB), to a via hole at least as much
for c in d["circles"]:
    o = nid(c["net"])
    g = Point(c["x"], c["y"])
    for ln in range(4):
        paint(tstack, g.buffer(c["r"] + 0.28 + W / 2 + MARGIN, 8), o, ln)
        paint(vstack, g.buffer(c["r"] + 0.28 + VIA_DRILL / 2 + MARGIN, 8), -1 if o == 99999 else o, ln)
        paint(vstack, g.buffer(c["r"] + 0.2 + VIA_DRILL / 2 + MARGIN, 8), -1, ln)      # hole to hole

# board edge + slots
outer = None
holes = []
for e in d["edge"]:
    if e["kind"] == "poly":
        pg = Polygon(e["pts"]).buffer(0)
        if outer is None or pg.area > outer.area:
            if outer is not None:
                holes.append(outer)
            outer = pg
        else:
            holes.append(pg)
for st, inf in ((tstack, EDGE + W / 2 + MARGIN), (vstack, EDGE + VIA_D / 2 + MARGIN)):
    bad_out = outer.buffer(10).difference(outer.buffer(-inf))
    bad = unary_union([bad_out] + [h.buffer(inf) for h in holes])
    for ln in range(4):
        paint(st, bad, -1, ln)

# ---- connectivity of each net
by_net = {}
for net, ln, g, kind, gid in items:
    by_net.setdefault(net, []).append((ln, g, gid))


def components(net):
    its = by_net.get(net, [])
    n = len(its)
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    tree = STRtree([it[1] for it in its])
    firstof = {}
    for a in range(n):
        gid = its[a][2]
        if gid is not None:
            if gid in firstof:
                par[find(a)] = find(firstof[gid])
            else:
                firstof[gid] = a
    for a in range(n):
        for b in tree.query(its[a][1].buffer(0.01)):
            b = int(b)
            if b > a and its[a][0] == its[b][0] and its[a][1].distance(its[b][1]) < 0.003:
                par[find(a)] = find(b)
    comps = {}
    for a in range(n):
        comps.setdefault(find(a), []).append(its[a])
    return list(comps.values())


def comp_dist(ca, cb):
    return min(ga.distance(gb) for _, ga, _ in ca for _, gb, _ in cb)


def comp_mask(comp, shape):
    m = np.zeros((len(ALL_LAYERS),) + shape, dtype=bool)
    for ln, g, _ in comp:
        minx, miny, maxx, maxy = g.bounds
        ax, ay = max(0, int((minx - x0) / RES) - 1), max(0, int((miny - y0) / RES) - 1)
        bx, by = min(Wc, int((maxx - x0) / RES) + 2), min(Hc, int((maxy - y0) / RES) + 2)
        im = Image.new("1", (bx - ax, by - ay), 0)
        dr = ImageDraw.Draw(im)
        for pg in ([g] if g.geom_type == "Polygon" else list(g.geoms)):
            dr.polygon([((x - x0) / RES - ax, (y - y0) / RES - ay) for x, y in pg.exterior.coords], fill=1)
        m[ln, ay:by, ax:bx] |= np.array(im, dtype=bool)
    return m


RL = [LI[n] for n in ROUTE]       # routing layer indices
LCOST = [opt["--in2-cost"] if ALL_LAYERS[ln] == "In2.Cu" else 1.0 for ln in RL]   # In2 is the ground plane: use it only when nothing else works
# nothing but the ground plane under the crystal circuit (AVR datasheet 4.5.1)
for e in ("Y1",):
    ys = [Polygon(p["pts"]) for p in d["pads"] if p["ref"].startswith("Y1.")]
    if ys:
        cx, cy = ys[0].centroid.x, ys[0].centroid.y
        paint(tstack, Polygon([(cx - 2.4, cy - 2.5), (cx + 4.1, cy - 2.5), (cx + 4.1, cy + 3.5), (cx - 2.4, cy + 3.5)]), -1, LI["In2.Cu"])


def astar(net_o, src_mask, dst_mask):
    """multi-source A*; cells are (k, y, x) with k the index in RL.  returns list of (k, y, x) or None"""
    nl = len(RL)
    free = []
    for ln in RL:
        t = tstack[ln]
        free.append(((t == 0) | (t == net_o)).ravel())
    # copper of the net itself is always usable
    for k, ln in enumerate(RL):
        free[k] = free[k] | (src_mask[ln].ravel()) | (dst_mask[ln].ravel())
    vok = np.ones((Hc, Wc), dtype=bool)
    for ln in range(4):
        v = vstack[ln]
        vok &= (v == 0) | (v == net_o)
    vok = vok.ravel()
    free = [f.tolist() for f in free]
    vok = vok.tolist()
    dsts = [dst_mask[ln].ravel().tolist() for ln in RL]
    # heuristic: distance to the bounding box of the target cells
    ys, xs = np.nonzero(np.any([dst_mask[ln] for ln in RL], axis=0))
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    N = Hc * Wc
    INF = 1e18
    g = [[INF] * N for _ in range(nl)]
    came = [dict() for _ in range(nl)]
    pq = []
    for k, ln in enumerate(RL):
        yy, xx = np.nonzero(src_mask[ln])
        for y, x in zip(yy.tolist(), xx.tolist()):
            i = y * Wc + x
            g[k][i] = 0.0
            came[k][i] = None
            heapq.heappush(pq, (0.0, 0.0, k, i))
    SQ = 1.41421356
    moves = [(-1, -1, SQ), (-1, 0, 1.0), (-1, 1, SQ), (0, -1, 1.0), (0, 1, 1.0), (1, -1, SQ), (1, 0, 1.0), (1, 1, SQ)]
    pops = 0
    while pq:
        f, gc, k, i = heapq.heappop(pq)
        if gc > g[k][i]:
            continue
        pops += 1
        if dsts[k][i]:
            path = []
            cur = (k, i)
            while cur is not None:
                path.append((cur[0], cur[1] // Wc, cur[1] % Wc))
                cur = came[cur[0]][cur[1]]
            path.reverse()
            return path, pops
        y, x = divmod(i, Wc)
        fk = free[k]
        for dy, dx, c in moves:
            ny, nx = y + dy, x + dx
            if ny < 0 or nx < 0 or ny >= Hc or nx >= Wc:
                continue
            j = ny * Wc + nx
            if not fk[j]:
                continue
            ng = gc + c * LCOST[k]
            if ng < g[k][j]:
                g[k][j] = ng
                came[k][j] = (k, i)
                dxm = max(bx0 - nx, 0, nx - bx1)
                dym = max(by0 - ny, 0, ny - by1)
                h = (max(dxm, dym) + 0.414 * min(dxm, dym))
                heapq.heappush(pq, (ng + h, ng, k, j))
        if vok[i]:
            for k2 in range(nl):
                if k2 != k and free[k2][i]:
                    ng = gc + VIA_COST
                    if ng < g[k2][i]:
                        g[k2][i] = ng
                        came[k2][i] = (k, i)
                        heapq.heappush(pq, (ng, ng, k2, i))
    return None, pops


def simplify(path):
    """cell path -> list of ('seg', layer, (x1,y1), (x2,y2)) and ('via', (x,y)) in mm"""
    out = []
    pts = [(k, x0 + (x + 0.5) * RES, y0 + (y + 0.5) * RES) for k, y, x in path]
    run = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        if a[0] != b[0]:
            out.append(("run", run))
            out.append(("via", (a[1], a[2])))
            run = [b]
        else:
            run.append(b)
    out.append(("run", run))
    res = []
    for kind, v in out:
        if kind == "via":
            res.append(("via", v))
            continue
        k = v[0][0]
        # drop collinear points
        keep = [v[0]]
        for p in v[1:]:
            if len(keep) >= 2:
                a, b = keep[-2], keep[-1]
                if abs((b[1] - a[1]) * (p[2] - b[2]) - (b[2] - a[2]) * (p[1] - b[1])) < 1e-9:
                    keep[-1] = p
                    continue
            keep.append(p)
        for a, b in zip(keep, keep[1:]):
            res.append(("seg", ALL_LAYERS[RL[k]], (a[1], a[2]), (b[1], b[2])))
    return res


def dump_fail(net, ma, mb):
    """picture of what the router saw: grey = blocked for tracks, green = source piece, red = target piece (one PNG per routing layer)"""
    yy, xx = np.nonzero(np.any([ma[ln] for ln in RL], axis=0))
    cx, cy = int(xx.mean()), int(yy.mean())
    r = 140
    for k, ln in enumerate(RL):
        t = tstack[ln]
        sub = t[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        img = np.zeros(sub.shape + (3,), dtype=np.uint8) + 255
        img[(sub != 0) & (sub != nid(net))] = (150, 150, 150)
        img[sub == -1] = (80, 80, 80)
        m1 = ma[ln][max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        m2 = mb[ln][max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        img[m1] = (0, 170, 0)
        img[m2] = (220, 0, 0)
        Image.fromarray(img).resize((sub.shape[1] * 3, sub.shape[0] * 3), Image.NEAREST).save("fail_%s_%s.png" % (net.strip("/"), ALL_LAYERS[ln][:3]))


new = []   # ('seg', layer, p1, p2, net) / ('via', p, net)
failed = []


def commit(net, o, segs):
    """put a routed path into the obstacle rasters and the output list; returns the new copper pieces"""
    added = []
    for s in segs:
        if s[0] == "seg":
            g = LineString([s[2], s[3]]).buffer(W / 2, 4)
            added.append((LI[s[1]], g, None))
            for st, inf in ((tstack, INF_T), (vstack, INF_V)):
                paint(st, g.buffer(inf, 4), o, LI[s[1]])
            new.append(("seg", s[1], s[2], s[3], net))
        else:
            g = Point(*s[1]).buffer(VIA_D / 2, 8)
            vid = "newvia%d" % len(new)
            for ln in range(4):
                added.append((ln, g, vid))
                paint(tstack, g.buffer(INF_TV, 4), o, ln)
                paint(vstack, g.buffer(INF_V, 4), o, ln)
            new.append(("via", s[1], net))
    by_net[net] = by_net.get(net, []) + added
    return added


def report(path, pops, t1):
    segs = simplify(path)
    nseg = sum(1 for s in segs if s[0] == "seg")
    nvia = sum(1 for s in segs if s[0] == "via")
    ln_mm = sum(math.dist(s[2], s[3]) for s in segs if s[0] == "seg")
    print(f"   routed: {nseg} segments, {nvia} vias, {ln_mm:.1f} mm, {pops} nodes, {time.time() - t1:.0f} s", flush=True)
    return segs


IN2 = LI["In2.Cu"]
for net in NETS:
    o = nid(net)
    comps = components(net)
    if net == "GND":
        # ground is the In2 plane: every piece with no copper on In2 (no via, no through-hole pad) needs a via to it
        todo = [c for c in comps if not any(it[0] == IN2 for it in c)]
        print(f"GND: {len(comps)} pieces, {len(todo)} not on the plane", flush=True)
        todo.sort(key=lambda c: -len(c))
        for c in todo:
            ma = comp_mask(c, (Hc, Wc))
            mb = np.zeros_like(ma)
            t2 = tstack[IN2]
            mb[IN2] = (t2 == 0) | (t2 == o)
            t1 = time.time()
            path, pops = astar(o, ma, mb)
            if path is None:
                print(f"   GND piece FAILED ({pops} nodes)", flush=True)
                failed.append(net)
                continue
            commit(net, o, report(path, pops, t1))
        continue
    print(f"{net}: {len(comps)} pieces", flush=True)
    tries = 0
    while len(comps) > 1 and tries < 12:
        tries += 1
        best = None
        for a in range(len(comps)):
            for b in range(a + 1, len(comps)):
                dd = comp_dist(comps[a], comps[b])
                if best is None or dd < best[0]:
                    best = (dd, a, b)
        _, a, b = best
        ma, mb = comp_mask(comps[a], (Hc, Wc)), comp_mask(comps[b], (Hc, Wc))
        t1 = time.time()
        path, pops = astar(o, ma, mb)
        if path is None:
            print(f"   FAILED between pieces (closest {best[0]:.2f} mm), {pops} nodes, {time.time() - t1:.0f} s", flush=True)
            failed.append(net)
            dump_fail(net, ma, mb)
            break
        added = commit(net, o, report(path, pops, t1))
        merged = comps[a] + comps[b] + added
        comps = [c for k, c in enumerate(comps) if k not in (a, b)] + [merged]

print("failed:", failed, flush=True)

# ---- write
src = open(SRC, encoding="utf8").read()
txt = ""
for n in new:
    if n[0] == "seg":
        txt += '\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %g)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (
            n[2][0], n[2][1], n[3][0], n[3][1], W, n[1], n[4], uuid.uuid4())
    else:
        txt += '\t(via\n\t\t(at %.4f %.4f)\n\t\t(size %g)\n\t\t(drill %g)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (
            n[1][0], n[1][1], VIA_D, VIA_DRILL, n[2], uuid.uuid4())
k = src.rindex("\t(embedded_fonts")
open(DST, "w", encoding="utf8").write(src[:k] + txt + src[k:])
print("wrote", DST, len([n for n in new if n[0] == "seg"]), "segments,", len([n for n in new if n[0] == "via"]), "vias", flush=True)
