"""Revision B re-pin, step 1: give U1's pads the revision B nets (and set the title-block revision), nothing else.
usage (KiCad python): repin_pcb.py in.kicad_pcb out.kicad_pcb
Prints the pad changes. The copper that belonged to the old assignment is removed in the next step (reroute_prep.py), the new copper is routed after that.
Revision B (see ../archive/boards/rev-A-2026-10-29-pre-repin/DEPRECATED.md): COL0-7 = PA0-7 (pins 44-48, 1-3), COL8-11 = PB0-3 (pins 4-7),
ROW0-7 = PC0-7 (pins 10-13, 16-19), ROW8-11 = PD0-3 (pins 20-23), SDA/SCL = PF2/PF3 (pins 36/37), BUZ_A/B stay on PB4/PB5, pins 24/25/46/47 columns or free."""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
NEW = {}
for pin, c in {44: 0, 45: 1, 46: 2, 47: 3, 48: 4, 1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11}.items():
    NEW[str(pin)] = f"/COL{c}_MCU"
for i, pin in enumerate([10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23]):
    NEW[str(pin)] = f"/ROW{i}"
NEW["24"] = ""
NEW["25"] = ""
NEW["36"] = "/SDA"
NEW["37"] = "/SCL"
u1 = [f for f in b.GetFootprints() if f.GetReference() == "U1"][0]
nets = b.GetNetsByName()
changed = []
for p in u1.Pads():
    n = p.GetNumber()
    if n not in NEW:
        continue
    want = NEW[n]
    if p.GetNetname() == want:
        continue
    old = p.GetNetname()
    if want:
        p.SetNet(nets[want])
    else:
        p.SetNetCode(0)
    changed.append((int(n), old, want or "(no net)"))
for n, o, w in sorted(changed):
    print(f"pad {n:2d}: {o} -> {w}")
print(len(changed), "pads changed")
tb = b.GetTitleBlock()
tb.SetRevision("B")
b.SetTitleBlock(tb)
pcbnew.SaveBoard(sys.argv[2], b)
