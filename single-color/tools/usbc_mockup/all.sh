#!/bin/bash
# all.sh : build the mock-up from the hardware board copy (usbc/base.kicad_pcb): parts + receptacle, clear, route, prune.  result um7.kicad_pcb
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
python usbc/notch.py
"$K" usbc/build.py usbc/m1.kicad_pcb 2>&1 | grep -v swig
"$K" "$T/copper_dump.py" usbc/m1.kicad_pcb usbc/cu_m1.json | tail -1
python usbc/clear_new.py usbc/cu_m1.json usbc/clear1.json
"$K" "$T/apply_ring_edits.py" usbc/m1.kicad_pcb usbc/m2.kicad_pcb usbc/clear1.json 2>&1 | grep -v swig
python usbc/shvias.py
"$K" "$T/apply_ring_edits.py" usbc/m2.kicad_pcb um3.kicad_pcb usbc/shvias.json 2>&1 | grep -v swig
dump um3
echo GND > usbc/nets_a.txt
printf '%s\n' VBUS /BATT CC1 CC2 SBU ISET TS +3V3 /UPDI /BUZ_B /COL11_MCU /COL2_MCU /COL3_MCU /COL4_MCU /COL7_MCU > usbc/nets_b.txt
echo /BUZ_B > usbc/nets_c.txt
python "$T/grid_route2.py" g_um3.json um3.kicad_pcb um3a.kicad_pcb @usbc/nets_a.txt --w 0.15 --layers F,In1,In2,B 2>&1 | tail -3
echo PASS-A-DONE
dump um3a
python "$T/grid_route2.py" g_um3a.json um3a.kicad_pcb um3b.kicad_pcb @usbc/nets_b.txt --max-attempts 80 --exclude "113.4,96.3,121.3,103.8@B" 2>&1 | tail -4
echo PASS-B-DONE
dump um3b
python "$T/grid_route2.py" g_um3b.json um3b.kicad_pcb um3c.kicad_pcb @usbc/nets_c.txt 2>&1 | tail -3
cp um3c.kicad_pcb um3b.kicad_pcb
echo PASS-C-DONE
cp user3.kicad_pro um3b.kicad_pro
python "$T/prune_dangling_drc.py" um3b.kicad_pcb um5.kicad_pcb 110 100 12 2>&1 | tail -3
cp user3.kicad_pro um5.kicad_pro
python "$T/prune_dangling_drc.py" um5.kicad_pcb um7.kicad_pcb 110 100 12 2>&1 | tail -3
echo PRUNE-DONE
bash chk.sh um7.kicad_pcb 80 | grep -av "silk\|text_height"
"$K" "$T/copper_dump.py" um7.kicad_pcb usbc/cu_m7.json | tail -1
echo ALL-DONE
