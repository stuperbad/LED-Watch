# Firmware / software handoff (for a separate Claude session)

Goal: firmware for the single-colour solar LED watch (AVR128DB48, VQFN-48), plus the face simulator. Hardware (routing, PCB) is handled in a different session; do not edit anything outside `firmware/` without asking.

## Status (2026-10-12)
Steps 1 and 4 (toolchain, mode state machine) are done in a different way than first planned: the AVR toolchain is installed (`README.md`), the browser simulator `sim/` is the behaviour reference, and the whole core has been ported to portable C in `c/watch.c` (matches the simulator frame-for-frame on 17 scripted scenarios; 24 KB flash, 1 KB RAM). The mode list in this file is outdated: read `../DESIGN-UX.md` and `sim/MANUAL.md`. The hardware layer (matrix scan, buttons, RTC and sleep, battery voltage, LIS2DW12 driver) is now written and compiles (`c/hw/`, 29 KB flash, 2 KB RAM) but has never run on a board. Remaining: bring-up and tuning on the real board (`c/BRINGUP.md`), EEPROM settings, particle-game speed at 4 MHz.

## Read first
- `docs/SCHEMATIC-GUIDE.md` : what every part is, how the LED matrix works, net names.
- `docs/DESIGN-UX.md` : modes and button behaviour (SET, TMR, BAT, FUN, CFG, LCK).
- `firmware/pins.h` : GENERATED pin map (`gen_pins.py` reads `hardware/netlist.xml`). Never edit by hand; rerun the generator if the schematic changes.
- `firmware/ledmap.h` : which row/column each of the 138 LEDs is on (hours H, minutes M, seconds S, indicators IND).
- `firmware/sim/watch_sim.py` : renders the face from `plan.json` + the netlist (writes a PNG). Extend it into an interactive simulator that runs the same scan code.

## Hardware facts the firmware depends on
- 12 columns (COLn_MCU, through 220 ohm to the LED anodes) x 12 rows (ROW0-11, LED cathodes; ROW11 = the six mode indicators). One row sunk at a time; only about 3 LEDs lit at once; row pin sink limit 10 mA.
- Supply is VBAT 3.0 to 4.2 V (battery), no regulator on the MCU. Brightness must therefore follow VDD (LED current changes 1.6 to 4.8 mA over that range): measure VDD (ADC on the internal reference) and scale PWM duty.
- 32.768 kHz crystal on PF0/PF1 (XTAL32K) drives the RTC; use PIT/RTC for the 1 s tick and sleep in standby between ticks.
- Buttons BTN1 (PE1), BTN2 (PE2): active low, internal pull-ups, wake from sleep on pin change.
- LIS2DW12 on I2C (SDA PA2, SCL PA3, address 0x18 or 0x19, check SA0 in the schematic), interrupt on PE0 (IMU_INT): wrist-raise / tap wakes the display.
- BAT_OK (PE3) from the BQ25570: low = battery low, show BAT indicator and dim or stop the display.
- Programming: UPDI pin 41 through the Tag-Connect TC2030 (needs a UPDI programmer, e.g. Microchip SNAP or a serial-UPDI adapter). No dev board is required; develop against the simulator first.
- No C compiler is installed on this PC yet. Options: Microchip AVR-GCC toolchain (avr-gcc 7.3 + DFP for AVR-Dx) or the `avr-gcc` from the Arduino/DxCore package; pick one and document the exact install in `firmware/README.md`.

## Suggested order
1. Toolchain install + blink one LED (verify against `pins.h`).
2. Matrix scan driver with a host-side build target so the same code runs in the simulator.
3. RTC timekeeping and the face renderer (hour / minute / second rings).
4. Mode state machine (SET, TMR, BAT, FUN, CFG, LCK) per DESIGN-UX.md.
5. IMU driver (wake on raise), brightness vs VDD, sleep current budget (target a few uA asleep).
6. Fuse and clock settings (single supply; internal oscillator; 32 kHz crystal) documented for programming day.

