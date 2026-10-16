# rgb/archive

Nothing here is needed to open the current RGB project (`../LED Watch - RGB.kicad_pro`). `2026-10-14 old RGB board ...` is the previous RGB project, put here when the new RGB design took over the file name `LED Watch - RGB`. `pre-claude/` holds the RGB work as it was before the single-colour redesign.
File names start with the date of the file; the original names are kept in the rest of the name.

| Folder | What it is |
|---|---|
| `2026-10-14 old RGB board - routed, Harvatek LEDs, ATmega165PA` | the old RGB project exactly as it was (schematic, routed board, project, library tables) plus its `production/` (Gerbers 2025-12-08, the 2026-10-05 fab quote work) and `scripts/`. Fully routed (DRC 0 errors, 0 unconnected) but not buildable: its LEDs and MCU are out of stock at JLCPCB. Its ring layout and net assignment live on in the new project |
| `2025-10-28 RGB version - first RGB schematic` | the first RGB schematic (+ project and netlist) |
| `2025-11-18/19 RGB empty version ...` | the empty (unrouted) board and schematic, and the Freerouting `.dsn` / `.ses` / `.rules` exports |
| `2025-11-19 ... 2025-11-25 RGB board - ...` | the 4-layer routing attempts, each a board + project file |
| `2025-12-08 RGB board - last version committed before the Oct 2026 edits` | the board, schematic, project and netlist exactly as the repository had them before your October 2026 edits became the main project |
| `2026-10-05 snapshots taken before the board edits` | copies of the board saved right before the 2026-10-05 edits |
| `gerbers-loose-copies/` | an earlier Gerber plot that sat at the top level of the folder (the newer set is in `../production/`) |
| `kicad-backups/`, `autosaves-and-caches/` | KiCad's automatic backups, autosaves, caches and logs |

Dates are the original file times (the repository checkout resets them).
