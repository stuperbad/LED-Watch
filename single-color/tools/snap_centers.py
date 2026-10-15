"""Move every straight-track end that touches a via or pad of its own net to that via's or pad's centre (the router accepts a landing anywhere in the copper).  Zero-length leftovers are deleted; refill the zone afterwards (fix_gnd_zone.py).
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
        if d < 0.17 and (best is None or d<best[0]): best=(d,pp)
    if best: return best[1]
    for p in pads:
        if p.GetNetname()==t.GetNetname() and p.IsOnLayer(t.GetLayer()) and p.HitTest(q,0):
            return p.GetPosition()
    return None
for t in trks:
    for which in ("s","e"):
        q = t.GetStart() if which=="s" else t.GetEnd()
        tg = target(t,q)
        if tg is None: continue
        if math.hypot(mm(q.x-tg.x), mm(q.y-tg.y)) > 0.002:
            (t.SetStart if which=="s" else t.SetEnd)(tg); moved+=1
    if t.GetStart()==t.GetEnd(): zero.append(t.m_Uuid.AsString())
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in zero: b.Remove(t)
print("ends moved", moved, "zero-length removed", len(zero))
pcbnew.SaveBoard(sys.argv[2], b)
