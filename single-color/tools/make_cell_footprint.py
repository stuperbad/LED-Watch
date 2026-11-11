"""make_cell_footprint.py LIB.pretty [IN.kicad_pcb OUT.kicad_pcb SYMBOL_UUID] (KiCad python):
1. writes the library footprint KXOB25_cell_2pad_23x8mm: ONE footprint for the whole solar cell (Anysolar KXOB25-05X3TF, 23 x 8 x 1.2 mm), the two hand-soldered pads 2.5 x 7.4 mm at +-10.75 mm
   (pad 1 = + = SOLAR_IN on the right as seen from the front, pad 2 = - = GND on the left), "+" / "-" install marks on the front silkscreen inside the cell area (covered by the cell once soldered; no edge lines), the cell outline on F.Fab,
   courtyard, and the 3D block with the back contacts.  Not in the BOM or position files (hand soldered).
2. with IN / OUT: replaces SC1+ / SC1- / MECH1 and the loose silk marks on the board by one footprint SC1 at the cell centre (100, 100), same pad positions, so the tracks stay connected.
Written 2026-11-05 after the owner could drag the two pads independently."""
import sys, pcbnew
FM = pcbnew.FromMM; mm = pcbnew.ToMM
P = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))
lib = sys.argv[1]; NAME = "KXOB25_cell_2pad_23x8mm"
fp = pcbnew.FOOTPRINT(None); fp.SetFPID(pcbnew.LIB_ID("LEDWatch", NAME)); fp.SetReference("SC1"); fp.SetValue("KXOB25-05X3TF cell")
fp.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
fp.SetLayer(pcbnew.F_Cu)
fp.SetLibDescription("One Anysolar KXOB25-05X3TF SolarBIT (23 x 8 x 1.2 mm, 3 cells in series) as ONE part: two hand-soldered pads 2.5 x 7.4 mm (contact 2.0 x 7.4 mm per data sheet p. 3, the outer 0.5 mm is the soldering fillet / iron access). Pad 1 = + (right, seen from the front), pad 2 = - (left). Copper and mask only, no paste (Sn42/Bi58 by hand).")
fp.SetKeywords("solar cell pad hand solder")
for num, x in (("1", 10.75), ("2", -10.75)):
    p = pcbnew.PAD(fp); p.SetNumber(num); p.SetShape(pcbnew.PAD_SHAPE_RECT); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetSize(P(2.5, 7.4)); p.SetPosition(P(x, 0))
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask); p.SetLayerSet(ls); fp.Add(p)
def text(t, x, y, layer, size=1.2, th=0.2):
    o = pcbnew.PCB_TEXT(fp); o.SetText(t); o.SetLayer(layer); o.SetTextSize(P(size, size)); o.SetTextThickness(FM(th)); o.SetPosition(P(x, y)); fp.Add(o); return o
def seg(x1, y1, x2, y2, layer, w):
    s = pcbnew.PCB_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(layer); s.SetWidth(FM(w)); fp.Add(s)
def rect(x0, y0, x1, y1, layer, w):
    s = pcbnew.PCB_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetLayer(layer); s.SetWidth(FM(w)); s.SetFilled(False); fp.Add(s)
# 2026-11-11: marks sit INSIDE the cell footprint, just inside each pad, so the cell covers them once soldered; no edge lines on the silkscreen
text("+", 8.4, 0, pcbnew.F_SilkS); text("-", -8.4, 0, pcbnew.F_SilkS)
rect(-11.5, -4.0, 11.5, 4.0, pcbnew.F_Fab, 0.1); rect(-12.0, -4.0, 12.0, 4.0, pcbnew.F_CrtYd, 0.05)
fp.Reference().SetVisible(False); fp.Value().SetVisible(False); fp.Reference().SetPosition(P(0, -6.2)); fp.Value().SetPosition(P(0, 6.2)); fp.Value().SetLayer(pcbnew.F_Fab)
m = pcbnew.FP_3DMODEL(); m.m_Filename = "${KIPRJMOD}/3dmodels/cell_kxob25.step"; m.m_Offset = pcbnew.VECTOR3D(0, 0, 0); m.m_Scale = pcbnew.VECTOR3D(1, 1, 1); m.m_Rotation = pcbnew.VECTOR3D(0, 0, 0); m.m_Show = True; m.m_Opacity = 1.0
fp.Models().push_back(m)
io = pcbnew.PCB_IO_KICAD_SEXPR(); io.FootprintSave(lib, fp); print("library footprint written:", NAME)
if len(sys.argv) > 4:
    b = pcbnew.LoadBoard(sys.argv[2])
    for r in ("SC1+", "SC1-", "MECH1"):
        f = b.FindFootprintByReference(r)
        if f: b.Remove(f)
    for d in list(b.GetDrawings()):
        if d.GetLayer() != pcbnew.F_SilkS: continue
        x, y = mm(d.GetPosition().x), mm(d.GetPosition().y)
        if d.GetClass() == "PCB_TEXT" and d.GetText() in ("+", "-") and abs(y - 95.2) < 0.01 and (abs(x - 110.75) < 0.01 or abs(x - 89.25) < 0.01): b.Remove(d)
        elif d.GetClass() == "PCB_SHAPE" and abs(mm(d.GetStart().y) - mm(d.GetEnd().y)) < 1e-6 and mm(d.GetStart().y) in (96.0, 104.0) and abs(mm(d.GetStart().x) - 90.7) < 0.01: b.Remove(d)
    new = io.FootprintLoad(lib, NAME); new.SetReference("SC1"); b.Add(new); new.SetPosition(P(100.0, 100.0))
    for p in new.Pads(): p.SetNet(b.FindNet("/SOLAR_IN" if p.GetNumber() == "1" else "GND"))
    new.SetPath(pcbnew.KIID_PATH("/" + sys.argv[4])); new.Reference().SetVisible(False); new.Value().SetVisible(False)
    pcbnew.SaveBoard(sys.argv[3], b); print("board written; SC1 pads at", [(p.GetNumber(), mm(p.GetPosition().x), mm(p.GetPosition().y), p.GetNetname()) for p in new.Pads()])
