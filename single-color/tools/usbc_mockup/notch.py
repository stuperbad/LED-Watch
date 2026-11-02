"""notch.py : shell tab polygons for build.py / fixpad.py.  All four tabs are the library rectangles (lower outboard tab rebuilt from the upper outboard tab's x range and the lower inboard tab's y range).
TRIM=1 trims the lower outboard tab to x >= 117.3 (clears the ROW3 / ROW4 vias of M17 / M18).  writes usbc/notch.json = [{c, pts}] (absolute polygons)"""
import json,os
from shapely.geometry import Polygon,box
M=json.load(open('usbc/cu_m1.json')); tabs=[]
for p in M["pads"]:
    if p["ref"]=="J2.SH" and p["layer"]=="B.Cu":
        e=Polygon(p["pts"]).buffer(0).envelope; tabs.append(e)
ur=next(t for t in tabs if t.centroid.x>115 and t.centroid.y<100); ll=next(t for t in tabs if t.centroid.x<115 and t.centroid.y>100)
res=[]
for t in tabs:
    c=(t.centroid.x,t.centroid.y)
    if c[0]>115 and c[1]>100:
        c=(ur.bounds[0]+ (ur.bounds[2]-ur.bounds[0])/2, ll.centroid.y)
        t=box(ur.bounds[0],ll.bounds[1],ur.bounds[2],ll.bounds[3])
        if os.environ.get("TRIM"): t=t.intersection(box(117.3,0,200,200))
        c=(t.centroid.x,t.centroid.y) if False else (ur.centroid.x,ll.centroid.y)
    res.append({"c":list(c),"pts":list(t.exterior.coords)[:-1],"area":t.area})
for r in res: print([round(x,2) for x in r["c"]],round(r["area"],2))
json.dump(res,open('usbc/notch.json','w'))
