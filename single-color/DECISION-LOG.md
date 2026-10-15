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

### 2026-10-13 — layout D, buzzer, 42 mm board, strap slots, silkscreen (working files `boards/Y43/Y43_mockD_pogo*.kicad_pcb`, placement only, not routed)
- **Buzzer:** one 9 x 9 x 1.9 mm Murata PKMCS0909E4000-R1 piezo (LCSC C910763, lifecycle unclear) on the BACK, left strip, driven in opposite phase from PB4 (pad 8, net /BUZ_A) and PB5 (pad 9, net /BUZ_B). Murata curve: 65 dB min at +-1.5 V / 4 kHz, typical 72 dB at 4 kHz, about 85 dB near 8 kHz; usable about 1.5-10 kHz. Timer-pin/anti-phase mapping of PB4/PB5 not yet verified. Fallback: 5 x 5 mm magnetic (FUET-5020, about 110 mA) between the buttons with U2 on the back.
- **Back layout:** two LiPo outlines (User.2) with margin envelopes (User.3: x 90.75-109.25, y 79.5-97.5 and 102.5-120.5): nothing on the back inside them. U4 + inductors + support parts in the 5 mm band between them; plugs J1/J1B and the piezo in the left strip. Support parts 2-9 mm from their U4 pins (band-limited).
- **MCU:** U1 rotated 180 degrees (best of four for ROW-pin wiring), crystal block low-left with its own F.Cu ground guard (exclusion box for the router in `boards/Y43/crystal_exclude.txt`), one decoupling cap per supply pin pair on the front (1.3 / 1.8 / 3.8-5.3 mm).
- **Programming pads:** Tag-Connect replaced by a 1.27 mm pogo row (RESET, VDD, GND, UPDI = Microchip UPDI v2 order, RESET on PF6) + 2 plated 0.3 mm guide holes, on the back at 3 o'clock. Only UPDI/VDD/GND are needed to program; RESET is for high-voltage recovery.
- **Indicators:** seven (SET TMR ALM BAT FUN CFG LCK), IND7 = ROW11/COL6.
- **Board diameter 43.5 -> 42.0 mm:** LED ring moved 0.75 mm radially inward (angles unchanged), outline regenerated; ring-to-edge margin unchanged (0.74 mm). Buttons moved 0.45 mm inward. Limits: solar cell pads (radius 12.6), buttons 12.8, C10 13.1. LED-only minimum would be 36.9 mm. Ring copper (polar) must be regenerated for the new radii before routing.
- **Strap slots:** 19.75 x 2.5 mm (was 1.77); test with a real band before ordering (3.0 mm is the fallback).
- **Silkscreen** (working file now `Y43_mockD_pogo8.kicad_pcb`): 0.8 mm text, unrotated. Hour numbers 12/3/6/9 just inside the hour LEDs (3 and 9 centred on the 3-9 axis). Minute numbers 0..55 between the minute and second rows, in the angular gap clockwise of the 5-minute LED. WEEKDAY on the mode LEDs: the labels read SET-S TMR-M ALM-T BAT-W FUN-T CFG-F LCK-S (week starts Sunday; 0.5 mm-wide characters): the day is shown by lighting that mode LED (firmware/DESIGN-UX to follow; replaces the old 1-7 LED bar on the outer ring). Text height 0.8 mm is below JLCPCB's stated 1.0 mm legibility limit.
- Marker layers for the layout work: User.4 MCU/crystal decoupling, User.5 BQ25570 support, User.6 IMU decoupling, User.7 dummies, User.8 programming pads, User.9 new parts, User.10 moved front->back.

