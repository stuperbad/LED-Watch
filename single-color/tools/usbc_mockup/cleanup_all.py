"""cleanup_all.py IN OUT : whole-board artefact pass (reviewer's 'no acute angles / no jogs' rule): delete zero-length pieces, rebuild every chain that has a micro piece (< 0.05 mm) or an end off a pad / via centre on its own lines, guarded by the 0.10 / 0.20 mm clearances."""
import sys, math
sys.path.insert(0, r"C:\Users\evanf\AppData\Local\Temp\claude\C--Users-evanf-Desktop-LED-Watch\7d45cda8-235b-47cf-9813-ce50d757bd77\scratchpad\v12")
import pcbnew
import cleanlib
from editlib import Ed
e = Ed(sys.argv[1]); b = e.b
gone = []
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and pcbnew.ToMM(t.GetLength()) < 0.002:
        gone.append((t.GetNetname(), b.GetLayerName(t.GetLayer()), round(pcbnew.ToMM(t.GetStart().x), 3), round(pcbnew.ToMM(t.GetStart().y), 3)))
        b.Remove(t); e.grave.append(t)
print("zero-length pieces removed:", gone)
allk = {cleanlib.key(b, t) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"}
rep, grave = cleanlib.clean_chains(b, allk, (60.0, 60.0, 140.0, 140.0), ends_too=False, skip={('/COL0', 'F.Cu')}); e.grave += grave
for r in rep: print(r)
pcbnew.SaveBoard(sys.argv[2], b)
