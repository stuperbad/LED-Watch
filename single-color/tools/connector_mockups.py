"""Connector mock-ups for the programming / charging row on a COPY of the board (never the real file): variants A (pogo row on the front, radial at 1:30), B (pogo row on the strap lug web), C (Tag-Connect TC2030-NL), D (JST SH 3-pin on the back at 3 o'clock).
usage (KiCad python): connector_mockups.py VARIANT out.kicad_pcb [x y rot for C]   (reads mock/base.kicad_pcb); render with kicad-cli pcb render --zoom --pivot"""
import pcbnew, sys, math
mm=pcbnew.FromMM; V=pcbnew.VECTOR2I
variant=sys.argv[1]; out=sys.argv[2]
b=pcbnew.LoadBoard("mock/base.kicad_pcb")
j2=b.FindFootprintByReference("J2")
def to_front(fp):
    if fp.GetLayer()==pcbnew.B_Cu: fp.Flip(fp.GetPosition(), True)
if variant=="A":      # pogo row on the front, radial, 1:30 position
    to_front(j2); j2.SetPosition(V(mm(109.3),mm(91.6))); j2.SetOrientationDegrees(45)
elif variant=="B":    # pogo row on the top strap lug web (front)
    to_front(j2); j2.SetPosition(V(mm(100.0),mm(75.33))); j2.SetOrientationDegrees(0)
elif variant=="C":    # Tag-Connect TC2030-NL on the front near the 1:30 position
    b.Remove(j2)
    lib="C:/Program Files/KiCad/10.0/share/kicad/footprints/Connector.pretty"
    fp=pcbnew.FootprintLoad(lib,"Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical")
    fp.SetReference("J2"); fp.SetPosition(V(mm(float(sys.argv[3])),mm(float(sys.argv[4])))); fp.SetOrientationDegrees(float(sys.argv[5]))
    b.Add(fp)
elif variant=="D":    # JST SH 3-pin side-entry cable connector on the back at 3 o'clock, replacing the pogo pads
    b.Remove(j2)
    j1=b.FindFootprintByReference("J1")
    lib="C:/Program Files/KiCad/10.0/share/kicad/footprints/Connector_JST.pretty"
    fp=pcbnew.FootprintLoad(lib,"JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal")
    fp.SetReference("J2")
    # mirror J1's pose about the 3-9 axis: same distance from the edge, opening toward the right edge
    p=j1.GetPosition(); rot=j1.GetOrientationDegrees()
    b.Add(fp)
    fp.Flip(fp.GetPosition(), True)
    fp.SetPosition(V(mm(200.0-pcbnew.ToMM(p.x)),mm(100.0)))
    fp.SetOrientationDegrees(rot)
    bb=fp.GetBoundingBox(False); shift=mm(120.2)-bb.GetRight(); fp.SetPosition(V(fp.GetPosition().x+shift,fp.GetPosition().y))
pcbnew.SaveBoard(out,b); print(variant,"saved",out)
