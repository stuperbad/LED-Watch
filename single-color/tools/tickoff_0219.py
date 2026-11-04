"""tickoff.py IN OUT : the last small fixes of the 02:19 save.
 1. four ring-LED pads (H11.1, H11.2, H5.2, H7.2): the first piece now leaves along the part axis; it meets the existing 45-degree line where the axis ray crosses it (stub and the start of that line are replaced)
 2. R5.1: the west COL4 line ends on the pad's exit piece (a T) instead of running 0.25 mm on to the fork: the 15-degree V disappears
 3. +3V3 (103.095, 98.75): two micro pieces (0.007 + 0.025 mm, both inside the copper of the horizontal line) removed; horizontal and vertical get an exact crossing node"""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; grave = []
V = lambda p: pcbnew.VECTOR2I(int(round(p[0])), int(round(p[1])))
ip = lambda p: (p.x, p.y)
def tracks(net, layer):
    return [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net and b.GetLayerName(t.GetLayer()) == layer]
def add(t, a, c, layer=None):
    n = pcbnew.PCB_TRACK(b); n.SetLayer(t.GetLayer()); n.SetWidth(t.GetWidth()); n.SetNet(t.GetNet()); n.SetStart(V(a)); n.SetEnd(V(c)); b.Add(n); return n
def rm(t): b.Remove(t); grave.append(t)
def ends(t): return ip(t.GetStart()), ip(t.GetEnd())
def other(t, p): s, e = ends(t); return e if s == p else s
log = []
# 1 ---------------------------------------------------------------- pad exits along the axis
for ref, num in (("H11", "1"), ("H11", "2"), ("H5", "2"), ("H7", "2")):
    f = b.FindFootprintByReference(ref); pads = list(f.Pads()); pad = [q for q in pads if q.GetNumber() == num][0]; opad = [q for q in pads if q.GetNumber() != num][0]
    P = ip(pad.GetPosition()); O = ip(opad.GetPosition()); net = pad.GetNetname(); layer = b.GetLayerName(f.GetLayer())
    ux, uy = P[0] - O[0], P[1] - O[1]; n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    ts = tracks(net, layer)
    stub = [t for t in ts if P in ends(t) and mm(t.GetLength()) < 0.25]
    assert len(stub) == 1, (ref, num, len(stub)); stub = stub[0]
    N1 = other(stub, P)
    D = [t for t in ts if t is not stub and N1 in ends(t)]
    assert len(D) == 1, (ref, num, "D", len(D)); D = D[0]; N2 = other(D, N1)
    dx, dy = N2[0] - N1[0], N2[1] - N1[1]; dl = math.hypot(dx, dy); dx, dy = dx / dl, dy / dl
    # ray P + s u = N1 + t d
    det = ux * (-dy) - uy * (-dx); assert abs(det) > 1e-9
    rx, ry = N1[0] - P[0], N1[1] - P[1]
    s = (rx * (-dy) - ry * (-dx)) / det; t_ = (ux * ry - uy * rx) / det
    assert s > 0.15e6 and 0 < t_ < dl - 0.05e6, (ref, num, s / 1e6, t_ / 1e6, dl / 1e6)
    I = (P[0] + s * ux, P[1] + s * uy)
    rm(stub); rm(D); add(stub, P, I); add(D, I, N2)
    log.append("%s.%s: axis piece %.3f mm along %.0f deg meets the 45-degree line at (%.3f, %.3f); old stub %.3f mm and the first %.3f mm of the line replaced" % (ref, num, s / 1e6, math.degrees(math.atan2(-uy, ux)) % 360, mm(I[0]), mm(I[1]), mm(stub.GetLength()) if False else 0.0, t_ / 1e6))
# 2 ---------------------------------------------------------------- R5.1
f = b.FindFootprintByReference("R5"); pad = [q for q in f.Pads() if q.GetNumber() == "1"][0]; P = ip(pad.GetPosition()); ts = tracks("/COL4", "F.Cu")
E = [t for t in ts if P in ends(t)]; assert len(E) == 1; E = E[0]; node = other(E, P)
Bq = [t for t in ts if t is not E and node in ends(t) and abs(mm(other(t, node)[0]) - 113.587) < 0.002]; assert len(Bq) == 1; Bq = Bq[0]; Wend = other(Bq, node)
W = [t for t in ts if t is not Bq and Wend in ends(t)]; assert len(W) == 1; W = W[0]
yW = Wend[1]; ex, ey = node[0] - P[0], node[1] - P[1]; s = (yW - P[1]) / ey; I = (P[0] + s * ex, yW); assert 0 < s < 1
# E is stored P->node or node->P: rebuild as two pieces P->I, I->node
rm(E); add(E, P, I); add(E, I, node)
if ends(W)[0] == Wend: W.SetStart(V(I))
else: W.SetEnd(V(I))
rm(Bq)
log.append("R5.1: COL4 west line now ends on the exit piece at (%.3f, %.3f); the 0.247 mm piece to the fork is gone" % (mm(I[0]), mm(I[1])))
# 3 ---------------------------------------------------------------- +3V3 micro jog
ts = tracks("+3V3", "B.Cu")
def at(t, x, y): return any(abs(mm(p[0]) - x) < 0.0015 and abs(mm(p[1]) - y) < 0.0015 for p in ends(t))
m1 = [t for t in ts if at(t, 103.095, 98.75) and at(t, 103.1, 98.745)]; m2 = [t for t in ts if at(t, 103.1, 98.745) and at(t, 103.125, 98.745)]
assert len(m1) == 1 and len(m2) == 1
H1 = [t for t in ts if at(t, 102.233, 98.75) and at(t, 103.095, 98.75)][0]; H2 = [t for t in ts if at(t, 103.78, 98.75) and at(t, 103.095, 98.75)][0]
Vt = [t for t in ts if abs(mm(ends(t)[0][0]) - 103.125) < 0.0015 and abs(mm(ends(t)[1][0]) - 103.125) < 0.0015 and min(mm(ends(t)[0][1]), mm(ends(t)[1][1])) < 98.75 < max(mm(ends(t)[0][1]), mm(ends(t)[1][1]))]
assert len(Vt) == 1, len(Vt); Vt = Vt[0]
Y = 98750000
X = ends(Vt)[0][0]
hs = [p for t in (H1, H2) for p in ends(t) if abs(mm(p[0]) - 103.095) > 0.01]
hA = min(hs, key=lambda p: p[0]); hB = max(hs, key=lambda p: p[0])
X0 = (X, Y)
for t in (m1[0], m2[0], H1, H2): rm(t)
add(H1, hA, X0); add(H1, X0, hB)
vs, ve = ends(Vt)
Vlen_old = Vt; rm(Vt); add(Vt, vs, X0); add(Vt, X0, ve)
log.append("+3V3 (103.1, 98.75): micro jog removed, horizontal and vertical meet in an exact node at (%.3f, %.3f)" % (mm(X0[0]), mm(X0[1])))
pcbnew.SaveBoard(sys.argv[2], b)
for l in log: print(l)
