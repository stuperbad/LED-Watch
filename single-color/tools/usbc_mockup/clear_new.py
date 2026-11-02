"""clear_new.py cu.json edit.json : remove the existing straight tracks and vias that overlap (or come within clearance of) the pads of the new parts; prints the nets that are opened"""
import json, math, sys
from shapely.geometry import Polygon, LineString, Point
D=json.load(open(sys.argv[1])); out=sys.argv[2]
NEW=("J2.","U5.","C55.","C56.","R68.","R69.","R70.","R71.","R72.","D50.")
newpads=[p for p in D["pads"] if p["ref"].startswith(NEW)]
holes=[]
for p in D["pads"]:
    if p["ref"].startswith(NEW) and p["hole"]>0: pass
newnets={p["net"] for p in newpads}
rem=[]; nets=set(); arcs=[]
CL=0.22
for L in ("F.Cu","In1.Cu","B.Cu"):
    zones=[(p["net"],Polygon(p["pts"]).buffer(CL)) for p in newpads if p["layer"]==L]
    for t in D["tracks"]:
        if t["layer"]!=L: continue
        g=LineString(t["poly"]).buffer(t["w"]/2)
        for n,z in zones:
            if n==t["net"] and n: continue
            if g.intersects(z):
                if t["k"]=="arc": arcs.append((t["net"],L))
                else: rem.append([L,t["net"],list(t["a"]),list(t["b"])]); nets.add(t["net"])
                break
# NPTH holes (no copper pad): through all layers
for p in D["pads"]:
    pass
for h in D["holes"]:
    if 113<h["p"][0]<121 and 93<h["p"][1]<107 and h["r"]>0.2:
        z=Point(h["p"]).buffer(h["r"]+0.3)
        for t in D["tracks"]:
            if LineString(t["poly"]).buffer(t["w"]/2).intersects(z):
                if t["k"]=="arc": arcs.append((t["net"],t["layer"]))
                else: rem.append([t["layer"],t["net"],list(t["a"]),list(t["b"])]); nets.add(t["net"])
vrem=[]
for v in D["vias"]:
    c=Point(v["p"]).buffer(0.15)
    hit=False
    for L in ("F.Cu","In1.Cu","B.Cu"):
        for p in newpads:
            if p["layer"]==L and Polygon(p["pts"]).buffer(CL).intersects(c) and p["net"]!=v["net"]: hit=True
    for h in D["holes"]:
        if 113<h["p"][0]<121 and 93<h["p"][1]<107 and h["r"]>0.2 and Point(h["p"]).buffer(h["r"]+0.3).intersects(c): hit=True
    if hit:
        import re as _re
        if _re.match(r"/(ROW\d+|COL\d+)$",v["net"]): print("RING VIA CONFLICT (not removed)",v["net"],v["p"]); continue
        vrem.append(["via",v["net"],list(v["p"])]); nets.add(v["net"])
# dedupe straight pieces
seen=set(); R=[]
for r in rem:
    k=(r[0],r[1],tuple(round(c,3) for c in r[2]),tuple(round(c,3) for c in r[3]))
    if k in seen: continue
    seen.add(k); R.append(r)
json.dump({"remove":R+vrem,"add":[]},open(out,"w"))
print("remove",len(R),"pieces,",len(vrem),"vias; nets opened:",sorted(nets)); print("ARCS HIT:",sorted(set(arcs)))
