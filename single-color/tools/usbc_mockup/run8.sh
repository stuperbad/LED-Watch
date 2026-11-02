#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
"$K" "$T/apply_ring_edits.py" u4/c1.kicad_pcb u4/c2.kicad_pcb u4/rm_b.json 2>&1 | grep -v swig
cp u4/c2.kicad_pcb d2.kicad_pcb; dump d2
echo GND > u4/g0.txt
timeout 600 python "$T/grid_route2.py" g_d2.json d2.kicad_pcb d3.kicad_pcb @u4/g0.txt --w 0.1 --layers F,In1,In2,B 2>&1 | grep -a "failed\|wrote"; echo "PASS GND"
dump d3
timeout 2400 python "$T/grid_route2.py" g_d3.json d3.kicad_pcb d4.kicad_pcb @u4/nets_all.txt --w 0.1 --max-attempts 300 --exclude "113.0,96.3,121.3,103.8@B" 2>&1 | grep -a "failed\|wrote\|attempt" | tail -40
echo "PASS ALL"
[ -f d4.kicad_pcb ] || cp d3.kicad_pcb d4.kicad_pcb
cp user3.kicad_pro d4.kicad_pro
bash chk.sh d4.kicad_pcb 80 | grep -av "silk\|text_height"
echo ALL-DONE d4
