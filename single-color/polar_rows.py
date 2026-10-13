"""
Polar router, step 1 (white board): the 11 ROW nets as concentric lanes.

Every ROW net touches LEDs that all sit on ONE ring (row 0 = hour ring, rows 1-5 = minute ring, rows 6-10 = second ring), 12 LEDs each.
So each row is routed as a full-circle arc on inner layer In1, at its own radius, with the cathode pad of every LED dropped to it by
  pad -> short F.Cu stub (tangential, then radial) -> through via at the lane radius, in the slot clockwise of the LED.
Lane pitch = (via + track)/2 + clearance  (via-driven; the same 0.35 mm pitch Evan's hand-built RGB board uses).
Everything else (columns, power, indicators) is left for freerouting with these tracks fixed.

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" polar_rows.py <in.kicad_pcb> <out.kicad_pcb>
"""
import math, re, sys
import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

TRACK, CLR, VIA_D, VIA_DR = 0.10, 0.10, 0.40, 0.20
HOLE_CLR = 0.20                              # hole-to-copper: NOT verified for JLCPCB (their page was not readable); KiCad's default is 0.25
PITCH = max((VIA_D + TRACK) / 2 + CLR, VIA_DR / 2 + TRACK / 2 + HOLE_CLR)   # lane pitch is via-driven


def mm(v):
    return v / 1e6


def build(src, dst, poly=False):
    b = pcbnew.LoadBoard(src)
    ds = b.GetDesignSettings()
    ds.m_HoleClearance = F(HOLE_CLR)
    ds.m_CopperEdgeClearance = F(0.2)
    CX = CY = 100.0
    class _N:
        def get(self, name):
            return b.FindNet(name)
    nets = _N()
    leds = {}
    for f in b.GetFootprints():
        m = re.fullmatch(r"([HMS])(\d+)", f.GetReference())
        if m:
            leds[f.GetReference()] = (m.group(1), int(m.group(2)), f)
    ring_r = {}
    for ref, (k, i, f) in leds.items():
        p = f.GetPosition()
        ring_r.setdefault(k, []).append(math.hypot(mm(p.x) - CX, mm(p.y) - CY))
    ring_r = {k: sum(v) / len(v) for k, v in ring_r.items()}
    print("ring radii", {k: round(v, 3) for k, v in ring_r.items()})

    def lane_radius(row):
        if row == 0:
            return ring_r["H"]
        if 1 <= row <= 5:
            return ring_r["M"] + (row - 3) * PITCH
        return ring_r["S"] + (row - 8) * PITCH

    def row_of(ref, kind, idx):
        if kind == "H":
            return 0
        return (idx % 5) + 1 if kind == "M" else (idx % 5) + 6

    def add_track(x1, y1, x2, y2, layer, net):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(F(x1), F(y1))); t.SetEnd(V(F(x2), F(y2))); t.SetWidth(F(TRACK)); t.SetLayer(layer); t.SetNet(net)
        b.Add(t)

    n_via = n_trk = 0
    for ref, (kind, idx, f) in leds.items():
        row = row_of(ref, kind, idx)
        net = nets.get(f"/ROW{row}")
        if net is None:
            print("no net for", ref, row); continue
        p = f.GetPosition()
        x, y = mm(p.x) - CX, mm(p.y) - CY
        r = math.hypot(x, y)
        th = math.atan2(x, -y)                            # clockwise from the top
        er = (math.sin(th), -math.cos(th))
        et = (math.cos(th), math.sin(th))
        pad = f.FindPadByNumber("1")                      # cathode, inner end
        px, py = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
        W = mm(pad.GetSize().y) if abs(mm(pad.GetSize().y)) < 2 else 0.64
        # pad size is given in the footprint frame; the tangential extent of the LED = the pad's short dimension
        # tangential half-extent of the LED copper, measured on the real pad outlines (any rotation)
        half_t = 0.0
        for pd in f.Pads():
            ps = pd.GetEffectivePolygon(pcbnew.F_Cu) if hasattr(pd, "GetEffectivePolygon") else None
            if ps is not None:
                for k in range(ps.VertexCount()):
                    vtx = ps.CVertex(k)
                    half_t = max(half_t, abs((mm(vtx.x) - (CX + x)) * et[0] + (mm(vtx.y) - (CY + y)) * et[1]))
        if half_t == 0.0:
            half_t = 0.35
        s_off = half_t + CLR + VIA_D / 2 + 0.03
        rho = lane_radius(row)
        vx, vy = CX + rho * er[0] + s_off * et[0] * 1.0 + 0.0, CY + rho * er[1] + s_off * et[1]
        # recompute the via on the lane circle exactly (keep the radius, shift the angle)
        ang = th + math.asin(max(-1, min(1, s_off / rho)))
        vx, vy = CX + rho * math.sin(ang), CY - rho * math.cos(ang)
        # stub: pad centre -> tangential offset at the pad radius -> via
        mx, my = px + s_off * et[0] * 1.0, py + s_off * et[1]
        add_track(px, py, mx, my, pcbnew.F_Cu, net)
        add_track(mx, my, vx, vy, pcbnew.F_Cu, net)
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(V(F(vx), F(vy))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(F(VIA_DR)); v.SetWidth(pcbnew.F_Cu, F(VIA_D)) if hasattr(v, "SetWidth") else None
        v.SetNet(net)
        b.Add(v)
        n_via += 1; n_trk += 2

    # lanes: one full circle per row, on In1, as four quarter arcs
    for row in range(11):
        net = nets.get(f"/ROW{row}")
        rho = lane_radius(row)
        for q in range(4):
            a0, a1 = q * math.pi / 2, (q + 1) * math.pi / 2
            am = (a0 + a1) / 2
            pt = lambda a: V(F(CX + rho * math.sin(a)), F(CY - rho * math.cos(a)))
            if poly:                                      # polyline copy, only used to hand the lanes to the autorouter (Specctra has no arcs)
                nseg = 30
                for k in range(nseg):
                    t0, t1 = a0 + (a1 - a0) * k / nseg, a0 + (a1 - a0) * (k + 1) / nseg
                    tr = pcbnew.PCB_TRACK(b)
                    tr.SetStart(pt(t0)); tr.SetEnd(pt(t1)); tr.SetWidth(F(TRACK)); tr.SetLayer(pcbnew.In1_Cu); tr.SetNet(net)
                    b.Add(tr)
                continue
            arc = pcbnew.PCB_ARC(b)
            arc.SetStart(pt(a0)); arc.SetMid(pt(am)); arc.SetEnd(pt(a1))
            arc.SetWidth(F(TRACK)); arc.SetLayer(pcbnew.In1_Cu); arc.SetNet(net)
            b.Add(arc)
    pcbnew.SaveBoard(dst, b)
    print(f"added {n_via} vias, {n_trk} stub tracks, 44 lane arcs ->", dst)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], poly=(len(sys.argv) > 3 and sys.argv[3] == "poly"))
