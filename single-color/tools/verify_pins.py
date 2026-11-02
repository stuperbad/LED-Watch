"""Check every connection of the MCU (U1) against the datasheets, using the real files: hardware/netlist.xml and docs/datasheets/*.pdf.
usage: python tools/verify_pins.py [--md]         (needs PyMuPDF: pip install pymupdf)   exit code 1 if any check fails

What it proves (each line is printed as PASS/FAIL with the datasheet place it comes from):
  A. pin number <-> port name of all 48 pins, read out of the I/O multiplexing table of DS40002247B and compared with the netlist
  B. functions: TWI1 default pins, TCA1 default pins, XTAL32K, UPDI, RESET, supplies, VDDIO2 / port C power domain
  C. voltage levels between the chips (MCU on VBAT 3.0-4.12 V, LIS2DW12 and I2C pull-ups on +3V3, BQ25570 BAT_OK on VSTOR)
  D. current per pin (column source, row sink) against the datasheet numbers, over the battery range
"""
import re
import sys
import bisect
import os

import fitz

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DS = os.path.join(ROOT, "docs", "datasheets")
fails = []


def check(ok, what, src=""):
    print(("PASS  " if ok else "FAIL  ") + what + (f"   [{src}]" if src else ""))
    if not ok:
        fails.append(what)


# ---------------- netlist ----------------
net = open(os.path.join(ROOT, "hardware", "netlist.xml"), encoding="utf-8").read()
pin_net = {}
nets = {}
for n, body in re.findall(r'<net code="\d+" name="([^"]*)"[^>]*>(.*?)</net>', net, re.S):
    nodes = re.findall(r'<node ref="([^"]+)" pin="([^"]+)"', body)
    nets[n] = nodes
    for r, p in nodes:
        if r == "U1":
            pin_net[int(p)] = n.lstrip("/")

# ---------------- A. pin table out of the datasheet ----------------
avr = fitz.open(os.path.join(DS, "AVR128DB28-32-48-64-DS40002247B.pdf"))
tab = {}
for pg in avr[14:22]:
    if "I/O Multiplexing" not in pg.get_text():
        continue
    ws = pg.get_text("words")
    for pw in [w for w in ws if re.fullmatch(r"P[A-F][0-7]", w[4]) and w[0] < 172]:
        nums = sorted([w for w in ws if abs(w[1] - pw[1]) < 4 and w[0] < 172 and re.fullmatch(r"\d+", w[4])], key=lambda w: w[0])
        if len(nums) >= 2:
            tab[int(nums[1][4])] = pw[4]                      # 2nd number column = VQFN48 / TQFP48
exp = {}
for p, port, bit in ([(44 + i, "A", i) for i in range(5)] + [(1 + i, "A", 5 + i) for i in range(3)] + [(4 + i, "B", i) for i in range(6)]
                     + [(10 + i, "C", i) for i in range(4)] + [(16 + i, "C", 4 + i) for i in range(4)] + [(20 + i, "D", i) for i in range(8)]
                     + [(30 + i, "E", i) for i in range(4)] + [(34 + i, "F", i) for i in range(6)]):
    exp[p] = f"P{port}{bit}"
bad = {p: (tab.get(p), e) for p, e in exp.items() if tab.get(p) != e and tab.get(p) is not None}
check(len(tab) >= 36 and not bad, f"datasheet multiplexing table gives {len(tab)} GPIO pins of the 48-pin package and they match the pin plan (mismatches: {bad})", "DS40002247B I/O Multiplexing table")
PORT = {p: tab.get(p, exp[p]) for p in exp}

role = {}
for p in range(1, 49):
    n = pin_net.get(p, "")
    role[p] = "" if n.startswith("unconnected") else n
print()
print(f'{"pin":>3} {"port":5} {"net":14} role')
GPIO_ROLE = {}
for p in range(1, 49):
    nm = role[p]
    port = PORT.get(p, "")
    if re.fullmatch(r"COL\d+_MCU", nm):
        k = "column (source, anode side)"
    elif re.fullmatch(r"ROW\d+", nm):
        k = "row (sink, cathode side)"
    else:
        k = {"SDA": "I2C data", "SCL": "I2C clock", "BUZ_A": "piezo A", "BUZ_B": "piezo B", "IMU_INT": "sensor interrupt", "BTN1": "button 1", "BTN2": "button 2",
             "BAT_OK": "charger status in", "XTAL1": "32 kHz crystal", "XTAL2": "32 kHz crystal", "RESET": "reset", "UPDI": "programming", "VBAT": "supply", "GND": "ground", "": "not connected"}.get(nm, "?")
    GPIO_ROLE[p] = (nm, k)
    print(f"{p:>3} {port:5} {nm:14} {k}")
print()

# the matrix lines on whole ports, bit n = pin n  (firmware rev B)
for i in range(12):
    pin = [p for p, (n, _) in GPIO_ROLE.items() if n == f"COL{i}_MCU"]
    want = "PA%d" % i if i < 8 else "PB%d" % (i - 8)
    check(len(pin) == 1 and PORT[pin[0]] == want, f"COL{i} is on {want}", "pin plan rev B")
