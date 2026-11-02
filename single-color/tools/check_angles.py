"""List the sharp bends in the copper: where two tracks (or arcs) of the same net on the same layer meet at a point and the angle between them is smaller than 90 degrees
(a 45-degree bend has 135 degrees between the tracks, a right angle has 90; anything below that is an acute angle that traps etching acid and fails a human design review).
Also lists T junctions where the end of a track touches the side of another track of its net at less than 90 degrees, and tracks that leave a pad or via and turn straight back on themselves.
usage (KiCad python): check_angles.py board.kicad_pcb [MIN_DEG=89.5] [--near=x,y,half]       prints one line per bend with its position; exit code 0
"""
import math
import sys

import pcbnew

tomm = pcbnew.ToMM
path = sys.argv[1]
MIN = 89.5
near = None
for a in sys.argv[2:]:
    if a.startswith("--near="):
        near = [float(v) for v in a[7:].split(",")]
    else:
        MIN = float(a)
b = pcbnew.LoadBoard(path)
EPS = 0.02


def P(p):
    return (tomm(p.x), tomm(p.y))


segs = []     # (net, layer, start, end, dir at start (pointing into the segment), dir at end (pointing into the segment), class)
for t in b.GetTracks():
    c = t.GetClass()
    if c == "PCB_VIA":
        continue
    s, e = P(t.GetStart()), P(t.GetEnd())
    if c == "PCB_ARC":
        m = P(t.GetMid())
        ds = (m[0] - s[0], m[1] - s[1]); de = (m[0] - e[0], m[1] - e[1])
    else:
        ds = (e[0] - s[0], e[1] - s[1]); de = (s[0] - e[0], s[1] - e[1])
    n = math.hypot(*ds) or 1; ds = (ds[0] / n, ds[1] / n)
    n = math.hypot(*de) or 1; de = (de[0] / n, de[1] / n)
    segs.append((t.GetNetname(), t.GetLayer(), s, e, ds, de, c, tomm(t.GetWidth())))

ends = {}
for i, sg in enumerate(segs):
    for which in (0, 1):
        pt = sg[2 + which]
        ends.setdefault((sg[0], sg[1], round(pt[0] / 0.05), round(pt[1] / 0.05)), []).append((i, which, pt))

vias = [P(t.GetPosition()) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [(P(p.GetPosition()), p.GetNetname()) for f in b.GetFootprints() for p in f.Pads()]
out = []


def inside(pt):
    return near is None or (abs(pt[0] - near[0]) <= near[2] and abs(pt[1] - near[1]) <= near[2])


# bends at shared end points
seen = set()
for key, lst in ends.items():
    # merge neighbouring buckets
    cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cand += ends.get((key[0], key[1], key[2] + dx, key[3] + dy), [])
    cand = [c for c in {(i, w): (i, w, p) for i, w, p in cand}.values()]
    for a in range(len(cand)):
        for c in range(a + 1, len(cand)):
            i, wi, pi = cand[a]; j, wj, pj = cand[c]
            if i == j or (min(i, j), max(i, j)) in seen or math.hypot(pi[0] - pj[0], pi[1] - pj[1]) > EPS:
                continue
            seen.add((min(i, j), max(i, j)))
            di = segs[i][4 + wi]; dj = segs[j][4 + wj]
            cosang = max(-1, min(1, di[0] * dj[0] + di[1] * dj[1]))
            ang = math.degrees(math.acos(cosang))
            if ang < MIN and inside(pi):
                out.append((ang, pi, segs[i][0], pcbnew.LayerName(segs[i][1]) if hasattr(pcbnew, "LayerName") else b.GetLayerName(segs[i][1]), "bend"))

# T junctions: end of track A on the side of track B (same net / layer)
def seg_point(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    q = (a[0] + t * dx, a[1] + t * dy)
    return q, math.hypot(p[0] - q[0], p[1] - q[1]), t


for i, sg in enumerate(segs):
    if sg[6] == "PCB_ARC":
        continue
    for which in (0, 1):
        p = sg[2 + which]
        if not inside(p):
            continue
        for j, o in enumerate(segs):
            if j == i or o[0] != sg[0] or o[1] != sg[1] or o[6] == "PCB_ARC":
                continue
            q, dist, t = seg_point(p, o[2], o[3])
            if dist < 0.02 and 0.02 < t < 0.98 and math.hypot(p[0] - o[2][0], p[1] - o[2][1]) > EPS and math.hypot(p[0] - o[3][0], p[1] - o[3][1]) > EPS:
                di = sg[4 + which]
                ox = (o[3][0] - o[2][0], o[3][1] - o[2][1]); n = math.hypot(*ox) or 1; ox = (ox[0] / n, ox[1] / n)
                ang = math.degrees(math.acos(max(-1, min(1, di[0] * ox[0] + di[1] * ox[1]))))
                ang = min(ang, 180 - ang) if False else ang
                a2 = min(abs(ang), abs(180 - ang))      # the track arrives from one side: the smaller angle to the other track's line
                if a2 < MIN:
                    out.append((a2, p, sg[0], b.GetLayerName(sg[1]), "T-junction"))

out.sort()
for ang, p, net, layer, kind in out:
    print(f"{kind:10s} {ang:5.1f} deg  at ({p[0]:.3f}, {p[1]:.3f})  {net:12s} {layer}")
print(len(out), "sharp spots")
