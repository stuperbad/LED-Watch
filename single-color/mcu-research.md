# LED Watch (132 white LEDs) - MCU / RTC / IMU research

Date: 2026-10-05. Scope: 12x11 matrix (23 GPIO) or 12-pin charlieplex, LiPo 3.0-4.2 V, tiny sleep current, parts at JLCPCB/LCSC and/or DigiKey.

## 0. How to read the tags

- **VERIFIED (doc, section)**: I read the exact manufacturer datasheet text for the exact MPN family in this session.
- **UNVERIFIED**: from a distributor page / search snippet / my memory only. Re-check before layout. No pin function or spec was borrowed from a sibling part. Where a datasheet could not be downloaded, the item is tagged UNVERIFIED and the part is not recommended on that basis alone.
- Stock/price figures are LCSC web-page snapshots fetched 2026-10-05 and move daily. **JLCPCB Basic vs Extended: UNVERIFIED for every part** (the pages I could fetch do not show the library class). Assume Extended (MCUs of this class almost never are Basic) and budget the per-part Extended fee.
- DigiKey stock came mostly from search-engine summaries, so treat as UNVERIFIED snapshots.

## 1. Key design finding: supply voltage decides a lot

LiPo is 3.0-4.2 V. Parts rated to 5.5 V (AVR DB/EA, ATmega1284P, PIC18-Q) run straight off the cell. Parts rated to 3.6 V (STM32L0/U0, nRF52, MSP430) need an LDO/buck, whose Iq adds to sleep current, and the rail sits at about 3.3 V. White LEDs have Vf of roughly 2.7-3.2 V (check your LED's datasheet), so a 3.3 V rail leaves almost no headroom for series resistors, and GPIO current is poorly controlled. Straight-from-battery 5.5 V-tolerant MCUs give headroom, but then LED current varies with battery voltage (a few resistors only, no constant-current), and a brightness-compensation table keyed on the battery ADC reading is advisable. ATmega1284P abs-max is 40 mA per I/O pin (VERIFIED, DS Atmel-8272F, section 28 Abs Max); the AVR DB per-pin limit I did not extract.

## 2. Candidate comparison

| | A. AVR128DB48-I/PT | B. AVR64EA48-I/PT | C. ATmega1284P-AU | D. STM32L071CBT6 (L072 pin-compatible, USB) | E. nRF52832-QFAA-R | F. PIC18F57Q43-I/6LX |
|---|---|---|---|---|---|---|
| Package | TQFP-48 7x7 (also VQFN-48 6x6, -I/6LX). Pitch 0.5 mm UNVERIFIED (not printed in text I read) | TQFP-48 7x7 (pitch UNVERIFIED) | TQFP-44 10x10, **0.80 mm** pitch (VERIFIED, 8272F sec 33.1 pkg 44A); also VQFN-44 7x7 0.50 mm (VERIFIED, pkg 44M1) but LCSC listing I found is TQFP | LQFP-48 7x7 | QFN-48 6x6 (LCSC listing; 0.4 mm pitch UNVERIFIED) | VQFN-48 6x6 (LCSC) |
| GPIO | 41 incl. RESET pin / 40 without (VERIFIED, DS40002247B Table 2, 48-pin col.) | 42/41 (VERIFIED, DS40002443A Table, 48-pin col.) | 32 (VERIFIED, 8272F features) | 37 on LQFP48 (VERIFIED, DocID027101 Rev 3 Table 2) | 32 (VERIFIED, Nordic PS key features) | 44 per LCSC listing (UNVERIFIED) |
| Flash / RAM | 128 KB / 16 KB (VERIFIED, Table 1) | 64 KB / 6 KB (VERIFIED, intro) | 128 KB / 16 KB (VERIFIED) | 128 KB / 20 KB (+6 KB EEPROM) (LCSC; family up to 192 KB, VERIFIED) | 512 KB / 64 KB or 256/32 (VERIFIED) | 128 KB (LCSC), RAM UNVERIFIED |
| Supply | 1.8-5.5 V (VERIFIED, sec 4/ features) | 1.8-5.5 V (VERIFIED, DS40002443A line "Supply voltage range: 1.8-5.5V") | 1.8-5.5 V (VERIFIED) but 4 MHz max below 2.7 V, 10 MHz below 4.5 V... (VERIFIED speed grades) | 1.65-3.6 V (VERIFIED) - needs LDO | 1.7-3.6 V (VERIFIED) - needs LDO | 1.8-5.5 V (LCSC; UNVERIFIED in DS) |
| 32.768 kHz crystal pins | **PF0 = XTAL32K1, PF1 = XTAL32K2** (VERIFIED, 48-pin pinout fig and pin-mux table: TQFP pins 34/35). Pins are overridden/dedicated when XOSC32K is enabled, so they are lost as GPIO (VERIFIED sec 4.5.1 / 36.x) | Same: PF0/PF1 = XTAL32K1/2, TQFP pins 34/35 (VERIFIED) | **PC6 = TOSC1, PC7 = TOSC2** (VERIFIED, Table 14-9). Tied to Timer/Counter2 async RTC; lost as GPIO when AS2 set (VERIFIED sec 17) | **PC14 = OSC32_IN, PC15 = OSC32_OUT** (VERIFIED pin names, DocID027101). Shared with GPIO | XL1/XL2 = P0.00/P0.01 (UNVERIFIED; PS pin table not retrieved) | SOSCI/SOSCO exist (VERIFIED, DS40002147F sec 12) but pin letters not extractable from my text conversion: UNVERIFIED |
| Sleep, RTC running | Power-Down 0.65 uA typ @3 V (0.8 uA with HTLLEN) (VERIFIED, DS40002247B Table 39-4) + RTC from XOSC32K 2.1 uA (LPMODE=1) + XOSC32K 0.5 uA (LPMODE=1) (VERIFIED, Table 39-5) => **about 3.3 uA derived, not a datasheet figure**. RTC on internal OSC32K: 0.7+0.3 uA (inaccurate clock) | Power-Down/Standby 0.08 uA typ (not tested, "design guidance") (VERIFIED, DS40002443A Table 35-5, **preliminary datasheet**); XOSC32K current is blank/TBD in that revision | Power-save with 32 kHz TOSC: 0.5 uA @1.8 V, 0.6 uA @3 V typ (VERIFIED, 8272F Table 28-9 "1284P DC characteristics"); Power-down WDT off 0.15 uA typ | Stop + RTC + RAM: 0.86 uA (VERIFIED, features); Standby (no RTC) 0.29 uA (VERIFIED, Table 37); Standby+RTC not extracted (UNVERIFIED) | System ON, RTC wake: 1.9 uA @3 V (VERIFIED, PS key features); System OFF 0.3 uA | Sleep base 1.1 uA + SOSC 2.1 uA @3 V => about 3.2 uA derived (VERIFIED, DS40002147F Table 47-3, preliminary datasheet) |
| I2C / ADC | 2x TWI (PA2/PA3 = TWI0 SDA/SCL on 48-pin, Fm+) (VERIFIED); 12-bit ADC with **VDDDIV10 internal channel** for battery sense (VERIFIED sec ADC) | TWI + ADC (family) | TWI on PC0/PC1 (VERIFIED); 10-bit ADC | I2C x3, 12-bit ADC | TWIM, SAADC | I2C, 12-bit ADC |
| Programming | UPDI (1 pin, PF7) (VERIFIED) | UPDI | ISP (SPI), JTAG; PB5-7/RESET | SWD (PA13/PA14) | SWD (dedicated pins, UNVERIFIED) | ICSP |
| LCSC | C1019766, **53 in stock**, $5.44 @1, $3.76 @100 (C1019768 VQFN: 48, $5.79). E-temp -E/6LX C1020223 out of stock | C7503036, **81 in stock**, $3.19 @1, $2.17 @100 | C33575, **1,998 in stock**, $6.65 @1, $4.83 @100 | C79758 STM32L071CBT6, **1,044**, $3.66 @1, $2.51 @250. STM32L072CBT6 C465977, 1,531, $3.75 | C77540, **29,860**, $4.03 @1, $2.84 @100 | C1236614, **out of stock** ($3.01 @1) |
| DigiKey | AVR128DB48-I/PT: 0 in stock, ~250 est. 2026-11-02 (ES mirror page, EUR 1.82 @1) | about 550 (UNVERIFIED snippet) | about 10k (UNVERIFIED snippet) | about 4.6k (UNVERIFIED snippet) | very large (UNVERIFIED) | UNVERIFIED |
| Toolchain | Microchip Studio/MPLAB X; Arduino core DxCore (supports DB/DA/DD/EA family, UNVERIFIED this session); PlatformIO via DxCore UNVERIFIED | Same family; EA support in DxCore UNVERIFIED | Arduino core MightyCore, avr-gcc, PlatformIO atmelavr (UNVERIFIED but long-standing) | STM32CubeIDE, Arduino_Core_STM32, PlatformIO ststm32 | nRF Connect SDK / Arduino nRF52 cores / PlatformIO (UNVERIFIED) | MPLAB X + XC8 |
| Caveats | **VDDIO2 pin must be tied to VDD for single-supply mode** and the MVIO fuse set accordingly (VERIFIED sec 19.2). Check Microchip errata before committing (not read). 24 MHz max | **Datasheet is "Preliminary"** (DS40002443A, 2022), sleep numbers incomplete. Newer revision may exist: check microchip.com | Oldest part; no UPDI. 0.8 mm TQFP-44 is big (10x10) for a 37 mm board. Shared pins: ISP vs matrix, JTAG PC2-5 (JTAGEN fuse). Active/NRND status not checked (UNVERIFIED) | LQFP-48 fine; 3.6 V max; LSE + SWD + BOOT0 shared pins | Needs LDO; BLE is a bonus; QFN 0.4 mm (UNVERIFIED) | Out of stock on LCSC; datasheet "Preliminary" |

Other families considered and not carried forward: STM32U073CBT6 (C27035627, LQFP-48, 1.71-3.6 V, **out of stock** at LCSC, $2.07; datasheet DS14548 Rev 2 read: Standby with RTC 160 nA, Stop 2 + RTC 825 nA, VBAT 130 nA, VERIFIED) - excellent on paper but not buyable on LCSC today; STM32U083CCT6 (C29759434, 2 in stock, $5.23). STM32L431CBT6 (C277951, 46 in stock, $8.34) overpriced. MSP430FR5994IPNR (LCSC C2052740, LQFP-80, 12x12, 3.6 V max, 1,011 in stock) too large. EFM32/EFR32: nothing found on LCSC (UNVERIFIED for DigiKey); not evaluated. Chinese low-power parts (e.g. HC32L130) appear on LCSC but were not researched.

## 3. Pin budgets

Needs: 23 matrix (12 columns + 11 rows) + 32 kHz crystal (2) + I2C (2) + IMU INT (1) + buttons (2) + battery ADC (1, or use internal VDD/10 on AVR) + programming/debug.

### 3a. AVR128DB48 (primary)

| Function | Pins | Notes |
|---|---|---|
| Matrix columns/rows | 23 of: PA4-7, PB0-5, PC0-7, PD0-7, PE0-3 (about 30 pins available) | Keep PA2/PA3 free for TWI0 |
| 32 kHz crystal | PF0, PF1 | Dedicated, VERIFIED |
| I2C (IMU/RTC) | PA2 = SDA, PA3 = SCL (TWI0 default) | VERIFIED; PORTMUX can move it |
| IMU INT | any PORT pin with async wake (e.g. PE0) | Pin-interrupt wake from Power-Down; async-capable pin set not verified |
| Buttons (2) | PE1, PE2 | |
| Battery ADC | none needed: internal VDDDIV10 channel | VERIFIED |
| UPDI | PF7 (dedicated) | |
| RESET | PF6 (or use as GPIO via fuse) | |
| VDDIO2 | tie to VDD | VERIFIED |
| Total | 23 + 2 + 2 + 1 + 2 = 30 of 40 usable; 10 spare | Plenty of headroom: could even go matrix + a few spare for a charlieplex test |

### 3b. ATmega1284P (backup)

| Function | Pins | Notes |
|---|---|---|
| 32 kHz crystal | PC6/PC7 (TOSC1/2) | Lose 2 of 32 GPIO => 30 |
| I2C | PC0 (SCL), PC1 (SDA) (VERIFIED) | |
| Matrix 23 | PA0-7, PB0-7 (conflicts with ISP MOSI/MISO/SCK PB5-7), PD0-7, PC2-5 (JTAG, needs JTAGEN fuse off) | Awkward: LEDs on PB5-7 will fight the ISP programmer; use series resistors and keep ISP on PB5-7 with RESET low only while programming (works) |
| INT / buttons / ADC | 1 + 2 + 1 | Total 29 of 30: fits but zero spare. ADC battery sense needs a divider (draws current) or bandgap-vs-VCC trick |
| Awkward | 0.8 mm TQFP-44 10x10 is a big part for the back of a 37 mm board; clustering is hard |

### 3c. Charlieplex option
12-pin charlieplex (132 LEDs) fits any of the above and frees about 11 pins, but needs more careful current-limit/LED-Vf matching and shows ghosting at low Vf headroom; with only ~3 LEDs lit at once, the 23-pin matrix is simpler and safer.

## 4. External RTC vs MCU RTC

| Option | Verified spec | LCSC / DigiKey (2026-10-05) |
|---|---|---|
| RV-3028-C7 (Micro Crystal), I2C, 8-pin SMD3215 | 45 nA @3 V timekeeping (60 nA max), 1.1-5.5 V (1.2 V for I2C), +-1 ppm @25 C factory-calibrated, INT/alarm + EVI pins, backup switchover (VERIFIED, RV-3028-C7 datasheet page via BFH mirror; pins 1 CLKOUT, 2 INT, 3 SCL, 4 SDA, 5 VSS, 6 VBACKUP, 7 VDD, 8 EVI per block diagram) | LCSC C3019759 (-QC) and C3304278 (-QA): **out of stock**, $1.44-$2.22. DigiKey QC variant backorder; QA variant 830 in stock at Dove (UNVERIFIED) |
| RV-8803-C7 | 240 nA @3 V, 1.5-5.5 V, +-3 ppm (LCSC description, UNVERIFIED vs datasheet) | C5341296 / C2846926: out of stock |
| PCF8563 (IDCHIP clone C5795601, $0.13) / NXP original | Needs external crystal; clone vs original behaviour UNVERIFIED | C5795601: 34,346 in stock; do not trust the clone's current figures |
| DS3231M | TCXO class; price $5.90, 347 in stock (C37663); current UNVERIFIED | |
| AB1805 | Not found on LCSC | |

**Recommendation:** with the AVR DB the saving from an external RTC is about 2.5-3 uA (3.3 uA derived for MCU RTC + crystal oscillator vs 0.045 uA), because on the DB the XOSC32K and RTC dominate sleep current. With ATmega1284P it saves only about 0.45 uA (0.6 power-save vs about 0.15 power-down), not worth a part. With nRF52832 it saves about 1.6 uA. A watch that only lights the display on wrist-raise sleeps most of the time, so the saving is real but modest (about 17 mAh/yr per 2 uA, i.e. about 10-15 % of a 100-150 mAh cell per year - my arithmetic). Counter-considerations: RV-3028 is factory trimmed to +-1 ppm (vs about 20 ppm raw crystal needing calibration), has battery backup switchover, but is **out of stock on LCSC** (JLCPCB assembly requires supply), adds I2C reads on wake, and costs $1.4-3. Recommendation: **start with the MCU's own RTC (XOSC32K LPMODE=1 on DB)** for the first board; add a footprint option for RV-3028-C7 (or a 32.768 kHz crystal pair as BOM-DNP alternatives) if the measured sleep current is too high. If you do want the external RTC to run the whole watch, use RV-3028 INT as the 1 Hz/alarm wake and leave PF0/PF1 as GPIO.

## 5. IMU

### 5a. BMI270 (VERIFIED, Bosch BST-BMI270-DS000-08, rev 1.6, sec 4.4)
- After every POR or soft reset the IMU stays in suspend; you must disable advanced power save, write INIT_CTRL=0, **burst-write an 8 kB configuration file (bmi270_config_file) to INIT_DATA (about 6.6 ms at 10 MHz SPI), write INIT_CTRL=1, and wait up to 20 ms for INTERNAL_STATUS.message=1**. Can be chunked if the host's burst is smaller.
- Pin-out VERIFIED (sec 7.1, Table 22): LGA-14 2.5x3. 1 SDO, 2 ASDx, 3 ASCx, 4 INT1, 5 VDDIO, 6 GNDIO, 7 GND, 8 VDD, 9 INT2, 10 OCSB, 11 OSDO, 12 CSB, 13 SCx, 14 SDx. Typ. current 685 uA in full-ODR A+G mode.
- MCU flash for the 8 kB blob: all candidates have far more (smallest is the EA at 64 KB). It must be re-uploaded on every IMU power-up, so keep the IMU on the always-on rail (do not power-gate it) or you pay about 26 ms of init each time.

### 5b. Alternatives (accelerometer-only is enough for wrist-raise)

| Part | Package | Config upload? | Key specs | LCSC | Footprint-compatible with BMI270? |
|---|---|---|---|---|---|
| **BMA400** (Bosch) | LGA-12 2x2x0.95 | **No** - POR boot is automatic; no INIT_CTRL register in the datasheet (VERIFIED, BST-BMA400-DS000-09 rev 1.8, POR text and register list) | VDD 1.62-3.6 V, VDDIO 1.2-3.6 V; sleep 160 nA; low-power 25 Hz ODR 850 nA; normal mode 14.5 uA; step counter 4 uA; auto-wakeup, wake-up, activity-change, orientation interrupts; power-up 1 ms (all VERIFIED). Pinout (VERIFIED): 1 SDO, 2 SDX, 3 VDDIO, 4 NC, 5 INT1, 6 INT2, 7 VDD, 8 GNDIO, 9 GND, 10 CSB, 11 NC, 12 SCX | C437655: 96 in stock, **$15.06 @1 / $11.26 @100** (expensive) | **No** (12-pin 2x2 vs 14-pin 2.5x3) |
| **LIS2DW12TR** (ST) | LGA-12 2x2 | Believed no (UNVERIFIED; ST DS not downloadable here) | LCSC lists 1.62-3.6 V, 50 nA standby (UNVERIFIED), wake-up/activity/6D/free-fall/tap | C189624: 19,313 in stock, $1.20 @1, $0.74 @1k | No (different footprint) |
| BMA456 (Bosch) | LGA-12 2x2 | **Yes** - same INIT_CTRL / FEATURES_IN burst-write scheme as BMI270 (VERIFIED, BST-BMA456-DS000-01 sec 4.2; size not stated in the doc I read) | 1.62-3.6 V | C189518: 2,540 in stock, $4.91 | No. Does **not** solve the config-upload problem |
| **LSM6DS3TR-C** (ST) | LGA-14 2.5x3x0.86 | Believed no (UNVERIFIED - ST DS not reachable) | 1.71-3.6 V; 0.90 mA high-perf (LCSC/ST summary); pin map from secondary source (Adom wiki, UNVERIFIED vs ST DS): 1 SDO/SA0, 2 SDx, 3 SCx, 4 INT1, 5 VDDIO, 6 GND, 7 GND, 8 VDD, 9 INT2, 10 NC, 11 NC, 12 CS, 13 SCL, 14 SDA | C967633: 22,130 in stock, $1.53 @1, $0.97 @1k | **Likely drop-in** for BMI270 on pins 1-9, 12-14 (pins 10/11 are OCSB/OSDO on BMI270 vs NC on ST). Pin 2/3: tie as BMI270 requires (VDDIO/DNC) and ST requires (tie to VDDIO or GND in mode 1). **Confirm against the ST datasheet before relying on this.** Gyro adds idle current unless powered down |
| ICM-42607-P (TDK) | LGA-14 2.5x3 | Unknown (UNVERIFIED; datasheet not reachable) | LCSC: 3.5 uA standby, 2.25 KB FIFO | C5129967: 10,019 in stock, $2.15 @1 | Pin order believed similar to ICM-426xx family but UNVERIFIED |

**IMU recommendation:** If you must keep the existing BMI270 footprint, **LSM6DS3TR-C is the only candidate with the same 14-pin LGA 2.5x3 and a probable matching footprint**, but verify its datasheet (config upload absence, pin table, accel-only low-power current) first. If you can respin the IMU footprint, **LIS2DW12TR (cheap, plentiful) or BMA400 (verified lowest current, no config upload, but about $11-15)** is the better wrist-raise choice. BMA456 has the same upload burden as BMI270.

## 6. Recommendation

**Primary: Microchip AVR128DB48-I/PT (LCSC C1019766)**, MCU RTC with 32.768 kHz crystal on PF0/PF1 (LPMODE=1), BMA400 or LSM6DS3TR-C/LIS2DW12TR on I2C (TWI0 = PA2/PA3), no external RTC at first.
- Runs straight off the LiPo (1.8-5.5 V, VERIFIED) so no regulator Iq and LEDs get real headroom; 40 usable GPIO leaves 10 spare; 7x7 TQFP at 0.5 mm is easy to hand-solder/reflow; UPDI single-wire programming; internal VDD/10 ADC channel for battery sense.
- Estimated sleep with RTC from crystal about 3.3 uA (derived); with a 0.85 uA BMA400 in low-power mode, about 4-5 uA total (arithmetic, not measured).
- Risks: LCSC stock only 53 (ask JLCPCB/US assembler to consign-buy early; AVR64DB48 would be cheaper if it appears on LCSC, not checked); DigiKey 0 in stock now; Extended-fee likely; errata not reviewed; VDDIO2 must be wired to VDD.

**Backup: ATmega1284P-AU (LCSC C33575, 1,998 in stock)**. Best stock and the simplest, most proven tooling; 0.6 uA power-save with RTC is better than the DB on paper (VERIFIED). Costs: 10x10 mm 0.8 mm TQFP-44, only 30 usable GPIO (exactly fits the plan with 1 spare), pin-sharing with ISP/JTAG, 4 MHz max below 2.7 V. If you prefer an ARM backup, STM32L071CBT6 (C79758, 1,044 in stock, 37 GPIO, 0.86 uA Stop+RTC) works but needs an LDO from the LiPo.

**Not recommended now:** AVR64EA48 (attractive, 0.08 uA, cheaper, but preliminary datasheet and XOSC32K current unspecified); nRF52832 (great stock, BLE bonus, but 1.9 uA, 3.6 V max needs regulator, 0.4 mm QFN - consider only if BLE becomes a goal); PIC18F57Q43 (out of stock); STM32U073 (out of stock on LCSC).

## 7. Sources
- AVR128DB28/32/48/64 datasheet DS40002247B: https://datasheet.lcsc.com/lcsc/2410121941_Microchip-Tech-AVR64DB64T-I-PT_C3228455.pdf (Microchip complete data sheet; I downloaded via the LCSC-hosted copy)
- AVR64EA28/32/48 preliminary DS40002443A: https://docs.rs-online.com/35e4/A700000014022030.pdf
- ATmega164A/PA/324A/PA/644A/PA/1284/P datasheet Atmel-8272F (07/2014): https://community.infineon.com:443/gfawx74859/attachments/gfawx74859/psoc135/7549/1/Atmel-8272-8-bit-AVR-microcontroller-ATmega164A_PA-324A_PA-644A_PA-1284_P_datasheet.pdf
- STM32L071xx DocID027101 Rev 3: https://www.farnell.com/datasheets/2309235.pdf
- STM32U073x8/B DS14548 Rev 2: https://www.farnell.com/datasheets/4792202.pdf
- nRF52832 PS index: https://file01.andesource.com/dkpdf/NRF52832-QFAA-R.pdf ; Nordic product page: https://docs.nordicsemi.com/r/bundle/ps_nrf52832/page/pmu.html
- PIC18F27/47/57Q43 DS40002147F (preliminary): https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210171600_Microchip-Tech-PIC18F27Q43-I-SS_C641880.pdf
- BMI270 BST-BMI270-DS000-08: previously downloaded copy in the session scratchpad (Bosch Sensortec)
- BMA400 BST-BMA400-DS000-09: https://cdn.sparkfun.com/assets/e/9/e/6/0/BMA400-Datasheet.pdf
- BMA456 BST-BMA456-DS000-01: https://cdn.sparkfun.com/assets/1/2/c/2/f/BMA456.pdf
- RV-3028-C7: https://yggdrasil.ti.bfh.ch/_static/datasheets/yggdrasil/RV-3028-C7.pdf (Micro Crystal datasheet copy)
- LCSC pages: C1019766 https://www.lcsc.com/product-detail/C1019766.html ; C1019768 ; C1020223 ; C7503036 ; C33575 ; C79758 ; C465977 ; C77540 ; C27035627 ; C29759434 ; C1236614 ; C437655 ; C189518 ; C967633 ; C5129967 ; C189624 ; C3019759 ; C3304278 ; C5341296 (all at https://www.lcsc.com/product-detail/C<number>.html)
- DigiKey mirror for AVR128DB48-I/PT: https://punchouttest.digikey.es/en/products/detail/microchip-technology/AVR128DB48-I-PT/12807288
- LSM6DS3TR-C pin map (secondary source, UNVERIFIED): https://wiki.adom.inc/ray/lsm6ds3tr
