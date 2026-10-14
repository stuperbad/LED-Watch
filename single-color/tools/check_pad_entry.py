"""Check how every track lands on pads and vias.
A track that ends at a pad's edge or corner only overlaps the pad with part of its
round end, so the copper joint is much narrower than the track.  For each track end
that touches a pad (same net, same layer) this reports the depth of the end inside the
pad: a full-width landing needs depth >= width/2.

usage (KiCad python): check_pad_entry.py board.kicad_pcb [--fix out.kicad_pcb]
--fix adds a short stub from each shallow end to the pad centre (same net/width/layer).
The stub stays inside the pad plus the existing round end, so it adds no new copper
near other nets; run DRC afterwards anyway."""
import sys, math
import pcbnew

TOL = 0.005  # mm
mm, tomm = pcbnew.FromMM, pcbnew.ToMM


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def inside(p, poly):
    x, y = p; c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def depth(p, poly):
    d = min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
    return d if inside(p, poly) else -d


def pad_poly(pad, layer):
    sps = pad.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
    ch = sps.Outline(0)
    return [(tomm(ch.CPoint(i).x), tomm(ch.CPoint(i).y)) for i in range(ch.PointCount())]


b = pcbnew.LoadBoard(sys.argv[1])
fix_out = sys.argv[sys.argv.index("--fix") + 1] if "--fix" in sys.argv else None

pads = []  # (pad, layer, poly, bbox, centre)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetCode() <= 0:
            continue
        for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not pad.IsOnLayer(layer) or not pad.IsOnCopperLayer():
                continue
            try:
                poly = pad_poly(pad, layer)
            except Exception:
                continue
            if len(poly) < 3:
                continue
            xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            c = pad.ShapePos(layer) if hasattr(pad, "ShapePos") else pad.GetPosition()
            pads.append((pad, layer, poly, (min(xs), min(ys), max(xs), max(ys)), (tomm(c.x), tomm(c.y))))

tracks = [t for t in b.GetTracks() if t.GetClass() in ("PCB_TRACK", "PCB_ARC")]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]

bad, ok, viabad = [], 0, []
for t in tracks:
    w = tomm(t.GetWidth()); L = t.GetLayer(); net = t.GetNetCode()
    for end in (t.GetStart(), t.GetEnd()):
        p = (tomm(end.x), tomm(end.y))
        for pad, layer, poly, (x0, y0, x1, y1), c in pads:
            if layer != L or pad.GetNetCode() != net:
                continue
            if p[0] < x0 - w or p[0] > x1 + w or p[1] < y0 - w or p[1] > y1 + w:
                continue
            d = depth(p, poly)
            if d <= -w / 2:
                continue  # not touching
            if d >= w / 2 - TOL:
                ok += 1
                continue
            bad.append(dict(t=t, end=end, p=p, w=w, d=d, pad=pad, c=c, layer=layer,
                            name="%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber()),
                            net=t.GetNetname(), off=math.hypot(p[0] - c[0], p[1] - c[1])))
        for v in vias:
            if v.GetNetCode() != net or not v.IsOnLayer(L):
                continue
            vc = v.GetPosition(); r = tomm(v.GetWidth(L) if hasattr(v, "GetWidth") else v.GetWidth()) / 2
            off = math.hypot(p[0] - tomm(vc.x), p[1] - tomm(vc.y))
            if off < r + w / 2 and off > TOL:
                viabad.append((t.GetNetname(), p, off, r, end, vc, t))

# vias that only partly overlap a same-net pad (centre outside the pad)
viapad = []
for v in vias:
    vc = (tomm(v.GetPosition().x), tomm(v.GetPosition().y))
    for pad, layer, poly, (x0, y0, x1, y1), c in pads:
        if pad.GetNetCode() != v.GetNetCode() or not v.IsOnLayer(layer):
            continue
        r = tomm(v.GetWidth(layer)) / 2
        if vc[0] < x0 - r or vc[0] > x1 + r or vc[1] < y0 - r or vc[1] > y1 + r:
            continue
        d = depth(vc, poly)
        if -r < d < TOL:
            viapad.append(dict(v=v, vc=vc, r=r, d=d, pad=pad, c=c, layer=layer,
                               name="%s.%s" % (pad.GetParentFootprint().GetReference(), pad.GetNumber())))

