# DEPRECATED: revision B, the pogo-pad board (archived 2026-11-02)

**Do not order this.** It was never ordered. It is the last state of revision B before charging and programming moved to a USB-C receptacle; the living design in `../../../hardware/` is now **revision C** (USB-C). Code word: **`pogo-b`**.

What this folder holds, exactly as it was when it was replaced:
- `hardware/` the KiCad project (schematic, routed board, custom footprints, `netlist.xml`, `production/` with Gerbers, BOM and CPL, `renders/`, the old generator `gen_schematic.py` with `symlib.py`). Open `hardware/LED Watch - Single Color.kicad_pro` (the clean committed project file of that day).
- Charging and programming: four 1.27 mm pogo pads on the back (1 RESET, 2 VBAT, 3 GND, 4 UPDI); the BQ25570 harvester charges the LiPo from the solar cell only.
- The firmware pin map is the same as revision C's (the MCU pins did not change), so there is no separate `firmware-pinmap/`.

## Known problem: do not use as it is
The solar cell pad **SC1+ is on net `SOLAR_IN` (no slash) while the harvester input, L1 and C50 are on `/SOLAR_IN`**, so no copper reaches the pad and the cell is not connected to the BQ25570. KiCad's normal DRC does not show it (`kicad-cli pcb drc --schematic-parity` does, as `net_conflict`). Found 2026-11-02, fixed in revision C. See `../../../docs/DECISION-LOG.md` (2026-11-02, "solar cell pad was never connected").

## Why it was replaced
Programming through a jig of pogo pins needs a home-made fixture, and the pads gave no way to charge from a cable. Revision C has a GCT USB4110 USB-C receptacle (JLCPCB C5143397) at 3 o'clock on the back: VBUS charges the LiPo through a TI BQ21040 (U5, 54 mA), and the two SBU pins carry UPDI (1 k in series, BAT54WS clamp to +3V3), so a USB-C cable with the SBU wires plus a UPDI adapter programs the watch. Details: `../../../hardware/REVISIONS.md`.
