"""Hook up the 32.768 kHz crystal for the layout where Y1 stands upright to the LEFT of the MCU (MCU rotated 180 degrees) with its two load caps one column further left.
  - XTAL2: straight west from its MCU pad into the lower crystal pad
  - XTAL1: west to just beyond the crystal, up into the upper crystal pad (outside the via channel of the MCU's west-edge fan-out)
  - load caps: signal pad straight into its crystal pad, both ground pads tied to one ground via between them
  (the F.Cu ground guard zone and the In2 ground plane are already on the board; nothing else may be routed in crystal_exclude.txt)
usage (KiCad python): crystal_left.py in.kicad_pcb out.kicad_pcb"""
import sys

import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

W = 0.12
VIA_D, VIA_H = 0.30, 0.15
b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, net):
    for p in fp[ref].Pads():
        if p.GetNetname() == net:
            return p
    raise SystemExit("%s: no pad on net %s" % (ref, net))


def pt(p):
    q = p.GetPosition()
    return q.x / 1e6, q.y / 1e6


def edge_r(p):
    bb = p.GetBoundingBox()
    return bb.GetRight() / 1e6


def edge_l(p):
    bb = p.GetBoundingBox()
    return bb.GetX() / 1e6


def track(a, c, net):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(F(a[0]), F(a[1])))
    t.SetEnd(V(F(c[0]), F(c[1])))
    t.SetWidth(F(W))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(b.FindNet(net))
    b.Add(t)


def via(p, net):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(F(p[0]), F(p[1])))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(F(VIA_H))
    v.SetWidth(pcbnew.F_Cu, F(VIA_D))
    v.SetNet(b.FindNet(net))
    b.Add(v)


m1, m2 = pt(pad("U1", "/XTAL1")), pt(pad("U1", "/XTAL2"))
y1, y2 = pad("Y1", "/XTAL1"), pad("Y1", "/XTAL2")
c1, c2 = pt(y1), pt(y2)
assert c1[1] < c2[1] and m1[1] < m2[1], "crystal pads / MCU pads not in the expected order (XTAL1 above XTAL2)"
xr = max(edge_r(y1), edge_r(y2))                       # right edge of the crystal pads
bb1, bb2 = y1.GetBoundingBox(), y2.GetBoundingBox()
# XTAL1 (northern MCU pin): west through the fan-out channel, then up right beside the crystal, into the upper pad from the right
xv1 = xr + 0.15
ye1 = bb1.GetBottom() / 1e6 - 0.15
track(m1, (xv1, m1[1]), "/XTAL1")
track((xv1, m1[1]), (xv1, ye1), "/XTAL1")
track((xv1, ye1), (xr - 0.05, ye1), "/XTAL1")
# XTAL2 (southern MCU pin): west, a short step down, into the lower pad from the right
xv2 = xr + 0.30
ye2 = bb2.GetY() / 1e6 + 0.15
track(m2, (xv2, m2[1]), "/XTAL2")
track((xv2, m2[1]), (xv2, ye2), "/XTAL2")
track((xv2, ye2), (xr - 0.05, ye2), "/XTAL2")
# load caps: signal pad -> crystal pad (left edge), grounds -> one via between the caps
for cap, net, yp in (("C20", "/XTAL1", c1), ("C21", "/XTAL2", c2)):
    cs = pt(pad(cap, net))
    track((cs[0] + 0.28, cs[1]), (edge_l(y1) + 0.1, cs[1]), net)
g1, g2 = pt(pad("C20", "GND")), pt(pad("C21", "GND"))
gv = (g1[0], (g1[1] + g2[1]) / 2)
track(g1, gv, "GND")
track(g2, gv, "GND")
via(gv, "GND")
print("XTAL tracks, cap links and ground via at (%.2f, %.2f) added" % gv)
pcbnew.SaveBoard(sys.argv[2], b)
