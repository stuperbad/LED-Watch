"""fixnets.py in out ref.json : give back to every track / via the net it had in the reference board (KiCad re-tags copper that touches a pad when the part is moved)"""
import pcbnew,sys,json
tomm=pcbnew.ToMM
ref=json.load(open(sys.argv[3]))
tk={tuple(r[0:1])+tuple(map(tuple,r[1])):r[2] for r in ref["tracks"]}; vi={tuple(r[0]):r[1] for r in ref["vias"]}
b=pcbnew.LoadBoard(sys.argv[1]); n=0
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        k=(round(tomm(t.GetPosition().x),2),round(tomm(t.GetPosition().y),2))
        if k in vi and vi[k]!=t.GetNetname(): t.SetNet(b.FindNet(vi[k])); n+=1
    elif t.GetClass()=="PCB_TRACK":
        a=(round(tomm(t.GetStart().x),2),round(tomm(t.GetStart().y),2)); c=(round(tomm(t.GetEnd().x),2),round(tomm(t.GetEnd().y),2))
        k=(b.GetLayerName(t.GetLayer()),)+tuple(sorted([a,c]))
        if k in tk and tk[k]!=t.GetNetname(): t.SetNet(b.FindNet(tk[k])); n+=1
pcbnew.SaveBoard(sys.argv[2],b); print("nets restored on",n,"items")
