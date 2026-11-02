"""final_clean.py in.kicad_pcb out.kicad_pcb : the last dead copper the DRC reported on the USB-C mock-up (2026-11-02): two zero-length /COL10 F.Cu pieces at (85.61, 92.32);
the dead /COL9_MCU via at (106.35, 93.05) with its In1 spur to (103.8, 92.47) (via_dangling: connected on one layer only); one of the two GND vias stacked at (100.0, 91.87). KiCad python."""
import pcbnew, sys
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); grave = []
k = lambda p: (round(tomm(p.x), 3), round(tomm(p.y), 3))
gv = []; n = 0
for t in list(b.GetTracks()):
    net = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        if net == "/COL9_MCU" and k(t.GetPosition()) == (106.35, 93.05):
            b.Remove(t); grave.append(t); n += 1
        elif net == "GND" and k(t.GetPosition()) == (100.0, 91.87):
            gv.append(t)
        continue
    s, e = k(t.GetStart()), k(t.GetEnd())
    if net == "/COL10" and b.GetLayerName(t.GetLayer()) == "F.Cu" and tomm(t.GetLength()) < 0.01 and abs(s[0] - 85.61) < 0.02 and abs(s[1] - 92.32) < 0.02:
        b.Remove(t); grave.append(t); n += 1
    elif net == "/COL9_MCU" and b.GetLayerName(t.GetLayer()) == "In1.Cu" and {s, e} == {(106.35, 93.05), (105.77, 92.47)}:
        b.Remove(t); grave.append(t); n += 1
    elif net == "/COL9_MCU" and b.GetLayerName(t.GetLayer()) == "In1.Cu" and {s, e} == {(105.77, 92.47), (103.8, 92.47)}:
        b.Remove(t); grave.append(t); n += 1
if len(gv) == 2:
    b.Remove(gv[1]); grave.append(gv[1]); n += 1
print("removed", n, "(expect 6: 2 COL10 pieces, 1 via, 2 In1 pieces, 1 duplicate GND via); stacked GND vias found", len(gv))
pcbnew.SaveBoard(sys.argv[2], b)
