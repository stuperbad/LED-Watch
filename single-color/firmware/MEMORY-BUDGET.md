# Firmware memory budget (2026-10-12; measured for the logic, estimated for the rest)

**Whole firmware, measured (2026-10-12, after the hardware layer): 29.4 KB flash (22 %), 2.2 KB RAM (13 %).**

**Core alone, measured (2026-10-12):** the platform-independent core `firmware/c/watch.c` (all modes, 9 games, scan plan, no hardware drivers yet) linked for the AVR128DB48 with avr-gcc 16.1 (`-Os`, `--gc-sections`, including the libgcc helpers) is **24,389 bytes of flash (19 % of 128 KB) and 968 bytes of RAM (6 % of 16 KB)**; with `-Os -flto` 23.6 KB; with `-O2` it grows to 34 KB. Reproduce with `firmware/c/size_probe.c` (see `firmware/README.md`). The rest of the table below is still an estimate for the parts that do not exist yet (hardware drivers).

Target part: AVR128DB48 = **128 KB flash, 16 KB SRAM, 512 B EEPROM.**

## Flash (code + constant tables)
Measured core: about 24 KB. The estimates below were made before the port; the hardware drivers (matrix scan interrupt, I2C accelerometer, RTC, ADC, sleep, startup) are expected to add roughly 4-8 KB, so the whole firmware should land near 30 KB of 128 KB.
| Part | Estimate |
|---|---|
| Startup, clocks, sleep, RTC/PIT, ADC (VDD read), button debounce, pin-change wake | 2-3 KB |
| Matrix scan driver, brightness vs VDD, row-current limiting | 1-2 KB |
| Mode state machine: Time, date (weekday, leap years), Set, Stopwatch, Battery, Config, mode selection, lock | 4-6 KB |
| Display helpers: bars, score digits, award animation | 1-2 KB |
| LIS2DW12 driver (I2C, wake/tap/shake detection) | 1.5-2.5 KB |
| Particles + bead (fixed point, 60 particles, collisions) | 3-5 KB |
| Ring Runner, Target, Quick Draw, Orbit (6 patterns), Random, Pacer, Simon, Pong | about 1-1.5 KB each, 8-12 KB total |
| Tables: LED row/column map (~280 B), ring angles (~280 B), sine/sqrt tables (~0.5 KB), settings defaults | ~1 KB |
| **Total** | **roughly 25-40 KB, i.e. 20-31 % of 128 KB** |
If the port were written carelessly with floating point (no FPU on AVR) it could reach 50-60 KB, still under half. Plenty of headroom: roughly 85-100 KB free.

## RAM (SRAM)
| Item | Estimate |
|---|---|
| Framebuffer 12 x 12 | 144 B |
| Particles: 60 x (x, y, vx, vy as 16-bit) | 480 B |
| Orbit "twinkle" levels (132 LEDs) | 132 B |
| Simon sequence (20 symbols suffice for 999; stored as bits or bytes) | 20-32 B |
| Settings, time/date, stopwatch, button state, menu | ~100 B |
| Per-game state (only one game runs at a time, so share one union) | ~300 B |
| Stack and I2C buffers | ~400 B |
| **Total** | **roughly 1.5-2 KB, i.e. about 10-13 % of 16 KB** |

## EEPROM (512 B)
Settings (10 values) plus best scores for the scored games: well under 64 B.

## The real constraint is CPU, not memory
- The particle simulation compares every pair of particles: 60 particles is about 1,770 pair checks per physics step. On an 8-bit core at the default 4 MHz that is too slow in plain C; it needs either a coarse grid (only neighbours), a cap of about 30-40 particles, or running at 24 MHz while a particle game is on screen (costs power, fine for a game).
- The LED matrix scan runs from a timer interrupt (12 rows, a few hundred Hz to 1 kHz per slot) and must stay light.
- Everything else (buttons, Simon, Pong, Random, Pacer) is trivial for the CPU.
