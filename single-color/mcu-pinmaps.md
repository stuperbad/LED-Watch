# MCU pin maps (read from the manufacturers' datasheets, 2026-10-08)

Datasheets saved in `datasheets/`: **AVR128DB28/32/48/64 DS40002247B** (exact part), **ATmega169P doc8018P rev 08/10** (this is the *ATmega169P*, not the *169PA* that JLCPCB stocks: same pinout family, but the 169PA datasheet itself returned HTTP 403 from Microchip, so the electrical numbers below are from the 169P edition and MUST be re-checked against the 169PA datasheet before ordering), **LIS2DW12 DS11811 rev 9**.

## 1. What the datasheets actually guarantee on one pin (this decides the row-driver question)
| | AVR128DB (all pins) | ATmega169P Port B | ATmega169P ports A,C,D,E,F,G |
|---|---|---|---|
| Sink, guaranteed VOL | 0.6 V max at **10 mA** (VDD 3.0 V) | 0.5 V max at **10 mA** (3 V) | 0.5 V max at **5 mA** (3 V) |
| Source, guaranteed VOH | VDD - 0.7 V min at **6 mA** (3.0 V) | 2.3 V min at **-10 mA** (3 V) | 2.3 V min at **-5 mA** (3 V) |
| Absolute maximum per pin | 50 mA | 40 mA | 40 mA |
| Whole-chip limit | 350 mA GND/VDD | 400 mA | 400 mA |

Those VOL/VOH values are the *maximum drop*, so the old "0.3 V lost in the MCU pins" input in the workbook was optimistic. Worst case at 3-4 mA is about 0.6 V (0.2 V sink + 0.4 V source). The workbook default is now 0.5 V.

