"""place7.py : owner's layout (connector at x 116.05) with the swaps agreed: bottom row R71 (TS, under pin 1) and C55 (VBUS cap, under pin 6); R70 above-right next to ISET pin 4; C56 left of U5 beside the battery pin; R72 as close to the SBU pads as it fits.  0.05 mm grid."""
import json,math,re
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
U=json.load(open('u4/cu_user.json'))
ring=lambda n: re.match(r"/(ROW\d+|COL\d+)$",n or "") is not None
NEW=("U5","C55","C56","R68","R69","R70","R71","R72","D50")
obs=[]
for p in U["pads"]:
    if p["layer"]=="B.Cu" and p["pts"] and p["ref"].split(".")[0] not in NEW: obs.append(Polygon(p["pts"]).buffer(0.28))
for t in U["tracks"]:
    if t["layer"]=="B.Cu" and ring(t["net"]): obs.append(LineString(t["poly"]).buffer(t["w"]/2+0.28))
for v in U["vias"]:
    if ring(v["net"]) and v["net"]!="/COL4": obs.append(Point(v["p"]).buffer(0.48))
obs.append(box(111.35,92.8,121.2,107.2))
O=json.load(open("usbc/outline.json"))[0]; board=Polygon(O["outer"],O["holes"]).buffer(-0.4); tr=STRtree(obs)
S={"U5":(3.3,2.7),"C55":(1.7,1.0),"C56":(1.7,1.0),"R68":(1.7,1.0),"R69":(1.7,1.0),"R70":(1.7,1.0),"R71":(1.7,1.0),"R72":(1.7,1.0),"D50":(2.7,1.2)}
def bx(ref,x,y,a): w,h=S[ref]; ww,hh=(w,h) if a==0 else (h,w); return box(x-ww/2,y-hh/2,x+ww/2,y+hh/2)
placed=[];out={}
def single(ref,x0,y0,a,R=2.0):
    best=None
    for xi in range(int(-R/0.05),int(R/0.05)+1):
        for yi in range(int(-R/0.05),int(R/0.05)+1):
            x=round(x0+xi*0.05,2);y=round(y0+yi*0.05,2);g=bx(ref,x,y,a)
            if board.contains(g) and not any(obs[j].intersects(g) for j in tr.query(g)) and not any(g.intersects(q) for q in placed):
                d=math.hypot(x-x0,y-y0)
                if best is None or d<best[0]: best=(d,x,y,g)
    if best is None: print("NO SPOT",ref); return
    d,x,y,g=best; placed.append(g.buffer(0.25)); out[ref]=(x,y,a); print(ref,(x,y,a),"from anchor %.2f"%d)
single("U5",108.5,104.5,0,R=0.5)
single("R71",107.5,107.0,0,R=0.6)
single("C55",109.5,107.0,0,R=0.6)
single("C56",106.0,104.5,90,R=1.5)
single("R70",110.5,101.25,90,R=1.2)
single("R69",110.5,98.75,90,R=1.0)
single("R72",110.5,100.0,90,R=2.5)
single("R68",109.5,96.5,0,R=1.0)
single("D50",109.5,94.0,90,R=1.0)
json.dump(out,open("u4/pos.json","w"))
