"""reroute_rects.py: like reroute_prep.py, but for any list of rectangles (e.g. the crystal keep-out box AND a chip core) and ARCS crossing a rectangle are deleted too.
Delete the track pieces (straight and arcs) that cross the rectangles, prune the dangling tails this leaves,
and write the board (true arcs, for the final merge).  Then arcs_to_segments.py makes the poly twin that tools/grid_dump.py and grid_route2.py can read:
  grid_dump.py poly.kicad_pcb grid.json ; grid_route2.py grid.json poly.kicad_pcb routed_poly.kicad_pcb NETS --exclude "x0,y0,x1,y1"
  merge_new.py poly.kicad_pcb routed_poly.kicad_pcb arc.kicad_pcb out.kicad_pcb
usage (KiCad python): reroute_rects.py in.kicad_pcb "x0,y0,x1,y1;x0,y0,x1,y1" out_arc.kicad_pcb NET [NET ...]   then   arcs_to_segments.py out_arc.kicad_pcb out_poly.kicad_pcb"""
import collections
import math
import os
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, rects, out_arc = sys.argv[1], sys.argv[2], sys.argv[3]
NETS = sys.argv[4:]
if NETS and NETS[0].startswith("@"):
    NETS = [ln.strip() for ln in open(NETS[0][1:]) if ln.strip()]
b = pcbnew.LoadBoard(src)
RECTS = [tuple(float(v) for v in r.split(",")) for r in rects.split(";") if r.strip()]


def seg_inside_any(x1, y1, x2, y2):
    return max(seg_inside(x1, y1, x2, y2, r) for r in RECTS)


def arc_inside(s, m, e):
    """sample the arc through the 3 points (nm tuples) and report whether any sample lies in a rectangle"""
    ax, ay, bx, by, cx2, cy2 = (tomm(v) for v in (s[0], s[1], m[0], m[1], e[0], e[1]))
    d = 2 * (ax * (by - cy2) + bx * (cy2 - ay) + cx2 * (ay - by))
    if abs(d) < 1e-9:
        return seg_inside_any(ax, ay, cx2, cy2) > 0.02
    ux = ((ax * ax + ay * ay) * (by - cy2) + (bx * bx + by * by) * (cy2 - ay) + (cx2 * cx2 + cy2 * cy2) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx2 - bx) + (bx * bx + by * by) * (ax - cx2) + (cx2 * cx2 + cy2 * cy2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(py - uy, px - ux) for px, py in ((ax, ay), (bx, by), (cx2, cy2)))
    n_ = lambda x: x % (2 * math.pi)
    ccw = n_(am - a0) < n_(a1 - a0)
    sweep = n_(a1 - a0) if ccw else -n_(a0 - a1)
    pts = [(ux + r * math.cos(a0 + sweep * i / 60), uy + r * math.sin(a0 + sweep * i / 60)) for i in range(61)]
    return any(any(rc[0] <= px <= rc[2] and rc[1] <= py <= rc[3] for rc in RECTS) for px, py in pts)


def seg_inside(x1, y1, x2, y2, r):
    x0, y0, x3, y3 = r
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - x0), (dx, x3 - x1), (-dy, y1 - y0), (dy, y3 - y1)):
        if p == 0:
            if q < 0:
                return 0.0
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return 0.0
                t0 = max(t0, t)
            else:
                if t < t0:
                    return 0.0
                t1 = min(t1, t)
    return max(0.0, t1 - t0) * math.hypot(dx, dy)


TOL = 3000  # nm: ends this close are connected
ONLY_LAYERS = [x for x in os.environ.get('ONLY_LAYERS', '').split(',') if x]   # e.g. ONLY_LAYERS=In2.Cu : delete only the pieces on these layers


def key(p):
    return (round(p.x / TOL), round(p.y / TOL))


