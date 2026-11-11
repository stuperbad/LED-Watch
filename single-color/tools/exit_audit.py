"""exit_audit.py BOARD [--list] (KiCad python): the owner's pad-exit rule for every pad except the ring LEDs (H/M/S, own eight-point rule) and the big pads (> 1.6 mm):
the trace must leave the pad ALONG ITS LONG AXIS (tangent), at least 0.15 mm beyond the pad edge, before any bend.  Pads that are nearly square are skipped (any of the 8 directions is fine).
Follows the chain from the pad centre through the pieces that stay inside the pad and measures the direction of the first piece that crosses the pad edge."""
import sys, math, re, collections, pcbnew
mm = pcbnew.ToMM; b = pcbnew.LoadBoard(sys.argv[1]); LIST = "--list" in sys.argv
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
byend = collections.defaultdict(list)
for t in tr:
    for e in (t.GetStart(), t.GetEnd()): byend[(t.GetLayer(), t.GetNetname(), e.x // 3000, e.y // 3000)].append(t)
def near(t, pt, tol=3000):
    return [u for k in ((t.GetLayer(), t.GetNetname(), pt.x // 3000 + i, pt.y // 3000 + j) for i in (-1, 0, 1) for j in (-1, 0, 1)) for u in byend.get(k, [])]
bad = []; ok = 0; skipped = 0
for f in b.GetFootprints():
    ref = f.GetReference()
    if re.match(r"^[HMS]\d+$", ref): continue
    for p in f.Pads():
        n = p.GetNetname()
        if not n or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or p.GetNumber() == "SH": continue
        sx, sy = mm(p.GetSizeX()), mm(p.GetSizeY())
        pc = p.GetPosition(); lays = [l for l in p.GetLayerSet().Seq()]
        smd = [q for q in f.Pads() if q.GetNumber() not in ("", "SH") and q.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        if len(smd) == 2 and max(sx, sy) < 2.0:                              # two-pad chip part: the PART axis (through both pad centres), leave from the outer end
            o2 = [q for q in smd if q is not p][0]; q2 = o2.GetPosition()
            th = math.degrees(math.atan2(q2.y - pc.y, q2.x - pc.x))
        else:
            if max(sx, sy) > 1.6 or abs(sx - sy) < 0.15 * max(sx, sy): skipped += 1; continue
            th = p.GetOrientationDegrees() + (0 if sx >= sy else 90)
        half = max(sx, sy) / 2
        first = [t for t in tr if t.GetNetname() == n and t.GetLayer() in lays and ((abs(t.GetStart().x - pc.x) <= 2000 and abs(t.GetStart().y - pc.y) <= 2000) or (abs(t.GetEnd().x - pc.x) <= 2000 and abs(t.GetEnd().y - pc.y) <= 2000))]
        if not first: continue
        for t in first:
            cur, frm, steps, res = t, pc, 0, None
            while cur is not None and steps < 4:
                a, c = cur.GetStart(), cur.GetEnd()
                o = c if (abs(a.x - frm.x) <= 2500 and abs(a.y - frm.y) <= 2500) else a
                L = math.hypot(o.x - frm.x, o.y - frm.y)
                if L < 1000: break
                if not p.HitTest(o):
                    # direction of this piece, measured from where it leaves the pad
                    res = (math.degrees(math.atan2(o.y - frm.y, o.x - frm.x)), mm(L)); break
                nxt = [u for u in near(cur, o) if u is not cur]
                cur, frm, steps = (nxt[0] if nxt else None), o, steps + 1
            if res is None: continue
            d = (res[0] - th) % 180; d = min(d, 180 - d)
            if d > 8: bad.append((ref, p.GetNumber(), n, round(res[0] % 180, 1), round(th % 180, 1), round(d, 1)))
            else: ok += 1
cnt = collections.Counter(x[0] for x in bad)
print("pad exits checked: tangent %d, NOT along the long axis %d (skipped round / square / big pads %d)" % (ok, len(bad), skipped))
if LIST:
    for x in bad: print("  %s.%s %-12s exits at %5.1f deg, pad axis %5.1f deg (off by %4.1f)" % x)
else: print(dict(cnt.most_common(25)))
