"""tailcut.py in.kicad_pcb out.kicad_pcb REF.PAD : delete the copper that serves only this pad: starting at the pad, follow the net's tracks and vias until the first place where the copper branches (three or more
neighbours) or reaches another pad; everything before that is the pad's private tail. The pad can then be routed again to the nearest copper of its net. KiCad python."""
import sys, math, collections
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
ref, num = sys.argv[3].split(".")
fp = b.FindFootprintByReference(ref); pad = next(p for p in fp.Pads() if p.GetNumber() == num)
net = pad.GetNetCode()
items = [t for t in b.GetTracks() if t.GetNetCode() == net and t.GetClass() != "PCB_ARC"]
pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == net and not (f.GetReference() == ref and p.GetNumber() == num)]
xy = lambda p: (tomm(p.x), tomm(p.y))


def seg(t):
    return xy(t.GetStart()), xy(t.GetEnd())


def dseg(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)


def touch(a, c):
    if a.GetClass() == "PCB_VIA" and c.GetClass() == "PCB_VIA":
        return math.hypot(*(xy(a.GetPosition())[i] - xy(c.GetPosition())[i] for i in (0, 1))) < 0.3
    if a.GetClass() == "PCB_VIA" or c.GetClass() == "PCB_VIA":
        v, t = (a, c) if a.GetClass() == "PCB_VIA" else (c, a)
        if not v.IsOnLayer(t.GetLayer()):
            return False
        s, e = seg(t)
        return dseg(xy(v.GetPosition()), s, e) < tomm(v.GetWidth(t.GetLayer())) / 2 + 0.05
    if a.GetLayer() != c.GetLayer():
        return False
    sa, ea = seg(a); sc, ec = seg(c)
    return min(dseg(p, sc, ec) for p in (sa, ea)) < 0.06 or min(dseg(p, sa, ea) for p in (sc, ec)) < 0.06


adj = collections.defaultdict(set)
for i, a in enumerate(items):
    for j in range(i + 1, len(items)):
        if touch(a, items[j]):
            adj[i].add(j); adj[j].add(i)


def on_pad(t, p):
    """True when track t (on a layer the pad is on) or via t has an end / centre on pad p"""
    ends = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
    ok_layer = (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)) if t.GetClass() == "PCB_VIA" else p.IsOnLayer(t.GetLayer())
    return ok_layer and any(p.HitTest(e, mm(0.05)) for e in ends)


start = [i for i, t in enumerate(items) if on_pad(t, pad)]
tail = set(); frontier = list(start); seen = set(start)
while frontier:
    i = frontier.pop()
    t = items[i]
    touches_other_pad = any(on_pad(t, q) for q in pads)
    nb = adj[i] - seen
    if touches_other_pad or len(adj[i]) >= 3 and i not in start:
        continue                 # branch point or another pad: it stays
    tail.add(i)
    for j in nb:
        seen.add(j); frontier.append(j)
grave = []
for i in tail:
    b.Remove(items[i]); grave.append(items[i])
print("tail of %s: %d pieces removed, %.1f mm" % (sys.argv[3], len(tail), sum(tomm(items[i].GetLength()) for i in tail if items[i].GetClass() != "PCB_VIA")))
pcbnew.SaveBoard(sys.argv[2], b)
