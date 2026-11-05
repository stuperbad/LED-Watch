import sys, math, heapq, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
def padxy(ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == str(num): return (p.GetPosition().x, p.GetPosition().y), p.GetNetname()
adj = collections.defaultdict(list)
# nodes: (net, x, y) ; same position different layer joined by zero-cost edge (vias / pads); pieces cost their length
pieces = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA": continue
    s, e = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y); n = t.GetNetname(); L = mm(t.GetLength()); lay = t.GetLayer()
    adj[(n, lay, s)].append(((n, lay, e), L)); adj[(n, lay, e)].append(((n, lay, s), L))
byxy = collections.defaultdict(set)
for k in list(adj): byxy[(k[0], k[2])].add(k)
vias = [(t.GetNetname(), (t.GetPosition().x, t.GetPosition().y)) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
def near_nodes(net, xy, r):
    out = []
    for k in adj:
        if k[0] == net and (k[2][0] - xy[0]) ** 2 + (k[2][1] - xy[1]) ** 2 <= r * r: out.append(k)
    return out
# link every node to the other layers' nodes inside the same via circle (r 0.17 mm) and at pad centres
R = 170000
for n, xy in vias:
    ns = near_nodes(n, xy, R)
    for a in ns:
        for c in ns:
            if a != c: adj[a].append((c, 0.0))
def walk(r1, p1, r2, p2):
    (a, n1), (c, n2) = padxy(r1, p1), padxy(r2, p2)
    if n1 != n2: return None
    # sources: nodes at the pad centre (any layer)
    S = [k for k in adj if k[0] == n1 and (k[2][0]-a[0])**2+(k[2][1]-a[1])**2 <= 300000**2]; T = {k for k in adj if k[0] == n1 and (k[2][0]-c[0])**2+(k[2][1]-c[1])**2 <= 300000**2}
    dist = {k: 0.0 for k in S}; pq = [(0.0, i, k) for i, k in enumerate(S)]; cnt = len(S)
    while pq:
        d, _, k = heapq.heappop(pq)
        if k in T: return d
        if d > dist.get(k, 1e9): continue
        for k2, w in adj[k]:
            nd = d + w
            if nd < dist.get(k2, 1e9): dist[k2] = nd; cnt += 1; heapq.heappush(pq, (nd, cnt, k2))
    return None
def straight(r1, p1, r2, p2):
    (a, _), (c, _) = padxy(r1, p1), padxy(r2, p2); return math.hypot(mm(a[0] - c[0]), mm(a[1] - c[1]))
pairs = [("OK_HYST divider R53", ("R53", 1, "U4", 10)), ("OK_PROG divider R54", ("R54", 1, "U4", 11)), ("C52 4.7 uF (CSTOR)", ("C52", 1, "U4", 19)), ("C53 10 nF (CBYP)", ("C53", 1, "U4", 19)), ("C50 4.7 uF (CIN)", ("C50", 1, "U4", 2)), ("C54 22 uF (COUT)", ("C54", 1, "U4", 14)),
         ("L1 LBOOST end", ("L1", 1, "U4", 20)), ("L1 VIN_DC end", ("L1", 2, "U4", 2)), ("L2 LBUCK end", ("L2", 1, "U4", 16)), ("L2 VOUT end", ("L2", 2, "U4", 14)), ("C51 10 nF (CREF)", ("C51", 1, "U4", 4)),
         ("R50 / R51 VBAT_OV", ("R51", 1, "U4", 7)), ("R52 OK_HYST", ("R52", 2, "U4", 10)), ("R54 OK_PROG", ("R54", 1, "U4", 11)), ("R56 VOUT_SET", ("R56", 1, "U4", 12))]
for name, (a, pa, c, pc) in pairs:
    w = walk(a, pa, c, pc); print("%-22s straight %.1f mm   copper %s" % (name, straight(a, pa, c, pc), ("%.1f mm" % w) if w is not None else "not found"))
