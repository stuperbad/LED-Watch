"""Read the 132 RGB LEDs of the old routed RGB board (archive/2026-10-14 ...): position relative to the board centre, rotation, and the nets on each pad.
Writes data/old_ring.json.   usage (KiCad python): extract_old_ring.py"""
import json
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "archive", "2026-10-14 old RGB board - routed, Harvatek LEDs, ATmega165PA", "LED Watch - RGB.kicad_pcb")
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(SRC)
leds = []
for f in b.GetFootprints():
    if "B39D3" not in str(f.GetValue()):
        continue
    p = f.GetPosition()
    d = dict(ref=f.GetReference(), x=round(mm(p.x) - 100.0, 4), y=round(mm(p.y) - 100.0, 4), rot=f.GetOrientationDegrees(), pads={})
    for pd in f.Pads():
        q = pd.GetPosition()
        d["pads"][pd.GetNumber()] = dict(net=pd.GetNetname(), dx=round(mm(q.x - p.x), 4), dy=round(mm(q.y - p.y), 4))
    leds.append(d)
leds.sort(key=lambda d: int(d["ref"][1:]))
json.dump(leds, open(os.path.join(HERE, "..", "data", "old_ring.json"), "w"), indent=0)
print(len(leds), "LEDs;", "first:", leds[0]["ref"], leds[0]["pads"])
