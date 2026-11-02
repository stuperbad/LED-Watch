"""Extract the F.Cu stubs of the ring LEDs (S = seconds, M = minutes, H = hours): for every ROW pad and every COL pad the chain of straight F.Cu pieces that touches the pad, with pad centre / size / ring angle,
the lane via a ROW stub ends on, and whether the chain is a plain path (ok) or has a branch.   Input of ring_stubs.py and ring_col.py.
usage (KiCad python): ring_extract.py in.kicad_pcb out.json"""
import pcbnew, math, sys, re, json
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); F=pcbnew.F_Cu
items=[]  # F.Cu straight pieces and arcs
for t in b.GetTracks():
    if t.GetClass()=="PCB_TRACK" and t.GetLayer()==F:
        items.append(dict(k="seg",net=t.GetNetname(),a=(tomm(t.GetStart().x),tomm(t.GetStart().y)),b=(tomm(t.GetEnd().x),tomm(t.GetEnd().y)),w=tomm(t.GetWidth())))
    elif t.GetClass()=="PCB_ARC" and t.GetLayer()==F:
        items.append(dict(k="arc",net=t.GetNetname(),a=(tomm(t.GetStart().x),tomm(t.GetStart().y)),b=(tomm(t.GetEnd().x),tomm(t.GetEnd().y)),m=(tomm(t.GetMid().x),tomm(t.GetMid().y)),w=tomm(t.GetWidth())))
vias=[dict(net=t.GetNetname(),p=(tomm(t.GetPosition().x),tomm(t.GetPosition().y))) for t in b.GetTracks() if t.GetClass()=="PCB_VIA"]
def near(p,q,e=0.03): return math.hypot(p[0]-q[0],p[1]-q[1])<e
out=[]
for f in sorted(b.GetFootprints(), key=lambda f:f.GetReference()):
    r=f.GetReference()
    if not re.match(r"^[SMH]\d+$", r): continue
    cx,cy=tomm(f.GetPosition().x),tomm(f.GetPosition().y)
    A=math.atan2(cx-100,-(cy-100))
    for p in f.Pads():
        n=p.GetNetname()
        if not (n.startswith("/ROW") or n.startswith("/COL")): continue
        px,py=tomm(p.GetPosition().x),tomm(p.GetPosition().y)
        # component of same-net straight pieces that touch the pad (and each other), not crossing vias
        comp=[i for i,s in enumerate(items) if s["k"]=="seg" and s["net"]==n and any(p.HitTest(pcbnew.VECTOR2I(mm(q[0]),mm(q[1]))) for q in (s["a"],s["b"]))]
        k=0
        while k<len(comp):
            s=items[comp[k]]; k+=1
            for j,t in enumerate(items):
                if j in comp or t["k"]!="seg" or t["net"]!=n: continue
                if any(near(u,v) for u in (s["a"],s["b"]) for v in (t["a"],t["b"])):
                    # do not grow through a via
                    if any(near(v["p"],u,0.06) for v in vias if v["net"]==n for u in (s["a"],s["b"])): continue
                    comp.append(j)
        ok=True;why=""
        deg={}
        key=lambda q:(round(q[0]/0.01),round(q[1]/0.01))
        for i in comp:
            for q in (items[i]["a"],items[i]["b"]): deg[key(q)]=deg.get(key(q),0)+1
        if any(d>2 for d in deg.values()): ok=False; why="vertex of degree>2"
        # order the pieces as a path starting at the end nearest the pad centre
        used=[];pts=[(px,py)];cur=None
        ends=[q for q in deg if deg[q]==1]
        used=list(comp)
        # path vertices: start at degree-1 vertex nearest pad centre
        verts={}
        for i in comp:
            for q in (items[i]["a"],items[i]["b"]): verts[key(q)]=q
        if ends:
            st=min(ends,key=lambda q:math.hypot(verts[q][0]-px,verts[q][1]-py))
            pts=[verts[st]];seen=set();curk=st
            while True:
                nxt=[i for i in comp if i not in seen and (key(items[i]["a"])==curk or key(items[i]["b"])==curk)]
                if not nxt: break
                i=nxt[0];seen.add(i)
                o=items[i]["b"] if key(items[i]["a"])==curk else items[i]["a"]
                pts.append(o);curk=key(o)
        cur=pts[-1]
        end_via=[v["p"] for v in vias if v["net"]==n and near(v["p"],cur,0.2)]
        # other same-net items touching interior vertices?
        out.append(dict(ref=r,pad=p.GetNumber(),net=n,center=(px,py),size=(tomm(p.GetSize().x),tomm(p.GetSize().y)),ringA=math.degrees(A),
                pts=pts,pieces=[(items[i]["a"],items[i]["b"]) for i in used],via=end_via[0] if end_via else None,ok=ok,why=why,
                endpoint=cur,start_off=math.hypot(pts[0][0]-px,pts[0][1]-py)))
json.dump(out,open(sys.argv[2],"w"))
rows=[o for o in out if o["net"].startswith("/ROW")]
print("rows",len(rows),"with via",sum(1 for o in rows if o["via"]),"clean",sum(1 for o in rows if o["ok"] and o["via"]))
for o in rows:
    if not (o["ok"] and o["via"]): print("  PROBLEM",o["ref"],o["net"],o["why"],"endpoint",o["endpoint"],"via",o["via"],len(o["pieces"]))
cols=[o for o in out if o["net"].startswith("/COL")]
print("cols",len(cols),"clean",sum(1 for o in cols if o["ok"]))
