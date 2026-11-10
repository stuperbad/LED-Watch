# Back-side layout concepts (2026-11-05) - parts only, no copper

Question: if the back were placed from scratch, what arrangement keeps the look symmetric, keeps the power parts close to their chip pins, and keeps tall parts out from under the batteries?
This is a placement study, nothing in KiCad was moved. Pictures: `back-concept-A.png` (as it is now), `-B`, `-C`, `-D`. Tool: `tools/back_concepts.py` (rectangles for the parts, simulated annealing, rule checks); geometry in `tools/back_parts_2026-11-05.json`.

## What is fixed, and the heights
| Item | Where | Height |
|---|---|---|
| Two LiPo pouches 15 x 15 x 5 mm | centres (100, 88.5) and (100, 111.5); the band between their tolerance outlines is **4.84 mm** (7.0 mm between the nominal bodies) | rest 1.1 mm above the board |
| Battery clips J1 / J1B | west, above and below the buzzer | 3.0 mm |
| Piezo BZ1 (9 x 9 mm) | west, centre | 1.9 mm |
| USB-C J2 | east, centre, mouth 1.3 mm from the rim | 3.3 mm |
| L1, L2 (1210 inductors) | | **2.5 mm** (too tall to sit under a battery) |
| U5 1.55, C54 1.25, D50 / D51 1.11 | | marginal / over 1.1 mm |
| 0402 caps 0.5, 0402 resistors 0.35, U4 0.78 | | fine under a battery |

Zones: the **band** between the batteries (4.84 mm tall, about 19 mm wide between the buzzer and the USB-C) takes anything; **under a battery** only parts up to 1.1 mm; the **east corners** (x > 109.5, above y 93 and below y 107, the "1-2 o'clock and 4-5 o'clock" areas) take anything because no battery is above them; the west is the buzzer and the clips.

## BQ25570 pin geometry (why the inductors are awkward)
Both inductor pins (16 LBUCK, 20 LBOOST) sit on the same side of the chip, and the two inductor "corners" (pins 16 / 14 and pins 20 / 2) are mirror images top and bottom. Two 2.65 mm inductors cannot be stacked inside a 4.84 mm band, so a perfectly mirrored pair needs the east corners.

## The four concepts (straight pad-to-pin distances, mm)
| | A: now | B: tidy cluster | C: corner inductors | D: only L2 in a corner |
|---|---|---|---|---|
| C52 CSTOR / C53 CBYP (priority 1) | 1.3 / 2.6 | 1.2 / 1.1 | 1.1 / 1.2 | 1.1 / 1.2 |
| C50 CIN (2) | 7.8 | 1.0 | 1.1 | 1.0 |
| L1 (3) | 6.9 / 8.6 | 5.4 / 6.1 | 8.3 / 10.7 | 5.5 / 6.2 |
| C54 COUT (4) | 5.3 | 3.7 | 3.7 | 3.7 |
| L2 (5) | 9.4 / 8.7 | 4.8 / 6.5 | 10.7 / 8.5 | 12.6 / 11.2 |
| dividers R50-R56, C51 | 1.5-4.8 | 1.1-2.7 | 1.1-2.6 | 1.1-2.2 |
| rule issues | D50, U5 under a battery | none | none | none |

* **A (now)** is the T shape of the band plus the USB corner. U5 (1.55 mm) and D50 (1.11 mm) are partly under the batteries.
* **B (tidy cluster)**: U4 in the band, dividers on its west, small caps tight around it, L2 west and L1 east in the band, everything that serves a pin within about 3 mm (inductors 5-6). The USB-charger parts (U5, C55, C56, R70, R71) move out from under the battery into the free corner south-east. Best distances, but it is the densest: routing room is the open question. Symmetry: left-right (L2 / L1), not up-down.
* **C (corner inductors)**: L2 north-east and L1 south-east, exactly mirrored about the horizontal axis through the USB-C; U4 shifted east to about x 104 (nearer the solar pad SC1+ and the USB corner, so SOLAR_IN and BATT get shorter); the dividers sit west of U4 in the quiet part of the band. Most elegant, and the band stays almost empty (room for routing), but the inductors are 8-11 mm from U4. The data sheet's priority order puts L1 and L2 last, and its layout advice is to use vias and bottom-layer traces for the inductors, so this may be acceptable; it needs a bench check of the converter efficiency.
* **D (L2 in the corner, L1 in the band)**: the middle road; L2 12 mm away is the price.

