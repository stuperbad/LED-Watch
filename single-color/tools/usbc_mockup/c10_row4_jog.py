"""c10_row4_jog.py in.kicad_pcb out.kicad_pcb : ROW4's F.Cu jog next to U1 pad 16 moved 0.05 mm east so it clears ROW5 by 0.125 mm (was 0.075): (101,88.25)->(100.55,87.8)->(100.55,86.787)->via (100.764,86.573). KiCad python."""
import pcbnew, sys
mm = pcbnew.FromMM; tomm = pcbnew.ToMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
want = {((101.0, 88.25), (100.5, 87.75)): ((101.0, 88.25), (100.55, 87.8)),
        ((100.5, 87.75), (100.5, 86.837)): ((100.55, 87.8), (100.55, 86.787)),
        ((100.5, 86.837), (100.764, 86.573)): ((100.55, 86.787), (100.764, 86.573))}
done = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" or t.GetNetname() != "/ROW4" or b.GetLayerName(t.GetLayer()) != "F.Cu":
        continue
    k = ((round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3)), (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3)))
    if k in want:
        (a, c) = want[k]
        t.SetStart(V(mm(a[0]), mm(a[1]))); t.SetEnd(V(mm(c[0]), mm(c[1]))); done += 1
print("ROW4 pieces moved", done, "(expect 3)")
assert done == 3
pcbnew.SaveBoard(sys.argv[2], b)
