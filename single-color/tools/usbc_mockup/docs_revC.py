"""docs_revC.py : the documentation edits of the switch to revision C (2026-11-02): README, REVISIONS, HANDOFF, BRING-UP, BRING-UP-TESTS, PRE-ORDER-CHECKLIST. Run once from the single-color folder (not idempotent)."""
import re


def rd(p):
    return open(p, encoding="utf8").read()


def wr(p, t):
    open(p, "w", encoding="utf8", newline="").write(t)


def sub(t, old, new, count=1):
    assert old in t, old[:70]
    return t.replace(old, new, count)


# ---------- README.md
p = "README.md"; t = rd(p)
t = re.sub(r"\*\*Status \(2026-10-29\): revision B is the current design, not ordered yet\.\*\*.*?\n",
           lambda m: "**Status (2026-11-02): revision C is the current design, not ordered yet.** Revision C is revision B with charging and programming moved from four pogo pads to a **USB-C receptacle** on the back (GCT USB4110, a TI BQ21040 charger, UPDI on the two SBU pins), the solar cell pad connection fixed (on revision B the cell pad was on a differently named net and not wired to the harvester), the outer LED-column arcs pulled in from the board edge, and the silkscreen reduced to the numbers, labels and a few orientation marks. Revision B (pogo pads, code word `pogo-b`) is deprecated and archived in `archive/boards/rev-B-pogo/`; revision A in `archive/boards/rev-A-2026-10-29-pre-repin/`. Nothing has been powered up.\n",
           t, count=1, flags=re.S)
t = sub(t, "| MCU | Microchip AVR128DB48 (VQFN-48), UPDI programming through 4 pogo pads (RESET, VDD, GND, UPDI) on the back |",
        "| MCU | Microchip AVR128DB48 (VQFN-48), UPDI programming through the USB-C receptacle's SBU pins (1 k in series, BAT54WS clamp); no reset pad (RESET on PF6 is not wired out) |")
t = sub(t, "| Power | Anysolar KXOB25-05X3TF cell -> TI BQ25570 harvester -> 2 protected LiPo pouches (JST SH plugs) |",
        "| Power | Anysolar KXOB25-05X3TF cell -> TI BQ25570 harvester -> 2 protected LiPo pouches (JST SH plugs); USB-C 5 V -> TI BQ21040 charger (54 mA) -> the same pouches |")
t = sub(t, "| `archive/` | older board generations and experiments; see `archive/README.md` |",
        "| `archive/` | older board generations and experiments (revision A, revision B with pogo pads); see `archive/README.md` |")
t = sub(t, "what you send to JLCPCB:", "what you send to JLCPCB (revision C):")
t = sub(t, "| `hardware/REVISIONS.md` | the revision table (A = the order candidate); revisions are git tags, not file names |",
        "| `hardware/REVISIONS.md` | the revision table (A and B archived, **C = current**); revisions are git tags, not file names |")
wr(p, t)

# ---------- hardware/REVISIONS.md
p = "hardware/REVISIONS.md"; t = rd(p)
t = sub(t, "| **B** | 2026-10-29 | **current design, in progress** (not ordered) |",
        "| B | 2026-10-29 | **DEPRECATED 2026-11-02, never ordered**; archived in `../archive/boards/rev-B-pogo/` (code word `pogo-b`; known problem: solar cell pad not connected, see its `DEPRECATED.md`) |")
row = ("| **C** | 2026-11-02 | **current design, in progress** (not ordered; Gerbers, BOM and CPL were uploaded to JLCPCB for a check, nothing saved to the cart) | "
       "Revision B with: **USB-C receptacle J2** (GCT USB4110-GF-A, JLCPCB C5143397) on the back at the rim, 3 o'clock, replacing the 4-pad pogo row; **BQ21040 charger U5** (VBUS -> BATT, ISET 10 k = 54 mA, TS 10 k), C55 / C56 1 uF, CC1 / CC2 5.1 k pull-downs (R68 / R69); "
       "**UPDI on the SBU pins** through R72 1 k with a BAT54WS clamp to +3V3 (D50, pads from the PANJIT datasheet); RESET no longer wired out. Fixed: solar cell pad SC1+ now on `/SOLAR_IN` with a link to L1.2. "
       "Layout: outer F.Cu COL arcs pulled in 0.29 mm (edge gap 0.31 -> 0.60 mm), COL9 / COL10 re-routed by hand, U5 with TI's land pattern, J1B aligned with J1 in x, silkscreen stripped (front: numbers, weekday letters, mode labels; back: + / - marks; pin-1 marks on U1, U2, U4, U5 and the D50 cathode bar), keep-out rules refined (`tools/usbc_mockup/zonespec.py`). "
       "32 BOM lines, 204 parts, DRC 0 errors / 0 unconnected, parity with the schematic clean. Development history: `docs/DECISION-LOG.md` (2026-11-01 / 02), save points in `mockups/save-points/`. |\n")
