"""Placement sketch of the new RGB watch: board outline, the 132 ring LEDs (positions copied from the old routed RGB board), the interior parts from a table, and a fit check.
No nets except the LED pads, nothing is routed.  Everything that sets the layout is in the PARAMETERS and PARTS tables below.
usage (KiCad python): build_sketch.py [--R 22.0] [--ring 15.0,17.5,20.0] [--out "../LED Watch - RGB.kicad_pcb"]
The fit check prints: parts whose courtyards overlap (same side), parts outside the usable circle, parts inside the solar cell / battery keep-outs, and the free distance to the nearest ring LED."""
import argparse
import json
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD_FP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
SC_FP = os.path.join(HERE, "..", "..", "single-color", "hardware", "footprints", "LEDWatch.pretty")
NEW_FP = os.path.join(HERE, "..", "footprints", "LEDWatchRGB.pretty")
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
V = pcbnew.VECTOR2I

ap = argparse.ArgumentParser()
ap.add_argument("--R", type=float, default=22.0, help="board radius, mm")
ap.add_argument("--ring", default="15.0,17.5,20.0", help="hour, minute, second ring radius, mm")
ap.add_argument("--out", default=os.path.join(HERE, "..", "LED Watch - RGB.kicad_pcb"))
ap.add_argument("--edge", type=float, default=0.6, help="courtyard to board edge, mm")
args = ap.parse_args()
R = args.R
RING_OLD = (14.0, 16.5, 19.0)
RING = tuple(float(x) for x in args.ring.split(","))
CX = CY = 100.0

# ---- keep-outs copied from the single-colour board (board frame, centre = 0,0)
KEEP_SOLAR = (-11.58, -4.08, 11.57, 4.07)                  # front: the cell body lies on the board here, nothing may stand in it
KEEP_LIPO = [(-8.33, -19.58, 8.32, -3.42), (-8.33, 3.42, 8.32, 19.57)]     # back: the two pouch cells (16.5 x 16 x 5.25)

# ---- parts table: ref, library ('k' = KiCad stock, 's' = single-colour LEDWatch, 'n' = new LEDWatchRGB), footprint, value, x, y, rot, side
# rot is the footprint rotation as in pcbnew (degrees); coordinates are board-frame mm, centre of the watch = 0,0, +y downward; the back side is NOT mirrored here
P = []


def part(ref, lib, name, value, x, y, rot=0.0, side="F", group=""):
    P.append(dict(ref=ref, lib=lib, name=name, value=value, x=x, y=y, rot=rot, side=side, group=group))


# front, centre: solar cell pads, mode lights, accelerometer, buttons (positions of the single-colour board)
part("SC1+", "s", "KXOB25_cell_pad_2.5x7.4mm", "cell pad", 10.75, 0.0)
part("SC1-", "s", "KXOB25_cell_pad_2.5x7.4mm", "cell pad", -10.75, 0.0)
for i in range(7):
    part("IND%d" % (i + 1), "n", "RGB0808_CommonAnode", "NCD0808RGB1 / MHPA0808RGBDT", -10.2 + 3.4 * i, 4.9, 90.0, group="mode")
part("IMU", "k", "Package_LGA.pretty/LGA-12_2x2mm_P0.5mm", "LIS2DW12", 0.0, 8.35)
part("SW1", "k", "Button_Switch_SMD.pretty/SW_Push_1P1T_NO_CK_KMR2", "SW", -4.45, 9.1)
part("SW2", "k", "Button_Switch_SMD.pretty/SW_Push_1P1T_NO_CK_KMR2", "SW", 4.45, 9.1)

# front, top segment: 24 row switches (P-channel, X2-DFN1006); the packer fills them in below
ROWSW = ["Q%d" % (i + 1) for i in range(24)]
COLR = ["RC%d" % (i + 1) for i in range(18)]

