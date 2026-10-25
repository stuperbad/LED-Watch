# Mechanical test prints (strap fit + bumper), first version

Everything to hand to the 3D printer is in **`print/`**. Nothing here has been printed yet: the geometry was checked by script (no overlaps in the assembled position, every file watertight) and by cross-sections, not on a printer.

| File | What it is | How to print |
|---|---|---|
| `print/01_pcb_blank.stl` | The bare board: exact outline and strap slots taken from the KiCad board (42.0 x 51.18 mm, 1.6 mm thick). A blank for checking the strap, the slots and the overall size. | Flat, any orientation. No supports. |
| `print/02_pcb_dummy_with_parts.stl` | The same board with stand-ins for the large parts. **Back:** two batteries (16.5 x 16.0 x 5.25 mm, nominal 15 x 15 x 5 plus half the datasheet tolerance, same as the board's keep-out), two battery connectors (2.96 mm tall), the buzzer (9 x 9 x 1.9). **Front:** solar cell (23 x 8 x 1.35), the MCU (6 x 6 x 0.9) and the two buttons (4.6 x 2.8 x 1.9). Smaller parts are left out. | Already exported **front side down**, so the batteries point up. Slicer supports "build plate only", about 2 mm tall under the plate. |
| `print/03_bumper.stl` | The skin-side bumper (see below). | As exported: floor on the bed, hooks pointing up. No supports needed (the hook lips overhang 0.95 mm and the pull tabs about 1.3 mm). |
| `print/variants/03_bumper_tighter_minus0.4.stl`, `..._looser_plus0.4.stl` | Same bumper with the strap gap 0.4 mm smaller or larger, for finding the right squeeze. | Same. |

Pictures: `previews/overview.png` (all three, plus assembled), `previews/sections.png` (cross-sections through the strap and through the hooks).

## How the strap and the bumper work
The strap goes from the front, **through the top slot, across the back of the board over the two batteries, and out through the bottom slot**. The bumper sits behind the strap, against the skin:

```
  skin   |  bumper floor 1.4 mm
         |  strap 1.75 mm, squeezed by 0.30 mm to 1.45   <- holds the batteries down
         |  battery 5.25 mm (against the board back)
         |  board 1.6 mm      <- hook lips (4) reach over the front face of the strap lugs
```
- The bumper is a shallow tray: a 1.4 mm floor, a 1.4 mm rim, the floor top 6.70 mm below the board's back face (5.25 battery + 1.75 strap - 0.30 squeeze).
- **Four snap hooks** rise outside the straight sides of the two strap lugs and clip 0.65 mm over the lugs' front face. The lugs carry no parts, and the ring of LEDs around the face leaves no room for a lip anywhere else. Each hook ends in a small tab: pull it outward with a fingernail to release that corner.
- The rim and floor are **open at the strap exits** (top and bottom, |x| < 10.6 mm) so the strap can turn up into the slots. The battery corners reach the rim there, so the rim is cut further back than the floor.
- Everything on the back sits inside the cavity: batteries, battery connectors, buzzer. The plug and wires of each battery (a 26 mm lead with a plug) are not modelled; they run from each connector inward toward the battery, under the board, inside the cavity.
- To work on the back of the watch, unhook the four tabs and lift the bumper off.

## Settings I would use
- **Material: PETG** (or nylon, ASA, or a stiff TPU). The hooks flex about 0.7 mm; my estimate is a bending strain of about 2 %, which PETG takes easily and PLA may not. The arms are printed standing up, so the bending pulls across layer lines: print the bumper with **4 perimeters, 100 % infill, 0.2 mm layers, slow and warm** for good layer bonding. If you break a hook, say so and I will thicken or lengthen it.
- 01 and 02: any material; PLA is fine.
- Nozzle 0.4 mm. Add nothing for clearances: all clearances (0.30 mm between lug edge and hook arm, 0.05 mm between the lip and the board face) are already in the model. A printer that over-extrudes may need a first print scaled to 99 to 99.5 %.

## What to look for in the first test
1. Print **01** first: does your strap pass through the 19.76 x 2.5 mm slots, and does it sit comfortably across the back?
2. Print **02**, thread the strap through, lay the strap over the battery stand-ins. Measure the squeeze: strap thickness + battery height should be a little more than the bumper's floor gap.
3. Print **03** (and, if the strap is thicker or thinner than 1.75 mm, the matching variant). Check: does it snap on, does it come off without cracking a hook, does the strap slide freely under the rim notches, does it feel comfortable on the skin?
4. Tell me what to change: strap thickness, squeeze, hook strength, or the shape of the edges.

## What I assumed (please correct)
- **Strap thickness 1.75 mm** (you said 1.5 to 2 mm), compressing 0.30 mm. Both are single numbers at the top of `make_models.py`.
- **Battery height 5.25 mm** (datasheet: 5.0 +- 0.5 mm; the pouch swells when stored warm). The board's own keep-out uses the same 16.5 x 16.0 x 5.25.
- The strap lies across the full back from slot to slot, as described above. If you want the strap to go another way (for example over the front, or on a different side of the batteries), the bumper changes.
- The inductors, the harvester chip and the small parts on the back (max 2.5 mm tall) are left out: the batteries are taller.
- The buttons are modelled 1.9 mm tall (KiCad's model of the KMR2).

## Rebuilding
`outline.json` holds the board outline and the two slots, dumped from `hardware/LED Watch - Single Color.kicad_pcb` (Edge.Cuts polygons, KiCad coordinates relative to the board centre). Edit the numbers at the top of `make_models.py`, then:

```
python make_models.py     # writes print/*.stl, runs the bumper-versus-board overlap check (expect 0.0)
python preview.py         # writes previews/*.png
```
Needs CadQuery, trimesh, numpy and matplotlib.
