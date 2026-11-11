"""led_s_flip.py IN.kicad_pcb OUT.kicad_pcb [--dry] (KiCad python): rotate the 60 seconds LEDs (S ring, 0201, r 19.57) by 180 degrees and redraw their front copper (the reviewer's idea, 2026-11-09):
  * after the turn pad 1 (ROW) is the OUTER pad and pad 2 (COL) the inner one;
  * the COL pad joins the COL arc of the minute ring (r 18.5, same net, same angle) with a short radial piece that ends on the arc's joint;  the outer COL arcs (r 20.35), their radial trunks and the old pad stubs are removed;
  * the ROW pad is joined to its existing via (r on its In2 lane, 1.5 degrees clockwise of the LED) with a tangent leg and a 45-degree leg (radial piece if the via is further than the 45 degree leg reaches).
Old ROW stubs (the hooks) are removed by walking the same-net F.Cu pieces from the old pad centre to the via."""
import sys, math, collections, pcbnew
dry = "--dry" in sys.argv
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; FM = pcbnew.FromMM
O = (100.0, 100.0); F = pcbnew.F_Cu
def pol(p): return (math.hypot(p[0] - O[0], p[1] - O[1]), math.degrees(math.atan2(p[1] - O[1], p[0] - O[0])))
def xy(v): return (v.x / NM, v.y / NM)
nets = b.GetNetsByName()
leds = [f for f in b.GetFootprints() if f.GetLayer() == F and f.GetValue() == "LED white 0201" and abs(pol(xy(f.GetPosition()))[0] - 19.57) < 0.1]
print("seconds LEDs:", len(leds))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F]
arcs = [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC" and t.GetLayer() == F]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
key = lambda p: (p.x, p.y)
uid = lambda t: t.m_Uuid.AsString()
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM)))
kill = {}; new_tracks = []; new_rot = []
inner_arcs = []
for a in arcs:
    r = math.hypot(xy(a.GetStart())[0] - O[0], xy(a.GetStart())[1] - O[1])
    if 18.4 < r < 18.6 and a.GetNetname().startswith("/COL"): inner_arcs.append(a)
def joint(net, theta):
    best = None
    for a in inner_arcs:
        if a.GetNetname() != net: continue
        for p in (a.GetStart(), a.GetEnd()):
            r, th = pol(xy(p)); dth = (th - theta + 180) % 360 - 180
            if abs(dth) < 0.03 and (best is None or abs(dth) < best[0]): best = (abs(dth), p)
    if best is None:                                  # no arc joint at this angle: a vertex of the minute ring's own stub chain (same net, r 18.3 - 18.6)
        for t in tracks:
            if t.GetNetname() != net or uid(t) in kill: continue
            for p in (t.GetStart(), t.GetEnd()):
                r, th = pol(xy(p)); dth = (th - theta + 180) % 360 - 180
                if 18.3 < r < 18.6 and abs(dth) < 0.4 and (best is None or abs(dth) < best[0]): best = (abs(dth), p)
    return best[1] if best else None
def split_arc(net, theta):
    for a in inner_arcs:
        if a.GetNetname() != net or uid(a) in kill: continue
        sa, ea = pol(xy(a.GetStart()))[1], pol(xy(a.GetEnd()))[1]
        if abs(sa - ea) < 180 and min(sa, ea) < theta < max(sa, ea):
            r = math.hypot(xy(a.GetStart())[0] - O[0], xy(a.GetStart())[1] - O[1]); w = a.GetWidth(); st, en = a.GetStart(), a.GetEnd()
            Pn = V(O[0] + r * math.cos(math.radians(theta)), O[1] + r * math.sin(math.radians(theta)))
            m1 = V(O[0] + r * math.cos(math.radians((sa + theta) / 2)), O[1] + r * math.sin(math.radians((sa + theta) / 2))); m2 = V(O[0] + r * math.cos(math.radians((theta + ea) / 2)), O[1] + r * math.sin(math.radians((theta + ea) / 2)))
            for q in ((st, m1, Pn), (Pn, m2, en)):
                n = pcbnew.PCB_ARC(b); n.SetStart(q[0]); n.SetMid(q[1]); n.SetEnd(q[2]); n.SetWidth(w); n.SetLayer(F); n.SetNet(nets[net]); b.Add(n); inner_arcs.append(n)
            b.Remove(a); inner_arcs.remove(a); return Pn
    return None