# back: harvester block (positions of the single-colour board), MCU, buzzer, plugs, pogo pads
BQ = [("BQ", "s", "BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm", "BQ25570", 0.0, 0.0),
      ("L1", "k", "Inductor_SMD.pretty/L_1210_3225Metric", "22uH", 7.3, 0.0), ("L2", "k", "Inductor_SMD.pretty/L_1210_3225Metric", "10uH", -7.7, 0.0),
      ("C54", "k", "Capacitor_SMD.pretty/C_0805_2012Metric", "22u", 4.55, 0.6),
      ("C50", "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "4u7", 9.5, -1.3), ("C51", "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "10n", -5.2, 1.4),
      ("C52", "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "4u7", 2.9, 1.4), ("C53", "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "10n", 9.5, 1.4),
      ("R50", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "6.49M", -2.95, 1.4), ("R51", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "5.11M", -4.05, 1.4),
      ("R52", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "1.47M", -2.95, -1.3), ("R53", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "6.49M", 4.55, -1.75),
      ("R54", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "3.74M", 2.9, -1.3), ("R55", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "6.49M", -5.2, -1.3),
      ("R56", "k", "Resistor_SMD.pretty/R_0402_1005Metric", "3.74M", -4.05, -1.3)]
ENV = lambda k, d: float(os.environ.get(k, d))
BQ_DX = ENV("BQ_DX", "-1.0")
for ref, lib, name, val, x, y in BQ:
    part(ref, lib, name, val, x + BQ_DX, y, 0.0, "B", "bq")

part("MCU", "k", "Package_DFN_QFN.pretty/VQFN-64-1EP_9x9mm_P0.5mm_EP5.4x5.4mm", "AVR128DB64-I/MR", ENV("MCU_X", "14.7"), ENV("MCU_Y", "0"), 0.0, "B", "mcu")
part("BZ1", "s", "Piezo_Murata_PKMCS0909E4000-R1_9x9mm", "PKMCS0909E4000-R1", ENV("BZ_X", "-15.4"), ENV("BZ_Y", "0.0"), 0.0, "B", "bz")
part("J1", "k", "Connector_JST.pretty/JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", "LiPo", ENV("J1_X", "-13.0"), ENV("J1_Y", "-10.0"), 0.0, "B", "plug")
part("J1B", "k", "Connector_JST.pretty/JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", "LiPo", ENV("J1B_X", "-13.0"), ENV("J1B_Y", "10.0"), 0.0, "B", "plug")
part("J2", "s", "UPDI_Pogo_1x4_P1.27mm_2Guide", "UPDI pogo", ENV("J2_X", "14.5"), ENV("J2_Y", "9.5"), 90.0, "B", "pogo")

