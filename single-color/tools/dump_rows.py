import pcbnew, math, sys, json, re
b=pcbnew.LoadBoard(sys.argv[1]); mm=lambda v:v/1e6
CX=CY=100.0
out={"arcs":[],"trk":[],"via":[],"led":[]}
for t in b.GetTracks():
    c=t.GetClass(); n=t.GetNetname()
    if c=="PCB_ARC":
        s,m,e=t.GetStart(),t.GetMid(),t.GetEnd()
        out["arcs"].append([n,math.hypot(mm(s.x)-CX,mm(s.y)-CY),math.atan2(mm(s.y)-CY,mm(s.x)-CX),math.atan2(mm(m.y)-CY,mm(m.x)-CX),math.atan2(mm(e.y)-CY,mm(e.x)-CX)])
    elif c=="PCB_TRACK" and t.GetLayerName()=="F.Cu":
        s,e=t.GetStart(),t.GetEnd(); out["trk"].append([n,mm(s.x)-CX,mm(s.y)-CY,mm(e.x)-CX,mm(e.y)-CY])
    elif c=="PCB_VIA":
        p=t.GetPosition(); out["via"].append([n,mm(p.x)-CX,mm(p.y)-CY])
for f in b.GetFootprints():
    if re.fullmatch(r"[HMS]\d+",f.GetReference()):
        p=f.GetPosition(); out["led"].append([mm(p.x)-CX,mm(p.y)-CY])
json.dump(out,open(sys.argv[2],"w"))
