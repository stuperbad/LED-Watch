"""refit.py base.kicad_pcb routed.kicad_pcb out.kicad_pcb NET [NET ...] : the pieces the router added (in routed, not in base) for the named nets are joined into chains (per layer, broken at vias),
the two ends are moved onto the centre of the pad or via they touch, and each chain is replaced by the fewest 0/45/90-degree legs that stay within EPS of the router's path.
Vias, other nets and the base copper are untouched. Env EPS (tolerance, mm), SKIP (boxes whose chains are left alone). KiCad python (MSYS_NO_PATHCONV=1 for net names with a leading /)."""
import sys, math, collections
import pcbnew
tomm, mm = pcbnew.ToMM, pcbnew.FromMM
import os
EPS = float(os.environ.get("EPS", "0.06"))
SKIP = [tuple(float(v) for v in r.split(",")) for r in os.environ.get("SKIP", "").split(";") if r.strip()]   # SKIP="x0,y0,x1,y1;..." chains with a point inside are not refitted
base = pcbnew.LoadBoard(sys.argv[1]); b = pcbnew.LoadBoard(sys.argv[2])
nets = sys.argv[4:]
V = lambda p: pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
xy = lambda p: (tomm(p.x), tomm(p.y))
k = lambda t: (t.GetLayer(), t.GetNetname(), tuple(sorted([(round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3)), (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))])))
have = {k(t) for t in base.GetTracks() if t.GetClass() == "PCB_TRACK"}
pads = [p for f in b.GetFootprints() for p in f.Pads()]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]


def dseg(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)


def dpoly(p, poly):
    return min(dseg(p, poly[i], poly[i + 1]) for i in range(len(poly) - 1))


def sample(poly, step=0.02):
    out = [poly[0]]
    for i in range(len(poly) - 1):
        a, c = poly[i], poly[i + 1]
        n = max(1, int(math.hypot(c[0] - a[0], c[1] - a[1]) / step))
        for j in range(1, n + 1):
            out.append((a[0] + (c[0] - a[0]) * j / n, a[1] + (c[1] - a[1]) * j / n))
    return out


