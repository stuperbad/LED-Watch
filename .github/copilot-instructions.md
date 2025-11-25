# Copilot instructions for LED-Watch repository

This repository is a KiCad PCB project for an LED watch (hardware design files, gerbers, and helper scripts). These instructions help an AI coding/design agent be productive and avoid common pitfalls.

Overview
- Purpose: PCB and schematic design files for multiple board variants (RGB and empty-RGB variants). Work includes schematic edits, PCB layout, footprint placement scripting, and generating manufacturing outputs (gerbers, drill files, BOM).

Big picture & architecture
- Main artifacts: KiCad schematic files (`*.kicad_sch`), PCB layout (`*.kicad_pcb`), netlists (`*.net`), board rules (`*.rules`), gerbers (`*.gbr`, `*.drl`) and a gerber job (`LED Watch-job.gbrjob`).
- Multiple variants: files include variant suffixes like `- RGB version` and `- empty RGB version`. Backups live in folders ending with `-backups` and autosaves have `~` or `_autosave` prefixes.
- Scripts: the repo contains KiCad pcbnew Python scripts (example: `radial ring script`) that programmatically place footprints using the `pcbnew` Python API. Inspect scripts before changing board geometry.

Key files to consult first
- `README.md` — project notes and parts links.
- `LED Watch.kicad_pcb`, `LED Watch - RGB version.kicad_pcb`, `LED Watch - empty RGB version.kicad_pcb` — primary board files. Pick the variant explicitly before editing.
- `radial ring script` — example pcbnew Python snippet that positions footprints (uses `board.FindFootprintByReference` and `SetPosition`). Run inside KiCad's PCB editor scripting console.
- `LED Watch-job.gbrjob` and existing `*.gbr`/`*.drl` files — existing manufacturing outputs; update them after layout changes.
- `*.csv` (e.g., `LED Watch - empty RGB version.csv`) — BOM/parts list exports.
- `freerouting.dsn` / `temp-freerouting.dsn` — FreeRouting sessions / autorouter exports. These indicate autorouter usage and should be preserved if present.

Developer workflows & actionable steps
- Opening and editing: open `.kicad_pcb` files in KiCad PCBNew (GUI). Many changes (footprint positions, copper, silkscreen) are intended to be done inside KiCad so downstream files (gerbers) remain consistent.
- Running placement scripts: open PCB editor → `Scripting Console` → run the script (the `radial ring script` uses `pcbnew` API). Example: open the script, paste into the console or run via KiCad's embedded Python.
- Generating gerbers: use KiCad GUI `File → Plot` and `File → Fabrication Outputs → Drill Files`, or reuse the existing `LED Watch-job.gbrjob` as a template. There is no repository build system—this is a manual KiCad workflow.
- Autorouting: `.dsn` files are FreeRouting sessions; to autoroute, export the appropriate session from KiCad and re-import as needed. Do not overwrite session files unless intended.
- BOM and parts: BOM CSV files are present; update BOM from the schematic editor (`Tools → Generate Bill of Materials`) when changing parts.

Project-specific conventions
- Variant names: include `RGB` or `empty RGB` in filenames. When making edits, confirm which variant you are targeting and update only that variant unless user asks to unify variants.
- Footprint references: the `radial ring script` expects footprints named like `U2..U133` (scripts build lists with `f"U{i}"`). When adding or renaming footprints, keep reference numbering consistent or update the script accordingly.
- Keep backups intact: do not delete or modify files in `*-backups/` or autosave files (`~*`, `_autosave*`) unless the user instructs.

What agents should avoid / ask before doing
- Avoid making unilateral edits to multiple `.kicad_pcb` variants. Ask which variant is canonical before cross-editing.
- Avoid deleting existing gerbers or the `.gbrjob` file; instead produce new gerbers alongside existing outputs.
- Ask before running destructive autorouter passes or large reposition scripts on the user's chosen board file.

Examples from repo
- The `radial ring script` uses:
  - `board.FindFootprintByReference(f"U{i}")` to locate footprints
  - `fp.SetPosition(pcbnew.VECTOR2I(...))` to place footprints
  Run it from KiCad's PCB editor scripting console rather than editing `.kicad_pcb` text by hand.
- Gerber outputs: `LED Watch-F_Cu.gbr`, `LED Watch-B_Cu.gbr`, `LED Watch-NPTH.drl`, `LED Watch-PTH.drl` are present — use these names as references for manufacturing file expectations.

If you need to change workflows
- If a CLI or script-based generation is required, request permission and specify the exact variant filename to operate on. The repository currently has no automated CI for KiCad exports.

When you're done
- After layout changes: regenerate gerbers and update the BOM CSV if component changes occurred. Commit the updated `.kicad_pcb` and the new gerbers or BOM CSV alongside a clear commit message indicating variant and purpose.

Questions for the user
- Which `.kicad_pcb` variant is the active design to edit (e.g., `LED Watch.kicad_pcb`, `LED Watch - RGB version.kicad_pcb`, or `LED Watch - empty RGB version.kicad_pcb`)?
- Do you want future changes to include a CLI-based export workflow or keep manual KiCad GUI workflows?

— End of instructions —
