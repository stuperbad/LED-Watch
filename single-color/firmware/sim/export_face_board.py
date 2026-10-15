"""Export the board geometry + matrix mapping for the browser simulator straight from a KiCad board file (no plan.json needed).

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" firmware/sim/export_face_board.py [board.kicad_pcb]   ->  firmware/sim/face_data.js

LED x/y (mm, y down like the board, 12 o'clock = -y, origin = board centre 100,100) come from the footprint positions;
row/col come from the nets of the LED pads (ROWn / COLn). Indicator LEDs are sorted left to right (= SET TMR ALM BAT FUN CFG LCK on the Y42 board).
"""
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
board_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "hardware" / "LED Watch - Single Color.kicad_pcb"
b = pcbnew.LoadBoard(str(board_file))
CX = CY = 100.0
mm = pcbnew.ToMM

leds, inds, sw = [], [], []
for f in b.GetFootprints():
    ref = f.GetReference()
    x, y = mm(f.GetPosition().x) - CX, mm(f.GetPosition().y) - CY
    nets = {p.GetNumber(): p.GetNetname().lstrip("/") for p in f.Pads()}
    rc = {}
    for n in nets.values():
        m = re.fullmatch(r"(ROW|COL)(\d+)", n)
        if m:
            rc[m.group(1)] = int(m.group(2))
    if re.fullmatch(r"[HMS]\d+", ref):
        size = re.search(r"LED_(\d{4})_", str(f.GetFPID().GetLibItemName())).group(1)
        leds.append(dict(ref=ref, ring=ref[0], x=round(x, 3), y=round(y, 3), size=size, row=rc["ROW"], col=rc["COL"]))
    elif re.fullmatch(r"IND\d", ref):
        inds.append(dict(ref=ref, x=round(x, 3), y=round(y, 3), row=rc["ROW"], col=rc["COL"]))
    elif ref in ("SW1", "SW2"):
        sw.append(dict(ref=ref, x=round(x, 3), y=round(y, 3)))
inds.sort(key=lambda d: d["x"])
radii = {}
for r in "HMS":
    rr = [math.hypot(L["x"], L["y"]) for L in leds if L["ring"] == r]
    radii[r] = round(sum(rr) / len(rr), 3)
# board diameter from the outline (the circle's extent along x at y = centre line is not available directly: use the ring-LED extent plus the edge margin of the design = 42.0 mm for Y42)
D = 42.0
pins = {}
for m in re.finditer(r"#define PIN_((?:ROW|COL)\d+)\w*\s+PORT(\w), (\d)", (ROOT / "firmware" / "pins.h").read_text()):
    pins[m.group(1)] = "P%s%s" % (m.group(2), m.group(3))
for m in re.finditer(r"#define PIN_(BUZ_[AB])\s+PORT(\w), (\d)", (ROOT / "firmware" / "pins.h").read_text()):
    pins[m.group(1)] = "P%s%s" % (m.group(2), m.group(3))
data = dict(pins=pins, board=board_file.stem.split("_")[0], D=D, radii=radii,
            cell=dict(name="KXOB25-05X3TF", w=23.0, h=8.0, t=1.2, x=0.0, y=0.0), cells=[dict(x=0.0, y=0.0)],
            leds=leds, inds=inds, sw=sw)
out = ROOT / "firmware" / "sim" / "face_data.js"
out.write_text("window.FACE = " + json.dumps(data, separators=(",", ":")) + ";\n")
print("wrote", out, len(leds), "ring LEDs,", len(inds), "indicators, radii", radii)
for d in inds:
    print(" ", d["ref"], "x=%.1f" % d["x"], "row", d["row"], "col", d["col"])
