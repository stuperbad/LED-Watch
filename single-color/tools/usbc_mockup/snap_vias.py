"""snap_vias.py in.kicad_pcb out.kicad_pcb [x0] : when every track end touching a via (all layers, same net) sits on ONE common point that is not the via centre, move the via onto that point,
so tracks end on via centres without changing any track. Ring nets are skipped. KiCad python."""
import sys, math, re
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
x0 = float(sys.argv[3]) if len(sys.argv) > 3 else 95.0
ring = re.compile(r"^/(COL\d+|ROW\d+)$")
xy = lambda p: (tomm(p.x), tomm(p.y))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
SKIP = {("/BTN2", 96.175, 97.585)}   # moving it clears the VBAT track by less than the rule; left for hand editing
moved, skipped = 0, []
for v in vias:
    if ring.match(v.GetNetname()) or tomm(v.GetPosition().x) < x0:
        continue
    if (v.GetNetname(), round(tomm(v.GetPosition().x), 3), round(tomm(v.GetPosition().y), 3)) in SKIP:
        continue
    c = xy(v.GetPosition()); r = tomm(v.GetWidth(pcbnew.F_Cu)) / 2
    pts = []
    for t in tracks:
        if t.GetNetCode() != v.GetNetCode() or not v.IsOnLayer(t.GetLayer()):
            continue
        for e in (xy(t.GetStart()), xy(t.GetEnd())):
            if math.hypot(e[0] - c[0], e[1] - c[1]) <= r:
                pts.append(e)
    if not pts:
        continue
    cl = []
    for p in pts:
        for q in cl:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 0.011:
                break
        else:
            cl.append(p)
    if len(cl) == 1:
        p = cl[0]
        if math.hypot(p[0] - c[0], p[1] - c[1]) > 0.005:
            print("moved via %-10s (%.3f,%.3f) -> (%.3f,%.3f)" % (v.GetNetname(), c[0], c[1], p[0], p[1]))
            v.SetPosition(pcbnew.VECTOR2I(mm(p[0]), mm(p[1])))
            moved += 1
    else:
        skipped.append((v.GetNetname(), (round(c[0], 3), round(c[1], 3)), [(round(q[0], 3), round(q[1], 3)) for q in cl]))
print("vias moved", moved, "| vias whose ends do not share one point:", len(skipped))
for s in skipped:
    print("   SKIP", s)
pcbnew.SaveBoard(sys.argv[2], b)