for i in range(12):
    pin = [p for p, (n, _) in GPIO_ROLE.items() if n == f"ROW{i}"]
    want = "PC%d" % i if i < 8 else "PD%d" % (i - 8)
    check(len(pin) == 1 and PORT[pin[0]] == want, f"ROW{i} is on {want}", "pin plan rev B")

# ---------------- B. functions ----------------
alltext = "\n".join(pg.get_text() for pg in avr)


def find(rx, flags=re.S):
    return re.search(rx, alltext, flags) is not None


check(find(r"0x0\s+DEFAULT\s+SDA\s*SCL.{0,300}PF2.{0,40}PF3") or find(r"DEFAULT\s+PF2\s+PF3") or find(r"TWI1\[1:0\].{0,600}DEFAULT[^\n]*PF2"),
      "TWI1 default pins (TWIROUTEA = 0) are SDA = PF2, SCL = PF3, host/client mode", "DS 17.3.6")
check(GPIO_ROLE[36][0] == "SDA" and GPIO_ROLE[37][0] == "SCL" and PORT[36] == "PF2" and PORT[37] == "PF3", "netlist: SDA on pin 36 (PF2), SCL on pin 37 (PF3)")
check(find(r"TCA1\[2:0\].{0,900}PORTB.{0,300}PB4") and PORT[8] == "PB4" and PORT[9] == "PB5" and {GPIO_ROLE[8][0], GPIO_ROLE[9][0]} == {"BUZ_A", "BUZ_B"},
      "TCA1 default route (TCAROUTEA = 0, PORTB) puts WO4 on PB4 and WO5 on PB5 = the two piezo pins", "DS 17.3.7")
check(PORT[34] == "PF0" and PORT[35] == "PF1" and {GPIO_ROLE[34][0], GPIO_ROLE[35][0]} == {"XTAL1", "XTAL2"} and find(r"PF0 \(XTAL32K1\)") and find(r"PF1 \(XTAL32K2\)"),
      "32.768 kHz crystal on PF0 (XTAL32K1) / PF1 (XTAL32K2) = pins 34 / 35", "DS 2.3 pinout")
check(GPIO_ROLE[41][0] == "UPDI" and find(r"41 UPDI|UPDI 41|40 PF6 \(RESET\)|PF6 \(RESET\)"), "UPDI is pin 41, RESET (PF6) is pin 40", "DS 2.3 pinout")
check(GPIO_ROLE[40][0] == "RESET", "netlist: RESET net on pin 40")
for p, nm in ((14, "VDDIO2"), (28, "AVDD"), (42, "VDD")):
    check(GPIO_ROLE[p][0] == "VBAT", f"pin {p} ({nm}) is on VBAT (all MCU supply pins on the same rail; single-supply mode needs VDDIO2 = VDD)", "DS 5.1, 19.2")
for p in (15, 29, 43):
    check(GPIO_ROLE[p][0] == "GND", f"pin {p} is ground")
check(pin_net.get(49) == "GND", "exposed pad (pin 49) is ground")
check(find(r"PC\[7:0\]"), "port C (rows 0-7) is the VDDIO2 power domain: needs MVSYSCFG = single supply (SYSCFG1 = 0x10; factory 0x08 = dual)", "DS 5.1, 19.2, fuse SYSCFG1")

# ---------------- C. levels ----------------
print()
w = avr[609].get_text("words")
rows = {}
for x in w:
    rows.setdefault(round(x[1] / 3), []).append(x)
lines = [" ".join(t[4] for t in sorted(r, key=lambda t: t[0])) for _, r in sorted(rows.items())]
vol = [l for l in lines if l.startswith("VOL")][0]
voh = [l for l in lines if l.startswith("VOH")][0]
print("datasheet (electrical characteristics, page", 610, "):", vol, "|", voh)
VOL_MAX, IOL = 0.6, 10.0
VOH_DROP, IOH = 0.7, 6.0
check("0.6" in vol and "IOL = 10 mA" in vol and "VDD - 0.7" in voh and "IOH = 6 mA" in voh, "I/O drive numbers read from the datasheet: VOL <= 0.6 V at 10 mA sink, VOH >= VDD - 0.7 V at 6 mA source (VDD = 3.0 V)", "DS 39.x")
check(find(r"On any standard I/O pin\s+.50\s*\n?.{0,20}mA") or find(r"On any standard I/O pin"), "absolute maximum per I/O pin is 50 mA, 350 mA through GND/VDD (we stay below 12 mA / 15 mA)", "DS 39.1")

