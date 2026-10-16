# LED Watch - RGB

The RGB watch: 132 RGB LEDs on three rings plus 7 RGB mode lights, JLCPCB-assemblable parts, AVR128DB64, solar harvester, two LiPo cells, buzzer, accelerometer and buttons. **Status (2026-10-15): placement sketch only**, no schematic, nothing routed. Open **`LED Watch - RGB.kicad_pro`** (it opens the board; the ring LED pads carry the row and colour nets, nothing else has nets yet).

Read **`docs/DESIGN-SKETCH.md`** first: board size, what goes where, the LED choice and its brightness warning, how the matrix is driven, risks and next steps.

| File / folder | What it is |
|---|---|
| `LED Watch - RGB.kicad_pro` / `.kicad_pcb` | the sketch: 44 mm round board with strap lugs, 132 + 7 LEDs, everything placed on the front and back |
| `docs/` | `DESIGN-SKETCH.md`, `pin-plan.csv` (AVR128DB64 pins), `BOM-candidates.csv` (new parts with LCSC numbers and stock, 2026-10-15) |
| `footprints/LEDWatchRGB.pretty` | the new common-anode LED footprint (fits Nationstar NCD0808RGB1 and Meihua MHPA0808RGBDT) |
| `data/` | `led_matrix.csv` (which LED is which second/minute/hour, row and column), `old_ring.json` (ring data read from the old board) |
| `tools/` | `build_sketch.py` makes the board (KiCad's Python: `"C:\Program Files\KiCad.0in\python.exe" toolsuild_sketch.py`), `extract_old_ring.py`, `check_pad_corners.py` |
| `renders/` | `top.png` (front) and `bottom.png` (back, seen from behind) |
| `mechanical/` | watch outline drawings (SVG), the 3D print and the Rhino layout, all of the **old 43 mm board**; not yet updated |
| `archive/` | **`2026-10-14 old RGB board - routed, Harvatek LEDs, ATmega165PA/`**: the previous RGB project (schematic, fully routed board, project, its Gerbers and the October 2026 fab quote work incl. `OPEN-ISSUES.md` and `jlc-alternatives.md`, and the ring placement script); everything older is in `pre-claude/` |

Below: Evan's original notes (part links and ideas).

---

# LED-Watch
first schematic progress commit. adding RGB sketch schematic as well as
completed single LED ring sketch. need to add buttons and sort out AND
gates in the RGB sketch.
Product Ideas.. data sheets and store locations:

Digikey working parts list: https://www.digikey.com/en/mylists/list/WPRJ7CQ35H

Boards options 

27 i/o pins and in the current sketch: https://www.digikey.com/en/products/detail/microchip-technology/ATMEGA4808-MUR/10444956

32 i/o pins: https://www.digikey.com/en/products/detail/microchip-technology/ATMEGA1284P-MU/1914520



LEDs options

addressable 1mm RGB: 
https://www.sparkfun.com/smd-led-addressable-rgb-apa-104-1010-pack-of-20.html
datasheet: https://cdn.sparkfun.com/assets/3/c/c/0/9/SparkFun_APA-104-1010__5mA__LED_Datasheet.pdf

nonaddressable 1mm RGB: 
https://www.digikey.com/en/products/detail/harvatek-corporation/B36J3RGB-F6C0001H4U1930/13588748


discrete white 0603:
https://www.digikey.com/en/products/detail/everlight-electronics-co-ltd/CSP0603AN101-WP30300563001-3T/15286660?s=N4IgjCBcoMwOxVAYygMwIYBsDOBTANCAPZQDaIALAExgAMAHLSALqEAOALlCAMocBOASwB2AcxABfQhQBsiECkgYcBYmRAy4tWgFYYLdl0i8BI8RKkgq6gASZcAExYSgA




Button Options

19 cent 3.4mm square: https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/TS21-34-035-BK-260-SMT-TR/21186457

8 cent 5.2mm square: https://www.digikey.com/en/products/detail/c-k/G01008829/16500348

Battery Parts:

Lipo Connector 
Thru-hole - 2mm.. they make 1mm mb? 
https://www.digikey.com/en/products/detail/jst-sales-america-inc/B2B-PH-K-S/926611

Coin Cell Harness
20mm dia. 3.
Do i need a negative connector? is SMD okay?
https://www.digikey.com/en/products/detail/keystone-electronics/3034TR/4499408