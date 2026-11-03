"""add_tvs_sch.py : adds D51 (UMW UDD32C05L01, 5 V bidirectional TVS, VBUS to GND; first drawn as the Bourns CDSOD323-T05LC, C840637) to the revision C schematic, next to C55 in the USB-C block.
Only appends new items (symbol, two stubs, two power symbols, one note) and the Device:D_TVS library symbol; nothing existing is changed.
Run with the system Python (3.10):  python add_tvs_sch.py   (from the repository's single-color/hardware folder)"""
import sys, os, re
HW = os.path.abspath(".")
sys.path.insert(0, HW)
import gen_schematic as gs
G = gs.G
SRC = os.path.join(HW, "LED Watch - Single Color.kicad_sch")
t = open(SRC, encoding="utf8").read()
assert '"D51"' not in t, "D51 already exists"
gs.ROOT_UUID = re.search(r'\(uuid "([^"]*)"', t[:600]).group(1)
gs.PROJECT = "LED Watch - Single Color"
s = gs.Sch("tvs")
s.pwr = max(int(x) for x in re.findall(r'"#(?:PWR|FLG)(\d+)"', t))
X, Y = 360.68, 482.6                         # one column left of C55 (382.27, 482.6), same row
for rot in (90, 270):
    d51 = s.place("Device", "D_TVS", "D51", "UDD32C05L01", "Diode_SMD:D_SOD-323", X, Y, rot, extra={"MPN": "UDD32C05L01", "LCSC": "C19185929", "Manufacturer": "UMW"},
                  desc="ESD / surge clamp on VBUS: UMW UDD32C05L01, bidirectional TVS, 5 V working, 6 V minimum breakdown, 9.8 V clamp at 1 A, 18.3 V at 5 A, ESD 8 kV contact / 15 kV air. Keeps a static spark or a hot-plug spike from the cable off the charger input (BQ21040 absolute maximum 30 V)",
                  ref_at=(3.0, -1.4), val_at=(3.0, 1.4))
    if s.pin_end(d51, "1")[0][1] < s.pin_end(d51, "2")[0][1]:
        break
    s.items.pop()
s.power(d51, "1", "VBUS")
s.power(d51, "2", "GND")
s.text("D51: static-discharge (ESD) clamp on VBUS, placed next to the receptacle on the board.", (X - 12.0, Y + 14.0), 2, max_mm=70)
libblk = None
i0 = t.index("(lib_symbols")
depth, j, instr = 0, i0, False
while True:
    c = t[j]
    if instr:
        if c == "\\": j += 1
        elif c == '"': instr = False
    elif c == '"': instr = True
    elif c == "(": depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0: break
    j += 1
libend = j + 1
libtxt = t[i0:libend]
new = "".join("\n\t\t" + txt.replace("\n", "\n\t\t") for key, txt in s.libs.items() if '(symbol "%s"' % key not in libtxt)
t = t[:libend - 1].rstrip() + new + "\n\t" + t[libend - 1:]
i = t.index("\t(sheet_instances")
t = t[:i] + "\n".join(s.items) + "\n" + t[i:]
open(SRC, "w", encoding="utf8").write(t)
print("added D51; libs added:", list(s.libs), "items", len(s.items))
