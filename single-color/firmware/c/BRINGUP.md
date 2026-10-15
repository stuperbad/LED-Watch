# Bring-up guide: from boards in the mail to a watch showing the time

Nothing in this firmware has run on a real board yet. This file says what to do on the day, what each check should show, and which numbers will need adjusting. Written 2026-10-12.

## 0. What the firmware does when it starts (so you know what you are looking at)
1. **Self-test, 2 seconds.** The six indicator LEDs (SET TMR BAT FUN CFG LCK, left to right under the solar cell) show what was found:
   - **SET** lit = the 32.768 kHz watch crystal started. If it is dark, the watch is timing itself from an inaccurate internal oscillator (the time will drift minutes per day).
   - **TMR** lit = the accelerometer answered on I2C.
   - **BAT** lit = the BQ25570's BAT_OK pin is high (battery fine).
   - **FUN** lit = supply reads above 3.0 V. **CFG** lit = supply reads above 3.6 V. (These two are only as accurate as the voltage reading, see section 4.)
   - **LCK** is not used.
2. Then the display goes dark and the chip sleeps. **Press any button (or raise the wrist) to wake it**: it shows the time (one LED per ring: hour, minute, second). 10 seconds later it goes dark again.
3. Everything else is the manual: `firmware/sim/MANUAL.md` (hold Left to pick a mode, games in FUN, settings in CFG, hold both buttons 2 s to lock).

## 1. What you need
- **A UPDI programmer.** The board has a Tag-Connect TC2030-NL footprint: pad 1 = UPDI, pad 2 = VBAT, pad 6 = GND (see PRE-ORDER-CHECKLIST B1). Options that AVRDUDE (already installed with the compiler) supports: Microchip **PICkit 4 or 5** (`-c pickit4_updi`, `-c pickit5_updi`), **Atmel-ICE** (`-c atmelice_updi`), **SNAP** (set to UPDI mode), a **Curiosity Nano AVR128DB48** used as a programmer (`-c pkobn_updi`), or the cheapest: a **USB-serial adapter plus a 4.7 kohm resistor** (`-c serialupdi`, TX through the resistor to UPDI, RX straight to UPDI). The Tag-Connect cable itself is a separate part (TC2030-NL, or TC2030-IDC-NL plus its adapter).
- **A bench supply with current limit** (or a battery with a meter in series): power the board through the VBAT pad of the programming connector at about 3.6 V, limit 20 mA for the first power-up.
- A multimeter, and a phone or computer clock to compare time against.
- Developing without the board: nothing more is needed; the simulator in `firmware/sim` and the tests in `firmware/c/test` already run on this PC.

## 2. First programming (the chip ships with the wrong power-supply fuse)
The AVR128DB48 comes with its "multi-voltage I/O" fuse set to dual-supply. Port C (our LED rows 0-5 and columns 10-11) is the multi-voltage port, and our board has VDDIO2 tied to VBAT, so the fuse must be set to **single supply** (datasheet DS40002247B section 19, fuse SYSCFG1 bits 4:3 = 0b10).
```
avrdude -c <programmer> -p avr128db48 -v                      # should report an AVR128DB48; stop here if it does not
avrdude -c <programmer> -p avr128db48 -U syscfg1:w:0x10:m     # single supply (factory value is 0x08 = dual)
avrdude -c <programmer> -p avr128db48 -U flash:w:hw\watch_fw.hex:i
```
(`<programmer>` is one of the names above; add `-P <port>` for serial UPDI, e.g. `-P COM5`; the avrdude program is in the toolchain folder, see `firmware/README.md`.) Build the hex first with `powershell -File build_fw.ps1`.

## 3. Check order (stop at the first thing that is wrong)
1. **Current:** at power-up it draws a few mA for about 3 seconds (the crystal starts, the self-test LEDs light), then it should fall to the sleep level. Target: **about 3-5 microamps** with the display off (RTC + crystal + accelerometer at 12.5 Hz). A reading of hundreds of microamps means something is awake or a pin is floating: check that the self-test finished and the display is dark.
2. **Self-test LEDs** as in section 0. Note which are missing.
3. **Wake with a button; the time shows.** Compare with a phone: set it first (hold Left, move with Right to SET, Left = next unit, Right = +1). After 12 hours compare again: crystal timekeeping should be within a second or so.
4. **Every LED:** the "Orbit" game (FUN, game 5) with pattern 2 (Lissajous) or the Target game shows lit LEDs at changing positions; walk through all rings and check no LED is missing or in the wrong place (hour LED 12 should be at the top). If the whole picture is mirrored or rotated, the matrix mapping and the board disagree (the generated `ledmap.h`, `pins.h`, `hwmap.h` come from the schematic: regenerate with `python firmware/gen_pins.py` if the schematic changed).
5. **Brightness:** the 12 dim "target zone" LEDs of the Target game and the full-brightness LEDs should differ clearly; the supply voltage correction (below) makes brightness constant between 3.0 and 4.2 V.
6. **Buttons:** short and long presses, both together for 2 s (LCK blinks).
7. **Accelerometer axes (needs the IMU found, TMR lit):** see section 4.

