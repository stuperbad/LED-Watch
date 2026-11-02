"""place4.py : keep the owner's arrangement (u3/pos1.json) but nudge each part to the nearest 0.05 mm spot that clears every copper item that must stay (ring-net vias and B.Cu tracks, all B.Cu pads, the receptacle).  Lane vias / tracks of the MCU columns are removable and are re-routed afterwards."""
import json,math,re
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
U=json.load(open('u3/cu_t1.json')); P=json.load(open('u3/pos1.json'))
ring=lambda n: re.match(r"/(ROW\d+|COL\d+)$",n or "") is not None
NEW=("U5","C55","C56","R68","R69","R70","R71","R72","D50")
obs=[]
for p in U["pads"]:
    if p["layer"]=="B.Cu" and p["pts"] and p["ref"].split(".")[0] not in NEW: obs.append(Polygon(p["pts"]).buffer(0.28))
for t in U["tracks"]:
    if t["layer"]=="B.Cu" and ring(t["net"]): obs.append(LineString(t["poly"]).buffer(t["w"]/2+0.28))
for v in U["vias"]:
    if ring(v["net"]): obs.append(Point(v["p"]).buffer(0.15+0.33))
obs.append(box(111.65,92.8,121.2,107.2))
O=json.load(open("usbc/outline.json"))[0]; board=Polygon(O["outer"],O["holes"]).buffer(-0.4)
tr=STRtree(obs)
S={"U5":(3.3,2.7),"C55":(1.7,1.0),"C56":(1.7,1.0),"R68":(1.7,1.0),"R69":(1.7,1.0),"R70":(1.7,1.0),"R71":(1.7,1.0),"R72":(1.7,1.0),"D50":(2.7,1.2)}
placed=[];out={}
for ref in ("U5","D50","R72","R69","R68","C55","R70","C56","R71"):
    x0,y0,a=P[ref]; w,h=S[ref]; ww,hh=(w,h) if a==0 else (h,w); best=None
    for xi in range(-40,41):
        for yi in range(-40,41):
            x=round(x0+xi*0.05,2); y=round(y0+yi*0.05,2)
            g=box(x-ww/2,y-hh/2,x+ww/2,y+hh/2)
            if not board.contains(g): continue
            if any(obs[j].intersects(g) for j in tr.query(g)) or any(g.intersects(q) for q in placed): continue
            d=math.hypot(x-x0,y-y0)
            if best is None or d<best[0]: best=(d,x,y,g)
    if best is None: print("NO SPOT",ref); continue
    d,x,y,g=best; placed.append(g.buffer(0.2)); out[ref]=(x,y,a); print(ref,"owner",(x0,y0),"->",(x,y),"moved %.2f"%d)
json.dump(out,open("u3/pos2.json","w"))
