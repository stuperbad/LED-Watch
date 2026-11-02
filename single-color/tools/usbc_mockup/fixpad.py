"""fixpad.py in out : put the anchor of every shell-tab pad at the centre of its (possibly trimmed) polygon so that the custom pad is one piece"""
import pcbnew,sys,json
mm=pcbnew.FromMM; V=pcbnew.VECTOR2I; tomm=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]); N=json.load(open("usbc/notch.json"))
for p in b.FindFootprintByReference("J2").Pads():
    if p.GetNumber()!="SH": continue
    c=(tomm(p.GetPosition().x),tomm(p.GetPosition().y))
    n=min(N,key=lambda r:(r["c"][0]-c[0])**2+(r["c"][1]-c[1])**2)
    from statistics import mean
    xs=[q[0] for q in n["pts"]]; ys=[q[1] for q in n["pts"]]; cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
    p.DeletePrimitivesList(); p.SetPosition(V(mm(cx),mm(cy))); p.SetSize(V(mm(0.2),mm(0.2)))
    p.AddPrimitivePoly(pcbnew.B_Cu,[V(mm(x-cx),mm(y-cy)) for x,y in n["pts"]],0,True)
pcbnew.SaveBoard(sys.argv[2],b)
