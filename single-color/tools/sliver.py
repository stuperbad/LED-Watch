"""sliver.py IN OUT [--max 0.0005] : pieces shorter than --max mm (default 0.5 micrometre): the pieces that end at its far end are set exactly onto its near end (a displacement under --max), then it is removed."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; grave = []
mx = float(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 0.0005
done = 0
for t in list(b.GetTracks()):
    if t.GetClass() != "PCB_TRACK" or mm(t.GetLength()) >= mx: continue
    s, e = t.GetStart(), t.GetEnd(); L = t.GetLayer(); net = t.GetNetname()
    for o in b.GetTracks():
        if o is t or o.GetClass() == "PCB_VIA" or o.GetLayer() != L or o.GetNetname() != net: continue
        if (o.GetStart().x, o.GetStart().y) == (e.x, e.y): o.SetStart(pcbnew.VECTOR2I(s.x, s.y))
        if (o.GetEnd().x, o.GetEnd().y) == (e.x, e.y): o.SetEnd(pcbnew.VECTOR2I(s.x, s.y))
    print("removed %s %s %.4f mm at (%.4f, %.4f)" % (net, b.GetLayerName(L), mm(t.GetLength()), mm(s.x), mm(s.y))); b.Remove(t); grave.append(t); done += 1
print("slivers removed:", done); pcbnew.SaveBoard(sys.argv[2], b)
