import json,sys,re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MP
D=json.load(open(sys.argv[1])); out=sys.argv[2]
X0,X1,Y0,Y1=85,112,83,114
ZB={"crystal":(90.49,90.815,94.75,95.585),"MCU core":(97.5,89.37,102.5,94.37),"U4 core":(97.65,98.15,101.35,101.85),"IMU":(98.94,107.29,101.06,109.41)}
col={"F.Cu":"#d02020","In1.Cu":"#1a9a3a","B.Cu":"#2050d0","In2.Cu":"#999"}
ring=re.compile(r"^/(COL\d+|ROW\d+)$")
def inzone(poly,net):
    for n,(a,b,c,d) in ZB.items():
        if net in ("GND",): continue
        if any(a<=x<=c and b<=y<=d for x,y in poly): return True
    return False
fig,ax=plt.subplots(figsize=(13,13*(Y1-Y0)/(X1-X0)))
for n,(a,b,c,d) in ZB.items():
    ax.add_patch(Rectangle((a,b),c-a,d-b,fc="#ffe9a0",ec="#c08000",lw=1.5,alpha=0.45)); ax.text(a+0.1,b+0.3,n,fontsize=9,color="#805000")
for p in D["pads"]:
    xs=[q[0] for q in p["pts"]]; ys=[q[1] for q in p["pts"]]
    if X0<=sum(xs)/len(xs)<=X1 and Y0<=sum(ys)/len(ys)<=Y1 and p["layer"] in("F.Cu","B.Cu"):
        ax.add_patch(MP(p["pts"],fc="#dddddd",ec="#888888",lw=0.4))
for t in D["tracks"]:
    if t["layer"]=="In2.Cu": continue
    pl=t["poly"]
    if max(q[0] for q in pl)<X0 or min(q[0] for q in pl)>X1 or max(q[1] for q in pl)<Y0 or min(q[1] for q in pl)>Y1: continue
    bad=(not ring.match(t["net"])) and inzone(pl,t["net"]) and t["net"] not in ("/XTAL1","/XTAL2")
    ax.plot([q[0] for q in pl],[q[1] for q in pl],color=col[t["layer"]],lw=2.6 if bad else 1.2,alpha=0.9,solid_capstyle="round",zorder=3 if not bad else 4)
for v in D["vias"]:
    if X0<=v["p"][0]<=X1 and Y0<=v["p"][1]<=Y1: ax.add_patch(plt.Circle(v["p"],0.15,fc="white",ec="k",lw=0.5,zorder=5))
ax.set_xlim(X0,X1); ax.set_ylim(Y1,Y0); ax.set_aspect("equal"); ax.set_title(sys.argv[3])
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([0],[0],color=c,lw=2,label=l) for l,c in col.items() if l!="In2.Cu"]+[Rectangle((0,0),1,1,fc="#ffe9a0",ec="#c08000",label="keep-out zone")],loc="lower left")
fig.savefig(out,dpi=95,bbox_inches="tight")
