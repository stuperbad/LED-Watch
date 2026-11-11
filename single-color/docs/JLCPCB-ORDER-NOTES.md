# JLCPCB order notes (revision C, quote of 2026-11-11, nothing ordered)

**Files:** `hardware/production/` (gerbers zip, `assembly/BOM.csv`, `assembly/CPL.csv`), all from the 04:06 save of `hardware/LED Watch - Single Color.kicad_pcb`.

**Quote, 5 boards:** PCB $87.82 + assembly $237.71 = **$325.53** before shipping and duties (2-3 day assembly +$49.63). Specification: 4 layers, 1.6 mm, black, white silk, ENIG 1 U", 1 oz / 0.5 oz, plugged vias, 0.15 mm / (0.25 / 0.3) vias, flying probe, Standard PCBA both sides, edge rails by JLCPCB, confirm parts placement **Yes with "do not confirm automatically" ticked**, parts by customer. In the BOM step three lines have to be ticked by hand (0402 LED, JST plugs, USB4110).

**Why the previewer looks wrong:** JLCPCB's 3D viewer uses its own library models by LCSC number, often generic boxes, and says "preview for reference only; check the final placement in the DFM analysis in the order history 4-6 hours after the order". Heights are wrong (second LEDs look taller than the hour LEDs; real heights 0.4 / 0.4 / 0.6 mm), the USB-C is a box about 8.4 mm deep (GCT's drawing: body 7.35 mm, 7.70 mm with the shell lip).

**J2 (USB4110-GF-A, C5143397, back side):** JLCPCB's model has its origin about 1.10 mm further out than our footprint's, so the placement file says X 115.65 (raw 116.75; `tools/make_bom_cpl.py`, `POS_FIX`). In the viewer the contact pins and the four mounting tabs then sit on their pads. The real mouth is about 0.58 mm inside the board rim (sheet: `docs/j2-placement-sheet-2026-11-11.png`).

**If JLCPCB's engineer contacts us (within 72 h of the order):**
- Send the J2 sheet. Say: pins on the pad row, tabs on the four shell pads, mouth must stay inside the rim, never beyond it; the plug has to seat.
- Pin 1 of the connectors J1 / J1B is at the minus mark (GND); U5 pin 1 triangle; D50 cathode band; LED polarity as in the viewer (checked 2026-10-14 and again 2026-11-11, no part looked rotated).
- Do not let them "fix" J2 by moving it to the model's origin: the raw CPL position would put the connector 1.1 mm too far out.
- Optional: set "Photo Confirmation" in the assembly options so they photograph the placement before reflow (cost not yet read off the quote page).
- Known and accepted assembly-side findings (JLCDFM): U1 leads flush with its 0.2 mm pads (pin left / right edge), SW1 / SW2 ground tab without a pad and lead overlap 0.73 against 0.75, U1 / U4 exposed-pad vias (lead to hole 0 mm).

**Before ordering:** the JLCPCB cart now holds draft items for the current board, created by the quote flow on 2026-11-11 (PCB "LED Watch - Single Color - gerbers_Y8", $87.82, and Standard PCBA both sides, $237.71; nothing paid or ordered). The old "Y42_routed_v4" item is gone from the cart. Before ordering, delete these drafts and re-upload the final files so the cart holds the current save only; check "Photo Confirmation" for J2 (its price could not be read from a reopened draft because the parts list does not reload there; read it on a fresh upload); re-run the JLCDFM assembly check after any new save; confirm the Murata piezo spec once murata.com is back.
