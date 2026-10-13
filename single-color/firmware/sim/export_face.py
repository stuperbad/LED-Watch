"""Export real board geometry + matrix mapping for the browser simulator.

  python firmware/sim/export_face.py [board_dir]   ->  firmware/sim/face_data.js

LED x/y (mm, y down like the board, 12 o'clock = -y) come from boards/<board>/plan.json;
row/col come from the netlist schematic/n_solar.xml (same source as pins.h).
"""
import json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
board = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "boards" / "Y43"
plan = json.load(open(board / "plan.json"))

rc = {}
for net in ET.parse(ROOT / "schematic" / "n_solar.xml").getroot().find("nets"):
    m = re.fullmatch(r"/(ROW|COL)(\d+)", net.get("name"))
    if m:
        for node in net:
            if re.fullmatch(r"[HMS]\d+|IND\d", node.get("ref")):
                rc.setdefault(node.get("ref"), {})[m.group(1)] = int(m.group(2))

leds = []
for L in plan["leds"]:
    leds.append(dict(ref=L["ref"], ring=L["ring"], x=round(L["x"], 3), y=round(L["y"], 3),
                     size=L["size"], row=rc[L["ref"]]["ROW"], col=rc[L["ref"]]["COL"]))
inds = []
for q in plan["parts"]:
    if re.fullmatch(r"IND\d", q["ref"]):
        inds.append(dict(ref=q["ref"], x=round(q["x"], 3), y=round(q["y"], 3),
                         row=rc[q["ref"]]["ROW"], col=rc[q["ref"]]["COL"]))
inds.sort(key=lambda d: d["x"])  # left to right = SET TMR BAT FUN CFG LCK
sw = [dict(ref=q["ref"], x=round(q["x"], 3), y=round(q["y"], 3)) for q in plan["parts"] if q["ref"] in ("SW1", "SW2")]
pins = {}
for m in re.finditer(r"#define PIN_((?:ROW|COL)\d+)\w*\s+PORT(\w), (\d)", (ROOT / "firmware" / "pins.h").read_text()):
    pins[m.group(1)] = "P%s%s" % (m.group(2), m.group(3))
data = dict(pins=pins, board=board.name, D=plan["D"], radii=plan["radii"], cell=plan["cell"], cells=plan["cells"],
            leds=leds, inds=inds, sw=sw)
out = ROOT / "firmware" / "sim" / "face_data.js"
out.write_text("window.FACE = " + json.dumps(data, separators=(",", ":")) + ";\n")
print("wrote", out, len(leds), "ring LEDs,", len(inds), "indicators")
for d in inds:
    print(" ", d["ref"], "x=%.1f" % d["x"], "row", d["row"], "col", d["col"])
