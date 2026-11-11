"""pad_exit_audit.py BOARD [PREFIX ...] (KiCad python): where do the traces leave the LED pads?  Owner's rule (2026-11-09): a pad has 8 attachment points (4 corners + 4 edge middles); the 3 on the edge facing
the LED body are not allowed; the first piece out of the pad must stick out at least 1.5 trace widths beyond the pad edge.  Pads are aligned radially (u = tangential, v = radial about 100, 100).
Prints per ring: pads, pads with an exit on the forbidden inner edge, pads with a first piece shorter than the minimum, exits by kind; and the worst offenders."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; NM = 1e6; O = (100.0, 100.0)
prefixes = sys.argv[2:] or ["H", "M", "S"]
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
def key(p): return (p.x, p.y)
res = collections.defaultdict(lambda: collections.Counter()); bad = collections.defaultdict(list)
for f in b.GetFootprints():
    r = f.GetReference()
    if f.GetLayerName() != "F.Cu" or r[0] not in prefixes or not r[1:].isdigit() or not str(f.GetValue()).startswith("LED"): continue
    c = f.GetPosition(); cx, cy = c.x / NM, c.y / NM; th = math.atan2(cy - O[1], cx - O[0]); u = (-math.sin(th), math.cos(th)); v = (math.cos(th), math.sin(th))
    for p in f.Pads():
        if not p.GetNumber(): continue
        pc = p.GetPosition(); px, py = pc.x / NM, pc.y / NM; hu, hv = mm(p.GetSizeY()) / 2, mm(p.GetSizeX()) / 2          # footprint x runs along the LED = radially
        # pad extents along u (tangential) and v (radial): the pad long side is radial for these LEDs
        pr = (px - cx) * v[0] + (py - cy) * v[1]; inner_sign = -1 if pr > 0 else 1                     # the edge facing the LED body
        res[r[0]]["pads"] += 1
        for t in tracks:
            if t.GetNetname() != p.GetNetname() or t.GetLayerName() != "F.Cu": continue
            for a, e in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                if key(a) != key(pc): continue
                d = ((e.x - a.x) / NM, (e.y - a.y) / NM); L = math.hypot(*d); du, dv = d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1]
                if L < 1e-6: continue
                tx = hu / abs(du) if abs(du) > 1e-9 else 1e9; tv = hv / abs(dv) if abs(dv) > 1e-9 else 1e9; tt = min(tx, tv) * L        # distance from the centre to the pad edge along the piece
                eu, ev = du / L * tt, dv / L * tt                                                                             # exit point in the pad frame
                on_inner = ev * inner_sign > hv - 0.06                                                                         # inner edge, corners included
                kind = ("corner" if abs(abs(eu) - hu) < 0.06 and abs(abs(ev) - hv) < 0.06 else ("side" if abs(abs(eu) - hu) < 0.03 else "end"))
                out = L - tt; res[r[0]]["exits"] += 1; res[r[0]]["kind " + kind + (" INNER" if on_inner else "")] += 1
                if on_inner: res[r[0]]["pads with inner exit"] += 1; bad[r[0]].append((r, p.GetNumber(), "inner", round(out, 2)))
                elif out < 0.145: res[r[0]]["first piece < 0.15 beyond the pad"] += 1; bad[r[0]].append((r, p.GetNumber(), "short", round(out, 2)))
for k in sorted(res): print(k, "ring:", dict(res[k]))
for k in sorted(bad): print(k, "examples:", bad[k][:8])
