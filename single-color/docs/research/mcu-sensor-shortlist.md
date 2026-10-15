# MCU + sensor shortlist (JLCPCB live library, queried 2026-10-08)

Source: JLCPCB parts-library search (all listed as Extended parts = extra feeder fee at assembly). Stock/price at qty 1. Pin counts are from my memory of the families (UNVERIFIED until the datasheet is read).

## Pin budget
- Single colour: 12 columns + 11 rows = 23 matrix pins; + 2 buttons, I2C (2), sensor INT (1), battery-sense ADC (1), UPDI/reset (1) = about 30 GPIO. Crystal pins are separate.
- RGB (original): 22 rows + 18 columns = 40 matrix pins; + same extras = about 47 GPIO -> needs a 64-pin part.

## Single-colour candidates
| Part | Package | I/O (approx) | JLCPCB stock | JLCPCB $ | Note |
|---|---|---|---|---|---|
| AVR128DB48-I/PT (C1019766) | TQFP-48 7x7 | 37 | 60 | 5.38 | current default; 217 at DigiKey; UPDI |
| AVR128DB48-I/6LX (C1019768) | VQFN-48 6x6 | 37 | 48 | 5.73 | smaller, harder to hand-fix |
| AVR128DA48-I/PT (C1012825) | TQFP-48 7x7 | 37 | 22 | 4.99 | no crystal-failure detect extras; same pinout family |
| AVR64DD32-I/PT (C5227839) | TQFP-32 | 27 | 23 | 3.26 | too few pins unless matrix shrinks |
| ATmega1284P-AU (C33575) | TQFP-44 10x10 | 32 | 1,943 | 6.59 | best JLCPCB stock; ISP not UPDI; very tight on pins; big body |
| ATmega644PA-AU (C38349) | TQFP-44 10x10 | 32 | 311 | 3.98 | same, 64 KB |
| ATmega328PB-AU (C132230) | TQFP-32 | 27 | 610 | 1.85 | too few pins for 12x11 |

## RGB candidates (64-pin)
| Part | Package | I/O | JLCPCB stock | JLCPCB $ |
|---|---|---|---|---|
| ATmega169PA-AU (C9434) / -AUR (C507109) | TQFP-64 14x14 | 54 | 170 / 226 | 4.87 / 4.02 |
| ATmega165PA-AU (C1339717) - what the RGB board uses | TQFP-64 14x14 | 54 | 10 | 6.90 |
| AVR128DA64-I/PT (C2912283) | TQFP-64 10x10 | 53 | 28 | 5.06 |
| AVR128DB64-I/MR (C1019767) | QFN-64 9x9 | 53 | 11 | 5.55 |

## Motion + other sensors (JLCPCB)
| Part | JLCPCB | Stock | $ | Note |
|---|---|---|---|---|
| LIS2DW12TR (C189624) | LGA-12 2x2 | 19,712 | 1.19 | ST page: 50 nA power-down, <1 uA active low-power, 1.62-3.6 V, wake-up/tap/6D/free-fall/activity, built-in temperature sensor, 32-level FIFO. ST datasheet PDF exists at st.com/resource/en/datasheet/lis2dw12.pdf (my download tool was blocked; the product page figures were read directly) |
| BMA400 (C437655) | LGA-12 2x2 | 199 | 14.91 | 0 stock at DigiKey; JLCPCB price very high |
| LIS3DH (C15134) | LGA-16 3x3 | 140 | 1.81 | older, ~2 uA low-power |
| VEML7700 (C504893) | SMD-4P | 3,340 | 1.13 | ambient light sensor (current UNVERIFIED) |
| OPT3001 (C90462) | USON-6 | 4,850 | 1.56 | ambient light sensor (current UNVERIFIED) |
| SHTC3 (C194656) | DFN-4 | 4,960 | 2.21 | temp + humidity |
| DRV5032 (C3716089) | TO-92 | 380 | 0.32 | Hall switch; TO-92 is the wrong package for a watch, small variants not checked |
