"""Mode-LED labels: 'TMR-M' -> 'TMR M' (dash removed from the 3-letter + weekday labels).
usage (KiCad python): silk_nodash.py in.kicad_pcb out.kicad_pcb"""
import re, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and re.fullmatch(r"[A-Z]{3}-[A-Z]", d.GetText()):
        print("  %s -> %s" % (d.GetText(), d.GetText().replace("-", " ")))
        d.SetText(d.GetText().replace("-", " ")); n += 1
print("relabelled %d" % n)
pcbnew.SaveBoard(sys.argv[2], b)