# dedupe (two segments sharing an end report the same point twice)
seen = set(); _b = []
for x in bad:
    k = (round(x["p"][0], 4), round(x["p"][1], 4), x["name"], x["layer"])
    if k not in seen:
        seen.add(k); _b.append(x)
bad = _b
seen = set(); _v = []
for x in viabad:
    k = (round(x[1][0], 4), round(x[1][1], 4), x[6].GetLayer(), x[5].x, x[5].y)
    if k not in seen:
        seen.add(k); _v.append(x)
viabad = _v

# A shallow end is fixed when a track runs from that end to a full landing in the
# same pad (or, for a via, to the via centre): report only the unresolved ones.
def _k(v): return (v.x, v.y)
ends = {}
for t in tracks:
    for a, c2 in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
        ends.setdefault((_k(a), t.GetLayer(), t.GetNetCode()), []).append(c2)
def resolved_pad(x):
    for o in ends.get((_k(x["end"]), x["layer"], x["t"].GetNetCode()), []):
        if depth((tomm(o.x), tomm(o.y)), pad_poly(x["pad"], x["layer"])) >= x["w"] / 2 - TOL:
            return True
    return False
def resolved_via(x):
    n, p, off, r, end, vc, t = x
    return any(_k(o) == _k(vc) for o in ends.get((_k(end), t.GetLayer(), t.GetNetCode()), []))
if not fix_out:
    nb, nv = len(bad), len(viabad)
    bad = [x for x in bad if not resolved_pad(x)]
    viabad = [x for x in viabad if not resolved_via(x)]
    print("(%d shallow pad ends and %d off-centre via ends already have a stub to the centre)" % (nb - len(bad), nv - len(viabad)))

# a shallow end only matters if no OTHER copper of the net lands that pad properly
by_pad = {}
for x in bad:
    by_pad.setdefault((x["name"], x["layer"]), []).append(x)

print("track ends landing fully on a pad: %d" % ok)
print("shallow pad landings (depth < width/2): %d ends on %d pads" % (len(bad), len(by_pad)))
for k, lst in sorted(by_pad.items()):
    for x in lst:
        print("  %-8s %-12s %-6s w=%.3f depth=%+.3f (need %.3f) %.3f from centre at (%.3f, %.3f)" % (
            x["name"], x["net"], b.GetLayerName(x["layer"]), x["w"], x["d"], x["w"] / 2, x["off"], x["p"][0], x["p"][1]))
print("vias only partly overlapping a same-net pad: %d" % len(viapad))
for x in viapad:
    print("  %-8s via at (%.3f, %.3f) r %.3f, centre %.3f outside the pad" % (x["name"], x["vc"][0], x["vc"][1], x["r"], -x["d"]))
print("track ends touching a via off-centre: %d" % len(viabad))
for n, p, off, r, *_ in viabad:
    print("  %-12s (%.3f, %.3f) %.3f mm from via centre (via r %.3f)" % (n, p[0], p[1], off, r))

if fix_out:
    for x in bad:
        s = pcbnew.PCB_TRACK(b)
        s.SetStart(x["end"]); s.SetEnd(pcbnew.VECTOR2I(mm(x["c"][0]), mm(x["c"][1])))
        s.SetWidth(x["t"].GetWidth()); s.SetLayer(x["layer"]); s.SetNetCode(x["t"].GetNetCode())
        b.Add(s)
    for n, p, off, r, end, vc, t in viabad:
        s = pcbnew.PCB_TRACK(b)
        s.SetStart(end); s.SetEnd(vc)
        s.SetWidth(t.GetWidth()); s.SetLayer(t.GetLayer()); s.SetNetCode(t.GetNetCode())
        b.Add(s)
    for x in viapad:
        s = pcbnew.PCB_TRACK(b)
        s.SetStart(x["v"].GetPosition()); s.SetEnd(pcbnew.VECTOR2I(mm(x["c"][0]), mm(x["c"][1])))
        s.SetWidth(mm(0.1)); s.SetLayer(x["layer"]); s.SetNetCode(x["v"].GetNetCode())
        b.Add(s)
    pcbnew.SaveBoard(fix_out, b)
    print("added %d pad stubs, %d via stubs, %d via-pad stubs -> %s" % (len(bad), len(viabad), len(viapad), fix_out))
