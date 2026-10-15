# Polar router: first results (2026-10-09)

Files: `polar_model.py` (ring/lane optimiser), `polar_sweeps.py` -> `polar_sweeps.png` (what drives the size), `polar_rows.py` (first polar router), `polar_rows.png` (picture of its output),
`tools/` (Specctra export/import helpers). The earlier plan is in `POLAR-TRACES.md`.

## 1. What Evan's hand-built RGB board actually does (measured from `LED Watch.kicad_pcb`)
- LED rings at radius 14.0 (12 hour LEDs), 16.5 (60), 19.0 (60); 0.83 mm LEDs with four 0.3 mm pads on a 0.5 mm pitch. Tracks are all 0.1 mm, every via is 0.4 mm / 0.2 mm drill (572 vias, 6,002 tracks).
- Inner layer `PWR.Cu` carries **18 concentric lanes, one per column net (R1-6, G1-6, B1-6), at 0.35 mm pitch**, spanning radius 12.1 to 20.5 mm. The lanes run UNDER the LED rings, not in the gaps.
- Vias are not scattered: they cluster in rows at 16.0, 17.0-17.25, 18.5 and 19.5 mm, i.e. just inside and outside the 16.5 and 19.0 mm rings. `B.Cu` carries short arcs at those via radii (the row/common-cathode groups).
- LEDs on that board are not rotated (all 0 degrees); only the single-colour board uses true radial rotation.
- 0.35 mm is exactly the pitch my model derives from the via rule: a through via pierces every layer, so neighbouring lanes need (via 0.4 + track 0.1)/2 + clearance 0.1 = 0.35 mm, wider than the bare track pitch of 0.2 mm.

## 2. The optimiser (`polar_model.py`)
Rules: lane pitch is via-driven; spokes (stubs to lane vias) that cross an LED ring between LEDs widen the LED pitch and so push that ring outward; lanes may run under the rings (zones: inner gap, ring, gap, ring, gap, ring, outer gap); the search tries every lane distribution (about 135,000) and keeps the smallest outer diameter for a required free-centre diameter.
The model is a LOWER-BOUND-STYLE estimate, not a router. Checked against Evan's board it is pessimistic: for a 27 mm free centre it predicts about 46 mm outside, his hand layout is about 40 mm. So treat absolute numbers as conservative and the DIFFERENCES between options as the useful output.

### Drivers (RGB, 18 long nets, free centre 24 mm): change in outer diameter vs the baseline of 43.9 mm
| Driver | Outer diameter | Change |
|---|---|---|
| Baseline: via 0.40/0.20, track and space 0.10, through vias | 43.9 mm | - |
| Via pad 0.30 | 41.8 | -2.1 |
| Via pad 0.25 | 40.7 | -3.2 |
| Track and space 0.127 (5 mil) | 50.6 | +6.7 |
| Track and space 0.09 (3.5 mil) | 43.4 | -0.5 |
| Blind/buried vias (no piercing) | 40.0 | -3.9 |
JLCPCB's official capability page (as found by a web search today) says multilayer vias are through-hole only, minimum hole 0.2 mm, minimum pad 0.45 mm (0.4 mm "limitation"), so the 0.4/0.2 via we use is already at the limit and blind/buried vias are not offered. Track and space limits were reported inconsistently (0.09 or 0.127 mm); hole-to-copper and copper-to-edge clearances could not be confirmed.

### Matrix shape (group size m = LEDs per common-cathode row), RGB, free centre 24 mm
| m | long nets (3m) | row nets (132/m) | MCU pins for the matrix | outer diameter |
|---|---|---|---|---|
| 2 | 6 | 66 | 72 | 37.6 mm |
| 3 | 9 | 44 | 53 | 37.6 mm |
| 4 | 12 | 33 | 45 | 39.7 mm |
| 6 (today) | 18 | 22 | 40 | 43.9 mm |
| 12 | 36 | 11 | 47 | 56.5 mm |
Fewer long nets means narrower lane bands and a smaller board, at the price of more MCU pins. m = 4 (45 pins) saves about 4 mm of diameter; m = 3 needs 53 pins, which is the whole 64-pin ATmega169PA.

### White version (same model, 12 sectors x 11 slots, 11 long row nets)
Smallest outer diameter for a 24 mm free centre is about 38 mm, a 20 mm free centre about 35 mm: consistent with the 36-43 mm boards the planner found. See `polar_sweeps.png` for the curves.

