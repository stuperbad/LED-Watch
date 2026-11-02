#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
route(){ # in out nets-file extra...
  in=$1; out=$2; nf=$3; shift 3
  timeout 240 python "$T/grid_route2.py" g_$in.json $in.kicad_pcb $out.kicad_pcb @$nf --max-attempts 40 "$@" 2>&1 | grep -a "failed\|wrote"
  [ -f $out.kicad_pcb ] || cp $in.kicad_pcb $out.kicad_pcb
}
"$K" u2/movep.py u3/t0.kicad_pcb u3/t1.kicad_pcb u3/pos2.json 2>&1 | grep -v swig
"$K" "$T/apply_ring_edits.py" u3/t1.kicad_pcb u3/t1b.kicad_pcb u3/col4rm.json 2>&1 | grep -v swig
"$K" "$T/copper_dump.py" u3/t1b.kicad_pcb u3/cu_t1b.json | tail -1
python usbc/clear_new.py u3/cu_t1b.json u3/clear.json
"$K" "$T/apply_ring_edits.py" u3/t1b.kicad_pcb u3/t2.kicad_pcb u3/clear.json 2>&1 | grep -v swig
"$K" "$T/apply_ring_edits.py" u3/t2.kicad_pcb u3/t2b.kicad_pcb u3/updi_via.json 2>&1 | grep -v swig
cp u3/t2b.kicad_pcb q0.kicad_pcb; dump q0
echo GND > u3/g0.txt
timeout 240 python "$T/grid_route2.py" g_q0.json q0.kicad_pcb q1.kicad_pcb @u3/g0.txt --w 0.15 --layers F,In1,In2,B 2>&1 | grep -a "failed\|wrote"; echo "PASS GND"
i=1
for grp in "SBU" "CC1 CC2" "VBUS /BATT" "ISET TS" "/UPDI +3V3" "/COL2_MCU /COL7_MCU /COL8_MCU /RESET /BUZ_B /COL4"; do
  dump q$i; printf '%s\n' $grp > u3/gn.txt
  route q$i q$((i+1)) u3/gn.txt --exclude "113.4,96.3,121.3,103.8@B"
  echo "PASS $grp"; i=$((i+1))
done
dump q$i; echo /COL3_MCU > u3/gn.txt; route q$i q$((i+1)) u3/gn.txt; echo "PASS COL3"; i=$((i+1))
cp user3.kicad_pro q$i.kicad_pro
bash chk.sh q$i.kicad_pcb 80 | grep -av "silk\|text_height"
echo ALL-DONE q$i
