"""Re-draw every routed chain as the SHORTEST route made of 0/45/90 degree pieces, wherever that is free of collisions.
A chain = straight track pieces of one net, one layer and one width between two fixed points.  Fixed points never move: via centres, pad centres, junctions (3+ pieces), chain ends, arc joints.
For each chain the polyline is walked greedily: from the current vertex try to reach the farthest later vertex with a two-piece 45-degree dogleg (or one straight piece); a candidate is accepted
only if it keeps the clearance to everything of another net (0.105 mm to copper, 0.205 mm to holes, 0.3 mm to the board edge).  Where nothing shorter fits the original pieces stay.
Branch ends that touch the body of another piece of their net (T junctions) are first made real junctions, so no connection can be lost.
usage (KiCad python): octo_opt.py in.kicad_pcb out.kicad_pcb [skip.json]     writes out.chains.json (chain ids + bounding boxes) for octo_loop.py; chains in skip.json are left as they are"""
import collections
import json
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
V = pcbnew.VECTOR2I
src, dst = sys.argv[1], sys.argv[2]
skip = set(json.load(open(sys.argv[3]))) if len(sys.argv) > 3 else set()
CLR, HOLE_CLR, EDGE_CLR = mm(0.105), mm(0.205), mm(0.305)
CELL = 1000000
b = pcbnew.LoadBoard(src)

# ---------------------------------------------------------------- the board as plain records
recs = []                                       # straight track pieces
vias, arcs = [], []
for t in b.GetTracks():
    c = t.GetClass()
    if c == "PCB_TRACK":
        recs.append(dict(net=t.GetNetname(), nobj=t.GetNet(), layer=t.GetLayer(), w=t.GetWidth(), a=(t.GetStart().x, t.GetStart().y), b=(t.GetEnd().x, t.GetEnd().y), obj=t))
    elif c == "PCB_VIA":
        vias.append(t)
    else:
        arcs.append(t)
pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
arc_keys = set()
for a in arcs:
    for p in (a.GetStart(), a.GetEnd()):
        arc_keys.add((a.GetNetname(), a.GetLayer(), round(p.x / 1000), round(p.y / 1000)))


def K(p):
    return (round(p[0] / 1000), round(p[1] / 1000))


def seg_dist(p, a, c):
    ux, uy, wx, wy = c[0] - a[0], c[1] - a[1], p[0] - a[0], p[1] - a[1]
    L2 = ux * ux + uy * uy
    t = max(0.0, min(1.0, (wx * ux + wy * uy) / L2)) if L2 else 0.0
    return math.hypot(wx - t * ux, wy - t * uy), t


# ---------------------------------------------------------------- T junction pre-pass: a free end on the body of another piece of its net becomes a real joint
def near_centre(net, layer, p):
    for v in vias:
        if v.GetNetname() == net and abs(v.GetPosition().x - p[0]) < 3000 and abs(v.GetPosition().y - p[1]) < 3000:
            return True
    for pd in pads:
        if pd.GetNetname() == net and pd.IsOnLayer(layer) and abs(pd.GetPosition().x - p[0]) < 3000 and abs(pd.GetPosition().y - p[1]) < 3000:
            return True
    return False


def weld():
    """a track end that reaches another piece of its net only by overlapping it (side or offset vertex) is moved onto a SHARED point:
    onto the other piece's vertex when it is at one, otherwise the other piece is split at the touching point"""
    n_weld = 0
    for _ in range(40):
        nodes = collections.defaultdict(list)
        for r in recs:
            for which in ("a", "b"):
                nodes[(r["net"], r["layer"], K(r[which]))].append((r, which))
        for r in recs:                           # ends in the same 1 um bucket become one exact point
            for which in ("a", "b"):
                k = (r["net"], r["layer"], K(r[which]))
                first = nodes[k][0]
                r[which] = first[0][first[1]]
        by_nl = collections.defaultdict(list)
        for r in recs:
            by_nl[(r["net"], r["layer"])].append(r)
        add = []
        changed = False
        for (net, layer, key), inc in list(nodes.items()):
            if len(inc) != 1 or (net, layer, key) in arc_keys:
                continue
            r, which = inc[0]
            p = r[which]
            if near_centre(net, layer, p):
                continue
            best = None
            for h in by_nl[(net, layer)]:
                if h is r or h.get("dead"):
                    continue
                d, tt = seg_dist(p, h["a"], h["b"])
                if d < (h["w"] + r["w"]) / 2 + mm(0.005) and (best is None or d < best[0]):
                    best = (d, h, tt)
            if not best:
                continue
            d, h, tt = best
            L = math.hypot(h["b"][0] - h["a"][0], h["b"][1] - h["a"][1])
            if tt * L < mm(0.03):
                q = h["a"]
            elif (1 - tt) * L < mm(0.03):
                q = h["b"]
            else:
                q = (round(h["a"][0] + tt * (h["b"][0] - h["a"][0])), round(h["a"][1] + tt * (h["b"][1] - h["a"][1])))
                add.append(dict(net=h["net"], nobj=h["nobj"], layer=h["layer"], w=h["w"], a=q, b=h["b"], obj=None))
                h["b"] = q
            if q != p:
                r[which] = q
                n_weld += 1
                changed = True
            if add:
                break                              # the lists are stale after a split: rebuild
        recs.extend(add)
        if not changed:
            break
    return n_weld


