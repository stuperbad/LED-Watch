# Bring-up tests without an oscilloscope (written 2026-10-18)

The idea: prove, step by step, that power, charging and the processor work, using **a multimeter** (voltage, plus a milliamp and a microamp range) and a **lamp or the sun**. Every step says what to expect and what a wrong reading would point to. Numbers marked (est.) are my estimates from datasheet figures, not measurements. Companion files: `BRING-UP.md` (first power-up in detail), `../firmware/c/BRINGUP.md` (what the firmware shows), `PRE-ORDER-REVIEW-2026-10-18.md` (what was checked).

## Tools
- A multimeter that can measure DC current down to microamps and up to about 20 mA (most can; use the separate current jack). A second meter or a bench supply with a current limit is nice, not needed.
- A bright lamp (a LED floodlight or halogen 20-30 cm from the cell) or direct sunlight; a phone for the clock; a UPDI programmer (Adafruit UPDI Friend, 3 V setting).
- Where to probe (back of the board): **pogo pad row**: pad 1 RESET, **pad 2 VBAT (system rail)**, pad 3 GND, pad 4 UPDI. **Battery plug J1, pin 1 = battery + (BATT)**. **Solar input (SOLAR_IN)** = the + cell pad. **3.3 V rail** = a pad of C54. Ground = pogo pad 3.

