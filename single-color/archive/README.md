# Archive

Nothing here is needed to build or order the current board (see `../hardware/`). It is kept so the history and the thinking are not lost.

| Folder | What it is |
|---|---|
| `boards/43.5mm-and-earlier/` | the previous board generation: `Y43_final` (43.5 mm, 2026-10-12) and its routing attempts (`Y43_arc`, `Y43_poly`, `Y43_dog`, `Y43_rip12`), its Gerbers (`fab/`), assembly files (`asm/`) and plan |
| `boards/X42/` | the first 42 mm placement study |
| `early-layout-generators/` | the first, fully scripted layout generators (`gen_rings.py`, `plan_board.py`, `write_pcb.py`), early ring/solar experiments (`rings*`, `scan*`, `sweep_top*`), and the old simulator data export that read `plan.json` |
| `schematic-old/` | the pad/USB-charged schematic variant and the old schematic project file |
| `work/` | scratch files from the RGB board outline |
| `local-only/` (not in git) | ~250 MB of intermediate boards from the routing work (`Y43-intermediates/`, including the hand-edited `Y42_routed_v2.kicad_pcb`) and the old layout experiments (`layout-experiments/`); only on the author's disk |

Old file names to current ones: `Y42_routed_v4` = `hardware/LED Watch - Single Color` (revision A), `Y43_mockD_pogo8` = `hardware/source/layout-D-hand-placement`,
`schematic/watch_solar` = `hardware/LED Watch - Single Color.kicad_sch`, `boards/Y43/fab42` = `hardware/production/gerbers`, `boards/Y43/asm42` = `hardware/production/assembly`.
