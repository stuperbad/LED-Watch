"""
Parametric schematic generator for the single-colour LED watch.

WARNING (2026-10-29): the saved 'LED Watch - Single Color.kicad_sch' was hand-rearranged in KiCad after the last run of this script, and its notes were
edited directly. Re-running this script OVERWRITES that layout. Edit the .kicad_sch in KiCad; use this script only as a reference or for a from-scratch rebuild.

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_schematic.py --variant usb
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_schematic.py --variant solar

Writes 'LED Watch - Single Color.kicad_sch' (solar variant; the old pad-charged variant writes '... _usb.kicad_sch') next to this script. Everything is derived from the CONFIG
block and the pin-assignment tables, so changing LED sizes, resistor values or the MCU pin map is a re-run.

Design (see ../README.md and ../docs/):
  * 132 white LEDs = 12 sectors (columns) x 11 slots (rows): per 30-degree sector, slot 0 = the HOUR LED,
    slots 1-5 = five MINUTE LEDs, slots 6-10 = five SECOND LEDs.
  * Anode of every LED goes to its COLUMN net (through one series resistor per column, MCU pin SOURCES), cathode to its ROW net (MCU pin SINKS).
  * Time display lights ~3 LEDs at once, so the MCU drives the matrix directly (the game mode may need row drivers - see ../docs/mcu-pinmaps.md).

Drawing rules (schematic style, after review by jsarrett):
  * Nothing connects to a component pin directly: every pin gets a short wire first, and the net label or power symbol sits on the end of that wire.
  * Power comes from power symbols (VBAT, +3V3, GND), never from net labels; a power symbol sits on a wire stub, pointing away from the part.
  * Parts that belong together in a circuit (inductors, ladders, crystal caps, the harvester's rails) are joined by real wires.
  * Reference and value text sit beside the part, never on a pin, a wire or another part; notes are wrapped and kept clear of the parts.
"""
import argparse, math, os, re, sys, textwrap, uuid
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

G = 2.54                              # schematic grid
VEC = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}      # screen direction of a "pin points away from the body" angle (screen y grows downward)
POWER = {"GND": ("GND", "GND"), "V33": ("+3V3", "+3V3"), "VBAT": ("+BATT", "VBAT"), "VBUS": ("VBUS", "VBUS")}   # kind -> (library symbol, value text)


def U():
    return str(uuid.uuid4())