# parts the packer places (first fit, rows from the top of the region): (refs, library, footprint, value, region x0,y0,x1,y1, side, rotation, gap)
AUTO = [
    (ROWSW, "k", "Package_DFN_QFN.pretty/Diodes_DFN1006-3", "DMP21D0UFB4", (-12.0, -12.5, 12.0, -4.4), "F", 0.0, 0.15),
    (["Y1"], "k", "Crystal.pretty/Crystal_SMD_3215-2Pin_3.2x1.5mm", "32.768kHz", (9.0, -14.0, 20.0, -5.6), "B", 0.0, 0.2),
    (["C20", "C21"], "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "18p", (9.0, -14.0, 20.0, -5.6), "B", 0.0, 0.2),
    (COLR, "k", "Resistor_SMD.pretty/R_0402_1005Metric", "R", (9.0, -16.0, 21.0, -5.6), "B", 0.0, 0.15),
    (["CM%d" % i for i in range(1, 8)], "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "100n", (9.0, 5.8, 21.0, 16.0), "B", 0.0, 0.15),
    (["C30", "C31"], "k", "Capacitor_SMD.pretty/C_0402_1005Metric", "100n", (-9.5, 5.0, 9.5, 8.0), "F", 0.0, 0.15),
    (["R20", "R21"], "k", "Resistor_SMD.pretty/R_0402_1005Metric", "10k", (9.0, 5.8, 21.0, 16.0), "B", 0.0, 0.15),
]

# ---------------------------------------------------------------- board
b = pcbnew.CreateEmptyBoard()
b.SetCopperLayerCount(4)


def circle_pts(r, a0, a1, n):
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def outline_points(R, lug_w=25.1, lug_end=25.55, corner=1.5):
    """circle of radius R plus two strap lugs (top and bottom), rounded outer corners"""
    hx = lug_w / 2
    ya = math.sqrt(R * R - hx * hx)                       # where the lug side meets the circle
    ang = math.degrees(math.asin(hx / R))
    pts = []
    # right arc from just below the top lug to just above the bottom lug (y down: angle measured from +x, going clockwise on screen)
    a_top = -(90 - ang)                                  # point (hx, -ya)
    a_bot = (90 - ang)                                   # point (hx, +ya)
    pts += circle_pts(R, a_top, a_bot, 120)
    # bottom lug, going right to left
    def lug(sign):
        out = []
        out.append((hx, sign * ya))
        out += [(hx, sign * (lug_end - corner))]
        cx, cy = hx - corner, sign * (lug_end - corner)
        for i in range(0, 11):
            a = math.radians(0 + 90 * i / 10) * (1 if sign > 0 else -1)
            out.append((cx + corner * math.cos(a), cy + corner * math.sin(a)))
        for i in range(0, 11):
            a = math.radians(90 + 90 * i / 10) * (1 if sign > 0 else -1)
            out.append((-hx + corner + corner * math.cos(a), cy + corner * math.sin(a)))
        out.append((-hx, sign * ya))
        return out
    pts += lug(1)[1:]
    pts += circle_pts(R, 180 - (90 - ang) * 0 - (90 - ang), 180 + (90 - ang), 120)[0:0]
    # left arc: from bottom-left (-hx, +ya) up to (-hx, -ya)
    a1 = 90 + ang
    a2 = 270 - ang
    pts += circle_pts(R, a1, a2, 120)
    top = lug(-1)
    top.reverse()
    pts += top[1:]
    return pts


def poly_shape(pts, layer, width=0.05):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyPoints([V(mm(CX + x), mm(CY + y)) for x, y in pts])
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    s.SetFilled(False)
    b.Add(s)


poly_shape(outline_points(R), pcbnew.Edge_Cuts)
# strap slots (2.5 mm wide, 19.75 long) in the lugs
for sy in (-22.5, 22.5):
    pts = []
    hw, hh = 19.75 / 2, 2.5 / 2
    for ang_ in range(0, 361, 6):
        pass
    cap = hh
    n = 12
    pts = [(-hw + cap + cap * math.cos(math.radians(90 + 180 * i / n)) * 1, sy + cap * math.sin(math.radians(90 + 180 * i / n))) for i in range(n + 1)]
    pts += [(hw - cap + cap * math.cos(math.radians(-90 + 180 * i / n)), sy + cap * math.sin(math.radians(-90 + 180 * i / n))) for i in range(n + 1)]
    poly_shape(pts, pcbnew.Edge_Cuts)
for rect, name, layer in [(KEEP_SOLAR, "solar cell keep-out (front)", pcbnew.User_1)] + [(k, "LiPo keep-out (back)", pcbnew.User_2) for k in KEEP_LIPO]:
    x0, y0, x1, y1 = rect
    poly_shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], layer, 0.1)


# ---------------------------------------------------------------- footprints
def lib_path(lib, name):
    if lib == "k":
        l, n = name.split("/")
        return os.path.join(KICAD_FP, l), n
    if lib == "s":
        return SC_FP, name
    return NEW_FP, name


def add_fp(ref, lib, name, value, x, y, rot, side):
    path, n = lib_path(lib, name)
    f = pcbnew.FootprintLoad(path, n)
    if f is None:
        raise SystemExit("footprint not found: %s / %s" % (path, n))
    f.SetReference(ref)
    f.SetValue(value)
    b.Add(f)
    f.SetPosition(V(mm(CX + x), mm(CY + y)))
    f.SetOrientationDegrees(rot)
    if side == "B":
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    return f


placed = {}
NETS = {}
# the ring LEDs: the old board's positions, scaled radially to the chosen ring radii, rotation +90 (see docs/DESIGN-SKETCH.md: Meihua pin 1/2/3/4 land on the old pads 1/4/3/2)
old = json.load(open(os.path.join(HERE, "..", "data", "old_ring.json")))
ring_of = {RING_OLD[0]: 0, RING_OLD[1]: 1, RING_OLD[2]: 2}
colour_pad = {"4": "R", "3": "G", "2": "B"}
for d in old:
    r0 = round(math.hypot(d["x"], d["y"]), 1)
    k = RING[ring_of[r0]] / r0
    x, y = d["x"] * k, d["y"] * k
    f = add_fp(d["ref"], "n", "RGB0808_CommonAnode", "NCD0808RGB1 / MHPA0808RGBDT", x, y, 90.0, "F")
    placed[d["ref"]] = f
    # nets: old pad 1 = row (common), old pad 4 = R column, 3 = G, 2 = B  ->  new pad numbers 1, 2, 3, 4 (rotation +90 puts new pin 2 (R) on old pad 4, new 3 (G) on old 3, new 4 (B) on old 2)
    m = {"1": d["pads"]["1"]["net"], "2": d["pads"]["4"]["net"], "3": d["pads"]["3"]["net"], "4": d["pads"]["2"]["net"]}
    for pd in f.Pads():
        nm = m[pd.GetNumber()]
        if nm not in NETS:
            NETS[nm] = pcbnew.NETINFO_ITEM(b, nm)
            b.Add(NETS[nm])
        pd.SetNet(NETS[nm])

