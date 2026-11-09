"""apply_models.py IN.kicad_pcb OUT.kicad_pcb [--lib hardware/footprints/LEDWatch.pretty] : 3D models for the parts that had none or a missing file (KiCad python, idempotent).
  J2  USB-C        ${KIPRJMOD}/3dmodels/usbc_gct_usb4110_aligned.step   (GCT's own model, aligned by align_gct_step.py; usbc_gct_usb4110.step is the fallback built from the drawing)
  U1  MCU          ${KIPRJMOD}/3dmodels/qfn48_6x6_ep4p2.step    (same reason)
  U4  BQ25570      stock Texas VQFN-RGR-20 3.5 x 3.5 mm model
  BZ1 piezo        ${KIPRJMOD}/3dmodels/piezo_pkmcs0909.step
  MECH1 solar cell 23 x 8 x 1.2 mm on the front between the cell pads; MECH2 / MECH3 the two LiPo pouches 15 x 15 x 5 mm on the back, bottom 1.1 mm above the board
  (the parts under the batteries are up to 1.1 mm high).   MECH parts are board-only footprints (no symbol, not in BOM or position files).
Models are made by make_models.py.   With --lib the library footprints get the same model entries."""
import sys, os, pcbnew
a = sys.argv[1:]; src, dst = a[0], a[1]; lib = a[a.index("--lib") + 1] if "--lib" in a else None
b = pcbnew.LoadBoard(src); FM = pcbnew.FromMM
STOCK = "${KICAD10_3DMODEL_DIR}/"; PRJ = "${KIPRJMOD}/3dmodels/"
def model(path, z=0.0):
    m = pcbnew.FP_3DMODEL(); m.m_Filename = path; m.m_Offset = pcbnew.VECTOR3D(0, 0, z); m.m_Scale = pcbnew.VECTOR3D(1, 1, 1); m.m_Rotation = pcbnew.VECTOR3D(0, 0, 0); m.m_Show = True; m.m_Opacity = 1.0; return m
def setmodel(fp, path, z=0.0):
    fp.Models().clear(); fp.Models().push_back(model(path, z))
for ref, path in (("J2", PRJ + "usbc_gct_usb4110_aligned.step"), ("U1", PRJ + "qfn48_6x6_ep4p2.step"), ("BZ1", PRJ + "piezo_pkmcs0909.step"),
                  ("U4", STOCK + "Package_DFN_QFN.3dshapes/Texas_VQFN-RGR-20-1EP_3.5x3.5mm_Pitch0.5mm.step")):
    setmodel(b.FindFootprintByReference(ref), path); print("model set on", ref)
for f in list(b.GetFootprints()):
    if f.GetReference().startswith("MECH"): b.Remove(f)
mech = []
def add_mech(ref, value, fpname, path, x, y, back, z=0.0):
    f = pcbnew.FOOTPRINT(b); f.SetReference(ref); f.SetValue(value); f.SetFPID(pcbnew.LIB_ID("LEDWatch", fpname))
    f.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    f.Reference().SetVisible(False); f.Value().SetVisible(False); setmodel(f, path, z)
    b.Add(f); f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    if back: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    mech.append(f); print("added", ref, value, "(%.2f, %.2f)" % (x, y), "back" if back else "front")
add_mech("MECH1", "Solar cell KXOB25-05X3TF 23x8x1.2 mm", "MECH_SolarCell_KXOB25_23x8x1.2mm", PRJ + "cell_kxob25.step", 100.0, 100.0, False)
add_mech("MECH2", "LiPo 501515 15x15x5 mm (upper)", "MECH_LiPo_501515_15x15x5mm", PRJ + "lipo_501515.step", 100.0, 88.5, True, 1.1)
add_mech("MECH3", "LiPo 501515 15x15x5 mm (lower)", "MECH_LiPo_501515_15x15x5mm", PRJ + "lipo_501515.step", 100.0, 111.5, True, 1.1)
pcbnew.SaveBoard(dst, b)
if lib:
    io = pcbnew.PCB_IO_KICAD_SEXPR()
    seen = set()
    for f in mech:
        n = str(f.GetFPID().GetLibItemName())
        if n in seen: continue
        seen.add(n); g = pcbnew.FOOTPRINT(f)                      # copy, placed at the origin on the front
        g.SetPosition(pcbnew.VECTOR2I(0, 0))
        if g.IsFlipped(): g.Flip(g.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        io.FootprintSave(lib, g); print("library footprint", n)
    for fpn, ref, path in (("Piezo_Murata_PKMCS0909E4000-R1_9x9mm", "BZ1", PRJ + "piezo_pkmcs0909.step"), ("BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm", "U4", STOCK + "Package_DFN_QFN.3dshapes/Texas_VQFN-RGR-20-1EP_3.5x3.5mm_Pitch0.5mm.step")):
        g = io.FootprintLoad(lib, fpn); setmodel(g, path); io.FootprintSave(lib, g); print("library footprint updated", fpn)
