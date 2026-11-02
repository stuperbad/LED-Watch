"""sch_usbc.py : schematic of the USB-C mock-up = the hand-arranged rev B sheet, minus the 1.27 mm UPDI pogo pads (old J2), plus the USB-C charging / UPDI block.
Reads  hardware/LED Watch - Single Color.kicad_sch  (never changed), writes  hardware/mockups/LED Watch - USB-C.kicad_sch  next to the mock-up board.
New parts (same references as on the mock-up board): J2 GCT USB4110 receptacle, U5 BQ21040 charger, C55 / C56 1 uF, R68 / R69 5.1 k (CC pull-downs), R70 8.2 k (ISET), R71 10 k (TS),
R72 1 k (SBU to UPDI) and D50 BAT54WS (UPDI clamp to +3V3). Drawing style of gen_schematic.py (a stub wire on every pin, labels / power symbols on its end).
KiCad python:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" sch_usbc.py
Net names: labels become /NAME on the root sheet, so the board nets CC1 CC2 SBU ISET TS must be /CC1 /CC2 /SBU /ISET /TS (rename_nets.py)."""
import sys, os, re
HW = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware"))
sys.path.insert(0, HW)
import gen_schematic as gs
G = gs.G
OLD, NEW = "LED Watch - Single Color", "LED Watch - USB-C"
SRC = os.path.join(HW, OLD + ".kicad_sch")
DST = os.path.join(HW, "mockups", NEW + ".kicad_sch")


def blocks(t, start=None):
    """child blocks (start, end, text) of the root (kicad_sch ...) form"""
    i = t.index("(", 1) if start is None else start
    out, depth, instr, b0 = [], 0, False, None
    j = i
    while j < len(t):
        c = t[j]
        if instr:
            if c == "\\":
                j += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            if depth == 0:
                b0 = j
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                out.append((b0, j + 1, t[b0:j + 1]))
            if depth < 0:
                break
        j += 1
    return out


