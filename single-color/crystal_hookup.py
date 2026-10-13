"""Hook up the 32.768 kHz crystal by hand, the way the first hand-built revision did it (see LED Watch - RGB version ... .kicad_pcb: Y1 + two caps directly under it).
  - XTAL1 / XTAL2: MCU pads -> short F.Cu tracks (no vias, nothing under the crystal) -> crystal pads
  - each load cap sits straight under its crystal pad: signal pad up (joined to the crystal pad), ground pad down -> ground via beside the cap
  - a GND zone on In2.Cu runs under everything (nothing else may be routed on In2 under the crystal)
usage: python crystal_hookup.py in.kicad_pcb out.kicad_pcb
"""
import sys
import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

W = 0.12          # track width
VIA_D, VIA_H = 0.30, 0.15
b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, net):
    for p in fp[ref].Pads():
        if p.GetNetname() == net:
            return p
    raise SystemExit(f"{ref}: no pad on net {net}")


def pt(p):
    q = p.GetPosition()
    return q.x / 1e6, q.y / 1e6


def track(a, c, net, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(F(a[0]), F(a[1]))); t.SetEnd(V(F(c[0]), F(c[1]))); t.SetWidth(F(W)); t.SetLayer(layer); t.SetNet(b.FindNet(net))
    b.Add(t)


def via(p, net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(F(p[0]), F(p[1]))); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetDrill(F(VIA_H)); v.SetWidth(pcbnew.F_Cu, F(VIA_D)); v.SetNet(b.FindNet(net))
    b.Add(v)


mcu = {n: pt(pad("U1", n)) for n in ("/XTAL1", "/XTAL2")}
cry = {n: pt(pad("Y1", n)) for n in ("/XTAL1", "/XTAL2")}
import math
vertical = abs(cry["/XTAL1"][0] - cry["/XTAL2"][0]) < 0.5          # crystal standing upright to the right of the MCU (layout B) instead of below it (layout A)
R_G = 13.9                                                      # guard stays inside the hour ring's via/pad band
stitch = []
if not vertical:
    for cap, net in (("C20", "/XTAL1"), ("C21", "/XTAL2")):
        px, py = mcu[net]; cx, cy = cry[net]
        # MCU pad -> straight out of the pad -> 45 degrees -> into the crystal pad from the top (nothing runs under the crystal)
        ex = py + 0.7
        ey = ex + abs(cx - px)
        track((px, py), (px, ex), net)
        track((px, ex), (cx, ey), net)
        # crystal pad -> cap signal pad (cap sits straight below the pad)
        cs = pt(pad(cap, net)); cg = pt(pad(cap, "GND"))
        track((cx, cy + 0.6), cs, net) if cs[1] > cy else None
        # ground pad -> ground via on the inner side of the cap (between the two caps)
        side = 1 if net == "/XTAL1" else -1
        v = (cg[0] + side * 0.8, cg[1])
        track(cg, v, "GND")
        via(v, "GND")
        print(net, "MCU", (round(px, 2), round(py, 2)), "-> crystal", (round(cx, 2), round(cy, 2)), "| cap", cap, "signal pad", tuple(round(c, 2) for c in cs), "ground via", tuple(round(c, 2) for c in v))
    cx0 = pt(pad("Y1", "/XTAL1"))[0]; cx1 = pt(pad("Y1", "/XTAL2"))[0]; yc = pt(pad("Y1", "/XTAL1"))[1]
    my = mcu["/XTAL1"][1]
    gx0, gx1, gy0, gy1 = cx0 - 1.6, cx1 + 2.7, my + 0.6, 100.0 + 14.5
    stitch = [(cx1 + 1.7, yc - 0.9), (cx1 + 1.7, yc + 0.9), (cx1 + 1.7, yc + 2.4), (cx0 - 1.2, yc + 2.9)]
