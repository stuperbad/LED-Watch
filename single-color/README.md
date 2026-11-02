# LED Watch (single color, solar)

A wrist-worn clock that tells the time with 132 tiny white LEDs on three concentric rings (12 hour, 60 minute, 60 second), seven mode LEDs that double as weekday lights,
a piezo buzzer, a motion sensor to wake it, a solar cell and two LiPo cells on the back, and no case. Run by Evan Finkle with Claude (Anthropic) doing research, scripting and layout.

**Status (2026-11-02): revision C is the current design, not ordered yet.** Revision C is revision B with charging and programming moved from four pogo pads to a **USB-C receptacle** on the back (GCT USB4110, a TI BQ21040 charger, UPDI on the two SBU pins), the solar cell pad connection fixed (on revision B the cell pad was on a differently named net and not wired to the harvester), the outer LED-column arcs pulled in from the board edge, and the silkscreen reduced to the numbers, labels and a few orientation marks. Revision B (pogo pads, code word `pogo-b`) is deprecated and archived in `archive/boards/rev-B-pogo/`; revision A in `archive/boards/rev-A-2026-10-29-pre-repin/`. Nothing has been powered up.
Requires **KiCad 10** (the project files will not open in older versions).
The checklist of what is still open is `docs/PRE-ORDER-CHECKLIST.md`; the reasoning behind every decision is `docs/DECISION-LOG.md`.

| | |
|---|---|
| Board | 42.0 mm circle with two strap lugs and 2.5 mm strap slots, 4 layers, 1.6 mm, JLCPCB rules (0.10 mm track/space, 0.15 mm vias) |
| MCU | Microchip AVR128DB48 (VQFN-48), UPDI programming through the USB-C receptacle's SBU pins (1 k in series, BAT54WS clamp); no reset pad (RESET on PF6 is not wired out) |
| Power | Anysolar KXOB25-05X3TF cell -> TI BQ25570 harvester -> 2 protected LiPo pouches (JST SH plugs); USB-C 5 V -> TI BQ21040 charger (54 mA) -> the same pouches |
| Sensor / sound | ST LIS2DW12 accelerometer (wrist raise, tap), Murata PKMCS0909E4000-R1 piezo on PB4/PB5 |
| Buttons | two, symmetric, low on the face |

## Folder map

| Folder | What is in it |
|---|---|
| **`hardware/`** | **The KiCad project. Open `hardware/LED Watch - Single Color.kicad_pro`.** `LED Watch - Single Color.kicad_sch` (schematic, hand-arranged in KiCad since 2026-10-29; `gen_schematic.py` is only a reference now and would overwrite that layout), `LED Watch - Single Color.kicad_pcb` (the routed board), `footprints/LEDWatch.pretty` (custom footprints), `netlist.xml` (exported from the schematic, read by the firmware tools) |
| `hardware/production/` | what you send to JLCPCB (revision C): `LED Watch - Single Color - gerbers.zip` (+ the loose `gerbers/`), `assembly/BOM.csv` and `CPL.csv` |
| `hardware/source/` | inputs of the layout pipeline: `layout-D-hand-placement.kicad_pcb` (the hand placement the routing started from), `nets.txt`, `crystal_exclude.txt` |
| `hardware/renders/` | top and bottom pictures of the board |
| `hardware/REVISIONS.md` | the revision table (A and B archived, **C = current**); revisions are git tags, not file names |
| `firmware/` | the watch software: `c/` AVR firmware (portable core `watch.c`, hardware layer `hw/`), `sim/` browser simulator running the same logic, `HANDOFF.md` current status. Start with `firmware/HANDOFF.md` |
| `mechanical/` | 3D-printable strap/fit test models: blank board, board with big-part stand-ins, snap-on skin-side bumper (`print/` has the STL files, `README.md` the print notes, `make_models.py` rebuilds them) |
| `docs/` | `BRING-UP.md` (first power-up: how the battery and power work, measurements, programming), `DESIGN-UX.md` (modes, buttons, LEDs, sounds), `DECISION-LOG.md`, `PRE-ORDER-CHECKLIST.md`, `SCHEMATIC-GUIDE.md`, `JLCPCB-RULES.md`, `ASSEMBLY-AND-COST.md`, `mcu-pinmaps.md`, `PIN-VERIFICATION.md` (every MCU pin checked against the datasheets, run `tools/verify_pins.py`); `datasheets/`; `research/` (solar, power, MCU studies, the power workbook) |
| `tools/` | the scripts that produced and checked the layout (routing pipeline, DRC helpers, BOM/placement export). KiCad's own Python is needed for the `pcbnew` ones |
| `archive/` | older board generations and experiments (revision A, revision B with pogo pads); see `archive/README.md` |

## Regenerating things

```
# the netlist the firmware tools read (edit the schematic in KiCad; do not re-run gen_schematic.py over it)
cd hardware
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch export netlist --format kicadxml -o netlist.xml "LED Watch - Single Color.kicad_sch"

# firmware pin map and simulator face data from the schematic netlist and the board
cd ..\firmware
python gen_pins.py
"C:\Program Files\KiCad\10.0\bin\python.exe" sim\export_face_board.py

# production files from the board
cd ..\hardware
kicad-cli pcb export gerbers --subtract-soldermask --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts -o production\gerbers\ "LED Watch - Single Color.kicad_pcb"
kicad-cli pcb export drill --format excellon --excellon-separate-th --generate-map --map-format gerberx2 -o production\gerbers\ "LED Watch - Single Color.kicad_pcb"
kicad-cli pcb export pos --format csv --units mm --side both --smd-only --exclude-dnp -o production\assembly\pos_raw.csv "LED Watch - Single Color.kicad_pcb"
python ..\tools\make_bom_cpl.py production\assembly\pos_raw.csv production\assembly
```

Firmware tests (PC): `python firmware\c\test\run_diff.py` (JavaScript vs C core, frame for frame), `run_unit.py`, `run_hw.py`. AVR build: `powershell -File firmware\c\build_fw.ps1`.
Simulator: `python firmware\sim\serve.py 8765`, then open http://127.0.0.1:8765/index.html.

## How the layout was made (so the tools make sense)
Evan hand-placed the parts in KiCad (`hardware/source/layout-D-hand-placement`), then Claude's scripts in `tools/` did the symmetry tidy-up, the real footprints, the crystal ground
guard, the polar routing of the LED rings (`polar_route.py`), a grid router for the rest (`grid_route2.py`), via/stub clean-up, the ground plane (`fix_gnd_zone.py`) and the checks
(`check_pad_entry.py`, `dfm_gaps.py`, DRC). Evan then hand-edited the result in KiCad. The step by step story is in `docs/DECISION-LOG.md`.

## Related
The earlier RGB version is in `../rgb/` (never built): open `../rgb/LED Watch - RGB.kicad_pro`.
