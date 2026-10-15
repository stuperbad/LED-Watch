"""
Polar router for the white board: ROW lanes (concentric arcs on In1) + COLUMN trunks (radial lines and arcs on F.Cu).

Rules are JLCPCB's own (JLCPCB-RULES.md): track 0.10, copper clearance 0.10, via 0.30 pad / 0.15 hole, via hole-to-copper 0.20 (we use 0.22).
Geometry (all derived from the placed LED rings, nothing hand-tuned per board):
  rows    : each ROW net touches 12 LEDs of ONE ring.  Cathode pad -> F.Cu stub -> through via at the lane radius in the slot clockwise of the LED.
            Lane radii are spaced by  drill/2 + track/2 + hole_clr  (0.345 mm) because a via pierces every layer.
  columns : each COL net = one 30-degree sector (1 hour + 5 minute + 5 second LEDs).  The series resistor R sits ON the trunk line at the
            sector boundary; trunk = pad -> radial -> short arc -> radial through the boundary slots of the minute and second rings.
            Anode arcs run just outside each ring's via band and are tied to every anode pad with a short radial stub.
  Everything is clipped against hole/pad/track clearances by construction; KiCad DRC is the judge.

  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" polar_route.py in.kicad_pcb out.kicad_pcb [poly]
"""
import math, re, sys
import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

W = 0.10            # track width
CLR = 0.10          # copper to copper
VIA_D, VIA_H = 0.30, 0.15
HOLE_CLR = 0.22     # hole edge to other-net copper: JLCPCB via hole to copper / to track = 0.20 (+0.02 margin); see JLCPCB-RULES.md
PITCH = VIA_H / 2 + W / 2 + HOLE_CLR          # 0.345 lane pitch
CX = CY = 100.0


def mm(v):
    return v / 1e6


def pol(r, deg):
    a = math.radians(deg)
    return CX + r * math.sin(a), CY - r * math.cos(a)


