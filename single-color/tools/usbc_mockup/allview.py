import json,sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
D=json.load(open(sys.argv[1])); X0,X1,Y0,Y1=[float(a) for a in sys.argv[3:7]]
fig,ax=plt.subplots(figsize=(12,12*(Y1-Y0)/(X1-X0)))
COL={"F.Cu":"#d33","In1.Cu":"#2a2","B.Cu":"#36c","In2.Cu":"#aaa"}
for p in D["pads"]:
    if p["layer"]=="B.Cu" and p["pts"]:
        xs=[q[0] for q in p["pts"]];ys=[q[1] for q in p["pts"]];cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
        if X0<cx<X1 and Y0<cy<Y1:
            ax.add_patch(MP(p["pts"],closed=True,fc="#cde",ec="k",lw=.5)); ax.text(cx,cy,p["ref"]+"\n"+p["net"],fontsize=4.5,ha="center",va="center")
for t in D["tracks"]:
    if t["layer"] in COL and t["layer"]!="In2.Cu":
        xs=[q[0] for q in t["poly"]];ys=[q[1] for q in t["poly"]]
        if max(xs)<X0 or min(xs)>X1 or max(ys)<Y0 or min(ys)>Y1: continue
        ax.plot(xs,ys,color=COL[t["layer"]],lw=1.5,alpha=.8,solid_capstyle="round")
        ax.text(sum(xs)/len(xs),sum(ys)/len(ys),t["net"],fontsize=3.5,color=COL[t["layer"]])
for v in D["vias"]:
    if X0<v["p"][0]<X1 and Y0<v["p"][1]<Y1: ax.add_patch(Circle(v["p"],v["d"]/2,fc="w",ec="m",lw=1)); ax.text(v["p"][0],v["p"][1]+0.25,v["net"],fontsize=3.5,color="m")
ax.set_xlim(X0,X1);ax.set_ylim(Y1,Y0);ax.set_aspect("equal");ax.grid(alpha=.2)
plt.savefig(sys.argv[2],dpi=110,bbox_inches="tight")
