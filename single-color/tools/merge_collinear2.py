"""merge_collinear2.py IN OUT x0,y0,x1,y1 (KiCad python): inside a window, delete zero-length track pieces and join straight pieces of one net / layer / width that meet end to end on one line with nothing else at the joint
(no third piece, arc, pad or via).  The copper does not change, only the number of pieces (ring nets too: only straight pieces are touched, arcs never)."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); win = tuple(map(float, sys.argv[3].split(","))); NM = 1e6
inw = lambda p: win[0] <= p[0] / NM <= win[2] and win[1] <= p[1] / NM <= win[3]
vias = {(t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"}; pads = {(p.GetPosition().x, p.GetPosition().y) for f in b.GetFootprints() for p in f.Pads()}
arcends = set()
objs = []; P = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_ARC": arcends |= {(t.GetLayer(), (t.GetStart().x, t.GetStart().y)), (t.GetLayer(), (t.GetEnd().x, t.GetEnd().y))}
    elif t.GetClass() == "PCB_TRACK": objs.append(t); P[len(objs) - 1] = [t.GetLayer(), t.GetNetname(), t.GetWidth(), (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
removed = merged = 0
alive = set(P)
for i in list(alive):
    l, n, w, s, e = P[i]
    if inw(s) and inw(e) and math.hypot(s[0] - e[0], s[1] - e[1]) < 2000: alive.discard(i); removed += 1
changed = set()
while True:
    at = collections.defaultdict(list); cnt = collections.Counter()
    for i in alive:
        l, n, w, s, e = P[i]
        for p in (s, e): at[(l, n, p)].append(i); cnt[(l, p)] += 1
    done = False
    for (l, n, p), lst in at.items():
        if len(lst) != 2 or lst[0] == lst[1] or p in vias or p in pads or (l, p) in arcends or cnt[(l, p)] != 2 or any(abs(v[0] - p[0]) < 0.06 * NM and abs(v[1] - p[1]) < 0.06 * NM for v in vias): continue
        a, c = lst
        if P[a][2] != P[c][2] or not (inw(P[a][3]) or inw(P[a][4]) or inw(P[c][3]) or inw(P[c][4])): continue
        oa = P[a][4] if P[a][3] == p else P[a][3]; oc = P[c][4] if P[c][3] == p else P[c][3]
        v1 = (p[0] - oa[0], p[1] - oa[1]); v2 = (oc[0] - p[0], oc[1] - p[1]); n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 == 0 or n2 == 0: continue
        if abs(v1[0] * v2[1] - v1[1] * v2[0]) / (n1 * n2) < 1e-4 and (v1[0] * v2[0] + v1[1] * v2[1]) > 0:
            P[a][3], P[a][4] = oa, oc; changed.add(a); alive.discard(c); merged += 1; done = True; break
    if not done: break
for i in changed:
    if i in alive: objs[i].SetStart(pcbnew.VECTOR2I(*P[i][3])); objs[i].SetEnd(pcbnew.VECTOR2I(*P[i][4]))
for i in range(len(objs)):
    if i not in alive: b.Remove(objs[i])
print("zero-length pieces removed:", removed, " pieces merged:", merged)
pcbnew.SaveBoard(sys.argv[2], b)