class Router:
    def __init__(self, board, poly=False):
        self.b = board
        self.poly = poly
        ds = board.GetDesignSettings()
        ds.m_HoleClearance = F(0.20); ds.m_CopperEdgeClearance = F(0.3); ds.m_HoleToHoleMin = F(0.2)
        for nm in ('m_ViasMinAnnulus', 'm_MinAnnulus', 'm_ViasMinAnnularWidth'):
            if hasattr(ds, nm):
                setattr(ds, nm, F(0.05))
        self.leds = {}
        for f in board.GetFootprints():
            m = re.fullmatch(r"([HMS])(\d+)", f.GetReference())
            if m:
                p = f.GetPosition()
                x, y = mm(p.x) - CX, mm(p.y) - CY
                self.leds[f.GetReference()] = dict(kind=m.group(1), idx=int(m.group(2)), fp=f, r=math.hypot(x, y), th=math.degrees(math.atan2(x, -y)) % 360)
        self.ring_r = {k: sum(v["r"] for v in self.leds.values() if v["kind"] == k) / sum(1 for v in self.leds.values() if v["kind"] == k) for k in "HMS"}
        self.n_via = self.n_trk = self.n_arc = 0

    # ---- primitives
    def net(self, name):
        return self.b.FindNet(name)

    def track(self, p1, p2, layer, net):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(V(F(p1[0]), F(p1[1]))); t.SetEnd(V(F(p2[0]), F(p2[1]))); t.SetWidth(F(W)); t.SetLayer(layer); t.SetNet(net)
        self.b.Add(t); self.n_trk += 1

    def arc(self, r, a0, a1, layer, net):
        """arc of radius r from angle a0 to a1 (degrees clockwise from the top), as a real arc (or polyline when poly=True)"""
        if abs(a1 - a0) < 1e-6:
            return
        if self.poly:
            n = max(2, int(abs(a1 - a0) / 4.0))
            for k in range(n):
                self.track(pol(r, a0 + (a1 - a0) * k / n), pol(r, a0 + (a1 - a0) * (k + 1) / n), layer, net)
            return
        am = (a0 + a1) / 2
        s, m, e = pol(r, a0), pol(r, am), pol(r, a1)
        arc = pcbnew.PCB_ARC(self.b)
        arc.SetStart(V(F(s[0]), F(s[1]))); arc.SetMid(V(F(m[0]), F(m[1]))); arc.SetEnd(V(F(e[0]), F(e[1])))
        arc.SetWidth(F(W)); arc.SetLayer(layer); arc.SetNet(net)
        self.b.Add(arc); self.n_arc += 1

    def via(self, p, net):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(F(p[0]), F(p[1]))); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetDrill(F(VIA_H))
        v.SetWidth(pcbnew.F_Cu, F(VIA_D)) if hasattr(v, "SetWidth") else None
        v.SetNet(net)
        self.b.Add(v); self.n_via += 1

    def half_t(self, led):
        """tangential half extent of an LED's copper (real pad outlines)"""
        f = led["fp"]; th = math.radians(led["th"])
        et = (math.cos(th), math.sin(th))
        c = f.GetPosition(); cx, cy = mm(c.x), mm(c.y)
        h = 0.0
        for pd in f.Pads():
            ps = pd.GetEffectivePolygon(pcbnew.F_Cu)
            for k in range(ps.VertexCount()):
                v = ps.CVertex(k)
                h = max(h, abs((mm(v.x) - cx) * et[0] + (mm(v.y) - cy) * et[1]))
        return h

    def pad_polar(self, led, number):
        pd = led["fp"].FindPadByNumber(number)
        x, y = mm(pd.GetPosition().x) - CX, mm(pd.GetPosition().y) - CY
        return math.hypot(x, y), math.degrees(math.atan2(x, -y)) % 360

    def pad_radial_edges(self, led, number):
        """(inner edge radius, outer edge radius) of a pad measured along the LED's radial direction"""
        pd = led["fp"].FindPadByNumber(number)
        th = math.radians(led["th"]); er = (math.sin(th), -math.cos(th))
        c = led["fp"].GetPosition()
        ps = pd.GetEffectivePolygon(pcbnew.F_Cu)
        vals = [((mm(ps.CVertex(k).x) - CX) * er[0] + (mm(ps.CVertex(k).y) - CY) * er[1]) for k in range(ps.VertexCount())]
        return min(vals), max(vals)

    # ---- rows
    def lane_radius(self, row):
        if row == 0:
            return self.ring_r["H"]
        if 1 <= row <= 5:
            return self.ring_r["M"] + (row - 3) * PITCH
        return self.ring_r["S"] + (row - 8) * PITCH

    def route_rows(self):
        self.via_pos = {}
        for ref, d in self.leds.items():
            row = 0 if d["kind"] == "H" else ((d["idx"] % 5) + (1 if d["kind"] == "M" else 6))
            net = self.net(f"/ROW{row}")
            rho = self.lane_radius(row)
            ht = self.half_t(d)
            s_off = ht + HOLE_CLR + VIA_H / 2 + 0.02                      # via hole to the LED's anode pad >= 0.30
            dang = math.degrees(math.asin(s_off / rho))
            v = pol(rho, d["th"] + dang)
            pr, pa = self.pad_polar(d, "1")                               # cathode pad (inner end)
            p0 = pol(pr, pa)
            # stub: pad centre -> tangential to the slot at the pad radius -> radial to the via radius -> via
            tang = pol(pr, d["th"] + math.degrees(math.asin(s_off / pr)))
            self.track(p0, tang, pcbnew.F_Cu, net)
            self.track(tang, v, pcbnew.F_Cu, net)
            self.via(v, net)
            d["row"] = row; d["via_ang"] = d["th"] + dang; d["via_r"] = rho
        for row in range(11):
            net = self.net(f"/ROW{row}")
            rho = self.lane_radius(row)
            for q in range(4):
                self.arc(rho, q * 90.0, (q + 1) * 90.0, pcbnew.In1_Cu, net)

    # ---- columns
    def route_columns(self, res_ref=None):
        rM, rS, rH = self.ring_r["M"], self.ring_r["S"], self.ring_r["H"]
        # via band of each ring (lane radii) and the radial extent of the anode (outer) pads
        band_out = {"M": rM + 2 * PITCH, "S": rS + 2 * PITCH, "H": rH}
        arc_off = VIA_H / 2 + HOLE_CLR + W / 2 + 0.03                      # arc centre-line distance from the outermost via of the ring
        r_aM = band_out["M"] + arc_off
        r_aS = band_out["S"] + arc_off
        # hour: jog arc just beyond the hour pad
        hour0 = self.leds["H1"]
        h_in, h_out = self.pad_radial_edges(hour0, "2")
        r_j1 = h_out + 0.45
        report = []
        for c in range(12):
            net = self.net(f"/COL{c}")
            # ----- trunk angle: inside the boundary slot, beyond the previous LED's via, clear of the next LED's pad
            phi = 30.0 * c - 1.9
            hour = self.leds["H%d" % (c if c else 12)]
            # resistor R{c+1}: LED-side pad 1 (outward)
            R = None
            for f in self.b.GetFootprints():
                if f.GetReference() == f"R{c + 1}":
                    R = f
            pad1 = R.FindPadByNumber("1")
            px, py = mm(pad1.GetPosition().x) - CX, mm(pad1.GetPosition().y) - CY
            pr, pa = math.hypot(px, py), math.degrees(math.atan2(px, -py)) % 360
            # trunk: R pad -> radial to r_j1 -> arc to the hour LED angle (passing phi) ; hour stub from its anode pad
            self.track(pol(pr, pa), pol(r_j1, pa), pcbnew.F_Cu, net)
            hth = hour["th"] if hour["th"] < 180 or c == 0 else hour["th"] - 360
            hth = 30.0 * c
            a_start = pa if pa < 180 else pa - 360
            a_start = (30.0 * c) + ((pa - 30.0 * c + 180) % 360 - 180)
            self.arc(r_j1, a_start, hth, pcbnew.F_Cu, net)
            hp_r, hp_a = self.pad_polar(hour, "2")
            self.track(pol(hp_r, 30.0 * c), pol(r_j1, 30.0 * c), pcbnew.F_Cu, net)
            # radial trunk through the boundary slots of the M and S rings up to the S arc level
            self.arc(r_j1, a_start, phi, pcbnew.F_Cu, net) if False else None
            self.track(pol(r_j1, phi), pol(r_aS, phi), pcbnew.F_Cu, net)
            # M and S anode arcs + stubs
            for kind, r_a in (("M", r_aM), ("S", r_aS)):
                last = None
                for i in range(5):
                    ref = f"{kind}{5 * c + i}"
                    d = self.leds[ref]
                    pr2, pa2 = self.pad_polar(d, "2")                      # anode pad (outer end)
                    ang = 30.0 * c + 6.0 * i
                    self.track(pol(pr2, ang), pol(r_a, ang), pcbnew.F_Cu, net)
                    last = ang
                self.arc(r_a, phi, last, pcbnew.F_Cu, net)
            # the hour jog arc continues from phi to nothing further; connect trunk to the M arc level
            self.track(pol(r_aM, phi), pol(r_aM, phi), pcbnew.F_Cu, net) if False else None
        return dict(r_aM=r_aM, r_aS=r_aS, r_j1=r_j1)


def build(src, dst, poly=False):
    b = pcbnew.LoadBoard(src)
    R = Router(b, poly)
    print("ring radii", {k: round(v, 3) for k, v in R.ring_r.items()}, "lane pitch", round(PITCH, 3))
    R.route_rows()
    info = R.route_columns()
    print("columns:", {k: round(v, 3) for k, v in info.items()})
    if list(b.Zones()):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())                      # re-fill the ground plane around the polar vias
    pcbnew.SaveBoard(dst, b)
    print(f"vias {R.n_via}, tracks {R.n_trk}, arcs {R.n_arc} ->", dst)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], poly=(len(sys.argv) > 3 and sys.argv[3] == "poly"))
