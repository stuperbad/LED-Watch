"""Small placement helpers for KiCad-python scripts (no shapely there): pad boxes, courtyard boxes, conflicts, search for a free spot."""
import math

import pcbnew

mm, tomm = pcbnew.FromMM, pcbnew.ToMM
CELLS = [(90.75, 79.5, 109.25, 97.5), (90.75, 102.5, 109.25, 120.5)]            # LiPo + margin envelope (User.3): nothing on the back inside these
SOLAR_BODY = (88.4, 95.9, 111.6, 104.1)                                        # solar cell body, front


def inter(a, c, m=0.0):
    return a[0] - m < c[2] and c[0] < a[2] + m and a[1] - m < c[3] and c[1] < a[3] + m


def pad_boxes(f):
    out = []
    for p in f.Pads():
        r = p.GetBoundingBox()
        out.append((tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()), p.HasHole()))
    return out


def court(f):
    poly = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if poly.OutlineCount() == 0:
        return None
    r = poly.BBox()
    return (tomm(r.GetX()), tomm(r.GetY()), tomm(r.GetRight()), tomm(r.GetBottom()))


def conflicts(fp, ref, extra_front=(), extra_back=(), margin=0.3):
    """names that the footprint `ref` collides with at its current place (pads + courtyards, other parts, keep-outs)"""
    f = fp[ref]
    mine = pad_boxes(f)
    bad = set()
    cm = court(f)
    for o, g in fp.items():
        if o == ref:
            continue
        same = g.IsFlipped() == f.IsFlipped()
        if same and cm is not None:
            co = court(g)
            if co is not None and inter(cm, co):
                bad.add(o)
        for a in mine:
            for c in pad_boxes(g):
                if not same and not (a[4] or c[4]):
                    continue
                if inter(a, c, margin):
                    bad.add(o)
    for a in mine:
        if f.IsFlipped():
            if any(inter(a, c) for c in CELLS) or any(inter(a, c, 0.2) for c in extra_back):
                bad.add("keep-out")
        else:
            if any(inter(a, c, 0.2) for c in extra_front):
                bad.add("keep-out")
    return bad


def set_side(f, back):
    if f.IsFlipped() != back:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)


def place(f, x, y, rot):
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def pad_pos(f, num):
    for p in f.Pads():
        if p.GetNumber() == str(num):
            return tomm(p.GetPosition().x), tomm(p.GetPosition().y)
