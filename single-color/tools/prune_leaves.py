"""Clean up after a re-route that joined new routes to the SIDES of old copper: for the given nets only,
  1. a via that touches copper on ONE layer only is not a layer change: with 2 or more tracks it is a plain junction (the tracks' ends move to its centre, the via goes); with 1 track it is a dead end (via goes);
  2. a track whose one end touches nothing (no pad, via or other copper of its net) is cut back to the nearest place where other copper of the net touches its side (that copper's end moves there, so the junction is a real one),
     or deleted if nothing touches it. 
Connectivity is judged by shape overlap, like KiCad does, not by end coordinates.
Only items with an end inside the box (cx, cy, half) are touched; everything else (arcs included) only counts as something to touch.
ONE pass per run (run it again until it reports 0 changes).
usage (KiCad python): prune_leaves.py in.kicad_pcb out.kicad_pcb CX CY HALF [--targets="[(x,y),...]"] NET [NET ...]
  --targets limits the work to the vias at those positions and the tracks within 0.8 mm of them   (or @file with one net per line)"""
import math
import os
import sys
import tempfile

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
CX, CY, HALF = (float(x) for x in sys.argv[3:6])
TARGETS = None
rest = sys.argv[6:]
for a_ in list(rest):
    if a_.startswith("--targets="):
        TARGETS = eval(a_.split("=", 1)[1]); rest.remove(a_)
NETS = rest
if NETS and NETS[0].startswith("@"):
    NETS = [ln.strip() for ln in open(NETS[0][1:]) if ln.strip()]
NETS = set(NETS)
EPS = 0.012


def pt(p):
    return (tomm(p.x), tomm(p.y))


