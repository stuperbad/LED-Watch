# MCU pin verification against the datasheets (revision B, 2026-10-29)

Question: is every U1 connection on a pin that can do the job, at the right voltage and current?
Answer: yes, with **one firmware bug found and fixed** (IMU interrupt input level, section 3).
Everything below is re-checked by `tools/verify_pins.py`, which reads `hardware/netlist.xml` and the PDFs in `docs/datasheets/` (51 checks, all pass). Run it again after any pin change:

```
python tools/verify_pins.py          # needs: pip install pymupdf
```

Datasheets used: AVR128DB28/32/48/64 DS40002247B (MCU), LIS2DW12 DS11811 (accelerometer), BQ25570 SLUSBH2 (charger).

## 1. Does each pin exist and can it do the function?
| Net | U1 pin | Port | Datasheet check |
|---|---|---|---|
| COL0-7 | 44-48, 1-3 | PA0-PA7 | plain GPIO; the pin number to port name table was read out of the datasheet's I/O multiplexing table by the script and matches (40 GPIO pins of the 48-pin package) |
| COL8-11 | 4-7 | PB0-PB3 | plain GPIO |
| BUZ_A / BUZ_B | 8 / 9 | PB4 / PB5 | TCA1 default route (PORTMUX.TCAROUTEA = 0, "PORTB") puts WO4 on PB4 and WO5 on PB5 (DS 17.3.7) |
| ROW0-7 | 10-13, 16-19 | PC0-PC7 | plain GPIO; **port C is powered from VDDIO2**: pin 14 is on VBAT, and the MVSYSCFG fuse must be single supply (SYSCFG1 = 0x10, factory 0x08 = dual; DS 19.2, fuse table). Already in `firmware/c/BRINGUP.md` |
| ROW8-11 | 20-23 | PD0-PD3 | plain GPIO |
| IMU_INT, BTN1, BTN2, BAT_OK | 30-33 | PE0-PE3 | plain GPIO, any pin can wake from sleep with a pin interrupt |
| XTAL1 / XTAL2 | 34 / 35 | PF0 / PF1 | these are the XTAL32K1 / XTAL32K2 pins (DS 2.3 pinout) |
| SDA / SCL | 36 / 37 | PF2 / PF3 | TWI1 default pins (PORTMUX.TWIROUTEA TWI1 = 0: host SDA = PF2, SCL = PF3; DS 17.3.6). Fm+ capable |
| RESET, UPDI | 40, 41 | PF6, UPDI | dedicated pins |
| VDD, AVDD, VDDIO2 | 42, 28, 14 | | all on VBAT (AVDD is tied to VDD inside the chip; VDDIO2 must equal VDD in single-supply mode) |
| GND | 15, 29, 43, 49 | | pin 49 is the exposed pad |
| free | 24-27 (PD4-PD7), 38, 39 (PF4, PF5) | | no connect |

## 2. Voltages: who drives what, and who reads it
Rails: the MCU, its LED matrix pins and the BQ25570 storage node (VSTOR = VBAT) run at **3.0 to 4.12 V** (4.12 V = the charge-stop resistors R50/R51). The LIS2DW12 and the I2C pull-ups R20/R21 run from the BQ25570's regulated output **+3V3**.

