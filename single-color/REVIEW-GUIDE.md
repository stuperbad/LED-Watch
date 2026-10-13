# Review guide: single-colour solar LED watch, board Y43 (2026-10-12)

Please give everything a once-over before the JLCPCB order is placed. Nothing has been ordered yet.

## Where things are
| What | File |
|---|---|
| Final board (KiCad 10, true arcs) | `boards/Y43/Y43_final.kicad_pcb` |
| Fab files (Gerber + drill, uploaded to JLCPCB for the quote) | `boards/Y43/Y43_final_gerbers.zip`, `boards/Y43/fab/` |
| Assembly files (BOM with LCSC numbers, placement list) | `boards/Y43/asm/BOM.csv`, `boards/Y43/asm/CPL.csv` |
| Renders and last full DRC (0 errors, 0 unconnected, 6 harmless via warnings) | `boards/Y43/final_top.png`, `final_bottom.png`, `final_all_drc.json` |
| What every part is for | `SCHEMATIC-GUIDE.md` |
| Schematic (generated; source of truth is the script) | `schematic/watch_solar.kicad_sch`, `schematic/gen_schematic.py` |
| JLCPCB rules we design to (quoted from their page) | `JLCPCB-RULES.md` |
| Pre-order checklist and open items | `PRE-ORDER-CHECKLIST.md`, `DECISION-LOG.md` |
| Firmware pin map / simulator | `firmware/` |

## Current quote (JLCPCB, 5 boards, assembled both sides): $288.74 before shipping
Black solder mask, lead-free HASL, 1.6 mm, 4 layers, 0.15 mm vias (the via size is the expensive option: +$34). Board $75.75 + assembly $212.99.

## What to check, most valuable first
1. **BQ25570 resistor ladders (R50-R56).** Re-picked on 2026-10-12 so JLCPCB has them in stock (details in `DECISION-LOG.md`). Please recompute with datasheet equations 2, 3, 4, 5 (VBIAS 1.21 V): over-voltage 4.12 V, BAT_OK falls 3.31 V / rises 3.78 V, VOUT 3.31 V.
2. **LCSC part numbers** in `asm/BOM.csv`: package, value, ratings (inductor saturation current for the BQ25570, 22 uF cap voltage rating, switch footprint).
3. **Part rotations** (`asm/CPL.csv`, KiCad convention). JLCPCB's own preview looked right but each part was not individually verified, especially U1, U2, U4, Y1, the JST plugs, and the LEDs (polarity!).
4. **LED colour.** The 0402 LED (XL-1005UWC, C20613596) is listed at 15,000 K by JLCPCB (another listing of the same part says 4,000-8,000 K); the 0201 LED is 5,500-6,000 K. They may look different in colour. Not yet resolved.
5. **Battery plug polarity** (J1/J1B: pin 1 = +) against the TinyCircuits cells, and the solar cell pad polarity (SC1+/SC1-) against the real KXOB25-05X3TF.
6. **Crystal circuit**: 18 pF load caps and the guard layout (AVR128DB datasheet 4.5.1).
7. **Thermal pad / via-in-pad rules** for the VQFN parts, and the 0.10 mm track / 0.10 mm space we use (JLCPCB minimum is 0.09).

## How the board was made (so you can rebuild it)
`build_board_b.sh` (placement + polar LED copper), then `tools/add_stubs.py --via` (MCU fan-out), `tools/grid_route2.py` (our own router, rip-up and reroute), `tools/merge_new.py` (onto the true-arc board). `tools/make_bom_cpl.py` writes the assembly files. Old layout experiments are not in this repo (they are regenerable).

> Paths in this guide are relative to the `single-color/` folder of the repository.
