# To-do from jsarrett's review (2026-10-28 / 29)

Working list, not committed on purpose. Tick items off as they are done; record the decisions in DECISION-LOG.md when they are final.

Order of work: **1. pinout (decide)  ->  2. schematic (regenerate)  ->  3. firmware pin map and two timer swaps  ->  4. board: re-route the changed nets and the trace tidy in one pass  ->  5. gerbers, DFM, quote.**
The pinout comes first because every pin that moves changes the routing; the schematic and trace cosmetics do not depend on each other.

## 1. Pinout (decision needed)

His point: rows and columns should sit on whole ports with nothing else on them, so a slot is one or two plain port writes instead of mask juggling. He suggested swapping COL10/COL11 with BUZ_A/BUZ_B, or putting ROW0-7 on PC0-7.

Facts this is based on (datasheet AVR128DB.txt, sections 17 PORTMUX, and the current board):
- Rows already sit on contiguous pins: ROW0-5 = PC2-7 (pins 12, 13, 16-19), ROW6-11 = PD0-5 (pins 20-25). Moving them would re-route 12 nets. Not needed: they only have to be alone on their ports.
- Columns run in clock order along pins 44-48, 1-7, 10, 11. Keep that order or the fan-out crosses itself.
- TWI0 and TWI1 are identical peripherals ("primary/secondary" is only a name). TWI1 default pins are PF2/PF3 (pins 36/37), marked Fm+ like PA2/PA3.
- TCA1 can output only to ports B, C, E, G. TCA0 can output to port F: PF4/PF5 = WO4/WO5, the same split-mode high-byte channels the buzzer uses now.
- TCA0 is currently the matrix microsecond timer (single mode, needs no pin), so the two timers swap jobs: matrix -> TCA1, buzzer -> TCA0 on PORTF.

### Proposal (6 nets move, nothing else)

| Port | Today | Proposed | Pins |
|---|---|---|---|
| A | COL0,1,2,3,4,5 on PA0,1,4,5,6,7 + SDA/SCL on PA2/PA3 | **COL0-5 only** (bits 0,1,4-7); PA2/PA3 unused | 44,45,48,1,2,3 (unchanged) |
| B | COL6-9 on PB0-3 + BUZ on PB4/PB5 | **COL6-11 only** (PB0-5): COL10 -> PB4, COL11 -> PB5 | 4-9 |
| C | COL10/11 on PC0/PC1 + ROW0-5 on PC2-7 | **ROW0-5 only** (bits 2-7); PC0/PC1 unused | 12,13,16-19 (unchanged) |
| D | ROW6-11 on PD0-5, PD6/7 spare | **ROW6-11 only** (bits 0-5) | 20-25 (unchanged) |
| E | IMU_INT, BTN1, BTN2, BAT_OK | unchanged | 30-33 |
| F | crystal PF0/1, reset PF6 | + **SDA/SCL on PF2/PF3 (TWI1)**, **BUZ_A/B on PF4/PF5 (TCA0 WO4/WO5)** | 36-39 |

Net moves: COL10 (pin 10 -> 8), COL11 (11 -> 9), BUZ_A (8 -> 38), BUZ_B (9 -> 39), SDA (46 -> 36), SCL (47 -> 37). All six pins sit within a few millimetres of where the nets already go. Port F becomes the "system" port (crystal, I2C, buzzer, reset).

Firmware: `i2c_twi.c` TWI0 -> TWI1 (18 refs); `matrix.c` TCA0 -> TCA1 (18 refs, vectors TCA1_OVF/CMP0); `buzzer.c` TCA1 -> TCA0 plus `PORTMUX.TCAROUTEA` TCA0 = PORTF (16 refs); regenerate `pins.h` / `hwmap.h` with `gen_pins.py`; `matrix_map.c` assumes only ports A-D (still true). Update `mcu-pinmaps.md`, `HANDOFF.md`, `gen_schematic.py` (COL_PINS/EXTRA_PINS), `sim` if it mirrors pin names.

Options not taken: his literal swap puts the buzzer on PC0/PC1, i.e. back on a matrix port. ROW0-7 on PC0-7 re-routes all 12 row nets. Closing the gap at PA2/PA3 would shift columns 2-9 by two pins each. A 6-bit spread costs about five instructions per slot, so it is not worth a re-route.

**Revised 2026-10-29 (owner: re-routing is cheap, so do not minimise moved nets).** Chart: `docs/pinout-map.html` (five tabs). New recommendation, "whole ports, contiguous runs": COL0-7 = PA0-7, COL8-11 = PB0-3, ROW0-7 = PC0-7, ROW8-11 = PD0-3; buzzer stays PB4/PB5 on TCA1 (no timer swap); SDA/SCL -> PF2/PF3 (TWI1 default). Columns on pins 44-48,1-7, rows on 10-13,16-23, every net slides about 2 pins in the same order. Firmware: TWI0 -> TWI1 (about 18 refs) + regenerate pins.h/hwmap.h; matrix code needs no change. The 3-port variant (only A, C, D) fits exactly but splits port C in half and puts a 6-pin hole (port B) in the column run. The earlier 'small fix' (buzzer to PF4/PF5, timer swap) is superseded. Speed is not a reason for any of this: the ISR already uses OUTSET/OUTCLR masks, and the slot planner's 32-bit divide (full * lvl / 255) per lit LED is the real cost (not yet measured).

