# Pre-order review of revision A (2026-10-18)

A last read-through of the schematic, the power design, the firmware and the parts, done before ordering. **Measured/checked** means a script or the datasheet text gave the answer today; **not verifiable here** means it needs a real board.

## 1. Schematic: the BQ25570 pin by pin (from `hardware/netlist.xml`)

| Pin | Name | Connected to | What the datasheet wants | Verdict |
|---|---|---|---|---|
| 2 | VIN_DC | solar cell +, C50 4.7 uF, L1 | CIN at least 4.7 uF; input 0.1-5.1 V | OK (at the minimum, see 5) |
| 3 | VOC_SAMP | VSTOR (the system rail) | "Connect to VSTOR to sample at 80 % of open-circuit voltage" | OK, and it fits the cell (Vmpp/Voc = 0.81) |
| 4 | VREF_SAMP | 10 nF to ground | 9-11 nF | OK |
| 5 | EN | ground | low = enabled | OK |
| 6 | VOUT_EN | VSTOR | high = buck enabled | OK |
| 7 | VBAT_OV | R50 / R51 | resistor sum 11-15 Mohm | 11.6 Mohm, OK: charge stops at **4.12 V** |
| 10, 11 | OK_HYST, OK_PROG | R52 / R53 / R54 | sum 11-15 Mohm | 11.7 Mohm, OK: BAT_OK falls at **3.31 V**, rises at **3.78 V** |
| 12 | VOUT_SET | R55 / R56 | sum 11-15 Mohm | **was 10.23 Mohm (7 % under the range), changed, see 4**: now 11.54 Mohm, output **3.309 V** |
| 13 | VBAT_OK | MCU pin PE3 | open output, high level = VSTOR through about 20 kohm | OK |
| 14 | VOUT | +3V3: C54 22 uF, C30/C31 100 nF, IMU, I2C pull-ups | COUT 10-22 uF | OK |
| 16, 20 | LBUCK, LBOOST | L2 10 uH, L1 22 uH | L2 4.7-10 uH, L1 22 uH | OK |
| 18 | VBAT | the battery plugs J1/J1B | battery of at least 100 uF equivalent | OK with a battery; **not supported without one** |
| 19 | VSTOR | the system rail with C52 4.7 uF and C13 10 uF | CSTOR at least 4.7 uF | OK |

All three resistor ladders were recomputed from the netlist values with the datasheet equations 2-5 (VBIAS = 1.21 V): VBAT_OV = 1.5 x 1.21 x (1 + 6.49 / 5.11) = 4.12 V; BAT_OK falling 1.21 x (1 + 6.49 / 3.74) = 3.31 V, rising 1.21 x (1 + (6.49 + 1.47) / 3.74) = 3.78 V; VOUT 1.21 x (1 + 7.32 / 4.22) = 3.309 V.

The other connections checked: accelerometer address pin to ground (address 0x18), chip select high (I2C mode), I2C pull-ups to **+3V3** (not the battery), its interrupt output to the MCU, MCU VDD, AVDD and VDDIO2 all on the battery rail, crystal on PF0/PF1, UPDI and RESET to the pogo pads. ERC: 2 warnings, both harmless (the accelerometer address pin tied to ground on purpose; a symbol library path).

## 2. Overvoltage: where could a part see too much?

| Part / pin | Highest voltage it can see in this design | Limit | Verdict |
|---|---|---|---|
| BQ25570 VIN_DC | solar cell open-circuit, about 2.1 V at full sun (about 2.3 V cold) | 5.1 V operating, 5.5 V absolute | large margin |
| BQ25570 VSTOR / VBAT / VOUT | the charger regulates to **4.12 V** | 5.5 V absolute | OK |
| LiPo cell | charge stops at 4.12 V; the cell's own protection board cuts at 4.28 V | cell rating 4.2 V | OK, two layers |
| AVR128DB (VDD, VDDIO2, AVDD) | battery voltage, at most 4.2 V | 5.5 V | OK |
| LIS2DW12 (VDD, VDD_IO) | the 3.31 V buck output | 3.6 V | OK |
| LIS2DW12 I2C lines | pulled up to 3.3 V, the MCU only pulls low | VDD_IO + 0.3 V | OK as long as the firmware keeps SDA/SCL open-drain (it does: TWI mode) |
| Accelerometer interrupt into the MCU | 3.1 V output into a pin whose supply can be 4.2 V | needs TTL input level | firmware setting noted in BRING-UP; not a damage risk |
| LEDs, buzzer | the battery rail | fine | OK |

The datasheet's caution about a full battery (input pulled to ground at the overvoltage point; source impedance must be above 20 ohm) is fine for a solar cell.

**The real overvoltage hazards are not on the board but around it:**
1. **A programmer that supplies power while a battery is connected.** The programming pad 2 is the battery rail; a 5 V (or even 3.3 V) programmer output would push current through the BQ25570's battery switch into the cell, with nothing limiting it except the cell's own protection board. **Program with the battery unplugged**, or leave the programmer's supply pin disconnected and power the board from the battery.
2. **A reversed battery plug.** There is no reverse protection. The plug's pin 1 = GND / pin 2 = + now matches TinyCircuits' own wiring (see section 7: the board originally had it the other way round). Check by eye and by meter before the first power-up (BRING-UP-TESTS step 0).
3. **Using your larger sibling panel for tests.** The 23 x 25 mm KXOB081K06TF has 4.15 V open-circuit at full sun (about 4.4 V in the cold). That is under the 5.1 V input limit, but with only 0.7 V of margin: fine for a test on a mild day, not for a cold bright day.

