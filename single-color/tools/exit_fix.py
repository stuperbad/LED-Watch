"""exit_fix.py IN OUT [--only REF,..] [--skip REF.PAD,..] [--list] (KiCad python): traces that leave a pad DIAGONALLY (or at an odd angle) get a straight first piece along the pad's axis:
centre -> point X on the axis, at least 0.15 mm beyond the pad edge -> the old first vertex B (45 degrees if the geometry allows, else a 90 degree elbow).
Axis = the part axis for two-pad chips (through both pad centres), the long axis for other pads.  Round, square and big pads, the ring LEDs H/M/S and the ring COL resistors / indicator LEDs are left alone.
Exits already along the axis (or at 90 degrees to it) are not touched."""
import sys, math, re, collections, pcbnew
mm = pcbnew.ToMM; FM = pcbnew.FromMM; a = sys.argv[1:]
b = pcbnew.LoadBoard(a[0]); only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None; skip = set(a[a.index("--skip") + 1].split(",")) if "--skip" in a else set()
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]; V = lambda x, y: pcbnew.VECTOR2I(int(round(x)), int(round(y)))
RING = re.compile(r"^([HMS]\d+|R(1[0-2]|[1-9])|IND\d+)$")           # ring LEDs, COL resistors R1..R12, indicator LEDs
byend = collections.defaultdict(list)
for t in tr:
    for e in (t.GetStart(), t.GetEnd()): byend[(t.GetLayer(), t.GetNetname(), e.x // 3000, e.y // 3000)].append(t)
def nxt(cur, pt):
    return [u for i in (-1, 0, 1) for j in (-1, 0, 1) for u in byend.get((cur.GetLayer(), cur.GetNetname(), pt.x // 3000 + i, pt.y // 3000 + j), []) if u is not cur and (abs(u.GetStart().x - pt.x) <= 2500 and abs(u.GetStart().y - pt.y) <= 2500 or abs(u.GetEnd().x - pt.x) <= 2500 and abs(u.GetEnd().y - pt.y) <= 2500)]
changed = []; log = []
for f in b.GetFootprints():
    ref = f.GetReference()
    if (only and ref not in only) or (not only and RING.match(ref) and not ref.startswith("D5")): continue
    smd = [q for q in f.Pads() if q.GetNumber() not in ("", "SH") and q.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    for p in smd:
        n = p.GetNetname(); key = "%s.%s" % (ref, p.GetNumber())
        if not n or key in skip: continue
        sx, sy = mm(p.GetSizeX()), mm(p.GetSizeY()); pc = p.GetPosition()
        if len(smd) == 2 and max(sx, sy) < 2.0:
            q2 = [q for q in smd if q is not p][0].GetPosition(); th = math.atan2(q2.y - pc.y, q2.x - pc.x); half = (min(sx, sy) if abs(sx - sy) < 0.2 else (sx if abs(math.cos(math.radians(p.GetOrientationDegrees()))) > 0.7 else sy)) / 2
            half = max(mm(math.hypot(0, 0)), (mm(p.GetBoundingBox().GetWidth()) if abs(math.cos(th)) > 0.7 else mm(p.GetBoundingBox().GetHeight())) / 2)
        else:
            if max(sx, sy) > 1.6 or abs(sx - sy) < 0.15 * max(sx, sy): continue
            th = math.radians(p.GetOrientationDegrees() + (0 if sx >= sy else 90)); half = max(sx, sy) / 2
        for t0 in [t for t in tr if t.GetNetname() == n and t.GetLayer() in p.GetLayerSet().Seq() and ((abs(t.GetStart().x - pc.x) <= 2000 and abs(t.GetStart().y - pc.y) <= 2000) or (abs(t.GetEnd().x - pc.x) <= 2000 and abs(t.GetEnd().y - pc.y) <= 2000))]:
            chain = []; cur, frm, B = t0, pc, None
            for _ in range(5):
                s_, e_ = cur.GetStart(), cur.GetEnd(); o = e_ if (abs(s_.x - frm.x) <= 2500 and abs(s_.y - frm.y) <= 2500) else s_
                chain.append(cur)
                if not p.HitTest(o): B = o; break
                nn = nxt(cur, o)
                if len(nn) != 1: break
                cur, frm = nn[0], o
            if B is None: continue
            dx, dy = B.x - pc.x, B.y - pc.y; ang = math.atan2(dy, dx); d = math.degrees(ang - th) % 360
            rel = min(d % 180, 180 - d % 180)
            if rel < 8 or abs(rel - 90) < 8: continue                                   # along the axis or square to it: fine
            ux, uy = math.cos(th), math.sin(th); bu = dx * ux + dy * uy; bv = -dx * uy + dy * ux
            sgn = 1 if bu >= 0 else -1; s, w = abs(bu), abs(bv); minX = FM(half + 0.15)
            if s < 1000: log.append("%s: B is level with the centre, skipped" % key); continue
            if s - w >= minX: X, kind = s - w, "45"
            elif s >= minX: X, kind = s, "90"
            else: log.append("%s: not enough room for 0.15 beyond the pad before the bend (B only %.2f out)" % (key, mm(s))); continue
            Xp = V(pc.x + sgn * X * ux, pc.y + sgn * X * uy)
            log.append("%s %s: exit at %.0f deg off the axis -> axis stub %.2f mm, then %s" % (key, n, rel, mm(X), kind))
            changed.append((chain, pc, Xp, B, t0, n))
if "--list" in a: print("\n".join(log)); sys.exit()
done = 0
for chain, pc, Xp, B, t0, n in changed:
    lay, w = t0.GetLayer(), t0.GetWidth(); net = t0.GetNet()
    for t in chain:
        try: b.Remove(t)
        except Exception: pass
    for q0, q1 in ((pc, Xp), (Xp, B)):
        if q0.x == q1.x and q0.y == q1.y: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(q0); t.SetEnd(q1); t.SetWidth(w); t.SetLayer(lay); t.SetNet(net); b.Add(t)
    done += 1
print("\n".join(log)); print("pads re-exited:", done)
pcbnew.SaveBoard(a[1], b)