- [x] DECIDED 2026-10-29 (owner): "whole ports, contiguous runs" = revision B. Rev A archived and deprecated in `archive/boards/rev-A-2026-10-29-pre-repin/`.
- [x] DONE 2026-10-29: schematic labels (netlist differs from rev A in exactly the 26 U1 pins), `netlist.xml`, firmware pin map + TWI1 + tests (219 hw checks, 71 unit, differential scenarios, AVR build), docs, board (24 nets re-routed, DRC 0 errors / 0 unconnected), gerbers and zip re-exported. NOT done: JLCDFM re-run, quote, ordering.

## 2. Schematic clean-up (cosmetic, from the generator)

Done 2026-10-29 in `hardware/gen_schematic.py` (regenerated `LED Watch - Single Color.kicad_sch`), not committed yet, waiting for review:
- [x] S1 Short wire between every component pin and its net label or power symbol (all passives, LEDs, MCU)
- [x] S2 Power: wires from +V symbol to caps and caps to GND; VBAT as a power symbol, not a net label; one VBAT / one GND symbol on the MCU's supply pins
- [x] S3 No overlapping text: references/values vs signals, PWR_FLAG vs +3V3 (L2), notes vs parts (rough checker: 40 overlapping text pairs before, 0 now)
- [x] S4 BQ25570 circuit (L1, L2, ladders, caps) drawn as a connected circuit, not a field of labels
- [x] LIS2DW12 symbol body widened (Local.kicad_sym) so the pin names SDA/SDI/SDO and INT1 no longer collide
- [x] Check after regenerating: netlist identical to before (88 nets, same pins on every net, same components), ERC the same two warnings as before. Footprints in the PCB carry no schematic path, so the new symbol IDs do not matter.
- [x] Look it over in KiCad: owner rearranged the sheet by hand and saved it (2026-10-29). **The .kicad_sch is now the source of truth; do not re-run `gen_schematic.py` over it.**
- [x] Notes resolved in the saved schematic: 'VARIANT B' title -> 'POWER: ...'; crystal load caps confirmed (18 pF C0G, CL = (18+5)/2 + ~1 = 12.5 pF for the SC-32S); ladder note rewritten in plain words; LED-resistor and battery-polarity notes point at the bench checks. Netlist (88 nets) and ERC unchanged.
- [ ] Pinout-dependent notes (IMU 'SDA = PA2', piezo 'PB4 / PB5 ... TCA1') need a text edit once S5 is decided
- [ ] P1 README: "Requires KiCad 10" (his older KiCad would not open the files)

## 3. Board layout

- [x] B1 Programming connector: **decided to keep the 1.27 mm pogo pads** (owner's call, 2026-10-29): Tag-Connect under the solar cell would only be reachable from the back or before the cell is soldered on; the pads are reachable now. His reliability concern is noted: check the pogo jig against the pad pitch before ordering.
- [ ] B2 Power routing: no high-current traces hopping layers; follow the BQ25570 datasheet layout (LBOOST / LBUCK / VSTOR / VOUT loops)
- [ ] B3 No acute angles in copper
- [ ] B4 Traces leave pads straight out, not from the side (fine-pitch parts first). Rev B re-route: all new MCU fan-outs are straight dogbones except pad 1 (COL5_MCU) and pad 13 (ROW3), which the router exits sideways
- [ ] B5 Inner ground-plane clearance down to what JLC needs (about the minimum trace width; check their rule)
- [ ] B6 Crystal ground pour: delete it, or stitch its corners with vias
- [ ] B7 Straighten the crooked traces (low priority; works as is)
- [ ] B8 MCU bypass caps: rotate so the supply goes through the cap pad straight to the MCU pin, no inner-layer detour (check all four)
- [ ] B9 Not for rev A: MCU at the bottom, edge buttons, bigger square solar cell

## Layout rules to follow in the board pass

1. Bypass cap: the supply trace enters at the cap pad and leaves from the same pad to the chip pin. Cap within about 1 mm of the pin, no via between cap and pin.
2. Pads: traces leave straight out of the pad along its long axis, never from a side, for every part at 0.5 mm pitch or finer (MCU, BQ25570, LIS2DW12).
3. Corners: 45 degrees or arcs; no angle under 90 degrees between copper edges (this includes traces meeting pads and vias).
4. Power path (solar -> L1 -> VSTOR -> L2 -> 3V3): keep each switching loop on one layer, short, with the BQ25570 datasheet's placement.
5. Inner ground plane clearance = JLC minimum, not the default.
6. No foreign signals under the BQ25570 core (existing rule in DECISION-LOG).
7. After every pass: DRC clean, restore `.kicad_pro` if pcbnew rewrote it, re-export gerbers, rerun JLCDFM.

## Rev B follow-ups
- [ ] Owner to look over the re-routed MCU area in KiCad (reload the PCB; close and re-open the project first, KiCad rewrites the .kicad_pro)
- [ ] Optional polish pass: the router left about 175 micro-jogs (< 0.1 mm, 0.05 mm staircase) in the new copper; octo_loop.py was tried and broke a dogbone via, so it was not applied
- [ ] Re-run JLCDFM on the new zip, redo the quote (nothing saved to cart)
- [ ] Idea parked: two UART pads (TX/RX) beside the pogo row on free pins PD4-PD7 / PF4-PF5 for debug logging or a serial bootloader. A micro-USB connector was considered and not recommended (no USB peripheral on the AVR128DB, no room: the buzzer sits between the battery plugs)
- [x] (2026-10-29, later) BTN1 / BTN2 / IMU_INT / BAT_OK / SDA and everything else out of the crystal zone on all layers: the crystal block (Y1, C20, C21) was moved 1.2 mm west, see DECISION-LOG "crystal block moved".