## 4. The numbers that will need adjusting (all in `hw/hw_config.h`)
| Setting | Why it needs checking | How |
|---|---|---|
| `IMU_MAP_*` (axis map) | the chip's mounting direction on the PCB is not known | Particles game, mode 5 (bead): lay the watch flat: nothing moves. Lift the 12 o'clock edge: the bead must roll toward 6 o'clock. Lift the 3 o'clock edge: it must roll toward 9. If a direction is wrong, flip its `SIGN`; if 12/3 are swapped, swap the `AXIS` numbers. Flat and face-up the z reading must be +1000 (use the Random game or a debugger to see it; sign of z: raising the watch face toward you must keep it positive). |
| `VDD_CAL_PERMILLE` | the internal VDD/10 divider is only +-10 % accurate | measure the battery with a multimeter, compare with what the BAT screen shows (hour-ring bar) or step in a debugger; set it to (real / measured) x 1000. |
| `IMU_WAKE_THS`, `IMU_TAP_THS_Z`, `IMU_INT_DUR`, `RAISE_*` | thresholds depend on the real watch on a real wrist | raise the wrist at your normal speed with the display off: it must wake; walking and arm swings should not. Tune `IMU_WAKE_THS` (higher = needs a bigger movement), `RAISE_MG_PER_PERCENT` (strength scale; compare with CFG 2 "raise sensitivity"), and for taps `IMU_TAP_THS_Z` (lower = lighter tap). |
| `CLKCTRL_LPMODE` for the crystal (`hw/clock.c`) | normal drive is used for reliable start-up; low-power drive saves some current but only works with a suitable crystal and load capacitors | after the crystal works, try `CLKCTRL_LPMODE_bm` and see if SET still lights at power-up and the sleep current drops. |

## 5. Known gaps (not done yet)
- **Settings are not saved**: the 10 CFG values go back to their defaults at every power-up (EEPROM storage is the next small job).
- **Solar level and "charging"** screens read 0 (no measurement path yet; the BQ25570 does not report them on a pin).
- **Particle games are probably too slow at 4 MHz.** The pair-collision loop is the heavy part; on the PC it does not matter, on the chip at 4 MHz it may run at only a few frames a second. Options: run the CPU at 24 MHz while that game is on screen (needs the scan timer and I2C divider re-timed), use fewer particles (`WATCH_MAX_PARTICLES` in `watch.h`), or add a neighbour grid. Measure first.
- **Quick Draw / Pong timing** use the 15.6 ms heartbeat, so button reaction is resolved to about 16 ms plus the 15-30 ms debounce.
- The debounce makes the first press after sleep take 16-31 ms longer to show (not noticeable).

## Buzzer (added 2026-10-14)
1. At power-up the watch plays a 150 ms 4 kHz beep together with the self-test LEDs (indicator row: SET crystal, TMR accelerometer, BAT battery OK, FUN > 3.0 V, CFG > 3.6 V). No beep = check PB4/PB5 (BUZ_A / BUZ_B) and the piezo solder joints (it is a 9 x 9 mm part with two 1.3 x 3.4 mm pads).
2. Scope PB4 and PB5 together while the alarm test runs (ALM mode: switch the alarm on, set it to the next minute): the two pins must swing in OPPOSITE phase (about 6.6 V across the piezo at VDD 3.3 V) and both must sit LOW when silent. If they are in phase the inversion (`PORTB.PIN5CTRL`) is off.
3. Listen at 2, 3, 4, 5 kHz (the key beeps are 3.5 kHz, the alarm 4 kHz, game tunes 1.3 - 4.8 kHz): the piezo is loudest near 4 kHz. The sound leaves through the slots under the two edges without terminals; keep them clear of tape or the strap. If it is too quiet or too loud change the alarm frequency in the `P_ALARM` pattern (both cores).
4. Measure the supply current while a tone plays (a piezo is a capacitor, expect well under 1 mA extra) and check that sleep current is unchanged afterwards (timer stopped, both pins low).
