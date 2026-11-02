"""shvias.py : one GND via inside each shell tab (via-in-pad), at the point with the most room to other-net copper on F.Cu / In1 / B.Cu; writes usbc/shvias.json for apply_ring_edits.py"""
import json,math
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
M=json.load(open('usbc/cu_m1.json'))
cop=[]
for t in M["tracks"]:
    if t["net"]!="GND" and t["layer"] in("F.Cu","In1.Cu","B.Cu"): cop.append(LineString(t["poly"]).buffer(t["w"]/2))
for p in M["pads"]:
    if p["pts"] and p["net"]!="GND" and p["layer"] in("F.Cu","In1.Cu","B.Cu"): cop.append(Polygon(p["pts"]).buffer(0))
for v in M["vias"]:
    if v["net"]!="GND": cop.append(Point(v["p"]).buffer(v["d"]/2))
tr=STRtree(cop)
add=[]
for p in M["pads"]:
    if p["ref"]=="J2.SH" and p["layer"]=="B.Cu":
        g=Polygon(p["pts"]).buffer(0).buffer(-0.45)
        x0,y0,x1,y1=g.bounds; best=None
        x=x0
        while x<=x1:
            y=y0
            while y<=y1:
                if g.contains(Point(x,y)):
                    c=Point(x,y).buffer(0.15)
                    d=min((c.distance(cop[j]) for j in tr.query(c.buffer(0.6))),default=9)
                    if best is None or d>best[0]: best=(d,x,y)
                y+=0.05
            x+=0.05
        print(round(best[1],2),round(best[2],2),"room %.2f"%best[0])
        if best[1]<115: add.append(["via","GND",[round(best[1],3),round(best[2],3)]])
add+=[["B.Cu","GND",[114.0,94.3],[116.7,94.3]],["B.Cu","GND",[114.0,105.1],[117.6,105.1]]]   # tie the outboard shell tabs to the inboard ones
json.dump({"remove":[],"add":add},open("usbc/shvias.json","w"))
