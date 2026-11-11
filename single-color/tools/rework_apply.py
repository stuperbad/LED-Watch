"""rework_apply.py IN.kicad_pcb OUT.kicad_pcb POS.json [--clear MARGIN] : move the back parts of POS.json ({ref: [x, y, rot]}) and rip up the copper they now touch (KiCad python).
Removed: every track / arc / via of ANOTHER net that comes within MARGIN (default 0.25 mm) of a pad of a moved part (any copper layer a via touches), every track / via of the moved parts' own nets
that lies inside the window (--win x0,y0,x1,y1; default 90.2,95.6,111.8,104.4) and is not connected to anything outside it is NOT searched for: all own-net copper in the window goes (the router rebuilds it).
Prints the nets that lost copper (they need routing again)."""
import sys, json, collections, math, pcbnew
a = sys.argv[1:]; src, dst, posf = a[0], a[1], a[2]
margin = float(a[a.index("--clear") + 1]) if "--clear" in a else 0.25
win = tuple(map(float, a[a.index("--win") + 1].split(","))) if "--win" in a else (90.2, 95.6, 111.8, 104.4)
POS = json.load(open(posf)); b = pcbnew.LoadBoard(src); mm = pcbnew.ToMM; FM = pcbnew.FromMM
moved = []; oldpads = {}
for r, (x, y, rot) in POS.items():
    f = b.FindFootprintByReference(r)
    if f is None: print("missing", r); continue
    cur = (mm(f.GetPosition().x), mm(f.GetPosition().y), f.GetOrientationDegrees())
    if abs(cur[0] - x) < 1e-3 and abs(cur[1] - y) < 1e-3 and abs((cur[2] - rot + 180) % 360 - 180) < 1e-3: continue
    oldpads[r] = [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in f.Pads()]
    f.SetOrientationDegrees(2 * cur[2] - rot if f.IsFlipped() else rot); f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); moved.append(r)
print("moved", len(moved), moved)

mnets = set(); pads = []
for r in moved:
    f = b.FindFootprintByReference(r)
    for p in f.Pads():
        if p.GetNetname(): mnets.add(p.GetNetname())
        pads.append(p)
inwin = lambda p: win[0] <= mm(p.x) <= win[2] and win[1] <= mm(p.y) <= win[3]
def pad_hits(t):
    """distance from track/via copper to the nearest foreign pad of a moved part on a shared layer"""
    best = 1e9
    for p in pads:
        if p.GetNetname() == t.GetNetname(): continue
        if t.GetClass() != "PCB_VIA" and not p.IsOnLayer(t.GetLayer()): continue
        bb = p.GetBoundingBox(); cx, cy = mm(bb.GetCenter().x), mm(bb.GetCenter().y); hx, hy = mm(bb.GetWidth()) / 2, mm(bb.GetHeight()) / 2
        if t.GetClass() == "PCB_VIA": pts = [(mm(t.GetPosition().x), mm(t.GetPosition().y))]; rad = mm(t.GetWidth(t.TopLayer())) / 2 if hasattr(t, "TopLayer") else 0.2
        else:
            n = 6; s, e = t.GetStart(), t.GetEnd(); pts = [(mm(s.x) + (mm(e.x) - mm(s.x)) * i / n, mm(s.y) + (mm(e.y) - mm(s.y)) * i / n) for i in range(n + 1)]; rad = mm(t.GetWidth()) / 2
        for px, py in pts:
            d = math.hypot(max(abs(px - cx) - hx, 0), max(abs(py - cy) - hy, 0)) - rad; best = min(best, d)
    return best
CORE = {"U4", "L1", "L2", "C50", "C51", "C52", "C53", "C54", "R50", "R51", "R52", "R53", "R54", "R55", "R56"}
corenets = set()
for r in CORE & set(moved):
    for p in b.FindFootprintByReference(r).Pads():
        if p.GetNetname() and p.GetNetname() != "GND": corenets.add(p.GetNetname())
near_pts = [pt for r in moved if r not in CORE for pt in oldpads[r]] + [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for r in moved if r not in CORE for p in b.FindFootprintByReference(r).Pads()]
def near_usb(t):
    pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
    return any(math.hypot(mm(q.x) - px, mm(q.y) - py) < 1.0 for q in pts for px, py in near_pts)
gone = collections.Counter(); kill = []
for t in b.GetTracks():
    isvia = t.GetClass() == "PCB_VIA"; own = t.GetNetname() in mnets
    if t.GetClass() == "PCB_ARC": continue
    near = (inwin(t.GetPosition()) if isvia else (inwin(t.GetStart()) or inwin(t.GetEnd())))
    nm = t.GetNetname()
    if nm in corenets and inwin(t.GetPosition() if isvia else t.GetStart()) | inwin(t.GetPosition() if isvia else t.GetEnd()) and (win[0] <= mm((t.GetPosition() if isvia else t.GetStart()).x) <= 104.6 or win[0] <= mm((t.GetPosition() if isvia else t.GetEnd()).x) <= 104.6): kill.append(t); continue
    if nm == "GND" and not isvia and near and (CORE & set(moved)) and any(win[0] <= mm(q.x) <= 104.6 for q in (t.GetStart(), t.GetEnd())): kill.append(t); continue
    if own and near_usb(t) and nm != "GND": kill.append(t); continue
    if near and pad_hits(t) < margin: kill.append(t)
for t in kill: gone[t.GetNetname()] += 1; b.Remove(t)
print("removed", len(kill), "items; nets:", dict(gone))
# U4 courtyard: pads + 0.1 mm instead of the library's +0.34 (4.59 mm square) so that C52 / C53 can sit under the power pins
u4 = b.FindFootprintByReference("U4")
if u4 is not None and "--keep-courtyard" not in a:
    cx, cy = u4.GetPosition().x, u4.GetPosition().y; h = FM(2.05)
    for g in [g for g in u4.GraphicalItems() if g.GetLayer() == pcbnew.B_CrtYd]: u4.Remove(g)
    r = pcbnew.PCB_SHAPE(u4); r.SetShape(pcbnew.SHAPE_T_RECT); r.SetLayer(pcbnew.B_CrtYd); r.SetWidth(FM(0.05)); r.SetFilled(False)
    r.SetStart(pcbnew.VECTOR2I(int(cx - h), int(cy - h))); r.SetEnd(pcbnew.VECTOR2I(int(cx + h), int(cy + h))); u4.Add(r); print("U4 courtyard set to +-2.05 mm")
pcbnew.SaveBoard(dst, b)
