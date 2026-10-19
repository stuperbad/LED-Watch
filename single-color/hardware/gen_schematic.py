"""
Parametric schematic generator for the single-colour LED watch.

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_schematic.py --variant usb
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_schematic.py --variant solar

Writes 'LED Watch - Single Color.kicad_sch' (solar variant; the old pad-charged variant writes '... _usb.kicad_sch') next to this script. Everything is derived from the CONFIG
block and the pin-assignment tables, so changing LED sizes, resistor values or the MCU pin map is a re-run.

Design (see ../README.md and ../docs/):
  * 132 white LEDs = 12 sectors (columns) x 11 slots (rows): per 30-degree sector, slot 0 = the HOUR LED,
    slots 1-5 = five MINUTE LEDs, slots 6-10 = five SECOND LEDs.
  * Anode of every LED goes to its COLUMN net (through one series resistor per column, MCU pin SOURCES), cathode to its ROW net (MCU pin SINKS).
  * Time display lights ~3 LEDs at once, so the MCU drives the matrix directly (the game mode may need row drivers - see ../docs/mcu-pinmaps.md).
"""
import argparse, math, os, re, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symlib

# ------------------------------------------------------------------ CONFIG
CONFIG = dict(
    led_fp={"H": "LED_SMD:LED_0603_1608Metric", "M": "LED_SMD:LED_0402_1005Metric", "S": "LED_SMD:LED_0201_0603Metric", "I": "LED_SMD:LED_0402_1005Metric"},
    led_value={"H": "LED white 0603", "M": "LED white 0402", "S": "LED white 0201", "I": "LED white 0402 (indicator)"},
    r_col="220",            # series resistor per column [ohm]: led_resistor.py (worst case <= 5 mA at 4.12 V with a low-Vf LED; 1.6-4 mA from 3.3 V to 4.12 V). Drop-in value change, no net change
    r_fp="Resistor_SMD:R_0402_1005Metric",
    c_fp="Capacitor_SMD:C_0402_1005Metric",
    cells=1,                # 1 = single KXOB25-05X3TF (default), 2 = two KXOB25-07X1TF in series (SC_MID)
    c_xtal="18p",           # crystal load caps: DS40002247B Table 39-10: XTAL pin parasitic C = 5 pF/pin, max crystal CL 18 pF; CL(12.5 pF crystal) = (C+5)/2 + ~1 pF stray -> C = 18 pF (C0G). Verify on the bench (AN2648)
    r_prog="10k",           # MCP73831 PROG: 1000/10k = 100 mA charge current (suits a ~100 mAh cell)
)
# MCU pin assignment (AVR128DB48, TQFP-48). Names must match the KiCad symbol's pin names.
# COL pins SOURCE one LED at a time (6 mA/pin spec); ROW pins SINK up to 12 LEDs (10 mA/pin spec) - see ../docs/mcu-pinmaps.md.
COL_PINS = ["PA0", "PA1", "PA4", "PA5", "PA6", "PA7", "PB0", "PB1", "PB2", "PB3", "PC0", "PC1"]   # 12 columns (sources)
ROW_PINS = ["PC2", "PC3", "PC4", "PC5", "PC6", "PC7", "PD0", "PD1", "PD2", "PD3", "PD4", "PD5"]    # 12 rows (sinks); row 11 = the six mode-indicator LEDs
EXTRA_PINS = {"PA2": "SDA", "PA3": "SCL", "PE0": "IMU_INT", "PE1": "BTN1", "PE2": "BTN2", "PE3": "CHG_STAT",
              "XTAL32K1/PF0": "XTAL1", "XTAL32K2/PF1": "XTAL2", "UPDI": "UPDI",
              "PB4": "BUZ_A", "PB5": "BUZ_B",      # piezo BZ1, driven in antiphase from TCA1 WO4/WO5 (split mode), see firmware/HANDOFF.md
              "PF6": "RESET"}                      # RESET (PF6) to pogo pad 1: high-voltage / reset recovery

REVISION = "A"                        # board / schematic revision, see REVISIONS.md
PROJECT = "LED Watch - Single Color"                 # = the KiCad project name (led-watch.kicad_pro): the symbol instances refer to it
ROOT_UUID = str(uuid.uuid4())


def U():
    return str(uuid.uuid4())


