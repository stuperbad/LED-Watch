# Watch simulator (browser)

Interactive model of the single-colour solar LED watch. It runs `watch_core.js` (the firmware logic, written C-style so it ports to the AVR128DB48) against the **real board data**: LED positions from `boards/Y43/plan.json`, row/column wiring from the netlist, MCU pin names from `pins.h`.

## Run
```
cd firmware/sim
python serve.py 8765
```
then open http://127.0.0.1:8765/index.html (opening index.html directly from disk also works).

## Regenerate the data after a schematic or board change
```
python firmware/gen_pins.py          # pins.h + ledmap.h
python firmware/sim/export_face.py   # face_data.js (pass a board dir to use another layout)
```

## What you can poke
- **Buttons**: click the L/R buttons on the face, the big buttons, or Z/X (or arrow keys). 1 s = long press, both 2 s = lock. Macros for long press / lock.
- **Accelerometer**: tilt pad (drag toward the edge you lift, or WASD), shake, free-fall, raise wrist (with adjustable strength vs. the wake-sensitivity setting), double tap, optional phone tilt.
- **Environment**: simulated-clock speed (1x to 600x), battery level (sets VDD), solar input, ambient light; optional battery drain/charge from the simulated current.
- **Physical model**: the status panel shows per-LED current vs VDD, the scan plan (slots per frame, 10 mA row-sink limit), how much brightness is lost when too many LEDs are lit, average LED power and energy used. "Slow-motion scan" shows one row slot at a time with the real ROW/COL port pins.

## Files
- `watch_core.js` - state machine, modes, games, scan-plan/brightness model (no DOM).
- `index.html` - UI, accelerometer/battery models, drawing.
- `export_face.py` -> `face_data.js` - board geometry + matrix map + pin names.
- `watch_sim.py` - older one-shot PNG renderer.

## Assumptions to check against hardware
LED current model (1.6 mA at 3.0 V to 4.8 mA at 4.2 V, from the handoff), MCU 1.2 mA awake / 4 uA asleep (guess), LiPo voltage curve, battery 140 mAh, solar-to-battery efficiency 80 %.

## Board data from the real board (Y42)
`python firmware/gen_pins.py` (pins.h, hwmap.h, ledmap.h, from the schematic netlist `schematic/n_solar.xml` + the board file for the indicator order) and
`"C:\Program Files\KiCad.0in\python.exe" firmware/sim/export_face_board.py` (face_data.js straight from `boards/Y43/Y42_routed_v4.kicad_pcb`) replace `export_face.py` (which reads the old `plan.json`).
Regenerate the netlist first when the schematic changes: `kicad-cli sch export netlist --format kicadxml -o schematic/n_solar.xml schematic/watch_solar.kicad_sch`.

## Sound
The Sound panel plays `out.tone` (Hz) from the core as a square wave (WebAudio; click the page once so the browser allows sound). "Alarm test" sets the alarm for the next minute and moves the clock to :55. The CFG settings 11 (key beeps) and 12 (game sounds) decide what beeps.