for p in P:
    placed[p["ref"]] = add_fp(p["ref"], p["lib"], p["name"], p["value"], p["x"], p["y"], p["rot"], p["side"])


def court_bb(f):
    """bounding box of the courtyard (or, without one, of the pads plus 0.1 mm), in nm"""
    lay = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
    poly = f.GetCourtyard(lay)
    if poly is not None and poly.OutlineCount() > 0:
        return poly.BBox()
    bb = None
    for pd in f.Pads():
        pb = pd.GetBoundingBox()
        if bb is None:
            bb = pcbnew.BOX2I(pb.GetOrigin(), pb.GetSize())
        else:
            bb.Merge(pb)
    bb.Inflate(mm(0.1))
    return bb



# top segment of the front: pack the row switches and the column resistors into rows between the cell keep-out and the ring
def courtyard_wh(f):
    bb = court_bb(f)
    return tomm(bb.GetWidth()), tomm(bb.GetHeight())


def pack_rows(refs, lib, name, value, y0, pitch_y, per_row, gap, rot=0.0, side="F"):
    n = len(refs)
    i = 0
    row = 0
    while i < n:
        take = refs[i:i + per_row]
        f0 = add_fp(take[0], lib, name, value, 0, 0, rot, side)
        w, h = courtyard_wh(f0)
        f0.SetPosition(V(0, 0))
        total = len(take) * (w + gap) - gap
        x = -total / 2 + w / 2
        for j, ref in enumerate(take):
            f = f0 if j == 0 else add_fp(ref, lib, name, value, 0, 0, rot, side)
            f.SetPosition(V(mm(CX + x), mm(CY + y0 + row * pitch_y)))
            placed[ref] = f
            x += w + gap
        i += per_row
        row += 1




def bbox_now(f):
    bb = court_bb(f)
    return (tomm(bb.GetX()) - CX, tomm(bb.GetY()) - CY, tomm(bb.GetX() + bb.GetWidth()) - CX, tomm(bb.GetY() + bb.GetHeight()) - CY)


def box_ok(bx, side_, region, usable_r, placed_boxes, gap):
    x0, y0, x1, y1 = region
    if bx[0] < x0 or bx[2] > x1 or bx[1] < y0 or bx[3] > y1:
        return False
    if max(math.hypot(x, y) for x, y in ((bx[0], bx[1]), (bx[2], bx[1]), (bx[2], bx[3]), (bx[0], bx[3]))) > usable_r:
        return False
    if side_ == "F" and not (bx[2] < KEEP_SOLAR[0] or bx[0] > KEEP_SOLAR[2] or bx[3] < KEEP_SOLAR[1] or bx[1] > KEEP_SOLAR[3]):
        return False
    if side_ == "B":
        for k in KEEP_LIPO:
            if not (bx[2] < k[0] or bx[0] > k[2] or bx[3] < k[1] or bx[1] > k[3]):
                return False
    for ob_side, ob in placed_boxes:
        if ob_side == side_ and bx[0] < ob[2] + gap and ob[0] < bx[2] + gap and bx[1] < ob[3] + gap and ob[1] < bx[3] + gap:
            return False
    return True


