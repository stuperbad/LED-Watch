#!/bin/bash
# order.sh TAG net net ... : route the nets one at a time (in this order) from z1 with the keep-outs; print failures and total length
export MSYS_NO_PATHCONV=1
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
tag=$1; shift; cur=${START:-z1}; tot=0; fails=""
for n in "$@"; do
  cp user3.kicad_pro $cur.kicad_pro; "$K" "$T/arcs_to_segments.py" $cur.kicad_pcb ${cur}_poly.kicad_pcb >/dev/null 2>&1; cp user3.kicad_pro ${cur}_poly.kicad_pro
  "$K" "$T/grid_dump.py" ${cur}_poly.kicad_pcb g_${tag}.json >/dev/null 2>&1
  printf '%s\n' $n > ../rev/go_$tag.txt
  out=$(timeout 200 python "$T/grid_route2.py" g_${tag}.json $cur.kicad_pcb o_${tag}_$(echo $n | tr -d '/+').kicad_pcb @../rev/go_$tag.txt --max-attempts 40 --rip-cost 100000 --via-cost 100 --exclude "$(cat ../rev/excl3.txt)" 2>&1 | grep -a "routed\|failed:")
  len=$(echo "$out" | grep routed | sed 's/.* \([0-9.]*\) mm,.*/\1/' | paste -sd+ | bc 2>/dev/null)
  if echo "$out" | grep -q "failed: \[\]"; then echo "$n ok $(echo "$out" | grep routed | sed 's/.* \([0-9.]*\) mm,.*//' | paste -sd+)"; else echo "$n FAILED"; fi
  [ -f o_${tag}_$(echo $n | tr -d '/+').kicad_pcb ] && echo "$out" | grep -q "failed: \[\]" && cur=o_${tag}_$(echo $n | tr -d '/+')
done
echo "END $tag $cur"
