"""prune2.py in.kicad_pcb drc.json out.kicad_pcb : delete the track pieces / vias that the DRC calls dangling AND that really have a free end (nothing of the same net touches that end), except the owner's via at (96.03, 90.87).
A piece is matched by net + length + one end at the DRC position, so a neighbour of equal length is never taken by mistake."""
import pcbnew,json,sys,re
tomm=pcbnew.ToMM; V=pcbnew.VECTOR2I; mm=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]); D=json.load(open(sys.argv[2]))
items=[]
for v in D["violations"]:
    if v["type"] in("track_dangling","via_dangling"):
        for i in v["items"]:
            d=i["description"]; p=(i["pos"]["x"],i["pos"]["y"])
            if abs(p[0]-96.025)<.02 and abs(p[1]-90.87)<.02: continue
            m=re.search(r"length ([\d.]+) mm",d)
            items.append((v["type"],p,float(m.group(1)) if m else None,re.search(r"\[(.*?)\]",d).group(1)))
trk=[t for t in b.GetTracks()]
def touched(t,pt,net,layer):
    for o in trk:
        if o is t or o.GetNetname()!=net: continue
        if o.GetClass()=="PCB_VIA":
            if ((o.GetPosition().x-pt.x)**2+(o.GetPosition().y-pt.y)**2)**.5<mm(0.16): return True
        elif o.GetLayer()==layer and o.HitTest(pt,2000): return True
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==net and p.IsOnLayer(layer) and p.HitTest(pt,2000): return True
    return False
kill=[]
for t in trk:
    net=t.GetNetname()
    if t.GetClass()=="PCB_VIA":
        p=(tomm(t.GetPosition().x),tomm(t.GetPosition().y))
        for ty,q,l,n in items:
            if ty=="via_dangling" and abs(p[0]-q[0])<.002 and abs(p[1]-q[1])<.002 and net==n: kill.append(t); break
    else:
        a=t.GetStart(); c=t.GetEnd(); L=tomm(((a.x-c.x)**2+(a.y-c.y)**2)**.5)
        for ty,q,l,n in items:
            if ty!="track_dangling" or net!=n or abs(L-l)>0.006: continue
            qa=abs(tomm(a.x)-q[0])<.002 and abs(tomm(a.y)-q[1])<.002; qc=abs(tomm(c.x)-q[0])<.002 and abs(tomm(c.y)-q[1])<.002
            if not (qa or qc): continue
            if not touched(t,a,net,t.GetLayer()) or not touched(t,c,net,t.GetLayer()): kill.append(t); break
for t in kill: b.Remove(t)
pcbnew.SaveBoard(sys.argv[3],b); print("removed",len(kill),"of",len(items),"flagged")
