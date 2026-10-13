# Polar (radial + arc) trace system: plan

## Why it is worth building even though freerouting finished the white board
- freerouting produced working but visually messy copper. A polar router would make the LED rings look designed: every column net a straight radial spoke, every row net a concentric arc, with via hops where they cross.
- DRC becomes predictable: lane widths and spacings come from a formula, not from whatever the autorouter decides.
- The RGB version (132 RGB LEDs, 4 pads each on a 0.5 mm pitch with 0.3 mm pads, 528 pads on three rings) is where a plain autorouter is most likely to struggle or take hours. A polar router attacks that case directly.
- The same code can regenerate the routing whenever the ring radii change (the board is already parametric).

## Coordinate system and what gets routed
- Polar frame about the board centre. Ring radii r_H, r_M, r_S and angles theta_k = k * 360 / N are already known to `plan_board.py`.
- Nets that are naturally polar: the 12 sector (COL) nets, each touching every LED of one 30 degree sector, and the row (ROW) nets, each touching one slot in every sector (hour, five minute, five second positions). Power/solar/battery nets stay with a normal router.
- Lanes: the 0.8 mm gap between rings holds about 3-4 arc lanes at 0.1 mm track + 0.1 mm space on one layer; with 4 layers (front, two inner, back) there is room for 12 row arcs and 12 column spokes with vias hopping layers at LED spaces.

## How it would work
1. Read the LED positions and nets from `plan.json` and the netlist.
2. Assign each net to a layer and a lane (a small constraint solver; start with a hand-written rule: columns on In1 as spokes, rows on In2 as arcs, front/back only for escape).
3. Emit `PCB_ARC` and `PCB_TRACK` items with `pcbnew` (KiCad 10 python), plus vias at the LED pads and at crossings.
4. Run KiCad DRC; report violations with the offending net and lane so the lane table can be adjusted.
5. Hand the leftover nets (power, solar, I2C, buttons) to freerouting with the polar tracks locked.

## Milestones
1. (small) Prototype on ONE sector of the single-colour board: one column spoke + five row arcs, check DRC at JLCPCB rules.
2. (medium) Full single-colour board: all 12 columns and 12 rows polar, rest freerouted.
3. (larger) RGB board: escape routing for 4-pad LEDs, then the same lane logic with 18 columns and 22 rows.

## Open questions
- Is a pure polar look more important than the shortest possible tracks? (Arc rows are longer than direct routes.)
- Do we want the rows on one inner layer and columns on another, or mixed per sector for current density?
- JLCPCB limits for arcs and acid traps need to be checked against their capability page before committing to 0.1 mm lanes.

Effort estimate (ESTIMATE): milestone 1 about a day of work, milestone 2 a few days with debugging, RGB another few days.