| Signal | Driver | Reader | Levels | Verdict |
|---|---|---|---|---|
| SDA, SCL | open drain, pulled to +3V3 | MCU TWI1 and LIS2DW12 | bus high = 3.3 V; MCU input high (I2C levels) needs 0.7 x VDD = 2.10 V at 3.0 V, 2.88 V at 4.12 V; the sensor needs 0.7 x 3.3 = 2.31 V | OK over the whole range. The MCU pull-ups must stay off (they would pull the bus to VBAT, above the sensor's Vdd_IO + 0.3 V): `i2c_twi.c` does not enable them |
| IMU_INT | LIS2DW12 INT1, push-pull | MCU PE0 | high = Vdd_IO - 0.2 V = 3.1 V (DS, 4 mA); the default Schmitt-trigger input needs 0.8 x VDD: 2.4 V at 3.0 V but **3.30 V at 4.12 V, more than the sensor can deliver** | **was wrong at high battery voltage; fixed, see section 3** |
| BAT_OK | BQ25570 pin 13, "referenced to VSTOR" | MCU PE3 | high = VSTOR - 200 mV at 10 uA (BQ25570 DS, VBAT_OK(H)) | same rail as the MCU: VSTOR - 0.2 V is above 0.8 x VSTOR for any VSTOR over 1.0 V, so OK without TTL |
| BTN1, BTN2 | switch to ground | MCU PE1, PE2 with internal pull-up | pull-up 90-150 uA at 3.0 V, low = GND | OK |
| RESET, UPDI | programmer | MCU | VBAT levels | OK |

## 3. The bug: IMU_INT input level (fixed)
`docs/mcu-pinmaps.md` already listed "set INLVL = TTL on the sensor interrupt pin", but `firmware/c/hw/buttons.c` never did it. With a fully charged cell (4.12 V) the sensor's 3.1 V high would sit below the 3.30 V the default input needs, so the shake/tap wake-up would stop working exactly when the battery is full. `inputs_init()` now writes `PORT_INLVL_bm` (TTL input, high threshold 2.0 V) for that pin. The AVR build (31.8 KB flash, 2.2 KB RAM), 71 unit checks and 219 hardware checks still pass. `verify_pins.py` greps for the line so it cannot silently disappear.

## 4. Current per pin
Datasheet numbers (DS 39, VDD = 3.0 V): VOL <= 0.6 V at 10 mA sink, VOH >= VDD - 0.7 V at 6 mA source; absolute maximum 50 mA per pin, 120 mA per supply pin.
Model: `docs/research/led_resistor.py` (R = 220 ohm, white LED knee 2.45 / 2.60 / 2.75 V, 30 ohm dynamic, typical pin drops 60 ohm source / 35 ohm sink; the datasheet-worst drops 117 / 60 ohm are in brackets). The LED knee voltages are estimates from LCSC datasheets (first item of `PRE-ORDER-CHECKLIST` C2: measure on the real parts).

| VBAT | low-Vf LED | typical | high-Vf |
|---|---|---|---|
| 3.30 V | 2.5 (2.0) mA | 2.0 (1.6) | 1.6 (1.3) |
| 3.70 V | 3.6 (2.9) | 3.2 (2.6) | 2.8 (2.2) |
| 4.12 V | 4.8 (3.9) | 4.4 (3.6) | 4.0 (3.2) |

- **Column pin (source)** carries one LED: at most 4.8 mA, under the 6 mA the datasheet guarantees. OK.
- **Row pin (sink)** carries every LED lit in that row: 1 LED 4.8 mA, 2 LEDs 9.7 mA (pin drop about 0.34 V, inside the guaranteed 0.6 V at 10 mA), 3 LEDs 14.5 mA (drop 0.5 V, past the 10 mA test point but nowhere near the 50 mA limit), 12 LEDs 58 mA (above the absolute maximum). The firmware therefore lights at most `ROW_SINK_UA / led_current` = 2 LEDs of one row per slot (`watch.c`, `ROW_SINK_UA = 10000`). This depends on the LED current estimate being right: if the real LEDs draw more, `ROW_SINK_UA / i_led` becomes 1 automatically only if the firmware's current table is updated (bring-up test, `BRING-UP-TESTS.md`).
- **Whole chip:** one row active at a time, so peak LED current is about 10 mA plus the MCU itself: far below the 120 mA per supply pin.
- **Piezo** pins PB4/PB5 drive a 9 mm Murata piezo (capacitive load, no DC current): OK at VBAT.

## 5. What this does NOT prove
- LED forward voltages and the real brightness (needs the parts: checklist C2).
- That the 32 kHz crystal starts reliably with the load caps and the longer traces after the crystal move (about 4 mm from pin to crystal now): bench check with `PRE-ORDER-CHECKLIST` B3 / AN2648.
- Anything about the firmware's use of the pins beyond `INLVL`, pull-ups and the static asserts in `main.c` / `buttons.c`.
