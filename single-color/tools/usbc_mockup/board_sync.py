"""board_sync.py in.kicad_pcb out.kicad_pcb : bring the USB-C mock-up board in line with its schematic (sch_usbc.py) and the BAT54WS datasheet. KiCad python.
 * nets CC1 CC2 SBU ISET TS -> /CC1 /CC2 /SBU /ISET /TS (labels on the root sheet become /NAME; the power-symbol nets VBUS, +3V3, GND keep their names)
 * D50 value BAT54WS, C55 / C56 value 1u (as in the schematic)
 * D50 pads from the PANJIT BAT54WS mounting pad layout (SOD-323, REV.12): 0.73 mm along x 0.50 mm across, centres 2.17 mm apart (KiCad stock: 0.60 x 0.45, 2.10)"""
import pcbnew, sys
mm = pcbnew.FromMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
for n in ("CC1", "CC2", "SBU", "ISET", "TS"):
    it = b.FindNet(n)
    if it is None:
        print("no net", n); continue
    it.SetNetname("/" + n)
b.BuildListOfNets()
for ref, val in (("D50", "BAT54WS"), ("C55", "1u"), ("C56", "1u")):
    b.FindFootprintByReference(ref).SetValue(val)
d = b.FindFootprintByReference("D50")
for p in d.Pads():
    sgn = -1 if p.GetNumber() == "1" else 1
    p.SetSize(V(mm(0.73), mm(0.50)))
    p.SetFPRelativePosition(V(mm(sgn * 1.085), 0))
pcbnew.SaveBoard(sys.argv[2], b)
print("saved", sys.argv[2])
