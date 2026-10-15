# Single-colour watch — schematic design notes (generated 2026-10-06)
Files: `gen_schematic.py` (the parametric generator), `symlib.py` (reads KiCad's own symbol libraries),
`watch_usb.kicad_sch` (Variant A) and `watch_solar.kicad_sch` (Variant B). Re-run:
`"C:\Program Files\KiCad\10.0\bin\python.exe" gen_schematic.py --variant usb|solar`.
Each run is checked with KiCad's own tools: netlist export, a 132-LED row/column mapping check (0 errors), and ERC.

## What is common to both variants
- **LED matrix:** 12 columns (one per 30-degree sector, wired as a radial line) x 11 rows (slot 0 = hour LED, slots 1-5 = five minute LEDs, slots 6-10 = five second LEDs). Anode -> ROWn, cathode -> COLn, one series resistor per column (R1-R12, 150 ohm PLACEHOLDER). Only ~3 LEDs light at once, so MCU pins drive rows (source) and columns (sink) directly. Refs: H1-H12, M0-M59, S0-S59 (minute/second index = clock position).
- **MCU: Microchip AVR128DB48-I/PT (TQFP-48, 7x7 mm).** 23 matrix pins + SDA/SCL (PA2/PA3) + IMU interrupt + 2 buttons + charger/battery status + UPDI; 32.768 kHz crystal on PF0/PF1 (XTAL32K1/2 — verified in the datasheet); decoupling 100 nF per supply pin + 10 uF.
- **IMU: BMI270** (drawn with KiCad's BMI160 symbol: identical 14-pin pin-out; value says BMI270). VDD/VDDIO from 3.3 V, CSB high (I2C), SDO low (address 0x68), ASDx/ASCx/INT2/OCSB/OSDO unconnected, per BMI270 datasheet table 22.
- Buttons SW1/SW2 (active low, MCU pull-ups), UPDI 3-pin header J2, LiPo connector J1 (JST SH 2-pin).

## Variant A — pad/USB charged (`--variant usb`)
MCP73831-2 charger (4.2 V CV, charge current = 1000/Rprog mA; Rprog 10k = 100 mA, sized for a ~100 mAh cell), charge pads TP1/TP2 (VBUS/GND), STAT -> MCU. A 3.3 V LDO (MCP1700-3302, 1.6 uA Iq) feeds the IMU because the LiPo reaches 4.2 V and the BMI270 is limited to 3.6 V. System rail = battery.

## Variant B — solar (`--variant solar`)
TI **BQ25570** harvester/charger instead of the charger + LDO. Why the BQ25570 and not the BQ25504:
- BQ25504 datasheet (SLUSAH0G, rev Aug 2023) recommends VIN_DC only 0.13-3 V. Evan's cell (KXOB081K06TF) has Vmpp 3.35 V and Voc 4.15 V -> outside the recommended range.
- BQ25570 (SLUSBH2G) recommends VIN_DC 0.1-5.1 V, ties VOC_SAMP to VSTOR for 80% MPPT (the cell's Vmpp/Voc = 3.35/4.15 = 0.807), and has a built-in nano-power buck that makes the 3.3 V rail (so the LDO is not needed).
Resistor values come from the datasheet's own design procedure (VBIAS = 1.21 V, RSUM = 13 Mohm; sections 7.3.3, 7.3.4, 7.3.6), 1% values:
| Setting | Target | Resistors | Result |
|---|---|---|---|
| Battery over-voltage (charge stops) | 4.10 V | R50 6.49M / R51 5.11M | 4.12 V (4.10-4.15 over VBIAS tolerance) |
| BAT_OK falling / rising | 3.3 / 3.7 V | R52 1.47M, R53 6.49M, R54 3.74M | 3.31 / 3.78 V |
| 3.3 V output | 3.3 V | R55 8.25M / R56 4.75M | 3.31 V |
Other parts per the datasheet's typical circuit: CIN 4.7 uF, CSTOR 4.7 uF + 10 nF, CREF 10 nF (low-leakage C0G/X7R), COUT 22 uF, L1 22 uH (boost), L2 10 uH (buck; datasheet example Toko DFE252012C); ~EN to GND, VOUT_EN to VSTOR (full operation). The LiPo sits on the VBAT pin (net BATT) and the system rail is VSTOR (net VBAT). The battery must be >= 100 uF equivalent: a LiPo is.
Battery protection: BQ25570's own UV cut-off is fixed at ~1.95 V, which is far below a LiPo's safe limit, so this variant REQUIRES a LiPo with its own protection circuit (the Renata-type cells listed in solar-power-research.md have one).

## Placeholders / things to verify (nothing here is final)
1. Column resistor 150 ohm: needs an LED-current calculation. White LED Vf ~2.6-3.3 V is almost the whole LiPo range (3.0-4.2 V), so brightness will vary a lot with charge; plan to correct brightness in firmware using the MCU's internal VDD/10 ADC channel.
2. Crystal load caps 18 pF (ABS07 specifies CL = 12.5 pF; value is a rule-of-thumb) — confirm with the AVR128DB datasheet/EE.
3. MCP73831 capacitor values (4.7 uF) and Rprog — verify against its datasheet.
4. BQ25570 footprint: the RGR VQFN-20 (3.5x3.5 mm) is not in KiCad's stock libraries -> a custom footprint is needed before the PCB step (the schematic footprint field says TBD).
5. L1/L2 footprints are a generic 1210 placeholder; pick real inductors with Isat above the datasheet's current limits.
6. Solar cell connector J3 is a placeholder; the real part needs two 12 x 2 mm pads on the PCB matching the SolarBIT's back pads (+ at one 25 mm end, - at the other) and a low-temperature solder process (see ../solar-cell-evaluation-KXOB081K06TF.md).
7. LiPo connector polarity: confirm the cell's lead order against JST pin 1/2 before ordering.
8. ERC: the only notices are expected — BMI270 SDO tied to GND (as its datasheet says) and the TBD footprint.
9. Not yet designed: PCB placement/routing, strap lugs, power-path details such as reverse-polarity protection, ESD on buttons/pads, and the optional external RTC footprint.
