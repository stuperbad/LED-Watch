#!/bin/bash
export MSYS_NO_PATHCONV=1
cd "C:/Users/evanf/AppData/Local/Temp/claude/C--Users-evanf-Desktop-LED-Watch/7d45cda8-235b-47cf-9813-ce50d757bd77/scratchpad/v3"
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"; KC="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
dump(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/arcs_to_segments.py" $1.kicad_pcb $1_poly.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_poly.kicad_pro; "$K" "$T/grid_dump.py" $1_poly.kicad_pcb g_$1.json 2>&1 | tail -1; }
drc(){ cp user3.kicad_pro $1.kicad_pro; "$K" "$T/refill.py" $1.kicad_pcb $1_f.kicad_pcb 2>&1 | tail -1; cp user3.kicad_pro $1_f.kicad_pro; "$KC" pcb drc --format json --severity-all --output drc_$1.json $1_f.kicad_pcb >/dev/null 2>&1; }
"$K" u4/fixnets.py u4/user.kicad_pcb w0.kicad_pcb u4/netref.json 2>&1 | grep -v swig
"$K" "$T/apply_ring_edits.py" w0.kicad_pcb w1.kicad_pcb u4/rm1.json 2>&1 | grep -v swig
"$K" u2/movep.py w1.kicad_pcb w2.kicad_pcb u4/pos.json 2>&1 | grep -v swig
"$K" "$T/copper_dump.py" w2.kicad_pcb u4/cu_w2.json | tail -1
cat u4/refs.txt > u4/refs_all.txt; echo " U5 C55 C56 R68 R69 R70 R71 R72 D50" >> u4/refs_all.txt
python u4/clear_gen.py u4/cu_w2.json u4/refs_all.txt u4/clear.json
"$K" "$T/apply_ring_edits.py" w2.kicad_pcb w3.kicad_pcb u4/clear.json 2>&1 | grep -v swig
"$K" "$T/copper_dump.py" w3.kicad_pcb u4/cu_w3.json | tail -1
python u4/prep2.py u4/cu_w3.json
"$K" "$T/apply_ring_edits.py" w3.kicad_pcb x0.kicad_pcb u4/extra.json 2>&1 | grep -v swig
cur=x0
for round in 1 2 3; do
  drc $cur
  nets=$(python u4/nets_from_drc.py drc_$cur.json); echo "ROUND $round open nets: $nets"
  [ -z "$nets" ] && break
  n=0; set -- $nets; list=(); 
  while [ $# -gt 0 ]; do
    grp=""; k=0; while [ $# -gt 0 ] && [ $k -lt 3 ]; do grp="$grp $1"; shift; k=$((k+1)); done
    dump $cur; printf '%s\n' $grp > u4/gn.txt
    extra="--exclude 113.0,96.3,121.3,103.8@B"; layers=""
    case "$grp" in " GND"*) layers="--layers F,In1,In2,B --w 0.15";; esac
    out=r${round}_$n
    timeout 240 python "$T/grid_route2.py" g_$cur.json $cur.kicad_pcb $out.kicad_pcb @u4/gn.txt --max-attempts 40 $extra $layers 2>&1 | grep -a "failed\|wrote"
    [ -f $out.kicad_pcb ] && cur=$out
    echo "PASS $grp"; n=$((n+1))
  done
done
cp user3.kicad_pro $cur.kicad_pro
bash chk.sh $cur.kicad_pcb 80 | grep -av "silk\|text_height"
echo ALL-DONE $cur
