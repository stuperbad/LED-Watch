# Design review of revision C, for the design review (2026-11-03)

What this is: a read-through of the whole revision C design (schematic, board, firmware hooks, parts), done after the layout was finished, so the reviewer has the answers to hand. The October review of revision A (`PRE-ORDER-REVIEW-2026-10-18.md`: BQ25570 pin by pin, overvoltage table, resistor ladders) still stands and is not repeated; this one covers what changed since (USB-C, BQ21040, D51, the corner layout) and the points the reviewer raised on 2026-10-28 / 29.

How each finding was checked: **datasheet** = read in the manufacturer's data sheet today; **netlist / board** = measured by a script on the current files; **calculated** = my arithmetic, assumptions stated; **needs hardware** = cannot be settled on a PC. Nothing below has been tested on a real board.

## 1. Summary

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | VBUS had no static protection | was high | **fixed** (D51, 5 V TVS next to D50; ERC / DRC clean) |
| 2 | SBU clamp (BAT54WS to +3V3) cannot sink current into the buck rail if a damaged cable puts 5 V on SBU | low | recommendation, not changed (move the clamp cathode to VBAT); ask the reviewer |
| 3 | CC1 / CC2: no extra protection needed | none | explained (section 3) |
| 4 | SBU against an 8 kV discharge: 1 k + BAT54WS probably enough, not proven; a TVS on SBU is the safe answer but there is no room next to the connector | medium-low | **owner decision 2026-11-04: no TVS on SBU for the prototype** (no room next to the connector; 1 k + the clamp stay); revisit before boards go to other people |
| 5 | Buttons: low risk (plastic actuators); two TVS would fit on the front | low | **owner decision 2026-11-04: no button TVS for the prototype** |
| 6 | Battery plugs: no reverse-polarity protection, wire polarity of the cells unknown until measured | high if ignored | needs hardware (first step of the bring-up) |
| 7 | Two chargers on one battery (BQ25570 solar, BQ21040 USB) | none found | explained (section 2) |
| 8 | BQ25570: the input cap CIN (C50) is 7.7 mm from VIN_DC (14 mm of copper; was 11.2 / 19 until the lane move of 2026-11-03 night), CBYP (C53) 8.4 mm from VSTOR, the inductors 5.6 mm (L1) and 9.7 mm (L2) from the IC, the boost switching node 11.6 mm of copper over 3 layers with 3 vias (section 6b) | medium | known deviation from the data sheet's layout advice; ask the reviewer; measure efficiency at bring-up |
| 9 | MCU supply pins have their bypass caps at 1.4 / 2.2 / 4.8 mm (reviewer's rule: about 1 mm) | low-medium | known deviation, reasons in section 5 |
| 10 | Acute bends / micro pieces | low | 39 -> 28 spots; the rest listed |
| 11 | Charging cold: no battery thermistor, BQ21040 charges at any temperature | low | documented limitation |
| 13 | Data sheet 10.1: 'no ground planes near the voltage-setting resistors and the VREF_SAMP capacitor' (our In2 plane runs under R50-R56 and C51) | low | **recommendation: no cut-out.** The warning is about surface leakage from flux residue; an inner plane under about 0.2 mm of laminate is not exposed to it, the stray capacitance of those nodes is about 0.3 pF (3 Mohm x 0.3 pF = 1 us), and a cut-out would take the return plane away from about 40 mm of F.Cu / In1 copper (SCL, IMU_INT, BTN2, COL1, SDA, VBAT, VRDIV, VREF_SAMP, OK_HYST, VOUT_SET) that crosses that area. Picture `in2-under-dividers.png`; confirm with the reviewer |
| 12 | JLCPCB: new gerbers, BOM and CPL ready; stock check of C19185929 and a new quote still to do | - | open (checklist H9) |

## 2. Power

**Net names:** `BATT` = the battery pin of the BQ25570 (U4.18) + battery plugs J1 / J1B + BQ21040 OUT (U5.2) + C56; `VBAT` = the BQ25570's storage node VSTOR (U4.19) = the system rail (MCU, LEDs, C52, C53, C10-C13); `+3V3` = the buck output (IMU, I2C pull-ups). So both chargers charge the **cell**, the system runs from VSTOR through the BQ25570's own battery switch. (netlist)

**Two chargers on one battery (reviewer's question 1):**
- BQ25570 boost charger stops at VBAT_OV = **4.12 V** (recomputed in the October review: 1.5 x 1.21 x (1 + 6.49 M / 5.11 M)).
- BQ21040 terminates at **4.2 V** (datasheet). So with USB plugged in, the cell is brought to 4.2 V, 80 mV above the BQ25570's overvoltage point: the BQ25570 then simply does not charge (its overvoltage state only stops its own charging; absolute maximum on VSTOR / VBAT is 5.5 V). 4.2 V is the cell's rated charge voltage, its protection board cuts at 4.28 V. (datasheet, netlist)
- BQ21040 output cap C56 1 uF is inside the datasheet's 1-10 uF; input cap C55 1 uF inside 1-10 uF. (datasheet)
- **U5 pin map checked against the data sheet today:** TS 1, OUT 2, /CHG 3 (open), ISET 4, GND 5, IN 6; matches the schematic. TS through 10 k to ground = "no thermistor", exactly the data sheet's wording. (datasheet, netlist)
- **Charge current:** ISET = 10 k gives 540 / 10 k = **54 mA**. The data sheet's range for ISET is 675 ohm (800 mA) to **10.8 k (50 mA)**, so 54 mA is the lowest this part can be set to. The cell: standard charge 35 mA, maximum 70 mA (1 C); two cells in parallel 140 mA. So 54 mA is above the standard 0.5 C but within the maximum, and a lower current is not possible with the BQ21040. (datasheet; cell data sheet quoted in DECISION-LOG)
- **Charging in the cold:** the BQ21040 has no temperature input in use (10 k placeholder), the BQ25570 has none at all, the cell is rated for charging at 10-45 C. Nothing stops charging below 10 C. Accepted limitation, to be written on the product page. (datasheet)
- **Hot plug:** a long cable with a 1 uF ceramic can ring the input to roughly twice the supply (about 10 V, my estimate); the BQ21040 input is rated 30 V and switches charging off above 6.65 V; D51 clamps at 9.8 V (1 A). (datasheet, calculated)
- **Back-feed with no USB:** with the input dead the BQ21040 goes to sleep and drains the cell by only about 1 uA (the data sheet's "low battery leakage current" figure); C55 and D51 sit on VBUS only.

**USB-C receptacle (J2):** 5.1 k on CC1 and CC2 to ground = sink only, any USB-C source gives 5 V (no power delivery negotiation, so never more than 5 V). VBUS pairs A4/B9 and A9/B4 are joined by copper (checked: the north pair joins through a T junction at (108.59, 97.665)). The four shell pins are on GND. D+ / D- not connected, no damage possible there. (netlist, board)

## 3. The ESD question (CC, SBU, buttons)

| Line | What is on it | My answer |
|---|---|---|
| VBUS | D51 (5 V bidirectional TVS), C55 | done. D51 is on the VBUS line 8.4 mm of 0.1 mm copper from the receptacle pins (8.8 mm from the north pair), 3.1 mm of that line is the run to U5.6. |
| CC1 / CC2 | 5.1 k resistors to ground only, no chip | **No extra part needed.** A discharge on a CC pin can only flow through a resistor to ground. |
| SBU (UPDI) | R72 1 k in series, D50 BAT54WS to +3V3, then the MCU's UPDI pin | **Probably sufficient, not proven.** Estimate for an 8 kV contact discharge (330 ohm / 150 pF model): about (8000 - 4) / (330 + 1000) = 6 A peak, decaying in about 0.2 us, 1.2 uC in total; the clamp takes it into +3V3 (C54 22 uF, so +0.05 V). A BAT54-class Schottky is specified for much longer pulses at 0.6-4 A; I found no rating for nanosecond pulses, so "probably" is the honest word. A TVS on SBU would settle it (the same UMW part as D51, so no new BOM line), but **there is no room beside the connector**: the nearest free spot for a 3.2 x 1.9 mm part is 6.6 mm away. Making room means moving R72 / R70 / C53 / R69. Reviewer's call. |
| SBU, DC fault | a damaged cable can short VBUS to SBU (they are neighbours in the connector): 5 V through 1 k into the clamp, (5 - 3.3 - 0.3) / 1 k = about 1.4 mA into +3V3, a rail the buck cannot sink; with only microamps of load the rail would sit near 4.5 V while the fault lasts (calculated; the IMU's operating limit is 3.6 V, no damage expected, but it runs out of range). **Recommendation:** connect the clamp cathode to VBAT (the MCU's own supply, and the cell can take the current) instead of +3V3. One net change on D50 pin 1 and a short re-route; I did not do it unasked. |
| Buttons BTN1 / BTN2 | the switch to ground, MCU internal pull-up, nothing else | **Low risk:** the KMR2's actuator is plastic, the contacts are inside, and the MCU pins carry their own 2 kV HBM protection. If the reviewer wants more: two TVS on the front side, free spots at (104.3, 106.3) for BTN2 and (95.0, 106.3) for BTN1 (about 2.8 mm from the switch pads), same part, 3 cents each, no new BOM line. |
| D+ / D- | not connected | nothing to protect. |

## 4. Programming and bring-up (reviewer's question 4)

- UPDI runs over the receptacle's SBU pins (tied together) through R72 1 k. A 1 k plus pin and trace capacitance (estimate 35 pF) is a 50 ns time constant; UPDI at 225 kbaud is 4.4 us per bit, so no problem even at 900 kbaud. (calculated)
- The cable must carry the SBU wires: many charge-only cables do not (checklist H4).
- MVIO fuse must be set to single supply and VDDIO2 is tied to VDD (checklist B7); firmware sets the IMU interrupt input level.
- **Two cells in parallel (J1 + J1B):** connecting a second cell at a different state of charge makes a surge current between the cells. Plug both in only at the same voltage, or use one first. (calculated, not in BRING-UP yet)
- **Reverse battery:** no protection; JST pin 1 = GND, pin 2 = BATT as in TinyCircuits' own wiring, but the wire colours of the real cell are unknown until measured. Meter first, then plug. (needs hardware; BRING-UP-TESTS step 0)

## 5. MCU, clock and sensor (netlist / board / datasheet)

- **Crystal:** 18 pF C0G caps with a 12.5 pF crystal: CL = (18 + 5) / 2 + about 1 = 12.5 pF (the 5 pF is the XTAL pin capacitance from the AVR128DB data sheet). The crystal block was later moved 1.2 mm west, so the real stray capacitance is a little higher: check the frequency on the bench. The crystal pour has 14 stitching vias, every corner within 0.5-0.6 mm of one. (datasheet, board)
- **Decoupling:** U1.14 -> C10 1.4 mm, U1.28 -> C11 2.2 mm, U1.42 -> C13 (10 uF) 4.8 mm; the reviewer's rule is "within about 1 mm, no via between". The QFN is boxed in by the crystal keep-out, the ring fan-out and the LED vias; at 4 MHz this is common practice, but it is a deviation, listed for the reviewer. (board)
- **I2C:** 10 k pull-ups to +3V3 (R20, R21), IMU address 0x18 (SDO to ground), the interrupt to PE0. IMU supplied from +3V3. (netlist)
- **LED matrix:** columns source through 220 ohm, rows sink; the row pin's guaranteed sink is 10 mA (VOL 0.5 V), the firmware lights at most `m` LEDs per slot to stay under it (2 per slot at 4.2 V, about 4.8 mA each); this is tested in the host tests. (datasheet, firmware)
- **Firmware checks run today:** C core and JS simulator identical on 22 scenarios, 71 unit checks, 230 hardware-layer checks, 0 failed; AVR build 33,006 B of 131,072 B flash, 2,220 B RAM. **Nothing has run on a real chip.** (run today)

## 6. The reviewer's layout points (2026-10-28 / 29), checked on today's board

| Point | Today | Status |
|---|---|---|
| B2 power loops: short, wide, one layer, inductors close, vias to the bottom for the inductors | L1 5.6 mm from U4.20 (LBOOST copper 11.6 mm, 3 vias, 3 layers), L2 9.7 mm from U4.16 (LBUCK 13.6 mm, 2 vias). The data sheet itself says to use vias and bottom traces to connect the inductors, and to put CSTOR / CIN / CBYP first. Track width is 0.1 mm on every power net. | **deviation**, ask |
| B3 no acute angles | 39 -> **28** spots after the artefact pass; pieces under 0.05 mm: 25 -> 8, zero-length pieces 5 -> 0. What is left: the polar lanes (COL10 6.3 degrees at (83.68, 91.28) and its T junctions, COL11 T junction at (90.22, 84.29), ROW3 / ROW11 / VBAT T junctions at 45 degrees) and ring-lane joints. | partly done, listed |
| B4 traces leave pads along the axis | all 26 pads of the 14 two-pad parts in the USB-C corner checked: they leave along the axis (the last two exceptions, R69.2 and R72.2, were fixed by the owner) | done for the corner |
| B5 inner plane clearance down to JLC's minimum | GND zones use 0.2 mm clearance; JLCPCB's minimum for 4 layers is 0.09 mm | not changed |
| B6 crystal pour deleted or stitched | stitched (14 vias) | done |
| B8 bypass caps | see section 5 | deviation, ask |
| Test points | none on the board; for bring-up use the big pads: C54 for +3V3 / GND, J1 pads for the battery, C52 / C13 for VSTOR, L1 pad 2 for SOLAR_IN, the J2 pads for VBUS | note added to the bring-up list below |


## 6b. Power-chain proximity, measured (2026-11-03 evening; pictures `power-chain-proximity.png`, and after the CIN move `power-chain-cin-lane.png`)

Straight pad-to-pad distance from each part to the pin it serves, and the length of copper between them (a script walked the net's copper through vias). The data sheet's priority order for the boost charger: CBYP and CSTOR at VSTOR (pin 19) / VSS, then CIN at VIN_DC (pin 2) / VSS, then L1 at LBOOST (20) and VIN_DC; for the buck: COUT at VOUT (14) / VSS, L2 at LBUCK (16) and VOUT.

| Part (role) | Straight | Copper | Verdict (my thresholds: good <= 3 mm, acceptable 3-6, far > 6) |
|---|---|---|---|
| C52 4.7 uF (CSTOR) | 1.3 | 1.9 | good |
| C53 10 nF (CBYP) | 8.4 | 11.2 | far: the data sheet puts this first |
| **C50 4.7 uF (CIN, VIN_DC)** | **7.7** (was 11.2) | **14.1** (was 19.4) | **far-ish; moved by the owner's choice into the lane above L1 (106.15, 96.45), straight onto the SOLAR_IN node; pin 1 / pin 2 are on the south edge, which the battery keeps clear, so closer is not possible** |
| C54 22 uF (COUT) | 4.3 | 6.2 | acceptable |
| L1 (LBOOST end / VIN_DC end) | 5.7 / 7.5 | 11.8 / 16.2 | far-ish |
| L2 (LBUCK end / VOUT end) | 9.7 / 8.2 | 13.6 / not measured | far |
| C51 10 nF (CREF) | 4.8 | 8.1 | acceptable (high-impedance node, short stub matters more) |
| VBAT_OV divider (R50 / R51) | 2.4 | 3.2 | good |
| OK_HYST / OK_PROG dividers | 5.7 / 4.0 | 16.7 / 10.1 | acceptable straight, long copper |
| VOUT_SET divider | 3.6 | 5.3 | acceptable |
| BQ21040: C55 (IN) / C56 (OUT) | 3.5 / 1.6 | 7.3 / - | acceptable / good |
| BQ21040: R70 (ISET) / R71 (TS) | 3.7 / 3.5 | 6.7 / 6.9 | acceptable (DC nodes) |
| MCU: C10 / C11 / C13 to the VDD pins | 1.4 / 2.2 / 4.8 | 2.4 / 3.8 / 8.2 | good / good / acceptable-far |
| IMU: C30 / C31 | 3.5 / 3.6 | 10.9 / 8.5 | acceptable straight, long copper |

**What was tried for the others (2026-11-03 night).** The back is two LiPo envelopes (User.3: x 90.7-109.3, y up to 97.6 and from 102.4) with a 4.8 mm band between them; the east pocket beside U4 is about 7.4 x 4.6 mm and over 90 % full (C52, R54, R53, C54, L1), the west side is full too (6 of 6 slots; L2 cannot move west, the piezo is 0.17 mm away). To put CBYP (C53) beside C52 and CIN beside L1 the divider resistors R53 / R54 have to leave: (a) north-west strip: rejected by the owner (battery); (b) above R53: needs about 20 pieces of the owner's UPDI / COL4 / COL5 routing moved; (c) R54 into C53's old spot: the grid router finds no route to the OK_PROG node (L1, the VBUS corner and the COL / UPDI bundles box it in, both pad orientations, rip-up allowed); (d) R54 into C50's old spot: 46 pieces / 21 mm for a 5 mm link. So only CIN moved, CBYP stays at 8.4 mm (CSTOR 4.7 uF at 1.3 mm covers the low frequencies); a question for the reviewer. Pictures of the options: `power-chain-swap-proposal-2.png`; the move that was made: `power-chain-cin-lane.png`.

All ground returns reach a GND via within 0.5-1.4 mm of copper (the inner plane does the rest). The 4.7 uF input cap has free room right next to the IC: the nearest free spots for another 0402 on the back are about 1.0-1.1 mm from U4 pin 2, for example (99.4, 103.4) vertical or (99.0, 102.9) horizontal.

## 7. JLCPCB

- DFM: 229 pairs of traces at exactly 0.100 mm (JLCPCB's stated minimum for 4 layers is 0.09 mm), 0.10 mm tracks and 0.15 mm via rings by design; these were the red items of the earlier JLCDFM run.
- Files ready in `hardware/production/`: Gerber zip (14 files), `assembly/BOM.csv` (33 lines, 205 parts, every line with an LCSC number), `assembly/CPL.csv`. Stock of D51's part C19185929 (LCSC showed 5,100 on 2026-11-02) and a new quote are still open.

## 8. Questions for the reviewer, in order

1. SBU: the owner has decided against a TVS for the prototype (needs R72 / R70 / C53 / R69 moved); should the clamp go to VBAT?
2. Buttons: no TVS (owner's decision).
3. Inductor distances (L1 5.6 mm, L2 9.7 mm), the 11.6 mm LBOOST and CBYP (C53) at 8.4 mm / 11.2 mm of copper (picture `cbyp-8p4mm.png`; the slot beside C52 is R54's and R54 cannot be moved, see the decision log 2026-11-03 night): acceptable for a first board, or move closer?
4. Bypass caps at 1.4 / 2.2 / 4.8 mm: acceptable?
5. Inner-plane clearance 0.2 mm: reduce to 0.1 mm?
6. Anything in the USB-C block (CC, VBUS, shell, SBU) he would change?
