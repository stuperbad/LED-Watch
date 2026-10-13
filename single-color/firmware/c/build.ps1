# Build a C file for the AVR128DB48 with the winget-installed AVR-GCC (Zak Kemble build, GCC 16.1.0).
# usage: powershell -File build.ps1 blink_test.c
param([Parameter(Mandatory=$true)][string]$Source)
$bin = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ZakKemble.avr-gcc_Microsoft.Winget.Source_8wekyb3d8bbwe\avr-gcc-16.1.0-x64-windows\bin"
$name = [IO.Path]::GetFileNameWithoutExtension($Source)
& "$bin\avr-gcc.exe" -mmcu=avr128db48 -Os -Wall -Wextra -DF_CPU=4000000UL $Source -o "$name.elf"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$bin\avr-objcopy.exe" -O ihex "$name.elf" "$name.hex"
& "$bin\avr-size.exe" "$name.elf"      # text+data = flash used, data+bss = RAM used (AVR128DB48: 128 KB flash, 16 KB RAM)
