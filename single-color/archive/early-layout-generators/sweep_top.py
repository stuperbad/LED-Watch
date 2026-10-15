import subprocess,itertools,sys,re
base="--mcu-pkg qfn --safety 0 --btn-style bottom --ind-style arc --ind-count 6 --ind-pitch 3.4 --mcu-side front --battery tc70 --batt-count 2 --cell KXOB25_05X3 --cell-count 1 --rad-gap 0.8 --band-keepout 0 --res-angle -5.5 --res-flip --flush-inner --batt-conn jst --back-strip --back-edge 0.3 --pack-gap 0.2 --part-clr 0.25 --back-via-clr 0.6 --plug-rot-free --batt-clr 0.2 --xtal-below --edge-margin 0.88 --mcu-rot 270 --xtal-cap-rot 270 --flank-parts R57:12,R58:6,R50:3,R52:2,R55:4,R53:1,R51:11,R54:10,R56:8,R20:5,R21:7,C31:9 --slot-clear 1.5".split()
out=open("sweep_top.txt","w")
for D in (43.0,43.5,44.0):
    for cy in (0,-1,-2,-3):
        for top in ("","J2","J2,C54","J2,L2,C54","L2,C54"):
            cmd=["python","plan_board.py"]+base+["--cell-y",str(cy),"--diameter",str(D),"--name","SW"]+(["--top-parts",top] if top else [])
            r=subprocess.run(cmd,capture_output=True,text=True)
            last=(r.stdout.strip().splitlines() or [""])[-1]
            ok="ok=True" in last
            un=re.search(r"unplaced=(\[.*?\])",last)
            line=f"D={D} cy={cy} top=[{top}] -> {'OK' if ok else 'fail '+(un.group(1) if un else last[:60])}"
            print(line,flush=True); out.write(line+"\n"); out.flush()
