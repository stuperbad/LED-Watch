"""nudge_via.py IN OUT NET X Y DTHETA_DEG (KiCad python): move one via of a ring lane along its lane (about the board centre 100, 100) by DTHETA degrees; the two In2 arcs of the lane that end on it are
re-cut (centre and radius kept) and every F.Cu / B.Cu track end on the via follows.  Nothing is removed or added."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); net = sys.argv[3]; X, Y, dth = float(sys.argv[4]), float(sys.argv[5]), math.radians(float(sys.argv[6])); NM = 1e6; O = (100.0, 100.0)
via = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == net and abs(t.GetPosition().x / NM - X) < 0.03 and abs(t.GetPosition().y / NM - Y) < 0.03][0]
p0 = (via.GetPosition().x, via.GetPosition().y); r = math.hypot(p0[0] / NM - O[0], p0[1] / NM - O[1]); a0 = math.atan2(p0[1] / NM - O[1], p0[0] / NM - O[0])
new = pcbnew.VECTOR2I(int(round((O[0] + r * math.cos(a0 + dth)) * NM)), int(round((O[1] + r * math.sin(a0 + dth)) * NM)))
ang = lambda p: math.atan2(p.y / NM - O[1], p.x / NM - O[0]); at = lambda m: pcbnew.VECTOR2I(int(round((O[0] + r * math.cos(m)) * NM)), int(round((O[1] + r * math.sin(m)) * NM)))
n_arc = n_trk = 0
same = lambda p: abs(p.x - p0[0]) < 3000 and abs(p.y - p0[1]) < 3000
for t in b.GetTracks():
    if t.GetNetname() != net or t.GetClass() == "PCB_VIA": continue
    if t.GetClass() == "PCB_ARC":
        if same(t.GetStart()): t.SetStart(new); other = t.GetEnd(); t.SetMid(at((ang(new) + ang(other)) / 2)); n_arc += 1
        elif same(t.GetEnd()): t.SetEnd(new); other = t.GetStart(); t.SetMid(at((ang(new) + ang(other)) / 2)); n_arc += 1
    else:
        if same(t.GetStart()): t.SetStart(new); n_trk += 1
        if same(t.GetEnd()): t.SetEnd(new); n_trk += 1
via.SetPosition(new); print("via moved %.3f mm along its lane; arcs re-cut: %d, track ends moved: %d" % (r * abs(dth), n_arc, n_trk)); pcbnew.SaveBoard(sys.argv[2], b)
