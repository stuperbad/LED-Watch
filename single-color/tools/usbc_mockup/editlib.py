"""editlib.py : small helpers for scripted, reviewable board edits (KiCad python). Everything is explicit: move parts, delete listed track pieces / vias, add polylines / vias."""
import pcbnew, math
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
class Ed:
    def __init__(self, src):
        self.b = pcbnew.LoadBoard(src); self.grave = []; self.log = []
    def part(self, ref): return self.b.FindFootprintByReference(ref)
    def move(self, ref, x, y, rot=None):
        f = self.part(ref); f.SetPosition(V(x, y))
        if rot is not None: f.SetOrientationDegrees(rot)
        self.log.append("move %s -> (%.3f, %.3f)%s" % (ref, x, y, "" if rot is None else " rot %g" % rot))
    def pad(self, ref, num):
        for p in self.part(ref).Pads():
            if p.GetNumber() == str(num): return p
    def padxy(self, ref, num):
        q = self.pad(ref, num).GetPosition(); return (tomm(q.x), tomm(q.y))
    def rm_seg(self, a, b, layer="B.Cu", net=None, tol=0.006):
        """remove the track piece whose ends are a and b (either order) on layer"""
        for t in list(self.b.GetTracks()):
            if t.GetClass() in ("PCB_VIA",): continue
            if self.b.GetLayerName(t.GetLayer()) != layer: continue
            s, e = t.GetStart(), t.GetEnd(); p = ((tomm(s.x), tomm(s.y)), (tomm(e.x), tomm(e.y)))
            ok = lambda u, v: abs(u[0]-v[0]) < tol and abs(u[1]-v[1]) < tol
            if (ok(p[0], a) and ok(p[1], b)) or (ok(p[0], b) and ok(p[1], a)):
                self.b.Remove(t); self.grave.append(t); self.log.append("rm %s %s-%s" % (layer, a, b)); return True
        raise SystemExit("segment not found: %s %s %s" % (layer, a, b))
    def rm_via(self, xy, tol=0.006):
        for t in list(self.b.GetTracks()):
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                if abs(tomm(p.x)-xy[0]) < tol and abs(tomm(p.y)-xy[1]) < tol:
                    self.b.Remove(t); self.grave.append(t); self.log.append("rm via %s" % (xy,)); return True
        raise SystemExit("via not found %s" % (xy,))
    def poly(self, pts, net, layer="B.Cu", w=0.1):
        nt = self.b.FindNet(net); L = {"B.Cu": pcbnew.B_Cu, "F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu}[layer]
        for a, c in zip(pts, pts[1:]):
            if abs(a[0]-c[0]) < 1e-9 and abs(a[1]-c[1]) < 1e-9: continue
            t = pcbnew.PCB_TRACK(self.b); t.SetLayer(L); t.SetWidth(mm(w)); t.SetNet(nt); t.SetStart(V(*a)); t.SetEnd(V(*c)); self.b.Add(t)
            ang = math.degrees(math.atan2(c[1]-a[1], c[0]-a[0])) % 45
            if min(ang, 45-ang) > 0.05: raise SystemExit("not 0/45/90: %s -> %s" % (a, c))
        self.log.append("add %s %s %s" % (net, layer, pts))
    def via(self, xy, net, size=0.3, drill=0.15):
        v = pcbnew.PCB_VIA(self.b); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetPosition(V(*xy)); v.SetWidth(mm(size)); v.SetDrill(mm(drill)); v.SetNet(self.b.FindNet(net)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); self.b.Add(v); self.log.append("add via %s %s" % (net, xy))
    def save(self, out): pcbnew.SaveBoard(out, self.b)

def _near(a, b, tol=0.012): return abs(a[0]-b[0]) < tol and abs(a[1]-b[1]) < tol
def tracks_of(ed, net=None, layer=None):
    out = []
    for t in ed.b.GetTracks():
        if t.GetClass() == "PCB_VIA": continue
        if net is not None and t.GetNetname() != net: continue
        if layer is not None and ed.b.GetLayerName(t.GetLayer()) != layer: continue
        out.append(t)
    return out
def ends(t): s, e = t.GetStart(), t.GetEnd(); return (tomm(s.x), tomm(s.y)), (tomm(e.x), tomm(e.y))
def rm_tail(ed, start, net, layer="B.Cu", stop_pads=()):
    """remove the chain of track pieces of `net` that starts at `start` (a pad centre) and runs until it reaches a junction (another piece / via / pad of another part), returns the removed ends"""
    removed = []; cur = start
    while True:
        here = [t for t in tracks_of(ed, net, layer) if any(_near(p, cur) for p in ends(t))]
        if len(here) != 1 and removed: break
        if not here: break
        t = here[0]; a, b = ends(t); nxt = b if _near(a, cur) else a
        ed.b.Remove(t); ed.grave.append(t); removed.append((cur, nxt)); ed.log.append("rm tail %s %s -> %s" % (net, cur, nxt))
        # stop at a via, a pad, or when more than one other piece meets at nxt
        if any(_near((tomm(v.GetPosition().x), tomm(v.GetPosition().y)), nxt) for v in ed.b.GetTracks() if v.GetClass() == "PCB_VIA"): break
        if any(p for f in ed.b.GetFootprints() for p in f.Pads() if _near((tomm(p.GetPosition().x), tomm(p.GetPosition().y)), nxt)): break
        cur = nxt
        if len([t for t in tracks_of(ed, net, layer) if any(_near(p, cur) for p in ends(t))]) != 1: break
    return removed
def pad_rect(p):
    bb = p.GetBoundingBox(); return (tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
def d_rect_seg(R, a, c, step=0.02):
    n = max(2, int(math.hypot(c[0]-a[0], c[1]-a[1]) / step)); best = 9
    for i in range(n+1):
        t = i/n; x = a[0]+(c[0]-a[0])*t; y = a[1]+(c[1]-a[1])*t
        best = min(best, math.hypot(max(R[0]-x, 0, x-R[2]), max(R[1]-y, 0, y-R[3])))
    return best
def rm_colliding(ed, refs, margin=0.17, layer="B.Cu"):
    """remove every B.Cu track piece of another net that comes closer than `margin` (edge to edge) to a pad of the parts in refs; returns the list"""
    out = []
    for ref in refs:
        for p in ed.part(ref).Pads():
            R = pad_rect(p)
            for t in list(tracks_of(ed, None, layer)):
                if t.GetNetname() == p.GetNetname(): continue
                a, c = ends(t)
                if d_rect_seg(R, a, c) - tomm(t.GetWidth())/2 < margin:
                    ed.b.Remove(t); ed.grave.append(t); out.append((ref, p.GetNumber(), t.GetNetname(), a, c)); ed.log.append("rm colliding %s %s-%s (%s.%s)" % (t.GetNetname(), a, c, ref, p.GetNumber()))
    return out
def near_vias(ed, refs, margin=0.25):
    out = []
    for ref in refs:
        for p in ed.part(ref).Pads():
            R = pad_rect(p)
            for v in ed.b.GetTracks():
                if v.GetClass() != "PCB_VIA" or v.GetNetname() == p.GetNetname(): continue
                q = v.GetPosition(); x, y = tomm(q.x), tomm(q.y)
                d = math.hypot(max(R[0]-x, 0, x-R[2]), max(R[1]-y, 0, y-R[3])) - tomm(v.GetWidth(pcbnew.B_Cu))/2
                if d < margin: out.append((ref, p.GetNumber(), v.GetNetname(), (round(x, 3), round(y, 3)), round(d, 3)))
    return out
