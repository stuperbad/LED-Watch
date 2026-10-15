# Build the complete watch firmware for the AVR128DB48 -> hw\watch_fw.elf / .hex, and print the flash and RAM use.
#   powershell -File build_fw.ps1
$bin = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ZakKemble.avr-gcc_Microsoft.Winget.Source_8wekyb3d8bbwe\avr-gcc-16.1.0-x64-windows\bin"
$src = "hw\main.c","hw\matrix.c","hw\matrix_map.c","hw\clock.c","hw\buttons.c","hw\vbat.c","hw\buzzer.c","hw\i2c_twi.c","hw\imu.c","hw\hw_pure.c","watch.c"
& "$bin\avr-gcc.exe" -mmcu=avr128db48 -std=gnu99 -Os -Wall -Wextra -I. -I.. -Ihw '-DF_CPU=4000000UL' -ffunction-sections -fdata-sections '-Wl,--gc-sections' $src -o hw\watch_fw.elf
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$bin\avr-objcopy.exe" -O ihex hw\watch_fw.elf hw\watch_fw.hex
& "$bin\avr-size.exe" hw\watch_fw.elf      # text + data = flash used (of 131072), data + bss = RAM used (of 16384)