i = t.index("\nHow to make the next revision")
t = t[:i].rstrip("\n") + "\n" + row + t[i:]
t = re.sub(r"\*\*Code word `pogo-b`\*\*.*$",
           lambda m: "**Code word `pogo-b`** = revision B with charge and program over the pogo row (before USB-C). Snapshot and notes: `../archive/boards/rev-B-pogo/`. Revision C (USB-C) is the main `LED Watch - Single Color.*` files since 2026-11-02; the file names did not change. The folder `mockups/` is the development history of C (save points, notes).",
           t, flags=re.S)
wr(p, t)

# ---------- firmware/HANDOFF.md
p = "firmware/HANDOFF.md"; t = rd(p)
t = sub(t, "- **Programming:** pogo pads RESET, VDD(VBAT), GND, UPDI (1.27 mm), RESET on PF6 for high-voltage recovery only.",
        "- **Programming (revision C):** UPDI through the USB-C receptacle's SBU1 / SBU2 pins (tied, R72 1 k in series, BAT54WS clamp to +3V3) with a USB-C cable that carries the SBU wires (not every charge-only cable does) and a UPDI adapter; GND from the cable. RESET (PF6) is no longer wired to a connector (the pogo row of revisions A / B is gone), so there is no high-voltage recovery path.")
wr(p, t)

# ---------- docs/BRING-UP.md
p = "docs/BRING-UP.md"; t = rd(p)
t = sub(t, "# Bring-up sheet: first power-up of revision A\n",
        "# Bring-up sheet: first power-up of revision A\n\n> **Revision C (2026-11-02):** the pogo pad row is gone. Where this sheet says pogo pad 2 (`VBAT` rail) probe **C10 pad 1** (front, beside U1) or **C52 pad 1** (back); programming goes through the **USB-C receptacle J2** (SBU pins), see the Programming section; the board can also charge from USB-C (BQ21040, 54 mA), see `BRING-UP-TESTS.md` step 1b. Nothing in revision C has been tried on a real board either.\n")
t = sub(t, "pogo pad row J2 (pad 1 RESET, 2 `VBAT` rail, 3 GND, 4 UPDI)",
        "the `VBAT` rail at C10 pad 1 (revision A / B: pogo pad 2), the USB-C receptacle J2 (revision C: VBUS, GND, SBU)")
t = sub(t, "2. `VBAT` rail (pogo pad 2) to GND: not a short.", "2. `VBAT` rail (C10 pad 1) to GND: not a short.")
t = sub(t, "   - pogo pad 2 (`VBAT` rail) = the battery voltage (the switch is closed);", "   - C10 pad 1 (`VBAT` rail) = the battery voltage (the switch is closed);")
t = sub(t, "- Tool: Adafruit UPDI Friend (product 5893, 3 V setting) or any serial-UPDI adapter, with a home-made jig of 1.27 mm pogo pins on **UPDI, VDD, GND** (RESET not needed). The two guide holes next to the pads are for alignment pins.",
        "- Tool (revision C): Adafruit UPDI Friend (product 5893, 3 V setting) or any serial-UPDI adapter, connected to the USB-C receptacle J2 through a **USB-C cable that carries the SBU wires** (many charge-only cables do not) and a USB-C splitter / breakout: **UPDI -> SBU1 and SBU2** (A8 / B8, tied on the board, 1 k in series, BAT54WS clamp to +3V3), **GND -> GND**. Check the cable's SBU and GND continuity with the meter first. Whether the adapter also feeds VBUS (then the BQ21040 charges a plugged battery at 54 mA and powers the rail) or only GND + UPDI (the battery or a bench supply powers the board) is to be decided on the first board. (Revision A / B had a home-made jig of 1.27 mm pogo pins on UPDI, VDD, GND.)")
wr(p, t)

# ---------- docs/BRING-UP-TESTS.md
p = "docs/BRING-UP-TESTS.md"; t = rd(p)
t = sub(t, "**pogo pad row**: pad 1 RESET, **pad 2 VBAT (system rail)**, pad 3 GND, pad 4 UPDI.",
        "**revision C: the pogo row is gone** (A / B had pad 1 RESET, pad 2 VBAT, pad 3 GND, pad 4 UPDI): probe the **VBAT system rail at C10 pad 1** (front, beside U1) or C52 pad 1 (back); UPDI is on the **USB-C receptacle J2's SBU pins** (A8 / B8); VBUS at C55 pad 1, charger output at C56 pad 1.")
