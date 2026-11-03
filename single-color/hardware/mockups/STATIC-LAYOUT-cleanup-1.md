# Static layout, cleanup pass 1 (2026-11-03)

`LED Watch - Static Layout (cleanup 1).*` = a copy of **your** `LED Watch - Static Layout.kicad_pcb` as saved at 00:55:38, cleaned. Your file is untouched. Picture: `static-layout-cleanup-1.png` (red = gone, green = new, gold = unchanged).

## What was changed (nothing else)
1. Dangling GND via at (107.715, 92.126): removed.
2. C50 moved 0.01 mm (y 93.36 -> 93.37) so it sits on R68's row; the shared GND via moved from (108.95, 93.35) to (108.95, 93.37); one straight piece from each pad (0.52 / 0.54 mm) replaces the pieces with the 0.01-0.03 mm kinks.
3. R68.1 (CC1): now leaves the pad end along the axis (east 0.30 mm), 45 degrees south-east, south into the via (111.1, 94.01). Was: 0.32 mm down from the side of the pad.
4. R72.1 (SBU): the via moved 0.05 mm onto the pad axis, (109.15, 102.475) -> (109.2, 102.475); straight piece pad to via; the two dead spurs next to the via removed; the In1 piece follows.
5. SBU at x = 110.923 / 110.925 (3 pieces, one of 0.003 mm) -> one vertical at 110.925 (the hole clearance to the CC1 via is exactly 0.325 mm there, so x = 110.925 is the only place); and the SBU vertical at the via (109.72 vs the via at 109.70) put on the via centre.
6. Ten more chains with a micro piece or an end off a pad / via centre re-built from their own lines (ends exactly on the centre, micro pieces dropped, corners moved at most 0.05 mm): VBAT (C53.1 to the via), GND (D51.2 to the shared via), GND (R70.2), SOLAR_IN (C50.1 to L1), COL7_MCU (F.Cu and B.Cu), COL3_MCU (In1), ISET (R70.1 to U5), SBU (J2.A8 branch), CC1. Every rebuild was checked against the 0.10 mm copper and 0.20 mm hole clearance before it was accepted; the VBUS chain J2.A9 to U5 and COL3_MCU on F.Cu were left alone because the rebuild would have tightened a limit.

## Checks
Against your file: 0 open connections, 0 new DRC items, keep-out 0, every piece 0 / 45 / 90 degrees, no dead ends. Among the 184 pieces you added, those under 0.15 mm: 32 -> 17; under 0.05 mm: 18 -> 2. (The base board has about a dozen more 0.003-0.035 mm pieces elsewhere, e.g. BUZ_B at (113.19, 93.05); I did not touch those.)

## Left for you (design pieces, not artefacts)
- Two artefacts left: a 0.01 mm piece at (106.825, 95.335), COL3_MCU F.Cu (snapping it breaks the 0.2 mm hole clearance to the COL1 via) and a 0.028 mm piece at (104.75, 100.6), VBAT In1. 16 chamfer / jog pieces between 0.05 and 0.15 mm (e.g. SOLAR_IN 0.12 and 0.099, +3V3 0.057 and 0.085, COL2/4/6 0.085-0.132, CC1 0.057 / 0.071 / 0.12, GND at R70.2 0.078, SBU 0.106 / 0.14).
- C53.1 (VBAT) now leaves the side of its pad (0.31 mm sideways; it was along the axis before your change); C53.2 (GND) and R72.2 (UPDI) leave sideways as well (these two were already so).
- CC1 is 7 mm with two vias (it was 4.2 mm, none); column alignment: C50 x 107.95 vs D51 107.98, R68 x 110.0 vs D50 109.98.
- C56: here at (105.83, 103.9); the main board has it at (105.85, 103.7).

## Ported to the main board (2026-11-03 01:22)
The owner kept editing `LED Watch - Static Layout (cleanup 1).kicad_pcb` after this pass (saved 01:20:41: C55, C56, R71 and U5 moved 0.15-0.34 mm to the right, the U5 corner re-routed, a few lane changes). That saved file was carried over to `../LED Watch - Single Color.kicad_pcb` as it is (main board unchanged since 00:18; silkscreen, zones, board settings, footprint values and nets identical, only part positions and copper differ). Restore point: `save-points/rev C board (before layout port).kicad_pcb`. These mock-up files are history from here on.
