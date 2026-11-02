"""prep2.py cu.json : shell-tab ground (via-in-pad in the inboard tabs, strips tying the outboard tabs) and the UPDI via on the In1 lane nearest R72 pin 2 -> u4/extra.json"""
import json,math
from shapely.geometry import Polygon,LineString,Point
M=json.load(open(__import__("sys").argv[1]))
tabs=[(Polygon(p["pts"]).buffer(0),p) for p in M["pads"] if p["ref"]=="J2.SH" and p["layer"]=="B.Cu"]
cop=[]
for t in M["tracks"]:
    if t["net"]!="GND" and t["layer"] in("F.Cu","In1.Cu","B.Cu"): cop.append(LineString(t["poly"]).buffer(t["w"]/2))
for p in M["pads"]:
    if p["pts"] and p["net"]!="GND" and p["layer"] in("F.Cu","In1.Cu","B.Cu"): cop.append(Polygon(p["pts"]).buffer(0))
for v in M["vias"]:
    if v["net"]!="GND": cop.append(Point(v["p"]).buffer(v["d"]/2))
add=[]
left=[g for g,p in tabs if g.centroid.x<115]; right=[g for g,p in tabs if g.centroid.x>115]
for g in left:
    gi=g.buffer(-0.45); x0,y0,x1,y1=gi.bounds; best=None; x=x0
    while x<=x1:
        y=y0
        while y<=y1:
            if gi.contains(Point(x,y)):
                c=Point(x,y).buffer(0.15); d=min((c.distance(o) for o in cop if o.distance(c)<0.8),default=9)
                if best is None or d>best[0]: best=(d,x,y)
            y+=0.05
        x+=0.05
    print("tab via",round(best[1],2),round(best[2],2),"room %.2f"%best[0]); add.append(["via","GND",[round(best[1],3),round(best[2],3)]])
for gl in left:
    gr=min(right,key=lambda r:abs(r.centroid.y-gl.centroid.y))
    y=round(gl.bounds[1]+0.5,3) if gl.centroid.y<100 else round(gl.bounds[3]-1.1,3)
    add.append(["B.Cu","GND",[round(gl.centroid.x,3),y],[round(gr.centroid.x,3),y]])
# UPDI via: lane pieces of /UPDI on In1
r72=[Polygon(p["pts"]) for p in M["pads"] if p["ref"]=="R72.2"][0]
obs=[o for o in []]
oc=[]
for t in M["tracks"]:
    if t["net"]!="/UPDI" and t["layer"] in("F.Cu","B.Cu"): oc.append(LineString(t["poly"]).buffer(t["w"]/2))
for p in M["pads"]:
    if p["pts"] and p["net"]!="/UPDI" and p["layer"] in("F.Cu","B.Cu"): oc.append(Polygon(p["pts"]).buffer(0))
for v in M["vias"]:
    if v["net"]!="/UPDI": oc.append(Point(v["p"]).buffer(v["d"]/2))
best=None
for t in M["tracks"]:
    if t["net"]=="/UPDI" and t["layer"]=="In1.Cu" and t["k"]=="seg":
        L=math.dist(t["a"],t["b"]); n=int(L/0.05)
        for i in range(n+1):
            p=(t["a"][0]+(t["b"][0]-t["a"][0])*i/n,t["a"][1]+(t["b"][1]-t["a"][1])*i/n); pt=Point(p)
            if min(pt.distance(o) for o in oc)>=0.29:
                d=pt.distance(r72)
                if best is None or d<best[0]: best=(d,p)
print("UPDI via",best)
if best: add.append(["via","/UPDI",[round(best[1][0],3),round(best[1][1],3)]])
json.dump({"remove":[],"add":add},open("u4/extra.json","w"))