### 2026-10-13 (evening) — Y42 routed (`boards/Y43/Y42_routed.kicad_pcb`, 42.0 mm board)
- Pipeline for this board: `Y43_mockD_pogo8` (hand placement) -> `tools/crystal_left.py` (left-side crystal) -> `polar_route.py` (ring rows/columns; arc + poly versions) -> `tools/add_stubs.py --via` (MCU dogbones) -> `tools/grid_route2.py` (new `--via-pad-area`: no via in or touching an SMD pad under 1 mm2) -> `tools/merge_new.py` onto the arc board -> `tools/undangle.py` -> zone refill. Crystal exclusion box for the router: `boards/Y43/crystal_exclude.txt` (91.5,90.6,95.3,95.8). Net order: `boards/Y43/nets42.txt`.
- Fixes needed on the way: flank/dummy resistors must be translated along the hour axis when the ring shrinks (`tools/fix_flank.py`); back parts in the ring band (J1, J1B, J2) had to be nudged clear of the polar vias/lanes (`tools/fix_back_ring.py`): J1 (86.8, 92.1), J1B (86.5, 109.0), J2 (113.65, 100.0).
- Result: DRC (project rules) 0 errors, 0 unconnected; warnings only for the placeholder piezo footprint silkscreen. 295 vias (0.3 / 0.15 mm), tracks 0.10 / 0.12 mm, 3 vias in SMD pads (the thermal pads of U1 and U4 only), nothing but the crystal nets and ground inside the crystal exclusion box.
- Still open before an order: real land pattern for the Murata piezo (BZ1 is a generic placeholder), schematic/netlist sync (IND7, /BUZ_A, /BUZ_B on PB4/PB5, RESET pad on PF6, removed dummies), BOM + placement files, new quote, strap-slot test with a real band, PB4/PB5 timer mapping for the buzzer.
- **Footprint audit and Y42_routed_v2 (same evening):** the first routed board still had a placeholder footprint for the piezo (BZ1) and a Tag-Connect name on the programming pads (J2); that should have been fixed before routing. Checked against the datasheets: U1 (Microchip C04-2494: pads 0.20 x 0.85, spacing 5.90, centre pad 4.20) OK; U4 (TI RGR0020A: pads 0.24 x 0.60, 3.30 span, thermal pad 2.05) OK (the old "stand-in" note is obsolete); U2 uses KiCad's stock LGA-12 2 x 2 (pads 0.375 x 0.35 vs ST's 0.25 x 0.275 terminals; ST TN0018 not in the repo, not checked). BZ1 is now the real Murata land pattern (two pads 1.3 x 3.4 at +-4.35, courtyard 10.4 x 9.4, sound slots on the two edges without terminals: keep open) in `footprints/LEDWatch.pretty`; J2 saved there as `UPDI_Pogo_1x4_P1.27mm_2Guide`. Whole board rerouted: `boards/Y43/Y42_routed_v2.kicad_pcb` (supersedes `Y42_routed`), DRC 0 errors / 0 unconnected (2 warnings: library table does not list LEDWatch). Not yet checked against the real LCSC parts: LED pads (C965789 / C20613596 / C2290), crystal C97606, switch C72443.

