> **File layout changed on 2026-10-15.** Entries below were written with the old paths. Old -> new: `boards/Y43/Y42_routed_v4.*` = `hardware/LED Watch - Single Color.*` (revision A), `boards/Y43/fab42` = `hardware/production/gerbers`, `boards/Y43/asm42` = `hardware/production/assembly`, `schematic/` = `hardware/`, `footprints/` = `hardware/footprints/`, top-level `*.md` = `docs/`, older boards = `archive/`. Details: `archive/README.md`.

# Pre-order checklist (everything between now and pressing "order")

Status key: [ ] open, [~] partly done, [x] done. Owner: E = Evan, C = Claude (can do), E+C = needs a decision first.

## A. Decisions to lock first
- [ ] A1 (E+C) Solar: two KXOB25-07X1TF in series, or one AM-1606C (15 mm)? Check Anysolar stock/price and lead time (no live stock was found); get a quote or ask for samples.
- [ ] A2 (E+C) Batteries: TinyCircuits 70 mAh pair (JST-SH plug) vs generic 401030/301030 pair vs Renata 50 mAh pair. Confirm real dimensions and wire exit side; buy ONE of each to test-fit before the board is final.
- [ ] A3 (E) Board diameter limit (43 mm now; 1 mm bumper -> 45 mm outside) and whether one-sided SMT (47 mm) is worth the cheaper assembly (see ASSEMBLY-AND-COST.md).
- [ ] A4 (E) LED brightness target and colour temperature; confirm LED parts (below, section E).
- [ ] A5 (E) Mode list and indicator labels (DESIGN-UX.md section 7).
- [ ] A6 (E) RGB version: keep as a later project, or run in parallel? (needs the polar-trace tool first)

## B. Schematic (C unless noted)
- [x] B1 (2026-10-11) Schematic matches the board: VQFN-48 MCU (symbol AVR128DB48x-x6LX), two battery plugs J1/J1B, two series solar cells J3/J4 (net `SC_MID`), UPDI Tag-Connect TC2030-IDC-NL (pad 1 UPDI, 2 VBAT, 6 GND). ERC: only the 3 known warnings. NB the .kicad_sch is generated; `watch_usb.kicad_sch` (open in KiCad) was NOT regenerated.
- [x] B2 (2026-10-11) Real BQ25570 RGR0020A footprint built from TI's drawing (bq25570.pdf p.44; pads 0.6 x 0.24, 0.5 pitch, span 3.3, EP 2.05 x 2.05) in `footprints/LEDWatch.pretty`; symbol pin numbers 1-21 checked against the datasheet pin table (pins 9 and 17 are NC-to-PowerPAD in the datasheet, VSS in the symbol).
- [x] B3 (2026-10-11) Crystal load caps: DS40002247B Table 39-10 gives XTAL pin parasitic capacitance 5 pF per pin, max crystal CL 18 pF (LPMODE=0), ESR 100 kOhm typ. With a 12.5 pF crystal CL = (C+5)/2 + ~1 pF stray -> C = 18 pF (C0G). So 18 pF was right under the per-pin reading; confirm on the bench (AN2648). The datasheet's Figure 4-7 also shows an optional series resistor RS on XTAL32K2 (not fitted yet). Layout follows datasheet 4.5.1: crystal and caps on the MCU side, grounded plane (In2) under, no traces under the crystal.
- [x] B4 (2026-10-11, 220 ohm from `led_resistor.py`; re-check when the LED parts are chosen) LED resistor value: choose from a brightness-vs-battery curve (workbook tab 'LED types'); consider 100 ohm; confirm the AVR pin drop (datasheet limits: sink 10 mA at 0.6 V, source 6 mA at 0.7 V).
- [ ] B5 Row/column current limits and the game-mode brightness plan (software scheduling or row driver transistors; see mcu-pinmaps.md section 3).
- [ ] B6 Add ESD protection on the two buttons; add test points (VBAT, 3V3, GND, UPDI, SDA, SCL, SOLAR_IN); pull-ups; decoupling counts per supply pin.
- [ ] B7 Set the MVIO fuse (single supply) and tie VDDIO2 to VDD; set the INT pin input level to TTL (firmware note).
- [ ] B8 Run ERC to zero warnings that matter; document the accepted ones.
- [ ] B9 Charging for a dead battery: decide the BQ25570 BAT_OK threshold behaviour; two small cells in series should clear the 0.6 V cold-start minimum (to verify on the bench).

