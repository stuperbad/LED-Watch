#!/bin/bash
# usage (git bash, from a scratch folder): ring_route_test.sh OFFSET "hour,minute,second ring radii" R TAG   -> builds the board, routes the 40 ring nets (colour lines first, F/In1/B) with single-color/tools/grid_route2.py; needs rt/off0cols/nets.txt (one net name per line)
OFF=$1; RING=$2; R=$3; TAG=$4
KP="C:/Program Files/KiCad/10.0/bin/python.exe"; T="/c/Users/evanf/Desktop/LED Watch/single-color/tools"; B="/c/Users/evanf/Desktop/LED Watch/rgb/tools/build_sketch.py"
D=rt/s_$TAG; mkdir -p $D
"$KP" "$B" --led-offset $OFF --ring $RING --R $R --out "$(cygpath -m "$PWD")/$D/b.kicad_pcb" >/dev/null 2>&1
cp "/c/Users/evanf/Desktop/LED Watch/rgb/LED Watch - RGB.kicad_pro" $D/b.kicad_pro
"$KP" "$T/grid_dump.py" $D/b.kicad_pcb $D/grid.json >/dev/null 2>&1
cp rt/off0cols/nets.txt $D/nets.txt
( time python -u "$T/grid_route2.py" $D/grid.json $D/b.kicad_pcb $D/routed.kicad_pcb @$D/nets.txt ) > $D/log.txt 2>&1
