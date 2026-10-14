"""Nudge back-side parts out of the LED-ring via lanes.  The polar copper (vias at the lane radii, ROW arcs on In1) runs through the ring band;
back parts that sit in that band (plug J1, programming pads J2) must keep clear of it.  Also deletes the Tag-Connect keep-out areas left inside J2.
usage (KiCad python): fix_back_ring.py in_with_polar.kicad_pcb base_in.kicad_pcb base_out.kicad_pcb REF[,REF...]
 - in_with_polar: the board after polar_route.py (obstacles are read from it)
 - base_in / base_out: the placement-only board the parts are moved in
Search: translations within +-2.5 mm (J2: whole right strip) keeping the rotation; clearance model = JLCPCB via/hole rules (+ margin)."""
import math
import sys

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
pol = pcbnew.LoadBoard(sys.argv[1])
base = pcbnew.LoadBoard(sys.argv[2])
refs = sys.argv[4].split(",")

segs = []          # (x1, y1, x2, y2, half_width)
vias = []          # (x, y)
for t in pol.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vias.append((tomm(t.GetPosition().x), tomm(t.GetPosition().y)))
    else:
        s, e = t.GetStart(), t.GetEnd()
        segs.append((tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y), tomm(t.GetWidth()) / 2))
bf = {f.GetReference(): f for f in base.GetFootprints()}
others_court = {}
others_pads = {}                                   # side -> list of boxes (all footprints except the ones being moved)
for ref, f in bf.items():
    if ref in refs:
        continue
    for p in f.Pads():
        r = p.GetBoundingBox()
        box = (tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()))
        sides = ("F", "B") if p.HasHole() else (("B",) if f.IsFlipped() else ("F",))
        for s_ in sides:
            others_pads.setdefault(s_, []).append(box)
    poly = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if poly.OutlineCount():
        cb = poly.BBox()
        others_court.setdefault("B" if f.IsFlipped() else "F", []).append((tomm(cb.GetX()), tomm(cb.GetY()), tomm(cb.GetRight()), tomm(cb.GetBottom())))


def d_pt_seg(px, py, s):
    x1, y1, x2, y2, hw = s
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)) - hw


def d_pt_box(px, py, b):
    dx = max(b[0] - px, 0, px - b[2])
    dy = max(b[1] - py, 0, py - b[3])
    return math.hypot(dx, dy)


def d_box_pt(bx, px, py):
    return d_pt_box(px, py, bx)


def clear(f):
    """True if the footprint at its current position keeps clear of the polar copper and the other pads"""
    own = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if own.OutlineCount():
        ob_ = own.BBox()
        cb_ = (tomm(ob_.GetX()), tomm(ob_.GetY()), tomm(ob_.GetRight()), tomm(ob_.GetBottom()))
        for oc in others_court.get("B" if f.IsFlipped() else "F", []):
            if cb_[0] < oc[2] and oc[0] < cb_[2] and cb_[1] < oc[3] and oc[1] < cb_[3]:
                return False
    for p in f.Pads():
        r = p.GetBoundingBox()
        box = (tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()))
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if p.HasHole():                                       # plated hole: whole-stack copper ring, radius ~ half of the pad
            rr = max(tomm(p.GetSize().x), tomm(p.GetSize().y)) / 2
            for s in segs:
                if min(s[0], s[2]) - 1.2 < cx < max(s[0], s[2]) + 1.2 and min(s[1], s[3]) - 1.2 < cy < max(s[1], s[3]) + 1.2 and d_pt_seg(cx, cy, s) < rr + 0.12:
                    return False
            for vx, vy in vias:
                if math.hypot(vx - cx, vy - cy) < rr + 0.15 + 0.12:
                    return False
            for side in ("F", "B"):
                for ob in others_pads.get(side, []):
                    if d_pt_box(cx, cy, ob) < rr + 0.12:
                        return False
        else:
            for vx, vy in vias:                               # SMD pad on the back vs the via's annular ring and hole
                if d_pt_box(vx, vy, box) < 0.15 + 0.12 or (box[0] - 0.3 < vx < box[2] + 0.3 and box[1] - 0.3 < vy < box[3] + 0.3 and d_pt_box(vx, vy, box) < 0.30):
                    return False
            side = "B" if f.IsFlipped() else "F"
            for ob in others_pads.get(side, []):
                if box[0] - 0.25 < ob[2] and ob[0] < box[2] + 0.25 and box[1] - 0.25 < ob[3] and ob[1] < box[3] + 0.25:
                    return False
        if max(math.hypot(x - 100, y - 100) for x in (box[0], box[2]) for y in (box[1], box[3])) > 20.5:
            return False
    return True


moved = {}
for ref in refs:
    f = bf[ref]
    if ref == "J2":
        for z in list(f.Zones()):
            f.Remove(z)                                       # Tag-Connect keep-out areas
    x0, y0 = tomm(f.GetPosition().x), tomm(f.GetPosition().y)
    rot0 = f.GetOrientationDegrees()
    best = None
    all_segs, all_vias = segs[:], vias[:]
    segs[:] = [q for q in all_segs if x0 - 14 < min(q[0], q[2]) < x0 + 14 and y0 - 14 < min(q[1], q[3]) < y0 + 14]
    vias[:] = [q for q in all_vias if abs(q[0] - x0) < 14 and abs(q[1] - y0) < 14]
    if ref == "J2":
        rots = [rot0, (rot0 + 180) % 360]
        span_x, span_y, step = (-6.0, 1.0), (-8.0, 8.0), 0.1
    else:
        rots = [rot0]
        span_x, span_y, step = (-2.5, 2.5), (-2.5, 2.5), 0.1
    for rot in rots:
        f.SetOrientationDegrees(rot)
        nx = int((span_x[1] - span_x[0]) / step) + 1
        ny = int((span_y[1] - span_y[0]) / step) + 1
        for i in range(nx):
            for j in range(ny):
                dx, dy = span_x[0] + i * step, span_y[0] + j * step
                f.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
                d = math.hypot(dx, dy) + (0.01 if rot != rot0 else 0)
                if best is not None and d >= best[0]:
                    continue
                if clear(f):
                    best = (d, x0 + dx, y0 + dy, rot)
    segs[:] = all_segs
    vias[:] = all_vias
    if best is None:
        print(ref, "NO CLEAR POSITION in the search window")
        f.SetPosition(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        f.SetOrientationDegrees(rot0)
        continue
    _, x, y, rot = best
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    f.SetOrientationDegrees(rot)
    print("%s: (%.2f, %.2f) rot %.0f -> (%.2f, %.2f) rot %.0f   moved %.2f mm" % (ref, x0, y0, rot0, x, y, rot, best[0]))
pcbnew.SaveBoard(sys.argv[3], base)
