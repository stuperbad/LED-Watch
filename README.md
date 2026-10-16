# LED-Watch

A round LED wristwatch: 132 small LEDs (12 hours, 60 minutes, 60 seconds as three concentric rings) driven straight from an AVR microcontroller, with an accelerometer to wake it. Two variants share the idea and some code but have different hardware, so each lives in its own folder.

| Open this KiCad project | Variant | Status |
|---|---|---|
| [`single-color/hardware/LED Watch - Single Color.kicad_pro`](single-color/hardware/) | White LEDs, solar-charged (TI BQ25570 + one Anysolar cell + two small LiPo cells), AVR128DB48, piezo buzzer, 42 mm board | **Revision A is an order candidate** (JLCPCB quote $308.63 for 5 assembled boards), fully routed, DRC clean, **not ordered yet**. Firmware (alarm, weekday lights, sounds) and a browser simulator are in the folder. Start with [`single-color/README.md`](single-color/README.md). Tagged `rev-A`. |
| [`rgb/LED Watch - RGB.kicad_pro`](rgb/) | RGB LEDs that JLCPCB can assemble (common-anode), AVR128DB64, solar + LiPo + buzzer like the single-colour watch | **Placement sketch only** (2026-10-15): board size and fit worked out, no schematic or routing yet. Start with `rgb/docs/DESIGN-SKETCH.md`. The earlier RGB board (Harvatek LEDs, ATmega165PA, fully routed, not buildable: parts out of stock) is in `rgb/archive/2026-10-14 old RGB board ...` |

## Layout of the repository
```
LED-Watch/
  single-color/        the solar white-LED watch
    hardware/          KiCad project, custom footprints, production files (Gerbers, BOM, placement), schematic generator
    firmware/          AVR firmware (C), browser simulator, tests
    docs/              design notes, decision log, checklists, datasheets, research
    tools/             layout / routing / checking scripts
    archive/           older board generations of this variant
  rgb/                 the RGB watch
    LED Watch - RGB.*  the RGB project (placement sketch, 2026-10-15)
    docs/              DESIGN-SKETCH.md, pin plan, BOM candidates
    footprints/ data/ tools/ renders/   LED footprint, LED map, sketch generator, pictures
    mechanical/        outline drawings and the 3D print (of the old 43 mm board)
    archive/           the old routed RGB board and everything older
```
Both variants live side by side on `main`; branches are for work in progress. Revisions are git tags (`rev-A`, ...) rather than file names.
Code that both variants will share (LED matrix scan, RTC and mode state machine, accelerometer driver) can move to a top-level `shared/` folder when RGB firmware starts; `single-color/firmware/` is the starting point.

## Reviewing
Open `single-color/README.md` (what everything is), then `single-color/docs/REVIEW-GUIDE.md` (what to check first), and `single-color/docs/PRE-ORDER-CHECKLIST.md` (what is still open).
