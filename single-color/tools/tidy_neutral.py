"""tidy_neutral.py IN OUT [--apply] : tidy-ups that change NO copper.
  1. a straight piece lying entirely on another piece of the same net / layer / width (overlap, within 1 micrometre of its line): the host is cut at the contained piece's ends
     (so anything hanging on them keeps an exact node), then the contained piece is removed;
  2. (report only) a straight piece under 0.06 mm whose whole capsule lies inside the copper of a via of its net: removing it would change no copper but would leave the neighbour's
     end off the via centre, which breaks the owner's ends-on-centres rule, so these are listed and kept.
usage (KiCad python): tidy_neutral.py in.kicad_pcb out.kicad_pcb [--apply]  (without --apply: report only)"""
import sys, math, collections
import pcbnew
sys.path.insert(0, __file__.rsplit("/", 1)[0].rsplit("\\", 1)[0])
from check_joints import make
args = sys.argv[1:]; apply = "--apply" in args
b = pcbnew.LoadBoard(args[0]); mm = pcbnew.ToMM
V = lambda p: pcbnew.VECTOR2I(int(p[0]), int(p[1]))
pt = lambda p: (p.x, p.y)
grave = []; log = []; log2 = []
def line_off(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; L = math.hypot(dx, dy)
    return abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / L, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (L * L), L
# 1. contained overlaps
for rnd in range(10):
    done = False
    groups = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK": groups[(t.GetNetname(), t.GetLayer(), t.GetWidth())].append(t)
    for key, ts in groups.items():
        for B in ts:
            sb, eb = pt(B.GetStart()), pt(B.GetEnd())
            if sb == eb: continue
            for A in ts:
                if A is B: continue
                sa, ea = pt(A.GetStart()), pt(A.GetEnd())
                if sa == ea: continue
                o1, u1, L = line_off(sb, sa, ea); o2, u2, _ = line_off(eb, sa, ea)
                if o1 <= 1000 and o2 <= 1000 and -1e-9 <= min(u1, u2) and max(u1, u2) <= 1 + 1e-9:
                    cuts = sorted({(u, p) for u, p in ((u1, sb), (u2, eb)) if 1e-9 < u < 1 - 1e-9 and math.hypot(p[0] - sa[0], p[1] - sa[1]) > 1000 and math.hypot(p[0] - ea[0], p[1] - ea[1]) > 1000})
                    log.append("%s %s: piece (%.3f, %.3f)-(%.3f, %.3f) lies on (%.3f, %.3f)-(%.3f, %.3f): host cut at %d point(s), contained piece removed" % (key[0], b.GetLayerName(key[1]), mm(sb[0]), mm(sb[1]), mm(eb[0]), mm(eb[1]), mm(sa[0]), mm(sa[1]), mm(ea[0]), mm(ea[1]), len(cuts)))
                    if apply:
                        cur = A; old_end = ea
                        for u, p in cuts:
                            n = pcbnew.PCB_TRACK(b); n.SetLayer(A.GetLayer()); n.SetWidth(A.GetWidth()); n.SetNet(A.GetNet()); n.SetStart(V(p)); n.SetEnd(V(old_end)); b.Add(n)
                            cur.SetEnd(V(p)); cur = n
                        b.Remove(B); grave.append(B)
                    done = True; break
            if done: break
        if done: break
    if not done or not apply: break
# 2. micro pieces inside vias
if apply or True:
    A_ = make(b); cand = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or mm(t.GetLength()) >= 0.06: continue
        for v in A_.items[t.GetNetname()]:
            if v.kind != "via": continue
            lim = v.r - t.GetWidth() / 2
            if all(math.hypot(e.x - v.p[0], e.y - v.p[1]) <= lim for e in (t.GetStart(), t.GetEnd())): cand.append((t, v)); break
    for t, v in cand:
        net = t.GetNetname(); before = len(make(b).joints(net)[1])
        s, e = t.GetStart(), t.GetEnd(); info = "%s %s: %.3f mm piece at (%.3f, %.3f) inside the via at (%.3f, %.3f)" % (net, b.GetLayerName(t.GetLayer()), mm(t.GetLength()), mm(s.x), mm(s.y), mm(v.p[0]), mm(v.p[1]))
        log2.append(info + ": kept (the neighbour would end off the via centre)")
print("changes that move no copper: %d" % len(log))
for l in log: print("  ", l)
print("micro pieces inside vias (kept): %d" % len(log2))
for l in log2: print("  ", l)
if apply: pcbnew.SaveBoard(args[1], b)
