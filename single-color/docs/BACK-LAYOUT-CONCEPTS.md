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
