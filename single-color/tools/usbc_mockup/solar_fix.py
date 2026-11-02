"""solar_fix.py in.kicad_pcb out.kicad_pcb : put the cell pad SC1+ on /SOLAR_IN (it was on a separate net 'SOLAR_IN'), join it on F.Cu to the nearest /SOLAR_IN via with
centre-to-centre 0/45 degree legs, then delete every /SOLAR_IN piece that no pad needs (dead branches, duplicates), one at a time, keeping the connections of all four pads.
KiCad python; MSYS_NO_PATHCONV=1 not needed (no net name on the command line)."""
import sys, pcbnew
tomm = pcbnew.ToMM; mm = pcbnew.FromMM; V = pcbnew.VECTOR2I
b = pcbnew.LoadBoard(sys.argv[1])
NET = "/SOLAR_IN"
net = b.FindNet(NET)
pad = b.FindFootprintByReference("SC1+").Pads()[0]
print("cell pad was on", repr(pad.GetNetname()))
pad.SetNet(net)
pc = pad.GetPosition()
# nearest /SOLAR_IN via that has an F.Cu annulus (every via here is through)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == NET]
v = min(vias, key=lambda t: (tomm(t.GetPosition().x - pc.x)) ** 2 + (tomm(t.GetPosition().y - pc.y)) ** 2)
vp = v.GetPosition()
dx = tomm(pc.x - vp.x); dy = tomm(pc.y - vp.y)
print("nearest via", round(tomm(vp.x), 3), round(tomm(vp.y), 3), "dx dy", round(dx, 3), round(dy, 3))
# horizontal leg first, then a 45 degree leg ending on the pad centre
d = min(abs(dx), abs(dy)); sx = 1 if dx > 0 else -1; sy = 1 if dy > 0 else -1
corner = V(pc.x - sx * mm(d), vp.y if abs(dx) >= abs(dy) else pc.y - sy * mm(d))
if abs(dx) < abs(dy): corner = V(vp.x, pc.y - sy * mm(d))
w = mm(0.1)
def add(a, c):
    t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetLayer(pcbnew.F_Cu); t.SetWidth(w); t.SetNet(net); b.Add(t)
legs = [(vp, corner), (corner, pc)]
for a, c in legs:
    if a != c: add(a, c); print("  F.Cu", round(tomm(a.x), 3), round(tomm(a.y), 3), "->", round(tomm(c.x), 3), round(tomm(c.y), 3))
def unc():
    b.BuildConnectivity(); c = b.GetConnectivity(); c.RecalculateRatsnest(); return c.GetUnconnectedCount(False)
base = unc(); print("open connections after the new link:", base)
items = [t for t in b.GetTracks() if t.GetNetname() == NET]
grave = []; n = 0
# KiCad counts a floating piece of copper as an open connection too, so a dead branch only comes apart from its far end: repeat until nothing more goes
while True:
    gone = 0
    for t in [t for t in b.GetTracks() if t.GetNetname() == NET]:
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu and any(t.GetStart() == a and t.GetEnd() == c for a, c in legs): continue
        b.Remove(t); grave.append(t)
        if unc() == base: gone += 1
        else: b.Add(t); grave.pop()
    n += gone
    if not gone: break
print("removed", n, "of", len(items))
pcbnew.SaveBoard(sys.argv[2], b)
