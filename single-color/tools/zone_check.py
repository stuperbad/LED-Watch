"""zone_check.py BOARD x0 y0 x1 y1 (KiCad python): which nets have copper (tracks, vias) inside a rectangle, by layer. Used for the crystal keep-out box (91.5 90.6 95.5 95.8) and the 5 x 5 mm core under U1 (97.5 89.37 102.5 94.37). Arcs are checked by their chord only."""
import sys, pcbnew, math
b=pcbnew.LoadBoard(sys.argv[1]); to=pcbnew.ToMM
x0,y0,x1,y1=[float(v) for v in sys.argv[2:6]]
def inside(x,y): return x0<=x<=x1 and y0<=y<=y1
def seg_hits(s,e):
    n=40
    for i in range(n+1):
        x=to(s.x+(e.x-s.x)*i/n); y=to(s.y+(e.y-s.y)*i/n)
        if inside(x,y): return True
    return False
res={}
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition()
        if inside(to(p.x),to(p.y)): res.setdefault((t.GetNetname(),"via"),0); res[(t.GetNetname(),"via")]+=1
    else:
        s,e=t.GetStart(),t.GetEnd()
        if seg_hits(s,e): 
            k=(t.GetNetname(),b.GetLayerName(t.GetLayer())); res[k]=res.get(k,0)+1
for k,v in sorted(res.items()): print(k,v)