## C. Power and firmware validation (before trusting the estimates)
- [ ] C1 Measure sleep current on a dev board with the same MCU and sensor (target about 3 uA with the 32 kHz crystal).
- [ ] C2 Measure LED current vs battery voltage with the chosen resistor.
- [ ] C3 Check wake-on-motion thresholds with the LIS2DW12 on a breakout.
- [ ] C4 Prototype LED-as-light-sensor (reverse-bias discharge timing).

## D. PCB layout and routing
- [ ] D1 Set design rules to JLCPCB's current 4-layer capabilities (min track/space, via drill/annular ring, hole-to-copper, copper-to-edge, silkscreen). Verify each number on JLCPCB's capability page; do not trust memory.
- [ ] D2 Re-export the Specctra file and re-route (about 25 minutes with freerouting; command in README); fix the 6 unrouted connections and dangling tracks by hand.
- [ ] D3 Ground pours on the inner layers and front/back as needed; stitch vias; solar and battery power traces wide enough.
- [ ] D4 Silkscreen: LED polarity/orientation marks if useful, indicator labels (done), reference text off pads, board name/version, no silk over pads.
- [ ] D5 Mechanical: confirm the strap slot size against a real strap (placeholder 19.75 x 1.77 mm), lug width (25.1 mm), corner radii, battery keep-outs (yellow dashes), solar cell alignment marks.
- [ ] D6 Check part heights in a 3D view (cells 5.25 mm, battery plugs, inductors) so nothing touches the strap.
- [ ] D7 Fiducials and panelisation (JLCPCB can add rails; avoid breaking the lugs).
- [ ] D8 Stack-up and finish: 4-layer 1.6 mm, ENIG (skin contact, sweat) unless cost says otherwise; confirm via-in-pad rules for the VQFN thermal pad.
- [ ] D9 Final DRC clean and a second pair of eyes (EE review of pin 1 orientation, crystal traces, antenna-free zones, analog traces).

