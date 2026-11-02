"""Remove the inner-layer lanes of whole nets so they can be routed again from their pad fan-outs: every straight track and arc of the named nets on the given layers goes, then
the vias that no remaining track or pad of the net touches, then (repeatedly) the F.Cu/B.Cu tails whose free end touches nothing (a pad, a via or another track of the net).
Copper that still joins a pad or a via on a layer that is NOT listed stays, so the router finds the net in pieces: pad stub + via at each end.
usage (KiCad python): rip_lanes.py in.kicad_pcb out.kicad_pcb LAYERS NET [NET ...]       LAYERS e.g. In1.Cu,B.Cu     (net names starting with / need MSYS_NO_PATHCONV=1, or @file)"""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst, layers = sys.argv[1], sys.argv[2], set(sys.argv[3].split(","))
nets = sys.argv[4:]
if nets and nets[0].startswith("@"):
    nets = [ln.strip() for ln in open(nets[0][1:]) if ln.strip()]
nets = set(nets)
b = pcbnew.LoadBoard(src)
EPS = 0.02
kill = set()
snap = []
for t in b.GetTracks():
    if t.GetNetname() not in nets:
        continue
    c = t.GetClass()
    if c == "PCB_VIA":
        p = t.GetPosition()
        snap.append(dict(u=t.m_Uuid.AsString(), cls="via", net=t.GetNetname(), pts=[(tomm(p.x), tomm(p.y))], layer=None))
    else:
        pts = [(tomm(t.GetStart().x), tomm(t.GetStart().y)), (tomm(t.GetEnd().x), tomm(t.GetEnd().y))]
        snap.append(dict(u=t.m_Uuid.AsString(), cls="arc" if c == "PCB_ARC" else "trk", net=t.GetNetname(), pts=pts, layer=b.GetLayerName(t.GetLayer())))
for s in snap:
    if s["cls"] != "via" and s["layer"] in layers:
        kill.add(s["u"])
pads = [(p, f.GetReference()) for f in b.GetFootprints() for p in f.Pads()]


def on_pad(pt, net, lname):
    v = pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))
    lid = b.GetLayerID(lname)
    return any(p.GetNetname() == net and p.IsOnLayer(lid) and p.HitTest(v, mm(0.02)) for p, _ in pads)


changed = True
while changed:
    changed = False
    alive = [s for s in snap if s["u"] not in kill]
    for s in alive:
        net = s["net"]
        if s["cls"] == "via":
            x, y = s["pts"][0]
            used = any(o["cls"] != "via" and o["net"] == net and any(math.hypot(x - px, y - py) < EPS for px, py in o["pts"]) for o in alive)
            if not used and not on_pad((x, y), net, "F.Cu"):
                kill.add(s["u"]); changed = True
        elif s["cls"] == "trk":
            for i in (0, 1):
                p = s["pts"][i]
                touch = any(o is not s and o["net"] == net and (o["layer"] == s["layer"] or o["layer"] is None) and any(math.hypot(p[0] - px, p[1] - py) < EPS for px, py in o["pts"]) for o in alive)
                if not touch and not on_pad(p, net, s["layer"]):
                    kill.add(s["u"]); changed = True
                    break
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in kill:
        b.Remove(t)
by = {}
for s in snap:
    if s["u"] in kill:
        by[s["net"]] = by.get(s["net"], 0) + 1
print("removed:", by)
pcbnew.SaveBoard(dst, b)
