# LED Watch (RGB) — open issues & quote notes
Written 2026-10-05 by Claude from the live project at `Desktop\LED-Watch`.
Nothing below has been changed in the design. Each item says how well it is verified.

Backup of everything before any Claude edit: `Desktop\LED Watch pre-Claude October 2026\`
Per-edit snapshots: `claude-snapshots\`

## Changes already made to the board (all DRC-checked: 0 violations, 0 unconnected)
1. `/Minute6` trace re-routed *below* MCU pads 28-32 (new via at 101.7, 106.0; blue-layer run to the existing via at 104.375, 104.56). Removed the front-layer segments that clipped pad 32.
2. Four GND vias through the MCU centre pad (pad 65) at (99.12,102.06) (101.4,102.06) (102.54,99.78) (101.4,99.21) to tie it to the coin-cell GND pad on the back. Evan may remove/reduce these ("no vias under the MCU") — undecided.
3. VCC link: vias at (100.13,90.47) and (101.63,91.77) + 2 mm blue-layer track, joining two separate VCC pour pieces (pad 21's side vs pad 52's side).
4. Board rule `min_hole_clearance` 0.25 -> 0.19 mm (JLCPCB hole-to-track minimum is 0.20 mm; board sat at 0.1997-0.2000).
5. Zones refilled (the old saved fills were stale; the 66 zone-clearance DRC errors were not real).

## Open issues (NOT changed — need Evan / his electrical engineer)

### A. 32.768 kHz crystal is on pins 31/32 (PD6/PD7)
- VERIFIED against Atmel doc 8285 (ATmega165A/PA datasheet; the exact datasheet linked in the schematic): pins **23 = XTAL2 (TOSC2)** and **24 = XTAL1 (TOSC1)** are the oscillator pins. Pins 31/32 are plain I/O PD6/PD7.
- In the schematic Y1 is on PD6/PD7 and XTAL1/XTAL2 are unconnected.
- The Y1 traces are LOCKED on purpose (engineer's instruction). Do not move them without Evan + engineer.
- Question for the engineer: "Why is Y1 on 31/32 rather than 23/24?"
- NOTE: an earlier Claude message said the oscillator pins were PG3/PG4. That was WRONG (that is the ATmega169). Correct pins are 23/24.

### B. AVCC (pin 64) unconnected
- VERIFIED, same datasheet, section 2.3.15: "AVCC is the supply voltage pin for Port F and the A/D Converter. It should be externally connected to VCC, even if the ADC is not used."
- Relevance: this design USES Port F (PF0-PF3 buttons, PF4/PF5 = Minute9/Minute10 LED rows). AREF (pin 62) and PF6/PF7 are unused.
- Fix would be one trace from pin 64 to VCC. Evan wants to read the datasheet first.

### C. BMI160 pins VDDIO (5) / GNDIO (6) / CSB (12) / SDO (1) floating — NOT YET VERIFIED
- Seen in the netlist. Not yet checked against the Bosch datasheet (link is in the schematic). Claude believes VDDIO must be powered and CSB tied high for I2C mode — verify before acting.

### D. No current-limiting resistors; no MCU decoupling capacitors — REASONING, NOT DATASHEET-VERIFIED
- BOM has no resistors; only two capacitors (crystal load caps). Digikey listing for the LED quotes Vf 1.9 V (red) / 2.5 V (green, blue).
- Driving 132 RGB LEDs as a multiplexed matrix straight from MCU pins from a 3-4.2 V supply with no series resistance would overcurrent the red channel and the MCU pins. Needs a real calculation against the LED datasheet and the ATmega165PA pin/port current limits.
- Decoupling: normally 100 nF per VCC pin + AVCC; none on the board.

### E. Parts with no part number in the schematic (blocks a firm assembly quote)
- Y1 crystal (value only "Crystal"), C1/C2 (value "C"), D1-D4 (0201 LEDs, colour unspecified). See `LED-Watch-BOM.csv` for the placeholders.

## Datasheets (the exact parts, per Evan: never sibling parts)
- MCU: ATmega165PA, Atmel doc 8285 — link stored in schematic field.
- IMU: Bosch BMI160 — link stored in schematic field.
- LED: Harvatek B39D3RGB-F6C0001HOU1930 (0.83 mm, common-cathode per Digikey) — no datasheet linked in the schematic. Still to download.
- Others (switch TS21-34-035-BK-260-SMT-TR, Keystone 3034, JST SM02B-SRSS-TB): no datasheet fields set.

## JLCPCB quote (PCB only), 5 boards, 2026-10-05
Gerbers: `LED-Watch-gerbers.zip` (regenerated from the fixed board; inner layers now correctly L2/L3).
JLCPCB parsed it as 4-layer, 42.87 x 50.28 mm.
| Item | USD |
|---|---|
| Base 4-layer x5 (special offer) | 8.00 |
| ENIG finish | 16.80 |
| 0.2 mm vias (forces FR4 Tg155) | 16.81 + 3.36 |
| 4-wire Kelvin test (forced by 0.2 mm vias) | 16.68 |
| **Boards total** | **~61.65** |
| DHL shipping estimate | 31.23 |

Assembly (not priced yet — needs a JLCPCB sign-in):
- "Economic" tier = top side only. Coin-cell holder J3 is on the BOTTOM, so use "Standard" (both sides) or hand-solder J3 (big part, easy by hand).
- "Standard" tier enlarges the board to 70.9 x 70.3 mm (edge rails) and allows 2-5 assembled boards.
- 132 Harvatek LEDs are unlikely to be in JLCPCB's parts library -> "By Customer (Self-Service)" (consign parts bought from Digikey) or ask for a Global Sourcing match.
- Files ready: `LED-Watch-BOM.csv`, `LED-Watch-CPL-jlcpcb.csv` (145 placements; J1 Tag-Connect excluded — footprint only).
- Placement rotations in the CPL are raw KiCad values; JLCPCB often needs per-footprint rotation corrections for QFN/LGA/LED parts — check their placement preview.

## JLCPCB assembly attempt, 2026-10-05 (signed in as Evan; draft project "LED-Watch-gerbers" saved in his JLCPCB account; nothing ordered, nothing in cart)
What JLCPCB's BOM matcher did with `LED-Watch-BOM.csv` + `LED-Watch-CPL-jlcpcb.csv` (145 placements, both parsed fine):
| Part | JLCPCB match | Status |
|---|---|---|
| 132x Harvatek B39D3RGB-F6C0001HOU1930 | LCSC C6509069 (exact MPN) | **0 stock** ("660 shortfall" for 5 boards) |
| MCU ATmega165PA | C2053871 (-MUR, tape & reel) | **Out of stock** (confirmed on LCSC) |
| BMI160 | C94021 | **Out of stock** (confirmed on LCSC) |
| JST SM02B-SRSS-TB | C18337480 | shortfall 9 |
| C1,C2 (0201 caps) | WRONG auto-match: 22 uF plug-in electrolytic | must be replaced (needs a real value, e.g. 0201 C0G) |
| D1-D4 (0201 LED) | WRONG auto-match: 2.2x1.2 mm red LED | needs the real part |
| SW1,SW2 / Y1 / J3 | no match | out of library; J3 (bottom side) left off -> "top side only" |
Out-of-stock parts cannot be ticked for placement, and JLCPCB then refuses to continue ("select at least one part"). The path forward there is JLCPCB's consignment (ship Digikey-bought parts to their warehouse in China and register them in "your own parts library") or "Pre-order" — both slow/expensive for a one-off, and every extended part also carries a per-part-type fee.
Conclusion: JLCPCB is fine for the BARE BOARD (~$61.65 + ~$31 shipping) but a poor fit for ASSEMBLING this design because its three critical parts are not stocked. Better: a US turnkey/consignment assembler that buys from Digikey (e.g. Bittele, Advanced Circuits, MacroFab, PCBWay turnkey) — send them: gerbers zip, BOM (fill in the TBD MPNs first), CPL.

## DigiKey list "Watch Project" (WPRJ7CQ35H) cross-check, 2026-10-05
Contents (7 lines): TS21-34-035-BK-260-SMT-TR switch (39,050 in stock); **BMI270** IMU (828-1091-2-ND); JST SM02B-SRSS-TB (66,088); Keystone 3034 (45,006); Micro Crystal RV-3028-C7 RTC IC (0 stock, not in schematic); **Abracon ABS07-32.768KHZ-T** crystal 12.5 pF (535-9542-2-ND, 526,454); JST BM06B-SRSS-TB 6-pin (older ISP idea, not in schematic).
- The list is OLDER than the schematic (it predates the Tag-Connect ISP and the BMI160 in the schematic).
- DISCREPANCY: list says BMI270, schematic says BMI160. Same package family (LGA-14 2.5x3) but different parts — Evan to decide which is intended. BMI160 datasheet check (issue C) is moot if it becomes BMI270.
- Likely Y1 = ABS07-32.768KHZ-T (3.2x1.5 mm, 12.5 pF load). Load-cap value for C1/C2 depends on the stray capacitance; typical ~18-22 pF for 12.5 pF — ENGINEER TO CONFIRM, not decided.
- Still no part number anywhere for D1-D4 and for the LED/MCU DigiKey P/Ns.

## DigiKey part hunt, 2026-10-05 (candidates only — BOM now lists schematic parts only, not the brainstorm list)
Rule from Evan: the DigiKey list is a brainstorm; only parts in the schematic go in the BOM. Candidates below were chosen to match the schematic footprints/functions.
- **LED B39D3RGB-F6C0001HOU1930 is OBSOLETE** at DigiKey ("no longer manufactured, stocked until depleted"); 20,772 in stock, 3147-...-CT-ND. Fine for prototypes, a risk for production/reorders. Part is common-cathode, 0.83x0.83x0.75 mm, Vf 1.9 V red / 2.5 V green / 2.5 V blue, MSL 2A.
- **BMI160 is OBSOLETE** at DigiKey. BMI270 (828-1091-2-ND) is reported as the same-size, same-pinout successor — which is presumably why it's in Evan's list. Needs a schematic decision (not made). Verify BMI270 pin functions against its own datasheet before swapping.
- **ATmega165PA-MU** only ~51 in stock at DigiKey when checked (1611-ATMEGA165PA-MU-ND): enough for prototypes, check again before ordering.
- D1-D4 are a 4-LED charlieplexed cluster on PF6/PF7/PD0/PG4 at the top of the board (~102.8-105.5, 91.3), driven straight from MCU pins with no resistors — another instance of the series-resistor question in item D.
- Candidate Y1/C1/C2/D1-4 parts are in LED-Watch-BOM.csv, flagged CANDIDATE.

## JLCPCB ASSEMBLY QUOTE (substitute-parts variant), 2026-10-05 — NOT ORDERED, not in cart
Config: 5 boards, Standard PCBA, top side, edge rails (70.87 x 70.28 mm), ENIG, 0.2 mm vias. BOM = `LED-Watch-BOM-JLC-variant.csv`, CPL = `LED-Watch-CPL-jlcpcb-topside.csv`. Screenshot: `jlcpcb-assembly-quote-2026-10-05.jpg`.
Parts placed in the quote (all in stock at JLCPCB): 132x Meihua MHPA0808RGBDT C404279 (664 incl. spares, $25.83 total), ATmega169PA-MU C1339313 (5), BMI270 C2836813 (5), Abracon ABS07-32.768KHZ-T C130253 (5).
| Line | USD |
|---|---|
| PCB (4-layer, 5 pcs, ENIG, 0.2 mm vias, etc.) | 62.66 |
| Standard PCBA: setup 25.75, stencil 8.27, components (4 items) 84.85, feeder loading 6.20, SMT 5.20, X-ray 8.25, packaging 0.50 | 139.02 |
| **Total, before shipping** | **201.68** (2-3 day assembly instead of 3-4: +49.63) |
NOT in this price (left unticked): D1-D4 (matcher chose a wrong 3.4 mm RGB LED), C1/C2 18 pF 0201 (out of stock, 15 short), J2 JST (9 short), SW1/SW2 tact switches (no JLC match), J3 coin-cell holder (bottom side, hand-solder). Adding the placeable ones will add components + feeder fees; expect a rough total ~$215-235 + ~$31 shipping.
Open design consequences of this variant: Meihua LED is common-ANODE (matrix drive polarity must be reversed in firmware/possibly circuit), ATmega169PA needs a recompile + different programmer signature, BMI270 needs an 8 KB init blob at power-up (half the 16 KB flash), and no schematic changes made yet.

## Can JLCPCB place parts at 5-degree angles? (tested 2026-10-05)
- No JLCPCB documentation found either way (searched). General industry knowledge: pick-and-place machines can place at any angle if the placement file gives it.
- Empirical test: uploaded `TEST-CPL-radial-5deg.csv` (132 LEDs at radial angles rounded to 5-degree steps, 60 distinct angles) to the live JLCPCB project. RESULT: file accepted with no error; JLCPCB's PCBA viewer rendered the LEDs tilted at those angles. This proves their *software pipeline* accepts and shows non-90-degree rotations.
- NOT proven: that their machines place them accurately, or that their post-order DFM review won't flag them. JLCPCB's own note: the viewer is "for reference only"; final placement is checked in DFM within hours after the order is placed.
- The JLCPCB draft project "LED-Watch-gerbers" now has the TEST CPL attached (not the real one). Re-upload `LED-Watch-CPL-jlcpcb-topside.csv` before ever ordering from that draft.
- To be sure: ask JLCPCB support (live chat/email) and add the question to US assembler RFQs (done in rfq-emails.md).
- Also remember JLCPCB rotation CONVENTIONS differ from KiCad per footprint; for custom LED footprints we must define the 0-degree orientation and verify in their viewer.

### JLCPCB live-chat answer on 5-degree placement (asked 2026-10-05 by Claude at Evan's request, via the chat widget on the PCBA page)
Question sent: can Standard PCBA place components at arbitrary rotation angles in 5-degree steps from the CPL, any extra cost/manual handling/restriction? (Mentioned the viewer test.)
Reply (agent "Finn"), paraphrased: this is an **extra service**; put a **remark on the order** and a colleague will check, and tell you whether it's available and whether there's an extra fee.
=> Not a flat yes or no. Possible case-by-case, may carry an extra fee, confirmed by a person AFTER you place the order with the remark. Not yet a firm guarantee. Ask the US assemblers too (question already added to rfq-emails.md).