## E. BOM and assembly files (JLCPCB)
- [ ] E1 One BOM row per unique part with the LCSC number; mark Basic vs Extended; count extended types (each costs a loading fee); reduce unique values where possible (the BQ25570 ladder uses 6 odd resistor values).
- [ ] E2 Stock check on the day: AVR128DB48 had only 60 at JLCPCB (217 at DigiKey); LIS2DW12 19,712; BQ25570 476; white 0201/0402/0603 LEDs plentiful.
- [ ] E3 Generate a clean CPL (placement) file from the final board; check rotation conventions per footprint (JLCPCB's rotation offsets differ from KiCad for many packages); LEDs sit at arbitrary angles (6 degree steps): ask JLCPCB again with the real file, expect an extra fee or a refusal.
- [ ] E4 Decide which parts JLCPCB places on the BACK (two-sided assembly) vs hand-assembled; see ASSEMBLY-AND-COST.md.
- [ ] E5 Parts we buy and fit ourselves: 2 batteries (+ spare), 2 solar cells, battery wires/plugs, Kapton and foam tape, optional shield. Order a spare set.
- [ ] E6 Upload to JLCPCB for a real quote; run their DFM check; read every warning.

## F. Tools and consumables for the hand steps
- [ ] F1 Soldering station with fine tips, flux, hot-air or hot plate, tweezers, magnification.
- [ ] F2 Programmer for UPDI (cheap UPDI cable or Atmel-ICE), test leads, bench supply or source-meter for current measurements.
- [ ] F3 Foam tape, 0.025 mm polyimide tape, strap material, tiny screws only if a shield is used.

## G. Bring-up plan (when boards arrive)
1. Visual and microscope inspection of the 0201 ring; check LED polarity on a sample.
2. Power with a bench supply and current limit; measure idle current.
3. Program over UPDI; verify the crystal (RTC) and the I2C sensor address 0x18.
4. Scan the LED matrix; check every LED lights at the right angle.
5. Attach batteries (one at a time, check voltage match before connecting both); charge test via the harvester under a lamp.
6. Run the UX firmware skeleton (DESIGN-UX.md); measure average power in each mode.

## H. Documentation for outsiders
- [ ] H1 Keep README, DECISION-LOG and this list current after every session.
- [ ] H2 Publish BOM, schematic PDF, board renders and generator scripts once the design is stable; choose a licence (open hardware, e.g. CERN-OHL-P or CC BY-SA).
- [ ] H3 Add photos of the real boards and the measurement logs.

## Biggest risks, in order
1. Solar cell and battery availability (Anysolar stock unknown; Renata cells not stocked).
2. Routing and DRC against JLCPCB's real limits (0.1 mm features, 0201 LEDs).
3. The 0201 / arbitrary-angle LED placement at JLCPCB (extra fee or refusal).
4. Brightness near the bottom of the battery range.
5. Back-side parts and strap rubbing (coat or film).

## Solar cell switch (2026-10-11)
- [x] Schematic and board now use ONE Anysolar KXOB25-05X3TF (23 x 8 x 1.2 mm, 3 cells in series: Voc 2.07 V, Vmpp 1.67 V / 18.4 mA, 30.7 mW at 1 sun; datasheet in `datasheets/`, marked Preliminary) instead of two KXOB25-07X1TF in series (28.5 mW). Reasons: one part and one pad pair to hand-solder (was two and four), Voc far above the BQ25570 cold-start minimum (600 mV typ / 700 mV max, datasheet p.), Vmpp/Voc = 0.807 so VOC_SAMP to VSTOR (80 %) fits. Board pads 2.5 x 7.4 mm at each end (cell pads are 2.0 x 7.4; the extra 0.5 mm sticks out as iron access).
- [ ] SOLDERING: the datasheet recommends Sn42/Bi58 paste at 220 C peak, or hand soldering 5 s below 400 C; JLCPCB's standard reflow is hotter, so the cell is NOT a JLCPCB assembly part - order it separately and hand-solder. No paste layer on the cell pads.
- [ ] POLARITY: the datasheet back-side drawing shows + at the left end; seen from above through the cell that is the RIGHT end (SC1+ = SOLAR_IN on the board). Measure Voc on a real cell before soldering and confirm.
- [ ] STOCK: DigiKey listings (cached regional pages) showed 1,866 in stock for KXOB25-05X3TF-TR at $3.45 (1), $2.82 (10); lead time 15 weeks. Check the live page.

## Status 2026-10-14 (Y42 board, quote done, not ordered)
- [x] Schematic == board: `schematic/watch_solar.kicad_sch` regenerated; 197 parts, all nets equal (far KMR2 switch pads aside). Supersedes the stale B1 line above (Tag-Connect, two series cells).
- [x] D1/D9 JLCPCB rules + final DRC: `boards/Y43/Y42_routed_v4.kicad_pcb`, 0 errors / 0 unconnected; pad-landing stubs and 0.15 mm silk, two-line mode labels re-applied 2026-10-14 (they had been lost when v4 was rebuilt).
- [x] E1/E3/E6 BOM + CPL (`boards/Y43/asm42/`): 24 BOM lines, 194 placed parts (176 top, 18 bottom), all stocked on 2026-10-14. Quote: redo with the corrected gerbers (the $296.56 made earlier used a stale zip; the earlier quote on fixed gerbers was $308.21 with ENIG).
- [x] Datasheet pad checks 2026-10-14: 0201/0402/0603 LEDs (vendor pads smaller than our stock pads, OK), KMR2 (matches, G ground tab omitted), crystal, MCU, BQ25570 - see DECISION-LOG. JLCDFM run: only the known 0.10 mm rule items red. Quote on the corrected files: $308.63.
- [ ] Still open before ordering: IMU land pattern vs ST TN0018 (ST site unreachable), JST/inductor drawings; strap slot test with a real band; piezo sound path test; firmware on the real board (ALM, weekday lights, buzzer TCA1 split mode: written and tested on the PC, not yet run on hardware); bench test serial UPDI on AVR128DB48 with the Adafruit UPDI Friend (5893) and a 4-pad pogo jig; decide whether to save to cart (JLCPCB asks for login again).
