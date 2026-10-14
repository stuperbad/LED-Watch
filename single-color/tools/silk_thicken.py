"""Raise every silkscreen stroke (text and lines, board and footprint items) to at least MIN mm.
JLCPCB prints silkscreen down to about 0.15 mm line width; thinner prints faint or broken.
usage (KiCad python): silk_thicken.py in.kicad_pcb out.kicad_pcb [min_mm=0.15]"""
import sys, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); MIN = pcbnew.FromMM(float(sys.argv[3]) if len(sys.argv) > 3 else 0.15)
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
n = collections.Counter()
def fix(item, where):
    if item.GetLayer() not in SILK: return
    c = item.GetClass()
    if c in ("PCB_TEXT", "PCB_FIELD", "PCB_TEXTBOX") or hasattr(item, "GetTextThickness") and c != "PCB_SHAPE":
        if item.IsVisible() if hasattr(item, "IsVisible") else True:
            if item.GetTextThickness() < MIN:
                n["text " + where] += 1; item.SetTextThickness(MIN)
    elif c == "PCB_SHAPE":
        w = item.GetWidth()
        if 0 < w < MIN and not item.IsSolidFill():
            n["line " + where] += 1; item.SetWidth(MIN)
for d in b.GetDrawings(): fix(d, "board")
for fp in b.GetFootprints():
    for f in list(fp.GetFields()) + list(fp.GraphicalItems()): fix(f, "footprint")
print(dict(n))
pcbnew.SaveBoard(sys.argv[2], b)
