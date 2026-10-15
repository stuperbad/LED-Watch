# Bring-up sheet: first power-up of revision A

What to do, in order, when the boards arrive. Everything below follows from the schematic, the BQ25570 datasheet and the firmware; **none of it has been tried on a real board yet**, so treat the expected values as "what the design says", and write down what you actually measure. Firmware-side details (self-test LEDs, buzzer scope check) are in `../firmware/c/BRINGUP.md`.

## How the power works (one paragraph)
There is no power switch. The battery plugs into J1 and/or J1B (both go to the same node, `BATT`, in parallel: **one or two cells both work**, two give twice the capacity). The TI BQ25570 harvester sits between the battery and the rest: its battery pin is `BATT`, its storage/output pin (VSTOR) is the system rail that the processor runs from (net `VBAT`, the pogo pad 2), and its buck makes a 3.3 V rail (`+3V3`) for the accelerometer. Once the battery is above about 2 V the chip closes an internal switch between `BATT` and `VBAT` (the datasheet says within about 50 ms), the processor wakes by itself and the 3.3 V rail comes up. The solar cell only tops the battery up.

| Number | Value | Source |
|---|---|---|
| Battery connected to the system | rises above about 1.98 V (undervoltage threshold 1.95 V + 32 mV hysteresis), disconnects again below 1.95 V | BQ25570 datasheet 7.3.2 |
| Charge stops (overvoltage setting) | 4.12 V | resistor ladder R50/R51 |
| BAT_OK pin (low-battery flag to the processor) | falls at 3.31 V, rises again at 3.78 V | ladder R52-R54 |
| 3.3 V rail | 3.31 V | ladder R55/R56 |
| Solar cold start (battery empty) | the cell must give at least 0.6 V (typical, 0.7 V max) | datasheet |
| Quiescent current of the BQ25570 | about 0.5 uA | datasheet |
| Sleep current target of the whole watch | a few uA | `power-budget.md` (estimate) |

## Before anything is connected (no battery, no programmer)
Use the meter in resistance mode. Probe points: battery plug J1 (pin 1 = battery +, pin 2 = GND; the connectors are right-angle JST SH on the back), pogo pad row J2 (pad 1 RESET, 2 `VBAT` rail, 3 GND, 4 UPDI), and either pad of C54 for `+3V3`.
1. `BATT` (J1 pin 1) to GND: should not be a short (expect open or the charge of a cap, rising).
2. `VBAT` rail (pogo pad 2) to GND: not a short.
3. `+3V3` (C54) to GND: not a short.
4. Optional: look at the BQ25570 (U4) and the accelerometer (U2) under a microscope for bridged pins (JLCPCB places them; the BQ25570 has a thermal pad underneath).

## Battery polarity: the one thing that can kill the board
**The board has no reverse-polarity protection**, and the connectors do not stop a reversed battery. Do this before the first battery goes in:
- Look up the pin order of your battery's JST SH plug (red lead = battery +). Confirm that it lands on **J1 pin 1**.
- Measure the pigtail with a meter first (plug it into a breakout or a spare connector) rather than trusting wire colours.
- The TinyCircuits / generic pouch cells are protected cells; a protected cell that has tripped its protection looks like 0 V and may need charging before it will wake (see "Flat battery" below).

## First power-up, one battery
1. Put a meter in series with the battery (current range), or use a current-limited supply set to 3.7 V and about 50 mA through the JST pigtail instead of a cell.
2. Plug the **one** battery into J1. A blank processor does nothing visible; expect the current to settle to a few microamps to tens of microamps once the 22 uF and other capacitors have charged.
3. Measure with the cell still connected:
   - pogo pad 2 (`VBAT` rail) = the battery voltage (the switch is closed);
   - C54 pad (`+3V3`) = about 3.3 V (with a battery above about 3.4 V; a buck cannot output more than its input, so expect it to sag as the battery drops below that);
   - the `VBAT_OV`, `VRDIV` nodes etc. are high-impedance (megohm ladders): do not probe them with a low-impedance meter or scope probe, it changes the thresholds.
4. If the rail does not follow the battery: check that the battery is above 2 V and polarity again.

## Programming (UPDI)
- Tool: Adafruit UPDI Friend (product 5893, 3 V setting) or any serial-UPDI adapter, with a home-made jig of 1.27 mm pogo pins on **UPDI, VDD, GND** (RESET not needed). The two guide holes next to the pads are for alignment pins.
- First programming: set the fuses for a single supply (the MVIO fuse, VDDIO2 tied to VDD: checklist item B7), select the 32 kHz crystal as the RTC source (done in firmware), then flash `firmware/c/hw/watch_fw.hex` with avrdude 7 (SerialUPDI). If the programmer powers the board, do it **without** the battery in, or set the programmer's voltage to match and check that nothing fights over the rail (checklist: power question open).
- Serial UPDI on the AVR128DB48 has not been tried with this adapter; try a low baud rate first.

## Power-up self-test (firmware)
On every power-up the watch shows, for 2 seconds on the mode LEDs, with a 150 ms 4 kHz beep: **SET** = crystal started, **TMR** = accelerometer answered, **BAT** = BAT_OK pin high (battery fine), **FUN** = supply above 3.0 V, **CFG** = supply above 3.6 V. ALM and LCK are not used. Then the display goes dark and the chip sleeps; any button press wakes it. Time and date start at a default and must be set (SET mode); nothing is saved across a power loss yet.
Missing SET: crystal problem (the watch then keeps time from the inaccurate internal oscillator). Missing TMR: I2C or accelerometer. No beep: see the buzzer notes in `../firmware/c/BRINGUP.md`.

## With one battery or two
- One cell alone is fine and is a complete system (half the capacity).
- **Before plugging a second cell in, check that both are within about 0.1 V of each other** (measure each at its plug). A larger difference makes a current surge flow between them when they are joined. Plug the second one in with the first one connected, and re-check the supply current after.
- If you ever want one plug disconnected permanently, nothing else changes.

## Flat or tripped battery
- Below about 1.98 V the BQ25570 keeps the battery off the system rail. It then needs light on the solar cell: at least 0.6 V from the cell starts the cold-start charger (the cell's open-circuit voltage is about 2.07 V in full sun, so use a bright lamp close to it).
- A protected pouch that tripped has to be woken by charge first; try a bench supply (4.0 V, 20 mA current limit) on the plug for a minute, then connect it normally.
- The TinyCircuits ASR00011 pouch has its own protection board (datasheet: overdischarge cuts off at 2.5 V +-0.05 V and releases at 2.9 V +-0.1 V, overcharge cuts at 4.28 V; it says a 0 V cell can be recharged). That cutoff is far above the BQ25570's own 1.95 V disconnect, so the cell's board is what really stops the discharge; a tripped cell looks like 0 V until it is charged (solar cold start or a bench supply). Whether the BQ25570's cold-start charger can revive a tripped cell through the protection board is not tested.
- Running from the solar cell with **no** battery at all is not supported: the BQ25570 wants a storage element of at least 100 uF on its battery pin.

## What to measure and write down
Supply current (asleep), with the display on in Time (about the LED current plus 1-2 mA), battery voltage, `+3V3`, BAT_OK level, whether the crystal and accelerometer self-test LEDs come on, whether the beep is audible and at what frequency it is loudest, solar charging current under a lamp, and how long one cell lasts. Put the numbers in `DECISION-LOG.md` and update `PRE-ORDER-CHECKLIST.md` section C.