## 2. Why the shape of the matrix matters
- One *column* pin (source) feeds exactly one LED at a time, about 3 mA: fine on any pin.
- One *row* pin (sink) carries every LED lit in that row at once. Clock mode: 1 LED. Game mode: up to 12 (single colour), 12 x 3.7 mA = 44 mA, which is **4x the 10 mA the datasheet guarantees** (and above the 169P's 5 mA on most ports). Past the guarantee the pin's own resistance (about 60 ohm at 10 mA) eats the LED's headroom and the LEDs go dim and uneven.
- So the high-count line must be the **sink** line (10 mA beats 6 mA). The schematic now has anodes on the columns (sources) and cathodes on the rows (sinks); before, the 12-LED line was the source. This costs nothing.

## 3. Can software avoid row drivers? (arithmetic, game mode, single colour)
Rule: LEDs lit at the same instant in one row x peak current per LED must be 10 mA or less.
- Peak current per LED is set by the resistor and battery (about 2-4 mA, not selectable at run time), so **at most 2-3 LEDs per row per time slot**.
- The firmware splits each row's lit LEDs into groups of 2 and scans the groups. A 40-LED game picture needs about 22 slots instead of 11, so each LED is on 1/22 of the time at about 3.7 mA peak, roughly 0.17 mA average. The clock mode targets 0.3 mA, so the game is **about 55% as bright** as the clock: visible indoors, never over the pin limit.
- Total average LED current is capped at about 10 mA (one row on at a time x 10 mA), whatever the matrix shape. 40 LEDs x 0.3 mA = 12 mA is already over it; that is the real limit.
- With **row driver transistors** (11 tiny N-channel MOSFETs, a couple of cents each, the MCU pin only drives the gate) the full 12-LED row works and the game reaches the full 0.3 mA per LED. Cost: 11 more parts that can sit anywhere along the row traces (or under them).
- Recommendation: build without drivers, schedule in software (works today), and leave a footprint option on the board for the transistors if the game looks too dim.

## 4. Single colour: AVR128DB48-I/PT (TQFP-48 7x7)
Usable I/O after the dedicated pins: PA0-7, PB0-5, PC0-7, PD0-7, PE0-3, PF2-5 = 38 GPIO. PF0/PF1 are the 32 kHz crystal, PF6 is RESET (input only), UPDI has its own pin. Need: 12 columns + 11 rows + 2 I2C + 3 INT/buttons + charge-status = 29, so **9 spare**.

| Pin | Name | Assigned to |
|---|---|---|
| 1 | PA5 | COLUMN (anode side, SOURCE, series resistor) |
| 2 | PA6 | COLUMN (anode side, SOURCE, series resistor) |
| 3 | PA7 | COLUMN (anode side, SOURCE, series resistor) |
| 4 | PB0 | COLUMN (anode side, SOURCE, series resistor) |
| 5 | PB1 | COLUMN (anode side, SOURCE, series resistor) |
| 6 | PB2 | COLUMN (anode side, SOURCE, series resistor) |
| 7 | PB3 | COLUMN (anode side, SOURCE, series resistor) |
| 8 | PB4 | BUZ_A: piezo drive, TCA1 WO4 (split mode, high byte HCMP1), default PORTB route |
| 9 | PB5 | BUZ_B: piezo drive, TCA1 WO5 (split mode, HCMP2); set PORTB.PIN5CTRL.INVEN for opposite phase |
| 10 | PC0 | COLUMN (anode side, SOURCE, series resistor) |
| 11 | PC1 | COLUMN (anode side, SOURCE, series resistor) |
| 12 | PC2 | ROW (cathode side, SINK) |
| 13 | PC3 | ROW (cathode side, SINK) |
| 14 | VDDIO2 | power: tie to VDD (single-supply fuse), 100 nF |
| 15 | GND | ground |
| 16 | PC4 | ROW (cathode side, SINK) |
| 17 | PC5 | ROW (cathode side, SINK) |
| 18 | PC6 | ROW (cathode side, SINK) |
| 19 | PC7 | ROW (cathode side, SINK) |
| 20 | PD0 | ROW (cathode side, SINK) |
| 21 | PD1 | ROW (cathode side, SINK) |
| 22 | PD2 | ROW (cathode side, SINK) |
| 23 | PD3 | ROW (cathode side, SINK) |
| 24 | PD4 | ROW (cathode side, SINK) |
| 25 | PD5 | spare GPIO |
| 26 | PD6 | spare GPIO |
| 27 | PD7 | spare GPIO |
| 28 | AVDD | power: tie to VDD, 100 nF |
| 29 | GND | ground |
| 30 | PE0 | LIS2DW12 INT1 (set INLVL=TTL) |
| 31 | PE1 | BTN1 |
| 32 | PE2 | BTN2 |
| 33 | PE3 | CHG_STAT (A) / BAT_OK (B) |
| 34 | PF0 | 32.768 kHz crystal XTAL32K1 |
| 35 | PF1 | 32.768 kHz crystal XTAL32K2 |
| 36 | PF2 | spare GPIO |
| 37 | PF3 | spare GPIO |
| 38 | PF4 | spare GPIO |
| 39 | PF5 | spare GPIO |
| 40 | PF6/RESET | RESET (input only; leave open or pull up) |
| 41 | UPDI | UPDI programming |
| 42 | VDD | power: VBAT, 100 nF |
| 43 | GND | ground |
| 44 | PA0 | COLUMN (anode side, SOURCE, series resistor) |
| 45 | PA1 | COLUMN (anode side, SOURCE, series resistor) |
| 46 | PA2 | I2C SDA (TWI0) |
| 47 | PA3 | I2C SCL (TWI0) |
| 48 | PA4 | COLUMN (anode side, SOURCE, series resistor) |

Hazards found in the datasheet:
- **Port C is powered from VDDIO2** (pin 14). It must be tied to VDD and the single-supply fuse (MVSYSCFG) must be set, or every Port C pin is dead. Check the fuse before first power-up.
- The LIS2DW12 interrupt output only reaches about 3.1 V (VDD_IO - 0.2 V) but the MCU runs at up to 4.2 V, where the default Schmitt input needs 0.8 x VDD = 3.4 V. **Set the input level to TTL (2.0 V)** on that pin (PINnCTRL.INLVL).
- The MCU reads the battery itself: the ADC has a VDD/10 channel, so no battery-sense pin or divider is needed.
- Any pin can wake the chip from sleep using LEVEL or BOTHEDGES sense, so buttons and INT need no special pins.
- Sleep: power-down 0.65 uA typ, RTC from the 32 kHz crystal about 2.1 uA (datasheet section 39). Whole standby about 3 uA, as already modelled.

## 5. RGB board: ATmega169PA-AU (TQFP-64 14x14), 22 rows x 18 columns
53 GPIO. Need 22 + 18 + I2C 2 + 2 buttons + INT + charge-status + debug UART 2 = 48, so **5 spare**.

| Pin | Name | Assigned to |
|---|---|---|
| 1 | LCDCAP | LCD unused: can stay open |
| 2 | PE0 | debug UART RXD |
| 3 | PE1 | debug UART TXD |
| 4 | PE2 | spare GPIO |
| 5 | PE3 | spare GPIO |
| 6 | PE4 | I2C SCL (USI) |
| 7 | PE5 | I2C SDA (USI) |
| 8 | PE6 | BTN1 (pin-change PCINT6) |
| 9 | PE7 | BTN2 (pin-change PCINT7) |
| 10 | PB0 | ROW (cathode side, SINK) |
| 11 | PB1 | ROW (cathode side, SINK) |
| 12 | PB2 | ROW (cathode side, SINK) |
| 13 | PB3 | ROW (cathode side, SINK) |
| 14 | PB4 | ROW (cathode side, SINK) |
| 15 | PB5 | ROW (cathode side, SINK) |
| 16 | PB6 | ROW (cathode side, SINK) |
| 17 | PB7 | ROW (cathode side, SINK) |
| 18 | PG3 | spare GPIO |
| 19 | PG4 | spare GPIO |
| 20 | RESET/PG5 | RESET (ISP) |
| 21 | VCC | power |
| 22 | GND | ground |
| 23 | XTAL2/TOSC2 | 32.768 kHz crystal (dedicated pins) |
| 24 | XTAL1/TOSC1 | 32.768 kHz crystal (dedicated pins) |
| 25 | PD0 | spare GPIO |
| 26 | PD1 | sensor INT (INT0, wakes from power-down) |
| 27 | PD2 | ROW (cathode side, SINK) |
| 28 | PD3 | ROW (cathode side, SINK) |
| 29 | PD4 | ROW (cathode side, SINK) |
| 30 | PD5 | ROW (cathode side, SINK) |
| 31 | PD6 | ROW (cathode side, SINK) |
| 32 | PD7 | ROW (cathode side, SINK) |
| 33 | PG0 | COLUMN (anode side, SOURCE) |
| 34 | PG1 | COLUMN (anode side, SOURCE) |
| 35 | PC0 | ROW (cathode side, SINK) |
| 36 | PC1 | ROW (cathode side, SINK) |
| 37 | PC2 | ROW (cathode side, SINK) |
| 38 | PC3 | ROW (cathode side, SINK) |
| 39 | PC4 | ROW (cathode side, SINK) |
| 40 | PC5 | ROW (cathode side, SINK) |
| 41 | PC6 | ROW (cathode side, SINK) |
| 42 | PC7 | ROW (cathode side, SINK) |
| 43 | PG2 | CHG_STAT |
| 44 | PA7 | COLUMN (anode side, SOURCE) |
| 45 | PA6 | COLUMN (anode side, SOURCE) |
| 46 | PA5 | COLUMN (anode side, SOURCE) |
| 47 | PA4 | COLUMN (anode side, SOURCE) |
| 48 | PA3 | COLUMN (anode side, SOURCE) |
| 49 | PA2 | COLUMN (anode side, SOURCE) |
| 50 | PA1 | COLUMN (anode side, SOURCE) |
| 51 | PA0 | COLUMN (anode side, SOURCE) |
| 52 | VCC | power |
| 53 | GND | ground |
| 54 | PF7 | COLUMN (anode side, SOURCE) |
| 55 | PF6 | COLUMN (anode side, SOURCE) |
| 56 | PF5 | COLUMN (anode side, SOURCE) |
| 57 | PF4 | COLUMN (anode side, SOURCE) |
| 58 | PF3 | COLUMN (anode side, SOURCE) |
| 59 | PF2 | COLUMN (anode side, SOURCE) |
| 60 | PF1 | COLUMN (anode side, SOURCE) |
| 61 | PF0 | COLUMN (anode side, SOURCE) |
| 62 | AREF | ADC reference (100 nF to GND) |
| 63 | GND | ground |
| 64 | AVCC | power: to VCC through a filter |

Hazards from the 169P datasheet:
- **The crystal goes on pins 23/24 (XTAL2/TOSC2, XTAL1/TOSC1)**, not on PD6/PD7. This is exactly the error in the first RGB board.
- **JTAG is enabled from the factory** on PF4-PF7 (TCK/TMS/TDO/TDI). The JTAGEN fuse must be turned off before those pins can drive columns. If touching fuses is a concern, move those four columns to PE2, PE3, PG3, PG4.
- ISP programming shares PB1/PB2/PB3 (SCK/MOSI/MISO) with three row pins: the programmer will blink those LEDs briefly.
- Sink current: only **Port B (8 pins) is guaranteed to 10 mA**; the other ports are guaranteed 5 mA at 3 V. An RGB row can light up to 3 elements per LED, so row drivers are far more likely to be needed on the RGB board (or use lower currents, about 1.5 mA per colour element).
- Pin-change interrupts exist only on PB and PE, plus INT0 on PD1: buttons are on PE6/PE7 and the sensor INT on PD1 for that reason.
- Sleep: power-save with the 32 kHz crystal running 0.8 uA typ (2.6 uA max) at 3 V, about 2.5 uA better than the AVR128DB. It runs at most 8 MHz at 2.7-5.5 V (the DB goes to 24 MHz).
- AVCC (pin 64) must be wired to VCC; AREF (62) needs a capacitor; LCDCAP (1) can stay open when the LCD driver is not used.
- Stock: 170 + 226 at JLCPCB. The 14x14 mm TQFP-64 body is big next to a 30-50 mm board.

## 6. Parts that were NOT chosen (and why)
ATmega1284P (1,943 at JLCPCB, 44-pin 10x10): fits clock mode only with almost no spare pins, uses ISP, big body. AVR64DD32 (32 pins): too few pins. AVR128DB64 (53 I/O, QFN-64, 11 in stock): the best RGB option if UPDI and the AVR-Dx family matter more than the 169PA's lower sleep current.

## 7. Still to verify before any order
1. The ATmega169PA datasheet itself (JLCPCB stocks the PA; numbers above are from the 169P edition).
2. LIS2DW12 land pattern (ST TN0018) against KiCad's `LGA-12_2x2mm_P0.5mm`: the numbering is the same family but the pad sizes were not compared.
3. The MVSYSCFG fuse default on a new AVR128DB (set it explicitly when programming).
4. All current figures at the real operating voltage (datasheets quote 3 V and 1.8 V test points).
