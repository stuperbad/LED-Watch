#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"; KC="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
drc(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/refill.py" $1.kicad_pcb $1_f.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_f.kicad_pro; "$KC" pcb drc --format json --severity-all --output drc_$1.json $1_f.kicad_pcb >/dev/null 2>&1; }
cp u5/s4.kicad_pcb x0.kicad_pcb
cur=x0
for round in 1 2 3 4; do
  drc $cur
  nets=$(python u4/nets_from_drc.py drc_$cur.json); echo "ROUND $round open nets: $nets"
  [ -z "$nets" ] && break
  n=0; set -- $nets; list=(); 
  while [ $# -gt 0 ]; do
    grp=""; k=0; while [ $# -gt 0 ] && [ $k -lt 3 ]; do grp="$grp $1"; shift; k=$((k+1)); [ "$1" = "GND" ] && break; case "$grp" in " GND") break;; esac; done
    dump $cur; printf '%s\n' $grp > u4/gn.txt
    extra="--exclude 113.0,96.3,121.3,103.8@B"; layers=""
    case "$grp" in " GND"*) layers="--layers F,In1,In2,B";; esac
    out=y${round}_$n
    timeout 240 python "$T/grid_route2.py" g_$cur.json $cur.kicad_pcb $out.kicad_pcb @u4/gn.txt --max-attempts 40 $extra $layers 2>&1 | grep -a "failed\|wrote"
    [ -f $out.kicad_pcb ] && cur=$out
    echo "PASS $grp"; n=$((n+1))
  done
done
cp user3.kicad_pro $cur.kicad_pro
bash chk.sh $cur.kicad_pcb 80 | grep -av "silk\|text_height"
echo ALL-DONE $cur
