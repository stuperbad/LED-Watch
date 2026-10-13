# BOM vs JLCPCB: what they place, what we are unsure about (checked 2026-10-12)

Stock numbers are live reads of JLCPCB's parts-search endpoint on this date and change hourly; re-check on order day. Library: Basic = no loading fee, Extended = per-part loading fee (see ASSEMBLY-AND-COST.md).
BOM source: `schematic/n_solar.xml` (190 parts, 31 unique lines).

## Parts JLCPCB can place (everything SMT: 186 of 190)
| Part | LCSC | JLCPCB stock | Library | Confidence |
|---|---|---|---|---|
| AVR128DB48-I/6LX (U1, VQFN-48 6x6, 0.4 mm pitch) | C1019768 | **33** (60 on 2026-10-05, falling) | Extended | **LOW: stock** |
| BQ25570RGRR (U4, VQFN-20) | C506250 | 376 | Extended | medium: stock fine, layout and cold start need bench proof |
| LIS2DW12TR (U2, LGA-12) | C189624 | 16,840 (ST original; clones also listed, avoid) | Extended | high |
| 32.768 kHz 3215 crystal, 12.5 pF (Y1) | C97606 | 132,435 | Extended | high (check load caps on the bench) |
| 22 uH / 10 uH 1210 inductors (L1, L2) | e.g. C90320 / C74563 | thousands | Extended | medium: pick parts with enough saturation current for the BQ25570 (many 1210s are only 110-300 mA) |
| JST SH 2-pin SM02B-SRSS-TB (J1, J1B) | C160402 | 80,552 | Extended | high |
| KMR2 tactile switch (SW1, SW2) | C72443 (KMR221GLFS, 2 N) | 5,688 | Extended | high |
| White LED 0603 (12 hour LEDs) | C2290 KT-0603W | 1.9 M | Basic | high |
| White LED 0201 (60 outer LEDs) | C965789 XL-0201UWC (0.7x0.4 mm, 5500-6000 K) | 7,966 | Extended | medium: enough for about 25 boards; colour and brightness to confirm |
| White LED 0402 (60 minute LEDs + 6 indicators) | not found by my quick search | - | - | **UNVERIFIED: find a part** |
| 220 ohm, 10k 0402 resistors | C25091, C25744 | >1 M | Basic | high |
| 100n 0402, 4u7, 10u, 22u 0805 caps | e.g. C60474, C23733, C45783 | millions | mixed | high |
| 18 pF C0G 0402 (crystal caps) | C106202 | 1.97 M | Extended | high |
| **BQ25570 resistors (re-picked 2026-10-12): 6.49 M (x3), 5.11 M, 1.47 M, 3.74 M (x2), all 1 % 0402 with thousands in stock** | 7.32M C423137; 8.25M C423131; 4.22M C477721 | **7.32 M: 4 total; 8.25 M: 24; 4.22 M: 5**; others in the thousands | Extended | **LOW: cannot build 5 boards as written** |

## Not placed by JLCPCB (we buy and fit them)
- 2 LiPo cells (TinyCircuits 70 mAh with JST-SH plugs), 1 Anysolar KXOB25-05X3TF solar cell (hand-solder, low-temperature solder; listed stock is thin), wires, foam, Kapton.
- The UPDI Tag-Connect is only pads (no part to place).

## What I am not confident about (ranked)
1. **The MCU's JLCPCB stock (33).** Five boards need 5 chips and JLCPCB also needs spares for placement losses. It is the only chip that could stop the order. Options: order the chip from DigiKey/LCSC and have JLCPCB assemble it as a customer-supplied ("consigned") part (fee not checked), or keep an alternative footprint-compatible part in mind. Re-check the day before ordering.
2. **The BQ25570 resistor ladder.** 7.32 M, 4.22 M and 8.25 M have almost no stock. Re-pick the divider values from what is in stock (the ratios matter, not the exact values) or the order fails at the parts check.
3. **0402 white LED (60 + 6 parts).** I could not find a stocked part with my quick search; this must be settled before the BOM is final.
4. **LED rotation.** The 132 ring LEDs sit at arbitrary angles (6 degree steps); JLCPCB may refuse or charge extra (PRE-ORDER-CHECKLIST E3).
5. **BQ25570 behaviour** (cold start from the solar cell, crystal load caps, 0.4 mm QFN layout) cannot be settled from stock data; it needs the bench steps in PRE-ORDER-CHECKLIST C and G.
