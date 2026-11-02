"""viamove_one.py in.kicad_pcb out.kicad_pcb NET x y nx ny : move the via of NET at (x, y) to (nx, ny) (tracks are not touched). KiCad python."""
import sys, pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); net = sys.argv[3]; x, y, nx, ny = [float(a) for a in sys.argv[4:8]]
n = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA" and t.GetNetname() == net and abs(tomm(t.GetPosition().x) - x) < 0.01 and abs(tomm(t.GetPosition().y) - y) < 0.01:
        t.SetPosition(pcbnew.VECTOR2I(mm(nx), mm(ny))); n += 1
pcbnew.SaveBoard(sys.argv[2], b); print("moved", n)