removed = {}
kill_all = set()
all_pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
for net in NETS:
    # snapshot of the net's copper as plain data (items are removed by their UUID afterwards, so no stale wrappers)
    snap = {}
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        cls = t.GetClass()
        if cls == "PCB_VIA":
            p0 = t.GetPosition()
            snap[t.m_Uuid.AsString()] = dict(cls="via", layer=None, a=(p0.x, p0.y), b=(p0.x, p0.y))
        else:
            s, e = t.GetStart(), t.GetEnd()
            snap[t.m_Uuid.AsString()] = dict(cls="arc" if cls == "PCB_ARC" else "trk", layer=t.GetLayer(), a=(s.x, s.y), b=(e.x, e.y), m=((t.GetMid().x, t.GetMid().y) if cls == "PCB_ARC" else None))
    kill = set()
    for u, d in snap.items():
        if d["cls"] == "trk" and (not ONLY_LAYERS or b.GetLayerName(d["layer"]) in ONLY_LAYERS) and seg_inside_any(tomm(d["a"][0]), tomm(d["a"][1]), tomm(d["b"][0]), tomm(d["b"][1])) > 0.02:
            kill.add(u)
        elif d["cls"] == "arc" and arc_inside(d["a"], d["m"], d["b"]):
            kill.add(u)
    npads = [p for p in all_pads if p.GetNetname() == net]

    def k2(pt):
        return (round(pt[0] / TOL), round(pt[1] / TOL))

    def on_pad(pt, layer):
        v = pcbnew.VECTOR2I(int(pt[0]), int(pt[1]))
        return any(p.IsOnLayer(layer) and p.HitTest(v, 0) for p in npads)
    # prune the tails the deletion left: only chains that START at a cut point (an end of a deleted piece), so branches that were always open are not touched
    cut = set()
    for u in kill:
        d = snap[u]
        cut.add(k2(d["a"]))
        cut.add(k2(d["b"]))
    seen = {}
    for u, d in snap.items():                       # identical duplicate tracks (same layer, same ends) count as one
        if d["cls"] == "trk" and u not in kill:
            kk = (d["layer"],) + tuple(sorted((k2(d["a"]), k2(d["b"]))))
            if kk in seen:
                kill.add(u)
            else:
                seen[kk] = u
    changed = True
    while changed:
        changed = False
        alive = {u: d for u, d in snap.items() if u not in kill}
        ends = collections.defaultdict(set)
        for u, d in alive.items():
            if d["cls"] == "via":
                ends[("v",) + k2(d["a"])].add(u)
            else:
                for pt in (d["a"], d["b"]):
                    ends[(d["layer"],) + k2(pt)].add(u)
        via_keys = {k2(d["a"]) for d in alive.values() if d["cls"] == "via"}
        for u, d in alive.items():
            if d["cls"] != "trk":
                continue
            for pt, other in ((d["a"], d["b"]), (d["b"], d["a"])):
                if k2(pt) not in cut:
                    continue
                others = ends[(d["layer"],) + k2(pt)] - {u}
                if others or k2(pt) in via_keys or on_pad(pt, d["layer"]):
                    continue
                kill.add(u)
                cut.add(k2(other))
                changed = True
                break
            if changed:
                break
    alive = {u: d for u, d in snap.items() if u not in kill}
    for u, d in alive.items():                      # vias that lost every track and sit on no pad (only those at a cut point)
        if d["cls"] == "via" and k2(d["a"]) in cut:
            used = any(o["cls"] != "via" and (k2(o["a"]) == k2(d["a"]) or k2(o["b"]) == k2(d["a"])) for o in alive.values())
            if not used and not on_pad(d["a"], pcbnew.F_Cu):
                kill.add(u)
    kill_all |= kill
    removed[net] = len(kill)
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in kill_all:
        b.Remove(t)
print("removed pieces per net:", removed)
pcbnew.SaveBoard(out_arc, b)
print("wrote", out_arc, "rects", RECTS)
