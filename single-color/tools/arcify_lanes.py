import pcbnew, math, sys, re
from pcbnew import FromMM as F, VECTOR2I as V
b=pcbnew.LoadBoard(sys.argv[1]); mm=lambda v:v/1e6
CX=CY=100.0
b.GetDesignSettings().m_HoleClearance=F(0.2); b.GetDesignSettings().m_CopperEdgeClearance=F(0.2)
lanes={}
rm=[]
for t in b.GetTracks():
    if t.GetClass()!="PCB_TRACK" or t.GetLayerName()!="In1.Cu": continue
    n=t.GetNetname()
    if not re.fullmatch(r"/ROW(\d+)",n): continue
    s,e=t.GetStart(),t.GetEnd()
    r1,r2=math.hypot(mm(s.x)-CX,mm(s.y)-CY),math.hypot(mm(e.x)-CX,mm(e.y)-CY)
    if abs(r1-r2)<0.01:                       # lane segment (both ends on the same circle)
        lanes[n]=lanes.get(n,[])+[round((r1+r2)/2,3)]
        rm.append(t)
print("lane segments removed",len(rm),{k:round(sum(v)/len(v),2) for k,v in lanes.items()})
for t in rm: b.Remove(t)
for n,rs in lanes.items():
    rho=sum(rs)/len(rs); net=b.FindNet(n)
    pt=lambda a:V(F(CX+rho*math.sin(a)),F(CY-rho*math.cos(a)))
    for q in range(4):
        a0,a1=q*math.pi/2,(q+1)*math.pi/2
        arc=pcbnew.PCB_ARC(b); arc.SetStart(pt(a0)); arc.SetMid(pt((a0+a1)/2)); arc.SetEnd(pt(a1)); arc.SetWidth(F(0.1)); arc.SetLayer(pcbnew.In1_Cu); arc.SetNet(net); b.Add(arc)
pcbnew.SaveBoard(sys.argv[2],b)
