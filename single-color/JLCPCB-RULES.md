# JLCPCB design rules for this watch (with sources)

Primary source for every number below: JLCPCB "PCB Manufacturing & Assembly Capabilities" page, https://jlcpcb.com/capabilities/pcb-capabilities
(Rigid PCB Capabilities -> tabs "Drilling" and "Traces"). Rows quoted VERBATIM from the page text on **2026-10-11** (read in a browser, element by element). JLCPCB updates this page; re-read it before ordering.

## CORRECTION (2026-10-11)
My earlier file (2026-10-09) used **0.30 mm** as the hole-to-copper rule for our vias. That was wrong: 0.30 mm is JLCPCB's row for **PTH pad holes** (component pads), not vias. For **vias** the page says **0.2 mm**. That is why the polar design looked ~1 mm per lane band bigger than your hand-built RGB board. Your hand layout (0.2 mm drill, 0.1 mm track, 0.35 mm lane pitch) puts the via hole edge exactly 0.20 mm from the neighbouring lane's copper = JLCPCB's stated minimum. So the hand layout is on the real limit, not violating it.

## Rows that matter (verbatim)
| Page tab / row label | Value on the page |
|---|---|
| Traces / Inner layer via hole to copper clearance | **0.2mm** |
| Traces / Via hole to Track | **0.2mm** |
| Traces / Inner layer PTH pad hole to copper clearance | 0.3mm (component through-hole pads only; we have none besides slots) |
| Traces / PTH to Track | 0.28mm ("0.35mm is recommended, minimum 0.28mm") |
| Traces / NPTH to Track | 0.2mm |
| Traces / Min. track width and spacing (1 oz) | 0.10 / 0.10 mm (4/4 mil); "1- and 2-layer: 0.10 / 0.10 mm"; **"Multilayer: 0.09 / 0.09 mm (3.5 / 3.5 mil). 3 mil is acceptable in BGA fan-outs."** |
| Traces / Track width tolerance | ±20% (0.1 mm track finishes 0.08-0.12 mm) |
| Traces / Pad to track clearance (1oz) | 0.1mm ("Min. 0.1 mm (stay well above if possible)") |
| Traces / SMD pad to pad clearance (different nets) | 0.15mm; minimum SMD pad 0.25 x 0.25 mm |
| Traces / PTH annular ring | multilayer 1 oz: recommended 0.20 mm, absolute minimum 0.15 mm |
| Traces / Same-net track spacing | 0.25mm (hatched grids; not an issue for us) |
| Drilling / Min. Via hole size/diameter | **0.15 mm hole / 0.25 mm via diameter** multilayer ("0.1mm/0.2mm only available for board thickness <=1mm; ENIG/OSP surface finish required"); "Via diameter should be 0.1mm (0.15mm preferred) larger than Via hole size"; "Preferred Min. Via hole size: 0.2mm" |
| Drilling / Via Hole-to-Hole Spacing | 0.2mm |
| Drilling / Pad Hole-to-Hole Spacing | 0.45mm |
| Drilling / Hole position tolerance, through-hole size tolerance | ±0.075 mm; +0.13 / -0.08 mm |
| Drilling / Min. Non-plated slots | 1.0 mm (strap slots are far larger) |
| Top of page / HDI | Blind via 0.075-0.15 mm (laser, copper-filled), buried via 0.15-0.55 mm (mechanical, epoxy filled and capped); HDI min trace/space 3/3 mil; "Currently support (1-step / 2-step / 3-step)" |

Read on 2026-10-09 and NOT re-read on 2026-10-11 (still believed current; re-verify before ordering): copper to routed board edge 0.20 mm (Outline tab); silkscreen text height below 1.0 mm is "unidentifiable" (Legend tab); board thickness 1.6 mm +/-10% (Thickness row).

## What the instant-quote tool said (2026-10-11)
Uploaded `LED Watch pre-Claude October 2026/Gerber Files/LED Watch.zip` (your hand-built 4-layer RGB board) to https://cart.jlcpcb.com/quote without signing in or ordering. Result: "Detected 4 layer board of 50.28x42.87mm" (so the 43 mm circle plus the strap lugs), standard price $8 for 5 pieces, no warnings. The "Min via hole size" option defaulted to 0.3 mm, so the quote tool alone does not test via-to-copper clearance. JLCPCB's Gerber viewer / free DFM analysis require signing in (I did not sign in). To get their automatic check on that board: sign in, upload again, open Gerber Viewer / DFM.

## Third-party numbers (conflicting; NOT used)
Forum posts and a KiCad rules reference quote older or different figures (via to track 0.254 mm, PTH to track 0.33 mm, pad to pad 0.127 mm, inner-layer tracks 0.127 mm). Those are second-hand and out of date relative to the page above; they only serve as a reminder to re-check the page.

## What this means for us
- **Polar lane pitch** = drill/2 + track/2 + hole clearance = 0.075 + 0.05 + 0.20 = **0.325 mm** at the JLCPCB minimum; **0.345 mm** with 0.02 mm margin (our default). Was 0.425 mm. Your hand layout: 0.35 mm.
- Via 0.30 pad / 0.15 hole (or 0.25 / 0.15) is within limits. Hole position tolerance (±0.075) is already inside JLCPCB's stated numbers.
- Track/space 0.09 mm is allowed on multilayer boards; we keep 0.10 for margin and can use 0.09 where needed.
- Copper to board edge 0.2 mm; silk text >= 1.0 mm.
- KiCad: set hole clearance 0.2 mm, copper clearance 0.1 mm, min via 0.25, min through hole 0.15, hole-to-hole 0.2, edge clearance 0.2.
