"""shift_block.py in out dx : move the power-manager block (U4, L1, L2, C51, C52, C54, R50-R56) by dx mm in x together with its own copper.
 * footprints move;  * vias of the block's nets inside the window move, except the dog-bone vias of the MCU fan-out (they touch an F.Cu stub that ends on a U1 pad);
 * tracks of the block's nets with both ends inside the window and neither end on something that stays (a stay-put via, a pad of a part that did not move) move;
 * tracks of the block's nets that would be stretched (one end moves, one stays) are deleted and left for the router.
 prints what it did"""
import pcbnew,sys,json
tomm=pcbnew.ToMM; mm=pcbnew.FromMM; V=pcbnew.VECTOR2I
b=pcbnew.LoadBoard(sys.argv[1]); dx=float(sys.argv[3]); D=V(mm(dx),0)
REFS=["U4","L1","L2","C51","C52","C54","R50","R51","R52","R53","R54","R55","R56"]
fp={f.GetReference():f for f in b.GetFootprints()}
nets=set(); xs=[];ys=[]
for r in REFS:
    for p in fp[r].Pads():
        if p.GetNetname() and p.GetNetname()!="GND": nets.add(p.GetNetname())
        xs.append(tomm(p.GetPosition().x)); ys.append(tomm(p.GetPosition().y))
X0,X1,Y0,Y1=min(xs)-1.2,max(xs)+1.2,min(ys)-1.2,max(ys)+1.2
inW=lambda p: X0<=tomm(p.x)<=X1 and Y0<=tomm(p.y)<=Y1
def close(a,c,t=mm(0.02)): return abs(a.x-c.x)<=t and abs(a.y-c.y)<=t
# stay-put pads: pads of footprints that do not move
stay_pads=[p for f in b.GetFootprints() if f.GetReference() not in REFS for p in f.Pads()]
trk=[t for t in b.GetTracks()]
vias=[t for t in trk if t.GetClass()=="PCB_VIA"]; segs=[t for t in trk if t.GetClass()=="PCB_TRACK"]
# fixed vias: end of an F.Cu piece that touches a U1 pad
u1=[p for p in fp["U1"].Pads()]
fixed=[]
for s in segs:
    if s.GetLayer()!=pcbnew.F_Cu: continue
    for e,o in ((s.GetStart(),s.GetEnd()),(s.GetEnd(),s.GetStart())):
        if any(p.HitTest(e,2000) for p in u1):
            for v in vias:
                if close(v.GetPosition(),o): fixed.append(v.GetPosition())
fixed_set=lambda pos: any(close(pos,q) for q in fixed)
pads_block=[p for r in REFS for p in fp[r].Pads()]
movedv=[];stayv=[]
for v in vias:
    pos=v.GetPosition(); n=v.GetNetname()
    near_block=any(((pos.x-p.GetPosition().x)**2+(pos.y-p.GetPosition().y)**2)**.5<mm(1.3) for p in pads_block)
    if inW(pos) and not fixed_set(pos) and ((n in nets) or (n=="GND" and near_block)): movedv.append(v)
    else: stayv.append(v)
mvpos=[v.GetPosition() for v in movedv]; stpos=[v.GetPosition() for v in stayv]
def endpoint_status(pt,layer,self_):
    """'move' if the end sits on a moved via / pad of a moved part; 'stay' if on a stay-put via or pad; 'free' otherwise"""
    if any(close(pt,q) for q in mvpos): return "move"
    if any(close(pt,q) for q in stpos): return "stay"
    for p in pads_block:
        if p.IsOnLayer(layer) and p.HitTest(pt,2000): return "move"
    for p in stay_pads:
        if p.IsOnLayer(layer) and p.HitTest(pt,2000): return "stay"
    return "free"
moved=deleted=kept=0; todo_move=[];todo_del=[]
for s in segs:
    n=s.GetNetname()
    if n not in nets and not (n=="GND" and inW(s.GetStart()) and inW(s.GetEnd()) and any(((s.GetStart().x-p.GetPosition().x)**2+(s.GetStart().y-p.GetPosition().y)**2)**.5<mm(1.3) for p in pads_block)): continue
    a,c=s.GetStart(),s.GetEnd()
    if not (inW(a) or inW(c)): continue
    sa=endpoint_status(a,s.GetLayer(),s); sc=endpoint_status(c,s.GetLayer(),s)
    if inW(a) and inW(c) and "stay" not in (sa,sc): todo_move.append(s)
    elif "stay" in (sa,sc) or (inW(a)!=inW(c)):
        # one end would be stretched
        if "move" in (sa,sc) or (inW(a) and inW(c)): todo_del.append(s)
keys=[]
for s in todo_move:
    s.SetStart(s.GetStart()+D); s.SetEnd(s.GetEnd()+D); moved+=1
    keys.append(["t",s.GetNetname(),b.GetLayerName(s.GetLayer()),round(tomm(s.GetStart().x),3),round(tomm(s.GetStart().y),3),round(tomm(s.GetEnd().x),3),round(tomm(s.GetEnd().y),3)])
for v in movedv:
    v.SetPosition(v.GetPosition()+D); keys.append(["v",v.GetNetname(),round(tomm(v.GetPosition().x),3),round(tomm(v.GetPosition().y),3)])
json.dump(keys,open("u5/moved_keys.json","w"))
for s in todo_del: b.Remove(s); deleted+=1
for r in REFS: f=fp[r]; f.SetPosition(f.GetPosition()+D)
pcbnew.SaveBoard(sys.argv[2],b)
print("block nets",len(nets),"| footprints",len(REFS),"| vias moved",len(movedv),"fixed(MCU dogbone)",len(fixed),"| tracks moved",moved,"deleted (stretch)",deleted)