t = sub(t, "1. Resistance to ground at the pogo VBAT pad, at the battery + pin and at the C54 pad: not zero (a short). ",
        "1. Resistance to ground at C10 pad 1 (VBAT), at VBUS (C55 pad 1), at the battery + pin and at the C54 pad: not zero (a short). ")
t = sub(t, "with a 20 mA limit on the VBAT pogo pad (or a battery through your meter in the mA range).",
        "with a 20 mA limit on C10 pad 1 (VBAT; revision A / B: the VBAT pogo pad), or a battery through your meter in the mA range.")
t = sub(t, "rail at pogo pad 2 about the supply voltage;", "rail at C10 pad 1 about the supply voltage;")
t = sub(t, "1. Battery unplugged, programmer on its 3 V setting through the pogo jig (UPDI, VDD, GND).",
        "1. Battery unplugged, programmer on its 3 V setting, connected to J2 through a USB-C cable with SBU and the splitter (UPDI -> SBU, GND; revision A / B: the pogo jig).")
new = ("## Step 1b. USB-C charging (revision C only, new)\n"
       "Battery plugged, programmer not connected, a plain 5 V USB source (not a PD-only charger) through a USB-C cable.\n"
       "- Expect: VBUS at C55 pad 1 about 5 V; `BATT` (C56 pad 1) follows the battery and climbs toward 4.2 V; charge current about **54 mA** (540 / R70 10 k, BQ21040) with the meter in series in the battery lead, less for a nearly full pouch (the two pouches in parallel are 140 mAh, so about 0.4 C). The charger's status pin (~CHG, U5 pin 3) is not connected to anything.\n"
       "- Wrong? **No VBUS:** the cable or source (CC1 / CC2 each have 5.1 k to ground, the source must see a sink). **VBUS present, no charge:** TS (U5 pin 1) must be pulled to ground by R71 10 k; check R70 10 k on ISET (U5 pin 4).\n"
       "- Not yet known (first board): that the 5 V source starts with only the 5.1 k pull-downs (it should, 5 V default), the real charge current, and whether UPDI over SBU works while a source is plugged.\n\n")
t = sub(t, "## Step 2. Program (once per board)", new + "## Step 2. Program (once per board)")
wr(p, t)

# ---------- docs/PRE-ORDER-CHECKLIST.md
p = "docs/PRE-ORDER-CHECKLIST.md"; t = rd(p)
t = re.sub(r"- \[ \] \*\*BLOCKER: solar cell \+ pad SC1\+ is not connected\.\*\*",
           lambda m: "- [x] **Solved in revision C (2026-11-02): solar cell pad SC1+ is connected.** It was a BLOCKER on revision B (archived in `archive/boards/rev-B-pogo/`, do not order it). Original note: solar cell + pad SC1+ is not connected.", t, count=1)
t = t.rstrip("\n") + "\n\n" + (
    "## H. Revision C (USB-C), 2026-11-02\n"
    "- [x] H1 (C) USB-C receptacle, BQ21040 charger, UPDI on SBU, in the schematic, the board, the parts list and the placement file; DRC 0 / 0, parity clean, keep-out 0; Gerbers, BOM, CPL regenerated under `hardware/production/`.\n"
    "- [x] H2 (C) JLCPCB check (owner signed in, nothing saved to the cart, nothing ordered): zip parsed (4 layers, 51.18 x 42 mm), all 32 BOM lines matched, the placement viewer shows U5, D50, J2, J1 / J1B and U1 / U2 oriented as drawn. Three lines (0402 LED, JST plugs, USB4110) have to be ticked by hand. PCBA quote at default PCB options: $237.92 for 5 (setup $51.50, stencil $16.54, components $106.12, feeder loading $49.60, SMT $5.26, X-ray $8.25); the PCB itself and shipping come on top.\n"
    "- [ ] H3 (E+C) Order specification and a real quote: black, ENIG, 0.15 mm vias plugged (as the rev B cart item: $87.82 for the PCB), 5 boards, shipping. Then JLCDFM on the zip, and JLCPCB's own engineering questions after the order.\n"
    "- [ ] H4 (E) USB-C cable that carries the SBU wires + splitter / breakout to the UPDI adapter; check continuity of SBU and GND before the first programming.\n"
    "- [ ] H5 (E) Accepted: the 7 weekday letters are 0.6 mm high (below JLCPCB's recommended 1 mm); J2's 4 hole-clearance items (0.194 against 0.2 mm, library footprint).\n"
    "- [ ] H6 (E) Design review (offered 2026-11-02) once this is in shape.\n"
    "- [ ] H7 (C) Open from before: IMU land pattern vs ST TN0018, JST / inductor drawings, piezo sound path, firmware on the real board (the strap slot is fine for the 18 mm strap per the 3D print).\n")
wr(p, t)
print("docs updated")
