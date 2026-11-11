import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); NM = 1e6; nets = b.GetNetsByName()
f = b.FindFootprintByReference("R10"); P = [p for p in f.Pads() if p.GetNumber() == "1"][0].GetPosition()
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "/COL9" and t.GetLayerName() == "F.Cu"]
near = lambda p, x, y: abs(p.x / NM - x) < .006 and abs(p.y / NM - y) < .006
t0 = [t for t in tr if (t.GetStart().x, t.GetStart().y) == (P.x, P.y) or (t.GetEnd().x, t.GetEnd().y) == (P.x, P.y)][0]
t1 = [t for t in tr if t is not t0 and (near(t.GetStart(), 84.881, 101.405) or near(t.GetEnd(), 84.881, 101.405))][0]
B = t1.GetEnd() if near(t1.GetStart(), 84.881, 101.405) else t1.GetStart()
A = pcbnew.VECTOR2I(int(round((B.x / NM + (B.y / NM - 0) * 0) * NM)), 0)
dy = (P.y - B.y) / NM; Ax = B.x / NM + abs(dy); A = pcbnew.VECTOR2I(int(round(Ax * NM)), P.y)       # horizontal out of the pad, then exactly 45 degrees to the old far end
if (t0.GetStart().x, t0.GetStart().y) == (P.x, P.y): t0.SetEnd(A)
else: t0.SetStart(A)
if near(t1.GetStart(), 84.881, 101.405): t1.SetStart(A)
else: t1.SetEnd(A)
print("R10 pad 1: first piece now horizontal %.3f mm, then 45 degrees" % ((P.x - A.x) / NM)); pcbnew.SaveBoard(sys.argv[2], b)