def where(b):
    pts = [(float(a), float(c)) for a, c in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", b)] or [(float(a), float(c)) for a, c in re.findall(r"\(at ([-\d.]+) ([-\d.]+)", b)[:1]]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


t = open(SRC, encoding="utf8").read()
gs.ROOT_UUID = re.search(r'\(uuid "([^"]*)"', t[:600]).group(1)
gs.PROJECT = NEW

# ---- 1. take the pogo-pad block out (old J2: symbol, 4 stubs, RESET / UPDI labels, 2 power symbols, the note)
cut = []
for s0, e0, b in blocks(t):
    k = re.match(r"\((\w+)", b).group(1)
    if k in ("wire", "label", "symbol", "text", "junction", "no_connect"):
        p = where(b)
        if p and 360 < p[0] < 430 and 255 < p[1] < 310:
            cut.append((s0, e0, k, (re.search(r'\(property "Reference" "([^"]*)"', b) or re.search(r'\(label "([^"]*)"', b) or re.search(r"\((text) ", b)).group(1) if k in ("symbol", "label", "text") else ""))
assert sorted(c[3] for c in cut if c[2] != "wire") == sorted(["#PWR026", "#PWR027", "J2", "RESET", "UPDI", "text"]), cut
# U5 now drives BATT (a power output), so the PWR_FLAG that stood in for the battery plug on that net (#FLG050) and its branch wire go as well
flag = [(s0, e0, b) for s0, e0, b in blocks(t) if '"#FLG050"' in b][0]
fx, fy = re.search(r"\(at ([-\d.]+) ([-\d.]+)", flag[2]).groups()
cut.append((flag[0], flag[1], "symbol", "#FLG050"))
for s0, e0, b in blocks(t):
    if b.startswith("(wire") and re.search(r"\(xy %s %s\)" % (re.escape(fx), re.escape(fy)), b):
        cut.append((s0, e0, "wire", ""))
for s0, e0, k, n in sorted(cut, reverse=True):
    t = t[:s0].rstrip(" \t") + t[e0:].lstrip("\n") if False else t[:s0] + t[e0:]
t = t.replace('(project "%s"' % OLD, '(project "%s"' % NEW)

# ---- 2. the USB-C block, far below the existing drawing (free area, y > 400)
s = gs.Sch("usb-c block")
s.pwr = max(int(x) for x in re.findall(r'"#(?:PWR|FLG)(\d+)"', t))
OX, OY = 380.0, 440.0
s.text("USB-C CHARGING AND UPDI PROGRAMMING (replaces the 1.27 mm pogo pads). The receptacle sits on the back at the rim (3 o'clock). VBUS -> U5 (BQ21040) -> BATT; "
       "the two SBU pins carry UPDI (1 k in series, BAT54WS clamp to +3V3); USB data pins are not used.", (OX - 20, OY - 52), 2, max_mm=240)
j2 = s.place("Connector", "USB_C_Receptacle_USB2.0_16P", "J2", "USB-C power + UPDI (GCT USB4110)", "Connector_USB:USB_C_Receptacle_GCT_USB4110", OX, OY, 0,
             extra={"MPN": "USB4110-GF-A", "LCSC": "C5143397"},
             desc="USB Type-C receptacle, 16 pins, GCT USB4110. VBUS charges the LiPo through U5; SBU1 / SBU2 (tied) are the UPDI line; CC1 / CC2 5.1 k to ground; D+ / D- unused",
             ref_at=(-16.0, -29.0), val_at=(-16.0, -26.5), just="left")
vb = s.power(j2, "A4", "VBUS", 2 * G)
s.flag_on(gs.add(s.pin_end(j2, "A4")[0], 0, G), 90)
s.net(j2, "A5", "CC1", 2 * G)
s.net(j2, "B5", "CC2", 2 * G)
s.net(j2, "A8", "SBU", 2 * G)
s.net(j2, "B8", "SBU", 2 * G)
for pn in ("A6", "A7", "B6", "B7"):
    s.nc(j2, pn)
s.power(j2, "A1", "GND", 2 * G)
s.power(j2, "SH", "GND", 2 * G)

UX, UY = OX + 80.0, OY
u5 = s.place("Battery_Management", "BQ21040DBV", "U5", "BQ21040DBVR", "Package_TO_SOT_SMD:SOT-23-6", UX, UY, 0,
             extra={"MPN": "BQ21040DBVR", "LCSC": "C202311"},
             desc="TI single-cell Li-ion charger, 4.2 V, 800 mA max; charge current 540 / R_ISET (10 k = 54 mA); TS to ground through 10 k = no thermistor",
             ref_at=(-12.0, -9.0), val_at=(-12.0, -6.5), just="left")
s.power(u5, "6", "VBUS", 2 * G)
s.net(u5, "2", "BATT", 2 * G)
s.net(u5, "1", "TS", 2 * G)
s.net(u5, "4", "ISET", 2 * G)
s.nc(u5, "3")
s.power(u5, "5", "GND", G)

PY = OY + 70.0
parts = [("C", "C55", "1u", "Capacitor_SMD:C_0402_1005Metric", "C52923", "VBUS", "GND", "charger input capacitor, 1 uF"),
         ("C", "C56", "1u", "Capacitor_SMD:C_0402_1005Metric", "C52923", "BATT", "GND", "charger output capacitor, 1 uF"),
         ("R", "R68", "5.1k", "Resistor_SMD:R_0402_1005Metric", "C25905", "CC1", "GND", "CC1 pull-down: tells the source a sink is attached"),
         ("R", "R69", "5.1k", "Resistor_SMD:R_0402_1005Metric", "C25905", "CC2", "GND", "CC2 pull-down"),
         ("R", "R70", "10k", "Resistor_SMD:R_0402_1005Metric", "C25744", "ISET", "GND", "charge current set: 540 / 10 k = 54 mA (BQ21040 datasheet, K_ISET = 540 A-ohm)"),
         ("R", "R71", "10k", "Resistor_SMD:R_0402_1005Metric", "C25744", "TS", "GND", "TS held at mid-scale: no battery thermistor")]
for i, (k, ref, val, fp, lcsc, n1, n2, d) in enumerate(parts):
    x = OX + i * 22.0
    c = s.place("Device", k, ref, val, fp, x, PY, 0, extra={"LCSC": lcsc}, desc=d)
    (s.power if n1 == "VBUS" else s.net)(c, "1", *( ("VBUS",) if n1 == "VBUS" else (n1,)))
    s.power(c, "2", "GND")
r72 = s.place("Device", "R", "R72", "1k", "Resistor_SMD:R_0402_1005Metric", OX + 6 * 22.0, PY, 0, extra={"LCSC": "C11702"}, desc="series resistor between the receptacle's SBU pins and the MCU UPDI pin")
s.net(r72, "1", "SBU", 2 * G)
s.net(r72, "2", "UPDI", 2 * G)
for rot in (90, 270):
    d50 = s.place("Device", "D_Schottky", "D50", "BAT54WS", "Diode_SMD:D_SOD-323", OX + 7 * 22.0 + 12, PY, rot, extra={"MPN": "BAT54WS", "LCSC": "C304155"},
                  desc="UPDI clamp: anode on UPDI, cathode on +3V3, keeps a 5 V fault (VBUS next to SBU in the receptacle) from reaching the MCU pin")
    if s.pin_end(d50, "1")[0][1] < s.pin_end(d50, "2")[0][1]:
        break
    s.items.pop()
s.power(d50, "1", "V33", 2 * G)
s.net(d50, "2", "UPDI", 2 * G)
s.text("UPDI path: SBU (both pins) - R72 1 k - UPDI (the MCU's UPDI pin). D50 clamps UPDI to +3V3.", (OX - 20, PY + 24), 2, max_mm=240)

# ---- 3. splice in: symbols the file does not have yet, then the items
libblk = [(a, b_, x) for a, b_, x in blocks(t) if x.startswith("(lib_symbols")][0]
new = "".join("\n\t\t" + txt.replace("\n", "\n\t\t") for key, txt in s.libs.items() if '(symbol "%s"' % key not in libblk[2])
t = t[:libblk[1] - 1].rstrip() + new + "\n\t" + t[libblk[1] - 1:]
i = t.index("\t(sheet_instances")
t = t[:i] + "\n".join(s.items) + "\n" + t[i:]
t = t.replace('(title "LED watch single colour - solar variant")', '(title "LED watch single colour - solar variant, USB-C mock-up")')
open(DST, "w", encoding="utf8").write(t)
print("wrote", DST, "items", len(s.items), "removed", len(cut))
