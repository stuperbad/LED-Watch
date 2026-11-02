"""j1b_x.py in.kicad_pcb out.kicad_pcb : J1B 0.3 mm to the right (x 86.5 -> 86.8, J1's x); the two B.Cu tracks that start on its pads follow to the new pad centres ((84.5, 108.5) GND, (84.5, 109.5) BATT -> x 84.8);
the + and - marks go to the same place relative to the plug as at J1. (An exact mirror of J1 at y 107.9 is blocked by the ROW1 LED via of M40 at (85.19, 107.82).) KiCad python."""
import pcbnew, sys
mm = pcbnew.FromMM; tomm = pcbnew.ToMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
j = b.FindFootprintByReference("J1B"); p = j.GetPosition()
assert abs(tomm(p.x) - 86.5) < 0.001 and abs(tomm(p.y) - 109.0) < 0.001, (tomm(p.x), tomm(p.y))
n = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" or b.GetLayerName(t.GetLayer()) != "B.Cu":
        continue
    for w, q in (("s", t.GetStart()), ("e", t.GetEnd())):
        if abs(tomm(q.x) - 84.5) < 0.002 and abs(tomm(q.y) - 108.5) < 0.002 and t.GetNetname() == "GND" or abs(tomm(q.x) - 84.5) < 0.002 and abs(tomm(q.y) - 109.5) < 0.002 and t.GetNetname() == "/BATT":
            (t.SetStart if w == "s" else t.SetEnd)(V(mm(84.8), q.y)); n += 1
print("track ends moved", n, "(expect 2)")
j.SetPosition(V(mm(86.8), p.y))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and b.GetLayerName(d.GetLayer()) == "B.Silkscreen":
        x, y = tomm(d.GetPosition().x), tomm(d.GetPosition().y)
        if abs(x - 83.27) < 0.05 and abs(y - 107.54) < 0.05: d.SetPosition(V(mm(82.91), mm(107.53)))
        elif abs(x - 83.18) < 0.05 and abs(y - 110.2) < 0.05: d.SetPosition(V(mm(82.88), mm(110.0)))
# the COL8_MCU via at (89.556, 107.6) now sits on J1B's upper mounting pad (x 87.775-89.575, y 106.6-107.8): move it onto the In1 diagonal at (89.9, 107.41), 0.325 mm clear of the pad;
# F.Cu from R9 pin 2: (88.889, 107.985) -> (89.325, 107.985) -> 45 degrees to the via; the In1 tail (89.725, 107.585)-(89.571, 107.585)-(89.556, 107.6) goes, the diagonal ends on the via
k = lambda q: (round(tomm(q.x), 3), round(tomm(q.y), 3))
grave = []; via = None; fc = None
for tr in list(b.GetTracks()):
    if tr.GetNetname() != "/COL8_MCU":
        continue
    if tr.GetClass() == "PCB_VIA":
        if k(tr.GetPosition()) == (89.556, 107.6): via = tr
        continue
    s, e, L = k(tr.GetStart()), k(tr.GetEnd()), b.GetLayerName(tr.GetLayer())
    if L == "In1.Cu" and {s, e} in ({(89.571, 107.585), (89.556, 107.6)}, {(89.725, 107.585), (89.571, 107.585)}):
        b.Remove(tr); grave.append(tr)
    elif L == "In1.Cu" and {s, e} == {(91.925, 105.385), (89.725, 107.585)}:
        (tr.SetEnd if e == (89.725, 107.585) else tr.SetStart)(V(mm(89.9), mm(107.41)))
    elif L == "F.Cu" and {s, e} == {(88.889, 107.985), (89.556, 107.6)}:
        fc = tr
assert via is not None and fc is not None
via.SetPosition(V(mm(89.9), mm(107.41)))
fc.SetStart(V(mm(88.889), mm(107.985))); fc.SetEnd(V(mm(89.325), mm(107.985)))
n2 = pcbnew.PCB_TRACK(b); n2.SetLayer(pcbnew.F_Cu); n2.SetWidth(fc.GetWidth()); n2.SetNet(fc.GetNet())
n2.SetStart(V(mm(89.325), mm(107.985))); n2.SetEnd(V(mm(89.9), mm(107.41))); b.Add(n2)
print("COL8_MCU via moved, In1 tail removed", len(grave), "(expect 2)")
pcbnew.SaveBoard(sys.argv[2], b)
