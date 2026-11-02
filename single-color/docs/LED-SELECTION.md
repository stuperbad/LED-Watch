# LED brightness and colour temperature: what we have, what JLCPCB offers, what to do (2026-11-02)

Question (owner): are the three LED rings (hour 0603, minute 0402, second 0201) in a good state for brightness and colour temperature, is there a continuity from ring to ring (hours brightest, seconds dimmest, a colour gradient), and what does JLCPCB offer for white LEDs in those three sizes?
**Short answer:** the parts we have already run in the "right" direction (hours a little brighter and bluer, seconds a little dimmer and whiter), but only by accident; the average brightness of the three rings is within 1.5 x of each other, the part-to-part (bin) scatter is 5 x or more, and the hour LEDs are *very* blue. A hardware swap can change the colour of a ring but not its brightness (all 11 LEDs of a column share one 220 ohm resistor). The brightness hierarchy is a firmware job (per-ring gain) plus one calibration on the first real board.

**Decision (owner, 2026-11-02): keep the three parts as they are** (option A). The colour order violet-blue (hours) to blue-white (minutes) to cool white (seconds) is what was wanted; option B (part swap) is parked: if the hour LEDs turn out too violet on the first board it is a BOM-only change for the next order. The per-ring brightness gain in the firmware stays on the to-do list.

## 1. The parts on the board now (data sheets read, not only the JLCPCB listing)
| Ring | Part (LCSC) | Light output | Forward voltage | Colour | Max current | Stock 2026-11-02 |
|---|---|---|---|---|---|---|
| hour, 12 x 0603 | Hubei KENTO KT-0603W (C2290, Basic) | bins P22-P26: **145-360 mcd at 5 mA** (typ about 250), +-10 % | 2.6-3.1 V at 5 mA (bins VM-VQ) | bins DT1-DT7: x 0.21-0.25, y 0.16-0.23 = **40,000 K to over 100,000 K**, a deep blue-white (JLCPCB shows no CCT) | not read (0603 class, 100 mW) | 1.22 M |
| minute, 60 x 0402 (+7 mode LEDs) | Xinglight XL-1005UWC (C20613596, Extended) | bins E1-E9: **350-1000 mcd at 20 mA**, +-10 % | 2.6-3.3 V at 20 mA (bins M18-8 to M19-5) | **15,000 K** typ, x 0.2454 y 0.2481: blue-white | 20 mA, 75 mW | 114 k |
| second, 60 x 0201 | Xinglight XL-0201UWC (C965789, Extended) | bins E5-E8: **550-900 mcd at 20 mA** (typ 700) | 2.6-3.4 V at 20 mA | **5500-7500 K** (bins UW7-10 / UW9-10 / UW11-10 = 5500-6000 / 6000-6500 / 6500-7000), CRI 70 | 20 mA, 70 mW | 5.9 k |

JLCPCB's listing text is wrong or unclear for two of them: C20613596 is shown as "1 cd at 5 mA" (the data sheet says 350-1000 mcd at **20** mA) and C965789 as "185 mcd" (data sheet: 550-900 mcd at 20 mA). Another LCSC number for the same 0402 family, C965796, is listed as 135 mcd at 20 mA (a different bin or an error; not used). The LCSC file of C965789 is named for a Lite-On part but contains the Xinglight XL-0201UWC data sheet.

## 2. What the board really runs (model, `docs/research/led_balance.py`)
The LEDs run at **1.7-4.2 mA** (220 ohm, 3.3-4.12 V battery), far below the 20 mA of the light-output bins, so the numbers are scaled down linearly (estimate; real LEDs are a little better than linear at low current, so these are slightly pessimistic). Typical parts, typical pin drops:

| Battery | hour 0603 | minute 0402 | second 0201 |
|---|---|---|---|
| 3.3 V | 1.8 mA, **88 mcd** | 1.9 mA, **61 mcd** | 1.7 mA, **61 mcd** |
| 3.7 V | 2.9 mA, **144 mcd** | 3.0 mA, **97 mcd** | 2.8 mA, **100 mcd** |
| 4.12 V | 4.1 mA, **205 mcd** | 4.2 mA, **137 mcd** | 4.1 mA, **142 mcd** |

* **Ring to ring:** hours are about 1.45 x brighter than minutes and seconds (which are equal), at every battery voltage. That is a mild hours-brightest order, not a designed 3 : 2 : 1 gradient.
* **Battery voltage:** every ring gets 2.3 x brighter between 3.3 V and 4.12 V. The firmware already plans to measure VDD and scale (`firmware/HANDOFF.md`).
* **Bin scatter (the big one):** with the worst and best bin and forward-voltage combinations one ring spans 5-8 x (hour 63-259 mcd, minute 35-200, second 48-180 at 3.7 V). Parts of one reel are normally one or two bins, so within a board the ratio between rings is stable, but **reel to reel it can move by 2-3 x**: the ratio on the first real board cannot be known from data sheets.
* **Colour:** hours 40,000 K+ (violet-blue), minutes 15,000 K (blue-white), seconds 6,000 K (cool white). In mired (1,000,000 / K) that is 25 / 67 / 167: a monotonic cool-to-neutral gradient, but it starts very blue; the hour LEDs will look visibly bluer than the rest.