### 2026-10-14 — Y42_routed_v4: every pad/via landing checked, silkscreen dashes removed
- New check `tools/check_pad_entry.py` (KiCad python): for every track end touching a same-net pad it measures how deep the end sits inside the pad; a full-width joint needs depth >= width/2. Also flags track ends that touch a via off-centre and vias that only partly overlap a pad.
- On `Y42_routed_v2` (as saved 2026-10-14 01:17, incl. Evan's hand fixes) it found 148 shallow pad landings on 130 pads (most ended 0.01-0.03 mm OUTSIDE the pad edge: the grid router stopped on its 0.05 mm grid at the pad edge/corner, so only part of the round track end overlapped the pad), 159 track ends kissing a via off-centre, and 3 vias half on a pad (C54.2, SC1-, U4 thermal pad). DRC passed all of these because the copper does touch.
- Fix (`check_pad_entry.py --fix`): a short stub, same net/width/layer, from each shallow end to the pad centre (or via centre). Re-check: 0 unresolved. DRC 0 errors / 0 unconnected (same 2 library-table warnings as before).
- Silkscreen: SET-S TMR-M ALM-T BAT-W FUN-T CFG-F LCK-S -> "SET S", "TMR M", ... (`tools/silk_nodash.py`).
- In2 ground zone outline rebuilt from the board outline and all zones refilled (`tools/fix_gnd_zone.py`, as in v3).
- Outputs: `boards/Y43/Y42_routed_v4.kicad_pcb` (supersedes v2/v3), `fab42/Y42_routed_v4-*` + `Y42_routed_v4_gerbers.zip` (silk with soldermask subtracted, as v3), `asm42/` BOM/CPL regenerated from v4 (SC1+/SC1- are hand-soldered cell pads, not in the CPL).
- Silkscreen thickened (same day): every silk stroke raised to 0.15 mm (23 board texts, 308 footprint lines, 1 footprint text; `tools/silk_thicken.py`), gerbers re-exported. JLCDFM on v4: silk line width 0 danger (was 7); remaining reds are DFM-tool defaults or same-net items: trace width 0.10 mm (JLCPCB multilayer min 0.09), via annular ring 0.075 mm (0.15/0.30 vias, within JLCPCB's via spec; choose "Min via hole size 0.15 mm" when ordering), pad spacing / via-to-pad / mask-exposing-trace (all same-net via-next-to-pad, checked with `tools/dfm_gaps.py`: no different-net pad gap under 0.1 mm), silk-to-pad/hole (silk is clipped at mask openings; vias are tented).
- Mode labels on two lines (same day, `tools/silk_twoline.py`): mode name on top (0.85 mm high, 0.60 mm char width, 0.15 mm line, centre y 105.80) and the weekday letter under it (0.60 mm high, 0.45 wide, centre y 106.855). Fits between the indicator LEDs (pads end y 105.14) and the button silk (y 107.475) without moving anything, so the indicator LEDs stayed put (moving them would have meant re-routing their tracks). DRC: 7 new warnings only (the 0.6 mm letters are below the board's 0.8 mm silk-height rule; deliberate). Gerbers + zip re-exported.
- JLCPCB PCBA preview (same day, Y42_routed_v4 gerbers + asm42 BOM/CPL, 5 boards, 4-layer black ENIG, 0.15 mm vias (forces plugged vias, 4-wire Kelvin test, Tg155), Standard PCBA both sides): all 24 BOM lines matched and in stock (XL-1005UWC and SM02B-SRSS-TB had to be re-selected by hand: JLCPCB flagged them "multiple types of parts" because the IND values differ and J1/J1B share a line). Rotation check against the silkscreen pin-1 marks: U1 OK, U2 (LGA-12) and U4 (BQ25570 VQFN-20, bottom) were 90 degrees off; fixed with ROT_FIX in `tools/make_bom_cpl.py` (-90 for both footprints) and verified in the preview (CPL now U2 270, U4 0). LED polarity markers sit on the outer (anode) ends, consistent with pad 1 = cathode on the inner side. Quote at that point: PCB $87.82 + PCBA $220.39 = $308.21 before shipping; nothing saved to the cart. Old cart items (Y43_final_gerbers_Y3/Y4) deleted at Evan's request.

### 2026-10-14 — Y42_routed_v4: ground plane fix, part checks, buzzer pins
- `boards/Y43/Y42_routed_v4.kicad_pcb` supersedes v2/v3: the In2 ground-plane zone outline had still followed the old 43.5 mm board and the old 1.77 mm strap slots; `tools/fix_gnd_zone.py` rebuilds it from the current outline (inset 0.4 mm, slots cut out) and refills. Also contains Evan's BTN1 track cleanup. DRC 0 errors / 0 unconnected. Gerbers/BOM/CPL regenerated (`fab42/`, `asm42/`, `Y42_routed_v4_gerbers.zip`).
- **Footprints vs the real parts:** crystal Seiko SC-32S (C97606): recommended pads 1.0 x 1.8 mm, 1.5 mm gap = ours exactly; load capacitance 12.5 pF = two 18 pF caps (9 pF) + strays, fine. 0402 LED (Xinglight XL-1005 family datasheet): recommended pads 0.3 x 0.55 mm on 0.8 mm pitch vs our stock 0402 pads (larger, normal for chip LEDs); pin 1 = cathode, pin 2 = anode = our pad 1 / pad 2. NOT verifiable: LCSC's datasheet file for the 0201 LED (C965789) is a different part's document (Lite-On LTST-C191KRKT); C&K's KMR2 datasheet was not reachable; 0603 LED, JST, inductors and the IMU land pattern (ST TN0018) still unchecked. LED rotation/polarity in the CPL has to be confirmed in JLCPCB's placement review.
- **Buzzer pins:** PB4/PB5 = TCA1 WO4/WO5 on the default PORTB route (TCA1 exists on the 48-pin part); TCA1 split mode (high byte), equal compare values, `PORTB.PIN5CTRL.INVEN` for opposite phase. Recorded in `mcu-pinmaps.md` and `firmware/HANDOFF.md`.
- JLCDFM (jlcdfm.com) on the v3 Gerbers (same copper as v4 apart from the BTN1 edit): trace width, annular ring and silkscreen-to-pad entries flag the known 0.10 mm rules; see the chat summary.

## 2026-10-14 (late) - schematic brought in line with the Y42 board; JLCPCB quote
- **Quote (JLCPCB, 5 assembled boards, both sides, standard PCBA, black mask, lead-free HASL, 0.15 mm via option, Kelvin test auto-added): $296.56** excluding shipping/tax = PCB $75.72 + assembly $220.84 (setup 51.50, stencil 16.54, parts 101.82, feeders 37.20, SMT 4.58, X-ray 8.25, placement confirm 0.45, packaging 0.50). 2-3 day assembly would be +$49.63. Not ordered, not saved to cart. All 24 BOM lines match and are stocked (the first view showed Qty 0 for XL-1005UWC C20613596 and SM02B-SRSS-TB C160402; re-selecting the same parts cleared it: 279,691 and 65,125 in stock). Piezo C910763 is a JLCPCB Extended part, placed by them on the back.
- **Schematic regenerated** (`schematic/gen_schematic.py --variant solar` -> `watch_solar.kicad_sch`) from the board: 7 mode LEDs (IND1..IND7 by column; IND7 = ALM on ROW11/COL6, the third LED from the left on the face), BZ1 Murata piezo on BUZ_A/BUZ_B (PB4/PB5), RESET (PF6) to pogo pad 1, J2 = 4-pad pogo row (RESET VBAT GND UPDI), dummy resistors R57-R59 + R61-R67 (cosmetic, unconnected), dummy caps C60-C62 and J3 removed, SC1+/SC1- cell pads as symbols. Netlist compared to `Y42_routed_v4.kicad_pcb`: 197 parts on both sides, 0 value differences, every pin on the same net, except the far-side pads of SW1/SW2 (see below).
- **Board fix:** IND7's value said LCK; now ALM (text only, gerbers/BOM/CPL unchanged - regenerated and diffed identical). DRC still 0 errors / 0 unconnected / 2 library-config warnings.
- **Switch far pads:** each KMR2 has two pads per terminal (1,1,2,2). The far pads carry no net on the board because the footprint does not declare them jumpered and nothing joins them; the terminals are shorted inside the switch. If the board is ever re-synced from the schematic KiCad will give them nets and DRC will report them unconnected - ignore or join them then.
- **Programmer:** Adafruit High Voltage UPDI Friend (product 5893, CH340E, 3 V/5 V selectable, JST SH cable) is the plan, with a home-made 4-pin 1.27 mm pogo jig (RESET left unwired). To check: serial UPDI on AVR128DB48 on the bench, and whether to feed VDD from the adapter at all (BQ25570 VOUT rail).
- **Firmware** (`firmware/`) not touched: `ledmap.h` still has 6 mode LEDs and `pins.h`/`hwmap.h` have no buzzer; the board changes are listed in `firmware/HANDOFF.md`.
- **Correction (same evening): v4 had lost earlier fixes.** The ground-plane v4 (03:12) was built from `Y42_routed_v2` and overwrote the silk/pad fixes recorded in the "every pad/via landing checked" entry above, so the committed v4 gerbers still had 0.10 mm silk, "SET-S" labels and 148 shallow pad landings (the JLCPCB viewer showed the dashed one-line labels). Re-applied to `Y42_routed_v4.kicad_pcb` in order: `check_pad_entry.py --fix` (148 pad + 159 via + 3 via-pad stubs), `silk_nodash.py` (7), `silk_thicken.py` (23 texts, 308 lines, 1 footprint text), `silk_twoline.py` (7 two-line labels), `fix_gnd_zone.py` (refill). Check: 0 shallow landings, DRC 0 errors / 0 unconnected, warnings = 2 library-table + 7 silk text-height (deliberate 0.6 mm weekday letters). Gerbers re-exported with `kicad-cli pcb export gerbers --subtract-soldermask` + drill (`--excellon-separate-th --generate-map --map-format gerberx2`) into `fab42/` and zipped; BOM/CPL regenerated (identical). Front silk still contains ~690 strokes at 0.112-0.125 mm (footprint default-width items); JLCDFM had reported silk line width 0 danger for this state, not re-run.
- **The $296.56 quote above was made on the stale gerbers** (no silk/stub fixes; default options) - redo it with the new `Y42_routed_v4_gerbers.zip`. The earlier session's quote on the fixed gerbers was PCB $87.82 + PCBA $220.39 = $308.21 (ENIG, 0.15 mm vias, Kelvin test). JLCPCB's session had logged out when this was written.
