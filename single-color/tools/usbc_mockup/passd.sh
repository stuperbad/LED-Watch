#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
dump um7
printf '%s\n' VBUS CC2 SBU /UPDI > usbc/nets_d.txt
python "$T/grid_route2.py" g_um7.json um7.kicad_pcb um8.kicad_pcb @usbc/nets_d.txt --max-attempts 60 2>&1 | tail -6
echo PASS-D-DONE
cp user3.kicad_pro um8.kicad_pro
python "$T/prune_dangling_drc.py" um8.kicad_pcb um9.kicad_pcb 110 100 12 2>&1 | tail -3
bash chk.sh um9.kicad_pcb 80 | grep -av "silk\|text_height"
"$K" "$T/copper_dump.py" um9.kicad_pcb usbc/cu_m9.json | tail -1
echo ALL-DONE
