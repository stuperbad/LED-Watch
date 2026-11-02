"""clear_gen.py cu.json refs.txt out.json : remove the straight tracks and (non-ring) vias of other nets that meet the pads of the listed refs (+ J2); ring vias are only reported"""
import json,re,sys
from shapely.geometry import Polygon,LineString,Point
D=json.load(open(sys.argv[1])); refs=set(open(sys.argv[2]).read().split())|{"J2"}
pads=[p for p in D["pads"] if p["ref"].split(".")[0] in refs and p["pts"]]
CL=0.22; rem=[]; nets=set(); ring=lambda n: re.match(r"/(ROW\d+|COL\d+)$",n or "") is not None
for L in ("F.Cu","In1.Cu","B.Cu"):
    zs=[(p["net"],Polygon(p["pts"]).buffer(CL)) for p in pads if p["layer"]==L]
    for t in D["tracks"]:
        if t["layer"]!=L or t["k"]=="arc": continue
        g=LineString(t["poly"]).buffer(t["w"]/2)
        for n,z in zs:
            if n==t["net"] and n: continue
            if g.intersects(z): rem.append([L,t["net"],list(t["a"]),list(t["b"])]); nets.add(t["net"]); break
arcs=[t["net"] for t in D["tracks"] if t["k"]=="arc" and t["layer"] in("F.Cu","In1.Cu","B.Cu") and any(LineString(t["poly"]).buffer(t["w"]/2).intersects(Polygon(p["pts"]).buffer(CL)) for p in pads if p["layer"]==t["layer"] and p["net"]!=t["net"])]
for h in D["holes"]:
    if 112<h["p"][0]<119 and 93<h["p"][1]<107 and h["r"]>0.2:
        z=Point(h["p"]).buffer(h["r"]+0.3)
        for t in D["tracks"]:
            if t["k"]=="seg" and LineString(t["poly"]).buffer(t["w"]/2).intersects(z): rem.append([t["layer"],t["net"],list(t["a"]),list(t["b"])]); nets.add(t["net"])
vrem=[]
for v in D["vias"]:
    c=Point(v["p"]).buffer(0.15)
    if any(Polygon(p["pts"]).buffer(CL).intersects(c) and p["net"]!=v["net"] for p in pads):
        if ring(v["net"]): print("RING VIA CONFLICT (not removed)",v["net"],v["p"]); continue
        vrem.append(["via",v["net"],list(v["p"])]); nets.add(v["net"])
seen=set(); R=[]
for r in rem:
    k=(r[0],r[1],tuple(round(c,3) for c in r[2]),tuple(round(c,3) for c in r[3]))
    if k not in seen: seen.add(k); R.append(r)
json.dump({"remove":R+vrem,"add":[]},open(sys.argv[3],"w")); print("remove",len(R),"pieces,",len(vrem),"vias; nets opened:",sorted(nets),"| arcs hit:",sorted(set(arcs)))
