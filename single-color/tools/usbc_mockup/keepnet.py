"""keepnet.py in.kicad_pcb out.kicad_pcb NET [NET ...] : strip a net's routing back to its pad escapes (a track with an end inside one of the net's pads, and the via at its far end);
every other track and via of the net is deleted so the net can be routed again. Env ADDVIA=net,net adds a via at the far end of a kept stub that has none. KiCad python (use MSYS_NO_PATHCONV=1 for net names with a leading /)."""
import sys, math, os
import pcbnew
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
nets = sys.argv[3:]
grave = []
for n in nets:
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == n]
    items = [t for t in b.GetTracks() if t.GetNetname() == n]
    keep = set()
    for t in items:
        if t.GetClass() != "PCB_TRACK":
            continue
        for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
            if any(p.IsOnLayer(t.GetLayer()) and p.HitTest(e) for p in pads):
                keep.add(id(t))
                for v in items:
                    if v.GetClass() == "PCB_VIA" and math.hypot(tomm(v.GetPosition().x - o.x), tomm(v.GetPosition().y - o.y)) < 0.02:
                        keep.add(id(v))
    # a via at the far end of every kept stub that has none (the pad-exit rule: stub along the pad axis, via at its end)
    addv = n in os.environ.get("ADDVIA", "").split(",")
    vtpl = next((t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"), None)
    for t in items:
        if id(t) in keep and t.GetClass() == "PCB_TRACK":
            for e in (t.GetStart(), t.GetEnd()):
                if any(p.IsOnLayer(t.GetLayer()) and p.HitTest(e) for p in pads):
                    continue
                if addv and not any(v.GetClass() == "PCB_VIA" and id(v) in keep and math.hypot(tomm(v.GetPosition().x - e.x), tomm(v.GetPosition().y - e.y)) < 0.02 for v in items):
                    nv = vtpl.Duplicate(); nv.SetPosition(e); nv.SetNetCode(t.GetNetCode()); b.Add(nv)
                    print("  added via at", round(tomm(e.x), 3), round(tomm(e.y), 3))
    k = 0
    for t in items:
        if id(t) in keep:
            continue
        b.Remove(t); grave.append(t); k += 1
    print(n, "kept", len(keep), "removed", k)
pcbnew.SaveBoard(sys.argv[2], b)
