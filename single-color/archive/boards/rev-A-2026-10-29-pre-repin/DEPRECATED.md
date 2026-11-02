# DEPRECATED: revision A, the pre-repin board (archived 2026-10-29)

**Do not order this.** It was never ordered. It is the last state of the revision A design before the MCU pins were reorganised; the living design in `../../../hardware/` is now **revision B**.

What this folder holds, exactly as it was on 2026-10-29:
- `hardware/` the KiCad project (schematic with the hand-arranged, cleaned-up sheet, routed and DRC-clean board, custom footprints, `netlist.xml`), `production/` (Gerbers, BOM, CPL as quoted at JLCPCB: $308.63 for 5 assembled boards), `renders/`, `source/` (the layout-D hand placement), and the old generator `gen_schematic.py`.
- `firmware-pinmap/` the firmware pin map (`pins.h`, `hwmap.h`, `ledmap.h`, `gen_pins.py`) that matches this board.

The board and the schematic are electrically the same as git commit `7c34eee` (the schematic file here has the later layout clean-up, same nets). The git tag `rev-A` is an older snapshot (2026-10-15) and does not have the battery polarity fix or the later re-routes; use this folder instead.

## Why it was replaced
A review (jsarrett, 2026-10-28) pointed out that the LED matrix pins were not organised by port, which makes the schematic, the board and the firmware harder to read and explain. Re-routing was cheap, so revision B puts every matrix line on a whole port in pin order. Nothing was wrong electrically; nothing here is known to be broken.

## Pin differences (A -> B)
| Net | Rev A (this folder) | Rev B |
|---|---|---|
| COL0-COL1 | PA0, PA1 | PA0, PA1 (unchanged) |
| COL2-COL7 | PA4-PA7 + PB0, PB1 (pins 48, 1, 2, 3, 4, 5) | PA2-PA7 (pins 46, 47, 48, 1, 2, 3) |
| COL8-COL11 | PB2, PB3, PC0, PC1 | PB0-PB3 (pins 4-7) |
| ROW0-ROW7 | PC2-PC7, PD0, PD1 | PC0-PC7 (pins 10-13, 16-19) |
| ROW8-ROW11 | PD2-PD5 | PD0-PD3 (pins 20-23) |
| SDA / SCL | PA2 / PA3 (TWI0) | PF2 / PF3 (TWI1) |
| BUZ_A / BUZ_B | PB4 / PB5 | PB4 / PB5 (unchanged) |

To go back to this design, copy the folders above over `hardware/` and `firmware/` (and revert the firmware's I2C driver to TWI0).