def legal(a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    if math.hypot(dx, dy) < 1e-6:
        return True
    r = math.degrees(math.atan2(dy, dx)) % 45
    return min(r, 45 - r) < 0.05


def cands(a, c):
    if legal(a, c):
        return [[a, c]]
    dx, dy = c[0] - a[0], c[1] - a[1]
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    ax, ay = abs(dx), abs(dy)
    if ax >= ay:
        es = [(a[0] + sx * (ax - ay), a[1]), (a[0] + sx * ay, a[1] + sy * ay)]
    else:
        es = [(a[0], a[1] + sy * (ay - ax)), (a[0] + sx * ax, a[1] + sy * ax)]
    return [[a, e, c] for e in es]


def fit(poly):
    out = [poly[0]]
    i = 0
    n = len(poly) - 1
    while i < n:
        for j in range(n, i, -1):
            sub = poly[i:j + 1]
            best = None
            for cp in cands(poly[i], poly[j]):
                if any(math.hypot(cp[q + 1][0] - cp[q][0], cp[q + 1][1] - cp[q][1]) < 1e-6 for q in range(len(cp) - 1)):
                    continue
                if all(dpoly(p, sub) <= EPS for p in sample(cp)) and all(dpoly(p, cp) <= EPS for p in sub):
                    best = cp
                    break
            if best:
                out += best[1:]
                i = j
                break
        else:                      # nothing fits (degenerate piece): keep the router's own point and go on
            i += 1
            out.append(poly[i])
    return out


def centre_at(p, L, net):
    P = V(p)
    for slack in (0.0, 0.2):
        for t in vias:
            if t.GetNetname() == net and t.IsOnLayer(L) and math.hypot(xy(t.GetPosition())[0] - p[0], xy(t.GetPosition())[1] - p[1]) <= tomm(t.GetWidth(L)) / 2 + slack:
                return xy(t.GetPosition())
        for q in pads:
            if q.GetNetname() == net and q.IsOnLayer(L) and q.GetNumber() != "SH" and q.HitTest(P, mm(slack)):
                return xy(q.GetPosition())
    return None


grave = []
for net in nets:
    new = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetname() == net and k(t) not in have]
    for L in {t.GetLayer() for t in new}:
        ps = [t for t in new if t.GetLayer() == L]
        ends = collections.defaultdict(list)
        for t in ps:
            ends[(round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3))].append(t)
            ends[(round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))].append(t)
        used = set()
        for t in ps:
            if id(t) in used:
                continue
            # walk to one end of the chain
            chain = [t]; used.add(id(t))
            for direction in (0, 1):
                cur = t
                pt = (round(tomm((cur.GetStart() if direction == 0 else cur.GetEnd()).x), 3), round(tomm((cur.GetStart() if direction == 0 else cur.GetEnd()).y), 3))
                while True:
                    nxt = [u for u in ends[pt] if id(u) not in used]
                    if len(ends[pt]) != 2 or not nxt:
                        break
                    u = nxt[0]; used.add(id(u))
                    chain = [u] + chain if direction == 0 else chain + [u]
                    s = (round(tomm(u.GetStart().x), 3), round(tomm(u.GetStart().y), 3)); e = (round(tomm(u.GetEnd().x), 3), round(tomm(u.GetEnd().y), 3))
                    pt = e if s == pt else s
                    cur = u
            # order the points
            pts = [xy(chain[0].GetStart()), xy(chain[0].GetEnd())]
            if len(chain) > 1:
                s2, e2 = xy(chain[1].GetStart()), xy(chain[1].GetEnd())
                if math.hypot(pts[0][0] - s2[0], pts[0][1] - s2[1]) < 0.002 or math.hypot(pts[0][0] - e2[0], pts[0][1] - e2[1]) < 0.002:
                    pts.reverse()
            for u in chain[1:]:
                s, e = xy(u.GetStart()), xy(u.GetEnd())
                pts.append(e if math.hypot(pts[-1][0] - s[0], pts[-1][1] - s[1]) < 0.002 else s)
            if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts for (x0, y0, x1, y1) in SKIP):
                print("   chain left as it is (inside a skip box)", pts[0], pts[-1])
                continue
            w = chain[0].GetWidth()
            c0, c1 = centre_at(pts[0], L, net), centre_at(pts[-1], L, net)
            poly = list(pts)
            # a free end that lands within 0.08 mm of an end of existing copper (same net and layer) joins that end exactly
            for idx in (0, -1):
                if centre_at(poly[idx], L, net) is None:
                    for o in base.GetTracks():
                        if o.GetClass() == "PCB_TRACK" and o.GetLayer() == L and o.GetNetname() == net:
                            for e in (xy(o.GetStart()), xy(o.GetEnd())):
                                if 0 < math.hypot(e[0] - poly[idx][0], e[1] - poly[idx][1]) < 0.08:
                                    poly[idx] = e
            print("   chain ends", pts[0], pts[-1], "->", c0, c1)
            if c0 and math.hypot(c0[0] - poly[0][0], c0[1] - poly[0][1]) > 0.001:
                poly = [c0] + poly
            if c1 and math.hypot(c1[0] - poly[-1][0], c1[1] - poly[-1][1]) > 0.001:
                poly = poly + [c1]
            # the added lead-in/out is a straight piece from the old end to the centre; keep it in the fit
            newp = fit(poly)
            for u in chain:
                b.Remove(u); grave.append(u)
            for a, c in zip(newp, newp[1:]):
                if math.hypot(c[0] - a[0], c[1] - a[1]) < 1e-6:
                    continue
                tt = pcbnew.PCB_TRACK(b); tt.SetStart(V(a)); tt.SetEnd(V(c)); tt.SetWidth(w); tt.SetLayer(L); tt.SetNetCode(chain[0].GetNetCode())
                b.Add(tt)
            print("%-10s %-6s %2d pieces -> %2d   ends %s %s" % (net, b.GetLayerName(L), len(chain), len(newp) - 1, "centre" if c0 else "free", "centre" if c1 else "free"))
pcbnew.SaveBoard(sys.argv[3], b)
