#!/bin/bash
# autorefit2.sh BASE ROUTED OUT NET... : as autorefit.sh, and the refit must not add keep-out violations (zonecount) either
export MSYS_NO_PATHCONV=1
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"; KC="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
base=$1; routed=$2; out=$3; shift 3
cur=$routed
z0=$("$K" "$T/usbc_mockup/zonecount.py" $cur.kicad_pcb usbc/base.kicad_pcb 2>&1 | grep -v -E 'duplicate|leak' | head -1)
for net in "$@"; do
  ok=""
  for e in 0.15 0.12 0.10 0.08 0.06 0.04 0.02; do
    EPS=$e timeout 120 "$K" "$T/usbc_mockup/refit.py" $base.kicad_pcb $cur.kicad_pcb try2.kicad_pcb $net >/dev/null 2>&1
    cp user3.kicad_pro try2.kicad_pro; "$K" "$T/refill.py" try2.kicad_pcb try2_f.kicad_pcb >/dev/null 2>&1; cp user3.kicad_pro try2_f.kicad_pro
    "$KC" pcb drc --format json --severity-all --output drc_try2.json try2_f.kicad_pcb >/dev/null 2>&1
    n=$(python ../rev/bad.py drc_try2.json); z=$("$K" "$T/usbc_mockup/zonecount.py" try2.kicad_pcb usbc/base.kicad_pcb 2>&1 | grep -v -E 'duplicate|leak' | head -1)
    echo "$net EPS $e -> $n errors, zone $z (was $z0)"
    if [ "$n" = "0" ] && [ "$z" -le "$z0" ]; then ok=$e; cp try2.kicad_pcb ${out}_acc.kicad_pcb; break; fi
  done
  [ -z "$ok" ] && echo "$net: no tolerance passes, keeping the router's own path" && continue
  cur=${out}_acc
done
cp $cur.kicad_pcb $out.kicad_pcb; echo done $out
