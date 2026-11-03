"""add_tvs_pcb.py SRC OUT cx cy rot [vx vy]   (KiCad python; 2026-11-02, as run for D51: VBUS_TO=109.34,107.0 GND_PATH="111.54,107.89;110.9,107.25" add_tvs_pcb.py in out 110.44 108.5 0)
Adds D51 = copy of D50's SOD-323 footprint with pads of 0.8 x 0.5 mm (Bourns' recommendation; also fits the UMW part) (0.8 x 0.5 mm, 1.4 mm gap), pad 1 (VBUS) on the west / north end.
VBUS: straight track from pad 1 to the VBUS point in env VBUS_TO (default: the vertex 111.125,95.225; the board uses C55 pad 1) - GND: env GND_PATH = polyline from pad 2 to an existing GND via centre. GND: via at (vx, vy) joined to pad 2 by a straight 0.1 mm track (only when vx vy given)."""
import sys, pcbnew
src, out = sys.argv[1], sys.argv[2]
cx, cy, rot = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
import os
via = (float(sys.argv[6]), float(sys.argv[7])) if len(sys.argv) > 7 else None
VB = tuple(float(v) for v in os.environ.get("VBUS_TO", "111.125,95.225").split(","))
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(src)
assert b.FindFootprintByReference("D51") is None
f = pcbnew.FOOTPRINT(b.FindFootprintByReference("D50"))
b.Add(f)
f.SetReference("D51"); f.SetValue("UDD32C05L01")
f.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy))); f.SetOrientationDegrees(rot)
grave = []
for g in list(f.GraphicalItems()):
    if g.GetLayer() == pcbnew.B_SilkS: f.Remove(g); grave.append(g)
for fld in f.GetFields():
    if fld.GetName() == "Reference": fld.SetVisible(False)
vbus, gnd = b.FindNet("VBUS"), b.FindNet("GND")
for p in f.Pads():
    p.SetSize(pcbnew.VECTOR2I(mm(0.8), mm(0.5)))
for sign in (1, -1):                                   # find the sign convention: pad 1 must end up west (rot 0) or north (rot 90)
    for p in f.Pads():
        p.SetFPRelativePosition(pcbnew.VECTOR2I(sign * mm(1.1) * (1 if p.GetNumber() == "1" else -1), 0))
    P = {p.GetNumber(): p.GetPosition() for p in f.Pads()}
    west = (P["1"].x < P["2"].x) if rot % 180 == 0 else (P["1"].y < P["2"].y)
    if west: break
for p in f.Pads(): p.SetNet(vbus if p.GetNumber() == "1" else gnd)
P = {k: (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)) for k, v in P.items()}
def track(a, c, net, w=0.1):
    t = pcbnew.PCB_TRACK(b); t.SetLayer(pcbnew.B_Cu); t.SetWidth(mm(w)); t.SetNet(net)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1]))); b.Add(t)
track(P["1"], VB, vbus)
GP = os.environ.get("GND_PATH")
if GP:                                                  # polyline from pad 2 to an existing GND via centre: "x,y;x,y"
    pts = [P["2"]] + [tuple(float(v) for v in q.split(",")) for q in GP.split(";")]
    for a, c in zip(pts, pts[1:]): track(a, c, gnd)
if via:
    track(P["2"], via, gnd)
    v = pcbnew.PCB_VIA(b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetPosition(pcbnew.VECTOR2I(mm(via[0]), mm(via[1])))
    v.SetWidth(mm(0.3)); v.SetDrill(mm(0.15)); v.SetNet(gnd); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
pcbnew.SaveBoard(out, b)
print("pads", P, "via", via)
