# Applies a new .kicad_pcb to the LED Watch project and reloads KiCad on it.
# Usage: apply-and-reload.ps1 -NewPcb <path to the edited board>
param([Parameter(Mandatory)][string]$NewPcb, [string]$NewSch)

$proj = 'C:\Users\evanf\Desktop\LED-Watch'
$pcb  = Join-Path $proj 'LED Watch.kicad_pcb'
$snap = Join-Path $proj 'claude-snapshots'
New-Item -ItemType Directory -Force $snap | Out-Null

# 1. snapshot the current board (and schematic if given) before replacing
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
Copy-Item $pcb (Join-Path $snap "LED Watch-before-$stamp.kicad_pcb")
$sch = Join-Path $proj 'LED Watch.kicad_sch'
if ($NewSch) { Copy-Item $sch (Join-Path $snap "LED Watch-before-$stamp.kicad_sch") }

# 2. close KiCad (unsaved view state is discarded; the snapshot above is the safety net)
Get-Process kicad, pcbnew, eeschema -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 3. clear stale lock files left by the forced close, then swap in the new board
Get-ChildItem $proj -Filter '~LED Watch*.lck' -Force -ErrorAction SilentlyContinue | Remove-Item -Force
Copy-Item $NewPcb $pcb -Force
if ($NewSch) { Copy-Item $NewSch $sch -Force }

# 4. reopen KiCad: project manager + PCB editor on the board
Start-Process 'C:\Program Files\KiCad\10.0\bin\kicad.exe' -ArgumentList ('"' + (Join-Path $proj 'LED Watch.kicad_pro') + '"')
Start-Sleep -Seconds 4
Start-Process 'C:\Program Files\KiCad\10.0\bin\pcbnew.exe' -ArgumentList ('"' + $pcb + '"')
"Applied $NewPcb; snapshot saved as LED Watch-before-$stamp.kicad_pcb"
