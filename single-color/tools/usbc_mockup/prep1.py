import json
U=json.load(open('u3/cu_q8c.json')); B=json.load(open('usbc/cu_base.json'))
def key(t): return (t["layer"],t["net"],tuple(sorted([tuple(round(c,2) for c in t["a"]),tuple(round(c,2) for c in t["b"])])),t["k"])
kb={key(t) for t in B["tracks"]}; vb={(v["net"],round(v["p"][0],2),round(v["p"][1],2)) for v in B["vias"]}
NETS={"CC1","CC2","SBU","/UPDI","+3V3","VBUS","ISET","TS","/BATT","GND"}
def ok(net,x,y): return net in NETS and (net!="GND" or (x<112.5 or (x<118.8 and 92<y<108)))
rem=[]
for t in U["tracks"]:
    if key(t) in kb or t["k"]=="arc": continue
    if ok(t["net"],min(t["a"][0],t["b"][0]),t["a"][1]): rem.append([t["layer"],t["net"],list(t["a"]),list(t["b"])])
for v in U["vias"]:
    if (v["net"],round(v["p"][0],2),round(v["p"][1],2)) in vb: continue
    if ok(v["net"],v["p"][0],v["p"][1]) or (v["net"]=="/COL4" and v["p"] in ([108.825,104.985],[111.475,106.185])): rem.append(["via",v["net"],list(v["p"])])
print(len(rem),"to remove")
json.dump({"remove":rem,"add":[]},open('u4/rm1.json','w'))
P=json.load(open('u4/pos.json')); P["J2"]=(116.05,100.0,270); json.dump(P,open('u4/pos_all.json','w'))
