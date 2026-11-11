#!/bin/bash
# rework_route.sh POS.json OUTBASE : apply a placement to the rework board copy, rip up what it touches, route the loops first (wide), then the rest. scratch-relative paths (v17/)
export MSYS_NO_PATHCONV=1
S="C:/Users/evanf/AppData/Local/Temp/claude/4e09da735c58ddc7/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v17"; cd "$S"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
POS=$1; OUT=$2
cp ../v16/rework.kicad_pro base.kicad_pro
dump(){ cp base.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp base.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
"$K" "$T/rework_apply.py" ../v16/rework.kicad_pcb ${OUT}_0.kicad_pcb "$POS" 2>&1 | grep -v -E "swig|assert"
