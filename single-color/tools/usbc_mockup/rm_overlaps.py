"""rm_overlaps.py in.kicad_pcb out.kicad_pcb : delete track pieces that lie completely on top of a longer collinear piece of the same net and layer (redundant copper, found by tools/audit_board.py). KiCad python."""
import pcbnew, sys, math, collections
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); L = b.GetLayerName
P = lambda p: (round(tomm(p.x), 3), round(tomm(p.y), 3))
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
by = collections.defaultdict(list)
for t in tr: by[(L(t.GetLayer()), t.GetNetname())].append(t)
kill = []
for (lay, net), ts in by.items():
    for i in range(len(ts)):
        for j in range(len(ts)):
            if i == j: continue
            a, b_ = P(ts[i].GetStart()), P(ts[i].GetEnd()); c, d = P(ts[j].GetStart()), P(ts[j].GetEnd())
            va = (b_[0] - a[0], b_[1] - a[1]); la = math.hypot(*va)
            lc = math.hypot(d[0] - c[0], d[1] - c[1])
            if la < 0.01 or lc < 0.01 or lc >= la - 1e-6: continue          # j must be the shorter piece
            if abs((c[0] - a[0]) * va[1] - (c[1] - a[1]) * va[0]) / la > 0.01 or abs((d[0] - a[0]) * va[1] - (d[1] - a[1]) * va[0]) / la > 0.01: continue
            u = lambda p: ((p[0] - a[0]) * va[0] + (p[1] - a[1]) * va[1]) / la
            if min(u(c), u(d)) >= -0.01 and max(u(c), u(d)) <= la + 0.01 and ts[j] not in kill:
                kill.append(ts[j]); print("remove", lay, net, c, d, "(inside", a, b_, ")")
grave = []
for t in kill: b.Remove(t); grave.append(t)
print("removed", len(kill))
pcbnew.SaveBoard(sys.argv[2], b)
