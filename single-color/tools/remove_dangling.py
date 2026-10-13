"""delete the vias KiCad reports as dangling (connected on one layer only): usage: remove_dangling.py board.kicad_pcb drc_all.json out.kicad_pcb"""
import json, re, sys
board, drc, out = sys.argv[1:4]
pts = [(i["pos"]["x"], i["pos"]["y"]) for v in json.load(open(drc))["violations"] if v["type"] == "via_dangling" for i in v["items"]]
txt = open(board, encoding="utf8").read()
n = 0
def keep(m):
    global n
    at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", m.group(1))
    x, y = float(at.group(1)), float(at.group(2))
    if any(abs(x - a) < 0.01 and abs(y - b) < 0.01 for a, b in pts):
        n += 1
        return ""
    return m.group(0)
txt = re.sub(r"\t\(via\n(.*?)\n\t\)\n", keep, txt, flags=re.S)
open(out, "w", encoding="utf8").write(txt)
print("removed", n, "dangling vias of", len(pts))