def autopack(usable_r):
    placed_boxes = []
    for ref, f in placed.items():
        if not (ref.startswith("U") and ref[1:].isdigit() and 2 <= int(ref[1:]) <= 133):
            placed_boxes.append(("B" if f.IsFlipped() else "F", bbox_now(f)))
    for ref, f in placed.items():                           # the ring LEDs keep a clearance from front parts, too
        if ref.startswith("U") and ref[1:].isdigit() and 2 <= int(ref[1:]) <= 133:
            placed_boxes.append(("F", bbox_now(f)))
    failed = []
    for refs, lib, name, value, region, side_, rot, gap in AUTO:
        for ref in refs:
            f = add_fp(ref, lib, name, value, 0, 0, rot, side_)
            w0 = bbox_now(f)
            wd, ht = w0[2] - w0[0], w0[3] - w0[1]
            done = False
            y = region[1] + ht / 2
            while y <= region[3] - ht / 2 + 1e-6 and not done:
                x = region[0] + wd / 2
                while x <= region[2] - wd / 2 + 1e-6:
                    bx = (x - wd / 2, y - ht / 2, x + wd / 2, y + ht / 2)
                    if box_ok(bx, side_, region, usable_r, placed_boxes, gap):
                        f.SetPosition(V(mm(CX + x), mm(CY + y)))
                        if side_ == "B":
                            pass
                        placed[ref] = f
                        placed_boxes.append((side_, bbox_now(f)))
                        done = True
                        break
                    x += 0.1
                y += 0.1
            if not done:
                failed.append(ref)
                b.Remove(f)
    return failed


# ---------------------------------------------------------------- fit check
usable = R - args.edge
FAILED = autopack(usable)


def bbox_mm(f):
    bb = court_bb(f)
    return (tomm(bb.GetX()) - CX, tomm(bb.GetY()) - CY, tomm(bb.GetX() + bb.GetWidth()) - CX, tomm(bb.GetY() + bb.GetHeight()) - CY)


def corners(bx):
    return [(bx[0], bx[1]), (bx[2], bx[1]), (bx[2], bx[3]), (bx[0], bx[3])]


def overlap(a, c, m=0.0):
    return a[0] < c[2] - m and c[0] < a[2] - m and a[1] < c[3] - m and c[1] < a[3] - m


issues = []
objs = [(ref, f) for ref, f in placed.items()]
boxes = {ref: bbox_mm(f) for ref, f in objs}
side = {ref: ("B" if f.IsFlipped() else "F") for ref, f in objs}
for ref, bx in boxes.items():
    if ref.startswith("U") and ref[1:].isdigit() and int(ref[1:]) >= 2 and int(ref[1:]) <= 133:
        continue
    worst = max(math.hypot(x, y) for x, y in corners(bx))
    # lugs: parts in the strap lugs are not expected; the circle is the limit
    if worst > usable:
        issues.append("OUT   %-6s corner at r=%.2f > usable %.2f" % (ref, worst, usable))
    if side[ref] == "F" and overlap(bx, KEEP_SOLAR) and ref not in ("SC1+", "SC1-"):
        issues.append("SOLAR %-6s inside the cell keep-out" % ref)
    if side[ref] == "B":
        for k in KEEP_LIPO:
            if overlap(bx, k):
                issues.append("LIPO  %-6s inside a battery keep-out" % ref)
refs = sorted(boxes)
for i, a in enumerate(refs):
    for c in refs[i + 1:]:
        if side[a] == side[c] and overlap(boxes[a], boxes[c], 0.3):
            la = a.startswith("U") and a[1:].isdigit() and 2 <= int(a[1:]) <= 133
            lc = c.startswith("U") and c[1:].isdigit() and 2 <= int(c[1:]) <= 133
            if la and lc:
                continue
            issues.append("OVER  %-6s x %-6s" % (a, c))
# distance of the interior parts (front) to the nearest ring LED
ring_leds = [boxes[r] for r in boxes if r.startswith("U") and r[1:].isdigit() and 2 <= int(r[1:]) <= 133]
for ref, bx in boxes.items():
    if side[ref] != "F" or (ref.startswith("U") and ref[1:].isdigit() and 2 <= int(ref[1:]) <= 133):
        continue
    for lb in ring_leds:
        if overlap(bx, lb, -0.15):
            issues.append("RING  %-6s closer than 0.15 mm to a ring LED" % ref)
            break
for ref_, f_ in placed.items():            # keep the pictures readable: only the bigger parts show their reference
    if (ref_.startswith("U") and ref_[1:].isdigit()) or ref_.startswith(("Q", "RC", "CM", "IND", "C", "R")) and ref_ not in ("RC",):
        f_.Reference().SetVisible(False)
    f_.Value().SetVisible(False)
print("board radius %.2f, ring radii %s, usable radius %.2f, parts %d" % (R, RING, usable, len(placed)))
if FAILED:
    issues.append("NOROOM " + ",".join(FAILED))
print("\n".join(issues) if issues else "NO FIT ISSUES")
b.Save(args.out)
print("wrote", os.path.abspath(args.out))
