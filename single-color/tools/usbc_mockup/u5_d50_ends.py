"""u5_d50_ends.py in.kicad_pcb out.kicad_pcb : after the U5 / D50 land patterns changed: (1) drop the dead TS stub that ran into U5 pad 3 (~CHG, unused) from (106.45, 105.9) via (106.45, 105.55), (106.55, 105.45) to (107.362, 105.45);
(2) track ends that lie inside a U5 / D50 pad but not on its centre (overshoot or the pad moved) are put on the pad centre, unless the end is a bend shared with another piece. KiCad python."""
import pcbnew, sys, math
mm = pcbnew.FromMM; tomm = pcbnew.ToMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
key = lambda p: (round(tomm(p.x), 3), round(tomm(p.y), 3))
stub = {((106.45, 105.9), (106.45, 105.55)), ((106.45, 105.55), (106.55, 105.45)), ((106.55, 105.45), (107.362, 105.45))}
gone = 0; grave = []   # keep removed items alive: KiCad's python crashes on a board whose removed tracks were freed
for t in list(b.GetTracks()):
    if t.GetClass() != "PCB_VIA" and t.GetNetname() == "/TS" and (key(t.GetStart()), key(t.GetEnd())) in stub | {(e, s) for s, e in stub}:
        b.Remove(t); grave.append(t); gone += 1
print("TS stub pieces removed", gone, "(expect 3)")
for ref in ("U5", "D50"):
    for p in b.FindFootprintByReference(ref).Pads():
        if not p.GetNetname():
            continue
        c = p.GetPosition(); bb = p.GetBoundingBox()
        ends = [(t, w, q) for t in b.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetNetname() == p.GetNetname() and p.IsOnLayer(t.GetLayer())
                for w, q in (("s", t.GetStart()), ("e", t.GetEnd())) if bb.Contains(q)]
        for t, w, q in ends:
            off = math.hypot(tomm(q.x - c.x), tomm(q.y - c.y))
            same = [1 for t2 in b.GetTracks() if t2.m_Uuid.AsString() != t.m_Uuid.AsString() and t2.GetNetname() == p.GetNetname() and (key(t2.GetStart()) == key(q) or key(t2.GetEnd()) == key(q))]
            if 0.001 < off < 0.2 and not same:
                (t.SetStart if w == "s" else t.SetEnd)(V(c.x, c.y)); print(ref, p.GetNumber(), p.GetNetname(), "end moved", round(off, 3), "mm onto the pad centre")
pcbnew.SaveBoard(sys.argv[2], b)
