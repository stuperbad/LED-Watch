"""zonespec.py : the keep-out rules of the back-side layout, shared by ripzone.py / zones check. KiCad python.
Rules (docs/DECISION-LOG.md 2026-10-15 / 10-29 / 10-30): no copper of another net on any layer in the crystal octagon box; nothing but GND and U1's own VBAT in the 5 x 5 mm core under U1;
no In1 / B.Cu copper within 0.18 mm of a U1 pad; no foreign signal under the U4 core (F.Cu / In1); no foreign copper under the IMU (U2) pads box.
2026-11-02 review (owner: zones should be thought through, not forced): (a) the crystal zone is the OCTAGON of the F.Cu GND guard pour (chamfer 0.5 mm), not its bounding rectangle (hits() tests the octagon;
the rectangle stays in the list because the router's --exclude takes rectangles, which is the safe side); (b) the U1-pad rule (pad + 0.18 mm) was a router corridor rule for In1 vias / lanes beside the QFN pads: it now covers In1 only,
B.Cu lies behind the In2 ground plane and DRC already checks the real clearances; (c) the IMU zone is the pad box of U2 (99.05-100.95 x 107.4-109.3), the footprint's bounding box (0.33-0.57 mm larger on every side) included its silkscreen.
ZONES = [(name, (x0,y0,x1,y1), layers, allowed_nets)]  -- layers: tuple of F.Cu / In2.Cu / B.Cu.
2026-11-05: the inner layers were swapped (ground plane on In1 = layer 2, signals on In2 = layer 3); the crystal zone is now the front layer only (the plane sits directly under it, owner + reviewer), the other rules follow the signal layer to In2."""
import pcbnew
tomm = pcbnew.ToMM


def build(b):
    Z = [("crystal", (90.49, 90.815, 94.75, 95.585), ("F.Cu",), {"/XTAL1", "/XTAL2", "GND"}),
         ("mcu-core", (97.5, 89.37, 102.5, 94.37), ("F.Cu", "In2.Cu", "B.Cu"), {"GND", "VBAT"})]
    f = b.FindFootprintByReference("U1")
    for p in f.Pads():
        if p.GetNetname() in ("GND", ""):
            continue
        c = p.GetPosition(); hx, hy = tomm(p.GetSizeX()) / 2, tomm(p.GetSizeY()) / 2
        # pad rectangle (the QFN pads are axis aligned or 90 degrees; use the larger extent on the rotated axis)
        o = round(p.GetOrientationDegrees()) % 180
        if o == 90:
            hx, hy = hy, hx
        Z.append(("u1-pad %s" % p.GetNumber(), (tomm(c.x) - hx - 0.18, tomm(c.y) - hy - 0.18, tomm(c.x) + hx + 0.18, tomm(c.y) + hy + 0.18), ("In2.Cu",), {p.GetNetname(), "GND"}))
    for ref, lay, nm in (("U4", ("F.Cu", "In2.Cu"), "u4-core"), ("U2", ("F.Cu", "In2.Cu", "B.Cu"), "imu")):
        f = b.FindFootprintByReference(ref)
        bb = f.GetBoundingBox(False)              # all pads and the body outline, no courtyard
        if ref == "U2":                           # the pads of the LGA are the package footprint: the bounding box above also holds the silkscreen
            pb = [p.GetBoundingBox() for p in f.Pads()]
            box0 = (min(tomm(q.GetLeft()) for q in pb), min(tomm(q.GetTop()) for q in pb), max(tomm(q.GetRight()) for q in pb), max(tomm(q.GetBottom()) for q in pb))
        else:
            box0 = None
        own = {p.GetNetname() for p in f.Pads()}
        box = box0 or (tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
        if ref == "U4":                           # the 4 x 4 mm core of the harvester (2026-10-15 rule)
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            box = (cx - 2.0, cy - 2.0, cx + 2.0, cy + 2.0)
        Z.append((nm, box, lay, own))
    return Z


def in_octagon(x, y, x0, y0, x1, y1, c=0.5):
    """box with its four corners cut by c (the guard pour around the crystal): False inside a cut corner"""
    ex, ey = min(x - x0, x1 - x), min(y - y0, y1 - y)
    return not (ex < c and ey < c and ex + ey < c)


def hits(t, Z):
    """zone names where track / via t (not of an allowed net) has copper"""
    out = []
    isvia = t.GetClass() == "PCB_VIA"
    n = t.GetNetname()
    if isvia:
        pts = [(tomm(t.GetPosition().x), tomm(t.GetPosition().y))]
    else:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(tomm(s.x + (e.x - s.x) * i / 30), tomm(s.y + (e.y - s.y) * i / 30)) for i in range(31)]
    for name, (x0, y0, x1, y1), lay, allow in Z:
        if n in allow:
            continue
        if not isvia and t.GetLayerName() not in lay:
            continue
        if any(x0 <= x <= x1 and y0 <= y <= y1 and (name != "crystal" or in_octagon(x, y, x0, y0, x1, y1)) for x, y in pts):
            out.append(name)
    return out


def exclude_arg(Z, skip_nets=()):
    """--exclude string for grid_route2.py (vias always kept out; tracks only on the listed layers)"""
    short = {"F.Cu": "F", "In1.Cu": "In1", "B.Cu": "B"}
    parts = []
    for name, (x0, y0, x1, y1), lay, allow in Z:
        if name.startswith("imu") or name.startswith("u4"):
            pass
        parts.append("%.3f,%.3f,%.3f,%.3f@%s" % (x0, y0, x1, y1, ",".join(short[l] for l in lay)))
    return ";".join(parts)
