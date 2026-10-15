# LED Watch - RGB

The RGB version of the watch (132 RGB LEDs, ATmega-class MCU, never built). Open **`LED Watch - RGB.kicad_pro`**.

| File / folder | What it is |
|---|---|
| `LED Watch - RGB.kicad_pro` / `.kicad_sch` / `.kicad_pcb` / `.net` | the current RGB project: schematic and board as of December 2025 (this was called just `LED Watch` before) |
| `mechanical/` | watch outline drawings (SVG) and the 3D print (`LED Watch - RGB.stl`) |
| `production/gerbers 2025-12-08/` | Gerbers of that board (used for an instant quote) |
| `scripts/` | KiCad scripting-console script that places the LEDs on the three rings |
| `archive/pre-claude/` | everything older, named by date: the first RGB schematic (2025-10-28), the empty/unrouted version and its Freerouting export (2025-11), the 4-layer routing attempts of 2025-11-19 ... 2025-11-25 (`...50PERCENT`, `...95PERCENT` = how far the routing got), KiCad backups, autosaves, a link to a Discord-hosted board file |

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