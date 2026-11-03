# Static layout (draft for hand routing), 2026-11-03

Files: `LED Watch - Static Layout.kicad_pro` / `.kicad_sch` / `.kicad_pcb` (open the .kicad_pro). Picture: `static-layout.png`. Made from the main revision C board as it was at 00:18 (with the C56 move), the main files are not touched.

**What it is:** the parts in the owner's layout, only the copper of the moved parts and what sat on their pads ripped up, everything else left as drawn. Routing the open connections is for the owner (magenta lines in the picture; in KiCad: the ratsnest). Nothing here has been routed or optimised by a script.

## Placement (centre, mm)
| Part | Was | Now | Notes |
|---|---|---|---|
| D51 (TVS) | 110.44, 108.5 horizontal, under C55 | **107.5, 94.0**, vertical | next to D50; VBUS pad south, GND pad north; the old GND via (107.5, 92.4) sits on its north axis |
| C50 (4u7) | 107.5, 93.5 vertical | **108.5, 91.5**, horizontal | row above the diodes; SOLAR_IN pad west, GND pad east |
| R68 (CC1 5.1k) | 109.84, 96.5 horizontal | **110.9, 91.5**, horizontal (rotated 180) | row above the diodes, 2.4 mm from C50; CC1 pad east, GND pad west |
| D50 | 109.5, 94.0 | unchanged | the UPDI column (x 109.5) runs north between C50 and R68 |
| C56 | 106.0, 104.5 | 105.85, 103.7 | already moved on the main board 00:18 |
| everything else | | unchanged | C53, R69, R70, R72, L1, U5, C55, R71 left where they were |

## Copper ripped (it is open, not deleted from your knowledge)
- D51's two tracks under C55 (VBUS stub to C55, GND link to the via).
- The own copper of the moved pads: SOLAR_IN from C50.1 down to the via at (107.8, 97.2) (3 pieces); the GND piece C50.2 to its via; the whole CC1 route J2.A5 to R68.1 (6 pieces); the GND route R68.2 up to the via (110.575, 95.135) (4 pieces).
- Sitting on the new pads: one BUZ_B piece, (108.552, 92.352)-(107.435, 91.235) (the left arm's diagonal), one UPDI piece, (109.5, 91.85)-(108.56, 90.91) (UPDI's way out of D50's north pad).
- Left as they were, now dangling: the BUZ_B via at (107.425, 91.235) and the rest of that arm, the UPDI stubs (109.5, 92.915)-(109.5, 91.85) and (108.56, 90.91)-(107.14, 90.91), the GND via (107.5, 92.4).

## Open connections (7): C50.1 SOLAR_IN, C50.2 / R68.2 / D51.2 GND, R68.1 CC1 (to J2.A5), D51.1 VBUS, UPDI (D50.2 to its old way west), BUZ_B (the cut arm). Check list as you go: DRC with schematic parity, `tools/usbc_mockup/zonecount.py` (keep-out), traces leave pads from the ends along the axis.

## Checks of the draft as saved
No new clearance, short, crossing or outline-overlap item against the main board; the only new DRC items are the dangling pieces listed above. 0 keep-out items. Zones refilled.

## Getting it back into the main files
When you are done, tell me: I compare the modification times, diff your board against this draft and carry your routing over to `../LED Watch - Single Color.kicad_pcb` (the main board stays the source of truth; this folder is history).
