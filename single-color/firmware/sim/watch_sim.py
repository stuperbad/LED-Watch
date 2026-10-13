"""
Desktop simulator of the watch face, driven by the REAL board data (no hardware needed):
  - LED positions come from boards/<board>/plan.json
  - every LED's matrix row/column comes from the schematic netlist (the same data the firmware headers are generated from)
It shows what the firmware will light for a given time, and which row/column pins it has to drive for each scan slot.

  python firmware/sim/watch_sim.py [HH:MM:SS] [board_dir]        -> firmware/sim/face_HHMMSS.png
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

ROOT = Path(__file__).resolve().parents[2]
hh, mm, ss = (int(v) for v in (sys.argv[1] if len(sys.argv) > 1 else "10:08:37").split(":"))
board = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "boards" / "Y43"

plan = json.load(open(board / "plan.json"))
pos = {L["ref"]: (L["x"], L["y"], L["size"]) for L in plan["leds"]}
for q in plan["parts"]:
    if q["ref"].startswith("IND"):
        pos[q["ref"]] = (q["x"], q["y"], "0402")

# matrix position of every LED from the netlist
rc = {}
for net in ET.parse(ROOT / "schematic" / "n_solar.xml").getroot().find("nets"):
    m = re.fullmatch(r"/(ROW|COL)(\d+)", net.get("name"))
    if m:
        for node in net:
            if re.fullmatch(r"[HMS]\d+|IND\d", node.get("ref")):
                rc.setdefault(node.get("ref"), {})[m.group(1)] = int(m.group(2))

# what a clock face shows: one hour LED, one minute LED, one second LED
lit = [f"H{hh % 12 if hh % 12 else 12}", f"M{mm}", f"S{ss}"]
print("time", f"{hh:02d}:{mm:02d}:{ss:02d}", "lights", lit)
for ref in lit:
    print(f"  {ref:4s} -> ROW{rc[ref]['ROW']} (pull low), COL{rc[ref]['COL']} (drive high through its 220 ohm)")
rows = {rc[r]["ROW"] for r in lit}
print(f"  {len(rows)} different rows -> {len(rows)} scan slots per frame; at 1 kHz per slot each LED is on {100 / len(rows):.0f} % of the time")

fig, ax = plt.subplots(figsize=(8, 8))
ax.add_patch(Circle((0, 0), plan["D"] / 2, fc="#1b2235", ec="#8892b0"))
for ref, (x, y, size) in pos.items():
    r = {"0603": 0.55, "0402": 0.42, "0201": 0.3}.get(size, 0.4)
    on = ref in lit
    ax.add_patch(Circle((x, y), r * (1.9 if on else 1.0), fc="#fff3a0" if on else "#3a4560", ec="#ffd54a" if on else "none", lw=1.5))
ax.set_xlim(-plan["D"] / 2 - 1, plan["D"] / 2 + 1)
ax.set_ylim(plan["D"] / 2 + 1, -plan["D"] / 2 - 1)      # y down like the board
ax.set_aspect("equal"); ax.axis("off")
ax.set_title(f"{hh:02d}:{mm:02d}:{ss:02d}   lit: " + ", ".join(f"{r} (row {rc[r]['ROW']}, col {rc[r]['COL']})" for r in lit), color="w", fontsize=9)
fig.patch.set_facecolor("#0e1220")
out = ROOT / "firmware" / "sim" / f"face_{hh:02d}{mm:02d}{ss:02d}.png"
fig.savefig(out, dpi=110, facecolor=fig.get_facecolor())
print("wrote", out)
