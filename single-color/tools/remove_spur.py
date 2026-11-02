"""Remove a dead-end spur: starting at a free track end (x, y) of a net on a layer, delete that track, then the next one that continues from its other end, and so on, until the walk reaches a point where
another track, a via or a pad of the net touches (the junction itself stays).   Prints what was removed.
usage (KiCad python): remove_spur.py in.kicad_pcb out.kicad_pcb NET LAYER x y [NET LAYER x y ...]"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
EPS = 0.012
pads = [p for f in b.GetFootprints() for p in f.Pads()]
snap = []                                  # plain data (no SWIG objects are touched after a Remove)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        snap.append(dict(obj=t, via=True, net=t.GetNetname(), layer=-1, a=(tomm(t.GetPosition().x), tomm(t.GetPosition().y)), b=None, alive=True))
    elif t.GetClass() == "PCB_TRACK":
        snap.append(dict(obj=t, via=False, net=t.GetNetname(), layer=t.GetLayer(), a=(tomm(t.GetStart().x), tomm(t.GetStart().y)), b=(tomm(t.GetEnd().x), tomm(t.GetEnd().y)), alive=True))
args = sys.argv[3:]
for k in range(0, len(args), 4):
    net, layer, x, y = args[k], args[k + 1], float(args[k + 2]), float(args[k + 3])
    lid = b.GetLayerID(layer)
    cur = (x, y)
    while True:
        hit = [r for r in snap if r["alive"] and not r["via"] and r["net"] == net and r["layer"] == lid and min(math.hypot(r["a"][0] - cur[0], r["a"][1] - cur[1]), math.hypot(r["b"][0] - cur[0], r["b"][1] - cur[1])) < EPS]
        if len(hit) != 1:
            print("stop at", cur, "with", len(hit), "tracks")
            break
        r = hit[0]
        far = r["b"] if math.hypot(r["a"][0] - cur[0], r["a"][1] - cur[1]) < EPS else r["a"]
        r["alive"] = False
        print("removed", net, layer, "(%.3f, %.3f)-(%.3f, %.3f)" % (r["a"] + r["b"]))
        touch = [o for o in snap if o["alive"] and o["net"] == net and (
            (o["via"] and math.hypot(o["a"][0] - far[0], o["a"][1] - far[1]) < 0.2)
            or (not o["via"] and o["layer"] == lid and min(math.hypot(o["a"][0] - far[0], o["a"][1] - far[1]), math.hypot(o["b"][0] - far[0], o["b"][1] - far[1])) < EPS))]
        onpad = any(p.GetNetname() == net and p.IsOnLayer(lid) and p.HitTest(pcbnew.VECTOR2I(mm(far[0]), mm(far[1])), mm(0.02)) for p in pads)
        ntrk = [o for o in touch if not o["via"]]
        if onpad or any(o["via"] for o in touch) or len(ntrk) != 1:
            print("junction at", far)
            break
        cur = far
for r in snap:
    if not r["alive"]:
        b.Remove(r["obj"])
pcbnew.SaveBoard(dst, b)
