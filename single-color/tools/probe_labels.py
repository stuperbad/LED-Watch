import sys, pcbnew
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
def bb(x):
    r = x.GetBoundingBox(); return "x %.3f..%.3f y %.3f..%.3f" % (tomm(r.GetX()), tomm(r.GetRight()), tomm(r.GetY()), tomm(r.GetBottom()))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetText()[:3] in ("SET","TMR","ALM","BAT","FUN","CFG","LCK"):
        print("TEXT %-6s pos (%.3f,%.3f) h %.3f w %.3f t %.3f  %s" % (d.GetText(), tomm(d.GetPosition().x), tomm(d.GetPosition().y), tomm(d.GetTextHeight()), tomm(d.GetTextWidth()), tomm(d.GetTextThickness()), bb(d)))
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r.startswith("IND") or r.startswith("SW") or r.startswith("SC") or r in ("U2","C30","C31","R20","R21"):
        cy = fp.GetCourtyard(fp.GetLayer()).BBox() if hasattr(fp,"GetCourtyard") else None
        print("FP %-5s %s pos (%.3f,%.3f) rot %.0f  bbox %s  pads: %s" % (r, fp.GetValue(), tomm(fp.GetPosition().x), tomm(fp.GetPosition().y), fp.GetOrientationDegrees(), bb(fp),
              "; ".join("%s(%.3f,%.3f)%s" % (p.GetNumber(), tomm(p.GetPosition().x), tomm(p.GetPosition().y), p.GetNetname()) for p in fp.Pads())))
# drawings on user layers near the cell
for d in b.GetDrawings():
    ln = b.GetLayerName(d.GetLayer())
    if d.GetClass()=="PCB_SHAPE" and ln not in ("Edge.Cuts","F.Silkscreen","B.Silkscreen"):
        r=d.GetBoundingBox()
        if tomm(r.GetY())<106 and tomm(r.GetBottom())>95 and tomm(r.GetX())<100<tomm(r.GetRight()):
            print("SHAPE", ln, bb(d))
