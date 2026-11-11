"""pad_centre_fix.py IN OUT [--skip REF,..] [--dry] (KiCad python): every pad that has a track ending on it but no track end on its CENTRE gets its trace carried to the centre
(owner's rule: a trace goes to the middle of the pad, never just to a corner or edge).
  * a piece that passes straight through the centre is cut in two there;
  * otherwise one or two pieces are added inside the pad (45 / 90 degrees, last leg along the pad's long axis when it can be) from the end to the centre; skipped (and listed) if they would leave the pad.
Never touched: ring LEDs H / M / S (their ends sit on the outer pad end by the eight-point rule), shell / mounting pads (SH, NPTH)."""
import sys, math, re, pcbnew
mm = pcbnew.ToMM; FM = pcbnew.FromMM; a = sys.argv[1:]
b = pcbnew.LoadBoard(a[0]); skip = set(a[a.index("--skip") + 1].split(",")) if "--skip" in a else set(); dry = "--dry" in a
nets = b.GetNetsByName(); V = lambda x, y: pcbnew.VECTOR2I(int(round(x)), int(round(y)))
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
added = cut = 0; todo = []
for f in b.GetFootprints():
    ref = f.GetReference()
    if ref in skip or re.match(r"^[HMS]\d+$", ref): continue
    for p in f.Pads():
        n = p.GetNetname()
        if not n or p.GetNumber() in ("SH",) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
        pc = p.GetPosition(); lay = [l for l in p.GetLayerSet().Seq() if l in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu)]
        mine = [t for t in tr if t.GetNetname() == n and t.GetLayer() in lay]
        ends = [(t, e) for t in mine for e in (t.GetStart(), t.GetEnd()) if p.HitTest(e, 60000)]      # on the pad or within 0.06 mm of its edge (rounded corners)
        if not ends: continue
        if any(abs(e.x - pc.x) <= 2000 and abs(e.y - pc.y) <= 2000 for t, e in ends): continue
        todo.append((ref, p, ends, mine))
log = []
for ref, p, ends, mine in todo:
    pc = p.GetPosition(); C = (pc.x, pc.y); sx, sy = p.GetSizeX(), p.GetSizeY()
    th = p.GetOrientationDegrees(); hor = (sx >= sy) == (abs(math.cos(math.radians(th))) > 0.7)         # long axis horizontal on the board?
    # pass-through: a piece whose body goes through the centre
    thru = [t for t in mine if t.HitTest(pc, 1500) and t.GetStart() != pc and t.GetEnd() != pc]
    if thru:
        t = thru[0]; log.append("%s.%s %s: cut through the centre" % (ref, p.GetNumber(), p.GetNetname()))
        if not dry:
            n2 = pcbnew.PCB_TRACK(b); n2.SetStart(pc); n2.SetEnd(t.GetEnd()); n2.SetWidth(t.GetWidth()); n2.SetLayer(t.GetLayer()); n2.SetNet(t.GetNet()); b.Add(n2); t.SetEnd(pc)
        cut += 1; continue
    t, e = min(ends, key=lambda te: math.hypot(te[1].x - pc.x, te[1].y - pc.y))
    dx, dy = C[0] - e.x, C[1] - e.y; adx, ady = abs(dx), abs(dy); sgx = 1 if dx >= 0 else -1; sgy = 1 if dy >= 0 else -1
    pts = [(e.x, e.y)]
    if adx < 3000 or ady < 3000 or abs(adx - ady) < 3000: pts.append(C)
    elif hor:
        if adx > ady: pts += [(e.x + sgx * ady, e.y + sgy * ady), C]                    # diagonal first, then along the axis
        else: pts += [(e.x, e.y + sgy * (ady - adx)), C]                                # straight, then the diagonal into the centre
    else:
        if ady > adx: pts += [(e.x + sgx * adx, e.y + sgy * adx), C]
        else: pts += [(e.x + sgx * (adx - ady), e.y), C]
    ok = all(p.HitTest(V(*q), 60000) and p.HitTest(V((q[0] + w[0]) / 2, (q[1] + w[1]) / 2), 30000) for q, w in zip(pts, pts[1:]))
    if not ok: log.append("%s.%s %s: SKIPPED (the carry-in would leave the pad)" % (ref, p.GetNumber(), p.GetNetname())); continue
    log.append("%s.%s %s: carried %d piece(s) to the centre" % (ref, p.GetNumber(), p.GetNetname(), len(pts) - 1))
    if not dry:
        for q, w in zip(pts, pts[1:]):
            if q == w: continue
            n2 = pcbnew.PCB_TRACK(b); n2.SetStart(V(*q)); n2.SetEnd(V(*w)); n2.SetWidth(t.GetWidth()); n2.SetLayer(t.GetLayer()); n2.SetNet(t.GetNet()); b.Add(n2); added += 1
print("\n".join(log)); print("pads fixed: pieces added", added, "cuts", cut, "of", len(todo), "pads")
if not dry: pcbnew.SaveBoard(a[1], b)