## 3. What JLCPCB has (sampled 2026-11-02 from the parts library and part pages; the library has about 90,000 LED hits, its search has no colour-temperature filter, so this is a sample, not an exhaustive list; all Extended unless noted)
White only; brightness and colour from the listing unless a data sheet was read.
| Size | Part (LCSC) | Light | Vf | CCT | Stock | Price | Note |
|---|---|---|---|---|---|---|---|
| 0603 | KT-0603W (C2290) **Basic** | 145-360 mcd @5 mA | 2.6-3.1 | 40,000 K+ | 1.22 M | $0.012 | in use; data sheet read |
| 0603 | F.0603.00050 / P2-0603W9YS2-06T-002 (C7496824) | 550 mcd @5 mA | 2.9 | **3600 K** | 19 k | $0.010 | the only warm-ish 0603 white found; the listing calls the colour "yellow green" (contradiction): data sheet not read |
| 0402 | XL-1005UWC (C20613596) | 350-1000 mcd @20 mA | 2.6-3.3 | 15,000 K | 114 k | $0.011 | in use; data sheet read |
| 0402 | EKINGLUX E6X0402CWAY1UDA, 4500-5500 K bin (C6916228) | 300 mcd @5 mA | 2.7 | **4500-5500 K** | 2.1 k | $0.026 | neutral white; same part has an 8000-15000 K bin as C6916229 (236 in stock) |
| 0402 | NationStar NCD0402W1 (C130725) | 180 mcd @20 mA | 2.6-3.6 | not listed | 6.6 k | $0.043 | |
| 0402 | Bivar SM0402UWC (C6816681) | 600 mcd @20 mA | 3.1 | not listed | 0 | $0.83 | out of stock |
| 0201 | XL-0201UWC (C965789) | 550-900 mcd @20 mA | 2.6-3.4 | 5500-7500 K | 5.9 k | $0.066 | in use; data sheet read |
| 0201 | CHONGTIAN CT-0201UHWC-P4 (C52675959) | 250 mcd | 2.6-3.2 | "cold white" | 9.3 k | $0.027 | cheaper, about a third of the brightness |
| 0201 | TOGIALED TJ-S0704EX4T5ALCCW-A5 (C48689447) | 250-500 mcd @20 mA | 2.8-3.6 | 6000-17000 K | 2.0 k | $0.084 | bluer than the XL |
| 0201 | Everlight CSP0603AN101-WP30300563001-3T (C6768746) | 80 mcd @**1 mA** | 2.6 | not listed | 8.4 k | $0.071 | very efficient at low current: about 240 mcd at 3 mA, more than the XL-0201UWC |
| 0201 | Inolux IN-S21AT5UW (C5156918) | 130 mcd @5 mA | 2.6-3.2 | not listed | 0 | $0.18 | pre-order only |

**No warm white (2700-3500 K) in 0201 or 0402 was found at JLCPCB**; the warmest white in these sizes is the 0402 4500-5500 K bin, and in 0603 the 3600 K part above. (A German forum thread says the same about warm whites at LCSC.)

## 4. Options
* **A. Keep the parts, tune in firmware (recommended now).** Zero hardware risk, stock is plentiful (the 0201 at 5,900 pieces is about 100 boards, the 0402 at 114 k about 1,700). Add a per-ring gain in the firmware (the frame buffer already has a brightness 0-255 per LED, `watch_fb()`; only a gain table by ring is missing, in `watch.c` and the simulator): for example hours 100 %, minutes 70 %, seconds 45 % of the chosen level, and calibrate once on the first board (phone camera or lux meter), because of the reel-to-reel scatter. This gives the hours-brightest, seconds-dimmest order the owner wants. It does not change colour: hours stay violet-blue.
* **B. A warm-to-cool gradient by part swap (needs samples first).** Hour 0603 C7496824 (3600 K), minute 0402 C6916228 (4500-5500 K), second 0201 XL-0201UWC (5500-7500 K): 278 / 200 / 167 mired, a smooth warm hours to cool seconds gradient, and without the violet hour LEDs. Costs: two more Extended lines (a loading fee of roughly $2-3 each: the JLCPCB quote shows $49.60 feeder loading for the 22 Extended lines), the 0402 stock is 2,100 (about 30 boards of 67 pieces), and two of the three listings are not backed by a data sheet I could read. Brightness at 3 mA would be about 330 mcd (0603), 180 mcd (0402) and 105 mcd (0201), i.e. a built-in 3 : 1.7 : 1 hierarchy.
* **C. The reverse (hours coolest and brightest, seconds warmest and dimmest)** is what the current parts roughly do, but the warm end does not exist at JLCPCB in 0201 / 0402.
* Only the BOM line changes in all options (the pads are the same); the CPL does not; polarity of the new parts must be checked in JLCPCB's placement preview again.

## 5. Before choosing: a 30-minute test (cheap)
Buy 10 pieces each of C7496824, C6916228, C965789, C20613596 and C2290 (LCSC), solder or clip them on a scrap board in a row with the same 220 ohm and a 3.3 V supply: look at colour side by side, measure with a phone light meter at 3 mA, check the polarity mark. That settles A against B with real parts, and is the calibration data the firmware gain needs.

Sources: Hubei KENTO "Specification for approval CICADT(0603-0.6DT white)", 2018-12-06, p. 4 (bins); Xinglight XL-1005UWC and XL-0201UWC technical data sheets (LCSC copies), pp. 3-4; JLCPCB part pages and parts-library search of 2026-11-02 (stock, price, listing attributes); `docs/research/led_resistor.py` (circuit model).
