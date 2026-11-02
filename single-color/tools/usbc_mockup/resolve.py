"""resolve.py in drc.json out : delete the copper that is NOT part of the moved block but collides with it (shorting / clearance / hole clearance / crossing between a track or via and another track, via or pad); ring nets and pads are never deleted (reported)"""
import pcbnew,sys,json,re
tomm=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); D=json.load(open(sys.argv[2])); M=json.load(open("u5/moved_keys.json"))
mt={(k[1],k[2],k[3],k[4],k[5],k[6]) for k in M if k[0]=="t"}; mt|={(k[1],k[2],k[5],k[6],k[3],k[4]) for k in M if k[0]=="t"}
mv={(k[1],k[2],k[3]) for k in M if k[0]=="v"}
ring=lambda n: re.match(r"/(ROW\d+|COL\d+)$",n or "") is not None
def find(desc,pos):
    m=re.search(r"\[([^\]]*)\]",desc); net=m.group(1) if m else ""
    x,y=pos["x"],pos["y"]
    if desc.startswith("Via"):
        for t in b.GetTracks():
            if t.GetClass()=="PCB_VIA" and abs(tomm(t.GetPosition().x)-x)<.003 and abs(tomm(t.GetPosition().y)-y)<.003: return t,"via",net
    elif desc.startswith("Track"):
        L=float(re.search(r"length ([\d.]+)",desc).group(1)); ly=re.search(r"on ([A-Za-z0-9.]+),",desc).group(1)
        for t in b.GetTracks():
            if t.GetClass()!="PCB_TRACK" or b.GetLayerName(t.GetLayer())!=ly or t.GetNetname()!=net: continue
            a,c=t.GetStart(),t.GetEnd()
            if abs(tomm(t.GetLength())-L)<.006 and ((abs(tomm(a.x)-x)<.003 and abs(tomm(a.y)-y)<.003) or (abs(tomm(c.x)-x)<.003 and abs(tomm(c.y)-y)<.003)): return t,"track",net
    return None,None,net
kill=[];skipped=[]
for v in D["violations"]:
    if v["type"] not in("shorting_items","clearance","hole_clearance","tracks_crossing","hole_to_hole","solder_mask_bridge","via_dangling_never"): continue
    for i in v["items"]:
        d=i["description"]
        if not (d.startswith("Track") or d.startswith("Via")): continue
        it,kind,net=find(d,i["pos"])
        if it is None: continue
        if kind=="track":
            a,c=it.GetStart(),it.GetEnd(); key=(net,b.GetLayerName(it.GetLayer()),round(tomm(a.x),3),round(tomm(a.y),3),round(tomm(c.x),3),round(tomm(c.y),3))
            moved=key in mt
        else: moved=(net,round(tomm(it.GetPosition().x),3),round(tomm(it.GetPosition().y),3)) in mv
        if moved: continue
        if ring(net): skipped.append((kind,net,i["pos"])); continue
        if it not in kill: kill.append(it)
for t in kill: b.Remove(t)
pcbnew.SaveBoard(sys.argv[3],b); print("deleted",len(kill),"colliding items of other nets; ring items left:",skipped)
