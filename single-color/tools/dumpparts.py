import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
json.dump({f.GetReference(): dict(x=mm(f.GetPosition().x), y=mm(f.GetPosition().y), back=f.IsFlipped(), rot=f.GetOrientationDegrees(), pads=[(p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()]) for f in b.GetFootprints()}, open(sys.argv[2], "w"))