## What I would do
Start from **B** (functional first) and hand-tune it towards **C's** look: keep L1 / L2 in the band if the routing is comfortable, otherwise move only the farthest one to a corner; shift U4 east by 2-4 mm; keep the clips and the buzzer in the west (the clips are 3 mm tall and their wires run from the battery edge, the east strip is the USB corner); put U5 and its caps in the south-east free corner next to the USB-C instead of under the battery.
These distances are straight lines between pad centres with the parts as boxes: they ignore vias, keep-outs, the front side and routing; the packing is deliberately tight, so a layout that is denser than today is not necessarily routable.

## Open decisions
1. B-like (shortest loops) or C-like (mirrored, longer inductor loops)?
2. U4 shift east, yes or no?
3. Accept batteries resting on 0402 parts and D50 / D51 (1.1 mm), keep L1 / L2 / U5 / C54 out?
4. Battery clips stay west?

## Round 2 (2026-11-09): the owner's rules

Rules as I understood them: (1) above and below U4 nothing, except ONE long row of small parts (0603 or smaller, rotated horizontal) on one side, the bottom side preferred, everything centred accordingly; (2) U4, L1 and L2 pushed up a hair towards the top of the solar cell; (3) mirror symmetry left / right, parts snapped; (4) tall parts (L1, L2, U5, C54, D50 / D51) out of the battery outline; small parts may enter the ring between the two outlines but not the nominal 15 x 15 body (I took white = outer tolerance outline, blue = nominal body: please say if that is reversed); (5) the spots above and below the USB-C stay free of tall parts.

**Length budget of the band (x 90.4 to 111.0 = 20.6 mm between the buzzer and the USB-C pins):** U4 3.9 + L1 4.05 + L2 4.05 + C54 2.9 = 14.9 mm; the small vertical parts (C52, C53, R54-R56) in three columns another 2.2 mm; gaps about 2.4 mm: **19.5 mm, so the band is full with U5 left out.** U5 (3.7 mm) cannot also be in the band: it has to go to a corner (NE or SE, next to the USB-C, 1.55 mm tall, lower than the USB-C's 3.3 mm), or one of the inductors has to leave the band. That is the fixed trade-off behind every concept below.

**Which U4 side faces where** (the pin sides, current orientation): south 1 GND, 2 SOLAR_IN, 3 VBAT*, 4 VREF_SAMP, 5 GND; west 6 VBAT*, 7 VBAT_OV, 8 VRDIV, 9 GND, 10 OK_HYST; north 11 OK_PROG, 12 VOUT_SET, 13 BAT_OK, 14 VOUT (+3V3), 15 GND; east 16 LBUCK, 17 GND, 18 BATT, 19 VSTOR, 20 LBOOST (* control pins tied to VBAT). Both inductor pins are on the east side, so with L1 and L2 on opposite sides of U4 one of them is always on the wrong side; whatever side faces north cannot have its parts directly above (rule 1), so those pins are reached from the corners. Turning U4 by 90 degrees clockwise puts LBOOST and SOLAR_IN at the south-west corner and LBUCK and VOUT at the south-east corner: L1 west, L2 east, mirrored, with C50 and C54 as a mirrored pair, but then the divider pins face north.

**Concepts E, F, G** (annealed under these rules; pictures `back-concept-E/F/G.png`; F is the cleanest): F has L2 | U4 | L1 | C54 in the band with the row of six small parts under U4 and U5 in the north-east corner (no rule issues, but the row is not on one tidy line and three divider resistors sit beside U4, not in the row); E puts U5 in the south-east corner but has a C54 / L1 overlap; G keeps U5 in the band and overlaps C54 with U4, which is the budget problem again. These are starting points for hand work in KiCad, not finished layouts: the machine does not snap to a grid and does not make things look elegant.
