"""merge_collinear_exact.py IN OUT [--tol 0.001] [--apply] : copper-neutral tidy-up of chopped lines.
  * removes zero-length straight pieces (nothing else may hang on them: their end is moved onto the neighbour first)
  * merges two straight pieces of one net / layer / width that meet at a node with exactly those two pieces (no via, no pad position, no third piece) and are collinear
    (the node lies within --tol mm of the line between the outer ends, default 1 micrometre): one piece from outer end to outer end.
The outer ends keep their exact integer coordinates, so every other joint stays exact; the copper changes by at most --tol.
Without --apply it only reports.   usage (KiCad python)."""
import sys, math, collections
import pcbnew
args = sys.argv[1:]; tol = 0.001; apply = "--apply" in args
if "--tol" in args: tol = float(args[args.index("--tol") + 1])
TOL = tol * 1e6
b = pcbnew.LoadBoard(args[0]); mm = pcbnew.ToMM
pt = lambda p: (p.x, p.y)
def lines_of():
    d = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK": d[(t.GetNetname(), t.GetLayer(), t.GetWidth())].append(t)
    return d
vias = {pt(t.GetPosition()) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"}
padpos = {pt(p.GetPosition()) for f in b.GetFootprints() for p in f.Pads()}
arcends = collections.defaultdict(int)
for t in b.GetTracks():
    if t.GetClass() == "PCB_ARC": arcends[(t.GetLayer(), pt(t.GetStart()))] += 1; arcends[(t.GetLayer(), pt(t.GetEnd()))] += 1
rem0 = 0; merged = 0; log = []; grave = []        # removed items must stay alive: KiCad's python frees them with the last reference
changed = True
while changed:
    changed = False
    for key, ts in lines_of().items():
        net, layer, width = key
        # zero-length pieces
        for t in list(ts):
            if pt(t.GetStart()) == pt(t.GetEnd()):
                log.append("zero-length piece removed: %s %s at (%.3f, %.3f)" % (net, b.GetLayerName(layer), mm(t.GetStart().x), mm(t.GetStart().y)))
                if apply: b.Remove(t); grave.append(t)
                rem0 += 1; changed = True; ts.remove(t)
        ends = collections.defaultdict(list)
        for t in ts: ends[pt(t.GetStart())].append(t); ends[pt(t.GetEnd())].append(t)
        for p, lst in ends.items():
            if len(lst) != 2 or p in vias or p in padpos or arcends.get((layer, p)): continue
            # any other piece (other width, same layer / net) or via-less crossing at this point is rare; check same-layer pieces of other widths too
            t1, t2 = lst
            if t1 is t2: continue
            o1 = pt(t1.GetEnd()) if pt(t1.GetStart()) == p else pt(t1.GetStart()); o2 = pt(t2.GetEnd()) if pt(t2.GetStart()) == p else pt(t2.GetStart())
            dx, dy = o2[0] - o1[0], o2[1] - o1[1]; L = math.hypot(dx, dy)
            if L == 0: continue
            off = abs((p[0] - o1[0]) * dy - (p[1] - o1[1]) * dx) / L
            # the node must lie BETWEEN the outer ends (no hairpin)
            u = ((p[0] - o1[0]) * dx + (p[1] - o1[1]) * dy) / (L * L)
            if off <= TOL and 0 < u < 1:
                if apply:
                    t1.SetStart(pcbnew.VECTOR2I(*o1)); t1.SetEnd(pcbnew.VECTOR2I(*o2)); b.Remove(t2); grave.append(t2)
                merged += 1; changed = True; log.append("merged at (%.3f, %.3f) %s %s (off the line %.4f mm)" % (mm(p[0]), mm(p[1]), net, b.GetLayerName(layer), off / 1e6))
                break
        if changed: break
    if not apply: break
print("zero-length pieces %s: %d   collinear merges %s: %d" % ("removed" if apply else "found", rem0, "done" if apply else "possible (first level only without --apply)", merged))
for l in log[:60]: print("  ", l)
if apply: pcbnew.SaveBoard(args[1], b)
