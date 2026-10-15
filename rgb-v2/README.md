# LED Watch - RGB v2 (sketch)

A placement study for a second-generation RGB watch that JLCPCB can assemble: the single-colour watch's power, buzzer, motion sensor and buttons, with 132 common-anode RGB LEDs and an AVR128DB64 for the extra I/O. **Not a design yet**: no schematic, nothing routed.

Read **`docs/DESIGN-SKETCH.md`** first. Open **`hardware/sketch.kicad_pcb`** in KiCad to look at the placement; the pictures are in `renders/`.

| | |
|---|---|
| `docs/DESIGN-SKETCH.md` | the result: board size, what goes where, the LED choice and its brightness warning, how the matrix is driven, risks, next steps |
| `docs/pin-plan.csv`, `docs/BOM-candidates.csv` | MCU pin plan; new/changed parts with LCSC numbers and stock (2026-10-15) |
| `hardware/` | `sketch.kicad_pcb`, the new LED footprint in `footprints/RGBv2.pretty`, the LED-to-position map `led_matrix.csv`, ring data from the old board `old_ring.json` |
| `renders/` | `top.png` (front) and `bottom.png` (back, seen from behind) |
| `tools/` | `build_sketch.py` makes the sketch (KiCad's Python), `extract_old_ring.py` and `check_pad_corners.py` |

Regenerate: `"C:\Program Files\KiCad\10.0\bin\python.exe" tools\build_sketch.py` (options `--R 22 --ring 15,17.5,20`).
