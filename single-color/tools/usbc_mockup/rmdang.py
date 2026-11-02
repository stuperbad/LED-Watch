"""rmdang.py in.kicad_pcb drc.json out.kicad_pcb [x0] : delete every track/via that DRC flags as dangling when deleting it leaves the open-connection count unchanged (one at a time, re-tested);
in.kicad_pcb must be the zone-filled board the DRC ran on; items left of x0 (default 0) are skipped. KiCad python."""
import sys, json, math
import pcbnew
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
d = json.load(open(sys.argv[2]))
x0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0


def unc():
    b.BuildConnectivity()
    c = b.GetConnectivity()
    c.RecalculateRatsnest()
    return c.GetUnconnectedCount(False)


base = unc()
items = [(v["type"], v["items"][0]["pos"]["x"], v["items"][0]["pos"]["y"]) for v in d["violations"] if v["type"] in ("via_dangling", "track_dangling")]


def find(typ, x, y):
    best = None
    for t in b.GetTracks():
        isv = t.GetClass() == "PCB_VIA"
        if (typ == "via_dangling") != isv:
            continue
        if isv:
            p = t.GetPosition()
            dist = math.hypot(tomm(p.x) - x, tomm(p.y) - y)
        else:
            dist = min(math.hypot(tomm(q.x) - x, tomm(q.y) - y) for q in (t.GetStart(), t.GetEnd()))
        if best is None or dist < best[0]:
            best = (dist, t)
    return best


keep = []
n = 0
for typ, x, y in items:
    if x < x0:
        continue
    f = find(typ, x, y)
    if f is None or f[0] > 0.2:
        continue
    t = f[1]
    desc = "%s %s %s" % (typ, t.GetNetname(), (round(x, 2), round(y, 2)))
    b.Remove(t)
    keep.append(t)
    if unc() == base:
        print("deleted", desc)
        n += 1
    else:
        b.Add(t)
        keep.remove(t)
        print("kept   ", desc)
unc()
pcbnew.SaveBoard(sys.argv[3], b)
print("deleted", n)
