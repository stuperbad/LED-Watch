# LED Watch — Single-Color (white) version
Started 2026-10-05. Separate from `Desktop\LED-Watch` (the RGB design), which is left alone.
Nothing designed yet: this folder holds the brief and open decisions. Next step is to settle these, then iterate.

## Evan's goals for this version
- White LEDs only, individually placed around the dial like a clock face.
- LED rotated to its true radial angle on the clock (5° increments = 72 positions; a clock has 60 minute/second positions + 12 hour positions on concentric rings).
- Three LED sizes: **small = seconds, medium = minutes, large = hours**.
- Don't use 0201 LEDs (too small); something like 0402/0603 — see sizes below.
- Smaller overall board if possible (RGB board is 42.87 x 50.28 mm with strap lugs).
- Rings should be **parametric**: ring radii, LED sizes, rotation computed from a script, so the minimum spacing that still routes can be found automatically, instead of the locked hand-laid rings of the RGB design.
- A smaller-pin-count processor than the ATmega165PA (54 I/O) is acceptable/needed.
- Must be assemblable: JLCPCB in-stock parts preferred (a research agent is checking stock), otherwise a US assembler quote.

## Key facts and constraints
- 132 LEDs total if every position gets one (60 seconds + 60 minutes + 12 hours). In the RGB design the same 132 sit in a 22-row x 6-column multiplex.
- White LED Vf is ~2.8-3.2 V — barely works from a 3 V coin cell; fine from a LiPo (3.0–4.2 V). Needs a real current calculation (and resistors or a constant-current driver) — the RGB design had no series resistors; don't repeat that.
- Rotation: KiCad footprints accept any angle. Fabs place parts at any angle from the placement file, but need clean rotation data and the part's pin-1 orientation; some houses' pick-and-place charge extra or need confirmation for non-90° angles. 5° steps is a question to ask the assemblers (in the RFQ emails: not yet added).
- Package sizes (imperial / metric / mm): 0402 / 1005 / 1.0x0.5, 0603 / 1608 / 1.6x0.8, 0805 / 2012 / 2.0x1.25. (The RGB board's KiCad "LED_0201_0603Metric" is 0.6x0.3 — the thing to avoid.)

## Decisions made by Evan (2026-10-05)
- **Multiplexing from the MCU is the default** (Evan's principle, 2026-10-05: keep it simple, no extra chip). A matrix-driver chip stays only as a FALLBACK if pin count/space/brightness becomes a problem. Rough need: ~23 GPIO for a 132-LED grid (about 11 rows x 12 columns) + one resistor per column, plus crystal, I2C sensor, buttons, charger status -> likely a ~44-pin class MCU, not the 64-pin one.
- **Battery: LiPo (rechargeable) is the main plan.** Coin cell may stay as a prototype option; "all of it is in play for the prototype".
- **Possible solar**: a small solar panel in the centre of the front face, electronics on the back -> needs a LiPo charger IC with a solar/low-power input (and probably a fuel gauge or at least charge status). Not committed; design should leave room for it.
- **Motion sensor stays** (BMI270 or equivalent, e.g. for wrist-raise). Doesn't need to run all the time -> use the sensor's low-power/interrupt wake mode so the MCU can sleep.
- White LEDs only; three sizes (seconds small, minutes medium, hours large); parametric rings.

## Still open (need Evan)
1. Drive method for ~132 LEDs (decided: multiplex, option A; B/C are fallbacks):
   - A. Multiplexed/charlieplexed straight from MCU pins (needs ~24+ I/O; simple, few parts, but constant resistors/current issues and flicker design).
   - B. I2C/SPI LED-matrix driver IC(s) with constant-current outputs (e.g. IS31FL37xx-class 144–192 LED matrix drivers) + a small MCU (8–32 pins). Fewer pins, handles current, and shrinks the MCU; costs a driver chip and layout around it.
   - C. Shift registers / constant-current sink drivers + small MCU.
2. MCU choice (depends on 1; also what's in stock at JLCPCB / DigiKey). Keep a 32.768 kHz RTC crystal on the right pins this time.
3. (answered above: keep the motion sensor)
4. (answered above: LiPo; solar optional)
5. Overall size: target diameter, strap-lug style.
6. Do hours, minutes, seconds share one ring each (3 rings) or do all 60 minute/second positions use two interleaved rings?

## Plan
1. Settle decisions above.
2. Write a parametric generator (Python for KiCad's pcbnew) that places LEDs on rings with radial rotation, given ring radii and LED sizes; compute minimum ring radius from pad/courtyard spacing.
3. Auto-route trial; check DRC with the fab's limits (JLCPCB 4-layer or 2-layer if possible).
4. Generate Gerbers/BOM/CPL; quote at JLCPCB (should be easier with common, in-stock LED/MCU parts) and a US assembler.

## References
- RGB design and lessons: `Desktop\LED-Watch\fab-rfq\OPEN-ISSUES.md`
- JLCPCB part alternatives (research in progress): `Desktop\LED-Watch\fab-rfq\jlc-alternatives.md`

## Progress log
### 2026-10-05 — first parametric ring layout (LED placement only; no routing, no MCU yet)
- `gen_rings.py` (run with KiCad's python) builds `rings.kicad_pcb`, `rings_cpl.csv`, `rings_report.txt`, preview `rings_preview.png`.
- CORRECTION: a clock has 60 positions, so the true angle step is **6 degrees** (minutes/seconds) and 30 degrees (hours) — not 5 (that would be 72 positions). No rounding needed; the arbitrary-angle JLCPCB test still applies.
- Geometry: LED pad axis is radial (pad 1 cathode inward, pad 2 anode outward); KiCad rotation = 90 - clock angle. Only the LED's short side (pad width) limits spacing around a ring.
- Sizes (KiCad stock footprints): seconds 0402, minutes 0603, hours 0805. Defaults: 0.5 mm copper gap between neighbours around a ring, 0.8 mm radial gap between rings (for traces), 1.0 mm edge margin.
- Ring order compared (6 permutations): inner->outer **H,S,M = 32.15 mm board** (best); H,M,S 36.9; S,H,M 39.1; S,M,H 39.5; M,H,S and M,S,H 44.2. Radii: hours 3.67, seconds 10.89, minutes 13.85 mm. For reference the RGB watch is 42.9 x 50.3 mm.
- Tunables: `--tang-gap`, `--rad-gap`, `--center-keepout` (reserve space for a solar panel), `--edge-margin`, `--sec/--min/--hr` sizes, `--order`.
- NOT done yet: electrical net design (which LED in which matrix row/column), MCU/sensor/charger placement (back side), routing, strap lugs, board stackup, DRC against JLCPCB limits.

### 2026-10-05 (later) — corrected: rings packed OUTSIDE-IN, order H (inner, largest) -> M -> S (outer, smallest)
Evan's correction: seconds on the outer ring; LEDs pushed out against the board edge to maximize the central component space; hours must not crowd the middle.
- `gen_rings.py` now packs rings from the board edge inward (`solve_outward`). Default order H,M,S; `--diameter` fixes the board size (rings pushed to the edge), `--diameter 0` finds the smallest feasible.
- Smallest feasible at 0.5 mm LED gap / 0.8 mm ring gap: **36.88 mm board; 17.96 mm-diameter free centre** (a 12.7 mm square fits). Ring radii: hours 10.41, minutes 13.86, seconds 16.66 mm.
- Gap sensitivity (min board / free centre dia): 0.3 gap 33.1/14.1, 0.4 gap 35.0/16.1, 0.5 gap 36.9/18.0, 0.6 gap 38.8/19.9 (ring gap 0.8). Diameters below the minimum are infeasible (the 60 minute LEDs set the limit); larger boards give a larger free centre (38 mm -> 19.1, 40 -> 21.1, 42 -> 23.1).
- Solar panel: parked by Evan ("save that question"); small square/rectangular panels were sourced earlier. The free centre gives a benchmark (an ~12-18 mm square fits at the minimum size).
- Multiplexing plan (Evan): mix of RADIAL and CONCENTRIC traces, with layer-to-layer jumps (vias) at each LED space, like the RGB design's rings. Not started.

### 2026-10-05 (later still) — LED sizes, fabrication, solar, and the wiring plan
Evan's decisions/notes: open to smaller LEDs (biggest 0603, down to 0201); this board will be fabricated/assembled by a fab (not hand-built); size is "not critical" — don't over-minimise the diameter; interior components (MCU etc.) may be shaped around the free centre; wants a rechargeable on-board (non-swappable) LiPo, a power manager, and a solar cell if feasible; wants documentation of why each direction was chosen; wants the design PARAMETRIC (padding/spacing changes should be a quick regenerate, with routing re-done).
- LED size sets, board diameter / free-centre diameter (mm) at 0.4 and 0.5 mm LED gap: H0805/M0603/S0402 35.0/16.1 & 36.9/18.0; **H0603/M0402/S0402 28.2/11.8 & 30.1/13.7**; H0603/M0402/S0201 27.2/11.8 & 29.2/13.7; H0402/M0402/S0201 27.2/13.6 & 29.2/15.5; H0603/M0603/S0402 35.0/16.9 & 36.9/18.8; H0402/M0201/S0201 22.2/9.5 & 24.1/11.4.
- 0201 white LEDs DO exist: Xinglight XL-0201UWC (LCSC C965789, ~6,200 in stock, Vf 2.7 V, 0.65x0.35 mm, 5 mA test) and Kingbright APG0201VWF-A1-5MAV (typ 320 mcd @5 mA, 140 deg). Brightness and placement difficulty at 0201 still to weigh; 0402 stocked in far larger numbers.
- Matrix plan: 12 columns (one per 30-degree sector, each a RADIAL trace) x 11 rows (per sector: 1 hour + 5 minute + 5 second LEDs; row nets run CONCENTRICALLY with vias hopping layers at LED spaces) = 23 GPIO, ~12 series resistors, only ~3 LEDs lit at once. Alternative: charlieplex of 12 pins (12*11 = 132 LEDs).
- Source of truth to build next: a parametric design description (ring sizes/gaps, LED->row/column map, parts) -> generates schematic, PCB placement, netlist; routing (freerouting is installed) re-run after any change.
- Research in progress (agents): `solar-power-research.md` (PV cells, energy budget, harvester/charger ICs, LiPo cells) and `mcu-research.md` (MCU/RTC/IMU candidates and pin budget).

### 2026-10-06 — schematics (two variants) generated and verified
- `schematic/` has the parametric generator and two KiCad schematics: Variant A (pad/USB-charged LiPo) and Variant B (solar: BQ25570 harvester + LiPo). 132 LEDs wired as a real 12 x 11 matrix; MCU = AVR128DB48; IMU = BMI270. Rationale and every placeholder are in `schematic/DESIGN-NOTES.md`.
- Evan's cells (KXOB081K06TF, 23 x 25 mm, 105.9 mW @ 1 sun) are too big for the free centre of the earlier boards; layout around a 23 x 25 mm rectangle tested: 51.3 mm board with four arc segments (depth 5.0-6.0 mm) for chips (`rings_solar_rect_preview.png`).
- Decision pending: MCU/IMU defaults were assumed (AVR128DB48, BMI270) so schematics could be built; all changeable by re-running the generator.

### 2026-10-08 — live power calculator
- `Watch-Power-Calculator.xlsx` (built by `build_power_workbook.py`; 1,613 live formulas, 7 tabs: Inputs, Lists, LED types, Every LED, Solar, Power budget, Notes). Change the yellow cells; PWM duty per LED type, time shown (lights the 3 matching LEDs), wakes/day, wake sensor, battery, solar cell and profile all flow through to daily energy and battery life. Verified against `power_budget.py` (all outputs match; no formula errors).
- Findings: the always-on wake sensor (BMI270 ~1.0 mWh/day) outweighs a dim 3-LED display (~0.45 mWh/day at 60 wakes); dimming PWM from 100% to 5% only moves battery life 130 -> 182 days with the BMI270 but 196 -> 346 days with a BMA400.
- DESIGN FLAG: with the placeholder 150 ohm column resistor and ~2.7 V white LEDs, on-current is ~8 mA at 4.2 V, ~4.7 mA at 3.7 V, ~2 mA at 3.3 V and ZERO at 3.0 V (battery minus LED Vf minus pin drops). Brightness will swing ~4x over the battery range and the LEDs go dark near 3.0 V. Needs firmware brightness compensation (measure VDD) and/or a lower-Vf LED / different drive scheme.

### 2026-10-08 (later) — special mode (fluid/gravity/tilt game) added to the calculator
- Evan wants 1-2 min/day of an IMU "fun mode" (fluid that flows with gravity, tilt game) plus a cheap wake. A gravity sim only needs an ACCELEROMETER. BMI270 datasheet Table 6 (VERIFIED, VDD 1.8 V): suspend 3.5 uA, accel-only low-power 4-10 uA, accel-only normal 210 uA, A+G normal 685 uA, advanced features +3 uA. BMA400: sleep 160 nA, low-power 850 nA, normal 14.5 uA.
- Calculator default (2 min/day, 40 LEDs lit, 11 rows scanned, 70% duty, BMA400 normal): game costs ~1.84 mWh/day (~0.9 mWh per minute), mostly LEDs; total ~4.0 mWh/day with a BMI270 wake (92 days) or ~3.0 with a BMA400 wake (~122 days).
- DESIGN FLAG: lighting a full 12-LED row at 4.7 mA each pulls ~56 mA through ONE MCU row pin (limit assumed 20 mA; AVR absolute max reportedly ~40 mA, UNVERIFIED) -> game mode needs row-driver transistors (or lower on-current / fewer LEDs per row). Clock mode (1 LED per row) is fine.

### 2026-10-08 (late) — parametric board planner + 4 cell options
- `plan_board.py` (system python) + `write_pcb.py` (KiCad python): outline = circle + two strap lugs/slots copied from the RGB board (all parameters), rings H0603 / M0402 / S0201 (three sizes), LED band width is its own parameter (`--band`), diameter adjustable (`--diameter`, 0 = smallest that fits). BOM read from the schematic netlist (`schematic/n_*.xml`), real courtyards from KiCad footprints, packed onto front (around the cell) and back (around the battery). Output in `boards/<name>/` (png, plan.json, .kicad_pcb: placement only, no nets/routing).
- Results (80 mAh battery): no cell 35.5 mm (MCU front); KXOB25-07X1TF 11.35x8 36.0 mm (MCU back); AM-1606C 40.5 mm; KXOB081K06TF 23x25 50.0 mm. KXOB25 with other batteries: 35 mAh 36.0, 50 mAh 38.5, 155 mAh 46.0; forcing the MCU onto the front costs 47.5 mm.

## 2026-10-12: BQ25570 resistor ladders re-picked for JLCPCB stock
7.32M / 4.22M / 8.25M had 4 / 5 / 24 pieces in stock at JLCPCB (5 boards needs 10 / 5 / 5, 200 boards far more).
Re-derived with the datasheet equations (7.3.3, 7.3.4, 7.3.6; VBIAS 1.21 V) using 1 % 0402 values stocked in the thousands:
- VBAT_OV  = 1.5 x 1.21 x (1 + R50/R51) = 4.120 V with R50 6.49M, R51 5.11M (sum 11.6M, inside the 11-15M window)
- BAT_OK falling = 1.21 x (1 + R53/R54) = 3.310 V, rising = 1.21 x (1 + (R53+R52)/R54) = 3.785 V with R52 1.47M, R53 6.49M, R54 3.74M
- VOUT = 1.21 x (1 + R55/R56) = 3.310 V with R55 6.49M, R56 3.74M
LCSC parts: 6.49M C172111 (9134 in stock), 5.11M C166448 (7474), 3.74M C477705 (9807), 1.47M C477211 (9410). Four unique values instead of six.
Files changed: schematic/gen_schematic.py (+ regenerated watch_solar.kicad_sch, n_solar.xml), board value fields, tools/make_bom_cpl.py.