missing = []
for f in leds:
    pads = {p.GetNumber(): p for p in f.Pads() if p.GetNumber()}
    p1, p2 = pads["1"], pads["2"]; c1, c2 = p1.GetPosition(), p2.GetPosition(); rowNet, colNet = p1.GetNetname(), p2.GetNetname()
    theta = pol(xy(f.GetPosition()))[1]
    # old ROW stub chain: walk the same-net pieces from the old pad 1 centre until a via
    chain = []; frontier = [key(c1)]; seen = set()
    while frontier:
        k = frontier.pop()
        if k in seen: continue
        seen.add(k)
        for t in tracks:
            if t.GetNetname() == rowNet and uid(t) not in {uid(c) for c in chain} and (key(t.GetStart()) == k or key(t.GetEnd()) == k):
                chain.append(t); frontier += [key(t.GetStart()), key(t.GetEnd())]
    via = None
    for v in vias:
        if v.GetNetname() == rowNet:
            r, th = pol(xy(v.GetPosition())); dth = (th - theta + 180) % 360 - 180
            if 0.3 < abs(dth) < 3.0 and 18.7 < r < 20.5 and (via is None or abs(abs(dth) - 1.48) < abs(abs((pol(xy(via.GetPosition()))[1] - theta + 180) % 360 - 180) - 1.48)): via = v
    if via is None or not chain: missing.append(f.GetReference()); continue
    kill.update({uid(t): t for t in chain})
    # old COL stub at the outer pad
    for t in tracks:
        if t.GetNetname() == colNet and (key(t.GetStart()) == key(c2) or key(t.GetEnd()) == key(c2)): kill[uid(t)] = t
    new_rot.append((f, theta, p1, p2, via, colNet, rowNet))
print("LEDs with a complete old stub:", len(new_rot), "missing:", missing)
# the outer COL copper: arcs at r 20.3-20.4 and every non-arc COL piece reaching r >= 20.15
for a in arcs:
    r = math.hypot(xy(a.GetStart())[0] - O[0], xy(a.GetStart())[1] - O[1])
    if 20.3 < r < 20.4 and a.GetNetname().startswith("/COL"): kill[uid(a)] = a
for t in tracks:
    if t.GetNetname().startswith("/COL") and max(pol(xy(t.GetStart()))[0], pol(xy(t.GetEnd()))[0]) >= 20.15 and min(pol(xy(t.GetStart()))[0], pol(xy(t.GetEnd()))[0]) > 18.3: kill[uid(t)] = t
old_len = sum(mm(t.GetLength()) for t in kill.values() if t.GetClass() == "PCB_TRACK") + sum(mm(t.GetLength()) for t in kill.values() if t.GetClass() == "PCB_ARC")
print("pieces to remove:", len(kill), "length %.1f mm" % old_len)
add = []; newlen = 0.0; nojoint = []
for f, theta, p1, p2, via, colNet, rowNet in new_rot:
    f.SetOrientationDegrees(f.GetOrientationDegrees() + 180)
    P = p1.GetPosition(); Q = p2.GetPosition()                      # after the turn: pad 1 outer, pad 2 inner
    J = joint(colNet, theta)
    if J is None:
        J = split_arc(colNet, theta)
        if J is None: nojoint.append((f.GetReference(), colNet)); continue
    add.append((colNet, Q, J)); newlen += math.hypot(xy(Q)[0] - xy(J)[0], xy(Q)[1] - xy(J)[1])
    th = math.radians(theta); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    Pp, Vp = xy(P), xy(via.GetPosition()); d = (Vp[0] - Pp[0], Vp[1] - Pp[1]); du = d[0] * u[0] + d[1] * u[1]; dv = d[0] * v[0] + d[1] * v[1]
    su = 1 if du >= 0 else -1; du = abs(du); u = (u[0] * su, u[1] * su); a = abs(dv); s = 1 if dv >= 0 else -1
    if a <= du:
        pts = [Pp, (Pp[0] + u[0] * (du - a), Pp[1] + u[1] * (du - a)), Vp] if du - a > 0.02 else [Pp, Vp]
    else:
        pts = [Pp, (Pp[0] + u[0] * du + s * v[0] * du, Pp[1] + u[1] * du + s * v[1] * du), Vp]
    chainpts = [P] + [V(*q) for q in pts[1:-1]] + [via.GetPosition()]
    for q0, q1 in zip(chainpts, chainpts[1:]): add.append((rowNet, q0, q1)); newlen += math.hypot(xy(q0)[0] - xy(q1)[0], xy(q0)[1] - xy(q1)[1])
print("new pieces:", len(add), "length %.1f mm" % newlen, "no COL joint:", nojoint)
if dry: sys.exit()
for t in kill.values(): b.Remove(t)
for net, q0, q1 in add:
    t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets[net]); b.Add(t)
pcbnew.SaveBoard(sys.argv[2], b); print("written")