## Board changes 2026-10-13 that the firmware must follow (hardware session, board Y42)
- **Buzzer:** Murata PKMCS0909E4000-R1 piezo on **PB4 = BUZ_A** and **PB5 = BUZ_B** (see `mcu-pinmaps.md`). Both pins are TCA1 outputs on the default PORTB route (TCA1 exists on the 48-pin part): TCA1 in **split mode**, high-byte timer, HCMP1 -> WO4 (PB4), HCMP2 -> WO5 (PB5), enable HCMP1EN/HCMP2EN only (PB0-PB3 are LED columns, leave their compare outputs off); equal compare values, and `PORTB.PIN5CTRL |= PORT_INVEN_bm` so the two pins swing in opposite phase (about 6.6 V across the piezo). Split mode is 8-bit single-slope down-count: pick the prescaler per note (about 1.5-10 kHz is usable; Murata's curve is loudest near 8 kHz, about 72 dB at 4 kHz with a 3 V pk-pk drive).
- **Seven mode LEDs:** SET TMR **ALM** BAT FUN CFG LCK (new IND7 = ROW11 / COL6, silkscreen order left to right as listed).
- **Weekday display:** the mode LEDs double as weekday lights (S M T W T F S, Sunday first): SET-S TMR-M ALM-T BAT-W FUN-T CFG-F LCK-S are printed on the board. The day is shown by lighting that one LED (replaces the old 1-7 LED bar on the outer ring).
- **Programming:** pogo pads RESET, VDD(VBAT), GND, UPDI (1.27 mm), RESET on PF6 for high-voltage recovery only.

## Update 2026-10-14: ALM mode, weekday lights, buzzer (firmware session)
Done in BOTH cores (`c/watch.c` and `sim/watch_core.js`, 20 scenarios match frame-for-frame including the buzzer frequency; 71 unit checks, 197 hardware-layer checks; AVR build 31.7 KB flash / 2.2 KB RAM):
- **Seven indicators, face order** SET TMR ALM BAT FUN CFG LCK: `MODE_LED[7]` in `ledmap.h` is now generated in physical (left to right) order from the board file (`gen_pins.py` reads `hardware/led-watch.kicad_pcb`; IND7 = ALM = COL6 sits third). Mode ids follow the same order (TIME SET TMR ALM BAT FUN CFG), so mode selection walks the row.
- **ALM mode** (alarm clock: hour, minute, on/off; rings up to 1 min, any button stops it, wakes even a locked watch) and a dim ALM LED in Time while an alarm is set.
- **Weekday on the indicator LEDs** (SET = Sunday ... LCK = Saturday) instead of the outer-ring bar.
- **Sound engine**: the core reports `watch_tone_hz()`; patterns for key click, game events (Runner, Target, Quick Draw, Simon tones, Pong, Pacer ticks), award and the alarm. **CFG 11 key beeps (off by default), CFG 12 game sounds (on by default)**, 12 settings now (`set[12]`). Low battery mutes all but the alarm.
- **`c/hw/buzzer.c`**: TCA1 split mode, PB4 = WO4 (HCMP1), PB5 = WO5 (HCMP2) with PORTB.PIN5CTRL.INVEN (only while sounding), 50 % duty, prescaler chosen by `buzzer_plan()` (tested). `main.c` calls `buzzer_set(watch_awake() ? watch_tone_hz() : 0)`, beeps 150 ms at boot (confirms the piezo), boot diagnostics use the new LED order.
- **Simulator**: `export_face_board.py` (KiCad python) rebuilds `face_data.js` from the real Y42 board (ring radii now 14.635 / 17.44 / 19.57 mm; the C particle constants follow); Sound panel with WebAudio and an "Alarm test" button.
Not done: EEPROM for settings and the alarm (all RAM, lost at reset), snooze, bring-up on the real board (see `c/BRINGUP.md` step for the buzzer).
