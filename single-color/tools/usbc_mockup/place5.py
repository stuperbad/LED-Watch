"""place5.py : U5 on the upper row of the low side with C55 and R71 (rotated, same row) below it; R69 next to the CC2 pad; R68, R72, D50, R70, C56 on the high side.  Everything on the 0.05 mm grid, clear of the copper that must stay."""
import json,math,re
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
U=json.load(open('u3/cu_t1.json'))
ring=lambda n: re.match(r"/(ROW\d+|COL\d+)$",n or "") is not None
NEW=("U5","C55","C56","R68","R69","R70","R71","R72","D50")
obs=[]
for p in U["pads"]:
    if p["layer"]=="B.Cu" and p["pts"] and p["ref"].split(".")[0] not in NEW: obs.append(Polygon(p["pts"]).buffer(0.28))
for t in U["tracks"]:
    if t["layer"]=="B.Cu" and ring(t["net"]): obs.append(LineString(t["poly"]).buffer(t["w"]/2+0.28))
for v in U["vias"]:
    if ring(v["net"]) and not (v["net"]=="/COL4"): obs.append(Point(v["p"]).buffer(0.48))
obs.append(box(111.65,92.8,121.2,107.2))
obs.append(Point(108.83,97.08).buffer(0.9))      # landing of the UPDI lane (In1) - keep the back free there
O=json.load(open("usbc/outline.json"))[0]; board=Polygon(O["outer"],O["holes"]).buffer(-0.4); tr=STRtree(obs)
S={"U5":(3.3,2.7),"C55":(1.7,1.0),"C56":(1.7,1.0),"R68":(1.7,1.0),"R69":(1.7,1.0),"R70":(1.7,1.0),"R71":(1.7,1.0),"R72":(1.7,1.0),"D50":(2.7,1.2)}
def bx(ref,x,y,a): w,h=S[ref]; ww,hh=(w,h) if a==0 else (h,w); return box(x-ww/2,y-hh/2,x+ww/2,y+hh/2)
def ok(g,placed): return board.contains(g) and not any(obs[j].intersects(g) for j in tr.query(g)) and not any(g.intersects(q) for q in placed)
placed=[];out={}
def single(ref,x0,y0,a,R=2.0):
    best=None
    for xi in range(int(-R/0.05),int(R/0.05)+1):
        for yi in range(int(-R/0.05),int(R/0.05)+1):
            x=round(x0+xi*0.05,2);y=round(y0+yi*0.05,2);g=bx(ref,x,y,a)
            if ok(g,placed):
                d=math.hypot(x-x0,y-y0)
                if best is None or d<best[0]: best=(d,x,y,g)
    if best is None: print("NO SPOT",ref); return
    d,x,y,g=best; placed.append(g.buffer(0.25)); out[ref]=(x,y,a); print(ref,(x,y,a),"from anchor %.2f"%d)
def pair(r1,r2,x1,x2,y0,a,R=1.6,vertical=False):
    best=None; pitch=abs(x2-x1)
    for yi in range(int(-R/0.05),int(R/0.05)+1):
        for xi in range(int(-R/0.05),int(R/0.05)+1):
            if vertical: p1=(round(x1+xi*0.05,2),round(y0+yi*0.05,2)); p2=(p1[0],round(p1[1]-pitch,2))
            else: p1=(round(x1+xi*0.05,2),round(y0+yi*0.05,2)); p2=(round(p1[0]+pitch,2),p1[1])
            g1=bx(r1,*p1,a); g2=bx(r2,*p2,a)
            if ok(g1,placed) and ok(g2,placed) and not g1.buffer(0.2).intersects(g2):
                d=math.hypot(p1[0]-x1,p1[1]-y0)
                if best is None or d<best[0]: best=(d,p1,p2,g1,g2)
    if best is None: print("NO SPOT pair",r1,r2); return
    d,p1,p2,g1,g2=best; placed.extend([g1.buffer(0.25),g2.buffer(0.25)]); out[r1]=(p1[0],p1[1],a); out[r2]=(p2[0],p2[1],a); print(r1,r2,p1,p2)
best=None
for a in (0,90):
    for xi in range(-80,81):
        for yi in range(-60,81):
            x=round(108.95+xi*0.05,2);y=round(103.4+yi*0.05,2);g=bx("U5",x,y,a)
            if ok(g,placed):
                d=math.hypot(x-108.95,y-103.4)
                if best is None or d<best[0]: best=(d,x,y,a,g)
print("U5 best",best[:4] if best else None)
if best: placed.append(best[4].buffer(0.25)); out["U5"]=(best[1],best[2],best[3])
pair("C55","R71",108.4,110.4,105.9,0)
single("R69",110.75,101.5,90)
single("R68",110.35,96.85,0)
single("R72",110.75,98.7,90)
single("D50",110.25,94.4,90)
single("R70",108.4,95.2,90,R=3.0)
single("C56",108.4,93.4,90,R=3.0)
json.dump(out,open("u3/pos3b.json","w"))
