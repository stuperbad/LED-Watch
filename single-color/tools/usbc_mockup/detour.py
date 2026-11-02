import pcbnew, sys, math, collections
tomm=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
pads=collections.defaultdict(list); L=collections.defaultdict(float); nv=collections.Counter()
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname(): pads[p.GetNetname()].append((f.GetReference()+"."+p.GetNumber(),tomm(p.GetPosition().x),tomm(p.GetPosition().y)))
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA": nv[t.GetNetname()]+=1
    else: L[t.GetNetname()]+=tomm(t.GetLength())
rows=[]
for n,ps in pads.items():
    if len(ps)!=2 or n.startswith("unconnected"): continue
    d=math.hypot(ps[0][1]-ps[1][1],ps[0][2]-ps[1][2])
    if d<0.5: continue
    rows.append((L[n]/d,n,round(d,1),round(L[n],1),nv[n],ps[0][0],ps[1][0]))
rows.sort(reverse=True)
print("2-pad nets: routed length / straight distance")
for r in rows[:int(sys.argv[2])]: print("  %-12s ratio %.1f  straight %5.1f mm routed %5.1f mm vias %d  %s-%s"%(r[1],r[0],r[2],r[3],r[4],r[5],r[6]))
