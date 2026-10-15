"""Prepare a re-route of nets that pass UNDER a chip: delete the track pieces that cross the chip's core area, prune the dangling tails this leaves,
and write the board (true arcs, for the final merge).  Then arcs_to_segments.py makes the poly twin that tools/grid_dump.py and grid_route2.py can read:
  grid_dump.py poly.kicad_pcb grid.json ; grid_route2.py grid.json poly.kicad_pcb routed_poly.kicad_pcb NETS --exclude "x0,y0,x1,y1"
  merge_new.py poly.kicad_pcb routed_poly.kicad_pcb arc.kicad_pcb out.kicad_pcb
usage (KiCad python): reroute_prep.py in.kicad_pcb REF HALF out_arc.kicad_pcb NET [NET ...]   then   arcs_to_segments.py out_arc.kicad_pcb out_poly.kicad_pcb
  REF  = the chip (its position is the centre), HALF = half side of the core square in mm (the area no routed copper may cross afterwards)
Only straight track pieces are deleted (arcs are left alone and reported)."""
import collections
import math
import os
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, ref, half, out_arc = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
NETS = sys.argv[5:]
b = pcbnew.LoadBoard(src)
f = [x for x in b.GetFootprints() if x.GetReference() == ref][0]
cx, cy = tomm(f.GetPosition().x), tomm(f.GetPosition().y)
RECT = (cx - half, cy - half, cx + half, cy + half)


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
            snap[t.m_Uuid.AsString()] = dict(cls="arc" if cls == "PCB_ARC" else "trk", layer=t.GetLayer(), a=(s.x, s.y), b=(e.x, e.y))
    arcs = [u for u, d in snap.items() if d["cls"] == "arc"]
    if arcs:
        print("  note: net", net, "has", len(arcs), "arcs (left in place)")
    kill = set()
    for u, d in snap.items():
        if d["cls"] == "trk" and (not ONLY_LAYERS or b.GetLayerName(d["layer"]) in ONLY_LAYERS) and seg_inside(tomm(d["a"][0]), tomm(d["a"][1]), tomm(d["b"][0]), tomm(d["b"][1]), RECT) > 0.02:
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
print("wrote", out_arc, "core rect", [round(v, 2) for v in RECT])