## Step 0. Before any battery (5 minutes)
1. Resistance to ground at the pogo VBAT pad, at the battery + pin and at the C54 pad: not zero (a short). 
2. **Battery polarity:** measure the pouch's two wires with the meter in voltage mode (it should read about 3.7-4.2 V, red probe on +). Plug it into a spare JST connector, or touch the wires, and confirm which wire lands on **J1 pin 1**. Do not trust wire colours. Same for the **solar cell**: under the lamp, the cell's + end must go to the + pad (the datasheet's back drawing and the view through the cell are mirrored, so measure).
3. Do **not** connect the programmer's supply and a battery at the same time (see the review, section 2).

## Step 1. First power-up from a current-limited source
Bench supply 3.7 V with a 20 mA limit on the VBAT pogo pad (or a battery through your meter in the mA range).
- Expect: a blank (unprogrammed) AVR is **not** asleep: it runs through empty flash at its default clock, so a **few mA (est. 1-3 mA)** is normal until it is programmed. Anything above about 10 mA, or a board that warms up, is a problem.
- Measure: rail at pogo pad 2 about the supply voltage; **3.3 V rail 3.31 V** (a buck cannot exceed its input, so with a 3.7 V supply you should see about 3.3 V; if the supply drops below about 3.4 V it will follow it down).
- Wrong? **Rail does not follow the supply:** the BQ25570's battery switch is not closing: is the supply above 2 V, is the polarity right. **3.3 V missing:** the buck is not enabled or the inductor L2 is not soldered. **Large current:** a short; remove power.

## Step 2. Program (once per board)
1. Battery unplugged, programmer on its 3 V setting through the pogo jig (UPDI, VDD, GND).
2. `avrdude ... -v` must name an AVR128DB48; then **set the fuse** `-U syscfg1:w:0x10:m` (single supply) and flash the hex (`BRINGUP.md` section 2).
3. Expect at power-up: the **self-test** for 2 seconds and a 4 kHz beep. The six indicator LEDs: SET = crystal started, TMR = accelerometer answered, BAT = battery OK, FUN = supply above 3.0 V, CFG = supply above 3.6 V.
- Wrong? **Nothing at all:** most likely the fuse (programming did not finish) or a missing rail. **SET dark:** crystal or its two capacitors; the watch still runs on its internal clock. **TMR dark:** the accelerometer did not answer on I2C (soldering or the land pattern). **BAT dark with a good battery:** BAT_OK is low, so the BQ25570's ladder or the battery voltage is below 3.31 V: check the battery with the meter first. **No beep:** buzzer pins or the 3.3 V logic.

## Step 3. Sleep current (the number that decides battery life)
Battery lead through your meter in the **microamp** range, display off (let it time out after 10 s), not touched, in the dark.
- Target about 3-5 uA (the firmware notes); anything under 20 uA is acceptable for rev A.
- Wrong? **100 uA or more:** something is not sleeping: the accelerometer left in a fast mode, the crystal in a high-drive mode, a floating input; or the BQ25570's divider is shorted. Re-flash and measure again, and look at the accelerometer and crystal settings in the firmware, before blaming the hardware.

## Step 4. Does the cell make power?
Cell soldered on, battery **unplugged**, board powered from nothing else.
- Meter on the solar pad vs ground, under the lamp: expect **about 0.6-1.5 V indoors, about 2.0-2.1 V in full sun** (open circuit). The BQ25570 samples the cell for a fraction of a second every 16 s, so a battery-connected reading will flicker between the open-circuit voltage and about 80 % of it.
- Wrong? **Near 0 V in good light:** cell polarity or a bad solder joint on the cell pads. **A reading that is always about 0.5 V:** the cell is loaded by something (short).

## Step 5. Does it charge the battery? (the key test)
Battery connected **through your meter in the milliamp range** (meter between the cell battery's + and J1 pin 1, or between a bench supply and the board), the lamp or sun on the cell, display off.
- Expect (est.): in **full sun about 4-7 mA** flowing *into* the battery (the cell gives about 30 mW at its best point; after the converter about 25 mW into a 3.7 V cell); with a close lamp **1-3 mA**; at a desk in room light only **5-30 uA** (barely more than the sleep current: this is normal, the cell is small).
- Also: **battery voltage rising** over 30-60 minutes of sun by roughly 10-40 mV (the cell is only 70 mAh x 2); BAT_OK stays high.
- Wrong? **No current at all in sun, but step 4 was fine:** the harvester is not starting: check the 3.3 V rail, the VOC_SAMP connection (to the system rail) and L1; the cold-start needs at least 0.6 V from the cell. **Current flows out of the battery in sun:** the harvester is off and the MCU is drawing; same suspects.

## Step 6. Overvoltage sanity
Leave the battery in strong sun (or under the lamp) until the charge current falls to almost nothing. Measure the battery voltage: it must stop at **about 4.1 V (4.12 V)** and never exceed 4.2 V. If it climbs past 4.2 V, **disconnect and stop**: the VBAT_OV ladder (R50/R51) is wrong.

## Step 7. Accelerometer, buttons, display, brightness
The firmware shows each of these (`BRINGUP.md` sections 3-4): wake by wrist raise, the axis map in the bead game, the orbit game to see every LED, button presses, the BAT screen. The `VDD_CAL_PERMILLE` constant is set once by comparing the BAT screen with your meter reading.

## Monitoring it digitally (honest status)
- **Today the watch can tell you** at power-up (the six self-test LEDs and the beep), and in the BAT screen (battery bar); and the BQ25570's BAT_OK flag. That is all that is in rev A's firmware.
- **Not built, can be added later without a new board:** a small voltage logger that writes the supply voltage and BAT_OK to the chip's EEPROM every few minutes, which you then read out through the same programming pads with the programmer software (no oscilloscope): a day outside would show the battery voltage curve and whether it charges. It is firmware only, so it does not have to be done before the order. I would write it after the boards arrive, when we know the chip's real behaviour.
- **Not measurable at all** with the present hardware: the solar cell's power or the charge current from inside the watch (there is no sense resistor or ADC path); use the multimeter as above.
- A cheap USB power meter or a 0.1 ohm sense resistor with the multimeter in the millivolt range works for logging current by hand if you want numbers over a day.

## What would make me stop and think
| Observation | Most likely cause | Test |
|---|---|---|
| Nothing lights, no beep after programming | fuse not set, or no 3.3 V | read the fuse back with avrdude; measure the rails |
| Board warm, supply current high | short or a reversed battery | power off, check polarity, look for solder bridges under the QFN |
| Self-test: only TMR missing | accelerometer soldering / land pattern | reflow check under a microscope; I2C address 0x18 |
| Cell reads 2 V, no charge current in sun | harvester not starting | rail check, L1, VOC_SAMP (pin 3 to the system rail), battery plug polarity |
| Charge current but the battery voltage never rises | consumption equals harvest (display or sleep current too high) | step 3 again with the lamp on |
| Battery voltage above 4.2 V | wrong VBAT_OV ladder value | stop; measure R50 / R51 |
