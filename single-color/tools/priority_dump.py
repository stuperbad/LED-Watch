"""priority_dump.py BOARD OUT.json : geometry for priority_map.py (KiCad python): parts (side, pads, pad bounding box), copper pieces and vias, in mm."""
import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
parts = {}
for f in b.GetFootprints():
    pads = [(p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()]
    bbs = [p.GetBoundingBox() for p in f.Pads()]
    box = [min(mm(q.GetLeft()) for q in bbs), min(mm(q.GetTop()) for q in bbs), max(mm(q.GetRight()) for q in bbs), max(mm(q.GetBottom()) for q in bbs)] if bbs else None
    parts[f.GetReference()] = dict(back=f.IsFlipped(), pads=pads, box=box, value=f.GetValue())
trk = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA": continue
    pts = [t.GetStart(), t.GetEnd()]
    trk.append((b.GetLayerName(t.GetLayer()), t.GetNetname(), mm(pts[0].x), mm(pts[0].y), mm(pts[1].x), mm(pts[1].y), mm(t.GetLength())))
vias = [(t.GetNetname(), mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
json.dump(dict(parts=parts, trk=trk, vias=vias), open(sys.argv[2], "w"))
print(len(parts), "parts", len(trk), "pieces", len(vias), "vias")
