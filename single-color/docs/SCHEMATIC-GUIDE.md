# Single-colour solar LED watch: schematic guide (what every part is for)

Source of truth: `schematic/gen_schematic.py` -> `schematic/watch_solar.kicad_sch` (solar variant, the one we are building) and `watch_usb.kicad_sch` (USB-charged variant, not built). 183 components. Datasheets: `datasheets/`, `schematic/bq25570.pdf`.

## 1. Power chain (left to right)

```
two-step energy path

 solar cell (J3)  ->  BQ25570 (U4)  ->  VSTOR rail ("VBAT" net, 3.0-4.2 V)  ->  MCU (U1) + LEDs
                          |                 ^
                          |                 +-- battery J1 / J1B ("BATT" net, via BQ25570 pin 18)
                          +-> buck -> +3V3 rail -> IMU (U2) + I2C pull-ups
```

| Ref | Part | What it does |
|---|---|---|
| **J3 / SC1+ SC1-** | Anysolar **KXOB25-05X3TF** solar cell (23 x 8 x 1.2 mm), end pads on the board | Three silicon cells in series inside one package: Voc 2.07 V, 30.7 mW at full sun. Hand-soldered (low-temperature solder). |
| **U4** | TI **BQ25570** (VQFN-20) | Energy harvester: boost-charges the battery from the tiny solar voltage, tracks the cell's maximum power point (80 % of Voc, pin VOC_SAMP tied to VSTOR), protects the battery (over-voltage), and has a built-in buck that makes the 3.3 V rail. It needs no MCU to work. |
| **L1** 22 uH | boost inductor | Energy storage of the boost converter (LBOOST pin to SOLAR_IN). |
| **L2** 10 uH | buck inductor | Energy storage of the 3.3 V buck (LBUCK pin to +3V3). |
| **C50** 4.7 uF | solar input cap | Smooths the solar input (VIN_DC). |
| **C51** 10 nF | VREF_SAMP cap | Holds the sampled open-circuit voltage for the MPPT; must be a low-leakage part. |
| **C52** 4.7 uF + **C53** 10 nF | storage caps | The "CSTOR" caps on VSTOR, the system rail. |
| **C54** 22 uF (0805) | 3.3 V output cap | Output filter of the buck. |
| **R50 6.49 M / R51 5.11 M** | divider | Sets the battery **over-voltage** limit (about 4.12 V): charging stops there. |
| **R52 1.47 M / R53 6.49 M / R54 3.74 M** | divider | Sets the **BAT_OK** thresholds: falls at 3.31 V, rises at 3.78 V. BAT_OK goes to the MCU as a "battery good" flag. |
| **R55 6.49 M / R56 3.74 M** | divider | Sets the **3.3 V** output voltage of the buck. |
| **J1 / J1B** | JST-SH 2-pin plugs | Two small LiPo pouches (TinyCircuits 70 mAh) in parallel, one near each strap end. Pin 1 = - (GND), pin 2 = + (BATT), as on TinyCircuits' own boards; check the pouch lead polarity before plugging. The pouches must have a built-in protection circuit. |

Why a harvester IC and not just a charger: the cell makes only about 1.1 V to 2 V at 10-20 mA, far below a LiPo's 3-4.2 V; a boost converter that finds the maximum power point is the only way to get useful charge from indoor light.

## 2. Brain and sensing

