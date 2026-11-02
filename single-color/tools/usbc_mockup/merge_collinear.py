"""merge_collinear.py in.kicad_pcb out.kicad_pcb : join two straight pieces of the same net, layer and width that meet end to end on one line with nothing else at the joint (no third piece, pad or via).
Does not change the copper, only the number of pieces. Ring nets (/COLn, /ROWn) are skipped. KiCad python."""
import sys, math, re, collections
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
ring = re.compile(r"^/(COL\d+|ROW\d+)$")
key = lambda p: (round(tomm(p.x), 3), round(tomm(p.y), 3))
merged = 0
grave = []   # removed pieces stay referenced: SWIG frees them otherwise and the next board scan breaks
while True:
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and not ring.match(t.GetNetname())]
    at = collections.defaultdict(list)
    for t in tracks:
        at[(t.GetLayer(), t.GetNetCode(), key(t.GetStart()))].append(t)
        at[(t.GetLayer(), t.GetNetCode(), key(t.GetEnd()))].append(t)
    blocked = set()
    for v in b.GetTracks():
        if v.GetClass() == "PCB_VIA":
            blocked.add(key(v.GetPosition()))
    padat = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            blocked.add(key(p.GetPosition()))
    done = set()
    n = 0
    for (L, net, pt), lst in at.items():
        if len(lst) != 2 or pt in blocked:
            continue
        a, c = lst
        if a is c or id(a) in done or id(c) in done or a.GetWidth() != c.GetWidth():
            continue
        def far(t):
            return t.GetEnd() if key(t.GetStart()) == pt else t.GetStart()
        pa, pc = far(a), far(c)
        mid = a.GetStart() if key(a.GetStart()) == pt else a.GetEnd()
        v1 = (tomm(mid.x - pa.x), tomm(mid.y - pa.y)); v2 = (tomm(pc.x - mid.x), tomm(pc.y - mid.y))
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-4 or l2 < 1e-4:
            continue
        cross = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
        dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
        if abs(cross) > 1e-4 or dot < 0:
            continue
        a.SetStart(pa); a.SetEnd(pc)
        b.Remove(c)
        grave.append(c)
        done.add(id(a)); done.add(id(c))
        n += 1
    merged += n
    if n == 0:
        break
print("merged", merged, "joints")
pcbnew.SaveBoard(sys.argv[2], b)
