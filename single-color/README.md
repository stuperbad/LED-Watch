# LED Watch (single colour): a bare-bones solar LED clock on a PCB

A wrist-worn clock that tells time with 132 tiny white LEDs on three concentric rings (12 hour LEDs, 60 minute LEDs, 60 second LEDs), a motion sensor to wake it,
two small solar cells and two small LiPo cells on the back, and no case. Status: **design phase. Nothing has been ordered or built.**
Run by Evan Finkle with Claude (Anthropic) doing the research, scripting and layout work. Every number in these documents is tagged VERIFIED (read from a datasheet or live listing)
or ESTIMATE/UNVERIFIED, so please keep those tags when you edit.

## What it is
| Item | Current choice | Why |
|---|---|---|
| Display | 12 x 0603 hour, 60 x 0402 minute, 60 x 0201 second white LEDs, rotated to their true angle | three sizes: hours large and inner, seconds small and outer |
| Indicators | 6 x 0402 LEDs in an arc, labelled BAT SET CFG PLAY TMR LOCK | one light per mode (see DESIGN-UX.md) |
| MCU | Microchip AVR128DB48, 6x6 mm VQFN | UPDI programming, enough pins, low sleep current (datasheet read) |
| Motion sensor | ST LIS2DW12 | 50 nA power-down, wake-on-motion, tap, in stock at JLCPCB |
| Power | 2 x Anysolar KXOB25-07X1TF in series -> TI BQ25570 harvester -> 2 x protected LiPo pouches in parallel | solar top-up; weekly or monthly charging is easy even without sun |
| Buttons | two, symmetric, low on the face | left = navigate, right = act (DESIGN-UX.md) |
| Board | 4-layer, about 43 mm circle plus two strap lugs with strap slots, 1.6 mm | shape reused from the earlier RGB board |

## Where everything is
| File / folder | What it is |
|---|---|
| `README.md` | this page |
| `PRE-ORDER-CHECKLIST.md` | every step between now and an order, with owner and status |
| `ASSEMBLY-AND-COST.md` | one-sided vs two-sided assembly, home reflow, cost estimates for the white and RGB versions |
| `POLAR-TRACES.md` | plan for a custom polar (radial + arc) trace generator |
| `DESIGN-UX.md` | modes, buttons, indicator LEDs, game ideas |
| `DECISION-LOG.md` | the running log of every decision and why (the old README) |
| `mcu-pinmaps.md`, `mcu-sensor-shortlist.md`, `mcu-research.md` | datasheet-based pin maps and part research |
| `solar-*.md`, `power-budget.md`, `Watch-Power-Calculator.xlsx` | solar and power research; the workbook is a live model with 18 tabs (LEDs, sensors, MCUs, batteries, board size, shortcomings, links) |
| `datasheets/` | datasheets used (AVR128DB, ATmega169P, LIS2DW12) |
| `schematic/` | generated KiCad schematics (`watch_usb` = pad-charged, `watch_solar` = solar) and the generator `gen_schematic.py` |
| `gen_rings.py`, `plan_board.py`, `write_pcb.py` | parametric LED-ring and board generators (placement, outline, nets) |
| `placement_test.py` | early courtyard-packing test (kept for reference) |
| `boards/` | every layout option as a PNG + KiCad board; `boards/V1_2xKXOB25_D43/` is the current candidate |

## How to regenerate the current board
```
# 1. schematic -> netlist (KiCad 10 python)
cd schematic
"C:\Program Files\KiCad\10.0\bin\python.exe" gen_schematic.py --variant solar
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch export netlist --format kicadxml -o n_solar.xml watch_solar.kicad_sch
cd ..
# 2. plan the layout (system python: numpy, shapely, matplotlib)
python plan_board.py --cell KXOB25 --cell-count 2 --diameter 43 --mcu-pkg qfn --safety 0.5 --btn-style bottom --ind-style arc --ind-count 6 --auto-cell-y --batt-conn jst-side --mcu-side front --battery tc70 --batt-count 2 --name V1_2xKXOB25_D43
# 3. write the KiCad board with nets
"C:\Program Files\KiCad\10.0\bin\python.exe" write_pcb.py V1_2xKXOB25_D43
# 4. route (about 25 minutes): export Specctra, run freerouting, import the session (see PRE-ORDER-CHECKLIST.md section D)
```
Key knobs of `plan_board.py`: `--diameter` (0 = smallest that fits), `--band` (LED band width), `--hr/--min/--sec` (LED sizes), `--cell`, `--battery`, `--safety` (extra edge margin), `--slot-clear`, `--btn-x`, `--ind-count`, `--all-front`, `--back-strip`.

## Known problems right now (honest list)
- The routed board has 6 unrouted connections and about 270 DRC errors against KiCad's default rules (hole and edge clearance). Rules have not yet been set to JLCPCB's real limits.
- The schematic and board are slightly out of sync: the schematic still shows the TQFP MCU footprint, a two-pin solar connector, and one battery plug; the board has the VQFN MCU, four solar-cell contact pads, and two plugs.
- The BQ25570 uses a stand-in footprint; the real RGR package land pattern still has to be built and checked against TI's drawing.
- The TinyCircuits cell size is from a search summary; the Anysolar cell had no live stock when checked.
- Brightness drops as the battery falls toward 3.0 V with the current 150 ohm resistors (the white LEDs need about 2.8 V).
- Nothing has been checked against JLCPCB's assembly rules with the real placement file (arbitrary-angle LED rotation in particular).

## Related
The earlier RGB version lives in `Desktop\LED-Watch` (132 RGB LEDs on a rectangular-ish 43 x 50 mm board, never built). We want to revisit the RGB direction later; see `POLAR-TRACES.md`.
