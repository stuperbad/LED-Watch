#!/bin/bash
# Layout B (Evan's sketch): solar cell centred; MCU with the 32 kHz crystal standing upright to its right and the Tag-Connect pads to its left, all ABOVE the cell;
# mode LEDs as a horizontal row tight under the cell; buttons low and symmetric; battery plugs facing their own pouch. No autorouter.
# Usage: ./build_board_b.sh NAME [DIAMETER]
set -e
N=${1:-L43}; D=${2:-43.5}
KP="/c/Program Files/KiCad/10.0/bin/python.exe"; KC="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
cd "$(dirname "$0")"
python plan_board.py --mcu-pkg qfn --safety 0 --btn-style bottom --ind-style row --ind-count 6 --ind-pitch 3.4 --mcu-side front --battery tc70 --batt-count 2 --cell KXOB25_05X3 --cell-count 1 \
  --rad-gap 0.8 --band-keepout 0 --res-angle -5.5 --res-flip --flush-inner --batt-conn jst --back-strip --back-edge 0.3 --pack-gap 0.2 --part-clr 0.25 --back-via-clr 0.6 --plug-rot-free --batt-clr 0.2 \
  --edge-margin 0.88 --slot-clear 1.5 --cell-y 0 --mcu-target 0,-8.4 --mcu-rot 0 --xtal-side right --low-parts U2 --btn-x 4.9 --btn-up 0.4 --tag-gap 0.8 --xtal-gap 0.7 --mcu-halo 1.0 --label-h 0.8 --label-w 0.1 \
  --flank-parts "R57:12,R58:6,R59:9,R50:3,R52:2,R55:4,R53:1,R51:11,R54:10,R56:8,R20:5,R21:7" --plugs-outer --close-parts C10,C11,C12,C30,C31 --above-mcu C30,C11,C10,C12,C31 --above-pitch 1.9 --nudge "J2:0:-0.4,C54:0.97:-0.34,SW1:-0.02:-0.484,SW2:0.02:-0.484,U2:0:-0.484" --ring-caps "C53:12:L,C51:12:R,C50:6:L,C52:6:R,C13:9:R,C60:9:L,C61:3:L,C62:3:R" --diameter $D --name $N | tail -1
"$KP" write_pcb.py $N 2>&1 | grep -v "swig\|handler" | tail -1
cd boards/$N
"$KP" ../../crystal_hookup.py $N.kicad_pcb ${N}_x.kicad_pcb 2>&1 | grep -v "swig\|handler" | tail -3
"$KP" ../../polar_route.py ${N}_x.kicad_pcb ${N}_arc.kicad_pcb 2>&1 | grep -v "swig\|handler" | tail -1
"$KP" ../../polar_route.py ${N}_x.kicad_pcb ${N}_poly.kicad_pcb poly 2>&1 | grep -v "swig\|handler" | tail -1
"$KC" pcb drc --format json --severity-all --all-track-errors -o drc.json ${N}_arc.kicad_pcb >/dev/null 2>&1 || true
python -c "
import json,collections
j=json.load(open('drc.json'));print('DRC', dict(collections.Counter((v['severity'],v['type']) for v in j['violations'])))
for v in j['violations']:
    if v['severity']=='error': print(' ',v['description'][:110],[i['description'][:40] for i in v['items']])"