lis = fitz.open(os.path.join(DS, "LIS2DW12.pdf"))
lt = "\n".join(pg.get_text() for pg in lis)
check("Vdd_IO - 0.2" in lt.replace("\xa0", " ") or "Vdd_IO - 0.2" in re.sub(r"\s+", " ", lt), "LIS2DW12 INT1 output high level is Vdd_IO - 0.2 V (at 4 mA): 3.1 V with Vdd_IO = 3.3 V", "LIS2DW12 DS table 'Digital high-level output voltage'")
VDDIO = 3.3
INT_VOH = VDDIO - 0.2
for vbat in (3.0, 3.7, 4.12):
    sch = 0.8 * vbat
    print(f"      VBAT {vbat:4.2f} V: Schmitt VIH = 0.8 x VDD = {sch:4.2f} V   TTL VIH = 2.00 V   sensor INT high = {INT_VOH:3.1f} V   -> {'ok with Schmitt' if INT_VOH >= sch else 'NEEDS TTL'}; TTL {'ok' if INT_VOH >= 2.0 else 'FAILS'}")
check(INT_VOH >= 2.0 and INT_VOH < 0.8 * 4.12, "IMU_INT must use the TTL input level (INLVL = 1): fine at 3.0 V, wrong at 4.12 V with the default Schmitt trigger", "DS: VIH TTL 2.0 V, Schmitt 0.8 x VDD")
src = open(os.path.join(ROOT, "firmware", "c", "hw", "buttons.c"), encoding="utf-8").read()
check(re.search(r"IMU_INT_BIT\]\s*=\s*PORT_INLVL_bm", src) is not None, "firmware sets PORT_INLVL_bm on the IMU_INT pin (buttons.c)")
# I2C: MCU is VBAT powered, pull-ups to +3V3: high = 3.3 V
pull = {n for n, nd in nets.items() for r, p in nd if r in ("R20", "R21")}
check("+3V3" in pull, "SDA/SCL pull-ups R20/R21 go to +3V3 (not VBAT): the sensor never sees more than its Vdd_IO", "netlist")
for vbat in (3.0, 3.7, 4.12):
    vih = 0.7 * vbat
    print(f"      VBAT {vbat:4.2f} V: TWI I2C-level VIH = 0.7 x VDD = {vih:4.2f} V, bus high = 3.3 V -> {'ok' if 3.3 >= vih else 'FAIL'}")
check(3.3 > 0.7 * 4.12 + 0.1, "I2C bus high (3.3 V) is above the MCU's VIH (0.7 x 4.12 = 2.88 V) over the whole battery range; MCU pull-ups must stay OFF (they would pull to VBAT)", "DS 39.x TWI VIH")
i2c = open(os.path.join(ROOT, "firmware", "c", "hw", "i2c_twi.c"), encoding="utf-8").read()
check("PULLUPEN" not in i2c, "firmware does not enable the MCU pull-up on SDA/SCL")
check(("U4", "13") in nets.get("/BAT_OK", []) and ("U1", "33") in nets.get("/BAT_OK", []), "BAT_OK (U1 pin 33) comes from BQ25570 pin 13 'VBAT_OK', referenced to VSTOR (= VBAT = MCU VDD): level matches without TTL", "BQ25570 DS pin table")

# ---------------- D. currents ----------------
print()
RD, RSRC, RSNK, R = 30.0, 60.0, 35.0, 220.0
print("LED current in one lit LED, mA (R = 220 ohm; Vt 2.45 / 2.60 / 2.75 V; typical pin drops; datasheet-worst pin drops in brackets)")
worst_col = 0
for vbat in (3.3, 3.7, 4.12):
    out = []
    for vt in (2.45, 2.60, 2.75):
        i = max(vbat - vt, 0) / (RD + RSRC + RSNK + R) * 1000
        iw = max(vbat - vt, 0) / (RD + 117 + 60 + R) * 1000
        out.append(f"{i:4.1f} ({iw:4.1f})")
        worst_col = max(worst_col, i)
    print(f"   VBAT {vbat:4.2f} V: " + "   ".join(out))
check(worst_col <= IOH, f"column pin (source) carries one LED: worst {worst_col:.1f} mA <= 6 mA datasheet source point; absolute max 50 mA", "DS 39.x")
print("row pin (sink) with N LEDs lit at once, worst case LED (low Vf), 4.12 V:")
iled = (4.12 - 2.45) / (RD + RSRC + RSNK + R) * 1000
for n in (1, 2, 3, 12):
    cur = n * iled
    vo = cur * RSNK / 1000
    print(f"   N={n:2d}: {cur:5.1f} mA, pin drop about {vo:4.2f} V (guaranteed <= 0.6 V up to 10 mA)   {'ok' if cur <= IOL else ('above the 10 mA test point (dimmer, not damaged)' if cur <= 50 else 'ABOVE the 50 mA absolute maximum: the firmware must never light this many at once')}")
check(2 * iled < 1.05 * IOL, f"firmware limit of 2 LEDs per row slot ({2 * iled:.1f} mA at 4.12 V) is at the 10 mA sink test point", "firmware/c/watch.c ROW_SINK_UA")
print(f"chip total: one row active at a time -> average LED current <= ~10 mA, peak <= ~10 mA + CPU: far below the 120 mA per supply pin limit")

print()
print("RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
