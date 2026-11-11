"""via_centre_fix.py IN OUT [--dry] (KiCad python): every straight track end that lies inside a via's copper circle (same net, layer present) but not on its centre is moved onto the centre
(owner's rule: a trace ends exactly on the via centre).  Arc ends are never moved (ring lanes) and are listed.  A piece whose both ends are in the via (a sliver) is deleted."""
import sys, math, collections, pcbnew
mm = pcbnew.ToMM; a = sys.argv[1:]; dry = "--dry" in a
b = pcbnew.LoadBoard(a[0]); NM = 1e6
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
grid = collections.defaultdict(list)
for v in vias: grid[(int(v.GetPosition().x // 400000), int(v.GetPosition().y // 400000))].append(v)
moved = 0; skipped = []; arcs = []; vanish = []
for t in list(b.GetTracks()):
    if t.GetClass() not in ("PCB_TRACK", "PCB_ARC"): continue
    for which in ("start", "end"):
        e = t.GetStart() if which == "start" else t.GetEnd()
        gx, gy = int(e.x // 400000), int(e.y // 400000)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for v in grid[(gx + dx, gy + dy)]:
                    if v.GetNetname() != t.GetNetname() or not v.IsOnLayer(t.GetLayer()): continue
                    c = v.GetPosition(); d = math.hypot(e.x - c.x, e.y - c.y)
                    if d <= 2000 or d > v.GetWidth(pcbnew.F_Cu) / 2: continue
                    if t.GetClass() == "PCB_ARC": arcs.append((t.GetNetname(), round(mm(c.x), 3), round(mm(c.y), 3), round(mm(d), 3))); continue
                    o = t.GetEnd() if which == "start" else t.GetStart()
                    if math.hypot(o.x - c.x, o.y - c.y) < 20000: vanish.append(t); continue                       # a sliver inside the via: delete it (both ends are in the via anyway)
                    if not dry:
                        if which == "start": t.SetStart(c)
                        else: t.SetEnd(c)
                    moved += 1
vanish = list({id(t): t for t in vanish}.values())
if not dry:
    for t in vanish: b.Remove(t)
print("slivers inside vias deleted:", len(vanish))
print("track ends moved onto via centres:", moved, "| arc ends left:", len(arcs), arcs[:6], "| skipped:", skipped)
if not dry: pcbnew.SaveBoard(a[1], b)
