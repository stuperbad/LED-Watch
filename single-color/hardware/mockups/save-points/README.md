# Save points

Frozen copies of the USB-C mock-up board, kept so any step can be returned to. Never edited after saving.

| File | What it is |
|---|---|
| `LED Watch - USBC in progress hand routing.kicad_pcb` | The owner's hand-routed board (2026-11-01 20:28): after deleting dead wire and unneeded vias by hand, before the scripted dead-end and pad-centre cleanup. 0 shorts, 1 open (VBUS A4/B9 pair). |
| `LED Watch - USBC hand routing 2 (21-09).kicad_pcb` | Owner's second round of hand edits, before the per-net reroute (SBU, LBUCK, OK_PROG, COL*_MCU, BAT_OK, IMU_INT, BTN1/2). |
| `LED Watch - USBC hand routing 3.kicad_pcb` | Owner's third round, saved after the reroute of 2026-11-01 (night): the owner's cleanups on top of the rerouted board. |
| `LED Watch - USBC hand routing 4 (ring quadrant lost).kicad_pcb` | Owner's fourth round (2026-11-01 23:47), saved as found: the south-west quarter (90 to 180 degrees) of all 11 ROW rings on In1 had been deleted by accident. The live board is this file plus those 11 arcs restored. 18 keep-out violations from the owner's unfinished cleanups are still in it. |
| `LED Watch - USBC hand routing 5 (before cell pad fix).kicad_pcb` | Owner's fifth round (2026-11-02 00:23), saved as found: cell pad SC1+ still on the separate net `SOLAR_IN`, SOLAR_IN with a 100 mm dead branch around the west side, COL9_MCU / COL10_MCU with 0.05 mm staircase pieces. |
| `LED Watch - USBC hand routing 6 (col 9-11 hand routed).kicad_pcb` | Owner's sixth round (2026-11-02 02:15), saved as found: COL9 / COL10 hand routed, vias moved next to the MCU pins. Before the outer COL ring is moved inward. |
| `LED Watch - USBC hand routing 7 (before outer arcs in).kicad_pcb` | Owner's seventh round (2026-11-02 02:17), saved as found: COL9 / COL10 hand routed, outer F.Cu COL arcs still at r 20.64 mm (0.31 mm from the board edge). 6 DRC items (ROW4 / ROW5 / GND via at 100.5, 87.75), 13 keep-out hits, all the owner's. |
| `LED Watch - USBC hand routing 8 (before net rename).kicad_pcb` | Owner's eighth round (2026-11-02 02:55): saved as found, before the five USB-C nets became /CC1 /CC2 /SBU /ISET /TS and D50 got its datasheet pads. |
| `LED Watch - USBC hand routing 9 (before DRC items fixed).kicad_pcb` | The board as installed at 02:58 (nets renamed, D50 datasheet pads), before the extra GND via at (100.71, 87.23) was removed and ROW4 was shifted 0.05 mm. 6 DRC items. |
| `LED Watch - USBC hand routing 10 (before U5 datasheet pads).kicad_pcb` | Board with the DRC items fixed (03:53), before U5 got TI's land pattern (owner asked for it, conflicts left for hand routing). 0 DRC items. |
| `LED Watch - USBC hand routing 11 (U5 hand routed).kicad_pcb` | Owner's board at 04:04 after re-routing around the new U5 pads: no ratsnest, but a dead TS stub still ran through U5 pad 3 (3 DRC items) and a few track ends were off pad centre. |
| `LED Watch - USBC hand routing 12 (before final cleanup).kicad_pcb` | Owner's board at 04:21 (zones re-read, keep-out 0): before the last dead copper was removed (2 zero-length COL10 pieces, the dead COL9_MCU via with its In1 spur, one of two stacked GND vias). |
| `LED Watch - USBC hand routing 13 (before silkscreen strip).kicad_pcb` | Board at 04:26 (final clean-up done, 0 DRC / 0 keep-out), before the part outlines, LED polarity dots and back reference texts were removed from the silkscreen. |
| `LED Watch - USBC hand routing 14 (before J1B x move).kicad_pcb` | Board at 04:40 after the silkscreen strip, before J1B was moved 0.3 mm to J1's x. 0 DRC / 0 keep-out. |
| `rev C 01 (before overlap cleanup).kicad_pcb` | revision C main board at 05:21, before 14 redundant pieces were removed (5 pieces lying on top of a longer piece of their own net, 9 pieces of 0.01 mm). |
| `rev C 02 (before detour step).kicad_pcb` | revision C main board at 06:07, before the detour step (BAT_OK, COL0_MCU, BTN1 re-routed shorter; dead BUZ_B branch removed; 99 buried / zero-length pieces removed). |
| `rev C 03 (detour re-routes rejected).kicad_pcb` | The board as installed at 06:31 with the router's shorter BAT_OK, COL0_MCU and BTN1 routes, which the owner rejected (they cross the crystal area / other traces). Not used. The live board went back to the 06:07 routes, keeping only the 99 buried or zero-length pieces removed and the dead BUZ_B branch (2 vias, 3 pieces) pruned. |
| `rev C 04 (before bigger numerals).kicad_pcb` | revision C board at 06:35 (after the detour step was reverted), before 12 / 3 / 6 / 9 were made 1.2 mm and U1 pin 40 became a no-connect. |
| `rev C schematic (before RESET no-connect).kicad_sch` | revision C schematic at 05:21, before the RESET label and its wire stub were replaced by a no-connect flag on U1 pin 40. |
| `rev C 05 (before C54 hand edits ported).kicad_pcb` | revision C main board at 06:56, before the owner's hand edits around C54 (made by mistake in the old USB-C mock-up file, saved 07:20) were carried over: 121 pieces removed, 116 added (COL2, COL2_MCU, COL6_MCU, COL9_MCU, COL10_MCU, +3V3, BATT, OK_PROG, GND). |
| `USB-C mock-up as edited by the owner 07-20.kicad_pcb` | The frozen mock-up file `mockups/LED Watch - USB-C.kicad_pcb` as saved at 07:20 with those hand edits (on the older routing: it lacks the 14 overlap pieces / 99 buried pieces / BUZ_B dead-branch removals, the bigger numerals and the RESET no-connect). |
