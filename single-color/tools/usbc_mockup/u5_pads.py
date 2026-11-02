"""u5_pads.py in.kicad_pcb out.kicad_pcb : U5 (BQ21040, SOT-23-6) pads from TI's DBV0006A example board layout (datasheet SLUSB... figure 'Land pattern'): 6 pads 1.1 x 0.6 mm, pitch 0.95, rows 2.6 mm apart
(centres at +-1.3 mm); KiCad stock is 1.325 x 0.6 at +-1.1375 (IPC nominal). KiCad python."""
import pcbnew, sys
mm = pcbnew.FromMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
u = b.FindFootprintByReference("U5")
for p in u.Pads():
    n = int(p.GetNumber())
    x = -1.3 if n <= 3 else 1.3
    y = {1: -0.95, 2: 0.0, 3: 0.95, 4: 0.95, 5: 0.0, 6: -0.95}[n]
    p.SetSize(V(mm(1.1), mm(0.6))); p.SetFPRelativePosition(V(mm(x), mm(y)))
pcbnew.SaveBoard(sys.argv[2], b)
print("saved")
