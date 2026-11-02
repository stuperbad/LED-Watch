"""nview.py dump.json out.png x0 x1 y0 y1 NET,NET.. : B.Cu solid, F.Cu dashed, In1 dotted for the given nets (labelled); everything else B.Cu light grey"""
import json,sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
D=json.load(open(sys.argv[1])); X0,X1,Y0,Y1=[float(a) for a in sys.argv[3:7]]; NETS=sys.argv[7].split(",")
fig,ax=plt.subplots(figsize=(12,12*(Y1-Y0)/(X1-X0)))
C={n:plt.cm.tab10(i%10) for i,n in enumerate(NETS)}
for p in D["pads"]:
    if p["layer"]=="B.Cu" and p["pts"]:
        xs=[q[0] for q in p["pts"]];ys=[q[1] for q in p["pts"]]
        cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
        if X0<cx<X1 and Y0<cy<Y1:
            ax.add_patch(MP(p["pts"],closed=True,fc=C.get(p["net"],"#ddd"),ec="#888",lw=.4,alpha=.6))
            ax.text(cx,cy,p["ref"],fontsize=5,ha="center",va="center")
LS={"B.Cu":"-","F.Cu":"--","In1.Cu":":"}
for t in D["tracks"]:
    xs=[q[0] for q in t["poly"]];ys=[q[1] for q in t["poly"]]
    if max(xs)<X0 or min(xs)>X1 or max(ys)<Y0 or min(ys)>Y1: continue
    if t["net"] in C and t["layer"] in LS: ax.plot(xs,ys,LS[t["layer"]],color=C[t["net"]],lw=2.2,solid_capstyle="round")
    elif t["layer"]=="B.Cu": ax.plot(xs,ys,"-",color="#ccc",lw=1)
for v in D["vias"]:
    if X0<v["p"][0]<X1 and Y0<v["p"][1]<Y1:
        ax.add_patch(Circle(v["p"],v["d"]/2,fc="w",ec=C.get(v["net"],"#aaa"),lw=1.3))
for hh in D["holes"]:
    if X0<hh["p"][0]<X1 and Y0<hh["p"][1]<Y1 and hh["r"]>0.2: ax.add_patch(Circle(hh["p"],hh["r"],fc="none",ec="m",lw=1))
for n,c in C.items(): ax.plot([],[],color=c,label=n)
ax.legend(fontsize=7,loc="upper left")
ax.set_xlim(X0,X1);ax.set_ylim(Y1,Y0);ax.set_aspect("equal");ax.grid(alpha=.2)
ax.set_xticks([X0+i for i in range(int(X1-X0)+1)]);ax.set_yticks([Y0+i for i in range(int(Y1-Y0)+1)]);ax.tick_params(labelsize=6)
plt.savefig(sys.argv[2],dpi=100,bbox_inches="tight")
