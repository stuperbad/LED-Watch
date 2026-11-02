"""promote_revC.py : turn the USB-C mock-up into the main board (revision C), 2026-11-02.
Reads hardware/mockups/LED Watch - USB-C.kicad_pcb / .kicad_sch, writes hardware/LED Watch - Single Color.kicad_pcb / .kicad_sch:
 * schematic: project name in every symbol instance "LED Watch - USB-C" -> "LED Watch - Single Color", title block title / rev C, the mock-up wording out of the title
 * board: title block rev C, date, comment; zones refilled (KiCad python)
The .kicad_pro / .kicad_prl / library tables of hardware/ stay as they are (the mock-up project file only differs in its file names). Revision B is archived in archive/boards/rev-B-pogo/."""
import os, re, sys, pcbnew
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware"))
M = os.path.join(HW, "mockups"); N = "LED Watch - Single Color"
t = open(os.path.join(M, "LED Watch - USB-C.kicad_sch"), encoding="utf8").read()
t = t.replace('(project "LED Watch - USB-C"', '(project "%s"' % N)
t = t.replace('(title "LED watch single colour - solar variant, USB-C mock-up")', '(title "LED watch single colour - solar, USB-C charge and program (rev C)")')
t = re.sub(r'(\(title_block.*?\(rev )"B"', r'\1"C"', t, count=1, flags=re.S)
assert 'LED Watch - USB-C' not in t.replace("USB-C power", ""), [l for l in t.splitlines() if "LED Watch - USB-C" in l][:3]
open(os.path.join(HW, N + ".kicad_sch"), "w", encoding="utf8").write(t)
b = pcbnew.LoadBoard(os.path.join(M, "LED Watch - USB-C.kicad_pcb"))
tb = b.GetTitleBlock(); tb.SetRevision("C"); tb.SetDate("2026-11-02")
tb.SetComment(0, "4-layer 1.6 mm, JLCPCB rules (0.10 mm track/space, 0.15 mm via). Charge and program over USB-C (GCT USB4110, BQ21040). See hardware/REVISIONS.md")
b.SetTitleBlock(tb)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(os.path.join(HW, N + ".kicad_pcb"), b)
print("written", N)