def f(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


class Sch:
    def __init__(self, title):
        self.title = title
        self.libs = {}      # "Lib:Name" -> symbol text
        self.items = []
        self.pwr = 0
        self.refs = {}

    # ---- library handling
    def lib(self, lib, name):
        key = f"{lib}:{name}"
        if key not in self.libs:
            txt = symlib.flat_symbol_text(lib, name)
            txt = txt.replace(f'(symbol "{name}"', f'(symbol "{key}"', 1)
            self.libs[key] = txt
        return key

    # ---- primitives
    def wire(self, a, b):
        self.items.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    def junction(self, p):
        self.items.append(f'\t(junction\n\t\t(at {f(p[0])} {f(p[1])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')

    def noconnect(self, p):
        self.items.append(f'\t(no_connect\n\t\t(at {f(p[0])} {f(p[1])})\n\t\t(uuid "{U()}")\n\t)')

    def label(self, text, p, ang=0):
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append(f'\t(label "{text}"\n\t\t(at {f(p[0])} {f(p[1])} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    def text(self, s, p, size=2.0):
        self.items.append(f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(p[0])} {f(p[1])} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    # ---- symbols
    def place(self, libname, name, ref, value, fp, x, y, rot=0, show_ref=True, show_val=True, extra=None, desc=""):
        x, y = round(x / 2.54) * 2.54, round(y / 2.54) * 2.54
        key = self.lib(libname, name)
        pins = symlib.pins(libname, name)
        inst = dict(key=key, ref=ref, x=x, y=y, rot=rot, pins={p["number"]: p for p in pins}, byname={p["name"]: p for p in pins})
        hide = "\n\t\t\t\t(hide yes)" if False else ""

        def prop(k, v, dx, dy, hide):
            h = "\n\t\t\t\t(hide yes)" if hide else ""
            return (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {f(x + dx)} {f(y + dy)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){h}\n\t\t\t)\n\t\t)')
        props = [prop("Reference", ref, 2.54, -2.54, not show_ref), prop("Value", value, 2.54, 0, not show_val),
                 prop("Footprint", fp, 0, 0, True), prop("Datasheet", (extra or {}).get("Datasheet", "~"), 0, 0, True),
                 prop("Description", desc, 0, 0, True)]
        for k, v in (extra or {}).items():
            if k != "Datasheet":
                props.append(prop(k, v, 0, 0, True))
        pinblk = "".join(f'\n\t\t(pin "{n}"\n\t\t\t(uuid "{U()}")\n\t\t)' for n in inst["pins"])
        pwr = ref.startswith("#")
        self.items.append(
            f'\t(symbol\n\t\t(lib_id "{key}")\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom {"no" if pwr else "yes"})\n\t\t(on_board {"no" if pwr else "yes"})\n\t\t(dnp no)\n\t\t(uuid "{U()}")\n'
            + "\n".join(props) + pinblk +
            f'\n\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        return inst

    @staticmethod
    def pin_end(inst, which):
        p = inst["pins"].get(which) or inst["byname"][which]
        th = math.radians(inst["rot"])
        rx = p["x"] * math.cos(th) - p["y"] * math.sin(th)
        ry = p["x"] * math.sin(th) + p["y"] * math.cos(th)
        out = (p["angle"] + 180 + inst["rot"]) % 360          # direction pointing away from the body
        return (round(inst["x"] + rx, 4), round(inst["y"] - ry, 4)), int(round(out)) % 360

    def net(self, inst, which, netname):
        (pt, out) = self.pin_end(inst, which)
        self.label(netname, pt, out)
        return pt

    def nc(self, inst, which):
        (pt, out) = self.pin_end(inst, which)
        self.noconnect(pt)

    def power(self, kind, value, pt, up=True):
        """power symbol whose single pin sits exactly on pt"""
        lib, name = ("power", kind)
        self.pwr += 1
        ref = f"#PWR{self.pwr:03d}"
        key = self.lib(lib, name)
        p = symlib.pins(lib, name)[0]
        inst = dict(key=key, ref=ref, x=pt[0], y=pt[1], rot=0, pins={"1": p}, byname={})
        txt = (f'\t(symbol\n\t\t(lib_id "{key}")\n\t\t(at {f(pt[0])} {f(pt[1])} 0)\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(dnp no)\n\t\t(uuid "{U()}")\n'
               f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {f(pt[0])} {f(pt[1] + (-3.81 if up else 3.81))} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Value" "{value}"\n\t\t\t(at {f(pt[0])} {f(pt[1] + (-3.81 if up else 3.81))} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Footprint" ""\n\t\t\t(at 0 0 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(pin "1"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
               f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.items.append(txt)

    def flag(self, pt):
        self.power("PWR_FLAG", "PWR_FLAG", pt, up=True)

    def gnd(self, pt):
        self.power("GND", "GND", pt, up=False)

    def vbat(self, pt):
        self.power("+BATT", "VBAT", pt)

    def v33(self, pt):
        self.power("+3V3", "+3V3", pt)

    def vbus(self, pt):
        self.power("VBUS", "VBUS", pt)

    # ---- output
    def write(self, path, paper="A0"):
        libs = "\n".join("\t\t" + l.replace("\n", "\n\t\t") for l in self.libs.values())
        body = "\n".join(self.items)
        txt = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n\t(uuid "{ROOT_UUID}")\n\t(paper "{paper}")\n\t(title_block\n\t\t(title "{self.title}")\n\t\t(rev "{REVISION}")\n\t\t(company "generated by gen_schematic.py")\n\t)\n\t(lib_symbols\n{libs}\n\t)\n'
               f'{body}\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')
        open(path, "w", encoding="utf8").write(txt)


# ------------------------------------------------------------------ design
def build(variant):
    s = Sch(f"LED watch single colour - {variant} variant")
    cfg = CONFIG
    # ============ LED matrix =============
    X0, Y0, DX, DY = 50.8, 63.5, 22.86, 15.24
    cols, rows = 12, 12
    IND_LABELS = ['SET', 'TMR', 'BAT', 'FUN', 'CFG', 'LCK', 'ALM']   # by column COL0..COL6 (= IND1..IND7); on the face ALM (COL6) sits between TMR and BAT, so left to right: SET TMR ALM BAT FUN CFG LCK = the weekday lights S M T W T F S
    row_taps = {r: [] for r in range(rows)}
    col_taps = {c: [] for c in range(cols)}
    for c in range(cols):
        for r in range(rows):
            x, y = X0 + c * DX, Y0 + r * DY
            if r == 11 and c >= len(IND_LABELS):
                continue
            if r == 11:
                kind, ref, idx = "I", f"IND{c + 1}", c
            elif r == 0:
                kind, ref, idx = "H", f"H{c if c else 12}", c
            elif r <= 5:
                kind, idx = "M", c * 5 + (r - 1)
                ref = f"M{idx}"
            else:
                kind, idx = "S", c * 5 + (r - 6)
                ref = f"S{idx}"
            # rotated 180 deg: anode (pin 2) on the left -> sector bus COLn (MCU SOURCES, through the series resistor, one LED at a time);
            # cathode (pin 1) on the right -> slot bus ROWn (MCU SINKS up to 12 LEDs). The AVR128DB sinks 10 mA/pin but only sources 6 mA/pin (DS40002247B, table 39-6).
            inst = s.place("Device", "LED", ref, (IND_LABELS[idx] if kind == "I" else cfg["led_value"][kind]), cfg["led_fp"][kind], x, y, 180, show_ref=False, show_val=False,
                           extra={"Sim.Pins": "1=K 2=A"}, desc=(f"mode indicator {IND_LABELS[c]}" if r == 11 else f"white LED, sector {c}, slot {r}"))
            k_pt, a_pt = s.pin_end(inst, "1")[0], s.pin_end(inst, "2")[0]
            row_taps[r].append(k_pt)
            col_taps[c].append(a_pt)
    # row buses: horizontal wire 5.08 above each LED row, anode taps go up to it
    for r in range(rows):
        taps = row_taps[r]
        ybus = taps[0][1] - 5.08
        for (ax, ay) in taps:
            s.wire((ax, ay), (ax, ybus))
            s.junction((ax, ybus))
        s.wire((taps[0][0], ybus), (taps[-1][0] + 6.35, ybus))
        s.label(f"ROW{r}", (taps[-1][0] + 6.35, ybus), 0)
    # column buses: vertical wire 6.35 left of each LED column, cathode taps go left to it
    for c in range(cols):
        taps = col_taps[c]
        xbus = taps[0][0] - 6.35
        for (kx, ky) in taps:
            s.wire((kx, ky), (xbus, ky))
            s.junction((xbus, ky))
        ytop, ybot = taps[0][1], taps[-1][1] + 7.62
        s.wire((xbus, ytop), (xbus, ybot))
        s.label(f"COL{c}", (xbus, ybot), 270)
    s.text("LED MATRIX: 12 columns (sectors) x 11 rows (slot 0 = hour, 1-5 = minutes, 6-10 = seconds). Anodes -> COLn (sources), cathodes -> ROWn (sinks).", (X0 - 10, Y0 - 25), 3)

    # ============ column series resistors =============
    RX, RY = X0, Y0 + rows * DY + 30
    for c in range(cols):
        x = RX + c * DX
        r = s.place("Device", "R", f"R{c + 1}", cfg["r_col"], cfg["r_fp"], x, RY, 0, show_val=True)
        s.net(r, "1", f"COL{c}")
        s.net(r, "2", f"COL{c}_MCU")
    s.text("Series resistor per column: 220 ohm from led_resistor.py (peak LED current 1.6-4.8 mA over 3.3-4.12 V; worst case <= 5 mA). Re-check once the LED parts are chosen", (RX - 10, RY - 10), 2.5)

    # ============ MCU =============
    MX, MY = 520.0, 150.0
    mcu = s.place("MCU_Microchip_AVR_Dx", "AVR128DB48x-x6LX", "U1", "AVR128DB48-I/6LX", "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm", MX, MY, 0,
                  extra={"Datasheet": "https://ww1.microchip.com/downloads/en/DeviceDoc/AVR128DB64-48-32-DataSheet-DS40002247.pdf"},
                  desc="AVR128DB48 8-bit AVR, 128KB flash, VQFN-48 6x6 (6LX). Same pin numbers as the TQFP (datasheet DS40002247B pin table lists 48-pin TQFP/VQFN together). EP: KiCad footprint 4.2 mm, datasheet 4.1 mm - check land pattern")
    names = {p["name"]: p for p in mcu["pins"].values()}

    def pinname(base):
        for n in names:
            if n == base or n.split("/")[-1] == base or n.split("/")[0] == base:
                return n
        raise KeyError(base)
    used = set()
    for c, pn in enumerate(COL_PINS):
        n = pinname(pn); s.net(mcu, n, f"COL{c}_MCU"); used.add(n)
    for r, pn in enumerate(ROW_PINS):
        n = pinname(pn); s.net(mcu, n, f"ROW{r}"); used.add(n)
    extra = dict(EXTRA_PINS)
    extra["PE3"] = "CHG_STAT" if variant == "usb" else "BAT_OK"
    for pn, net in extra.items():
        n = pinname(pn); s.net(mcu, n, net); used.add(n)
    for p in mcu["pins"].values():
        if p["name"] in used:
            continue
        if p["type"] == "power_in" or p["name"] in ("GND",):
            continue
        s.nc(mcu, p["number"])
    # power pins
    for n in ("VDD", "VDDIO2", "AVDD"):
        pt, _ = s.pin_end(mcu, n)
        s.vbat(pt)
    for num in ("15", "29", "43"):
        pt, _ = s.pin_end(mcu, num)
        s.gnd(pt)
    # decoupling next to MCU
    dx = MX - 60
    for i, label in enumerate(("VDD", "VDDIO2", "AVDD")):
        c = s.place("Device", "C", f"C{10 + i}", "100n", cfg["c_fp"], dx + i * 12.7, MY + 60, 0)
        s.net(c, "1", "VBAT"); s.gnd(s.pin_end(c, "2")[0])
    cb = s.place("Device", "C", "C13", "10u", cfg["c_fp"], dx + 3 * 12.7, MY + 60, 0)
    s.net(cb, "1", "VBAT"); s.gnd(s.pin_end(cb, "2")[0])
    s.text("MCU decoupling (100 nF per supply pin + 10 uF bulk on VBAT)", (dx - 5, MY + 48), 2)

    # ============ 32 kHz crystal =============
    CX, CY = 380.0, 20.0
    y1 = s.place("Device", "Crystal", "Y1", "32.768kHz", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", CX, CY, 0,
                 extra={"MPN": "ABS07-32.768KHZ-T"}, desc="12.5 pF load")
    s.net(y1, "1", "XTAL1"); s.net(y1, "2", "XTAL2")
    for i, net in enumerate(("XTAL1", "XTAL2")):
        c = s.place("Device", "C", f"C{20 + i}", cfg["c_xtal"], cfg["c_fp"], CX - 7.62 + i * 15.24, CY + 20, 0)
        s.net(c, "1", net); s.gnd(s.pin_end(c, "2")[0])
    s.text("32.768 kHz crystal on PF0/PF1 (XTAL32K1/2). Load caps are a placeholder: confirm with the datasheet/EE.", (CX - 20, CY - 10), 2)

    # ============ accelerometer + 3V3 LDO =============
    IX, IY = 400.0, 90.0
    u2 = s.place("Local", "LIS2DW12", "U2", "LIS2DW12TR", "Package_LGA:LGA-12_2x2mm_P0.5mm", IX, IY, 0,
                 extra={"Datasheet": "https://www.st.com/resource/en/datasheet/lis2dw12.pdf", "MPN": "LIS2DW12TR"},
                 desc="ST LIS2DW12 accelerometer (DS11811 rev 9): 50 nA power-down, 1.62-3.6 V, I2C addr 0x18 with SDO/SA0 = GND")
    for p, tgt in (("VDD", "v33"), ("VDD_IO", "v33"), ("~{CS}", "v33"), ("SDO/SA0", "gnd"), ("RES", "gnd"), ("NC", "gnd")):
        pt, _ = s.pin_end(u2, p)
        (s.v33 if tgt == "v33" else s.gnd)(pt)
    for num in ("6", "8"):
        s.gnd(s.pin_end(u2, num)[0])
    s.net(u2, "SCL/SPC", "SCL"); s.net(u2, "SDA/SDI/SDO", "SDA"); s.net(u2, "INT1", "IMU_INT")
    s.nc(u2, "INT2")
    for i, net in enumerate(("SDA", "SCL")):
        r = s.place("Device", "R", f"R{20 + i}", "10k", cfg["r_fp"], IX - 40 + i * 10.16, IY + 5, 0)
        s.net(r, "2", net); s.v33(s.pin_end(r, "1")[0])
    DUMMIES = [57, 58, 59, 61, 62, 63, 64, 65, 66, 67]      # cosmetic dummies (same 10k 0402 as R20/R21 = no new BOM line; pins not connected): keep the hour-LED flanks and the compass-rose pairs symmetric
    for i, n in enumerate(DUMMIES):
        r = s.place("Device", "R", f"R{n}", "10k", cfg["r_fp"], IX - 40 + (i % 5) * 10.16, IY + 18 + (i // 5) * 12.7, 0, desc="COSMETIC DUMMY: not connected, keeps the layout symmetric around the 3 / 6 / 9 / 12 o'clock parts")
        s.nc(r, "1"); s.nc(r, "2")
    for i in range(2):
        c = s.place("Device", "C", f"C{30 + i}", "100n", cfg["c_fp"], IX + 25 + i * 10.16, IY + 5, 0)
        s.v33(s.pin_end(c, "1")[0]); s.gnd(s.pin_end(c, "2")[0])
    if variant == "usb":
        ldo = s.place("Regulator_Linear", "MCP1700x-330xxTT", "U3", "MCP1700-3302E/TT", "Package_TO_SOT_SMD:SOT-23", IX - 40, IY - 35, 0,
                      desc="3.3 V LDO, 1.6 uA Iq: the LIS2DW12 is limited to 3.6 V but the LiPo reaches 4.2 V")
        s.vbat(s.pin_end(ldo, "VI")[0]); s.v33(s.pin_end(ldo, "VO")[0]); s.gnd(s.pin_end(ldo, "GND")[0])
        for i, (net, fn) in enumerate((("vbat", "in"), ("v33", "out"))):
            c = s.place("Device", "C", f"C{35 + i}", "1u", cfg["c_fp"], IX - 62 + i * 52, IY - 35 + 14, 0)
            (s.vbat if net == "vbat" else s.v33)(s.pin_end(c, "1")[0]); s.gnd(s.pin_end(c, "2")[0])
    s.text("LIS2DW12 accelerometer on I2C (SDA=PA2, SCL=PA3) from the 3.3 V rail. CS high = I2C mode; SDO/SA0 low = address 0x18; pin 7 RES to GND (DS11811 Table 1). "
           "FIRMWARE: set PINnCTRL.INLVL=TTL on IMU_INT's pin (the sensor's high is only ~3.1 V and the MCU runs at up to 4.2 V).", (IX - 62, IY - 50), 2)

    # ============ buttons =============
    for i, net in enumerate(("BTN1", "BTN2")):
        sw = s.place("Switch", "SW_Push", f"SW{i + 1}", "SW_Push", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2", 380 + i * 30, 135, 0)
        s.net(sw, "1", net); s.gnd(s.pin_end(sw, "2")[0])
    s.text("Buttons: internal MCU pull-ups, active low", (370, 125), 2)

    # ============ programming pads =============
    # 4 spring-contact (pogo) pads at 1.27 mm on the back, in the Microchip UPDI v2 order: 1 RESET (PF6), 2 VDD (VBAT), 3 GND, 4 UPDI; plus two unplated-net guide holes (unnumbered pads in the footprint).
    # Only UPDI / VDD / GND are needed to program (e.g. Adafruit UPDI Friend 5893); RESET is for high-voltage / reset recovery.
    j2 = s.place("Connector_Generic", "Conn_01x04", "J2", "UPDI pogo pads 1.27 mm (RESET VDD GND UPDI)", "LEDWatch:UPDI_Pogo_1x4_P1.27mm_2Guide", 380, 165, 0,
                 desc="programming pads, not a part: spring pins on the programmer jig touch them")
    s.net(j2, "1", "RESET"); s.vbat(s.pin_end(j2, "2")[0]); s.gnd(s.pin_end(j2, "3")[0]); s.net(j2, "4", "UPDI")
    s.text("UPDI programming pads (1.27 mm pogo row, back side): 1 RESET, 2 VBAT, 3 GND, 4 UPDI", (370, 155), 2)

    # ============ battery connector =============
    j1 = s.place("Connector_Generic", "Conn_01x02", "J1", "LiPo", "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", 380, 195, 0)
    if variant == "usb":
        s.vbat(s.pin_end(j1, "1")[0])
    else:
        s.net(j1, "1", "BATT")             # solar variant: the cell sits on the harvester's VBAT pin, the system rail is VSTOR
    s.gnd(s.pin_end(j1, "2")[0])
    s.flag(s.pin_end(j1, "2")[0])
    s.text("LiPo (protected cell). Pin 1 = +, pin 2 = - : CHECK the cell's lead polarity against the JST pin order", (370, 185), 2)
    # second battery plug in parallel (two small pouches near the strap ends; board has J1 and J1B)
    j1b = s.place("Connector_Generic", "Conn_01x02", "J1B", "LiPo", "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", 410, 195, 0)
    if variant == "usb":
        s.vbat(s.pin_end(j1b, "1")[0])
    else:
        s.net(j1b, "1", "BATT")
    s.gnd(s.pin_end(j1b, "2")[0])
    s.text("Second pouch in parallel (J1B): same polarity rule as J1", (400, 185), 2)
    # ============ piezo buzzer =============
    bz = s.place("Device", "Buzzer", "BZ1", "PKMCS0909E4000-R1", "LEDWatch:Piezo_Murata_PKMCS0909E4000-R1_9x9mm", 450, 195, 0,
                 extra={"Datasheet": "https://www.murata.com/products/productdata/8796834160670/PKMCS0909E4000-R1.pdf", "MPN": "PKMCS0909E4000-R1", "LCSC": "C910763"},
                 desc="Murata piezo sounder 9x9x1.9, externally driven, ~4 kHz: BUZ_A / BUZ_B are driven in antiphase (PB4 = WO4, PB5 = WO5 inverted)")
    s.net(bz, "1", "BUZ_A"); s.net(bz, "2", "BUZ_B")
    s.text("Piezo BZ1: PB4 / PB5 drive it in antiphase (TCA1 split mode, PB5 inverted via PORTB.PIN5CTRL.INVEN)", (440, 185), 2)

    # ============ power variant =============
    PX, PY = 390.0, 250.0
    if variant == "usb":
        s.text("VARIANT A: pad/USB-charged LiPo (MCP73831, 4.2 V, 1000/Rprog mA)", (PX - 10, PY - 25), 3)
        ch = s.place("Battery_Management", "MCP73831-2-OT", "U4", "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5", PX + 20, PY, 0)
        s.vbus(s.pin_end(ch, "V_{DD}")[0]); s.gnd(s.pin_end(ch, "V_{SS}")[0]); s.vbat(s.pin_end(ch, "V_{BAT}")[0])
        s.net(ch, "STAT", "CHG_STAT")
        rp = s.place("Device", "R", "R30", cfg["r_prog"], cfg["r_fp"], PX - 15, PY, 0)
        s.net(rp, "1", "PROG"); s.gnd(s.pin_end(rp, "2")[0])
        s.net(ch, "PROG", "PROG")
        for i, kind in enumerate(("vbus", "vbat")):
            c = s.place("Device", "C", f"C{40 + i}", "4u7", cfg["c_fp"], PX + 50 + i * 15, PY, 0)
            (s.vbus if kind == "vbus" else s.vbat)(s.pin_end(c, "1")[0]); s.gnd(s.pin_end(c, "2")[0])
        for i, (net, ref) in enumerate((("VBUS", "TP1"), ("GND", "TP2"))):
            tp = s.place("Connector", "TestPoint", ref, net, "TestPoint:TestPoint_Pad_D2.0mm", PX - 20 + i * 12.7, PY + 30, 0)
            if net == "VBUS":
                s.vbus(s.pin_end(tp, "1")[0]); s.flag(s.pin_end(tp, "1")[0])
            else:
                s.gnd(s.pin_end(tp, "1")[0])
        s.text("Charge pads TP1 (VBUS) / TP2 (GND). Cap values (4.7 uF) per MCP73831 datasheet - verify.", (PX - 25, PY + 20), 2)
    else:
        s.text("VARIANT B: solar harvester + LiPo (TI BQ25570, 80% MPPT, built-in 3.3 V buck)", (PX - 20, PY - 25), 3)
        h = s.place("Battery_Management", "BQ25570", "U4", "BQ25570RGRR", "LEDWatch:BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm", PX + 30, PY + 35, 0,
                    extra={"Datasheet": "https://www.ti.com/lit/ds/symlink/bq25570.pdf"},
                    desc="Ultra-low-power boost charger + nano-power buck; VBIAS 1.21 V")
        for n in ("1", "9", "15", "17", "21"):
            s.gnd(s.pin_end(h, n)[0])
        s.net(h, "VIN_DC", "SOLAR_IN"); s.net(h, "LBOOST", "LBOOST")
        pt, _ = s.pin_end(h, "VOC_SAMP"); s.net(h, "VOC_SAMP", "VBAT")      # VOC_SAMP tied to VSTOR = 80% MPPT (datasheet 7.3.1)
        s.net(h, "VREF_SAMP", "VREF_SAMP")
        s.net(h, "VOUT_EN", "VBAT")           # EN low + VOUT_EN high = fully operating
        s.net(h, "VBAT_OV", "VBAT_OV"); s.net(h, "VRDIV", "VRDIV")
        s.net(h, "OK_HYST", "OK_HYST"); s.net(h, "OK_PROG", "OK_PROG"); s.net(h, "VOUT_SET", "VOUT_SET")
        s.net(h, "VBAT_OK", "BAT_OK"); s.net(h, "VBAT", "BATT"); s.vbat(s.pin_end(h, "VSTOR")[0])
        s.net(h, "LBUCK", "LBUCK"); s.v33(s.pin_end(h, "VOUT")[0])
        # ---- resistor ladders (values from the datasheet's design procedure, VBIAS = 1.21 V, RSUM = 13 MOhm)
        def ladder(name, x, y, parts):
            """vertical divider: parts = [(ref, value, top_net, bottom_net)] stacked top->bottom"""
            for i, (ref, val, top, bot) in enumerate(parts):
                r = s.place("Device", "R", ref, val, "Resistor_SMD:R_0402_1005Metric", x, y + i * 12.7, 0, desc="1% 0402; value from BQ25570 design procedure")
                s.net(r, "1", top); (s.gnd(s.pin_end(r, "2")[0]) if bot == "GND" else s.net(r, "2", bot))
        ladder("OV", PX - 40, PY + 10, [("R50", "6.49M", "VRDIV", "VBAT_OV"), ("R51", "5.11M", "VBAT_OV", "GND")])
        ladder("OK", PX - 20, PY + 10, [("R52", "1.47M", "VRDIV", "OK_HYST"), ("R53", "6.49M", "OK_HYST", "OK_PROG"), ("R54", "3.74M", "OK_PROG", "GND")])
        ladder("OUT", PX, PY + 10, [("R55", "7.32M", "VRDIV", "VOUT_SET"), ("R56", "4.22M", "VOUT_SET", "GND")])
        s.text("Ladders: VBAT_OV=4.12 V (R50/R51), BAT_OK falls 3.31 V / rises 3.78 V (R52-R54), VOUT=3.31 V (R55/R56). Equations: BQ25570 datasheet 7.3.3, 7.3.4, 7.3.6.", (PX - 45, PY - 8), 2)
        # passives
        for ref, val, net_a, net_b, dx2 in (("C50", "4u7", "SOLAR_IN", "GND", 60), ("C51", "10n", "VREF_SAMP", "GND", 72), ("C52", "4u7", "VBAT", "GND", 84),
                                              ("C53", "10n", "VBAT", "GND", 96), ("C54", "22u", "+3V3", "GND", 108)):
            c = s.place("Device", "C", ref, val, "Capacitor_SMD:C_0402_1005Metric" if val != "22u" else "Capacitor_SMD:C_0805_2012Metric", PX + dx2, PY + 20, 0)
            if net_a == "+3V3":
                s.v33(s.pin_end(c, "1")[0])
            else:
                s.net(c, "1", net_a)
            s.gnd(s.pin_end(c, "2")[0])
        l1 = s.place("Device", "L", "L1", "22uH", "Inductor_SMD:L_1210_3225Metric", PX + 60, PY + 40, 0, desc="22 uH, Isat above the BQ25570 boost current limit (see datasheet table)")
        s.net(l1, "1", "LBOOST"); s.net(l1, "2", "SOLAR_IN")
        l2 = s.place("Device", "L", "L2", "10uH", "Inductor_SMD:L_1210_3225Metric", PX + 76, PY + 40, 0, desc="10 uH (datasheet example: Toko DFE252012C), Isat above the buck current limit")
        s.net(l2, "1", "LBUCK"); s.v33(s.pin_end(l2, "2")[0]); s.flag(s.pin_end(l2, "2")[0])      # +3V3 comes from the buck output
        if cfg.get("cells", 1) == 1:
            # ONE solar cell: Anysolar KXOB25-05X3TF (23 x 8 x 1.2 mm, 3 cells in series inside: Voc 2.07 V, Vmpp 1.67 V / 18.4 mA, 30.7 mW at 1 sun; datasheet Rev. Jun. 2026, preliminary).
            # Vmpp/Voc = 0.807 -> VOC_SAMP tied to VSTOR (80 %) is right. Two end pads 2.0 x 7.4 mm on the back; hand solder (Sn42/Bi58, 5 s below 400 C). Board pads SC1+/SC1- are drawn by plan_board.py/write_pcb.py.
            scp = s.place("Connector", "TestPoint", "SC1+", "cell pad", "LEDWatch:KXOB25_cell_pad_2.5x7.4mm", PX + 100, PY + 40, 0,
                          desc="KXOB25-05X3TF + end pad (SOLAR_IN). Not a part: just the 2.5 x 7.4 mm board pad under the cell. VERIFY polarity of the physical cell (Voc) before soldering")
            scm = s.place("Connector", "TestPoint", "SC1-", "cell pad", "LEDWatch:KXOB25_cell_pad_2.5x7.4mm", PX + 100, PY + 60, 0,
                          desc="KXOB25-05X3TF - end pad (GND). Not a part: just the board pad under the cell")
            s.net(scp, "1", "SOLAR_IN"); s.gnd(s.pin_end(scm, "1")[0])
            s.text("One KXOB25-05X3TF (3 cells in series inside): Voc 2.07 V clears the BQ25570 cold-start minimum of 0.6 V (typ; 0.7 V max) even in dim light", (PX + 80, PY + 28), 2)
            s.flag(s.pin_end(scp, "1")[0]); s.flag(s.pin_end(j1, "1")[0])
        else:
            # two solar cells in series (KXOB25-07X1TF, 11.35 x 8 mm): GND -> cell 2 -> SC_MID -> cell 1 -> SOLAR_IN. The contact pads (SC1+/SC1-/SC2+/SC2-, 1.5 mm pads under each cell) are drawn by plan_board.py/write_pcb.py
            j3 = s.place("Connector_Generic", "Conn_01x02", "J3", "Solar cell 1", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", PX + 100, PY + 40, 0,
                         desc="cell 1 contact pads (board: SC1+ / SC1-): pin 1 = + (SOLAR_IN), pin 2 = - (SC_MID). Not placed as a part: plan_board.py draws the pads under the cell")
            s.net(j3, "1", "SOLAR_IN"); s.net(j3, "2", "SC_MID")
            j4 = s.place("Connector_Generic", "Conn_01x02", "J4", "Solar cell 2", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", PX + 100, PY + 60, 0,
                         desc="cell 2 contact pads (board: SC2+ / SC2-): pin 1 = + (SC_MID), pin 2 = - (GND). Not placed as a part")
            s.net(j4, "1", "SC_MID"); s.gnd(s.pin_end(j4, "2")[0])
            s.text("Two cells in series: 2 x ~0.7 V cold-start check on the bench (BQ25570 needs >= 0.6 V), Vmpp about twice one cell", (PX + 80, PY + 28), 2)
            s.flag(s.pin_end(j3, "1")[0]); s.flag(s.pin_end(j1, "1")[0])      # SOLAR_IN and BATT are fed from outside the schematic (one flag per net: J1B is on the same BATT net)
        enp = s.pin_end(h, "~{EN}")[0]
        s.gnd(enp)
    s.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), (f"{PROJECT}.kicad_sch" if variant == "solar" else f"{PROJECT}_{variant}.kicad_sch")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="solar", choices=["usb", "solar"])
    a = ap.parse_args()
    build(a.variant)
    print("wrote", f"{PROJECT}.kicad_sch" if a.variant == "solar" else f"{PROJECT}_{a.variant}.kicad_sch")
