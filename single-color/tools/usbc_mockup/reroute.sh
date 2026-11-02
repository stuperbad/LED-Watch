#!/bin/bash
# reroute.sh BOARD_BASENAME OUT_BASENAME NET [NET ...]  (run inside the scratch folder v3/, files without .kicad_pcb)
# per net: strip it back to its pad escapes, route it again with grid_route2.py (no rip-up of other nets), refit the router's pieces to 45-degree legs on pad / via centres
# (autorefit.sh: loosest tolerance whose DRC shows no new short / clearance / hole error), keep the result only if the net got shorter and no open connection appeared.
export MSYS_NO_PATHCONV=1
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"; KC="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
cur=$1; out=$2; shift 2
netlen(){ "$K" ../rev/detour.py $1.kicad_pcb 200 2>&1 | grep -E "^  $2 " ; }
for net in "$@"; do
  echo "=== $net"
  rm -f rr3.kicad_pcb rr2.kicad_pcb
  cp user3.kicad_pro ${cur}.kicad_pro
  "$K" "$T/usbc_mockup/keepnet.py" $cur.kicad_pcb rr1.kicad_pcb $net 2>&1 | grep -E "kept"
  cp user3.kicad_pro rr1.kicad_pro; "$K" "$T/arcs_to_segments.py" rr1.kicad_pcb rr1_poly.kicad_pcb >/dev/null 2>&1; cp user3.kicad_pro rr1_poly.kicad_pro
  "$K" "$T/grid_dump.py" rr1_poly.kicad_pcb g_rr1.json >/dev/null 2>&1
  printf '%s\n' $net > rrn.txt
  res=$(python "$T/grid_route2.py" g_rr1.json rr1.kicad_pcb rr2.kicad_pcb @rrn.txt --max-attempts 40 --rip-cost 100000 --via-cost 100 2>&1 | grep -a "routed\|failed:")
  echo "$res"
  echo "$res" | grep -q "failed: \[\]" || { echo "$net: router failed, net left as it was"; continue; }
  bash ../rev/autorefit.sh rr1 rr2 rr3 $net 2>&1 | tail -3
  [ -f rr3.kicad_pcb ] || continue
  before=$(MSYS_NO_PATHCONV=1 "$K" ../rev/detour.py $cur.kicad_pcb 300 2>&1 | grep -E "^  $net ")
  after=$(MSYS_NO_PATHCONV=1 "$K" ../rev/detour.py rr3.kicad_pcb 300 2>&1 | grep -E "^  $net ")
  echo "before: $before"; echo "after:  $after"
  cp rr3.kicad_pcb ${out}_$(echo $net | tr -d '/').kicad_pcb
  cur=${out}_$(echo $net | tr -d '/')
done
cp $cur.kicad_pcb $out.kicad_pcb; echo ALLDONE $out