| Ref | Part | What it does |
|---|---|---|
| **U1** | Microchip **AVR128DB48** (VQFN-48, 6 x 6 mm) | The MCU: 128 KB flash, runs from VSTOR (3.0-4.2 V). Drives the LED matrix directly from its pins, reads buttons, talks to the IMU, keeps time with the 32 kHz crystal, sleeps at a few uA. Pin use: 12 column pins (COL*_MCU) + 12 row pins (ROW0-11; row 11 is the six mode LEDs) + 2 buttons + IMU interrupt + I2C (SDA/SCL) + BAT_OK + crystal + UPDI. 12 spare pins (PB4, PB5, PD6, PD7, PF2-PF5, reset). |
| **Y1** 32.768 kHz + **C20, C21** 18 pF | watch crystal and its load caps | Gives the RTC accurate time (about 2 uA). 18 pF is derived from the datasheet's per-pin pin capacitance (5 pF) and a 12.5 pF crystal. Layout rule: caps right at the crystal, nothing under it, grounded guard around it. |
| **C10, C11, C12** 100 nF + **C13** 10 uF | MCU decoupling | One 100 nF per supply pin (VDD, AVDD, VDDIO2) and one bulk cap on the VBAT rail. |
| **U2** | ST **LIS2DW12** accelerometer (LGA-12) | Motion sensing: wake-on-motion, tap, wrist-raise detection; its INT1 pin wakes the MCU (IMU_INT). Runs from the 3.3 V rail. |
| **C30, C31** 100 nF | IMU decoupling | One on VDD, one on VDD_IO; datasheet: "as near as possible" to pin 9. |
| **R20, R21** 10 k | I2C pull-ups | Pull SDA and SCL up to +3V3 (the IMU's rail). |
| **SW1, SW2** | tactile buttons | The two user buttons (left/right), active low with the MCU's internal pull-ups. |
| **J2** | Tag-Connect TC2030-IDC-NL footprint | No part: six pads + 3 alignment holes for a spring-pin programming cable. Pad 1 = UPDI, pad 2 = VBAT (target power sense), pad 6 = GND (Microchip's 6-pin UPDI mapping). |

## 3. The display (132 + 6 LEDs)

| Ref | Part | What it does |
|---|---|---|
| **H1-H12** | white 0603 LEDs | The hour ring (inner, largest, brightest). |
| **M0-M59** | white 0402 LEDs | The minute ring. |
| **S0-S59** | white 0201 LEDs | The second ring (outer, smallest). |
| **IND1-IND6** | white 0402 LEDs, labelled **SET TMR BAT FUN CFG LCK** | Mode indicators in a row under the solar cell; exactly one lit shows the current mode (LCK = buttons locked). |
| **R1-R12** 220 ohm | column current limiters | One per 30-degree sector, in series with the whole column. 220 ohm gives 1.6-4.8 mA peak per LED over 3.3-4.12 V (`led_resistor.py`). Placed parallel to their hour LED. |
| **R57, R58, R59, C60, C61, C62** | **cosmetic dummies** (10 k / 100 nF, pins unconnected) | Only there so every hour LED has a part on each side and the 12/3/6/9 capacitor pairs are complete. They do nothing; they cost fractions of a cent. |

How the matrix works: 12 columns x 11 rows (+ the indicator row). Each LED's anode is on a column (sector) line through R1-R12, its cathode on a row line (ring position). The MCU lights one row at a time by pulling that row pin low, fast enough that the eye sees several LEDs at once. Only about 3 LEDs are on at any instant, so no driver chips are needed (row pin limit: 10 mA sink, about 3 LEDs at 3-4 mA).

## 4. Net names you will see

`VBAT` = the system rail (storage node VSTOR, battery voltage); `BATT` = the battery pin of the BQ25570; `+3V3` = the regulated 3.3 V; `SOLAR_IN` = solar input; `COLn` = LED column n (sector) at the LEDs, `COLn_MCU` = the same column on the MCU side of its resistor; `ROWn` = LED row n; `LBOOST`, `LBUCK` = inductor nodes; `VRDIV`, `VBAT_OV`, `OK_HYST`, `OK_PROG`, `VOUT_SET`, `VREF_SAMP` = BQ25570 configuration pins; `UPDI` = programming; `XTAL1/2` = crystal; `IMU_INT`, `SDA`, `SCL`, `BTN1/2`, `BAT_OK` = MCU signals.

## 5. Still open (none of it changes the netlist)

- LED series resistor: 220 ohm now; re-check when the actual LED parts are chosen (Vf spread is large for white LEDs on a 3.3-4.2 V rail).
- Crystal load caps 18 pF: confirm on the bench (Microchip AN2648).
- BQ25570 must cold-start from a flat pouch: two things to verify on a bench board (solar Voc above 0.6 V indoors, pouch protection behaviour).
- Fuse settings (single supply, MVIO) are programmed with the firmware, not parts.