def seg_point(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    q = (a[0] + t * dx, a[1] + t * dy)
    return q, math.hypot(p[0] - q[0], p[1] - q[1])


def one_pass(b):
    items = list(b.GetTracks())
    def inbox(p):
        return abs(tomm(p.x) - CX) <= HALF and abs(tomm(p.y) - CY) <= HALF
    allvias = [t for t in items if t.GetClass() == "PCB_VIA" and t.GetNetname() in NETS]
    vias = [t for t in allvias if inbox(t.GetPosition()) and (TARGETS is None or any(abs(tomm(t.GetPosition().x) - x_) < 0.05 and abs(tomm(t.GetPosition().y) - y_) < 0.05 for x_, y_ in TARGETS))]
    alltrks = [t for t in items if t.GetClass() == "PCB_TRACK" and t.GetNetname() in NETS]
    trks = [t for t in alltrks if (inbox(t.GetStart()) or inbox(t.GetEnd())) and (TARGETS is None or any(math.hypot(tomm(q.x) - x_, tomm(q.y) - y_) < 0.8 for q in (t.GetStart(), t.GetEnd()) for x_, y_ in TARGETS))]
    arcs = [t for t in items if t.GetClass() == "PCB_ARC" and t.GetNetname() in NETS]
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() in NETS]
    trash = []
    msgs = []

    def touches_pad(p, layer, net, w=0.1):
        v = pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
        return any(pd.GetNetname() == net and pd.IsOnLayer(layer) and pd.HitTest(v, mm(w / 2)) for pd in pads)

    # 1. vias
    for v in vias:
        c = pt(v.GetPosition()); r = tomm(v.GetWidth(pcbnew.F_Cu)) / 2
        net = v.GetNetname()
        near = []
        for t in alltrks:
            if t.GetNetname() != net or t in trash:
                continue
            for end in ("Start", "End"):
                p = pt(getattr(t, "Get" + end)())
                if math.hypot(p[0] - c[0], p[1] - c[1]) <= r + tomm(t.GetWidth()) / 2 + EPS:
                    near.append((t, end))
        arc_touch = []
        for a in arcs:
            if a.GetNetname() != net:
                continue
            for p_ in (pt(a.GetStart()), pt(a.GetEnd())):
                if math.hypot(p_[0] - c[0], p_[1] - c[1]) <= r + tomm(a.GetWidth()) / 2 + EPS:
                    arc_touch.append(a)
        layers = {t.GetLayer() for t, _ in near} | {a.GetLayer() for a in arc_touch}
        on_pad = any(pd.GetNetname() == net and pd.HitTest(v.GetPosition(), 0) for pd in pads)
        if len(layers) >= 2 or on_pad or arc_touch:
            continue
        if len(near) >= 2:
            for t, end in near:
                getattr(t, "Set" + end)(v.GetPosition())
            trash.append(v); msgs.append(f"junction via {net} at {c[0]:.3f},{c[1]:.3f} -> merged {len(near)} tracks")
        else:
            trash.append(v); msgs.append(f"dead-end via {net} at {c[0]:.3f},{c[1]:.3f} removed")
    live_vias = [v for v in allvias if v not in trash]

    # 2. tracks with a free end
    def contact(t, e, others):
        """does end e of track t touch something of its net (other track, via, pad)?  returns True/False"""
        w = tomm(t.GetWidth())
        for o in others:
            if o is t or o in trash or o.GetNetname() != t.GetNetname() or o.GetLayer() != t.GetLayer():
                continue
            s, f = pt(o.GetStart()), pt(o.GetEnd())
            q, dist = seg_point(e, s, f)
            if dist <= (w + tomm(o.GetWidth())) / 2 + EPS:
                return True
        for v in live_vias:
            if v.GetNetname() == t.GetNetname():
                c = pt(v.GetPosition())
                if math.hypot(e[0] - c[0], e[1] - c[1]) <= tomm(v.GetWidth(pcbnew.F_Cu)) / 2 + w / 2 + EPS:
                    return True
        for a in arcs:
            if a.GetNetname() != t.GetNetname() or a.GetLayer() != t.GetLayer():
                continue
            ps = [pt(a.GetStart()), pt(a.GetMid()), pt(a.GetEnd())]
            for i in range(2):
                q, dist = seg_point(e, ps[i], ps[i + 1])
                if dist <= (w + tomm(a.GetWidth())) / 2 + EPS:
                    return True
        return touches_pad(e, t.GetLayer(), t.GetNetname(), w)

    for t in trks:
        if t in trash:
            continue
        s, e = pt(t.GetStart()), pt(t.GetEnd())
        cs, ce = contact(t, s, alltrks), contact(t, e, alltrks)
        if cs and ce:
            continue
        if not cs and not ce:
            trash.append(t); msgs.append(f"isolated track {t.GetNetname()} {s} -> {e} removed")
            continue
        fixed, free = (s, e) if cs else (e, s)          # fixed = the connected end
        w = tomm(t.GetWidth())
        best = None
        for o in alltrks:
            if o is t or o in trash or o.GetNetname() != t.GetNetname() or o.GetLayer() != t.GetLayer():
                continue
            for end in ("Start", "End"):
                p = pt(getattr(o, "Get" + end)())
                q, dist = seg_point(p, fixed, free)
                if dist <= (w + tomm(o.GetWidth())) / 2 + EPS and math.hypot(q[0] - fixed[0], q[1] - fixed[1]) > 0.03 and math.hypot(p[0] - fixed[0], p[1] - fixed[1]) > 0.03:
                    d0 = math.hypot(q[0] - free[0], q[1] - free[1])
                    if best is None or d0 < best[0]:
                        best = (d0, q, o, end)
        if best is None:
            trash.append(t); msgs.append(f"leaf track {t.GetNetname()} {fixed} -> {free} removed")
        else:
            _, q, o, end = best
            nv = pcbnew.VECTOR2I(mm(q[0]), mm(q[1]))
            if free == s:
                t.SetStart(nv)
            else:
                t.SetEnd(nv)
            getattr(o, "Set" + end)(nv)
            msgs.append(f"cut {t.GetNetname()} tail at {q[0]:.3f},{q[1]:.3f}")
    for t in trash:
        b.Remove(t)
    return msgs, bool(trash)


b = pcbnew.LoadBoard(src)
msgs, removed = one_pass(b)
for m in msgs:
    print(m)
pcbnew.SaveBoard(dst, b)
print("changes:", len(msgs))
