"""place2.py : keep the charger cluster (U5, C55, C56, R70, R71) where place.py put it, and put the CC resistors, the SBU series resistor and the UPDI clamp next to the connector pads"""
import json, math
from shapely.geometry import Polygon, LineString, Point, box
M=json.load(open('usbc/cu_m1.json')); E=json.load(open('usbc/clear1.json')); P=json.load(open('usbc/place_v1.json'))
O=json.load(open("usbc/outline.json"))[0]; board=Polygon(O["outer"],O["holes"]).buffer(-0.4)
rem={(r[0],r[1],tuple(sorted([tuple(round(c,3) for c in r[2]),tuple(round(c,3) for c in r[3])]))) for r in E["remove"] if r[0]!="via"}
remv={(r[1],round(r[2][0],3),round(r[2][1],3)) for r in E["remove"] if r[0]=="via"}
NEWP=("U5.","C55","C56","R68","R69","R70","R71","R72","D50")
obs=[]
for p in M["pads"]:
    if p["layer"]=="B.Cu" and p["pts"] and not p["ref"].startswith(NEWP): obs.append(Polygon(p["pts"]).buffer(0.25))
for t in M["tracks"]:
    if t["layer"]!="B.Cu": continue
    if t["k"]=="seg" and (t["layer"],t["net"],tuple(sorted([tuple(round(c,3) for c in t["a"]),tuple(round(c,3) for c in t["b"])]))) in rem: continue
    obs.append(LineString(t["poly"]).buffer(t["w"]/2+0.25))
for v in M["vias"]:
    if (v["net"],round(v["p"][0],3),round(v["p"][1],3)) in remv: continue
    obs.append(Point(v["p"]).buffer(0.15+0.3))
obs.append(box(111.65,92.8,121.2,107.2))
S={"U5":(3.2,2.7),"C55":(1.7,1.0),"C56":(1.7,1.0),"R68":(1.7,1.0),"R69":(1.7,1.0),"R70":(1.7,1.0),"R71":(1.7,1.0),"R72":(1.7,1.0),"D50":(2.7,1.2)}
placed=[]; out={}
for ref in ("U5","C55","C56","R70","R71"):
    x,y,a=P[ref]; w,h=S[ref]; ww,hh=(w,h) if a==0 else (h,w)
    placed.append(box(x-ww/2,y-hh/2,x+ww/2,y+hh/2).buffer(0.15)); out[ref]=(x,y,a)
anch={"R69":(110.6,102.3),"R72":(110.6,104.2),"D50":(109.4,104.6),"R68":(110.6,100.6)}
for ref in ("R69","R72","D50","R68"):
    w,h=S[ref]; best=None
    for a in (0,90):
        ww,hh=(w,h) if a==0 else (h,w)
        for xi in range(-40,41):
            for yi in range(-40,41):
                x=anch[ref][0]+xi*0.1; y=anch[ref][1]+yi*0.1
                g=box(x-ww/2,y-hh/2,x+ww/2,y+hh/2)
                if not board.contains(g) or any(g.intersects(o) for o in obs) or any(g.intersects(q) for q in placed): continue
                d=math.hypot(x-anch[ref][0],y-anch[ref][1])
                if best is None or d<best[0]: best=(d,x,y,a,g)
    if best is None: print("NO SPOT",ref); continue
    _,x,y,a,g=best; placed.append(g.buffer(0.15)); out[ref]=(round(x,2),round(y,2),a)
print(out); json.dump(out,open("usbc/place.json","w"))
