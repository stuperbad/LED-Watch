"""rework_dump.py BOARD OUT.json : back-side parts with pad rectangles (world, at the board's rotation) for the placement viewer / checker (KiCad python)."""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; out = {}
for f in b.GetFootprints():
    if not f.IsFlipped(): continue
    x, y = mm(f.GetPosition().x), mm(f.GetPosition().y)
    pads = []
    for p in f.Pads():
        bb = p.GetBoundingBox()
        pads.append(dict(n=p.GetNumber(), net=p.GetNetname(), cx=mm(p.GetPosition().x) - x, cy=mm(p.GetPosition().y) - y, hx=mm(bb.GetWidth()) / 2, hy=mm(bb.GetHeight()) / 2))
    cy = f.GetCourtyard(pcbnew.B_CrtYd).BBox() if f.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else f.GetBoundingBox(False, False)
    out[f.GetReference()] = dict(x=x, y=y, rot=f.GetOrientationDegrees(), value=f.GetValue(), pads=pads,
                                 body=[mm(cy.GetLeft()) - x, mm(cy.GetTop()) - y, mm(cy.GetRight()) - x, mm(cy.GetBottom()) - y])
json.dump(out, open(sys.argv[2], "w"), indent=0); print(len(out), "back parts")
