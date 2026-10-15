#!/bin/bash
# Build the single-colour board end to end (placement -> pcb -> crystal -> polar rows/columns). Usage: ./build_board.sh NAME [DIAMETER]
# Does NOT run the autorouter (do that deliberately: see tools/prep_dsn.py).
set -e
N=${1:-G43}; D=${2:-43}
KP="/c/Program Files/KiCad/10.0/bin/python.exe"; KC="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
cd "$(dirname "$0")"
python plan_board.py --mcu-pkg qfn --safety 0 --btn-style bottom --ind-style arc --ind-count 6 --ind-pitch 3.4 --auto-cell-y --mcu-side front --battery tc70 --batt-count 2 --cell KXOB25_05X3 --cell-count 1 \
  --rad-gap 0.8 --band-keepout 0 --res-angle -5.5 --res-flip --flush-inner --batt-conn jst --back-strip --back-edge 0.3 --pack-gap 0.2 --part-clr 0.25 --back-via-clr 0.6 --plug-rot-free --batt-clr 0.2 \
  --xtal-below --edge-margin 0.88 --slot-clear 1.5 --top-parts J2,C54 --mcu-rot 270 --xtal-cap-rot 270 --flank-parts "R57:12,R58:6,R50:3,R52:2,R55:4,R53:1,R51:11,R54:10,R56:8,R20:5,R21:7,C31:9" --diameter $D --name $N | tail -1
"$KP" write_pcb.py $N 2>&1 | grep -v "swig\|handler" | tail -1
cd boards/$N
"$KP" ../../crystal_hookup.py $N.kicad_pcb ${N}_x.kicad_pcb 2>&1 | grep -v "swig\|handler" | tail -1
"$KP" ../../polar_route.py ${N}_x.kicad_pcb ${N}_arc.kicad_pcb 2>&1 | grep -v "swig\|handler" | tail -1
"$KP" ../../polar_route.py ${N}_x.kicad_pcb ${N}_poly.kicad_pcb poly 2>&1 | grep -v "swig\|handler" | tail -1
"$KC" pcb drc --format json --severity-all --all-track-errors -o drc.json ${N}_arc.kicad_pcb >/dev/null 2>&1 || true
python -c "
import json,collections
j=json.load(open('drc.json'));print('DRC', dict(collections.Counter((v['severity'],v['type']) for v in j['violations'])))
for v in j['violations']:
    if v['severity']=='error': print(' ',v['description'][:110],[i['description'][:40] for i in v['items']])"
