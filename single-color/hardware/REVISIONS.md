# Hardware revisions

One living set of files, `led-watch.*`, instead of a new filename per attempt. The revision is in the title block of the schematic and the board and in the
Gerber job file; every released revision gets a git tag (`rev-A`, `rev-B`, ...), so `git checkout rev-A` brings back exactly what was ordered.

| Rev | Date | Status | What it is |
|---|---|---|---|
| **A** | 2026-10-14 | order candidate (quote $308.63 for 5 assembled boards; not ordered yet) | 42.0 mm round board, layout "D", 132 ring LEDs + 7 mode LEDs, Murata piezo, 4-pad pogo programming row. DRC 0 errors / 0 unconnected (7 deliberate silk-height warnings). Was called `Y42_routed_v4` during the layout work. |

How to make the next revision: change `REVISION` in `gen_schematic.py`, set the revision in the board's title block (File > Board Setup > Title block, or `pcbnew` python),
regenerate `production/` (commands in `../README.md`), commit, tag.

Earlier attempts (43.5 mm board, wrist-strap lug experiments, X42) are in `../archive/boards/`.
