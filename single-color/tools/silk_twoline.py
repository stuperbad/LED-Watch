"""Mode-LED labels on two lines: mode name ('SET') on top, a smaller weekday letter ('S') under it.
usage (KiCad python): silk_twoline.py in.kicad_pcb out.kicad_pcb"""
import re, sys
import pcbnew
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
H1, W1, Y1 = 0.85, 0.60, 105.80   # mode name: height, char width, centre y
H2, W2, Y2 = 0.60, 0.45, 106.855  # weekday letter
T = 0.15
b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    m = re.fullmatch(r"([A-Z]{3})[ -]([A-Z])", d.GetText())
    if not m: continue
    x = d.GetPosition().x
    d.SetText(m.group(1)); d.SetTextSize(pcbnew.VECTOR2I(mm(W1), mm(H1))); d.SetTextThickness(mm(T))
    d.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); d.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    d.SetPosition(pcbnew.VECTOR2I(x, mm(Y1)))
    e = pcbnew.PCB_TEXT(b); e.SetLayer(d.GetLayer()); e.SetText(m.group(2))
    e.SetTextSize(pcbnew.VECTOR2I(mm(W2), mm(H2))); e.SetTextThickness(mm(T))
    e.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); e.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    e.SetPosition(pcbnew.VECTOR2I(x, mm(Y2))); b.Add(e)
    for t in (d, e):
        r = t.GetBoundingBox()
        print("  %-4s x %.3f..%.3f  y %.3f..%.3f" % (t.GetText(), tomm(r.GetX()), tomm(r.GetRight()), tomm(r.GetY()), tomm(r.GetBottom())))
    n += 1
print("split %d labels" % n)
pcbnew.SaveBoard(sys.argv[2], b)
