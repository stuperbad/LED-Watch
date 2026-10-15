"""Straighten the router's 0.05 mm staircase wobble: every chain of straight track pieces (same net, same layer) between two fixed points is replaced by the
Douglas-Peucker simplification of its polyline.  Fixed points (never moved, never removed): chain ends, junctions of 3+ pieces, via centres, anything within reach of a via or pad of the net.
usage (KiCad python): simplify_chains.py in.kicad_pcb out.kicad_pcb [TOL_mm=0.06] [skip.json]      prints  "chains N changed M pieces before -> after"  and writes chains.json (id, bbox) next to out
skip.json: list of chain ids (as printed in chains.json of an earlier run) to leave untouched.  Run DRC afterwards (and fix_gnd_zone.py): drive it with simplify_loop.py."""
import collections
import json
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.06
skip = set(json.load(open(sys.argv[4]))) if len(sys.argv) > 4 else set()
b = pcbnew.LoadBoard(src)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
trks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC"]


def K(p):
    return (round(p.x / 1000), round(p.y / 1000))


ends = collections.defaultdict(list)           # (net, layer, key) -> [(uuid, which)]
for t in trks:
    for w, p in (("s", t.GetStart()), ("e", t.GetEnd())):
        ends[(t.GetNetname(), t.GetLayer(), K(p))].append((t.m_Uuid.AsString(), w))
arc_keys = set()
for a in arcs:
    for p in (a.GetStart(), a.GetEnd()):
        arc_keys.add((a.GetNetname(), a.GetLayer(), K(p)))
byid = {t.m_Uuid.AsString(): t for t in trks}


def fixed(net, layer, key, p, hw):
    if len(ends[(net, layer, key)]) != 2 or (net, layer, key) in arc_keys:
        return True
    for v in vias:
        if v.GetNetname() == net and math.hypot(tomm(v.GetPosition().x - p.x), tomm(v.GetPosition().y - p.y)) < tomm(v.GetWidth(pcbnew.F_Cu)) / 2 + tomm(hw) + 0.03:
            return True
    for pd in pads:
        if pd.GetNetname() == net and pd.IsOnLayer(layer) and pd.HitTest(p, hw + 30000):
            return True
    return False


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    L = math.hypot(x2 - x1, y2 - y1)
    best, bi = -1, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = math.hypot(x - x1, y - y1) if L == 0 else abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)) / L
        if d > best:
            best, bi = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return dp(pts[:bi + 1], tol)[:-1] + dp(pts[bi:], tol)


seen, chains = set(), []
for t in trks:
    u0 = t.m_Uuid.AsString()
    if u0 in seen:
        continue
    net, layer, hw = t.GetNetname(), t.GetLayer(), t.GetWidth() // 2
    # walk both directions from this piece while the shared node is a plain pass-through
    pieces, order = [u0], [(t.GetStart(), t.GetEnd())]
    seen.add(u0)
    for direction in (0, 1):
        cur = t
        cur_end = cur.GetEnd() if direction == 0 else cur.GetStart()
        while True:
            key = K(cur_end)
            if fixed(net, layer, key, cur_end, hw):
                break
            nxt = [x for x in ends[(net, layer, key)] if x[0] != cur.m_Uuid.AsString()]
            if len(nxt) != 1 or nxt[0][0] in seen or byid[nxt[0][0]].GetWidth() != t.GetWidth():
                break
            nt = byid[nxt[0][0]]
            seen.add(nxt[0][0])
            a, c = (nt.GetStart(), nt.GetEnd()) if nxt[0][1] == "s" else (nt.GetEnd(), nt.GetStart())
            if direction == 0:
                pieces.append(nxt[0][0]); order.append((a, c)); cur_end = c
            else:
                pieces.insert(0, nxt[0][0]); order.insert(0, (c, a)); cur_end = c
            cur = nt
    chains.append((net, layer, t.GetWidth(), t.GetNet(), pieces, order))

kill, new, info, changed = set(), [], [], 0
for idx, (net, layer, w, netobj, pieces, order) in enumerate(chains):
    if len(pieces) < 3:
        continue
    pts = [(order[0][0].x, order[0][0].y)] + [(o[1].x, o[1].y) for o in order]
    cid = "%s|%s|%d,%d" % (net, b.GetLayerName(layer), pts[0][0], pts[0][1])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    info.append(dict(id=cid, bbox=[tomm(min(xs)), tomm(min(ys)), tomm(max(xs)), tomm(max(ys))]))
    if cid in skip:
        continue
    simp = dp(pts, mm(TOL))
    if len(simp) - 1 >= len(pieces):
        continue
    changed += 1
    kill |= set(pieces)
    for (x1, y1), (x2, y2) in zip(simp[:-1], simp[1:]):
        new.append((x1, y1, x2, y2, w, layer, netobj))
for u in kill:
    b.Remove(byid[u])
for x1, y1, x2, y2, w, layer, netobj in new:
    s = pcbnew.PCB_TRACK(b)
    s.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
    s.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
    s.SetWidth(w)
    s.SetLayer(layer)
    s.SetNet(netobj)
    b.Add(s)
pcbnew.SaveBoard(dst, b)
json.dump(info, open(dst + ".chains.json", "w"))
print("chains %d changed %d pieces %d -> %d" % (len(chains), changed, len(kill), len(new)))
