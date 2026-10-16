"""For all 132 ring LEDs: is every net (row, R, G, B) in the same corner of the LED as on the old routed board?  usage (KiCad python): check_pad_corners.py [board.kicad_pcb]"""
import json, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sk = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "LED Watch - RGB.kicad_pcb")
old = {d["ref"]: d for d in json.load(open(os.path.join(HERE, "..", "data", "old_ring.json")))}
b = pcbnew.LoadBoard(sk)
bad = 0
for f in b.GetFootprints():
    if f.GetReference() not in old:
        continue
    o = old[f.GetReference()]
    corner_old = {p["net"]: ((p["dx"] > 0), (p["dy"] > 0)) for p in o["pads"].values()}
    pc = f.GetPosition()
    for pd in f.Pads():
        q = pd.GetPosition()
        c = ((q.x - pc.x) > 0, (q.y - pc.y) > 0)
        if corner_old[pd.GetNetname()] != c:
            bad += 1
print("LEDs", len(old), "pads in a different corner than on the old board:", bad)
