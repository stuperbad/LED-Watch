"""outer_arc_in.py in.kicad_pcb out.kicad_pcb R_NEW : pull the outermost F.Cu COL arcs (the 12 concentric arcs outside ROW10, r about 20.64 mm) in to radius R_NEW.
Each COL net gets ONE arc about (100,100) from its first to its last stub; the radial stubs from the LED pads are shortened to meet it, the feed diagonal (r 20.24 -> arc) is
cut where it meets the new circle, hand-drawn chords / overlapping pieces that lay along the old arc are deleted. KiCad python."""
import pcbnew, sys, math, re
mm = pcbnew.FromMM; tomm = pcbnew.ToMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1]); R = float(sys.argv[3]); CX = CY = 100.0
pt = lambda p: (tomm(p.x), tomm(p.y))
rr = lambda q: math.hypot(q[0] - CX, q[1] - CY)
ang = lambda q: math.atan2(q[1] - CY, q[0] - CX)
OUT = 20.55
def on_circle(a): return V(mm(CX + R * math.cos(a)), mm(CY + R * math.sin(a)))
by = {}
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_VIA" or b.GetLayerName(t.GetLayer()) != "F.Cu" or not re.match(r"^/COL\d+$", t.GetNetname()):
        continue
    if max(rr(pt(t.GetStart())), rr(pt(t.GetEnd()))) >= OUT:
        by.setdefault(t.GetNetname(), []).append(t)
for net in sorted(by, key=lambda s: int(s[4:])):
    ps = by[net]; angs = []; width = None; ni = ps[0].GetNet(); dele = 0; cut = 0
    for t in ps:
        s, e = pt(t.GetStart()), pt(t.GetEnd())
        if rr(s) >= OUT and rr(e) >= OUT:            # arc or chord lying along the old ring
            width = t.GetWidth(); b.Remove(t); dele += 1; continue
        outer_is_end = rr(e) >= OUT
        P, Q = (e, s) if outer_is_end else (s, e)
        d = (P[0] - Q[0], P[1] - Q[1])
        # ray Q + k d meets circle R
        a = d[0] ** 2 + d[1] ** 2; bb_ = 2 * ((Q[0] - CX) * d[0] + (Q[1] - CY) * d[1]); c = (Q[0] - CX) ** 2 + (Q[1] - CY) ** 2 - R * R
        k = (-bb_ + math.sqrt(bb_ * bb_ - 4 * a * c)) / (2 * a)
        N = (Q[0] + k * d[0], Q[1] + k * d[1])
        # a radial stub keeps its exact angle
        if abs(((ang(P) - ang(Q) + math.pi) % (2 * math.pi)) - math.pi) < math.radians(0.3):
            N = (CX + R * math.cos(ang(P)), CY + R * math.sin(ang(P)))
        np_ = V(mm(N[0]), mm(N[1]))
        (t.SetEnd if outer_is_end else t.SetStart)(np_); angs.append(ang(N)); cut += 1
    ref = angs[0]; rel = [((a - ref + math.pi) % (2 * math.pi)) - math.pi for a in angs]
    lo, hi = min(rel), max(rel); a0, a1, am = ref + lo, ref + hi, ref + (lo + hi) / 2
    arc = pcbnew.PCB_ARC(b); arc.SetLayer(pcbnew.F_Cu); arc.SetWidth(width or mm(0.1)); arc.SetNet(ni)
    # end points: take the exact nm of the nearest cut stub end so the ends coincide
    arc.SetStart(on_circle(a0)); arc.SetEnd(on_circle(a1)); arc.SetMid(on_circle(am)); b.Add(arc)
    print(net, "removed", dele, "cut", cut, "arc %.1f..%.1f deg" % (math.degrees(a0), math.degrees(a1)))
pcbnew.SaveBoard(sys.argv[2], b)
