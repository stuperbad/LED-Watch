# JLCPCB order settings, quote of 2026-11-17 (revision C, USB-C board, nothing ordered)

Files uploaded to the JLCPCB cart: `hardware/production/` as of the 2026-11-14 03:35 save (the repo's production files were refreshed afterwards from the 2026-11-17 23:43 save, copper tweaks only; the cart must be rebuilt from them after the review) (gerber zip, `BOM.csv`, `CPL.csv`). The quote below is an autosaved draft in the JLCPCB account; it has not been paid.

**Total: $334.74 for 5 boards, assembled on both sides** (PCB $88.87 + assembly $245.87), before shipping (UPS Express Saver about $26) and duties. Build time: PCB 3 days, assembly 3-4 days (2-3 days would add $49.63).

## Pictures
- `jlcpcb-2026-11-17/pcb-settings-full.png`: every PCB option on one tall picture (stitched from three screenshots, nothing edited).
- `jlcpcb-2026-11-17/assembly.jpg`: assembly options with the advanced block open.
- `jlcpcb-2026-11-17/bom-matched.jpg`, `bom-ticked.jpg`: parts list before and after ticking the three lines JLCPCB leaves unticked.
- `jlcpcb-2026-11-17/viewer-top.jpg`, `viewer-bottom.jpg`: JLCPCB's placement viewer (its own library models, reference only).
- `jlcpcb-2026-11-17/quote.jpg`, `quote-remark.jpg`: price breakdown and the remark / attachment box.

## PCB options
| Option | Chosen | Why / note |
|---|---|---|
| Layers, size | 4, 42 x 51.18 mm (read from the gerbers) | In1 is the ground plane |
| Quantity | 5 | minimum for the assembled quote |
| Thickness | 1.6 mm | default |
| Colour / silkscreen | Black / white | +$8.00 for black |
| Material | FR4 TG155 | switched on automatically by the 0.15 mm via choice, not picked by hand |
| Surface finish | ENIG, 1 U" | flat pads for the 0201 / 0402 LEDs and the QFN parts; +$17.20 |
| Copper | 1 oz outer, 0.5 oz inner | defaults |
| Via covering | Plugged | |
| Min via | 0.15 mm hole (0.25 / 0.3 mm) | the design uses 0.3 / 0.15 vias; this choice also switches on the 4-wire Kelvin test (+$16.87) and costs +$34.32 itself |
| Outline tolerance | +/-0.2 mm (regular) | precision was greyed out |
| Electrical test | flying probe | only choice offered |
| Confirm production file | Yes, "do not confirm automatically" ticked | we look at JLCPCB's file before production (+$1.05) |
| Everything else | No / default | gold fingers, castellated holes, press-fit, edge plating, blind slots, UL marking, backdrill, humidity card, serial number mark |

## Assembly options
| Option | Chosen | Note |
|---|---|---|
| Type, sides, quantity | Standard, both sides, 5 | Economic is greyed out for both sides |
| Edge rails / fiducials | added by JLCPCB | board becomes 70 x 71.18 mm; depanelling service not taken |
| Confirm parts placement | Yes, "do not confirm automatically" ticked (+$0.45) | JLCPCB sends the placement for approval; they wait up to 72 h and then proceed if not told otherwise, unless the tick is set |
| Parts selection | by customer (self-service) | LCSC numbers are in `BOM.csv` |
| Photo Confirmation | Yes (+$8.27, charged after review, not in the order total) | JLCPCB's tooltip: images of the **assembled** boards are posted in Order history for confirmation, delays in confirming may delay delivery. A look at the finished boards before they ship, not a check before reflow. |
| Other advanced options | defaults | bake, cleaning, packaging (anti-static bubble film), special stencil, high-temperature solder paste, no function test, no nitrogen reflow, assembly remark "No" |
| Parts list | 33 lines matched, three ticked by hand | 0402 indicator LEDs (C20613596), JST plugs (C160402), USB-C (C5143397) |

Price lines: setup $51.50, stencil $16.54, components $103.64 (33 items), feeders $51.15, SMT assembly $5.42, parts-placement confirmation $0.45, X-ray $8.25, packaging $0.50, special components $0.15, Photo Confirmation $8.27.

## Cart state (2026-11-17, late evening)
- The two old drafts from 2026-11-11 were deleted. The cart holds one order (PCB "gerbers_Y12" $88.87 + assembly $237.60 = **$326.47**); shipping estimate $31.07 (UPS Express Saver, DDP, 2-4 business days; DHL DDP $33.08, FedEx DDP $43.54), subtotal $357.54, estimated ship date 2026-11-24. Nothing paid.
- **Photo Confirmation ($8.27)** is *not* in the $326.47. The quote page lists it under "Advanced Options: the cost of the options below is not included in the Total Price; the final charge will be determined and paid after review".
- **The assembly remark is also an advanced option and shows "Quote after review"**: JLCPCB reads the remark and may price or question it; the build time line says "add 1 more day (extended by advanced options)".
- **Product Description** (customs category, sets the HS code on the paperwork): Reserch\Education\DIY\Entertainment / **Development Board, HS code 847330**.
  - Tested: with *Programmable Controller (HS 853890)* the cart showed exactly the same merchandise total and shipping prices as with *Development Board*. The category does not change the cart price. Whether duties are settled differently at the border was not testable here.
  - Other branches in the dropdown: Sensor\Controller\Precision Instrument (sensors, HS 9025-9030), Office Appliance and Accessories (PC, mouse, keyboard, SSD, gateway, reader: HS 8473 / 8517), Audio and Video Appliance, Smart Product and Accessories (Charger, DC power supply: HS 8504; "Others" asks for a free-text description), Household Appliance, and "DIY - HS 902300", "Robot - 847990", "Others" under Research / DIY. "Others" entries ask for a free-text production description.
- **Assembly Remark** (397 of 500 characters, no attachment; the sentence asking for a photo / confirmation was removed so it cannot read as a request): "Parts by customer, both sides. J2 (USB4110-GF-A, C5143397, bottom side): the CPL X is already corrected by -1.10 mm for the library model origin (raw 116.75, CPL 115.65). Pins must sit on the contact pads and the 4 shell tabs on their pads; the mouth must stay inside the board edge, never beyond it, so a plug can seat. Please do not move J2 to the model origin. J1/J1B pin 1 is GND (minus mark)." PCB Remark empty. Cart order is now "gerbers_Y13" (the edit flow creates a new number each time).
- **Side effect of the edits:** the order's "File provided as" field now reads "Single Piece, pls help me repeat the data" (it said "Complete File, just proceed with my own files" on the first build); panel format is still 1 x 1 and the price did not change. One board with JLCPCB adding the rails fits "Single Piece"; the setting is on the Bill of Materials step if it should be changed back.

## JLCPCB live chat, 2026-11-17 22:58 (human agent)
- Question sent: does an informational assembly remark (no service requested) add a fee, or is it only read by an engineer? First answer: "yes" (unclear). Second answer: "since you will checkout with 'Review before Payment' the advance option service charge will be issued into the quotation after the engineer completes the review."
- An order card for Y13 ($88.87) was also posted into the chat by mistake while sending.
- JLCPCB help article "Review Before Payment": the order is submitted without paying, an engineer reviews the BOM / CPL files and the advanced-option fees, the order goes to "Approved / Awaiting Payment", and the customer confirms the final cost before paying. Parts are held for up to 7 days. An approved order awaiting payment cannot be modified; the page does not say whether the customer can cancel after seeing the quote. So advanced-option charges (Photo Confirmation, possibly the remark) appear in that final quote before any money is taken.

## What to expect after paying
- The file check on the board comes first (confirm within 48 h, the tick above stops automatic confirmation). Then the parts-placement approval: JLCPCB's engineer corrects placement and polarity within 4-6 hours of the order and emails for confirmation, which is required within 72 hours (with our tick they wait). After assembly the Photo Confirmation images go into Order history for approval before the boards ship.
- Possible questions from JLCPCB's engineers (a guess, not something they have said): the USB-C connector (J2) position and the "board edge" overhang, the two JST plugs and the 0201 LEDs next to the ring. Answers are in `JLCPCB-ORDER-NOTES.md`; the J2 sheet is `j2-placement-sheet-2026-11-11.png`.
- Do not let anyone move J2 to the library model's origin; the placement file already carries the 1.10 mm correction (X 115.65).
- The viewer's 3D models are JLCPCB's own, so heights and the USB-C depth look wrong there; the real check is the DFM analysis in the order history 4-6 hours after the order.

## Not done
- Nothing was paid; no sheet was attached to the order.
- Category effect on duty not tested (see above).
