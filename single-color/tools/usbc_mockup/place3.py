import json,math
from shapely.geometry import Polygon,LineString,Point,box
U=json.load(open('u2/cu_u0.json')); E=json.load(open('u2/rm_mine.json'))
rem={(r[0],r[1],tuple(sorted([tuple(round(c,2) for c in r[2]),tuple(round(c,2) for c in r[3])]))) for r in E["remove"] if r[0]!="via"}
remv={(r[1],round(r[2][0],2),round(r[2][1],2)) for r in E["remove"] if r[0]=="via"}
MOVE=("R68.","R72.","D50.")
obs=[]
for p in U["pads"]:
    if p["layer"]=="B.Cu" and p["pts"] and not p["ref"].startswith(MOVE): obs.append(Polygon(p["pts"]).buffer(0.25))
for t in U["tracks"]:
    if t["layer"]!="B.Cu": continue
    if t["k"]=="seg" and (t["layer"],t["net"],tuple(sorted([tuple(round(c,2) for c in t["a"]),tuple(round(c,2) for c in t["b"])]))) in rem: continue
    obs.append(LineString(t["poly"]).buffer(t["w"]/2+0.25))
for v in U["vias"]:
    if (v["net"],round(v["p"][0],2),round(v["p"][1],2)) in remv: continue
    obs.append(Point(v["p"]).buffer(0.45))
obs.append(box(111.65,92.8,121.2,107.2))
O=json.load(open("usbc/outline.json"))[0]; board=Polygon(O["outer"],O["holes"]).buffer(-0.4)
S={"R68":(1.7,1.0),"R72":(1.7,1.0),"D50":(2.7,1.2)}
anch={"R68":(110.6,97.2),"R72":(110.6,95.4),"D50":(109.5,93.8)}
placed=[];out={}
for ref in ("R68","R72","D50"):
    w,h=S[ref];best=None
    for a in (0,90):
        ww,hh=(w,h) if a==0 else (h,w)
        for xi in range(-50,51):
            for yi in range(-40,41):
                x=anch[ref][0]+xi*0.1;y=anch[ref][1]+yi*0.1
                g=box(x-ww/2,y-hh/2,x+ww/2,y+hh/2)
                if not board.contains(g) or any(g.intersects(o) for o in obs) or any(g.intersects(q) for q in placed): continue
                d=math.hypot(x-anch[ref][0],y-anch[ref][1])
                if best is None or d<best[0]: best=(d,x,y,a,g)
    if best is None: print("NO SPOT",ref);continue
    _,x,y,a,g=best;placed.append(g.buffer(0.15));out[ref]=(round(x,2),round(y,2),a)
print(out);json.dump(out,open("u2/place3.json","w"))
