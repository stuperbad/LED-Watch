"""Apply the edit files of ring_stubs.py / ring_col.py: remove the straight F.Cu pieces under "remove" (layer, net, two end points in mm, either order) and add the pieces under "add":
[layer, net, a, b] = straight piece, [layer, net, "arc", start, mid, end] = arc piece (width 0.1 mm); a "remove" entry [layer, net, "arc", start, end] removes an arc; ["via", net, [x, y]] removes (remove list) or adds (add list, copy of an existing via) a via.
usage (KiCad python): apply_ring_edits.py in.kicad_pcb out.kicad_pcb edit.json [edit2.json ...]"""
import json
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
rem, add = [], []
for f in sys.argv[3:]:
    E = json.load(open(f))
    rem += E["remove"]
    add += E["add"]
b = pcbnew.LoadBoard(src)
want = {}
want_arc = {}
want_via = {}
for e in rem:
    if e[0] == "via":                      # ["via", net, [x, y]]
        want_via[(e[1], round(e[2][0], 3), round(e[2][1], 3))] = 1
        continue
    if e[2] == "arc":                      # [layer, net, "arc", start, end]: an arc piece, matched by its two end points
        want_arc[(e[0], e[1]) + tuple(sorted([(round(e[3][0], 3), round(e[3][1], 3)), (round(e[4][0], 3), round(e[4][1], 3))]))] = 1
        continue
    layer, net, a, c = e
    want[(layer, net) + tuple(sorted([(round(a[0], 3), round(a[1], 3)), (round(c[0], 3), round(c[1], 3))]))] = 1
kill = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    a = (round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3))
    c = (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))
    k = (b.GetLayerName(t.GetLayer()), t.GetNetname()) + tuple(sorted([a, c]))
    if k in want:
        kill.append(t)
        want[k] = 0
for t in b.GetTracks():
    if t.GetClass() != "PCB_ARC":
        continue
    a = (round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3))
    c = (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))
    k = (b.GetLayerName(t.GetLayer()), t.GetNetname()) + tuple(sorted([a, c]))
    if k in want_arc:
        kill.append(t)
        want_arc[k] = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        k = (t.GetNetname(), round(tomm(t.GetPosition().x), 3), round(tomm(t.GetPosition().y), 3))
        if k in want_via:
            kill.append(t)
            want_via[k] = 0
via_tpl = next((t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t not in kill), None)
for t in kill:
    b.Remove(t)
missing = sum(1 for v in want.values() if v) + sum(1 for v in want_arc.values() if v) + sum(1 for v in want_via.values() if v)
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
n_seg = n_arc = 0
for e in add:
    layer, net = e[0], e[1]
    ni = b.FindNet(net)
    if layer == "via":
        nv = via_tpl.Duplicate()
        nv.SetPosition(V(e[2]))
        nv.SetNet(ni)
        b.Add(nv)
        continue
    if e[2] == "arc":
        t = pcbnew.PCB_ARC(b)
        t.SetStart(V(e[3]))
        t.SetMid(V(e[4]))
        t.SetEnd(V(e[5]))
        n_arc += 1
    else:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(e[2]))
        t.SetEnd(V(e[3]))
        n_seg += 1
    t.SetWidth(mm(0.1))
    t.SetLayer(b.GetLayerID(layer))
    t.SetNet(ni)
    b.Add(t)
pcbnew.SaveBoard(dst, b)
print("removed %d (not found: %d), added %d pieces + %d arcs" % (len(kill), missing, n_seg, n_arc))
