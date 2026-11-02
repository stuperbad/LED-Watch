# Layout audit and JLCDFM comparison, revision C (2026-11-02)

Purpose: numbers for the design review (the first review round criticised cleanliness and avoidable redundancies) and a ranked list of what is still worth changing before the order. Tools: `tools/audit_board.py` (cleanliness numbers), JLCDFM (jlcdfm.com, free, run on the Gerber zips of revision B (archive) and revision C), JLCPCB's quote tool.

## JLCDFM, red / orange / green items (PCB DFM)
| Check | Rev B (archived) | Rev C | |
|---|---|---|---|
| Sharp trace corner | 0 / 0 / 0 | 0 / 0 / 0 | |
| Trace spacing | 0 / 9 / 18 | **27** / 6 / 15 | worse: see below |
| Trace width (0.10 mm) | 100 / 0 / 0 | 100 / 0 / 0 | accepted: JLCPCB 4-layer minimum is 0.09 mm |
| Pad spacing | 21 / 22 / 57 | 7 / 34 / 59 | better |
| PTH to trace clearance | 0 / 64 / 36 | 0 / 100 / 0 | all orange |
| Annular ring (0.15 / 0.30 mm vias) | 100 / 0 / 0 | 100 / 0 / 0 | accepted (JLCPCB's own via option) |
| Via to pad | 0 / 2 / 55 | 0 / 1 / 54 | |
| Soldermask bridge | 0 / 12 / 38 | 0 / 12 / 45 | |
| Solder mask opening exposing trace | 18 / 48 / 30 | 7 / 88 / 5 | |
| Negative soldermask expansion | 0 / 40 / 0 | 0 / 40 / 0 | |
| Silkscreen to pad | 100 / 0 / 0 | 32 / 18 / 4 | better (outlines and dots gone) |
| Silkscreen to hole | 87 / 5 / 8 | 55 / 0 / 1 | better |
| Silkscreen line width | 0 / 73 / 0 | 0 / 10 / 0 | better |
| Unconnected via | 0 / 2 / 0 | 0 / 0 / 0 | |
Everything else 0. SMT DFM (BOM + CPL) was not re-run: the tool's BOM matching dialog would not open from here; JLCPCB's own placement viewer and quote showed no spacing or collision problem.

**The 27 red trace spacings** are gaps of exactly 0.100 mm (JLCDFM's red limit is "below 0.1", it shows "0.1 mm"). Measured with exact arcs (not KiCad's polygon approximation) there is **no pair below 0.0995 mm**, but there are 238 pieces pairs at exactly 0.100 mm on revision C (149 on revision B): the hand-routed area around the MCU and the crystal on the back (COL1 / IMU_INT, COL1 / COL9_MCU, BTN1 / +3V3, COL5_MCU / COL4_MCU, COL9_MCU / UPDI). Within JLCPCB's capability (0.09 mm), but with zero margin; opening them to 0.12 mm or more is the main remaining "tightness" item.

## audit_board.py (before the cleanup below)
| Item | Count | Comment |
|---|---|---|
| Pieces not on 0 / 45 / 90 degrees | 260 | almost all radial stubs and hooks of the LED rings (14-15 per COL net): the rings are at 6 degree steps, they cannot be 45 degree |
| Pieces shorter than 0.15 mm / 0.30 mm | 293 / 819 | mostly the same ring hooks and 0.05-0.1 mm jogs at pad exits |
| Corners of exactly 90 degrees | 23 | candidates for 45 degree chamfers |
| Acute corners (below 90 degrees) | 6 | BUZ_A, BUZ_B, OK_PROG, BTN2, VBAT, COL9 |
| Same-net pieces lying on top of each other | 5 real overlaps + 9 pieces of 0.01 mm | **removed 2026-11-02** (14 pieces; DRC unchanged) |
| Track ends in a pad but off its centre | 174 by bounding box (an overcount: rotated 0603 pads have a larger box); cleanup notes had 81 | to be re-measured with the true pad shape |
| Routed length / straight distance, 2-pad nets | BAT_OK 3.9 (23.6 mm for 6.0), COL0_MCU 3.6, **BUZ_B 3.4 (76 mm for 22)**, COL11_MCU 2.4, BTN1 / BTN2 / IMU_INT / LBOOST / TS about 2.0-2.1 | detours around the crystal / MCU keep-outs and the 1.6 mm strap slot area |
| Vias | 361 (59 GND) | |

## Pad exits (owner's question)
All pads are left from the **outer end of the pad, along its axis, from its centre**. That is the right way for small SMD parts: the copper on both ends of a 0402 / 0201 is symmetric (no tombstoning), the joint stays visible, and nothing runs under the body where a bridge cannot be seen. Leaving from the inner edge (between the two pads, under the part) is acceptable on big pads and in hand work, but at 0.2-0.5 mm gaps it invites solder bridging and hides the track under the part; leaving from a pad's side corner makes an uneven solder pull. So the current style stays; the pad-centre rule is about the track ends snapping reliably, not about the exit side.

## What is left, ranked (each step guarded by DRC and the keep-out count, with a save point)
1. **Open the 211 gaps at 0.100 mm to 0.12 mm or more** (32 clusters after the cleanup, mostly the dense back-side area between MCU and USB-C: COL2 / COL7_MCU 36, UPDI / +3V3 18, CC1 / SBU 15) **only in place, without changing any net's route**; not done: a router re-route at 0.12 mm was started and stopped (same method the owner rejected for the detours). The gaps are exactly the JLCPCB limit, not below it.
2. **23 corners of exactly 90 degrees to 45 degree chamfers** where room allows.
3. **Merge micro pieces** (0.01-0.15 mm) outside the ring hooks (`tools/merge_collinear.py`, `tools/usbc_mockup/refit.py` exist).
4. ~~Shorten the worst detours~~ **tried and rejected 2026-11-02**: the router's shorter BAT_OK, COL0_MCU and BTN1 crossed the crystal area / traces the owner does not want crossed; they stay as hand-routed. Only dead copper was removed (BUZ_B 76 -> 65 mm, 2 vias, 99 buried pieces). Any further detour work would be by hand, owner's call, with a picture first.
5. Re-measure the off-centre pad ends with the true pad shape and fix the real ones (the pad-centre rule).
6. Schematic tidy (see ERC: lone RESET label, annotation warning): to be listed together with what the reviewer flagged.
