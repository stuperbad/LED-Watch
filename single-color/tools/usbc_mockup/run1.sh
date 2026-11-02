#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
"$K" "$T/apply_ring_edits.py" uu0.kicad_pcb u2/s1.kicad_pcb u2/rm_mine.json 2>&1 | grep -v swig
"$K" u2/movep.py u2/s1.kicad_pcb s2.kicad_pcb u2/place3.json 2>&1 | grep -v swig
dump s2
echo GND > u2/nets_a.txt
printf '%s\n' CC1 SBU /UPDI +3V3 > u2/nets_b.txt
python "$T/grid_route2.py" g_s2.json s2.kicad_pcb s3.kicad_pcb @u2/nets_a.txt --w 0.15 --layers F,In1,In2,B 2>&1 | tail -3
echo PASS-A-DONE
dump s3
python "$T/grid_route2.py" g_s3.json s3.kicad_pcb s4.kicad_pcb @u2/nets_b.txt --max-attempts 80 --exclude "113.4,96.3,121.3,103.8@B" 2>&1 | tail -6
echo PASS-B-DONE
cp user3.kicad_pro s4.kicad_pro
bash chk.sh s4.kicad_pcb 60 | grep -av "silk\|text_height"
echo ALL-DONE
