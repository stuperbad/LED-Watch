"""rework_copper.py BOARD x0 y0 x1 y1 : copper (tracks, arcs, vias) of every net inside a window, per layer (KiCad python)"""
import sys, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6]); mm = pcbnew.ToMM
ins = lambda p: x0 <= mm(p.x) <= x1 and y0 <= mm(p.y) <= y1
cnt = collections.defaultdict(lambda: [0, 0.0]); vias = collections.defaultdict(list)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        if ins(t.GetPosition()): vias[t.GetNetname()].append((round(mm(t.GetPosition().x), 2), round(mm(t.GetPosition().y), 2)))
    else:
        if ins(t.GetStart()) or ins(t.GetEnd()):
            k = (t.GetNetname(), b.GetLayerName(t.GetLayer())); cnt[k][0] += 1; cnt[k][1] += mm(t.GetLength())
for k in sorted(cnt): print("%-14s %-6s %3d pieces %6.1f mm" % (k[0], k[1], cnt[k][0], cnt[k][1]))
for n in sorted(vias): print("vias", n, vias[n])
