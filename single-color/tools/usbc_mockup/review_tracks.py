"""review.py OWNER.pcb BASE.pcb : quality review of the tracks the owner added (vs BASE): pad exits, ends on centres, angles, short pieces, corners, dead ends, vias, detours"""
import pcbnew, sys, math, collections
o = pcbnew.LoadBoard(sys.argv[1]); base = pcbnew.LoadBoard(sys.argv[2]); mm = pcbnew.ToMM
def sig(b, t):
    if t.GetClass() == "PCB_VIA": p = t.GetPosition(); return ("via", t.GetNetname(), round(mm(p.x), 3), round(mm(p.y), 3))
    s, e = t.GetStart(), t.GetEnd(); return (t.GetLayerName(), t.GetNetname(), tuple(sorted([(round(mm(s.x), 3), round(mm(s.y), 3)), (round(mm(e.x), 3), round(mm(e.y), 3))])))
bs = {sig(base, t) for t in base.GetTracks() if t.GetClass() != "PCB_ARC"}
new = [t for t in o.GetTracks() if t.GetClass() != "PCB_ARC" and sig(o, t) not in bs]
newsegs = [t for t in new if t.GetClass() != "PCB_VIA"]; newvias = [t for t in new if t.GetClass() == "PCB_VIA"]
P = lambda p: (mm(p.x), mm(p.y))
def L(t): a, b = P(t.GetStart()), P(t.GetEnd()); return math.hypot(a[0]-b[0], a[1]-b[1])
print("owner added: %d pieces (%.1f mm total), %d vias; removed vs base: see cmp" % (len(newsegs), sum(L(t) for t in newsegs), len(newvias)))
print("added pieces by layer:", dict(collections.Counter(t.GetLayerName() for t in newsegs)))
# angles
bad = []
for t in newsegs:
    a, b = P(t.GetStart()), P(t.GetEnd())
    if L(t) < 1e-6: continue
    ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) % 45
    if min(ang, 45-ang) > 0.1: bad.append((t.GetNetname(), (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)), round(min(ang, 45-ang), 2)))
print("pieces not at 0/45/90 deg:", len(bad)); [print("   ", x) for x in bad[:12]]
short = [(t.GetNetname(), tuple(round(v, 3) for v in P(t.GetStart())), tuple(round(v, 3) for v in P(t.GetEnd())), round(L(t), 3)) for t in newsegs if L(t) < 0.15]
print("pieces shorter than 0.15 mm:", len(short)); [print("   ", x) for x in short[:15]]
# pad exits and ends on centres
parts2 = [f for f in o.GetFootprints() if f.GetLayer() == pcbnew.B_Cu and len(list(f.Pads())) == 2 and f.GetReference()[0] in "RCDL" and 103 < mm(f.GetPosition().x) < 113.5 and 89 < mm(f.GetPosition().y) < 110]
allsegs = [t for t in o.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetClass() != "PCB_ARC"]
print("\nPAD EXITS of the 2-pad parts in the corner (first piece direction vs the part axis; OK if within 20 deg of 'straight out of the pad end'):")
for f in sorted(parts2, key=lambda f: f.GetReference()):
    pads = list(f.Pads()); c = P(f.GetPosition())
    for p in pads:
        pc = P(p.GetPosition()); ax = (pc[0]-c[0], pc[1]-c[1]); n = math.hypot(*ax); ax = (ax[0]/n, ax[1]/n)
        pcs = [t for t in allsegs if t.GetLayerName() == "B.Cu" and t.GetNetname() == p.GetNetname() and any(math.hypot(P(e)[0]-pc[0], P(e)[1]-pc[1]) < 0.15 for e in (t.GetStart(), t.GetEnd()))]
        if not pcs:
            vias = [v for v in o.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == p.GetNetname() and math.hypot(P(v.GetPosition())[0]-pc[0], P(v.GetPosition())[1]-pc[1]) < 1.0]
            print("   %-4s.%s %-9s no B.Cu piece at the pad%s" % (f.GetReference(), p.GetNumber(), p.GetNetname().lstrip("/"), " (via near)" if vias else "")); continue
        out = []
        for t in pcs:
            s, e = P(t.GetStart()), P(t.GetEnd()); near, far = (s, e) if math.hypot(s[0]-pc[0], s[1]-pc[1]) <= math.hypot(e[0]-pc[0], e[1]-pc[1]) else (e, s)
            d = (far[0]-near[0], far[1]-near[1]); dn = math.hypot(*d)
            ang = math.degrees(math.acos(max(-1, min(1, (d[0]*ax[0]+d[1]*ax[1])/dn)))) if dn > 1e-6 else 0
            off = math.hypot(near[0]-pc[0], near[1]-pc[1])
            out.append((round(ang), round(dn, 2), round(off, 3)))
        flag = "OK " if all(a <= 20 for a, _, _ in out) else "SIDE/ANGLED"
        print("   %-4s.%s %-9s %s pieces (angle from axis deg, length mm, centre offset mm): %s" % (f.GetReference(), p.GetNumber(), p.GetNetname().lstrip("/"), flag, out))
# dead ends among new pieces + vias count
def node_users(xy, net, layer):
    n = 0
    for t in allsegs:
        if t.GetNetname() == net and t.GetLayerName() == layer:
            for e in (t.GetStart(), t.GetEnd()):
                if math.hypot(P(e)[0]-xy[0], P(e)[1]-xy[1]) < 0.012: n += 1
    return n
covers = lambda xy, net: any(math.hypot(P(p.GetPosition())[0]-xy[0], P(p.GetPosition())[1]-xy[1]) < 0.012 for f in o.GetFootprints() for p in f.Pads() if p.GetNetname() == net) or any(math.hypot(P(v.GetPosition())[0]-xy[0], P(v.GetPosition())[1]-xy[1]) < 0.012 for v in o.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == net)
dead = []
for t in newsegs:
    for e in (t.GetStart(), t.GetEnd()):
        xy = P(e)
        if node_users(xy, t.GetNetname(), t.GetLayerName()) == 1 and not covers(xy, t.GetNetname()): dead.append((t.GetNetname(), t.GetLayerName(), tuple(round(v, 3) for v in xy)))
print("\nnew-piece ends touching nothing (dead ends / ends off a pad centre):", len(dead)); [print("   ", x) for x in dead[:15]]
print("vias on the added list:", [(v.GetNetname(), tuple(round(x, 2) for x in P(v.GetPosition()))) for v in newvias])
