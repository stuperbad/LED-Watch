#!/bin/bash
# autorefit.sh BASE ROUTED OUT NET... : refit one net at a time, the loosest tolerance whose DRC shows no new short/clearance/hole error
export MSYS_NO_PATHCONV=1
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"; KC="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
base=$1; routed=$2; out=$3; shift 3
cur=$routed
for net in "$@"; do
  ok=""
  for e in 0.15 0.12 0.10 0.08 0.06 0.04 0.02; do
    EPS=$e timeout 120 "$K" "$T/usbc_mockup/refit.py" $base.kicad_pcb $cur.kicad_pcb try.kicad_pcb $net 2>&1 | grep -c pieces >/dev/null
    cp user3.kicad_pro try.kicad_pro; "$K" "$T/refill.py" try.kicad_pcb try_f.kicad_pcb >/dev/null 2>&1; cp user3.kicad_pro try_f.kicad_pro
    "$KC" pcb drc --format json --severity-all --output drc_try.json try_f.kicad_pcb >/dev/null 2>&1
    n=$(python ../rev/bad.py drc_try.json)
    echo "$net EPS $e -> $n errors"
    if [ "$n" = "0" ]; then ok=$e; cp try.kicad_pcb ${out}_acc.kicad_pcb; break; fi
  done
  [ -z "$ok" ] && echo "$net: no tolerance passes, keeping the router's own path" && continue
  cur=${out}_acc
done
cp $cur.kicad_pcb $out.kicad_pcb; echo done $out