def f(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def add(p, ang, n):
    """point n mm from p in direction ang (0 right, 90 up, 180 left, 270 down)"""
    return (round(p[0] + VEC[ang][0] * n, 4), round(p[1] + VEC[ang][1] * n, 4))


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
        if a == b:
            return
        self.items.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    def wpath(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.wire(a, b)

    def junction(self, p):
        self.items.append(f'\t(junction\n\t\t(at {f(p[0])} {f(p[1])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')

    def noconnect(self, p):
        self.items.append(f'\t(no_connect\n\t\t(at {f(p[0])} {f(p[1])})\n\t\t(uuid "{U()}")\n\t)')

    def label(self, text, p, ang=0):
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append(f'\t(label "{text}"\n\t\t(at {f(p[0])} {f(p[1])} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    def text(self, s, p, size=2.0, max_mm=None, anchor="left top"):
        """free text note; wrapped to max_mm (stroke font: about 0.8 x size per character) and anchored at its top-left corner by default"""
        if max_mm:
            s = "\n".join(textwrap.wrap(s, max(10, int(max_mm / (0.8 * size)))))
        s = s.replace('"', "'").replace("\n", "\\n")
        self.items.append(f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(p[0])} {f(p[1])} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify {anchor})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    # ---- symbols
    def place(self, libname, name, ref, value, fp, x, y, rot=0, show_ref=True, show_val=True, extra=None, desc="",
              ref_at=(3.0, -1.4), val_at=(3.0, 1.4), just="left"):
        """ref_at / val_at: offset of the reference and value text from the part's centre (default: right of a vertical two-pin part)"""
        x, y = round(x / G) * G, round(y / G) * G
        key = self.lib(libname, name)
        pins = symlib.pins(libname, name)
        inst = dict(key=key, ref=ref, x=x, y=y, rot=rot, pins={p["number"]: p for p in pins}, byname={p["name"]: p for p in pins})

        tang = 90 if rot in (90, 270) else 0           # KiCad turns field text with the symbol: counter-turn it so the text stays horizontal

        def prop(k, v, at, hide, justify=None):
            j = f"\n\t\t\t\t(justify {justify})" if justify else ""
            h = "\n\t\t\t\t(hide yes)" if hide else ""
            return (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {f(x + at[0])} {f(y + at[1])} {0 if hide else tang})\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}{h}\n\t\t\t)\n\t\t)')
        props = [prop("Reference", ref, ref_at, not show_ref, just), prop("Value", value, val_at, not show_val, just),
                 prop("Footprint", fp, (0, 0), True), prop("Datasheet", (extra or {}).get("Datasheet", "~"), (0, 0), True),
                 prop("Description", desc, (0, 0), True)]
        for k, v in (extra or {}).items():
            if k != "Datasheet":
                props.append(prop(k, v, (0, 0), True))
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

    # ---- nets: a pin never carries a label or a power symbol itself, there is always a wire stub in between
    def net(self, inst, which, netname, n=G):
        """wire stub away from the pin, net label on its far end; returns the end point"""
        pt, out = self.pin_end(inst, which)
        end = add(pt, out, n)
        self.wire(pt, end)
        self.label(netname, end, out)
        return end

    def nc(self, inst, which):
        (pt, out) = self.pin_end(inst, which)
        self.noconnect(pt)

    def sym(self, kind, pt, gdir, show=True):
        """power symbol (kind = GND / V33 / VBAT / VBUS) whose pin sits on pt and whose graphic points along gdir"""
        libname, value = POWER[kind]
        key = self.lib("power", libname)
        self.pwr += 1
        ref = f"#PWR{self.pwr:03d}"
        default = 270 if kind == "GND" else 90                  # direction the library graphic points
        rot = (gdir - default) % 360
        tang = 90 if rot in (90, 270) else 0
        if gdir == 90:
            tx, ty, j = pt[0], pt[1] - 3.81, ""
        elif gdir == 270:
            tx, ty, j = pt[0], pt[1] + 3.81, ""
        elif gdir == 0:
            tx, ty, j = pt[0] + 3.2 + 0.46 * len(value), pt[1], ""
        else:
            tx, ty, j = pt[0] - 3.2 - 0.46 * len(value), pt[1], ""
        txt = (f'\t(symbol\n\t\t(lib_id "{key}")\n\t\t(at {f(pt[0])} {f(pt[1])} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(dnp no)\n\t\t(uuid "{U()}")\n'
               f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {f(pt[0])} {f(pt[1])} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Value" "{value}"\n\t\t\t(at {f(tx)} {f(ty)} {tang})\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}{"" if show else chr(10) + chr(9) * 4 + "(hide yes)"}\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Footprint" ""\n\t\t\t(at 0 0 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(pin "1"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
               f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.items.append(txt)

    def power(self, inst, which, kind, n=G, style="rot"):
        """power symbol on a wire stub from a pin. style 'rot': the symbol points away from the part (any side);
        style 'L': the symbol stays upright (+V up, GND down), the wire turns once for it (only for pins with free space beside them)."""
        pt, out = self.pin_end(inst, which)
        end = add(pt, out, n)
        self.wire(pt, end)
        gdir = 270 if kind == "GND" else 90
        if out == gdir or style == "rot":
            self.sym(kind, end, out)
            return end
        if out in (0, 180):                                     # sideways pin, upright symbol: one more leg up (or down)
            end2 = add(end, gdir, G)
            self.wire(end, end2)
            self.sym(kind, end2, gdir)
            return end2
        raise ValueError("pin points the wrong way for an upright symbol: use style 'rot'")

    def power_bus(self, inst, pins, kind, n=G):
        """several pins on one rail side by side (e.g. VDD / VDDIO2 / AVDD): a stub from each, joined by one wire, ONE symbol on the middle one"""
        ends, out = [], None
        for w in pins:
            pt, out = self.pin_end(inst, w)
            end = add(pt, out, n)
            self.wire(pt, end)
            if end not in ends:
                ends.append(end)
        ends.sort()
        self.wire(ends[0], ends[-1])
        mid = ends[len(ends) // 2]
        self.junction(mid)
        self.sym(kind, mid, out)
        return mid

    def flag_on(self, pt, ang):
        """PWR_FLAG hung on a wire at pt (junction there): a 2.54 mm branch toward ang, the flag on its end, no value text"""
        self.junction(pt)
        end = add(pt, ang, G)
        self.wire(pt, end)
        libname = "PWR_FLAG"
        key = self.lib("power", libname)
        self.pwr += 1
        ref = f"#FLG{self.pwr:03d}"
        rot = (ang - 90) % 360
        txt = (f'\t(symbol\n\t\t(lib_id "{key}")\n\t\t(at {f(end[0])} {f(end[1])} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(dnp no)\n\t\t(uuid "{U()}")\n'
               f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {f(end[0])} {f(end[1])} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Value" "PWR_FLAG"\n\t\t\t(at {f(end[0])} {f(end[1])} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(property "Footprint" ""\n\t\t\t(at 0 0 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n'
               f'\t\t(pin "1"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
               f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.items.append(txt)

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
        ytop, ybot = taps[0][1], Y0 + (rows - 1) * DY + 7.62        # every column bus ends at the same height (below row 11), so labels never meet the ROW11 label
        s.wire((xbus, ytop), (xbus, ybot))
        s.label(f"COL{c}", (xbus, ybot), 270)
    s.text("LED MATRIX: 12 columns (sectors) x 11 rows (slot 0 = hour, 1-5 = minutes, 6-10 = seconds). Anodes -> COLn (sources), cathodes -> ROWn (sinks).", (X0 - 10, Y0 - 16), 3, max_mm=270, anchor="left bottom")

    # ============ column series resistors =============
    RX, RY = X0, Y0 + rows * DY + 40
    for c in range(cols):
        x = RX + c * DX
        r = s.place("Device", "R", f"R{c + 1}", cfg["r_col"], cfg["r_fp"], x, RY, 0)
        s.net(r, "1", f"COL{c}"); s.net(r, "2", f"COL{c}_MCU")
    s.text("Series resistor per column: 220 ohm from led_resistor.py (peak LED current 1.6-4.8 mA over 3.3-4.12 V; worst case <= 5 mA). Re-check once the LED parts are chosen.",
           (RX - 10, RY + 26), 2.5, max_mm=290)

    # ============ MCU =============
    MX, MY = 540.0, 150.0
    mcu = s.place("MCU_Microchip_AVR_Dx", "AVR128DB48x-x6LX", "U1", "AVR128DB48-I/6LX", "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm", MX, MY, 0,
                  extra={"Datasheet": "https://ww1.microchip.com/downloads/en/DeviceDoc/AVR128DB64-48-32-DataSheet-DS40002247.pdf"},
                  desc="AVR128DB48 8-bit AVR, 128KB flash, VQFN-48 6x6 (6LX). Same pin numbers as the TQFP (datasheet DS40002247B pin table lists 48-pin TQFP/VQFN together). EP: KiCad footprint 4.2 mm, datasheet 4.1 mm - check land pattern",
                  ref_at=(-44.0, -51.0), val_at=(-44.0, -48.5))
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
    # power pins: the three supply pins (top) share one wire and ONE VBAT symbol, the ground pins (bottom) likewise
    s.power_bus(mcu, ["VDD", "VDDIO2", "AVDD"], "VBAT", n=2 * G)
    s.power_bus(mcu, ["15", "29", "43"], "GND", n=2 * G)
    # decoupling next to MCU
    dx = MX - 36
    for i, label in enumerate(("VDD", "VDDIO2", "AVDD")):
        c = s.place("Device", "C", f"C{10 + i}", "100n", cfg["c_fp"], dx + i * 15.24, MY + 80, 0)
        s.power(c, "1", "VBAT"); s.power(c, "2", "GND")
    cb = s.place("Device", "C", "C13", "10u", cfg["c_fp"], dx + 3 * 15.24, MY + 80, 0)
    s.power(cb, "1", "VBAT"); s.power(cb, "2", "GND")
    s.text("MCU decoupling: 100 nF per supply pin + 10 uF bulk on VBAT", (dx - 5, MY + 100), 2, max_mm=90)

    # ============ 32 kHz crystal =============
    CX, CY = 381.0, 50.8
    s.text("32.768 kHz crystal on PF0/PF1 (XTAL32K1/2). Load caps are a placeholder: confirm with the datasheet/EE.", (CX - 30, CY - 22), 2, max_mm=100, anchor="left bottom")
    y1 = s.place("Device", "Crystal", "Y1", "32.768kHz", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", CX, CY, 0,
                 extra={"MPN": "ABS07-32.768KHZ-T"}, desc="12.5 pF load", ref_at=(0, -10.5), val_at=(0, -8.0), just=None)
    for i, net in enumerate(("XTAL1", "XTAL2")):
        c = s.place("Device", "C", f"C{20 + i}", cfg["c_xtal"], cfg["c_fp"], CX + (-7.62 if i == 0 else 7.62), CY + 20.32, 0,
                    ref_at=(3.0 if i else -3.0, -1.4), val_at=(3.0 if i else -3.0, 1.4), just="left" if i else "right")
        yp, _ = s.pin_end(y1, str(i + 1))
        cp, _ = s.pin_end(c, "1")
        corner = (cp[0], yp[1])
        s.wpath(yp, corner, cp)
        s.label(net, corner, 180 if i == 0 else 0)
        s.power(c, "2", "GND")

    # ============ accelerometer =============
    IX, IY = 406.4, 144.78
    s.text("LIS2DW12 accelerometer on I2C (SDA = PA2, SCL = PA3) from the 3.3 V rail. CS high = I2C mode; SDO/SA0 low = address 0x18; pin 7 RES to GND (DS11811 Table 1). "
           "FIRMWARE: set PINnCTRL.INLVL = TTL on IMU_INT's pin (the sensor's high is only about 3.1 V and the MCU runs at up to 4.2 V).", (IX - 62, IY - 36), 2, max_mm=110, anchor="left bottom")
    u2 = s.place("Local", "LIS2DW12", "U2", "LIS2DW12TR", "Package_LGA:LGA-12_2x2mm_P0.5mm", IX, IY, 0,
                 extra={"Datasheet": "https://www.st.com/resource/en/datasheet/lis2dw12.pdf", "MPN": "LIS2DW12TR"},
                 desc="ST LIS2DW12 accelerometer (DS11811 rev 9): 50 nA power-down, 1.62-3.6 V, I2C addr 0x18 with SDO/SA0 = GND",
                 ref_at=(-12.0, -18.5), val_at=(-12.0, -16.0))
    s.power(u2, "~{CS}", "V33", G)                  # pins are 2.54 apart: power symbols close in, the signal labels on long stubs, so their texts do not touch
    s.power(u2, "SDO/SA0", "GND", G)
    s.power(u2, "NC", "GND", G)
    s.power_bus(u2, ["VDD", "VDD_IO"], "V33", n=G)
    s.power(u2, "6", "GND", G)                      # pins 6, 7 (RES) and 8 are stacked on one point
    s.net(u2, "SCL/SPC", "SCL", 5 * G); s.net(u2, "SDA/SDI/SDO", "SDA", 5 * G); s.net(u2, "INT1", "IMU_INT")
    s.nc(u2, "INT2")
    for i, net in enumerate(("SDA", "SCL")):
        r = s.place("Device", "R", f"R{20 + i}", "10k", cfg["r_fp"], IX - 62 + i * 15.24, IY + 2.54, 0)
        s.net(r, "2", net); s.power(r, "1", "V33")
    DUMMIES = [57, 58, 59, 61, 62, 63, 64, 65, 66, 67]      # cosmetic dummies (same 10k 0402 as R20/R21 = no new BOM line; pins not connected): keep the hour-LED flanks and the compass-rose pairs symmetric
    for i, n in enumerate(DUMMIES):
        r = s.place("Device", "R", f"R{n}", "10k", cfg["r_fp"], IX - 62 + (i % 5) * 15.24, IY + 40 + (i // 5) * 20.32, 0,
                    desc="COSMETIC DUMMY: not connected, keeps the layout symmetric around the 3 / 6 / 9 / 12 o'clock parts")
        s.nc(r, "1"); s.nc(r, "2")
    s.text("Cosmetic dummy resistors R57-R67 (not connected): they keep the board layout symmetric around the 12 / 3 / 6 / 9 o'clock parts.", (IX - 62, IY + 25), 2, max_mm=90)
    for i in range(2):
        c = s.place("Device", "C", f"C{30 + i}", "100n", cfg["c_fp"], IX + 28 + i * 15.24, IY + 2.54, 0)
        s.power(c, "1", "V33"); s.power(c, "2", "GND")
    if variant == "usb":
        ldo = s.place("Regulator_Linear", "MCP1700x-330xxTT", "U3", "MCP1700-3302E/TT", "Package_TO_SOT_SMD:SOT-23", IX - 40, IY - 70, 0,
                      desc="3.3 V LDO, 1.6 uA Iq: the LIS2DW12 is limited to 3.6 V but the LiPo reaches 4.2 V")
        s.power(ldo, "VI", "VBAT"); s.power(ldo, "VO", "V33"); s.power(ldo, "GND", "GND")
        for i, (kind, fn) in enumerate((("VBAT", "in"), ("V33", "out"))):
            c = s.place("Device", "C", f"C{35 + i}", "1u", cfg["c_fp"], IX - 62 + i * 52, IY - 70 + 14, 0)
            s.power(c, "1", kind); s.power(c, "2", "GND")

    # ============ buttons =============
    BY = IY + 85
    s.text("Buttons: internal MCU pull-ups, active low", (CX - 30, BY - 14), 2, anchor="left bottom")
    for i, net in enumerate(("BTN1", "BTN2")):
        sw = s.place("Switch", "SW_Push", f"SW{i + 1}", "SW_Push", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2", CX + i * 40, BY, 0, ref_at=(-2.5, -6.5), val_at=(-2.5, -4.0), just=None)
        s.net(sw, "1", net, 2 * G); s.power(sw, "2", "GND", G, style="L")

    # ============ programming pads =============
    # 4 spring-contact (pogo) pads at 1.27 mm on the back, in the Microchip UPDI v2 order: 1 RESET (PF6), 2 VDD (VBAT), 3 GND, 4 UPDI; plus two unplated-net guide holes (unnumbered pads in the footprint).
    # Only UPDI / VDD / GND are needed to program (e.g. Adafruit UPDI Friend 5893); RESET is for high-voltage / reset recovery.
    JY = BY + 38
    s.text("UPDI programming pads (1.27 mm pogo row, back side): 1 RESET, 2 VBAT, 3 GND, 4 UPDI", (CX - 30, JY - 14), 2, max_mm=90, anchor="left bottom")
    j2 = s.place("Connector_Generic", "Conn_01x04", "J2", "UPDI pogo pads 1.27 mm (RESET VDD GND UPDI)", "LEDWatch:UPDI_Pogo_1x4_P1.27mm_2Guide", CX, JY, 0,
                 desc="programming pads, not a part: spring pins on the programmer jig touch them", ref_at=(-2.0, -7.5), val_at=(-2.0, -5.0), just="left")
    s.net(j2, "1", "RESET", 5 * G); s.power(j2, "2", "VBAT", G); s.power(j2, "3", "GND", G); s.net(j2, "4", "UPDI", 5 * G)    # pins are 2.54 apart: labels sit on long stubs, power symbols close in, so their texts do not touch

    # ============ battery connectors =============
    LY = JY + 58
    s.text("LiPo (protected cell). Pin 1 = - (GND), pin 2 = + (BATT): TinyCircuits' own wiring (their datasheet fig. 4); still measure the pouch's leads first.", (CX - 30, LY - 20), 2, max_mm=60, anchor="left bottom")
    j1 = s.place("Connector_Generic", "Conn_01x02", "J1", "LiPo", "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", CX, LY, 0, ref_at=(-2.0, -7.5), val_at=(-2.0, -5.0), just="left")
    if variant == "usb":
        s.power(j1, "2", "VBAT", 2 * G)
    else:
        s.net(j1, "2", "BATT", 2 * G)             # solar variant: the cell sits on the harvester's VBAT pin, the system rail is VSTOR
    s.power(j1, "1", "GND", 3 * G)
    s.flag_on(add(s.pin_end(j1, "1")[0], 180, G), 90)       # the connector's GND is fed from outside the schematic (battery): one flag
    # second battery plug in parallel (two small pouches near the strap ends; board has J1 and J1B)
    j1b = s.place("Connector_Generic", "Conn_01x02", "J1B", "LiPo", "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", CX + 60, LY, 0, ref_at=(-2.0, -7.5), val_at=(-2.0, -5.0), just="left")
    if variant == "usb":
        s.power(j1b, "2", "VBAT", 2 * G)
    else:
        s.net(j1b, "2", "BATT", 2 * G)
    s.power(j1b, "1", "GND", 3 * G)
    s.text("Second pouch in parallel (J1B): same polarity rule as J1.", (CX + 36, LY - 20), 2, max_mm=46, anchor="left bottom")
    # ============ piezo buzzer =============
    bz = s.place("Device", "Buzzer", "BZ1", "PKMCS0909E4000-R1", "LEDWatch:Piezo_Murata_PKMCS0909E4000-R1_9x9mm", CX + 110, LY, 0,
                 extra={"Datasheet": "https://www.murata.com/products/productdata/8796834160670/PKMCS0909E4000-R1.pdf", "MPN": "PKMCS0909E4000-R1", "LCSC": "C910763"},
                 desc="Murata piezo sounder 9x9x1.9, externally driven, ~4 kHz: BUZ_A / BUZ_B are driven in antiphase (PB4 = WO4, PB5 = WO5 inverted)",
                 ref_at=(-2.0, -9.0), val_at=(-2.0, -6.5), just="left")
    s.net(bz, "1", "BUZ_A", 2 * G); s.net(bz, "2", "BUZ_B", 2 * G)
    s.text("Piezo BZ1: PB4 / PB5 drive it in antiphase (TCA1 split mode, PB5 inverted via PORTB.PIN5CTRL.INVEN).", (CX + 90, LY - 20), 2, max_mm=70, anchor="left bottom")

    # ============ power variant =============
    PX, PY = 500.0, 470.0
    if variant == "usb":
        s.text("VARIANT A: pad/USB-charged LiPo (MCP73831, 4.2 V, 1000/Rprog mA)", (PX - 10, PY - 25), 3, anchor="left bottom")
        ch = s.place("Battery_Management", "MCP73831-2-OT", "U4", "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5", PX + 20, PY, 0)
        s.power(ch, "V_{DD}", "VBUS"); s.power(ch, "V_{SS}", "GND"); s.power(ch, "V_{BAT}", "VBAT")
        s.net(ch, "STAT", "CHG_STAT")
        rp = s.place("Device", "R", "R30", cfg["r_prog"], cfg["r_fp"], PX - 15, PY, 0)
        s.net(rp, "1", "PROG"); s.power(rp, "2", "GND")
        s.net(ch, "PROG", "PROG")
        for i, kind in enumerate(("VBUS", "VBAT")):
            c = s.place("Device", "C", f"C{40 + i}", "4u7", cfg["c_fp"], PX + 50 + i * 15, PY, 0)
            s.power(c, "1", kind); s.power(c, "2", "GND")
        for i, (net, ref) in enumerate((("VBUS", "TP1"), ("GND", "TP2"))):
            tp = s.place("Connector", "TestPoint", ref, net, "TestPoint:TestPoint_Pad_D2.0mm", PX - 20 + i * 12.7, PY + 30, 0)
            if net == "VBUS":
                s.power(tp, "1", "VBUS"); s.flag_on(add(s.pin_end(tp, "1")[0], 270, G), 0)
            else:
                s.power(tp, "1", "GND")
        s.text("Charge pads TP1 (VBUS) / TP2 (GND). Cap values (4.7 uF) per MCP73831 datasheet - verify.", (PX - 25, PY + 20), 2, max_mm=100)
    else:
        s.text("VARIANT B: solar harvester + LiPo (TI BQ25570, 80% MPPT, built-in 3.3 V buck)", (PX - 75, PY - 85), 3, anchor="left bottom")
        UX, UY = PX, PY
        h = s.place("Battery_Management", "BQ25570", "U4", "BQ25570RGRR", "LEDWatch:BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm", UX, UY, 0,
                    extra={"Datasheet": "https://www.ti.com/lit/ds/symlink/bq25570.pdf"},
                    desc="Ultra-low-power boost charger + nano-power buck; VBIAS 1.21 V", ref_at=(-17.78, -23.0), val_at=(-17.78, -20.5), just="right")
        hx, hy = h["x"], h["y"]

        def P(dx, dy):
            return (round(hx + dx, 4), round(hy + dy, 4))
        # --- ground: the five VSS pins sit on one point at the bottom
        s.power(h, "1", "GND", 2 * G)
        # --- left side: boost inductor L1 wired from LBOOST to the SOLAR_IN node, which also feeds VIN_DC, the input cap C50 and the cell pad
        l1 = s.place("Device", "L", "L1", "22uH", "Inductor_SMD:L_1210_3225Metric", hx - 30.48, hy - 12.7, 270,
                     desc="22 uH, Isat above the BQ25570 boost current limit (see datasheet table)", ref_at=(-3.0, -4.5), val_at=(-3.0, -2.5), just="left")
        lb_pt, _ = s.pin_end(h, "LBOOST")
        l1a, _ = s.pin_end(l1, "1"); l1b, _ = s.pin_end(l1, "2")
        s.wire(lb_pt, l1a)
        s.label("LBOOST", (round(lb_pt[0] - 3.81, 4), lb_pt[1]), 180)
        node = (hx - 40.64, l1b[1])                                   # SOLAR_IN node left of L1
        s.wire(l1b, node)
        vin_pt, _ = s.pin_end(h, "VIN_DC")
        top = hy - 33.02
        s.wpath(vin_pt, (vin_pt[0], hy - 22.86), (hx - 7.62, hy - 22.86), (hx - 7.62, top), (node[0], top), node)
        s.junction(node)
        s.label("SOLAR_IN", (hx - 20.32, top), 0)
        c50 = s.place("Device", "C", "C50", "4u7", "Capacitor_SMD:C_0402_1005Metric", hx - 48.26, hy + 2.54, 0)
        c50p, _ = s.pin_end(c50, "1")
        s.wpath(c50p, (c50p[0], node[1]), node)
        s.power(c50, "2", "GND")
        # cell pad (SOLAR_IN) hangs on the top wire; the cell's return pad goes to GND
        scp = s.place("Connector", "TestPoint", "SC1+", "cell pad", "LEDWatch:KXOB25_cell_pad_2.5x7.4mm", node[0], top - 10.16, 0,
                      desc="KXOB25-05X3TF + end pad (SOLAR_IN). Not a part: just the 2.5 x 7.4 mm board pad under the cell. VERIFY polarity of the physical cell (Voc) before soldering",
                      ref_at=(3.0, -2.5), val_at=(3.0, 0.0))
        scp_pt, _ = s.pin_end(scp, "1")
        s.wire(scp_pt, (node[0], top))
        s.junction((node[0], top))
        s.flag_on((node[0], top - 5.08), 180)
        scm = s.place("Connector", "TestPoint", "SC1-", "cell pad", "LEDWatch:KXOB25_cell_pad_2.5x7.4mm", node[0] - 22.86, top - 10.16, 0,
                      desc="KXOB25-05X3TF - end pad (GND). Not a part: just the board pad under the cell", ref_at=(3.0, -2.5), val_at=(3.0, 0.0))
        s.power(scm, "1", "GND", 2 * G)
        s.text("One KXOB25-05X3TF (3 cells in series inside): Voc 2.07 V clears the BQ25570 cold-start minimum of 0.6 V (typ; 0.7 V max) even in dim light.",
               (node[0] - 22.86, top - 27), 2, max_mm=70, anchor="left bottom")
        # --- top: VSTOR is the system rail (VBAT symbol); the cell sits on the VBAT pin (net BATT)
        s.power(h, "VSTOR", "VBAT", 2 * G)
        vb, _ = s.pin_end(h, "VBAT")
        vbe = (vb[0], hy - 22.86)
        s.wpath(vb, vbe, (vbe[0] + 7.62, vbe[1]))
        s.label("BATT", (vbe[0] + 7.62, vbe[1]), 0)
        # --- left pins: VOC_SAMP and VOUT_EN tied to the VBAT rail, EN to GND, VREF_SAMP to its 10 nF cap
        s.power(h, "VOC_SAMP", "VBAT", 2 * G)
        s.power(h, "~{EN}", "GND", 2 * G)
        s.power(h, "VOUT_EN", "VBAT", 2 * G)
        vr, _ = s.pin_end(h, "VREF_SAMP")
        c51 = s.place("Device", "C", "C51", "10n", "Capacitor_SMD:C_0402_1005Metric", hx - 25.4, hy + 25.4, 0)
        c51p, _ = s.pin_end(c51, "1")
        s.wpath(vr, (c51p[0], vr[1]), c51p)
        s.label("VREF_SAMP", (c51p[0], vr[1]), 180)
        s.power(c51, "2", "GND")
        # --- right side: buck inductor L2 from LBUCK to the +3V3 rail (VOUT pin, output cap C54, symbol, flag)
        lk, _ = s.pin_end(h, "LBUCK")
        l2 = s.place("Device", "L", "L2", "10uH", "Inductor_SMD:L_1210_3225Metric", hx + 40.64, hy - 12.7, 90,
                     desc="10 uH (datasheet example: Toko DFE252012C), Isat above the buck current limit", ref_at=(-3.0, -4.5), val_at=(-3.0, -2.5), just="left")
        l2a, _ = s.pin_end(l2, "1"); l2b, _ = s.pin_end(l2, "2")
        s.wire(lk, l2a)
        s.label("LBUCK", (round(lk[0] + 3.81, 4), lk[1]), 0)
        vo, _ = s.pin_end(h, "VOUT")
        rail_y = vo[1]
        x_l2 = l2b[0] + 5.08
        rail_end = (hx + 63.5, rail_y)
        s.wpath(vo, rail_end)
        s.wpath(l2b, (x_l2, l2b[1]), (x_l2, rail_y))
        s.junction((x_l2, rail_y))
        c54 = s.place("Device", "C", "C54", "22u", "Capacitor_SMD:C_0805_2012Metric", hx + 50.8, hy + 2.54, 0)
        c54p, _ = s.pin_end(c54, "1")
        s.wpath(c54p, (c54p[0], rail_y))
        s.junction((c54p[0], rail_y))
        s.power(c54, "2", "GND")
        s.sym("V33", rail_end, 90)
        s.flag_on((x_l2 + 5.08, rail_y), 90)
        s.net(h, "VBAT_OK", "BAT_OK", 2 * G)
        # --- resistor ladders from the datasheet's design procedure (VBIAS = 1.21 V, RSUM = 13 MOhm), all three hang from VRDIV
        vrd, _ = s.pin_end(h, "VRDIV")
        lx = [hx + 40.64, hx + 60.96, hx + 81.28]
        by = hy + 27.94
        s.wpath(vrd, (hx + 30.48, vrd[1]), (hx + 30.48, by - 5.08), (lx[-1], by - 5.08))
        s.label("VRDIV", (hx + 20.32, vrd[1]), 0)
        ladders = [("OV", lx[0], [("R50", "6.49M", "VBAT_OV"), ("R51", "5.11M", None)], ["VBAT_OV"]),
                   ("OK", lx[1], [("R52", "1.47M", "OK_HYST"), ("R53", "6.49M", "OK_PROG"), ("R54", "3.74M", None)], ["OK_HYST", "OK_PROG"]),
                   ("OUT", lx[2], [("R55", "7.32M", "VOUT_SET"), ("R56", "4.22M", None)], ["VOUT_SET"])]
        for name, x, parts, mids in ladders:
            prev = None
            for i, (ref, val, below) in enumerate(parts):
                r = s.place("Device", "R", ref, val, "Resistor_SMD:R_0402_1005Metric", x, by + 7.62 + i * 17.78, 0, desc="1% 0402; value from BQ25570 design procedure")
                top_pt, _ = s.pin_end(r, "1")
                if prev is None:
                    s.wpath((top_pt[0], by - 5.08), top_pt)
                    if x != lx[-1]:
                        s.junction((top_pt[0], by - 5.08))
                else:
                    s.wire(prev, top_pt)
                    mid = (prev[0], round((prev[1] + top_pt[1]) / 2, 4))
                    s.junction(mid)
                    s.wire(mid, (mid[0] + G, mid[1]))
                    s.label(mids[i - 1], (mid[0] + G, mid[1]), 0)
                prev = s.pin_end(r, "2")[0]
                if below is None:
                    s.power(r, "2", "GND")
        s.net(h, "OK_HYST", "OK_HYST", 2 * G); s.net(h, "OK_PROG", "OK_PROG", 2 * G)
        s.net(h, "VBAT_OV", "VBAT_OV", 2 * G); s.net(h, "VOUT_SET", "VOUT_SET", 2 * G)
        s.text("Ladders: VBAT_OV = 4.12 V (R50/R51), BAT_OK falls 3.31 V / rises 3.78 V (R52-R54), VOUT = 3.31 V (R55/R56). Equations: BQ25570 datasheet 7.3.3, 7.3.4, 7.3.6.",
               (hx + 30.48, by + 66), 2, max_mm=80)
        # --- rail capacitors
        for i, (ref, val, kind) in enumerate((("C52", "4u7", "VBAT"), ("C53", "10n", "VBAT"))):
            c = s.place("Device", "C", ref, val, "Capacitor_SMD:C_0402_1005Metric", hx + 12.7 * (i + 0) - 5.08 * (1 - i), hy + 50.8, 0)
            s.power(c, "1", kind); s.power(c, "2", "GND")
        # --- the cell / battery nets need a source for ERC: the cell pad (SOLAR_IN) and the battery plug J1 carry PWR_FLAGs
        s.flag_on(add(s.pin_end(j1, "2")[0], 180, G), 270)
    s.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), (f"{PROJECT}.kicad_sch" if variant == "solar" else f"{PROJECT}_{variant}.kicad_sch")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="solar", choices=["usb", "solar"])
    a = ap.parse_args()
    build(a.variant)
    print("wrote", f"{PROJECT}.kicad_sch" if a.variant == "solar" else f"{PROJECT}_{a.variant}.kicad_sch")
