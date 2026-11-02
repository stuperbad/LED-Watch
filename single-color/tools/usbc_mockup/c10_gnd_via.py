"""c10_gnd_via.py in.kicad_pcb out.kicad_pcb : remove the extra GND via at (100.71, 87.23) (it sat 0.01 mm from ROW4 and 0.085 mm hole-to-copper, 6 DRC items) with the 3 pieces that led to it from C10 pin 2,
and tie C10.2 to the GND via at (101.5, 88.201) (pad 15 of U1) instead: pad centre (101.35, 87.65) -> 45 degrees to (101.5, 87.8) -> straight down to the via centre. KiCad python."""
import pcbnew, sys
mm = pcbnew.FromMM; tomm = pcbnew.ToMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
near = lambda p, x, y: abs(tomm(p.x) - x) < 0.01 and abs(tomm(p.y) - y) < 0.01
gone = 0; ref = None
for t in list(b.GetTracks()):
    if t.GetNetname() != "GND":
        continue
    if t.GetClass() == "PCB_VIA":
        if near(t.GetPosition(), 100.71, 87.23): b.Remove(t); gone += 1
        elif near(t.GetPosition(), 101.5, 88.201): ref = t
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = {(round(tomm(s.x), 3), round(tomm(s.y), 3)), (round(tomm(e.x), 3), round(tomm(e.y), 3))}
    if pts in ({(101.351, 87.646), (100.846, 87.646)}, {(100.846, 87.646), (100.71, 87.51)}, {(100.71, 87.51), (100.71, 87.23)}):
        proto = t; b.Remove(t); gone += 1
print("removed", gone, "(expect 4)")
assert gone == 4 and ref is not None
for a, c in (((101.35, 87.65), (101.5, 87.8)), ((101.5, 87.8), (101.5, 88.201))):
    n = pcbnew.PCB_TRACK(b); n.SetLayer(pcbnew.F_Cu); n.SetWidth(mm(0.1)); n.SetNet(ref.GetNet())
    n.SetStart(V(mm(a[0]), mm(a[1]))); n.SetEnd(V(mm(c[0]), mm(c[1]))); b.Add(n)
