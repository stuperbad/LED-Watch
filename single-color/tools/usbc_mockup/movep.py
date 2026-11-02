import pcbnew,sys,json
mm=pcbnew.FromMM; V=pcbnew.VECTOR2I
b=pcbnew.LoadBoard(sys.argv[1]); P=json.load(open(sys.argv[3]))
for ref,(x,y,a) in P.items():
    f=b.FindFootprintByReference(ref); f.SetPosition(V(mm(x),mm(y))); f.SetOrientationDegrees(a)
pcbnew.SaveBoard(sys.argv[2],b); print("moved",list(P))
