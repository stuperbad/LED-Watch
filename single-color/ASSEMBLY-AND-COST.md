# Assembly options and cost estimates (white version and RGB version)

Draft 2026-10-09. Fees marked JLCPCB-PAGE come from JLCPCB's own assembly-price help page as reported by a web search on this date; everything marked ESTIMATE is my arithmetic from our BOM.
Prices move: re-quote with the real files before ordering (PRE-ORDER-CHECKLIST.md section E).

## 1. How surface-mount assembly works (and what "two sides" means)
1. Solder paste is printed on the pads of the first side through a stencil.
2. A pick-and-place machine sets every part for that side.
3. The board goes through a reflow oven: the paste melts, surface tension pulls each part onto its pads, then it freezes.
4. For a second side: flip the board, print paste on the other side, place parts, reflow again.
During the second reflow the FIRST side faces down. The first-side joints re-melt, and parts stay on only because of solder surface tension. Light parts stay; heavy parts (inductors, big connectors, big ICs) can drop off. So the rule is: put the light parts on the side reflowed first and the heavy ones on the side reflowed last.

### What JLCPCB offers
| Service | Sides | Setup | Stencil | Notes |
|---|---|---|---|---|
| Economic PCBA (JLCPCB-PAGE) | one side only | $8.18 | $1.53 | cheapest; some size/count limits |
| Standard PCBA, one side (JLCPCB-PAGE) | one | $25.56 | $8.21 | |
| Standard PCBA, both sides (JLCPCB-PAGE) | two | $51.12 | $16.42 | needed whenever any part sits on the second side |
| Extended-part loading fee | any | $3 per unique extended part (most sources; one source says about $1.50 since Dec 2025: UNVERIFIED) | | Basic parts are free; Preferred-extended parts can be free |
| Economic-vs-Standard gap rule | | if both are offered the price gap must be at least $14.93, otherwise a handling fee is billed | | |
| Joints and per-part labour | | small per-joint charge (about $0.002 per joint: ESTIMATE, not read from the page) | | |
So the two-sided premium is a FIXED fee of about $58 per order (setup + stencil difference), not a per-part charge. At 5 boards that is about $12 per board; at 20 boards about $3.

### Doing the second side at home (toaster oven or hot plate)
- Reflow the side with the light parts first, the heavy side last (our front has the 132 LEDs, MCU, buttons; our back has the inductors, battery plugs, harvester chip: so FRONT first, BACK second).
- Keep the board flat and still during the second pass; support it off the tray or plate; a stable oven is much better than a hot plate (forum reports).
- Options if parts on the first side start to drop: low-melt paste (about 138 C) on the second side, glue the heavy first-side parts, or hot-air / iron the heavy back parts by hand after reflow.
- The home route is realistic for a prototype run of a few boards; the 132 0201/0402 LEDs are the part where JLCPCB's machines are far better than hand work.

## 2. Our current board (V1, white, solar, two LiPo cells)
From the netlist and the planned placement (ESTIMATE of joint counts; 28 unique value+footprint BOM lines):
- 183 parts, about 446 solder joints; 10 parts (50 joints) on the BACK: U2 (LIS2DW12), U4 (BQ25570), L1, L2, C51-C54, J1 (battery plug), J2 (UPDI pads). 9 unique lines are on the back.
- Parts we buy and fit ourselves, NOT done by JLCPCB: 2 solar cells, 2 LiPo cells (and spare), wires/foam/Kapton.
- Layouts: with everything possible on the front but the plugs, the board grows from 43 mm to 47 mm (`--all-front`), because the harvester chip, inductors and UPDI pads need front area.

### Cost estimate for 5 boards (USD, ESTIMATE; ranges because the extended fee is uncertain)
| Line | Two-sided, 43 mm (Standard) | One-sided, 47 mm (Economic + hand-solder plugs) |
|---|---|---|
| Bare 4-layer PCB (5 pcs) | about 62 (from the RGB board quote; this outline untested) | about 62 |
| PCB shipping | about 31 | about 31 |
| Assembly setup + stencil | 51.12 + 16.42 = 67.54 | 8.18 + 1.53 = 9.71 |
| Extended-part loading (assume 18-22 types) | 54-66 at $3, or 27-33 at $1.50 | same |
| Joints | about 5 | about 5 |
| Parts bought via JLCPCB (about 20 per board) | about 100 | about 100 |
| Solar cells, LiPo cells, wires (ours, about 20-30 per watch, plus spares) | about 100-150 | about 100-150 |
| **Total for 5** | **about 400-480 (about 80-95 per watch)** | **about 340-410 (about 70-85 per watch)** |
Big levers: the number of extended parts (each $1.50-3 per ORDER, so 20 parts = $30-60 whatever the quantity), the quantity (setup and extended fees amortise), and the cells (which are not JLCPCB parts at all).
Reducing extended parts: the BQ25570 ladder uses six odd resistor values (7.32M, 5.76M, 1.47M, 4.22M, 8.25M, 4.75M); re-picking nearby Basic values would remove several loading fees.

## 3. RGB version (the earlier 43 x 50 mm board, re-done on the same ideas)
ESTIMATE from the earlier BOM (132 RGB LEDs, ATmega169PA-class MCU, LIS2DW12, charger, regulator):
- 132 RGB LEDs x 4 pads = 528 LED joints; about 700 joints per board in total.
- Fewer unique lines than the white board (one LED type instead of three sizes): about 12-15 lines, about 8-10 extended.
- RGB LED: JLCPCB C404279 (0.8 mm common-anode stand-in), Extended, 14,075 in stock on 2026-10-05, about $0.047 each (about $6.2 per board). The original Harvatek part is obsolete with zero JLCPCB stock.
- Risks that cost money or time: 0.5 mm pad pitch with 0.3 mm pads (fine-pitch stencil), arbitrary LED rotation, common-anode vs common-cathode (matrix polarity flips), row current limits on the 22-row matrix, and routing density (see POLAR-TRACES.md).
| Line | Two-sided (Standard) | One-sided (Economic) |
|---|---|---|
| PCB + shipping | about 93 | about 93 |
| Assembly setup + stencil | 67.54 | 9.71 |
| Extended loading (8-10 types) | 12-30 | 12-30 |
| Joints (about 3,500 for 5 boards) | about 7 | about 7 |
| Parts via JLCPCB (about 18-22 per board) | about 100 | about 100 |
| Cells / battery (ours) | about 100-150 | about 100-150 |
| **Total for 5** | **about 380-450** | **about 320-390** |
So the RGB version costs about the same as the white one at 5 boards; its real cost is risk (fine pitch, routing, polarity), not money.

## 4. What I would do
1. Quote the real files in both modes before deciding; the $58 two-sided premium is small next to the cells and the parts.
2. Accept two-sided assembly for the first order (43 mm board, parts on both sides), because it keeps the board small and makes the back self-protecting.
3. Hand-fit only the cells, battery plugs' wires and any spares; let JLCPCB do every SMT part including the 0201 LEDs.
4. Consolidate resistor values to Basic parts before the quote, and re-check stock on the order day.
5. Ask JLCPCB support again about 6-degree LED rotation with the real placement file (earlier chat said it might be possible with an extra step: not guaranteed).

## 5. Things I could not verify
- JLCPCB's per-joint fee and the exact extended-part fee today (one source says $1.50, others $3).
- Whether Economic assembly accepts a board this shape and size and our part mix.
- Whether JLCPCB will place the heavy back-side parts (1210 inductors, JST header) in a second pass without special handling.
- Stock and price of the solar cells and TinyCircuits cells.
