"""viamove.py REF[,REF..] : move the lane via of the given ROW stubs along the lane to the nearest spot that keeps clear of the receptacle's shell tabs / contact pads, and re-draw the F.Cu stub with ring_stubs.py.
tries candidate angles nearest first; prints the first that gets a path.  writes usbc/vm_<REF>.json (remove/add incl. via)"""
import json,math,subprocess,sys,os
from shapely.geometry import Polygon,LineString,Point,box
T="C:/Users/evanf/Desktop/LED Watch/single-color/tools"
G=json.load(open("g_c0.json")); S=json.load(open("u4/stubs_c0.json")); M=json.load(open("u4/cu_final.json"))
refs=sys.argv[1].split(","); prior=sys.argv[2] if len(sys.argv)>2 else ""
chosen=[tuple(v) for v in (json.load(open("u4/vm_chosen.json")) if os.path.exists("u4/vm_chosen.json") else [])]
tabs=[Polygon(p["pts"]).envelope for p in M["pads"] if p["ref"]=="J2.SH" and p["layer"]=="B.Cu"]
contact=[Polygon(p["pts"]) for p in M["pads"] if p["ref"].startswith(("J2.A","J2.B")) and p["layer"]=="B.Cu" and p["pts"]]
peg=[Point(h["p"]).buffer(h["r"]) for h in M["holes"] if 112.5<h["p"][0]<115 and 95<h["p"][1]<105]
body=tabs+contact+peg
def other_f(net):
    out=[]
    for t in G["trk"]:
        if t["layer"]=="F.Cu" and t["net"]!=net: out.append(LineString([(t["x1"],t["y1"]),(t["x2"],t["y2"])]).buffer(t["w"]/2))
    for p in G["pads"]:
        if p["layer"]=="F.Cu" and p["net"]!=net and len(p["pts"])>2: out.append(Polygon(p["pts"]).buffer(0))
    for v in G["via"]:
        if v["net"]!=net: out.append(Point(v["x"],v["y"]).buffer(v["d"]/2))
    for c in chosen: out.append(Point(c).buffer(0.15))
    return out
for ref in refs:
    st=next(s for s in S if s["ref"]==ref and s["pad"]=="1"); net=st["net"]; v0=st["via"]
    r=math.hypot(v0[0]-100,v0[1]-100); th0=math.degrees(math.atan2(v0[1]-100,v0[0]-100))
    obs=other_f(net)
    cand=[]
    for k in range(-400,401):
        th=th0+k*0.1
        if abs(th)>45: continue
        p=(100+r*math.cos(math.radians(th)),100+r*math.sin(math.radians(th))); pt=Point(p)
        if any(pt.distance(b)<0.32 for b in body): continue
        if any(pt.distance(o)<0.28 for o in obs): continue
        cand.append((abs(th-th0),th,p))
    cand.sort()
    print(ref,net,"old",[round(c,3) for c in v0],"r %.3f th %.2f"%(r,th0),len(cand),"candidates")
    done=False
    for _,th,p in cand[:200]:
        s2=dict(st); s2["via"]=[p[0],p[1]]; s2["endpoint"]=[p[0],p[1]]
        json.dump([s2],open("u4/vm_stub.json","w"))
        cmd=["python",T+"/ring_stubs.py","g_c0.json","u4/vm_stub.json","u4/vm_edit.json","--only",ref,"--own",os.environ.get("OWN","0.17"),"--min-seg",os.environ.get("MINSEG","0.15"),"--ext","0.25,0.3,0.4,0.5,0.6,0.8","--first-turn",os.environ.get("FT","90"),"--kmax",os.environ.get("KMAX","6")]
        if prior: cmd+=["--prior",prior]
        out=subprocess.run(cmd,capture_output=True,text=True).stdout
        E=json.load(open("u4/vm_edit.json"))
        pr_add=[];pr_rem=[]
        for f in [f for f in prior.split(",") if f]:
            P=json.load(open(f)); pr_add+=P["add"]; pr_rem+=P["remove"]
        E["add"]=[a for a in E["add"] if a not in pr_add]; E["remove"]=[a for a in E["remove"] if a not in pr_rem]
        if E["add"]:
            E["remove"].append(["via",net,[v0[0],v0[1]]]); E["add"].append(["via",net,[p[0],p[1]]])
            json.dump(E,open("u4/vm_%s.json"%ref,"w")); chosen.append(p); json.dump(chosen,open("u4/vm_chosen.json","w"))
            print("  OK th %.2f via (%.3f,%.3f) moved %.2f mm"%(th,p[0],p[1],math.dist(p,v0)),len(E["add"]),"pieces"); done=True; break
    if not done: print("  no path found for",ref)
