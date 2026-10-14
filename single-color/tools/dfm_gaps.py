"""Pad/via copper gaps on the outer layers below a threshold, with nets -- to sort JLCDFM
'Pad spacing' / 'Via to pad' hits into same-net (harmless) and different-net (real).
usage (KiCad python): dfm_gaps.py board.kicad_pcb [limit_mm=0.15]"""
import sys, itertools
import pcbnew
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); lim = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
items = []
for L in (pcbnew.F_Cu, pcbnew.B_Cu):
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(L):
                items.append((L, "%s.%s" % (fp.GetReference(), p.GetNumber()), p.GetNetname(), p.GetEffectiveShape(L), p.GetBoundingBox()))
    for v in b.GetTracks():
        if v.GetClass() == "PCB_VIA":
            items.append((L, "via(%.3f,%.3f)" % (tomm(v.GetPosition().x), tomm(v.GetPosition().y)), v.GetNetname(), v.GetEffectiveShape(L), v.GetBoundingBox()))
lm = pcbnew.FromMM(lim)
out = []
by = {}
for it in items: by.setdefault(it[0], []).append(it)
for L, lst in by.items():
    lst.sort(key=lambda t: t[4].GetX())
    for i, a in enumerate(lst):
        ab = a[4]
        for c in lst[i + 1:]:
            if c[4].GetX() > ab.GetRight() + lm: break
            if c[4].GetY() > ab.GetBottom() + lm or c[4].GetBottom() < ab.GetY() - lm: continue
            if a[1].startswith("via") and c[1].startswith("via"): continue
            if a[1].split(".")[0] == c[1].split(".")[0] and not a[1].startswith("via"): kind = "same-part"
            else: kind = ""
            if not a[3].Collide(c[3], lm):
                continue
            if a[3].Collide(c[3], 0):
                d = 0.0
            else:
                lo, hi = 0, lm
                for _ in range(12):
                    m = (lo + hi) // 2
                    if a[3].Collide(c[3], m): hi = m
                    else: lo = m
                d = tomm(hi)
            same = a[2] == c[2] and a[2] != ""
            out.append((d, b.GetLayerName(L), a[1], c[1], a[2], c[2], "SAME NET" if same else "DIFFERENT NETS", kind))
out.sort()
for o in out:
    if o[0] < lim: print("%.3f mm  %s  %-18s %-18s %-12s %-12s %s %s" % o)