seen_dup = set()
for r in list(recs):                              # identical duplicate pieces (same net, layer, ends) count once
    k = (r["net"], r["layer"]) + tuple(sorted([r["a"], r["b"]]))
    if k in seen_dup or r["a"] == r["b"]:
        r["dead"] = True
    seen_dup.add(k)
recs[:] = [r for r in recs if not r.get("dead")]
nsplit = weld()

# ---------------------------------------------------------------- obstacle index
items = {}
cells = collections.defaultdict(set)            # (layer, cx, cy) -> ids
holes = []                                      # (shape, net, clr) on every layer
nid = [0]


def bbox_of(shape):
    bb = shape.BBox()
    return (bb.GetX(), bb.GetY(), bb.GetX() + bb.GetWidth(), bb.GetY() + bb.GetHeight())


def add_item(layer, shape, net, clr, owner=None):
    nid[0] += 1
    i = nid[0]
    bx = bbox_of(shape)
    items[i] = dict(shape=shape, net=net, clr=clr, bb=bx, layer=layer, owner=owner)
    for cx in range(int(bx[0] // CELL), int(bx[2] // CELL) + 1):
        for cy in range(int(bx[1] // CELL), int(bx[3] // CELL) + 1):
            cells[(layer, cx, cy)].add(i)
    return i


def drop_item(i):
    it = items.pop(i)
    bx = it["bb"]
    for cx in range(int(bx[0] // CELL), int(bx[2] // CELL) + 1):
        for cy in range(int(bx[1] // CELL), int(bx[3] // CELL) + 1):
            cells[(it["layer"], cx, cy)].discard(i)


copper_layers = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
for L in copper_layers:
    for v in vias:
        add_item(L, v.GetEffectiveShape(L), v.GetNetname(), CLR)
    for pd in pads:
        if pd.IsOnLayer(L):
            add_item(L, pd.GetEffectiveShape(L), pd.GetNetname(), CLR)
    for a in arcs:
        if a.GetLayer() == L:
            add_item(L, a.GetEffectiveShape(), a.GetNetname(), CLR)
edge = []
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        edge.append(d.GetEffectiveShape())
hole_shapes = []
for v in vias:
    hole_shapes.append((v.GetEffectiveHoleShape(), v.GetNetname(), HOLE_CLR))
for pd in pads:
    if pd.HasHole():
        hole_shapes.append((pd.GetEffectiveHoleShape(), pd.GetNetname(), HOLE_CLR))
for L in copper_layers:
    for sh, net, clr in hole_shapes:
        add_item(L, sh, net, clr)
    for sh in edge:
        add_item(L, sh, "<edge>", EDGE_CLR)
rec_items = collections.defaultdict(list)       # id(rec) -> item ids, for the pieces currently in the index


def index_rec(r):
    r["sh"] = pcbnew.SHAPE_SEGMENT(V(int(r["a"][0]), int(r["a"][1])), V(int(r["b"][0]), int(r["b"][1])), r["w"])
    rec_items[id(r)].append(add_item(r["layer"], r["sh"], r["net"], CLR))


for r in recs:
    index_rec(r)


def free(layer, net, a, c, w):
    sh = pcbnew.SHAPE_SEGMENT(V(int(a[0]), int(a[1])), V(int(c[0]), int(c[1])), w)
    m = w // 2 + HOLE_CLR + 20000
    x0, x1 = min(a[0], c[0]) - m, max(a[0], c[0]) + m
    y0, y1 = min(a[1], c[1]) - m, max(a[1], c[1]) + m
    seen = set()
    for cx in range(int(x0 // CELL), int(x1 // CELL) + 1):
        for cy in range(int(y0 // CELL), int(y1 // CELL) + 1):
            for i in cells.get((layer, cx, cy), ()):
                if i in seen:
                    continue
                seen.add(i)
                it = items[i]
                if it["net"] == net:
                    continue
                bx = it["bb"]
                if bx[2] + it["clr"] < min(a[0], c[0]) - w // 2 or bx[0] - it["clr"] > max(a[0], c[0]) + w // 2 or bx[3] + it["clr"] < min(a[1], c[1]) - w // 2 or bx[1] - it["clr"] > max(a[1], c[1]) + w // 2:
                    continue
                if sh.Collide(it["shape"], it["clr"]):
                    return False
    return True


# ---------------------------------------------------------------- chains
ends = collections.defaultdict(list)
for r in recs:
    for w_, p in (("a", r["a"]), ("b", r["b"])):
        ends[(r["net"], r["layer"], K(p))].append((r, w_))


def at_centre(net, layer, p):
    for v in vias:
        if v.GetNetname() == net and abs(v.GetPosition().x - p[0]) < 3000 and abs(v.GetPosition().y - p[1]) < 3000:
            return True
    for pd in pads:
        if pd.GetNetname() == net and pd.IsOnLayer(layer) and abs(pd.GetPosition().x - p[0]) < 3000 and abs(pd.GetPosition().y - p[1]) < 3000:
            return True
    return False


by_nl2 = collections.defaultdict(list)
for r in recs:
    by_nl2[(r["net"], r["layer"])].append(r)


def is_fixed(r, p):
    k = (r["net"], r["layer"], K(p))
    if len(ends[k]) != 2 or k in arc_keys or at_centre(r["net"], r["layer"], p):
        return True
    inc = {id(x[0]) for x in ends[k]}
    for a in arcs:
        if a.GetNetname() == r["net"] and a.GetLayer() == r["layer"] and a.GetEffectiveShape().Collide(pcbnew.SHAPE_SEGMENT(V(int(p[0]), int(p[1])), V(int(p[0]), int(p[1])), r["w"]), 0):
            return True
    for v in vias:                                                 # touches a via / pad: only a stub that leads to its centre may be merged away
        if v.GetNetname() == r["net"] and math.hypot(v.GetPosition().x - p[0], v.GetPosition().y - p[1]) < v.GetWidth(pcbnew.F_Cu) / 2 + r["w"] / 2 + 30000:
            c = (v.GetPosition().x, v.GetPosition().y)
            if not any(abs(oth[0] - c[0]) < 3000 and abs(oth[1] - c[1]) < 3000 for rr, _w in ends[k] for oth in (rr["a"], rr["b"])):
                return True
    for pd in pads:
        if pd.GetNetname() == r["net"] and pd.IsOnLayer(r["layer"]) and pd.HitTest(V(int(p[0]), int(p[1])), r["w"] // 2 + 30000):
            c = (pd.GetPosition().x, pd.GetPosition().y)
            if not any(abs(oth[0] - c[0]) < 3000 and abs(oth[1] - c[1]) < 3000 for rr, _w in ends[k] for oth in (rr["a"], rr["b"])):
                return True
    return False


seen = set()
chains = []
for r in recs:
    if id(r) in seen:
        continue
    seen.add(id(r))
    pieces = [(r, r["a"], r["b"])]            # (rec, from, to) in walking order
    for direction in (0, 1):
        cur, cur_end = r, (r["b"] if direction == 0 else r["a"])
        while not is_fixed(cur, cur_end):
            nxt = [x for x in ends[(r["net"], r["layer"], K(cur_end))] if x[0] is not cur]
            if len(nxt) != 1 or id(nxt[0][0]) in seen or nxt[0][0]["w"] != r["w"]:
                break
            nr, w_ = nxt[0]
            seen.add(id(nr))
            fro, to = (nr["a"], nr["b"]) if w_ == "a" else (nr["b"], nr["a"])
            if direction == 0:
                pieces.append((nr, fro, to))
                cur_end = to
            else:
                pieces.insert(0, (nr, to, fro))
                cur_end = to
            cur = nr
    chains.append(pieces)


def split_chain(pieces):
    """cut a chain where a piece of ANOTHER chain of the same net touches one of its interior vertices"""
    mine = {id(x[0]) for x in pieces}
    cuts = []
    for i in range(1, len(pieces)):
        p = pieces[i][1]
        if any(id(o) not in mine and seg_dist(p, o["a"], o["b"])[0] < o["w"] / 2 + pieces[0][0]["w"] / 2 + mm(0.01) for o in by_nl2[(pieces[0][0]["net"], pieces[0][0]["layer"])]):
            cuts.append(i)
    out, prev = [], 0
    for i in cuts + [len(pieces)]:
        out.append(pieces[prev:i])
        prev = i
    return [x for x in out if x]


chains = [c for ch in chains for c in split_chain(ch)]


def octo(P, Q):
    """candidate pieces from P to Q: straight if on a 0/45/90 line, else the two 2-piece doglegs"""
    dx, dy = Q[0] - P[0], Q[1] - P[1]
    if dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) <= 2:
        return [[P, Q]]
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    m = min(abs(dx), abs(dy))
    k1 = (P[0] + sx * m, P[1] + sy * m)          # diagonal first
    k2 = (Q[0] - sx * m, Q[1] - sy * m)          # straight first
    return [[P, k1, Q], [P, k2, Q]]


def is_octo(a, c):
    dx, dy = abs(c[0] - a[0]), abs(c[1] - a[1])
    return dx <= 2 or dy <= 2 or abs(dx - dy) <= 2


def poly_dist(p, poly):
    return min(seg_dist(p, a, c)[0] for a, c in zip(poly[:-1], poly[1:]))


def length(poly):
    return sum(math.hypot(c[0] - a[0], c[1] - a[1]) for a, c in zip(poly[:-1], poly[1:]))


info, new_chain = [], {}
len_before = len_after = 0.0
angles_before = angles_after = 0
changed = 0
for pieces in chains:
    r0 = pieces[0][0]
    net, layer, w = r0["net"], r0["layer"], r0["w"]
    pts = [pieces[0][1]] + [p[2] for p in pieces]
    cid = "%s|%s|%d,%d" % (net, b.GetLayerName(layer), pts[0][0], pts[0][1])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    info.append(dict(id=cid, bbox=[tomm(min(xs)), tomm(min(ys)), tomm(max(xs)), tomm(max(ys))], pts=[[tomm(x_), tomm(y_)] for x_, y_ in pts]))
    len_before += length(pts)
    angles_before += sum(1 for a, c in zip(pts[:-1], pts[1:]) if not is_octo(a, c))
    if cid in skip:
        len_after += length(pts)
        angles_after += sum(1 for a, c in zip(pts[:-1], pts[1:]) if not is_octo(a, c))
        continue
    # drop this chain's own pieces from the index while its new route is being tried (same net, so they would not block anyway)
    out = [pts[0]]
    i, n = 0, len(pts) - 1
    while i < n:
        took = False
        for j in range(n, i, -1):
            cands = octo(pts[i], pts[j])
            cands = sorted(cands, key=lambda c: sum(poly_dist(q, pts[i:j + 1]) for q in c[1:-1]))
            for cand in cands:
                if all(free(layer, net, a, c, w) for a, c in zip(cand[:-1], cand[1:])):
                    out.extend(cand[1:])
                    took = True
                    break
            if took:
                i = j
                break
        if not took:                         # nothing fits: keep the original piece
            out.append(pts[i + 1])
            i += 1
    # remove repeated points and merge collinear neighbours
    clean = [out[0]]
    for p in out[1:]:
        if p != clean[-1]:
            clean.append(p)
    merged = [clean[0]]
    for p in clean[1:]:
        if len(merged) >= 2:
            a, c = merged[-2], merged[-1]
            if (c[0] - a[0]) * (p[1] - c[1]) - (c[1] - a[1]) * (p[0] - c[0]) == 0 and (c[0] - a[0]) * (p[0] - c[0]) + (c[1] - a[1]) * (p[1] - c[1]) > 0:
                merged[-1] = p
                continue
        merged.append(p)
    # keep only if shorter or fewer bent pieces
    better = length(merged) < length(pts) - 1000 or sum(1 for a, c in zip(merged[:-1], merged[1:]) if not is_octo(a, c)) < sum(1 for a, c in zip(pts[:-1], pts[1:]) if not is_octo(a, c)) or len(merged) < len(pts)
    if not better or merged == pts:
        len_after += length(pts)
        angles_after += sum(1 for a, c in zip(pts[:-1], pts[1:]) if not is_octo(a, c))
        continue
    changed += 1
    len_after += length(merged)
    angles_after += sum(1 for a, c in zip(merged[:-1], merged[1:]) if not is_octo(a, c))
    for rr, _a, _c in pieces:
        for i_ in rec_items.pop(id(rr), []):
            drop_item(i_)
        rr["dead"] = True
    for a, c in zip(merged[:-1], merged[1:]):
        nr = dict(net=net, nobj=r0["nobj"], layer=layer, w=w, a=a, b=c, obj=None)
        recs.append(nr)
        index_rec(nr)

# ---------------------------------------------------------------- write back: all straight pieces are re-created from the records
for t in [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]:
    b.Remove(t)
n_out = 0
for r in recs:
    if r.get("dead"):
        continue
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(int(r["a"][0]), int(r["a"][1])))
    t.SetEnd(V(int(r["b"][0]), int(r["b"][1])))
    t.SetWidth(r["w"])
    t.SetLayer(r["layer"])
    t.SetNet(r["nobj"])
    b.Add(t)
    n_out += 1
pcbnew.SaveBoard(dst, b)
json.dump(info, open(dst + ".chains.json", "w"))
print("loose joints welded %d, chains %d changed %d, pieces now %d, length %.1f -> %.1f mm, non-45 pieces %d -> %d" % (
    nsplit, len(chains), changed, n_out, len_before / 1e6, len_after / 1e6, angles_before, angles_after))
