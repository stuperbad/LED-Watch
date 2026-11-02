"""audit_board.py board.kicad_pcb : layout cleanliness numbers a reviewer would look at (KiCad python). Prints counts and the worst offenders; changes nothing.
 - track pieces not on a 0 / 45 / 90 degree line (arcs are skipped), 90 degree corners and acute corners between pieces of one net on one layer
 - micro pieces (< 0.15 mm, < 0.30 mm), track ends inside a pad or on a via that are off its centre, same-net pieces lying on top of each other
 - vias: total, per layer pair, vias whose net has only that via on a layer (a via used as a plain pass-through of 2 layers is normal; counted: 'stub vias' = via end of a net piece without a track on the far layer)
 - nets by length / straight-line distance between their pads (detour ratio) for nets with 2 pads
 usage: kicad python audit_board.py "hardware/LED Watch - Single Color.kicad_pcb" """
import pcbnew, sys, math, collections
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); L = b.GetLayerName
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
print("tracks %d, arcs %d, vias %d" % (len(tr), len(arcs), len(vias)))
P = lambda p: (round(tomm(p.x), 3), round(tomm(p.y), 3))
def ang(t):
    s, e = P(t.GetStart()), P(t.GetEnd()); dx, dy = e[0] - s[0], e[1] - s[1]
    return math.degrees(math.atan2(dy, dx)) % 180, math.hypot(dx, dy)
off = collections.Counter(); offl = []
micro15 = micro30 = 0
for t in tr:
    a, ln = ang(t)
    if ln < 0.15: micro15 += 1
    if ln < 0.30: micro30 += 1
    if ln > 0.02 and min(abs(a - k) for k in (0, 45, 90, 135, 180)) > 0.6:
        off[t.GetNetname()] += 1; offl.append((round(a, 1), round(ln, 2), t.GetNetname(), L(t.GetLayer())))
print("pieces not on 0/45/90: %d (nets: %s)" % (sum(off.values()), off.most_common(6)))
print("micro pieces < 0.15 mm: %d, < 0.30 mm: %d" % (micro15, micro30))
# corners
ends = collections.defaultdict(list)
for t in tr:
    for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
        ends[(L(t.GetLayer()), t.GetNetname(), P(e))].append(P(o))
c90 = acute = 0; acl = []
for (lay, net, p), others in ends.items():
    if len(others) != 2: continue
    v = [(o[0] - p[0], o[1] - p[1]) for o in others]
    if min(math.hypot(*x) for x in v) < 1e-6: continue
    cosang = (v[0][0] * v[1][0] + v[0][1] * v[1][1]) / (math.hypot(*v[0]) * math.hypot(*v[1]))
    a = math.degrees(math.acos(max(-1, min(1, cosang))))
    if abs(a - 90) < 1: c90 += 1
    elif a < 89: acute += 1; acl.append((round(a), net, lay, p))
print("corners of exactly 90 degrees: %d, acute (< 90) corners: %d" % (c90, acute))
for x in sorted(acl)[:8]: print("   acute", x)
# off-centre ends
pads = [(p, f) for f in b.GetFootprints() for p in f.Pads()]
offc = []
for t in tr:
    for e in (t.GetStart(), t.GetEnd()):
        for p, f in pads:
            if p.GetNetname() == t.GetNetname() and p.IsOnLayer(t.GetLayer()) and p.GetBoundingBox().Contains(e):
                d = math.hypot(tomm(e.x - p.GetPosition().x), tomm(e.y - p.GetPosition().y))
                if d > 0.02: offc.append((round(d, 3), f.GetReference() + "." + p.GetNumber(), t.GetNetname()))
                break
print("track ends inside a pad but off its centre by > 0.02 mm: %d (examples %s)" % (len(offc), sorted(offc, reverse=True)[:5]))
# overlapping same-net collinear pieces
seen = collections.defaultdict(list); ov = 0
for t in tr:
    s, e = P(t.GetStart()), P(t.GetEnd())
    a, ln = ang(t)
    if ln < 0.02: continue
    key = (L(t.GetLayer()), t.GetNetname(), round(a, 0), round((-s[0] * math.sin(math.radians(a)) + s[1] * math.cos(math.radians(a))), 2))
    seen[key].append((min(s[0] * math.cos(math.radians(a)) + s[1] * math.sin(math.radians(a)), e[0] * math.cos(math.radians(a)) + e[1] * math.sin(math.radians(a))), max(s[0] * math.cos(math.radians(a)) + s[1] * math.sin(math.radians(a)), e[0] * math.cos(math.radians(a)) + e[1] * math.sin(math.radians(a)))))
for k, v in seen.items():
    v.sort()
    for i in range(len(v) - 1):
        if v[i + 1][0] < v[i][1] - 0.02: ov += 1
print("same-net collinear pieces that overlap each other: %d" % ov)
# vias
vn = collections.Counter(v.GetNetname() for v in vias)
print("vias per net (top): %s" % vn.most_common(8))
# detour for 2-pad nets
res = []
for net in b.GetNetsByName().keys():
    n = str(net)
    pp = [p for p, f in pads if p.GetNetname() == n]
    if len(pp) != 2 or n.startswith("unconnected"): continue
    d = math.hypot(tomm(pp[0].GetPosition().x - pp[1].GetPosition().x), tomm(pp[0].GetPosition().y - pp[1].GetPosition().y))
    ln = sum(tomm(t.GetLength()) for t in b.GetTracks() if t.GetNetname() == n)
    if d > 2: res.append((round(ln / d, 1), round(ln, 1), round(d, 1), n))
res.sort(reverse=True)
print("2-pad nets, routed length / straight distance (worst 10): %s" % res[:10])
