"""short_pieces.py board.kicad_pcb [out.kicad_pcb] : classify the track pieces shorter than 0.15 mm and, with out.kicad_pcb, remove only the ones that change no copper at all:
  buried   both ends inside the copper of one via or one pad of the same net (the piece lies under that copper)
  collinear joint   piece collinear with BOTH neighbours (same net, layer, width), ends meeting nothing else: merged into one longer piece (geometry unchanged)
Everything else is only counted: chamfer (the diagonal of a 45 degree corner cut), jog (a step between two parallel pieces), other. KiCad python."""
import pcbnew, sys, math, collections
tomm = pcbnew.ToMM; mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); L = b.GetLayerName
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [v for v in b.GetTracks() if t.GetClass() == "PCB_VIA"] if False else [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
P = lambda q: (tomm(q.x), tomm(q.y))
def key(q): return (round(tomm(q.x), 3), round(tomm(q.y), 3))
ends = collections.defaultdict(list)
for t in tr:
    ends[(t.GetLayer(), t.GetNetname(), key(t.GetStart()))].append(t); ends[(t.GetLayer(), t.GetNetname(), key(t.GetEnd()))].append(t)
def via_of(q, net):
    for i, v in enumerate(vias):
        if v.GetNetname() == net and math.hypot(tomm(q.x - v.GetPosition().x), tomm(q.y - v.GetPosition().y)) <= tomm(v.GetWidth(pcbnew.F_Cu)) / 2 - 0.01: return i
    return None
def pad_of(q, t):
    for i, p in enumerate(pads):
        if p.GetNetname() == t.GetNetname() and p.IsOnLayer(t.GetLayer()) and p.HitTest(q): return i
    return None
in_via = lambda q, net: via_of(q, net) is not None
in_pad = lambda q, t: pad_of(q, t) is not None
def direction(t, rev=False):
    s, e = P(t.GetStart()), P(t.GetEnd()); d = (e[0] - s[0], e[1] - s[1]); n = math.hypot(*d)
    return (d[0] / n, d[1] / n) if n > 1e-9 else (0, 0)
cat = collections.Counter(); buried = []; merge = []
for t in tr:
    ln = tomm(t.GetLength())
    if ln >= 0.15: continue
    if ln < 1e-4: cat["zero length"] += 1; buried.append(t); continue
    s, e = t.GetStart(), t.GetEnd()
    vs, ve, ps, pe = via_of(s, t.GetNetname()), via_of(e, t.GetNetname()), pad_of(s, t), pad_of(e, t)
    if (vs is not None and vs == ve) or (ps is not None and ps == pe):
        cat["buried (both ends inside the SAME via / pad)"] += 1; buried.append(t); continue
    ns = [x for x in ends[(t.GetLayer(), t.GetNetname(), key(s))] if x is not t]; ne = [x for x in ends[(t.GetLayer(), t.GetNetname(), key(e))] if x is not t]
    d = direction(t)
    if len(ns) == 1 and len(ne) == 1 and not in_via(s, t.GetNetname()) and not in_via(e, t.GetNetname()):
        def col(o, at_end):
            do = direction(o)
            if (o.GetStart() == (e if at_end else s)): pass
            return abs(do[0] * d[1] - do[1] * d[0]) < 1e-3
        if col(ns[0], False) and col(ne[0], True) and ns[0].GetWidth() == t.GetWidth() == ne[0].GetWidth():
            cat["collinear joint (mergeable)"] += 1; merge.append((ns[0], t, ne[0])); continue
        ds, de = direction(ns[0]), direction(ne[0])
        cross = d[0] * de[1] - d[1] * de[0]; cross0 = d[0] * ds[1] - d[1] * ds[0]
        if abs(cross) > 0.5 and abs(cross0) > 0.5: cat["chamfer / diagonal between two perpendicular-ish pieces"] += 1; continue
        cat["jog or bend piece"] += 1; continue
    cat["other (at a via / pad / branch)"] += 1
print("pieces < 0.15 mm:", sum(cat.values()))
for k, v in cat.most_common(): print("  %4d  %s" % (v, k))
if len(sys.argv) > 2:
    grave = []
    for t in buried:
        b.Remove(t); grave.append(t)
    print("removed buried + zero-length pieces:", len(buried))
    pcbnew.SaveBoard(sys.argv[2], b)
