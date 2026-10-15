"""Remove dangling via stubs (a via whose copper is on one layer only, typically left over after a re-route) together with the track tail that leads to nothing.
usage (KiCad python): prune_stub_vias.py in.kicad_pcb out.kicad_pcb "[(x,y,'/NET'),...]"      (positions + nets from the DRC report: "via_dangling")
Starting at each given via, the via is removed, then every track whose end sits at the removed position (or at the end of an already removed tail) and touches no other
copper of the net and no pad is removed too, until the tail is gone.  Items are removed by UUID from a snapshot (no stale wrappers)."""
import collections
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
TOL = 3000
b = pcbnew.LoadBoard(sys.argv[1])
todo = eval(sys.argv[3])


def k2(pt):
    return (round(pt[0] / TOL), round(pt[1] / TOL))


all_pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
kill_all = set()
for (x, y, net) in todo:
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
    pads = [p for p in all_pads if p.GetNetname() == net]

    def on_pad(pt, layer):
        v = pcbnew.VECTOR2I(int(pt[0]), int(pt[1]))
        return any(p.IsOnLayer(layer) and p.HitTest(v, 0) for p in pads)
    vx, vy = mm(x), mm(y)
    VR = 170000                                      # a track end within 0.17 mm of a via centre touches the via (via radius 0.15 mm + router grid)
    near = lambda p, q: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 <= VR * VR
    kill = set()
    cutpts = []
    for u, d in snap.items():
        if d["cls"] == "via" and abs(d["a"][0] - vx) < 20000 and abs(d["a"][1] - vy) < 20000:
            kill.add(u)
            vc = d["a"]
    if not kill:
        print("no via found at", x, y, net)
        continue
    for u, d in snap.items():                        # the track ends that were touching the removed via are the cut points
        if d["cls"] == "trk":
            for pt in (d["a"], d["b"]):
                if near(pt, vc):
                    cutpts.append(pt)
    changed = True
    while changed:
        changed = False
        alive = {u: d for u, d in snap.items() if u not in kill}
        vias_alive = [d["a"] for d in alive.values() if d["cls"] == "via"]
        for u, d in alive.items():
            if d["cls"] != "trk":
                continue
            for pt, other in ((d["a"], d["b"]), (d["b"], d["a"])):
                if not any((pt[0] - c[0]) ** 2 + (pt[1] - c[1]) ** 2 <= 4000 ** 2 for c in cutpts):
                    continue
                touch = any(o is not d and o["cls"] != "via" and o["layer"] == d["layer"] and any(abs(pt[0] - q[0]) <= TOL and abs(pt[1] - q[1]) <= TOL for q in (o["a"], o["b"]))
                            for o in alive.values())
                if touch or any(near(pt, v) for v in vias_alive) or on_pad(pt, d["layer"]):
                    continue
                kill.add(u)
                cutpts.append(other)
                changed = True
                break
            if changed:
                break
    print("net", net, "via at (%.3f, %.3f): removing the via and %d track pieces" % (x, y, len(kill) - 1))
    kill_all |= kill
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in kill_all:
        b.Remove(t)
pcbnew.SaveBoard(sys.argv[2], b)