else:
    ys = []
    for cap, net in (("C20", "/XTAL1"), ("C21", "/XTAL2")):
        px, py = mcu[net]; qx, qy = cry[net]
        xv = qx - (1.75 if net == "/XTAL1" else 1.15)             # vertical leg: the lower pin's leg sits further left, so the two never cross; both stay well clear of the MCU pads (via channel)
        track((px, py), (xv, py), net)                         # out of the MCU pad (east)
        track((xv, py), (xv, qy), net)                         # straight down to the height of its crystal pad
        track((xv, qy), (qx - 0.45, qy), net)                  # into the crystal pad from the left
        cs = pt(pad(cap, net)); cg = pt(pad(cap, "GND"))
        track((qx + 0.4, qy), cs, net)                         # crystal pad -> cap signal pad (cap sits right of the pad)
        v = (cg[0], cg[1] + (0.95 if net == "/XTAL2" else -0.95))        # inward: the upper cap's via sits below its ground pad, the lower cap's above it
        track(cg, v, "GND"); via(v, "GND")
        ys.append(qy)
        print(net, "MCU", (round(px, 2), round(py, 2)), "-> crystal", (round(qx, 2), round(qy, 2)), "| cap", cap, "signal pad", tuple(round(c, 2) for c in cs), "ground via", tuple(round(c, 2) for c in v))
    qx = cry["/XTAL1"][0]; ytop, ybot = min(ys), max(ys)
    gx0, gx1, gy0, gy1 = qx - 1.05, qx + 3.05, ytop - 1.3, ybot + 1.3     # tight: crystal and its two caps with ~0.6 mm to spare, corners chamfered below
    stitch = [(qx + 0.4, ytop - 1.0), (qx + 0.4, ybot + 1.0)]       # the two inward cap vias already sit in the middle

# ground guard (datasheet DS40002247B 4.5.1): grounded copper on the top layer around the crystal circuit, tied to the solid ground plane (In2) with vias;
# the filler keeps 0.2 mm from every other net, so the guard simply fills what is free between the crystal block and its neighbours
def clamp(x, y):
    r = math.hypot(x - 100.0, y - 100.0)
    return (x, y) if r <= R_G else (100.0 + (x - 100.0) * R_G / r, 100.0 + (y - 100.0) * R_G / r)
ch_ = 0.8
pts = [(gx0 + ch_, gy0), (gx1 - ch_, gy0), (gx1, gy0 + ch_), (gx1, gy1 - ch_), (gx1 - ch_, gy1), (gx0 + ch_, gy1), (gx0, gy1 - ch_), (gx0, gy0 + ch_)]
if not vertical:
    def circ_y(x):
        return 100.0 + math.sqrt(max(R_G ** 2 - (x - 100.0) ** 2, 0.0))
    pts = [(gx0, gy0), (gx1, gy0), (gx1, circ_y(gx1))] + [(gx1 + (gx0 - gx1) * k / 12, circ_y(gx1 + (gx0 - gx1) * k / 12)) for k in range(1, 12)] + [(gx0, circ_y(gx0))]
gz = pcbnew.ZONE(b)
gz.SetLayer(pcbnew.F_Cu); gz.SetNet(b.FindNet("GND"))
so = pcbnew.SHAPE_POLY_SET(); so.NewOutline()
for x, y in pts:
    so.Append(F(x), F(y))
gz.SetOutline(so)
gz.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); gz.SetLocalClearance(F(0.2)); gz.SetMinThickness(F(0.15))
b.Add(gz)
def free_of_pads(vx, vy, m=0.5):
    """a ground via must keep hole clearance (0.2 mm) + pad radius from every other-net pad: test against each pad's bounding box grown by m mm"""
    for f_ in b.GetFootprints():
        for p_ in f_.Pads():
            if p_.GetNetname() in ("GND", ""):
                continue
            bb = p_.GetBoundingBox(); bb.Inflate(F(m))
            if bb.Contains(V(F(vx), F(vy))):
                return False
    for t_ in b.GetTracks():
        if t_.GetClass() == "PCB_TRACK" and t_.GetNetname() not in ("GND", ""):
            st, en = t_.GetStart(), t_.GetEnd()
            ax_, ay_, bx_, by_ = st.x / 1e6, st.y / 1e6, en.x / 1e6, en.y / 1e6
            dx_, dy_ = bx_ - ax_, by_ - ay_
            L2 = dx_ * dx_ + dy_ * dy_
            t__ = 0.0 if L2 == 0 else max(0.0, min(1.0, ((vx - ax_) * dx_ + (vy - ay_) * dy_) / L2))
            if math.hypot(vx - (ax_ + t__ * dx_), vy - (ay_ + t__ * dy_)) < 0.45:
                return False
    return True


for vx, vy in stitch:
    if (vx - 100.0) ** 2 + (vy - 100.0) ** 2 < 14.0 ** 2 and free_of_pads(vx, vy):
        via((vx, vy), "GND")
    else:
        print("stitching via skipped (no room):", round(vx, 2), round(vy, 2))

# GND zone on In2 (full board inside the edge)
ol = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(ol, True)
try:
    ol.Deflate(F(0.4), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 10000)
except Exception:
    ol.Inflate(-F(0.4), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 10000)
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.In2_Cu); z.SetNet(b.FindNet("GND")); z.SetOutline(ol)
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetLocalClearance(F(0.2)); z.SetMinThickness(F(0.1))
b.Add(z)
pcbnew.SaveBoard(sys.argv[2], b)
print("saved", sys.argv[2])
