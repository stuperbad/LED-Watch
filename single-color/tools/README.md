# tools/ - the layout pipeline and board checks

These scripts made and checked the revision A board. Most take the board file(s) as arguments; the ones that use KiCad's `pcbnew` module must be run with
`"C:\Program Files\KiCad\10.0\bin\python.exe"`, the router/geometry ones (`grid_route2.py`, `add_stubs.py`, ...) with a normal Python that has `shapely`, `numpy`, `Pillow`.

| Stage | Scripts |
|---|---|
| placement tidy-up | `mark_groups.py`, `mock_move.py`, `tidy_symmetry.py`, `mcu_area.py`, `bq_area.py`, `add_dummies.py`, `copy_positions.py`, `restore_cells.py`, `shrink_od.py`, `nudge_buttons.py`, `fix_flank.py`, `fix_back_ring.py`, `swap_j2_pogo.py`, `new_bz1.py`, `bz_nets.py` (helpers in `plc.py`) |
| routing | `polar_route.py` (LED rings: arcs + radial lanes), `grid_dump.py` -> `add_stubs.py` -> `grid_route2.py` (rip-up router) -> `merge_new.py`, `undangle.py`, `crystal_left.py` |
| re-routing a few nets (2026-10-15) | `reroute_prep.py` (delete the pieces that cross a chip's core, prune the tails), `arcs_to_segments.py`, then `grid_dump.py` -> `grid_route2.py --exclude` -> `merge_new.py`, then `fix_gnd_zone.py` and `prune_dangling_loop.py` / `prune_stub_vias.py` for stubs |
| finishing | `fix_gnd_zone.py` (ground plane to the board outline), `add_silk.py`, `silk_nodash.py`, `silk_thicken.py`, `silk_twoline.py`, `check_pad_entry.py --fix`, `dfm_gaps.py`, `drc_sum.py` |
| production | `make_bom_cpl.py` (position export -> JLCPCB BOM and CPL, with the rotation fixes) |
| older pipeline | `route_*.py`, `export_dsn.py`, `import_ses.py`, `prep_dsn.py`, `ses_keep_nonpolar.py` (the Freerouting round trip used for the 43.5 mm board) |

The story of the order the stages were run in, with the reasons, is in `../docs/DECISION-LOG.md`.
| centre landing | `snap_centers.py` (move track ends on vias/pads to their centres) |
| wobble | `simplify_chains.py`, `simplify_loop.py` (straighten the 0.05 mm staircase on routed diagonals, DRC-guarded) |
| octilinear | `octo_opt.py`, `octo_loop.py` (re-draw every routed chain as the shortest 0/45/90 route that fits, DRC-guarded; `simplify_*` is the older, angle-blind version) |