## 3. Firmware (run today)
- **Host tests all pass:** 71 unit checks, 197 hardware-layer checks, and the C core matches the browser simulator frame for frame on all 20 scenarios (`firmware/c/test`: `run_unit.py`, `run_hw.py`, `run_diff.py`).
- Last AVR build: 31.7 KB of 128 KB flash, 2.2 KB of RAM.
- **Nothing has run on a real chip.** Known gaps (BRINGUP.md section 5): settings are not saved (no EEPROM yet), the "solar level" and "charging" screens read 0 (no measurement path in the hardware), the particle games may be slow at 4 MHz, and the multi-voltage fuse must be set to single supply on first programming (`avrdude ... -U syscfg1:w:0x10:m`). Missing that fuse is the most likely "it does nothing" cause on day one.
- Firmware is not part of the order: it can be re-flashed any time through the pogo pads. Only the hardware has to be right on day one.

## 4. Change made today: R55 / R56 (VOUT divider)
The VOUT divider was 6.49 Mohm + 3.74 Mohm = 10.23 Mohm, 7 % below the datasheet's recommended 11-15 Mohm (probably harmless, but out of spec, and chosen earlier only to reduce the number of different resistor values). Replaced by **R55 = 7.32 Mohm (LCSC C423137, 10,004 in stock) and R56 = 4.22 Mohm (C423173, 9,980 in stock)**: the output stays at 3.309 V and the sum is 11.54 Mohm. Verified: the new netlist differs from the old one in exactly these two values and in none of the 470 pin-to-net connections; the board's copper is unchanged (only the value text of two footprints), so the Gerbers do not change; `BOM.csv` now has two more lines (26). Cost: two more unique part types, about $6 of extended-part fees per order.

## 5. Left as it is, on purpose
- **C50 (4.7 uF on the solar input)** sits at the datasheet's minimum, and a 0402 ceramic loses part of its value under bias, so the real value is lower. Common practice and fine for a first build; a 10 uF part would give more margin (the same 0402 part as C13), but its lower voltage rating is worse if a 4 V panel is ever used. I did not change it.
- **Ten 10 k resistors and the matching capacitors with unconnected pins** (R57-R67, C60-C62) are the decorative dummies documented in SCHEMATIC-GUIDE.md. They do nothing.

## 6. Not verifiable here (needs the real boards or cells)
- Whether the harvester starts from the cell and charges the battery (BRING-UP-TESTS steps 4-6).
- The accelerometer land pattern: the ST datasheet gives only the 2 x 2 x 0.7 mm outline and refers to its note TN0018 for the pads, which I could not get. The footprint is KiCad's stock LGA-12 2 x 2 mm, 0.5 mm pitch. Low risk, unverified.
- The solar cell's pad polarity (the datasheet's drawings are mirrored: measure it); battery polarity is settled by section 7 but still checked by meter; solar cell stock (DigiKey Canada showed 0 in stock, 12 weeks, an aggregator 1,866: check live); strap slot and sound path; crystal accuracy.
- A second pair of eyes (checklist D9). The power block, crystal and battery polarity are what I would ask the engineer to look at.

## 7. Battery plug polarity: found reversed, fixed (added 2026-10-18, later the same day)
**Finding.** The board had J1 / J1B pin 1 on the battery + net and pin 2 on ground. TinyCircuits' own documents say the opposite: their datasheet (figure 4, "wiring") and their ASL1201 Eagle files for the same SM02B-SRSS-TB header put **pin 1 = GND and pin 2 = battery +** (the 2D drawing's triangle mark is beside the black wire). A TinyCircuits pouch plugged into the old board would have been connected backwards: the BQ25570's VBAT pin at about -3.7 V and the system rail ground at +3.7 V. Nothing on the board protects against that. The product web page does not show the polarity, which is why it looked like an open question; the datasheet and the CAD files settle it.

**Fix (done, on the live board).** Pin 2 is now `/BATT` and pin 1 is `GND` on both plugs. `tools/fix_battery_polarity.py` reworks only the copper around the two plugs on the back: the old stubs are removed, new ones drawn to the same trunks, one ground via moved from beside pin 2 to beside pin 1 (the old position was 0.075 mm from the new + pad). It also adds "+" and "-" marks on the back silkscreen beside each plug. DRC: 0 errors, 0 unconnected (the same 7 silkscreen text-height warnings as before). The netlist differs from the previous one in exactly four pin assignments (J1 and J1B pins 1 and 2) and nothing else. Firmware pin map, BOM and placement files are unaffected (part rotations did not change). Gerbers and the zip were re-exported; **the JLCDFM check and the full assembled quote must be re-run on the new zip before ordering.**

**Why no protection circuit.** The usual protection is a P-channel MOSFET in series with the battery (drain to the plug, source to the BQ25570, gate to ground): it blocks a reversed battery. It does not help here: with two cells in parallel, **one** plug reversed and one correct still puts a reverse cell across a good cell through the two plugs, before the FET; protecting that case needs a back-to-back FET pair on each plug (four parts), and the board has no room left on the back around the plugs. The FET also adds a drop and leakage in the 3-5 uA sleep budget. With the polarity now matching the supplier's own wiring, the remaining risk is a hand-made or aftermarket plug wired the other way, which a visual check and a meter find in a minute (BRING-UP-TESTS, step 0). Not worth redesigning the board; left as a procedure.

**How to be sure before power.** (1) Plug the pouch's JST plug in and look: the "+" silk mark is beside pin 2, TinyCircuits' red wire is battery +. (2) Meter: with the battery connected, the pad marked "+" reads +3.7-4.2 V against the pad marked "-". (3) Only then connect the programmer or do anything else. The first connection can also be made through the meter in the milliamp range (it shows a few mA for a blank chip and a few microamps once programmed; a reading of the wrong sign means stop).
