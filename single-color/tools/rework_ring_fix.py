"""rework_ring_fix.py IN.kicad_pcb OUT.kicad_pcb (KiCad python): ring-lane repairs for the J2 shift (2026-11-09, J2 at x 116.9):
  1. /ROW0 (In2 arcs, r 14.63) is bent inward to r 13.9 (outward would cross the BUZ_B lane) around the two mounting pegs (45-degree ramps), arcs stay exact joints;
  2. /ROW8 (In2 arc, r 19.57): its two via taps move off the shell pads: the arc is split at two new points and the via + F.Cu links are drawn there."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; FM = pcbnew.FromMM; V = lambda x, y: pcbnew.VECTOR2I(int(round(x)), int(round(y)))
O = (100.0, 100.0); NM = 1e6
def pt(p): return (p.x / NM, p.y / NM)
def ang(p): return math.atan2(p[1] - O[1], p[0] - O[0])
def at(r, a): return (O[0] + r * math.cos(a), O[1] + r * math.sin(a))
def vec(p): return V(p[0] * NM, p[1] * NM)
L2 = b.GetLayerID("In2.Cu"); nets = b.GetNetsByName()
def arcs(net): return [t for t in b.GetTracks() if t.GetClass() == "PCB_ARC" and t.GetNetname() == net and t.GetLayer() == L2]
def add_arc(net, w, s, m, e):
    a = pcbnew.PCB_ARC(b); a.SetStart(s); a.SetMid(m); a.SetEnd(e); a.SetWidth(w); a.SetLayer(L2); a.SetNet(nets[net]); b.Add(a); return a
def add_trk(net, layer, w, p, q):
    t = pcbnew.PCB_TRACK(b); t.SetStart(p); t.SetEnd(q); t.SetWidth(w); t.SetLayer(b.GetLayerID(layer)); t.SetNet(nets[net]); b.Add(t)
def mid_of(r, a0, a1): return vec(at(r, (a0 + a1) / 2))
def ang_in(a, a0, a1):
    if abs(a0 - a1) > math.pi: return False          # arc across the +-180 degree seam
    lo, hi = min(a0, a1), max(a0, a1); return lo < a < hi
# ---- 1. ROW0 bumps
PEGX = float(sys.argv[4]) if len(sys.argv) > 4 else 14.3
R0, R1, ARCW = 14.63, (float(sys.argv[5]) if len(sys.argv) > 5 else 13.9), None
RAMP_LOWER = float(sys.argv[3]) if len(sys.argv) > 3 else 7.5
for pegy in (-2.89, 2.89):
    ap = math.atan2(pegy, PEGX)                                   # peg at (114.30, 100 +- 2.89)
    sgn = 1 if ap > 0 else -1
    d1, d2 = math.radians(6.0 if pegy < 0 else RAMP_LOWER), math.radians(3.4)
    aA, aA2, aB2, aB = ap - d1, ap - d2, ap + d2, ap + d1
    hit = [t for t in arcs("/ROW0") if ang_in(ap, ang(pt(t.GetStart())), ang(pt(t.GetEnd())))]
    assert len(hit) == 1, ("ROW0 arc for peg", pegy, len(hit)); t = hit[0]; w = t.GetWidth(); s, e = t.GetStart(), t.GetEnd(); r = math.hypot(pt(s)[0] - O[0], pt(s)[1] - O[1])
    sa, ea = ang(pt(s)), ang(pt(e)); lo_is_start = sa < ea
    b.Remove(t)
    PA, PA2, PB2, PB = vec(at(r, aA)), vec(at(R1, aA2)), vec(at(R1, aB2)), vec(at(r, aB))
    if lo_is_start: first, last = (s, sa), (e, ea)
    else: first, last = (e, ea), (s, sa)
    add_arc("/ROW0", w, first[0], mid_of(r, first[1], aA), PA)
    add_trk("/ROW0", "In2.Cu", w, PA, PA2); add_arc("/ROW0", w, PA2, mid_of(R1, aA2, aB2), PB2); add_trk("/ROW0", "In2.Cu", w, PB2, PB)
    add_arc("/ROW0", w, PB, mid_of(r, aB, last[1]), last[0])
    print("ROW0 bump at peg angle %.1f deg: arc r %.2f -> %.2f" % (math.degrees(ap), r, R1))
# the dangling start of the /COL3 In2 lane (its via was cleared by the shell pads) sits where the lower bump goes: cut it back, the router joins it again
def drop_any(net, layer, p, q): return drop(net, layer, p, q)
# ---- 2. ROW8 taps
RR = 19.567
def split(net, a_new):
    hit = [t for t in arcs(net) if ang_in(a_new, ang(pt(t.GetStart())), ang(pt(t.GetEnd())))]
    assert len(hit) == 1, ("split", net, len(hit)); t = hit[0]; s, e, w = t.GetStart(), t.GetEnd(), t.GetWidth(); sa, ea = ang(pt(s)), ang(pt(e)); r = math.hypot(pt(s)[0] - O[0], pt(s)[1] - O[1])
    P = vec(at(r, a_new)); b.Remove(t)
    add_arc(net, w, s, mid_of(r, sa, a_new), P); add_arc(net, w, P, mid_of(r, a_new, ea), e); return P, w
def via(net, p):
    v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FM(0.3)); v.SetDrill(FM(0.15)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); b.Add(v)
# drop the old F.Cu end pieces that led to the removed vias
def drop(net, layer, p, q):
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net and b.GetLayerName(t.GetLayer()) == layer:
            s, e = pt(t.GetStart()), pt(t.GetEnd())
            if (abs(s[0] - p[0]) < .006 and abs(s[1] - p[1]) < .006 and abs(e[0] - q[0]) < .006 and abs(e[1] - q[1]) < .006) or (abs(e[0] - p[0]) < .006 and abs(e[1] - p[1]) < .006 and abs(s[0] - q[0]) < .006 and abs(s[1] - q[1]) < .006): b.Remove(t); return True
    return False
print("dropped top pieces:", drop("/ROW8", "F.Cu", (118.17, 94.57), (118.64, 94.57)), drop("/ROW8", "F.Cu", (118.64, 94.57), (118.76, 94.44)))
print("dropped bottom piece:", drop("/ROW8", "F.Cu", (118.73, 104.57), (119.03, 104.57)))
print('COL3 lane cut back:', drop('/COL3', 'In2.Cu', (113.625, 103.685), (113.625, 104.085)), drop('/COL3', 'In2.Cu', (113.625, 104.085), (111.925, 105.785)))
yt = 93.35; at_ = math.atan2(yt - 100, math.sqrt(RR ** 2 - (yt - 100) ** 2)); Pt, w8 = split("/ROW8", at_)
yb = 103.0; ab = math.atan2(yb - 100, math.sqrt(RR ** 2 - (yb - 100) ** 2)); Pb, _ = split("/ROW8", ab)
via("/ROW8", Pt); via("/ROW8", Pb)
pt_, pb_ = pt(Pt), pt(Pb); print("ROW8 via taps at", [round(v, 3) for v in pt_], [round(v, 3) for v in pb_])
W1 = FM(0.1)
# remove the old zig-zag stubs behind the LED pads (S12.1 at 118.31,94.05 and S17.1 at 118.83,104.0), then link the pads to the new taps
for p_, q_ in (((118.31, 94.05), (117.93, 94.18)), ((117.93, 94.18), (117.93, 94.33)), ((117.93, 94.33), (118.17, 94.57)),
               ((118.83, 104.0), (118.44, 103.92)), ((118.44, 103.92), (118.33, 104.03)), ((118.33, 104.03), (118.33, 104.18)), ((118.33, 104.18), (118.73, 104.57))): drop("/ROW8", "F.Cu", p_, q_)
add_trk("/ROW8", "F.Cu", W1, vec((118.31, 94.05)), vec((118.31, 93.75))); add_trk("/ROW8", "F.Cu", W1, vec((118.31, 93.75)), Pt)
add_trk("/ROW8", "F.Cu", W1, vec((118.83, 104.0)), vec((118.83, 103.5))); add_trk("/ROW8", "F.Cu", W1, vec((118.83, 103.5)), Pb)
pcbnew.SaveBoard(sys.argv[2], b)
