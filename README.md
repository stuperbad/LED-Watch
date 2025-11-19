# LED-Watch — Software and Hardware Overview

This repository contains the hardware and firmware for the LED Watch project. The software work will live on the software-start branch while we scaffold the firmware and development tooling.

## Summary

A small wrist-worn LED watch using an ATmega128DB28 microcontroller and an RGB LED array. The KiCad hardware files are included in the repository (see the KiCad project folder listed below).

## Target hardware

- MCU / Board: ATmega128DB28 (AVR, 28-pin package)
- Display: RGB LEDs (project contains the "LED Watch - empty RGB version" KiCad project)
- RTC: (not populated in hardware docs — add here if present)
- Power: (battery, charging, regulator details to be added)
- Buttons: (pin mapping to be documented)

The most recent KiCad project is in the repository under the folder named "LED Watch - empty RGB version" and contains the schematic (.sch), PCB (.kicad_pcb), and other KiCad project files. If you want, I can list the exact files found there.

## Build and development

Two recommended workflows are supported by the scaffold we will add:

- PlatformIO (recommended for reproducible builds and CI)
  - We'll add a `platformio.ini` with a custom board definition if needed for ATmega128DB28, or instructions for adding a cores/board package.
- Arduino IDE (quick testing)
  - Open the `src`/`.ino` file in Arduino IDE and install any necessary core/board package for ATmega128DB28.

Note: The ATmega128DB28 is not a common Arduino default board; you may need a custom board definition or use raw AVR toolchains. I can add a sample PlatformIO configuration and a starter `main.ino` if you want.

## Software goals

- Drive the RGB LED display with efficient refresh
- Read time from an RTC (or maintain time on MCU)
- Handle button input and UI modes
- Support low-power sleep when idle

## Repo layout (planned)

- hardware/
  - LED Watch - empty RGB version/  (KiCad project files already present)
- software/
  - src/main.ino or src/main.cpp
  - drivers/
  - platformio.ini (optional)
  - README.md (this file)

## Branching and contribution

- This file was updated on branch `software-start` to reflect the actual MCU and presence of KiCad hardware files.
- Create feature branches off `software-start` for firmware work and open PRs to merge into `main` when ready.

## Next steps I can take now

- Add a PlatformIO `platformio.ini` and a starter `src/main.ino` for ATmega128DB28 (I can add a note about custom board config).
- Create driver stubs for display, buttons, and RTC.
- List the exact KiCad files in the "LED Watch - empty RGB version" folder.

Choose which one you'd like me to do next.