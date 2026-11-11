"""rework_clean.py IN.kicad_pcb BASE.kicad_pcb OUT.kicad_pcb [x0,y0,x1,y1] (KiCad python): rebuild the chains of NEW track pieces (not in BASE) so that they have no micro pieces and end exactly on pad / via centres
(usbc_mockup/cleanlib.py, guarded by the 0.10 / 0.20 mm clearances)."""
import sys
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0] + "/usbc_mockup")
import pcbnew, cleanlib
b = pcbnew.LoadBoard(sys.argv[1]); base = pcbnew.LoadBoard(sys.argv[2])
box = tuple(map(float, sys.argv[4].split(","))) if len(sys.argv) > 4 else (88.0, 92.0, 113.0, 108.0)
old = {cleanlib.key(base, t) for t in base.GetTracks() if t.GetClass() == "PCB_TRACK"}
new = {cleanlib.key(b, t) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"} - old
print("new pieces:", len(new))
rep, grave = cleanlib.clean_chains(b, new, box, ends_too=True)
for r in rep[:60]: print(r)
print("chains rebuilt:", len(rep))
pcbnew.SaveBoard(sys.argv[3], b)
