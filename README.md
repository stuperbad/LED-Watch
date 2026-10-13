# LED-Watch

A round LED wristwatch: 132 small LEDs (12 hours, 60 minutes, 60 seconds as three rings) driven straight from an AVR microcontroller, with an accelerometer to wake it. Two variants share the idea and some code but have different hardware, so each lives in its own folder.

| Folder | Variant | Status |
|---|---|---|
| [`single-color/`](single-color/) | White LEDs, solar-charged (BQ25570 + one Anysolar cell + two small LiPo cells), AVR128DB48 | Board `Y43` is fully routed (DRC clean) and quoted at JLCPCB; **not ordered yet**. Gerbers, BOM, placement files, schematic, docs, datasheets, firmware pin map and simulator are all in the folder. Start with [`single-color/README.md`](single-color/README.md) and [`single-color/REVIEW-GUIDE.md`](single-color/REVIEW-GUIDE.md). |
| [`rgb/`](rgb/) | RGB LEDs, the original KiCad work (schematic, several PCB iterations, Gerbers used to get an instant quote) | Work in progress. There is no RGB firmware in this repository yet. The old README is [`rgb/README.md`](rgb/README.md). |

## How the repository is organised (and why folders, not branches)
Both variants live side by side on `main`. Branches are used for work in progress (for example `firmware-matrix-scan`) and are merged back, rather than keeping each variant on a long-lived branch of its own: two long-lived branches drift apart, and anything they share (firmware drivers, the LED ring generator, the scripts) would have to be merged by hand forever.

- Each variant keeps its own BOM, schematic, board files and documentation inside its folder.
- Code that both variants use (for example the LED matrix scan, the RTC and mode state machine, the accelerometer driver) moves to a top-level `shared/` folder when the RGB firmware starts; the single-colour firmware in [`single-color/firmware/`](single-color/firmware/) is the starting point.
- Datasheets live in `single-color/datasheets/` for now. Anything RGB-specific can go in `rgb/datasheets/`.

## Reviewing
Teammates: open `single-color/REVIEW-GUIDE.md`. It lists what to check first and where each file is.
