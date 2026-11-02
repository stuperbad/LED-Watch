"""tidy2.py START OUT NET [EPS] : (system python, run inside the scratch folder with chk.sh) strip NET's tracks into a base copy, refit the whole net at EPS; where DRC then reports a conflict, leave the chains
within 1.2 mm of it alone (SKIP box) and refit again, until DRC (shorts / clearance / hole) is clean and zonecount does not rise. Writes OUT.kicad_pcb. Prints piece counts before / after."""
import subprocess,sys,json,os,re
start,out,net=sys.argv[1:4]; eps=sys.argv[4] if len(sys.argv)>4 else "0.08"
tag=net.replace("/","")
K="C:/Program Files/KiCad/10.0/bin/python.exe"; T="C:/Users/evanf/Desktop/LED Watch/single-color/tools/usbc_mockup"
env=dict(os.environ,MSYS_NO_PATHCONV="1")
def run(*a,**k): return subprocess.run(list(a),capture_output=True,text=True,env=k.get("env",env))
strip=f'''import pcbnew,sys
b=pcbnew.LoadBoard("{start}.kicad_pcb"); g=[]
for t in list(b.GetTracks()):
    if t.GetNetname()=="{net}" and t.GetClass()!="PCB_VIA": b.Remove(t); g.append(t)
pcbnew.SaveBoard("tb2_{tag}.kicad_pcb",b)
'''
open(f"strip_{tag}.py","w").write(strip); run(K,f"strip_{tag}.py")
import shutil; shutil.copy("user3.kicad_pro",f"tb2_{tag}.kicad_pro")
def count(board):
    r=run(K,"-c",f'import pcbnew;b=pcbnew.LoadBoard("{board}.kicad_pcb");print(sum(1 for t in b.GetTracks() if t.GetNetname()=="{net}" and t.GetClass()!="PCB_VIA"))')
    return int(r.stdout.strip().split()[-1])
n0=count(start); skips=[]
for it in range(6):
    e=dict(env,EPS=eps,SKIP=";".join(skips))
    run(K,f"{T}/refit.py",f"tb2_{tag}.kicad_pcb",f"{start}.kicad_pcb",f"{out}.kicad_pcb",net,env=e)
    shutil.copy("user3.kicad_pro",f"{out}.kicad_pro")
    r=subprocess.run(["C:/Program Files/Git/usr/bin/bash.exe","chk.sh",out],capture_output=True,text=True,env=env); txt=r.stdout
    bad=re.search(r"BAD (\d+)",txt); zone=re.search(r"ZONE (\d+)",txt)
    pos=re.findall(r"\('([^']*)', ([\d.]+), ([\d.]+)\)",txt)
    print("iteration",it,"skips",len(skips),"BAD",bad.group(1) if bad else "?","ZONE",zone.group(1) if zone else "?")
    if bad and bad.group(1)=="0":
        print(net,"pieces",n0,"->",count(out)); break
    for line in txt.splitlines():
        if line.strip().startswith(("clearance","shorting","hole_clearance","tracks_crossing","copper","solder")):
            for nm,x,y in re.findall(r"\('([^']*)', ([\d.]+), ([\d.]+)\)",line):
                x,y=float(x),float(y); skips.append(f"{x-1.2:.2f},{y-1.2:.2f},{x+1.2:.2f},{y+1.2:.2f}")
else:
    print("no clean result"); sys.exit(1)
