"""Move every straight-track end that touches a via or pad of its own net to that via's or pad's centre (the router accepts a landing anywhere in the copper).  Zero-length leftovers are deleted; a long track whose end would shift by more than 0.05 mm gets a short stub to the centre instead of being moved; refill the zone afterwards (fix_gnd_zone.py).
usage (KiCad python): snap_centers.py in.kicad_pcb out.kicad_pcb"""
import sys, math
import pcbnew
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
vias = [t for t in b.GetTracks() if t.GetClass()=="PCB_VIA"]
trks = [t for t in b.GetTracks() if t.GetClass()=="PCB_TRACK"]
moved = 0; zero = []
def target(t, q):
    best=None
    for v in vias:
        if v.GetNetname()!=t.GetNetname(): continue
        pp=v.GetPosition(); d=math.hypot(mm(q.x-pp.x), mm(q.y-pp.y))
        if d < mm(v.GetWidth(pcbnew.F_Cu))/2 + mm(t.GetWidth())/2 + 0.01 and (best is None or d<best[0]): best=(d,pp)
    if best: return best[1]
    for p in pads:
        if p.GetNetname()==t.GetNetname() and p.IsOnLayer(t.GetLayer()) and max(mm(p.GetSizeX()), mm(p.GetSizeY())) < 1.2 and p.HitTest(q, t.GetWidth() // 2):
            return p.GetPosition()
    return None
stubs = []
for t in trks:
    for which in ("s", "e"):
        q = t.GetStart() if which == "s" else t.GetEnd()
        tg = target(t, q)
        if tg is None:
            continue
        shift = math.hypot(mm(q.x - tg.x), mm(q.y - tg.y))
        if shift <= 0.002:
            continue
        if shift > 0.05 and mm(t.GetLength()) > 0.6:       # a long track keeps its direction: a short stub from its end to the centre instead
            stubs.append((q, tg, t.GetWidth(), t.GetLayer(), t.GetNet()))
        else:
            (t.SetStart if which == "s" else t.SetEnd)(tg)
            moved += 1
    if t.GetStart() == t.GetEnd():
        zero.append(t.m_Uuid.AsString())
for q, tg, w, layer, net in stubs:
    s = pcbnew.PCB_TRACK(b)
    s.SetStart(q)
    s.SetEnd(tg)
    s.SetWidth(w)
    s.SetLayer(layer)
    s.SetNet(net)
    b.Add(s)
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in zero: b.Remove(t)
print("ends moved", moved, "stubs added", len(stubs), "zero-length removed", len(zero))
pcbnew.SaveBoard(sys.argv[2], b)
