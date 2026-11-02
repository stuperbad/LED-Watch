"""Apply an edit list from octo_tidy.py: remove the straight tracks listed under "remove" (layer, net, two end points in mm, either order) and add the straight tracks under "add" (layer, net, a, b).
usage (KiCad python): apply_tidy.py in.kicad_pcb out.kicad_pcb edit.json"""
import json
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst, edit = sys.argv[1:4]
E = json.load(open(edit))
b = pcbnew.LoadBoard(src)
want = {}
for layer, net, a, c in E["remove"]:
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
for t in kill:
    b.Remove(t)
missing = sum(1 for v in want.values() if v)
for layer, net, a, c in E["add"]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
    t.SetWidth(mm(0.1))
    t.SetLayer(b.GetLayerID(layer))
    ni = b.FindNet(net)
    t.SetNet(ni)
    b.Add(t)
pcbnew.SaveBoard(dst, b)
print("removed %d (not found: %d), added %d" % (len(kill), missing, len(E["add"])))
