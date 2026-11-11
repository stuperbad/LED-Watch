"""rework_h2.py IN OUT (KiCad python): tidy the COL2 knot around H2 and R3 (2026-11-09): H2 pad 2 -> R3 pad 1 with a side exit, a diagonal and a radial piece (no octagon loop around the resistor),
H2 pad 2 -> the minute ring's COL2 arc joint with an end exit; the IND3 trunk now leaves R3 pad 1 directly."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; F = pcbnew.F_Cu; FM = pcbnew.FromMM; nets = b.GetNetsByName()
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM)))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F and t.GetNetname() == "/COL2"]
TOKILL = []
def drop(p, q):
    for t in tracks:
        s, e = (t.GetStart().x / NM, t.GetStart().y / NM), (t.GetEnd().x / NM, t.GetEnd().y / NM)
        hit = lambda a, c: abs(a[0] - c[0]) < .006 and abs(a[1] - c[1]) < .006
        if ((hit(s, p) and hit(e, q)) or (hit(s, q) and hit(e, p))) and t not in TOKILL_OBJS: TOKILL_OBJS.append(t); return (t.GetStart(), t.GetEnd())
    print("NOT FOUND", p, q); return None
TOKILL_OBJS = []
old = [((113.36, 92.29), (113.81, 91.83)), ((113.81, 91.83), (113.75, 92.08)), ((113.75, 92.08), (113.85, 91.98)), ((113.85, 91.98), (113.85, 91.38)), ((113.45, 90.98), (113.85, 91.38)), ((112.65, 90.98), (113.45, 90.98)),
       ((112.5, 91.14), (112.65, 90.98)), ((112.31, 91.32), (112.5, 91.14)), ((111.99, 91.5), (112.31, 91.32)), ((112.5, 91.14), (112.72, 91.36)), ((112.72, 91.36), (112.72, 91.54)), ((112.72, 91.54), (112.19, 92.07))]
se = drop((113.85, 91.38), (115.71, 90.22)); J = se[1] if abs(se[1].x / NM - 115.71) < .01 else se[0]
ends_ = {}
for p, q in old: ends_[(p, q)] = drop(p, q)
E19 = ends_[((112.72, 91.54), (112.19, 92.07))]; E19 = E19[1] if abs(E19[1].x / NM - 112.19) < .01 else E19[0]
for t in TOKILL_OBJS: b.Remove(t)
h2 = b.FindFootprintByReference("H2"); r3 = b.FindFootprintByReference("R3")
P2 = [p for p in h2.Pads() if p.GetNumber() == "2"][0].GetPosition(); R1 = [p for p in r3.Pads() if p.GetNumber() == "1"][0].GetPosition()
cx, cy = h2.GetPosition().x / NM, h2.GetPosition().y / NM; th = math.atan2(cy - 100, cx - 100); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
p2 = (P2.x / NM, P2.y / NM); r1 = (R1.x / NM, R1.y / NM)
def add(pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(a if isinstance(a, pcbnew.VECTOR2I) else V(*a)); t.SetEnd(c if isinstance(c, pcbnew.VECTOR2I) else V(*c)); t.SetWidth(FM(0.1)); t.SetLayer(F); t.SetNet(nets["/COL2"]); b.Add(t)
# A: pad 2 -> R3 pad 1: side exit toward the resistor, 45-degree piece, short radial piece into the pad centre
d = (r1[0] - p2[0], r1[1] - p2[1]); Du, Dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]; su = 1 if Du > 0 else -1; L1 = 0.78
ru = abs(Du) - L1; q1 = (p2[0] + su * u[0] * L1, p2[1] + su * u[1] * L1); sv = 1 if Dv > 0 else -1
q2 = (q1[0] + su * u[0] * ru + sv * v[0] * ru, q1[1] + su * u[1] * ru + sv * v[1] * ru)
print("A: side %.2f, diag %.2f, radial %.2f" % (L1, ru, abs(Dv) - ru)); add([P2, V(*q1), V(*q2), R1])
# B: pad 2 -> arc joint: end exit (radial), 45-degree piece, radial piece
j = (J.x / NM, J.y / NM); d = (j[0] - p2[0], j[1] - p2[1]); Du, Dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]; su = 1 if Du > 0 else -1; L1 = 0.62
q1 = (p2[0] + v[0] * L1, p2[1] + v[1] * L1); ru = abs(Du); q2 = (q1[0] + su * u[0] * ru + v[0] * ru, q1[1] + su * u[1] * ru + v[1] * ru)
print("B: end %.2f, diag %.2f, radial %.2f" % (L1, ru, Dv - L1 - ru)); add([P2, V(*q1), V(*q2), J])
# C: trunk to IND3 leaves R3 pad 1 to the east, 45 degrees, then the old piece (112.19, 92.07) onward
add([R1, V(112.6, r1[1]), V(112.6 - (91.91 - r1[1]), 91.91), V(E19.x / NM, 91.91), E19])
pcbnew.SaveBoard(sys.argv[2], b)
