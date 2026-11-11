"""chamfer90.py IN OUT REF [REF ...] [--c=0.25] (KiCad python): cut the 90-degree corners (two pieces of one net meeting at exactly 90 degrees, nothing else at the corner) of the traces that start on the pads of the given parts
by a chamfer of c mm (default 0.25; both pieces must be at least c + 0.2 long).  Pieces are shortened in place and one 45-degree piece is added per corner; foreign copper closer than 0.21 mm to the new piece blocks the corner."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); NM = 1e6; mm = pcbnew.ToMM; FM = pcbnew.FromMM; nets = b.GetNetsByName()
refs = [a for a in sys.argv[3:] if not a.startswith("--")]; c = float([a.split("=")[1] for a in sys.argv[3:] if a.startswith("--c=")][0]) if any(a.startswith("--c=") for a in sys.argv[3:]) else 0.25
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]; ends = collections.Counter()
for t in tracks: ends[(t.GetLayer(), t.GetStart().x, t.GetStart().y)] += 1; ends[(t.GetLayer(), t.GetEnd().x, t.GetEnd().y)] += 1
special = {(t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"} | {(p.GetPosition().x, p.GetPosition().y) for f in b.GetFootprints() for p in f.Pads()}
arcends = {(t.GetLayer(), t.GetStart().x, t.GetStart().y) for t in b.GetTracks() if t.GetClass() == "PCB_ARC"} | {(t.GetLayer(), t.GetEnd().x, t.GetEnd().y) for t in b.GetTracks() if t.GetClass() == "PCB_ARC"}
def seg_d(p, a, q):
    dx, dy = q[0] - a[0], q[1] - a[1]; L2 = dx * dx + dy * dy; t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def seg_seg(a, q, e, g): return min(seg_d(a, e, g), seg_d(q, e, g), seg_d(e, a, q), seg_d(g, a, q))
xy = lambda v: (v.x / NM, v.y / NM)
chain = {}
for r in refs:
    f = b.FindFootprintByReference(r)
    for p in f.Pads():
        net = p.GetNetname(); frontier = [(p.GetPosition().x, p.GetPosition().y)]; seen = set()
        while frontier:
            k = frontier.pop()
            if k in seen: continue
            seen.add(k)
            if k != (p.GetPosition().x, p.GetPosition().y) and k in special: continue
            for t in tracks:
                if t.GetNetname() == net and ((t.GetStart().x, t.GetStart().y) == k or (t.GetEnd().x, t.GetEnd().y) == k):
                    chain[t.m_Uuid.AsString()] = t; frontier += [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
done = 0; skipped = []; newp = []
byvert = collections.defaultdict(list)
for t in chain.values():
    byvert[(t.GetLayer(), t.GetStart().x, t.GetStart().y)].append(t); byvert[(t.GetLayer(), t.GetEnd().x, t.GetEnd().y)].append(t)
used = set()
for (lay, x, y), lst in byvert.items():
    if len(lst) != 2 or ends[(lay, x, y)] != 2 or (x, y) in special or (lay, x, y) in arcends: continue
    t1, t2 = lst
    if t1.m_Uuid.AsString() in used or t2.m_Uuid.AsString() in used: continue
    def far(t): return t.GetEnd() if (t.GetStart().x, t.GetStart().y) == (x, y) else t.GetStart()
    a, q = far(t1), far(t2); v1 = (a.x - x, a.y - y); v2 = (q.x - x, q.y - y); n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if abs(v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) > 0.01 or min(n1, n2) / NM < c + 0.2: continue
    pa = (x / NM + v1[0] / n1 * c, y / NM + v1[1] / n1 * c); pq = (x / NM + v2[0] / n2 * c, y / NM + v2[1] / n2 * c); net = t1.GetNetname()
    ok = all(t.GetNetname() == net or seg_seg(pa, pq, xy(t.GetStart()), xy(t.GetEnd())) >= 0.21 for t in tracks if t.GetLayer() == lay) and all(w.GetNetname() == net or seg_d(xy(w.GetPosition()), pa, pq) >= 0.335 for w in b.GetTracks() if w.GetClass() == "PCB_VIA")
    if not ok: skipped.append((round(x / NM, 2), round(y / NM, 2))); continue
    pa_v = pcbnew.VECTOR2I(int(round(pa[0] * NM)), int(round(pa[1] * NM))); pq_v = pcbnew.VECTOR2I(int(round(pq[0] * NM)), int(round(pq[1] * NM)))
    for t, nv in ((t1, pa_v), (t2, pq_v)):
        if (t.GetStart().x, t.GetStart().y) == (x, y): t.SetStart(nv)
        else: t.SetEnd(nv)
    newp.append((net, lay, pa_v, pq_v, t1.GetWidth())); used |= {t1.m_Uuid.AsString(), t2.m_Uuid.AsString()}; done += 1
for net, lay, p1, p2, w in newp:
    t = pcbnew.PCB_TRACK(b); t.SetStart(p1); t.SetEnd(p2); t.SetWidth(w); t.SetLayer(lay); t.SetNet(nets[net]); b.Add(t)
print("90-degree corners chamfered:", done, " blocked by neighbours:", skipped); pcbnew.SaveBoard(sys.argv[2], b)