## 3. The first polar router (`polar_rows.py`, white board)
The 11 ROW nets each touch 12 LEDs that all sit on one ring, so each becomes a full-circle arc on inner layer In1 at its own radius. Per LED: cathode pad -> short F.Cu stub (tangential, then radial) -> through via at the lane radius in the slot clockwise of the LED. Lane pitch uses the same formula (0.35 mm here; becomes 0.40 mm if the hole-to-copper clearance is 0.25 mm).
- Result on the V1 board (43 mm): 132 vias, 264 stub tracks, 44 arcs (11 lanes x 4 quarter arcs). **KiCad DRC at 0.1 mm track/space and 0.2 mm hole clearance is clean for all of it.** `polar_rows.png` shows the pattern.
- The one conflict found was real: a via from the hour ring (ROW0) lands on the UPDI pad on the BACK (`J2`), because vias go through the board. Rule for the planner: back-side parts must keep out of the LED band (or sit only where there are no vias).
- Hybrid flow tried: lock the polar copper, hand the rest to freerouting, import the session. Freerouting could not finish with the lanes locked (3 connections still unrouted after about 100 passes; without the lanes it finished in 18). Reason: the lane band on In1 plus the vias blocks via placement inside the band, so every column net has to stay on F.Cu until it leaves the band. After merging, the board has about 20 unconnected items (3 unrouted by the autorouter plus artefacts of the session merge) and the one via/pad conflict above.
- Specctra (the autorouter's file format) has no arcs, so the lanes are handed over as short segments and converted back to true arcs afterwards (`tools/arcify_lanes.py`).

## 4. What this means
- The polar row lanes work and are clean at 0.1 mm rules; the missing piece is the COLUMN side: each column (one sector: 1 hour + 5 minute + 5 second LEDs) should get its own F.Cu trunk (radial line plus short arcs) that leaves the lane band outside the outer ring. That makes every sector identical, so one generated sector can be rotated 12 times.
- For RGB the same idea needs the group structure (6 LEDs per cathode row; 18 column nets running all the way round); the model says the lane band (18 x 0.35 = 6.3 mm) overlaid on the rings is what sets the board size, and the biggest levers are via size, matrix group size and lane order.
- Vias of different nets must stay out of the lane band radii, so ring spacing is set by via rows adjacent to each ring as much as by LED pads.

## 5. Next steps
1. Column trunks for the white board (step 2 of the router); then re-run the autorouter only for power, solar and the MCU escape.
2. Fix the planner so back parts avoid the via band; add an automatic check.
3. Confirm JLCPCB's hole-to-copper and track/space limits on their capability page, then set `HOLE_CLR` and the lane pitch from the real numbers.
4. Port the lane generator to the RGB geometry (rotated LEDs, group arcs), and use the optimiser to propose ring radii and a group size.

## 6. Update 2026-10-11: JLCPCB rules, polar rows + columns, full autoroute (boards/V3_D50, 50 mm)
Rules are now JLCPCB's own (`JLCPCB-RULES.md`): hole-to-copper 0.28 outer / 0.30 inner, via 0.30 pad / 0.15 hole, edge 0.20, silk 1.0 mm. `polar_model.py` defaults and `polar_sweeps.py` use them (white 24 mm free centre: ~37.6 mm in the model; RGB ~46 mm; blind/buried vias -7.6 mm; group size m=4 -> ~41 mm).

**What works:** the polar rows (11 In1 lane circles, 132 vias) and columns (12 sector trunks + anode arcs on F.Cu) are generated by `polar_route.py` and are DRC-clean at those rules.

**What does not (yet):** autorouting the remainder (power, solar, MCU escape) around the locked polar copper.
- Autorouter locks: wires must be `(type protect)`; `(type fix)` made freerouting throw silent exceptions and skip nets.
- The autorouter only respected 0.1 mm copper clearance to vias (hole edge 0.177 mm from tracks). Typed via clearances must be set BOTH at structure level and in the net class `(rule ...)`, which otherwise overrides them. With 0.23 mm the hole-clearance errors fall from 199 to 4.
- At the true clearance the router cannot finish: 15-17 connections stay unrouted after ~1000 passes (GND, VBAT, a few ROW/COL links to U1). Before the clearance fix it "finished" only because it ignored the hole rule. The MCU escape area is physically too crowded at 50 mm.
- `tools/merge_new.py` now drops echoed copies of polar copper (same net, within 30 um) - dangling warnings 175 -> 25.
- Honest size: ~48-50 mm for the polar white board vs 43 mm for the earlier unbounded autoroute that ignored hole clearance. Polar is not tighter today.

**Levers:** blind/buried vias (HDI), fewer LEDs per common-cathode group (more MCU pins), via 0.25/0.15, MCU moved nearer the centre with a dedicated escape zone.
Best current board: `boards/V3_D50/V3_polar_best.kicad_pcb` (4 hole-clearance errors, ~39 unconnected items).

## 7. Correction and new result (2026-10-11): single colour at 43.5 mm, polar copper DRC-clean
- **Rule correction.** JLCPCB's page gives via hole to track / inner copper = **0.2 mm**; the 0.30 mm I used before is their row for PTH component-pad holes (see `JLCPCB-RULES.md`, verbatim rows and URL). Lane pitch 0.425 -> 0.345 mm. The size model with the corrected rule gives 42.4 mm for RGB (group 6, free centre 24), matching Evan's real 43 mm board; the earlier "46 mm" was the model with the wrong rule (+3.8 mm), never a layout.
- **Single colour, `boards/Z43.5`:** 43.5 mm board (was 50). Changes: via rule fix; edge margin 0.78 (derived: the outer anode arc needs R - r_S >= 1.32 mm, so LED tip to edge >= 0.77); ring gap 0.8 (derived minima: hour-minute 2.7, minute-second 2.1 centre distance); `--back-via-clr 0.6` (back parts only avoid the hour ring's vias, not the whole free circle); `--plug-rot-free` and `--batt-clr 0.2` (battery plugs fit the 6 mm strip between the pouches); `--xtal-below` (32 kHz crystal and its two caps directly below the MCU, as in the first hand-built revision).
- The polar rows and columns on this board pass KiCad DRC with **zero errors** at JLCPCB's real rules (0.1 track/space, 0.2 hole clearance, 0.2 edge).
- **Blind/buried vias are not free.** JLCPCB instant quote of the RGB Gerbers (50.28 x 42.87 mm, 4 layers, 5 pcs): standard $8.00, 3-4 days; choosing HDI (1-step): $116.79 (HDI structure fee $67.06, engineering fee $25, material/inner copper $23) with buried-via and lamination fees "Manual Quote" on top, 10-11 days. The model says blind vias would save ~4 mm; not worth it while the through-via layout already reaches 43.5 mm.
- `tools/prep_dsn.py` now prepares the autorouter file (protect + via clearances at both rule levels).

## 8. 2026-10-11 (late): crystal, guard, hour-ring parking, schematic sync - `./build_board.sh G43 43.5`
- One command now builds the board without routing: planner -> pcb -> `crystal_hookup.py` (crystal, caps, GND plane on In2, F.Cu ground guard + stitching vias) -> polar rows/columns. KiCad DRC: 0 errors at JLCPCB rules.
- MCU turned 270 degrees so PF0/PF1 face the crystal; load caps directly under the crystal pads; datasheet DS40002247B 4.5.1 followed (no traces under the crystal, guard on top tied to a solid plane).
- Series resistors parallel to their hour LED; R50-R56 and R20/R21 parked in the hour-ring gaps (`--band-parts`). D=43 needs the crystal caps to fit under the MCU inside the free circle, so 43.5 mm is the working size.
- Schematic regenerated (usb + solar): VQFN-48 MCU, J1B, two series solar cells J3/J4, Tag-Connect J2, BQ25570 footprint from TI RGR0020A (`footprints/LEDWatch.pretty`).

## 9. 2026-10-11: edge margin, slot padding, can the solar cell move to the centre? (`./build_board.sh K43.75 43.75`)
- JLCPCB Outline tab: copper to routed board edge >= 0.2 mm, copper to routed slot >= 0.2 mm, routed edge tolerance +/-0.2 mm (regular) / +/-0.1 mm (high precision, boards of at least 50 x 50 mm only). Design rule now 0.3 mm copper-to-edge (DRC enforces it); strap slots start 1.5 mm outside the LED ring (`--slot-clear 1.5`, was 0.78).
- Smallest board with the single KXOB25-05X3TF, crystal directly under the MCU, 0.3 mm edge: cell shifted 2.5 mm up -> 43.75 mm. Cell shifted 2 mm -> 44.75 mm; cell at 0 or -1 mm -> nothing up to 45.5 mm. Without the crystal-under-MCU rule and with J2/C54/L2 parked above the cell, a centred cell needs 44.25 mm. So centring the cell does NOT shrink the board: the lower stack (MCU 7.3 + crystal 2.3 + caps 2.2 + gaps = ~12 mm) needs the room the shift gives it.

## 10. Layout B (Evan's sketch), 43.5 mm: `./build_board_b.sh L43 43.5`
Solar cell centred; Tag-Connect | MCU | upright 32 kHz crystal (caps to its right, ground guard + stitching vias) all above the cell; the 6 mode LEDs as a horizontal row (labels under) tight below the cell; symmetric low buttons with the IMU/inductor between them. Battery plugs now face their OWN pouch (J1 up/outward, J1B down/outward) - the previous `--plug-rot-free` option let both face the same way. 0.3 mm copper-to-edge, strap slots padded 1.5 mm, DRC 0 errors. Smallest working diameter for this arrangement: 43.5 mm (43.25 fails on the programming pads; below that the plugs). Layout A (crystal under the MCU, `./build_board.sh K43.75 43.75`) is the fallback.
