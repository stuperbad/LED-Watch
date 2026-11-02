"""figure.py dump.json out.png : the back (B.Cu) around the USB-C receptacle at 3 o'clock, new nets coloured, everything else grey; board edge and receptacle body drawn as outlines"""
import json,sys,math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle, Rectangle
D=json.load(open(sys.argv[1])); X0,X1,Y0,Y1=99.0,122.5,90.0,114.5
NEW={"VBUS":"#e03030","CC1":"#e08a00","CC2":"#c0a000","SBU":"#8a2be2","/UPDI":"#b050d0","ISET":"#00a0a0","TS":"#008060","/BATT":"#2060e0","+3V3":"#e050a0","GND":"#3a8a3a"}
fig,ax=plt.subplots(figsize=(13,13*(Y1-Y0)/(X1-X0)))
ax.add_patch(Circle((100,100),21,fc="#f4efe4",ec="k",lw=1.5))
for t in D["tracks"]:
    if t["layer"]=="B.Cu":
        xs=[q[0] for q in t["poly"]];ys=[q[1] for q in t["poly"]]
        if max(xs)<X0 or min(xs)>X1 or max(ys)<Y0 or min(ys)>Y1: continue
        c=NEW.get(t["net"],"#b9b4a8")
        ax.plot(xs,ys,color=c,lw=2.4 if t["net"] in NEW else 1.3,solid_capstyle="round",zorder=3 if t["net"] in NEW else 2)
for v in D["vias"]:
    if X0<v["p"][0]<X1 and Y0<v["p"][1]<Y1:
        ax.add_patch(Circle(v["p"],v["d"]/2,fc="w",ec=NEW.get(v["net"],"#999"),lw=1.2,zorder=4))
for p in D["pads"]:
    if p["layer"]=="B.Cu" and p["pts"]:
        xs=[q[0] for q in p["pts"]];ys=[q[1] for q in p["pts"]]; cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
        if not(X0<cx<X1 and Y0<cy<Y1): continue
        new=p["ref"].startswith(("J2.","U5.","C55","C56","R68","R69","R70","R71","R72","D50"))
        ax.add_patch(MP(p["pts"],closed=True,fc=NEW.get(p["net"],"#d9d4c8") if new else "#d9d4c8",ec="k" if new else "#999",lw=.6 if new else .3,alpha=.95,zorder=5))
        if new and p["ref"] not in("J2.","J2.SH") and not p["ref"].startswith("J2.A") and not p["ref"].startswith("J2.B"): ax.text(cx,cy,p["ref"].split(".")[0]+"."+p["ref"].split(".")[1],fontsize=5.5,ha="center",va="center",zorder=6)
ax.add_patch(Rectangle((112.0,95.55),8.45,8.9,fc="none",ec="#1060c0",ls="--",lw=1.6,zorder=7))
ax.text(116.2,100.0,"USB-C receptacle\n(GCT USB4110)\nbody, mouth at the rim",ha="center",va="center",fontsize=8,color="#1060c0",zorder=7)
for pl,(x,y,t) in {"v":(112.7,97.6,"VBUS"),}.items(): pass
ax.set_xlim(X0,X1);ax.set_ylim(Y1,Y0);ax.set_aspect("equal");ax.axis("off")
for i,(n,c) in enumerate(NEW.items()): ax.plot([],[],color=c,lw=3,label=n)
ax.legend(loc="lower right",fontsize=8,ncol=2,frameon=True)
ax.set_title("Back side, 3 o'clock: USB-C receptacle, charger and UPDI parts (first-pass mock-up)",fontsize=10)
plt.savefig(sys.argv[2],dpi=110,bbox_inches="tight")
