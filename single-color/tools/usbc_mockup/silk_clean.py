"""silk_clean.py in.kicad_pcb out.kicad_pcb : strip the footprint silkscreen of the USB-C mock-up (owner, 2026-11-02): no LED polarity dots, no part outlines / borders, no reference texts on the back.
Kept: all text on the board (front numbers, weekday letters, mode labels; back + and - at the battery plugs), and the smallest orientation marks of five parts whose rotation JLCPCB's placement preview
has to be checked against: U1 / U2 pin-1 triangle, U4 pin-1 dot, U5 pin-1 triangle, D50 cathode bar (its 3 lines). KiCad python."""
import pcbnew, sys, collections
b = pcbnew.LoadBoard(sys.argv[1]); L = b.GetLayerName
KEEP = {"U1": ("Polygon",), "U2": ("Polygon",), "U4": ("Circle",), "U5": ("Polygon",), "D50": ("Line", "Polygon", "Circle")}
grave = []; gone = collections.Counter(); kept = collections.Counter(); hid = 0
for fp in b.GetFootprints():
    keepkinds = KEEP.get(fp.GetReference(), ())
    for it in list(fp.GraphicalItems()):
        if "Silk" not in L(it.GetLayer()):
            continue
        kind = it.GetShapeStr() if it.GetClass() == "PCB_SHAPE" else it.GetClass()
        if kind in keepkinds:
            kept[fp.GetReference()] += 1; continue
        fp.Remove(it); grave.append(it); gone[(fp.GetFPIDAsString().split(":")[-1][:22], kind)] += 1
    for fld in (fp.Reference(), fp.Value()):
        if fld.IsVisible() and "Silk" in L(fld.GetLayer()):
            fld.SetVisible(False); hid += 1
print("removed:", sum(gone.values()), dict(gone)); print("kept:", dict(kept)); print("fields hidden:", hid)
pcbnew.SaveBoard(sys.argv[2], b)
