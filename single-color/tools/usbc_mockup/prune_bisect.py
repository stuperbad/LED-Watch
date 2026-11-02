"""prune_bisect.py in.kicad_pcb out.kicad_pcb : remove every dangling track piece / via the DRC reports (dead ends: traces that go nowhere, vias that connect nothing),
in bulk, and bisect when a bulk removal makes the open-connection count grow, so only pieces that really carry a connection survive.  The owner's old VBAT via at (96.03, 90.87) is kept."""
import json,os,shutil,subprocess,sys,tempfile
K=r"C:\Program Files\KiCad\10.0\bin\python.exe"; KC=r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
HERE=os.path.dirname(os.path.abspath(__file__)); TOOLS=r"C:\Users\evanf\Desktop\LED Watch\single-color\tools"; PRO=os.path.join(HERE,"..","user3.kicad_pro")
w=tempfile.mkdtemp()
def drc(board):
    shutil.copy(PRO,os.path.join(w,"t.kicad_pro")); shutil.copy(PRO,os.path.join(w,"in.kicad_pro"))
    shutil.copy(board,os.path.join(w,"in.kicad_pcb"))
    subprocess.run([K,os.path.join(TOOLS,"refill.py"),os.path.join(w,"in.kicad_pcb"),os.path.join(w,"t.kicad_pcb")],capture_output=True)
    out=os.path.join(w,"d.json"); subprocess.run([KC,"pcb","drc","--severity-all","--format","json","-o",out,os.path.join(w,"t.kicad_pcb")],capture_output=True)
    return json.load(open(out))
def dang(d): return [v for v in d["violations"] if v["type"] in("track_dangling","via_dangling") and not (abs(v["items"][0]["pos"]["x"]-96.025)<.02 and abs(v["items"][0]["pos"]["y"]-90.87)<.02)]
def apply(board,items,out):
    dj=os.path.join(w,"sub.json"); json.dump({"violations":items},open(dj,"w"))
    r=subprocess.run([K,os.path.join(HERE,"..","usbc","prune2.py"),board,dj,out],capture_output=True,text=True); return r.stdout
cur=os.path.join(w,"cur.kicad_pcb"); shutil.copy(sys.argv[1],cur)
d=drc(cur); unc=len(d["unconnected_items"]); items=dang(d); print("start: %d dangling, %d open connections"%(len(items),unc),flush=True)
def attempt(items,depth=0):
    global cur,unc
    if not items: return
    nxt=os.path.join(w,"n%d.kicad_pcb"%(abs(hash(str(items)))%10**8)); apply(cur,items,nxt)
    if not os.path.exists(nxt): return
    d2=drc(nxt); u2=len(d2["unconnected_items"])
    if u2<=unc: shutil.copy(nxt,cur); unc=u2; return
    if len(items)==1: return          # this one carries a connection
    h=len(items)//2; attempt(items[:h],depth+1); attempt(items[h:],depth+1)
for rnd in range(5):
    d=drc(cur); items=dang(d)
    if not items: break
    n0=len(items); attempt(items)
    d=drc(cur); print("round %d: %d dangling -> %d, open connections %d"%(rnd,n0,len(dang(d)),len(d["unconnected_items"])),flush=True)
    if len(dang(d))>=n0: break
shutil.copy(cur,sys.argv[2]); print("wrote",sys.argv[2])
