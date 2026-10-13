"""
Parametric board planner for the single-colour watch (system python: numpy, shapely, matplotlib).

  python plan_board.py --cell KXOB25 --diameter 0 --band 0 ...

  * outline  = circle(D) + two strap lugs (profile taken from the RGB board: 25.1 mm wide lugs sticking 3.67 mm out of the circle,
               2.5 mm corner radius, a 19.75 x 1.77 mm strap slot in each lug)           -> all of it is a parameter
  * LED rings = hours (inner, largest), minutes, seconds (outer, smallest), packed against the board edge, true radial rotation
  * band     = radial width of the LED band (outer edge of the seconds ring to inner edge of the hours ring).  0 = tightest that fits
  * everything else (BOM read from the schematic netlist) is packed as real KiCad courtyards onto the FRONT free centre (around the solar cell)
    or the BACK (around the battery). D = 0 searches for the smallest board where every part fits.
Writes  boards/<name>/plan.json  and  boards/<name>/<name>.png ; write_pcb.py (KiCad python) turns plan.json into a .kicad_pcb.
"""
import argparse, json, math, os, re, sys, xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Point, box, Polygon, LineString
from shapely.ops import unary_union
import shapely

KIDIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
HERE = os.path.dirname(os.path.abspath(__file__))

# LED sizes: (KiCad footprint, pad-axis length, pad width) from KiCad's own footprints
SIZES = {"0201": ("LED_0201_0603Metric", 1.10, 0.40), "0402": ("LED_0402_1005Metric", 1.56, 0.64),
         "0603": ("LED_0603_1608Metric", 2.45, 0.95), "0805": ("LED_0805_2012Metric", 2.85, 1.40)}
RINGS = {"H": 12, "M": 60, "S": 60}
CELLS = {"none": None, "KXOB25": ("KXOB25-07X1TF", 11.35, 8.0, 1.2), "KXOB25_05X3": ("KXOB25-05X3TF", 23.0, 8.0, 1.2), "AM1606": ("AM-1606C", 15.0, 15.0, 0.9), "KXOB081": ("KXOB081K06TF", 23.0, 25.0, 1.2)}
CELL_PADS = {"KXOB25-05X3TF": ("LEDWatch:KXOB25_cell_pad_2.5x7.4mm", 2.5, 7.4, 0.5)}      # name: (footprint, pad length, pad height, how far the pad sticks out past the cell end)
BATTS = {"tc70": ("TinyCircuits 70 mAh, JST-SH plug (nominal + half tolerance)", 16.5, 16.0, 5.25), "tc150": ("TinyCircuits 150 mAh, JST-SH plug (nominal + half tolerance)", 21.5, 21.0, 5.25),
         "301030": ("LP301030 ~70 mAh generic pouch (3.0 x 10 x 30)", 30.5, 10.2, 3.2), "401030": ("LP401030 90 mAh (LiPol datasheet, charge <= 45 mA)", 30.0, 10.0, 4.0),
         "401230": ("LP401230 100 mAh generic pouch", 30.0, 12.0, 4.0), "402025": ("LP402025 150 mAh generic pouch", 27.0, 20.0, 4.0), "lir2032": ("LIR2032 coin 40 mAh 3.6 V (no protection)", 20.0, 20.0, 3.2, "round"), "lir2450": ("LIR2450 coin ~120 mAh (UNVERIFIED)", 24.5, 24.5, 5.0, "round"),
         "35": ("ICP341018PM 35 mAh", 19.5, 10.2, 3.7), "50": ("ICP331319PM 50 mAh", 21.0, 12.8, 3.7), "80": ("ICP501022UPM 80 mAh", 24.0, 10.0, 5.5),
         "155": ("ICP402025PC-01 155 mAh", 27.5, 20.5, 4.3)}
STEP = 0.1


# ------------------------------------------------------------------ KiCad footprint courtyards
def _sexp(text):
    tok = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', text)
    pos = 0

    def parse():
        nonlocal pos
        out = []
        while pos < len(tok):
            t = tok[pos]; pos += 1
            if t == "(":
                out.append(parse())
            elif t == ")":
                return out
            else:
                out.append(t.strip('"'))
        return out
    return parse()


def courtyard(fpid):
    lib, name = fpid.split(":", 1)
    path = os.path.join(os.path.join(HERE, "footprints") if lib == "LEDWatch" else KIDIR, lib + ".pretty", name + ".kicad_mod")
    if not os.path.exists(path):
        return None
    root = _sexp(open(path, encoding="utf8").read())[0]
    xs, ys = [], []

    def walk(n):
        if isinstance(n, list):
            if n and n[0] in ("fp_rect", "fp_line", "fp_poly", "fp_circle", "fp_arc") and any(isinstance(c, list) and c[:1] == ["layer"] and c[1] == "F.CrtYd" for c in n):
                for c in n:
                    if isinstance(c, list) and c[0] in ("start", "end", "center", "mid"):
                        xs.append(float(c[1])); ys.append(float(c[2]))
                    if isinstance(c, list) and c[0] == "pts":
                        for p in c[1:]:
                            if isinstance(p, list) and p[0] == "xy":
                                xs.append(float(p[1])); ys.append(float(p[2]))
            for c in n:
                walk(c)
    walk(root)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


# ------------------------------------------------------------------ rings (same maths as gen_rings.py)
def tang_min_radius(n, width, gap):
    return (width + gap) / (2 * math.sin(math.pi / n))


def solve_rings(sizes, order, tang_gap, rad_gap, edge, diameter, free_min, band):
    def pack(D, rg):
        r_edge = D / 2 - edge
        radii = {}
        for k in reversed(order):
            L = SIZES[sizes[k]][1]
            radii[k] = r_edge - L / 2
            r_edge = radii[k] - L / 2 - rg
        return radii

    def band_rg(D):
        """radial gap that makes the LED band exactly `band` wide"""
        tot = sum(SIZES[sizes[k]][1] for k in order)
        return max(rad_gap, (band - edge - tot) / (len(order) - 1)) if band else rad_gap

    def ok(D):
        rg = band_rg(D)
        radii = pack(D, rg)
        inner = order[0]
        if radii[inner] - SIZES[sizes[inner]][1] / 2 <= free_min:
            return False
        if band and (D / 2 - (radii[inner] - SIZES[sizes[inner]][1] / 2)) > band + 1e-6 and False:
            return False
        return all(radii[k] >= tang_min_radius(RINGS[k], SIZES[sizes[k]][2], tang_gap) for k in order)
    D = diameter if diameter else 5.0
    if not diameter:
        while not ok(D):
            D += 0.05
    elif not ok(D):
        return None
    rg = band_rg(D)
    radii = pack(D, rg)
    inner = order[0]
    free_r = radii[inner] - SIZES[sizes[inner]][1] / 2
    return D, radii, free_r


# ------------------------------------------------------------------ outline
def outline(D, lug_w, lug_out, lug_r, slot_w, slot_h, slot_off, n_slots=2):
    R = D / 2
    shape = Point(0, 0).buffer(R, 256)
    for s in (+1, -1):
        shape = shape.union(box(-lug_w / 2, 0 if s > 0 else -(R + lug_out), lug_w / 2, (R + lug_out) if s > 0 else 0))
    shape = shape.buffer(-lug_r, 64).buffer(lug_r, 64)       # round the lug corners
    shape = shape.buffer(0.8, 32).buffer(-0.8, 32)           # soften the lug-to-circle junctions
    slots = []
    if n_slots:
        for s in ((+1, -1) if n_slots == 2 else (-1,)):
            cy = s * (R + slot_off)
            slots.append(LineString([(-slot_w / 2 + slot_h / 2, cy), (slot_w / 2 - slot_h / 2, cy)]).buffer(slot_h / 2, 32))
    return shape, slots


# ------------------------------------------------------------------ BOM from the netlist
def read_bom(variant, pkg="tqfp"):
    root = ET.parse(os.path.join(HERE, "schematic", f"n_{variant}.xml")).getroot()
    out = []
    for c in root.find("components"):
        ref = c.get("ref")
        if re.fullmatch(r"[HMS]\d+", ref) or re.fullmatch(r"IND\d", ref) or ref == "J1B":     # J1B (second plug) is created by the planner next to J1
            continue
        fp = c.find("footprint").text
        if fp.startswith("TBD:"):
            fp = "LEDWatch:BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm"   # real RGR0020A land pattern from TI's drawing (footprints/LEDWatch.pretty)
        if pkg == "qfn" and fp.startswith("Package_QFP:TQFP-48"):
            fp = "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm"        # VQFN-48 6LX: 6x6x0.8, 0.40 pitch, EP 4.1x4.1 (DS40002247B 42.9); KiCad EP is 4.2, so check the land pattern
        out.append((ref, c.find("value").text, fp))
    return out


def classify(ref, fp):
    if ref in ("J3", "J4"):
        return None                                              # solar-cell contact: sits under the cell, drawn separately
    if ref == "U1":
        return dict(prio=0, sides=["back", "front"], near="centre")
    if ref in ("J1",):
        return dict(prio=1, sides=["back"], near="battery")
    if ref in ("U4", "U3") or fp.startswith("Inductor") or "SOT-23" in fp:
        return dict(prio=2, sides=["back", "front"], near="mcu")
    if "SW_Push" in fp:
        return dict(prio=3, sides=["front"], near="edge")
    if "TestPoint" in fp:
        return dict(prio=3, sides=["back"], near="centre")
    if "Tag-Connect" in fp:
        return dict(prio=0.6, sides=["front", "back"], near="mcu")
    if "PinHeader" in fp:
        return dict(prio=4, sides=["back", "front"], near="mcu")
    if "Crystal" in fp or "LGA" in fp:
        return dict(prio=5, sides=["front", "back"], near="mcu")
    return dict(prio=6, sides=["front", "back"], near="mcu")


# ------------------------------------------------------------------ packing
class Region:
    def __init__(self, poly, R):
        n = int(2 * R / STEP) + 4
        self.c = n * STEP / 2
        xs = (np.arange(n) + 0.5) * STEP - self.c
        self.X, self.Y = np.meshgrid(xs, xs)
        self.free = shapely.contains_xy(poly, self.X, self.Y)

    def cum(self):
        s = np.zeros((self.free.shape[0] + 1, self.free.shape[1] + 1), dtype=np.int32)
        s[1:, 1:] = self.free.astype(np.int32).cumsum(0).cumsum(1)
        return s

    def place(self, w, h, target):
        """find the free w x h block closest to `target`; returns (cx, cy) centre or None and marks it used"""
        nw, nh = int(round(w / STEP)), int(round(h / STEP))
        S = self.cum()
        H, W = S.shape[0] - 1, S.shape[1] - 1
        if nh > H or nw > W:
            return None
        tot = S[nh:, nw:] - S[:-nh, nw:] - S[nh:, :-nw] + S[:-nh, :-nw]
        ok = np.argwhere(tot == nw * nh)
        if len(ok) == 0:
            return None
        cx = (ok[:, 1] + nw / 2.0) * STEP - self.c
        cy = (ok[:, 0] + nh / 2.0) * STEP - self.c
        i = int(np.argmin((cx - target[0]) ** 2 + (cy - target[1]) ** 2))
        iy, ix = ok[i]
        self.free[iy:iy + nh, ix:ix + nw] = False
        return float(cx[i]), float(cy[i])


def _mark(reg_, cx, cy, w, h):
    nw, nh = int(round(w / STEP)), int(round(h / STEP))
    ix = int(round((cx + reg_.c) / STEP - nw / 2.0)); iy = int(round((cy + reg_.c) / STEP - nh / 2.0))
    reg_.free[max(iy, 0):iy + nh, max(ix, 0):ix + nw] = False


def place_through(reg_a, reg_b, w, h, target):
    """through-hole part: the block must be free on BOTH sides"""
    import copy
    tmp = copy.copy(reg_a)
    tmp.free = reg_a.free & reg_b.free
    pos = tmp.place(w, h, target)
    if pos:
        _mark(reg_a, pos[0], pos[1], w, h); _mark(reg_b, pos[0], pos[1], w, h)
    return pos


TAG_HOLES = [(-2.54, 0.0), (2.54, -1.016), (2.54, 1.016)]      # Tag-Connect TC2030-IDC-NL alignment holes (drilled through the board), rotation 0


def place_tag(reg_a, reg_b, w, h, target, hole_box=1.8):
    """Tag-Connect pads on side a; the three alignment holes must also be free (1.8 mm squares) on the other side b"""
    import copy
    tmp = copy.copy(reg_a)
    tmp.free = reg_a.free.copy()
    for _ in range(400):
        pos = tmp.place(w, h, target)                    # place() marks the block used in tmp
        if not pos:
            return None
        ok = True
        for hx, hy in TAG_HOLES:
            nb = int(round(hole_box / STEP))
            ix = int(round((pos[0] + hx + reg_b.c) / STEP - nb / 2.0)); iy = int(round((pos[1] + hy + reg_b.c) / STEP - nb / 2.0))
            if not reg_b.free[max(iy, 0):iy + nb, max(ix, 0):ix + nb].all():
                ok = False
        if ok:
            _mark(reg_a, pos[0], pos[1], w, h)
            for hx, hy in TAG_HOLES:
                _mark(reg_b, pos[0] + hx, pos[1] + hy, hole_box, hole_box)
            return pos
    return None


def affinity_translate(g, dx, dy):
    from shapely import affinity
    return affinity.translate(g, dx, dy)


def plan(a, D, quiet=True):
    sizes = {"H": a.hr, "M": a.min, "S": a.sec}
    cell = CELLS[a.cell]
    cell_c = []
    if cell:
        if a.cell_count == 2 and a.cell_layout == "side":
            cell_c = [(-(cell[1] / 2 + a.cell_gap / 2), a.cell_y), (cell[1] / 2 + a.cell_gap / 2, a.cell_y)]
        elif a.cell_count == 2:
            cell_c = [(0.0, a.cell_y - (cell[2] / 2 + a.cell_gap / 2)), (0.0, a.cell_y + (cell[2] / 2 + a.cell_gap / 2))]
        else:
            cell_c = [(0.0, a.cell_y)]
    free_min = (max(math.hypot(abs(cx_) + cell[1] / 2 + (CELL_PADS[cell[0]][3] if cell[0] in CELL_PADS else 0.0), abs(cy_) + cell[2] / 2) for cx_, cy_ in cell_c) + a.cell_clr) if cell else 0.0
    edge = a.edge_margin + a.safety
    sol = solve_rings(sizes, a.order.split(","), a.tang_gap, a.rad_gap, edge, D, free_min, a.band)
    if sol is None:
        return None
    D, radii, free_r = sol
    R = D / 2
    slot_clear = a.slot_clear if a.slot_clear else edge           # LED tip -> start of the strap slot (default = LED tip -> board edge)
    slot_gap = slot_clear - edge                                  # slot inner edge relative to the circle edge
    slot_off = slot_gap + a.slot_h / 2                            # slot centre beyond the circle edge
    lug_out = slot_gap + a.slot_h + a.lug_end                     # lug tip beyond the circle edge
    shape, slots = outline(D, a.lug_w, lug_out, a.lug_r, a.slot_w, a.slot_h, slot_off, a.slots)
    # LEDs
    leds = []
    for k in a.order.split(","):
        n = RINGS[k]
        for i in range(n):
            th = i * 360.0 / n
            leds.append(dict(ref=f"{k}{i if (k != 'H' or i) else 12}", fp="LED_SMD:" + SIZES[sizes[k]][0], x=radii[k] * math.sin(math.radians(th)), y=-radii[k] * math.cos(math.radians(th)),
                             rot=(90.0 - th) % 360.0, size=sizes[k], ring=k))
    # regions
    front_poly = Point(0, 0).buffer(free_r - a.part_clr - a.band_keepout, 128)
    cell_ext = CELL_PADS[cell[0]][3] if cell and cell[0] in CELL_PADS else 0.0
    cell_rects = [box(cx_ - cell[1] / 2 - cell_ext - a.cell_clr, cy_ - max(cell[2], CELL_PADS[cell[0]][2] if cell[0] in CELL_PADS else 0) / 2 - a.cell_clr, cx_ + cell[1] / 2 + cell_ext + a.cell_clr, cy_ + max(cell[2], CELL_PADS[cell[0]][2] if cell[0] in CELL_PADS else 0) / 2 + a.cell_clr) for cx_, cy_ in cell_c] if cell else []
    for cr_ in cell_rects:
        front_poly = front_poly.difference(cr_)
    batt = BATTS[a.battery]
    if a.batt_orient == "vertical" and not (len(batt) > 4 and batt[4] == "round"):
        batt = (batt[0], batt[2], batt[1], batt[3]) + tuple(batt[4:])      # long side along the strap axis
    back_poly = Point(0, 0).buffer(R - a.back_edge, 128)
    parts_circle = Point(0, 0).buffer((radii[a.order.split(",")[0]] - a.back_via_clr) if a.back_via_clr else (free_r - a.part_clr - a.band_keepout), 128)   # back parts only avoid the inner ring's through vias (hole 0.2 mm + pad)
    bx, by = 0.0, a.batt_y
    centres = [(bx, by)]
    if a.batt_count == 2 and not (len(batt) > 4 and batt[4] == "round"):
        # two cells, long side across the watch, pushed out toward the strap ends
        if a.batt_orient == "vertical":
            xb = math.sqrt(max(0.0, (R - a.back_edge) ** 2 - (batt[2] / 2) ** 2)) - batt[1] / 2 - 0.3
            if xb < batt[1] / 2 + a.batt_clr:
                return dict(ok=False, D=D, why="two cells do not fit")
            centres = [(-xb, 0.0), (xb, 0.0)]
            bx, by = -xb, 0.0
        else:
            yb = math.sqrt(max(0.0, (R - a.back_edge) ** 2 - (batt[1] / 2) ** 2)) - batt[2] / 2 - 0.3
            if yb < batt[2] / 2 + a.batt_clr:
                return dict(ok=False, D=D, why="two cells do not fit")
            centres = [(0.0, -yb), (0.0, yb)]
            by = -yb
    round_b = len(batt) > 4 and batt[4] == "round"
    batt_rect = Point(bx, by).buffer(batt[1] / 2, 64) if round_b else box(bx - batt[1] / 2, by - batt[2] / 2, bx + batt[1] / 2, by + batt[2] / 2)
    rects = [affinity_translate(batt_rect, cx_ - bx, cy_ - by) for cx_, cy_ in centres]
    if not all(r_.within(back_poly) for r_ in rects):
        return dict(ok=False, D=D, why="battery does not fit inside the board")
    for r_ in rects:
        back_poly = back_poly.difference(r_.buffer(a.batt_clr))
    for s in slots:
        back_poly = back_poly.difference(s.buffer(0.5)); front_poly = front_poly.difference(s.buffer(0.5))
    explicit = []                                                      # parts placed by rule instead of by the packer
    btn_fp = "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2"
    row_bottom = None
    if a.ind_style == "row" and a.ind_count and cell:
        ifp0 = "LED_SMD:LED_0201_0603Metric" if a.ind_size == "0201" else "LED_SMD:LED_0402_1005Metric"
        icy0 = courtyard(ifp0)
        ih0 = (icy0[3] - icy0[1]) if icy0 else 1.0
        row_y = max(cy_ for cx_, cy_ in cell_c) + cell[2] / 2 + a.cell_clr + 0.05 + ih0 / 2          # LED row tight under the cell
        row_bottom = row_y + ih0 / 2 + 0.35 + a.label_h + 0.2                                    # labels under the LEDs
    low_y = 8.0
    if a.btn_style == "bottom":
        by_ = courtyard(btn_fp)
        bw_, bh_ = (by_[2] - by_[0], by_[3] - by_[1]) if by_ else (5.69, 3.69)
        rr_ = free_r - a.part_clr
        yb_ = math.sqrt(max(0.0, rr_ ** 2 - (a.btn_x + bw_ / 2) ** 2)) - bh_ / 2
        if row_bottom is not None and yb_ - bh_ / 2 < row_bottom:
            return dict(ok=False, D=D, why="buttons do not fit below the indicator row")
        yb_ -= a.btn_up
        low_y = yb_
        for k_, sg in enumerate((-1, 1)):
            r_ = box(sg * a.btn_x - bw_ / 2, yb_ - bh_ / 2, sg * a.btn_x + bw_ / 2, yb_ + bh_ / 2)
            if any(r_.intersects(cr_) for cr_ in cell_rects):
                return dict(ok=False, D=D, why="buttons collide with the solar cell")
            front_poly = front_poly.difference(r_.buffer(a.pack_gap / 2))
            explicit.append(dict(ref=f"SW{k_ + 1}", value="SW_Push", fp=btn_fp, x=sg * a.btn_x, y=yb_, rot=0, side="front", w=bw_, h=bh_))
    if cell:                                                           # solar-cell contact pads (placeholder under each cell: + at one end, - at the other)
        for ci_, (cx_, cy_) in enumerate(cell_c):
            for sg_, nm_ in ((-1, "-"), (1, "+")):
                if cell[0] in CELL_PADS:      # real end pads (2.0 x 7.4 on the cell, 3.0 x 7.4 on the board so the outer 1 mm is an iron/solder access area)
                    pfp_, pw_, ph_, pext_ = CELL_PADS[cell[0]]
                    explicit.append(dict(ref=f"SC{ci_ + 1}{nm_}", value="cell pad", fp=pfp_, x=cx_ + sg_ * (cell[1] / 2 + pext_ - pw_ / 2), y=cy_, rot=0, side="front", w=pw_, h=ph_))
                else:
                    explicit.append(dict(ref=f"SC{ci_ + 1}{nm_}", value="cell pad", fp="TestPoint:TestPoint_Pad_D1.5mm", x=cx_ + sg_ * (cell[1] / 2 - 1.6), y=cy_, rot=0, side="front", w=1.5, h=1.5))
    labels = []
    if a.ind_style == "row" and a.ind_count and cell:
        ifp = "LED_SMD:LED_0201_0603Metric" if a.ind_size == "0201" else "LED_SMD:LED_0402_1005Metric"
        icy = courtyard(ifp)
        iw, ih = (icy[2] - icy[0], icy[3] - icy[1]) if icy else (1.9, 1.0)
        names = ["SET", "TMR", "BAT", "FUN", "CFG", "LCK", "X7", "X8", "X9"][:a.ind_count]
        n_ = a.ind_count
        free_circle = Point(0, 0).buffer(free_r - a.part_clr + 0.01, 128)
        for k_ in range(n_):
            x_ = (k_ - (n_ - 1) / 2) * a.ind_pitch
            box_ = box(x_ - iw / 2, row_y - ih / 2, x_ + iw / 2, row_y + ih / 2)
            if not free_circle.contains(box_) or not front_poly.buffer(0.02).contains(box_):
                return dict(ok=False, D=D, why="indicator row does not fit")
            front_poly = front_poly.difference(box_.buffer(a.pack_gap / 2))
            explicit.append(dict(ref=f"IND{k_ + 1}", value=names[k_], fp=ifp, x=x_, y=row_y, rot=0, side="front", w=iw, h=ih))
            ly_ = row_y + ih / 2 + 0.35 + a.label_h / 2
            labels.append(dict(text=names[k_], x=x_, y=ly_))
            lw_ = 0.75 * a.label_h * len(names[k_]) / 2 + 0.15
            front_poly = front_poly.difference(box(x_ - lw_, ly_ - a.label_h / 2 - 0.1, x_ + lw_, ly_ + a.label_h / 2 + 0.1))
    if a.ind_style == "arc" and a.ind_count:
        from shapely import affinity as _aff
        ifp = "LED_SMD:LED_0201_0603Metric" if a.ind_size == "0201" else "LED_SMD:LED_0402_1005Metric"
        icy = courtyard(ifp)
        iw, ih = (icy[2] - icy[0], icy[3] - icy[1]) if icy else (1.9, 1.0)
        names = ["SET", "TMR", "BAT", "FUN", "CFG", "LCK", "X7", "X8", "X9"][:a.ind_count]
        n_ = a.ind_count
        left_n = n_ // 2
        r_i = free_r - a.part_clr - a.ind_inset - max(iw, ih) / 2
        arcs = [-(a.ind_gap / 2 + (left_n - 1 - k_) * a.ind_pitch) for k_ in range(left_n)] + [(a.ind_gap / 2 + k_ * a.ind_pitch) for k_ in range(n_ - left_n)]
        free_circle = Point(0, 0).buffer(free_r - a.part_clr + 0.01, 128)
        for k_, sarc in enumerate(arcs):
            th_ = sarc / r_i
            if a.ind_side == "bottom":
                th_ = math.pi - th_                                  # mirrored to the bottom of the face, BAT stays on the left
            x_, y_ = r_i * math.sin(th_), -r_i * math.cos(th_)
            rot_ = (90.0 - math.degrees(th_)) % 360.0
            box_ = _aff.rotate(box(x_ - iw / 2, y_ - ih / 2, x_ + iw / 2, y_ + ih / 2), -rot_, origin=(x_, y_))
            if not free_circle.contains(box_) or any(box_.intersects(cr_) for cr_ in cell_rects) or not front_poly.buffer(0.02).contains(box_):
                return dict(ok=False, D=D, why="indicator arc does not fit")
            front_poly = front_poly.difference(box_.buffer(a.pack_gap / 2))
            explicit.append(dict(ref=f"IND{k_ + 1}", value=names[k_], fp=ifp, x=x_, y=y_, rot=rot_, side="front", w=iw, h=ih))
            labels.append(dict(text=names[k_], x=(r_i - ih / 2 - 1.3) * math.sin(th_), y=-(r_i - ih / 2 - 1.3) * math.cos(th_)))
            if k_ >= 1:
                pass
        amax = max(abs(a_) for a_ in arcs) / r_i + 0.12
        wedge = Polygon([(0, 0)] + [((r_i + 6) * math.sin(math.pi - t_ if a.ind_side == "bottom" else t_), -(r_i + 6) * math.cos(math.pi - t_ if a.ind_side == "bottom" else t_)) for t_ in np.linspace(-amax, amax, 24)])
        zone = wedge.intersection(Point(0, 0).buffer(r_i + max(iw, ih) / 2 + 0.7).difference(Point(0, 0).buffer(r_i - max(iw, ih) / 2 - 2.4)))
        front_poly = front_poly.difference(zone)
        for lb in labels:                                            # keep the labels clear of other parts
            front_poly = front_poly.difference(box(lb["x"] - 0.9 * len(lb["text"]) * 0.5 - 0.2, lb["y"] - 0.7, lb["x"] + 0.9 * len(lb["text"]) * 0.5 + 0.2, lb["y"] + 0.7))
    if a.batt_conn == "jst-side" and len(centres) == 2 and a.batt_orient == "horizontal":
        hf = "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal"
        hc = courtyard(hf)
        hw_, hh_ = (hc[2] - hc[0], hc[3] - hc[1]) if hc else (5.9, 6.7)
        rw_, rh_ = hh_, hw_                                          # rotated 90: opening along x
        for ci, (cx_, cy2) in enumerate(centres):
            x_ = a.plug_side * (batt[1] / 2 + a.batt_clr + rw_ / 2 + 0.2)
            yp_ = cy2 + (1 if cy2 < 0 else -1) * max(0.0, batt[2] / 2 - rh_ / 2)    # line the plug up with the cell's inner edge (toward the strip)
            r_ = box(x_ - rw_ / 2, yp_ - rh_ / 2, x_ + rw_ / 2, yp_ + rh_ / 2)
            if not r_.within(back_poly.intersection(parts_circle)):
                return dict(ok=False, D=D, why="battery plug does not fit beside the cell (inside the free circle)")
            back_poly = back_poly.difference(r_.buffer(a.pack_gap / 2))
            explicit.append(dict(ref="J1" if ci == 0 else "J1B", value="JST-SH", fp=hf, x=x_, y=yp_, rot=90 if a.plug_side > 0 else 270, side="back", w=hw_, h=hh_))
    if a.back_strip and len(centres) == 2 and a.batt_orient == "horizontal":
        half = abs(centres[0][1]) - batt[2] / 2 - a.batt_clr
        back_poly = back_poly.intersection(box(-R, -half, R, half))               # back parts only between the two cells
    back_poly = back_poly.intersection(parts_circle)                  # back parts stay inside the free circle (batteries are not parts: they may overlap the band)
    holes_poly = Point(0, 0).buffer(R - a.back_edge, 128).intersection(parts_circle)     # alignment holes may sit under a battery pouch (programmed with the pouches unplugged), not under a part
    reg = {"front": Region(front_poly, R), "back": Region(back_poly, R), "holes": Region(holes_poly, R)}        # "holes": back area that is neither under a pouch nor in the via band (alignment holes may land there)
    # parts
    variant = "solar" if cell else "usb"
    parts = []
    for ref, val, fpid in read_bom(variant, a.mcu_pkg):
        cl = classify(ref, fpid)
        if cl is None:
            continue
        if a.all_front and ref != "J1":
            cl = dict(cl, sides=["front"])
        if a.small_to_back and ref != "U1" and "SW_Push" not in fpid:
            cl = dict(cl, sides=["back", "front"])
        cy = courtyard(fpid)
        w = (cy[2] - cy[0]) if cy else 1.0
        h = (cy[3] - cy[1]) if cy else 1.0
        if (ref in ("SW1", "SW2") and a.btn_style == "bottom") or (ref == "J1" and a.batt_conn == "jst-side" and len(centres) == 2 and a.batt_orient == "horizontal"):
            continue
        if ref == "J1" and a.batt_conn == "jst" and len(centres) == 2 and a.batt_orient == "horizontal":
            for ci, (cx_, cy2) in enumerate(centres):
                top = cy2 < 0
                hx = (-1 if top else 1) * (batt[1] / 2 - 4.0)
                hy = cy2 + (1 if top else -1) * (batt[2] / 2 + a.batt_clr + 3.4)
                if a.plugs_outer:                                    # plugs at the two outer ends of the strip, opening outward; the chips and inductors sit between them
                    rc_ = radii[a.order.split(",")[0]] - a.back_via_clr
                    hx = (-1 if top else 1) * (math.sqrt(max(rc_ ** 2 - ((w + a.pack_gap) / 2) ** 2, 0.0)) - (h + a.pack_gap) / 2)
                parts.append(dict(ref="J1" if ci == 0 else "J1B", value=val, fp=fpid, w=w + a.pack_gap, h=h + a.pack_gap, cw=w, ch=h, prio=1, sides=["back"], near="point",
                                  tgt=(hx, hy), **({"rot_opts": ([] if a.plugs_outer else [(w + a.pack_gap, h + a.pack_gap, 0 if top else 180)]) + [(h + a.pack_gap, w + a.pack_gap, 90 if top else 270)]} if a.plug_rot_free else {"rot_force": 0 if top else 180})))
            continue
        if ref == "J1" and a.batt_conn == "solder":
            cy_ = courtyard("TestPoint:TestPoint_Pad_D1.5mm")
            pw, ph = (cy_[2] - cy_[0], cy_[3] - cy_[1]) if cy_ else (1.9, 1.9)
            for ci, (cx_, cy2) in enumerate(centres):
                tgt = (cx_, cy2 + (-1 if cy2 > 0 else 1) * (batt[2] / 2 + 1.6)) if len(centres) == 2 and a.batt_orient == "horizontal" else (cx_, cy2 - batt[2] / 2 - 1.6)
                for sign in ("+", "-"):
                    parts.append(dict(ref=f"BT{ci + 1}{sign}", value="wire pad", fp="TestPoint:TestPoint_Pad_D1.5mm", w=pw + a.pack_gap, h=ph + a.pack_gap, cw=pw, ch=ph,
                                      prio=1, sides=["back"], near="point", tgt=(tgt[0] + (-1.2 if sign == "+" else 1.2), tgt[1])))
            continue
        parts.append(dict(ref=ref, value=val, fp=fpid, w=w + a.pack_gap, h=h + a.pack_gap, cw=w, ch=h, **cl))
    placed, unplaced = list(explicit), []
    if a.indicators and a.ind_style != "arc":
        ic = courtyard("LED_SMD:LED_0402_1005Metric")
        iw, ih = (ic[2] - ic[0], ic[3] - ic[1]) if ic else (1.9, 1.0)
        for k_ in range(a.indicators):
            parts.append(dict(ref=f"IND{k_ + 1}", value="indicator LED", fp="LED_SMD:LED_0402_1005Metric", w=iw + a.pack_gap, h=ih + a.pack_gap, cw=iw, ch=ih, prio=2, sides=["front"], near="point",
                              tgt=((k_ - (a.indicators - 1) / 2) * 3.0, -(free_r - 3.5))))
    if a.res_style != "pack":
        rh = radii["H"]
        gap = [q for q in parts if re.fullmatch(r"R(\d|1[0-2])", q["ref"]) and 1 <= int(q["ref"][1:]) <= 12]
        parts = [q for q in parts if q not in gap]
        for q in gap:
            c = int(q["ref"][1:]) - 1                              # R1..R12 = series resistor of sector 0..11 (schematic)
            th = c * 30.0 + (a.res_angle if a.res_angle is not None else math.degrees(a.res_arc / rh))
            rot = (90.0 - c * 30.0 + (180.0 if a.res_flip else 0.0)) % 360.0 if a.res_style == "radial" else (-th) % 360.0      # parallel to the hour LED it serves (not turned with its own 5-degree offset)
            rr = rh if a.res_style == "radial" else rh
            rr = rh - (SIZES[sizes["H"]][1] / 2 - 0.78) if a.flush_inner else rh            # 0402 body is 1.56 long: inner end flush with the hour LED's inner pad edge
            placed.append(dict(ref=q["ref"], value=q["value"], fp=q["fp"], x=rr * math.sin(math.radians(th)), y=-rr * math.cos(math.radians(th)),
                               rot=rot, side="front", w=q["cw"], h=q["ch"]))
    if a.ring_caps:
        # caps parked in the hour ring OUTSIDE the flank parts, tangential (a compass-rose accent): "C53:12:L,C51:12:R" = ref : hour : side (L = counter-clockwise, R = clockwise)
        rh_ = radii["H"]
        ra_ = a.res_angle if a.res_angle is not None else -5.0
        r_cap = rh_ - (SIZES[sizes["H"]][1] / 2 - 0.47) if a.flush_inner else rh_
        step_ = math.degrees((0.45 + 0.2 + 0.93) / r_cap)                    # resistor half width + gap + cap half length, as an angle
        for item in a.ring_caps.split(","):
            ref_, hour_, side_ = item.split(":")
            q_ = next((q for q in parts if q["ref"] == ref_), None)
            if q_ is None:
                continue
            c_ = int(hour_) % 12
            th_ = c_ * 30.0 + (ra_ - step_ if side_ == "L" else -ra_ + step_)
            placed.append(dict(ref=ref_, value=q_["value"], fp=q_["fp"], x=r_cap * math.sin(math.radians(th_)), y=-r_cap * math.cos(math.radians(th_)),
                               rot=(-th_) % 360.0, side="front", w=q_["cw"], h=q_["ch"]))
            parts = [q for q in parts if q["ref"] != ref_]
    if a.flank_parts:
        # small 0402 parts mirrored across each hour LED from its series resistor: "R50:3,R52:2" = ref : hour LED (hour number, 12 = top)
        rh = radii["H"]
        rr_ = rh - (SIZES[sizes["H"]][1] / 2 - 0.78) if a.flush_inner else rh
        ra_ = a.res_angle if a.res_angle is not None else -5.0
        for item in a.flank_parts.split(","):
            ref_, hour_ = item.split(":")
            q_ = next((q for q in parts if q["ref"] == ref_), None)
            if q_ is None:
                continue
            c_ = int(hour_) % 12
            th_ = c_ * 30.0 - ra_                                   # the mirror image of the series resistor (which sits at c*30 + res_angle)
            placed.append(dict(ref=ref_, value=q_["value"], fp=q_["fp"], x=rr_ * math.sin(math.radians(th_)), y=-rr_ * math.cos(math.radians(th_)),
                               rot=(90.0 - c_ * 30.0 + (180.0 if a.res_flip else 0.0)) % 360.0, side="front", w=q_["cw"], h=q_["ch"]))
            parts = [q for q in parts if q["ref"] != ref_]
    parts.sort(key=lambda p: (0.5 + 0.01 * ("C20", "C21").count(p["ref"]) if ((a.xtal_below or a.xtal_side == "right") and p["ref"] in ("Y1", "C20", "C21")) else p["prio"], -(p["w"] * p["h"])))
    mcu_at = {}
    xt = {}
    top_x = {}
    low_x = {}
    if a.low_parts:
        lp_ = [q for r_ in a.low_parts.split(",") for q in parts if q["ref"] == r_]
        tot_ = sum(q["w"] for q in lp_) + 0.3 * (len(lp_) - 1)
        x_ = -tot_ / 2
        for q in lp_:
            low_x[q["ref"]] = x_ + q["w"] / 2
            x_ += q["w"] + 0.3
        parts = [dict(q, prio=0.7) if q["ref"] in low_x else q for q in parts]
    cell_top_y = (min(cy_ for cx_, cy_ in cell_c) - cell[2] / 2 - a.cell_clr) if cell else -4.0
    if a.top_parts:
        tp_ = [q for r_ in a.top_parts.split(",") for q in parts if q["ref"] == r_]
        tot_ = sum(q["w"] for q in tp_) + 0.3 * (len(tp_) - 1)
        x_ = -tot_ / 2
        for q in tp_:
            top_x[q["ref"]] = x_ + q["w"] / 2
            x_ += q["w"] + 0.3
        parts = [dict(q, prio=0.45) if q["ref"] in top_x else q for q in parts]
        parts.sort(key=lambda p: (0.5 + 0.01 * ("C20", "C21").count(p["ref"]) if ((a.xtal_below or a.xtal_side == "right") and p["ref"] in ("Y1", "C20", "C21")) else p["prio"], -(p["w"] * p["h"])))
    halo_box = None
    back_set = set(a.back_parts.split(",")) if a.back_parts else set()
    below_map = dict(x.split(":") for x in a.below.split(",")) if a.below else {}
    beside_map = {x.split(":")[0]: (x.split(":")[1], x.split(":")[2]) for x in a.beside.split(",")} if a.beside else {}
    for p in parts:
        done = False
        sides = list(p["sides"])
        if p["ref"] in back_set:
            sides = ["back"]
        if p["ref"] in beside_map:                               # parked right beside another (already placed) part: "C30:U2:L"
            bref_, bside_ = beside_map[p["ref"]]
            base_ = next((q for q in placed if q["ref"] == bref_), None)
            if base_ is not None:
                p = dict(p, near="point", tgt=(base_["x"] + (-1 if bside_ == "L" else 1) * (base_["w"] / 2 + 0.3 + p["w"] / 2), base_["y"]), sides=[base_["side"]])
                sides = [base_["side"]]
        if p["ref"] in below_map:                                # parked directly below another (already placed) part on the same side, e.g. C30 below L2 on the back
            base_ = next((q for q in placed if q["ref"] == below_map[p["ref"]]), None)
            if base_ is not None:
                p = dict(p, near="point", tgt=(base_["x"], base_["y"] + base_["h"] / 2 + p["h"] / 2 + 0.1), sides=[base_["side"]])
                sides = [base_["side"]]
        if halo_box is not None and p["ref"] not in ("U1", "Y1", "C20", "C21", "J2") and p["ref"] not in a.close_parts.split(",") and p["ref"] not in top_x:
            _mark(reg["front"], *halo_box)
            if os.environ.get("PLAN_DEBUG"):
                print("halo applied before", p["ref"], p["prio"], "placed so far:", [q["ref"] for q in placed][-12:])
            halo_box = None
        if p["ref"] == "U1" and a.mcu_side != "auto":
            sides = [a.mcu_side]
        if p["ref"] == "U1" and a.mcu_rot:
            p = dict(p, rot_force=a.mcu_rot)
        if p["ref"] == "U1" and a.mcu_target:
            tx_, ty_ = (float(v) for v in a.mcu_target.split(","))
            p = dict(p, near="point", tgt=(tx_, ty_), rot_force=a.mcu_rot)
        if p["ref"] in ("C20", "C21") and xt.get(p["ref"]):
            continue
        if a.above_mcu and p["ref"] in a.above_mcu.split(",") and mcu_at.get("front"):      # supply decoupling: a tight row right above the MCU's top edge, placed exactly (inside the 0.25 mm part margin if need be)
            ux, uy = mcu_at["front"]
            uh_ = next(q["h"] for q in placed if q["ref"] == "U1")
            k_ = a.above_mcu.split(",").index(p["ref"])
            n_ = len(a.above_mcu.split(","))
            x_c = ux + (k_ - (n_ - 1) / 2) * a.above_pitch
            y_c = uy - uh_ / 2 - 0.55 - 0.47
            placed.append(dict(ref=p["ref"], value=p["value"], fp=p["fp"], x=x_c, y=y_c, rot=0, side="front", w=p["cw"], h=p["ch"]))
            _mark(reg["front"], x_c, y_c, 1.9, 0.95)
            continue
        if a.tag_gap and p["ref"] in ("J2", "C54") and mcu_at.get("front"):
            ux, uy = mcu_at["front"]
            uw_ = next(q["w"] for q in placed if q["ref"] == "U1")
            if p["ref"] == "J2":
                p = dict(p, near="point", tgt=(ux - uw_ / 2 - a.tag_gap - p["w"] / 2, uy + 1.0), sides=["front"])
                xt["J2"] = p["tgt"]
            else:
                jx_, jy_ = xt.get("J2", (ux - 8.0, uy + 1.0))
                p = dict(p, near="point", tgt=(jx_, jy_ - 2.4 - a.tag_gap - p["h"] / 2), sides=["front"])
        if p["ref"] in low_x:                                   # parked BETWEEN the buttons, below the cell
            p = dict(p, near="point", tgt=(low_x[p["ref"]], low_y), sides=["front"])
        if p["ref"] in top_x:                                   # parked ABOVE the solar cell (between the cell and the indicator arc)
            p = dict(p, near="point", tgt=(top_x[p["ref"]], cell_top_y - p["h"] / 2 - 0.1), sides=["front"])
        if a.xtal_side == "right" and p["ref"] in ("Y1", "C20", "C21") and mcu_at.get("front"):
            ux, uy = mcu_at["front"]
            if p["ref"] == "Y1":                                 # crystal stands upright just right of the MCU's PF0/PF1 pins (MCU rotation 0)
                p = dict(p, near="point", w=p["h"], h=p["w"], tgt=(ux + 5.3 + a.xtal_gap, uy + 0.3), rot_force=270)
                sides = ["front"]
            else:
                continue                                         # the caps are placed exactly once the crystal is down
        if a.xtal_below and a.xtal_side == "below" and p["ref"] in ("Y1", "C20", "C21") and mcu_at.get("front"):
            ux, uy = mcu_at["front"]
            uh = next(q["h"] for q in placed if q["ref"] == "U1")
            xdx = 1.6 if a.mcu_rot == 270 else 0.0           # with the MCU turned 270 degrees the 32 kHz pins (PF0/PF1) face the crystal at x = +1.4 / +1.8
            if p["ref"] == "Y1":
                p = dict(p, near="point", tgt=(ux + xdx, uy + uh / 2 + 0.2 + p["h"] / 2), rot_force=a.xtal_rot)
                sides = ["front"]
            elif "Y1" in xt:
                yx, yy, yw, yh = xt["Y1"]
                # load caps straight below the crystal pads (like the first hand-built revision), turned 90 degrees: signal pad up, ground pad down
                p = dict(p, near="point", w=p["h"], h=p["w"], tgt=(yx + (-1 if p["ref"] == "C20" else 1) * (yw / 2 - 0.55), yy + yh / 2 + 0.25 + p["w"] / 2), rot_force=90)
                sides = ["front"]
        for side in sides:
            if p["near"] == "point":
                target = p["tgt"]
            elif p["near"] == "battery":
                target = (bx + batt[1] / 2 + 3, by) if side == "back" else (0, 0)
            elif p["near"] == "edge":
                target = (0, -R) if side == "front" else (0, R)
            elif p["near"] == "mcu" and mcu_at.get(side):
                target = mcu_at[side]
            else:
                target = (0, 0)
            for (ww, hh, rot) in (p["rot_opts"] if "rot_opts" in p else ((p["w"], p["h"], p["rot_force"]),) if "rot_force" in p else ((p["w"], p["h"], 0), (p["h"], p["w"], 90))):
                if "Tag-Connect" in p["fp"]:                                  # alignment holes drill through the board: only the three hole squares must be free on the other side
                    pos = place_tag(reg[side], reg["holes"] if side == "front" else reg["front"], ww, hh, target) if rot == 0 else None
                    if pos:
                        for hx, hy in TAG_HOLES:                       # keep other parts off the hole squares on the other face
                            _mark(reg["back" if side == "front" else "front"], pos[0] + hx, pos[1] + hy, 1.8, 1.8)
                elif "PinHeader" in p["fp"] and "SMD" not in p["fp"]:
                    pos = place_through(reg[side], reg["front" if side == "back" else "back"], ww, hh, target)
                else:
                    pos = reg[side].place(ww, hh, target)
                if pos:
                    placed.append(dict(ref=p["ref"], value=p["value"], fp=p["fp"], x=pos[0], y=pos[1], rot=rot, side=side, w=p["cw"], h=p["ch"]))
                    if p["ref"] == "U1":
                        mcu_at[side] = pos
                        if a.mcu_halo and side == "front":                   # remembered: applied just before the first ordinary part (the pads and the crystal stay snug, the small parts keep away)
                            halo_box = (pos[0], pos[1], p["w"] + 2 * a.mcu_halo, p["h"] + 2 * a.mcu_halo)
                    if p["ref"] == "Y1":
                        xt["Y1"] = (pos[0], pos[1], p["w"], p["h"])
                        if a.xtal_side == "right":
                            yx_, yy_ = pos[0], pos[1]
                            for ref_, dy_ in (("C20", 1.25), ("C21", -1.25)):          # C20 (XTAL1) at the lower crystal pad, C21 (XTAL2) at the upper
                                q_ = next((q for q in parts if q["ref"] == ref_), None)
                                if q_ is None:
                                    continue
                                blk = (yx_ + 2.55, yy_ + dy_)
                                nw_, nh_ = int(round(2.5 / STEP)), int(round(1.1 / STEP))
                                ix_ = int(round((blk[0] + reg["front"].c) / STEP - nw_ / 2.0)); iy_ = int(round((blk[1] + reg["front"].c) / STEP - nh_ / 2.0))
                                if reg["front"].free[max(iy_, 0):iy_ + nh_, max(ix_, 0):ix_ + nw_].all():
                                    _mark(reg["front"], blk[0], blk[1], 2.5, 1.1)
                                    placed.append(dict(ref=ref_, value=q_["value"], fp=q_["fp"], x=yx_ + 2.06, y=yy_ + dy_, rot=0, side="front", w=q_["cw"], h=q_["ch"]))
                                    xt[ref_] = True
                                else:
                                    print("note: no room for", ref_, "right of the crystal", "block", [round(v, 2) for v in blk], "free cells", int(reg["front"].free[max(iy_, 0):iy_ + nh_, max(ix_, 0):ix_ + nw_].sum()), "of", nw_ * nh_)
                            _mark(reg["front"], yx_ + 1.5, yy_, 5.4, 5.7)        # the grounded guard area around the crystal circuit: no other part may sit in it (datasheet DS40002247B 4.5.1)
                        # load caps exactly under the crystal pads (signal pad up, ground pad down), ground via beside each cap: reserve the block
                        yx_, yy_ = pos[0], pos[1]
                        for ref_, sgn_ in ((("C20", -1), ("C21", 1)) if a.xtal_side == "below" else ()):
                            q_ = next((q for q in parts if q["ref"] == ref_), None)
                            if q_ is None:
                                continue
                            cx_, cy_ = yx_ + sgn_ * 1.25, yy_ + 2.15
                            nb_w, nb_h = (1.7, 1.7) if sgn_ < 0 else (1.25, 1.7)           # ground via sits on the INNER side of each cap (between the two caps)
                            blk = ((cx_ + 0.2) if sgn_ < 0 else (cx_ - 0.35), yy_ + 2.1)
                            nw_, nh_ = int(round(nb_w / STEP)), int(round(nb_h / STEP))
                            ix_ = int(round((blk[0] + reg["front"].c) / STEP - nw_ / 2.0)); iy_ = int(round((blk[1] + reg["front"].c) / STEP - nh_ / 2.0))
                            if reg["front"].free[max(iy_, 0):iy_ + nh_, max(ix_, 0):ix_ + nw_].all():
                                _mark(reg["front"], blk[0], blk[1], nb_w, nb_h)
                                placed.append(dict(ref=ref_, value=q_["value"], fp=q_["fp"], x=cx_, y=cy_, rot=a.xtal_cap_rot, side="front", w=q_["cw"], h=q_["ch"]))
                                xt[ref_] = True
                            else:
                                print("note: no room for", ref_, "directly under the crystal; the packer will place it")
                    done = True
                    break
            if done:
                break
        if not done:
            unplaced.append(p["ref"])
    if a.align_x:                                          # "C54:J2": same x as another part (neat stacks)
        for item_ in a.align_x.split(","):
            r1_, r2_ = item_.split(":")
            q2_ = next((q for q in placed if q["ref"] == r2_), None)
            for q1_ in placed:
                if q1_["ref"] == r1_ and q2_ is not None:
                    q1_["x"] = q2_["x"]
    if a.nudge:                                            # explicit hand-tuning: "J2:0:-0.4,SW1:0.3:-0.4" = ref:dx:dy (mm, y down), applied after packing
        for item_ in a.nudge.split(","):
            r_, dx_, dy_ = item_.split(":")
            for q_ in placed:
                if q_["ref"] == r_:
                    q_["x"] += float(dx_); q_["y"] += float(dy_)
    if a.xtal_side == "right" and "Y1" in xt:
        ux_, uy_ = mcu_at.get("front", (0, 0))
        yx_, yy_, _, _ = xt["Y1"]
        if abs(yx_ - ux_ - 5.3 - a.xtal_gap) > 1.0 or abs(yy_ - uy_ - 0.3) > 1.0 or not (xt.get("C20") and xt.get("C21")):
            unplaced.append("crystal block (Y1/C20/C21 not right of the MCU)")
    if a.xtal_below and a.xtal_side == "below" and "Y1" in xt:                       # the crystal block must really sit directly under the MCU pins (a far-away packer fallback is a failure)
        ux_, uy_ = mcu_at.get("front", (0, 0))
        yx_, yy_, _, _ = xt["Y1"]
        if abs(yx_ - ux_ - (1.6 if a.mcu_rot == 270 else 0.0)) > 0.6 or not (0.0 < yy_ - uy_ < 7.0) or not (xt.get("C20") and xt.get("C21")):
            unplaced.append("crystal block (Y1/C20/C21 not directly under the MCU)")
    from shapely import affinity
    solid = shape
    for sl in slots:
        solid = solid.difference(sl)
    bad = []
    for L in leds:
        ln, wd = SIZES[L["size"]][1], SIZES[L["size"]][2]
        rect_ = affinity.rotate(box(L["x"] - ln / 2, L["y"] - wd / 2, L["x"] + ln / 2, L["y"] + wd / 2), -L["rot"], origin=(L["x"], L["y"]))
        if not solid.buffer(-0.3).contains(rect_):
            bad.append(L["ref"])
    return dict(ok=not unplaced and not bad, led_outside=bad, unplaced=unplaced, D=D, R=R, band=R - free_r, free_r=free_r, radii=radii, leds=leds, parts=placed,
                outline=list(shape.exterior.coords), slots=[list(s.exterior.coords) for s in slots],
                cell=dict(name=cell[0], w=cell[1], h=cell[2], t=cell[3], x=cell_c[0][0], y=cell_c[0][1]) if cell else None,
                cells=[dict(x=c_[0], y=c_[1]) for c_ in cell_c], labels=labels,
                battery=dict(name=batt[0], w=batt[1], h=batt[2], t=batt[3], x=centres[0][0], y=centres[0][1], round=round_b),
                batteries=[dict(x=c_[0], y=c_[1]) for c_ in centres],
                front_used=100 * (1 - reg["front"].free.sum() / max(1, shapely.contains_xy(front_poly, reg["front"].X, reg["front"].Y).sum())),
                back_used=100 * (1 - reg["back"].free.sum() / max(1, shapely.contains_xy(back_poly, reg["back"].X, reg["back"].Y).sum())),
                sizes=sizes, args={k: v for k, v in vars(a).items()})


def search(a):
    if a.auto_cell_y and CELLS[a.cell]:
        best = None
        for cy in [0.0] + [v * sgn for v in np.arange(0.5, 14.01, 0.5) for sgn in (1, -1)]:
            a.cell_y = float(cy)
            r = plan(a, a.diameter) if a.diameter else None
            if r and r.get("ok"):
                if best is None or abs(cy) < abs(best["cell"]["y"]):
                    best = r
                    break
        if best:
            return best
        a.cell_y = 0.0
    if a.diameter:
        return plan(a, a.diameter)
    D = 20.0
    last = None
    while D < 80:
        r = plan(a, 0 if D == 20.0 else D) if False else None
        # smallest ring-feasible diameter first, then step up until every part is placed
        sizes = {"H": a.hr, "M": a.min, "S": a.sec}
        cell = CELLS[a.cell]
        free_min = (math.hypot(cell[1] / 2 + (CELL_PADS[cell[0]][3] if cell[0] in CELL_PADS else 0.0), cell[2] / 2) + a.cell_clr) if cell else 0.0
        sol = solve_rings(sizes, a.order.split(","), a.tang_gap, a.rad_gap, a.edge_margin + a.safety, 0, free_min, a.band)
        D0 = sol[0]
        break
    D = math.ceil(D0 * 2) / 2
    while D < 80:
        r = plan(a, D)
        if r and r["ok"]:
            return r
        last = r
        D += 0.5
    return last


# ------------------------------------------------------------------ drawing
def draw(p, path, title=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Rectangle, Circle
    from matplotlib.transforms import Affine2D
    col = {"H": "#d94841", "M": "#e8a317", "S": "#2b7bd6"}
    fig, axs = plt.subplots(1, 2, figsize=(15, 8.4))
    for ax, side in zip(axs, ("front", "back")):
        sx = 1 if side == "front" else -1          # back is shown as if the watch were flipped left-to-right
        ax.add_patch(MP([(sx * x, y) for x, y in p["outline"]], closed=True, fc="#1f2a44", ec="#cfd8ea", lw=1.4))
        for s in p["slots"]:
            ax.add_patch(MP([(sx * x, y) for x, y in s], closed=True, fc="white", ec="#cfd8ea", lw=1))
        ax.add_patch(Circle((0, 0), p["free_r"], fill=False, ec="#6c7fa8", lw=0.8, ls="--"))
        if side == "front":
            for L in p["leds"]:
                _, ln, wd = SIZES[L["size"]]
                t = Affine2D().rotate_deg(-L["rot"]).translate(L["x"], L["y"])      # y axis is flipped below, so rotate the other way
                r = Rectangle((-ln / 2, -wd / 2), ln, wd, fc=col[L["ring"]], ec="none")
                r.set_transform(t + ax.transData); ax.add_patch(r)
            if p["cell"]:
                c = p["cell"]
                cl_ = p.get("cells", [dict(x=0.0, y=c["y"])])
                for cc in cl_:
                    ax.add_patch(Rectangle((cc["x"] - c["w"] / 2, cc["y"] - c["h"] / 2), c["w"], c["h"], fc="#3b3b3b", ec="#f4c542", lw=1.6, hatch="////", alpha=0.9))
                ax.text(sum(cc["x"] for cc in cl_) / len(cl_), sum(cc["y"] for cc in cl_) / len(cl_) + (c["h"] / 2 + 0.2 if len(cl_) == 2 and cl_[0]["x"] != cl_[1]["x"] else 0), f'solar cell\n{c["name"]}\n{c["w"]:g} x {c["h"]:g} mm', ha="center", va="center", color="white", fontsize=9)
            else:
                ax.text(0, 0, "free centre\n(no solar cell)", ha="center", va="center", color="#8fa1c7", fontsize=9)
        else:
            b = p["battery"]
            for bc in p.get("batteries", [dict(x=b["x"], y=b["y"])]):
                ax.add_patch(Rectangle((sx * bc["x"] - b["w"] / 2 - 1.0, bc["y"] - b["h"] / 2 - 1.0), b["w"] + 2.0, b["h"] + 2.0, fill=False, ec="#f4c542", lw=1.0, ls="--") if not b.get("round") else Circle((sx * bc["x"], bc["y"]), b["w"] / 2 + 1.0, fill=False, ec="#f4c542", lw=1.0, ls="--"))
                ax.add_patch(Circle((sx * bc["x"], bc["y"]), b["w"] / 2, fc="#2e7d4f", ec="#9be3b7", lw=1.4, alpha=0.9) if b.get("round") else Rectangle((sx * bc["x"] - b["w"] / 2, bc["y"] - b["h"] / 2), b["w"], b["h"], fc="#2e7d4f", ec="#9be3b7", lw=1.4, alpha=0.9))
                ax.text(sx * bc["x"], bc["y"], f'LiPo {b["name"]}\n{b["w"]:g} x {b["h"]:g} x {b["t"]:g} mm', ha="center", va="center", color="white", fontsize=7.5)
        for q in p["parts"]:
            if q["side"] != side:
                continue
            w, h = (q["w"], q["h"]) if q["rot"] in (0, 90) and q["rot"] == 0 else ((q["h"], q["w"]) if q["rot"] == 90 else (q["w"], q["h"]))
            big = max(w, h) > 3.2
            fc = "#ffe600" if q["ref"].startswith("IND") else "#c9a227" if q["ref"] == "U1" else ("#9b59b6" if q["ref"][0] == "U" else ("#16a085" if q["ref"][0] in "SJ" or q["ref"] == "Y1" else "#b0b7c3"))
            if q["ref"] in ("J1", "J1B"):
                th_ = math.radians(q["rot"]); dx_, dy_ = -math.sin(th_), -math.cos(th_)        # opening direction on the back side (verified against the generated KiCad pads)
                ax.annotate("", xy=(sx * (q["x"] + 3.2 * dx_), q["y"] + 3.2 * dy_), xytext=(sx * q["x"], q["y"]), arrowprops=dict(arrowstyle="-|>", color="white", lw=1.4))
            if q["rot"] in (0, 90):
                ax.add_patch(Rectangle((sx * q["x"] - w / 2, q["y"] - h / 2), w, h, fc=fc, ec="black", lw=0.6, alpha=0.95))
            else:
                rr_ = Rectangle((-w / 2, -h / 2), w, h, fc=fc, ec="black", lw=0.6, alpha=0.95)
                rr_.set_transform(Affine2D().rotate_deg(-q["rot"] * sx).translate(sx * q["x"], q["y"]) + ax.transData); ax.add_patch(rr_)
            if big:
                ax.text(sx * q["x"], q["y"], q["ref"], ha="center", va="center", fontsize=7.5, color="black")
        if side == "front":
            for lb in p.get("labels", []):
                ax.text(lb["x"], lb["y"], lb["text"], ha="center", va="center", fontsize=5.5, color="#e8eefc")
        ax.set_aspect("equal"); ax.invert_yaxis()
        ext = max(y for _, y in p["outline"]) + 2
        ax.set_xlim(-p["R"] - 4, p["R"] + 4); ax.set_ylim(ext, -ext)
        ax.set_title("FRONT (face)" if side == "front" else "BACK (against the wrist side; battery here)", fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
    ps = {q["ref"]: q["side"] for q in p["parts"]}
    mcu = ps.get("U1", "?")
    fig.suptitle(title or f'{(str(len(p.get("cells", [1]))) + " x " if p["cell"] and len(p.get("cells", [1])) > 1 else "") + p["cell"]["name"] if p["cell"] else "no solar cell"}  |  board {p["D"]:.1f} mm  |  LED band {p["band"]:.2f} mm  |  free centre {2 * p["free_r"]:.1f} mm  |  '
                 f'MCU on {mcu}  |  {len(p.get("batteries", [1]))} x {p["battery"]["name"]}' + (f'  |  cell shifted {p["cell"]["y"]:+.1f} mm' if p["cell"] and abs(p["cell"]["y"]) > 0.01 else ''), fontsize=12)
    fig.text(0.5, 0.045, "yellow dashes on the back = 1 mm shield / foam-tape zone around each cell", ha="center", fontsize=8.5)
    fig.text(0.5, 0.02, "red = hour LEDs (largest, inner)   amber = minute LEDs   blue = second LEDs (smallest, outer)   purple = ICs   gold = MCU   green = connectors / crystal / buttons   grey = passives   yellow = indicator LEDs   "
                        "(courtyards drawn to scale; not routed)", ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", default="KXOB25", choices=list(CELLS))
    ap.add_argument("--battery", default="80", choices=list(BATTS))
    ap.add_argument("--diameter", type=float, default=0.0, help="board diameter mm (0 = smallest board where everything fits)")
    ap.add_argument("--band", type=float, default=0.0, help="width of the LED band mm (0 = tightest)")
    ap.add_argument("--hr", default="0603"); ap.add_argument("--min", default="0402"); ap.add_argument("--sec", default="0201")
    ap.add_argument("--order", default="H,M,S")
    ap.add_argument("--tang-gap", type=float, default=0.5); ap.add_argument("--rad-gap", type=float, default=0.8); ap.add_argument("--edge-margin", type=float, default=1.0)
    ap.add_argument("--cell-clr", type=float, default=0.3); ap.add_argument("--part-clr", type=float, default=0.3)
    ap.add_argument("--back-edge", type=float, default=1.0); ap.add_argument("--batt-clr", type=float, default=0.5); ap.add_argument("--batt-y", type=float, default=0.0); ap.add_argument("--batt-orient", default="horizontal", choices=["horizontal", "vertical"], help="vertical = long side of each cell along the strap axis")
    ap.add_argument("--batt-conn", default="jst", choices=["jst", "solder", "jst-side"], help="battery connection: JST-SH header or wires soldered to pads")
    ap.add_argument("--ind-style", default="pack", choices=["pack", "arc", "row"], help="arc = one indicator LED per mode on an arc above the centre, silkscreen labels"); ap.add_argument("--ind-count", type=int, default=6)
    ap.add_argument("--ind-size", default="0402", choices=["0402", "0201"]); ap.add_argument("--ind-pitch", type=float, default=3.6); ap.add_argument("--ind-gap", type=float, default=4.0); ap.add_argument("--ind-inset", type=float, default=0.8)
    ap.add_argument("--all-front", action="store_true", help="every part except the battery plugs on the front (one-sided SMT assembly)")
    ap.add_argument("--band-keepout", type=float, default=0.0, help="extra radial margin (mm) between the free circle and any part, front and back (room for polar vias)")
    ap.add_argument("--res-angle", type=float, default=None, help="series resistors: angle in degrees from the hour LED (negative = counter-clockwise) instead of --res-arc")
    ap.add_argument("--res-flip", action="store_true", help="series resistors: pad 1 (LED side) outward")
    ap.add_argument("--back-via-clr", type=float, default=0.0, help="back-side parts may reach out to (inner LED ring radius - this) mm, since only the inner ring's vias are there; 0 = old rule (free circle)")
    ap.add_argument("--plug-rot-free", action="store_true", help="battery plugs may turn 90 degrees (opening sideways) so they fit a narrow strip between the pouches")
    ap.add_argument("--xtal-below", action="store_true", help="32 kHz crystal directly below the MCU with its two load caps on either side (as in the first hand-built revision)")
    ap.add_argument("--mcu-rot", type=float, default=0.0, help="MCU rotation in degrees (270 = the 32 kHz pins face the bottom, toward the crystal)")
    ap.add_argument("--xtal-rot", type=float, default=180.0, help="crystal rotation (180 puts pad 1 = XTAL1 on the left)")
    ap.add_argument("--xtal-cap-rot", type=float, default=90.0, help="rotation of the crystal load caps (90 or 270, whichever puts the signal pad up)")
    ap.add_argument("--flank-parts", default="", help="park 0402 parts mirrored across an hour LED from its series resistor: ref:hour,ref:hour,...")
    ap.add_argument("--flush-inner", action="store_true", help="series resistors and flank parts: inner end flush with the hour LED inner edge (not centred)")
    ap.add_argument("--band-parts", default="", help="park small passives in the hour-ring gaps, e.g. \"R50,R51,R52,R53:3;R54,R55,R56:4;R20,R21:6\" (refs : hour sector, placed counter-clockwise of that sector's series resistor)")
    ap.add_argument("--top-parts", default="", help="comma list of refs parked above the solar cell, e.g. J2,L2,C54")
    ap.add_argument("--ind-side", default="top", choices=["top", "bottom"], help="mode-indicator arc at the top (default) or the bottom of the face")
    ap.add_argument("--mcu-target", default="", help="x,y: place the MCU nearest to this point (mm from the centre)")
    ap.add_argument("--xtal-side", default="below", choices=["below", "right"], help="32 kHz crystal group below the MCU (default) or standing upright to its right (needs --mcu-rot 0)")
    ap.add_argument("--low-parts", default="", help="comma list of refs parked between the buttons below the cell, e.g. U2,L2,C54")
    ap.add_argument("--mcu-halo", type=float, default=0.0, help="extra clear space (mm) kept around the MCU courtyard for escape vias")
    ap.add_argument("--xtal-gap", type=float, default=0.0, help="--xtal-side right: move the crystal group this far further from the MCU (mm)")
    ap.add_argument("--label-h", type=float, default=1.0, help="mode-LED label silk text height (mm); JLCPCB lists 1.0 mm as the minimum legible")
    ap.add_argument("--label-w", type=float, default=0.15, help="mode-LED label silk stroke width (mm); JLCPCB lists 0.15 mm as the minimum")
    ap.add_argument("--ring-caps", default="", help="caps parked tangentially in the hour ring outside the flank parts: ref:hour:L|R,...")
    ap.add_argument("--plugs-outer", action="store_true", help="battery plugs at the two outer ends of the back strip, opening outward")
    ap.add_argument("--back-parts", default="", help="comma list of refs forced onto the back (e.g. C31)")
    ap.add_argument("--below", default="", help="ref:base,ref:base - park a part directly below an already placed part (e.g. C30:L2)")
    ap.add_argument("--tag-gap", type=float, default=0.0, help="clear space (mm) between the MCU and the Tag-Connect pads / C54 on its left")
    ap.add_argument("--close-parts", default="", help="refs that stay right at the MCU (exempt from the late halo), e.g. the supply-pin decoupling caps")
    ap.add_argument("--above-mcu", default="", help="refs placed in a row just above the MCU top edge (supply decoupling)")
    ap.add_argument("--beside", default="", help="ref:base:L|R - park a part right beside an already placed part (e.g. C30:U2:L)")
    ap.add_argument("--btn-up", type=float, default=0.0, help="raise the two low buttons (and U2 between them) by this many mm")
    ap.add_argument("--above-pitch", type=float, default=1.95, help="centre spacing (mm) of the caps in the row above the MCU")
    ap.add_argument("--nudge", default="", help="ref:dx:dy,... shift placed parts by hand after packing (mm, y down)")
    ap.add_argument("--align-x", default="", help="ref:base,... give ref the same x as base")
    ap.add_argument("--cell-count", type=int, default=1, choices=[1, 2]); ap.add_argument("--cell-layout", default="side", choices=["side", "stack"]); ap.add_argument("--cell-gap", type=float, default=0.8)
    ap.add_argument("--btn-style", default="pack", choices=["pack", "bottom"], help="bottom = two buttons symmetric about the centre line, low on the face"); ap.add_argument("--btn-x", type=float, default=7.0)
    ap.add_argument("--indicators", type=int, default=0, help="extra indicator LEDs (0402) near the top of the face")
    ap.add_argument("--plug-side", type=int, default=1, choices=[1, -1], help="jst-side: +1 = plugs on the +x side of the cells")
    ap.add_argument("--back-strip", action="store_true", help="two cells: every back-side part must sit between the cells")
    ap.add_argument("--batt-count", type=int, default=1, choices=[1, 2], help="2 = two cells in parallel near the strap ends")
    ap.add_argument("--pack-gap", type=float, default=0.3)
    ap.add_argument("--mcu-side", default="auto", choices=["auto", "front", "back"])
    ap.add_argument("--lug-w", type=float, default=25.1); ap.add_argument("--lug-r", type=float, default=2.5)
    ap.add_argument("--slot-w", type=float, default=19.75); ap.add_argument("--slot-h", type=float, default=1.77)
    ap.add_argument("--slot-clear", type=float, default=0.0, help="clearance from the outermost LED tip to the start of the strap slot (0 = same as the LED-to-edge margin)")
    ap.add_argument("--safety", type=float, default=0.0, help="extra board radius beyond the LED edge margin, mm (adds 2x to the diameter)")
    ap.add_argument("--mcu-pkg", default="tqfp", choices=["tqfp", "qfn"], help="AVR128DB48 package: TQFP-48 7x7 or VQFN-48 6x6 (both stocked at JLCPCB)")
    ap.add_argument("--small-to-back", action="store_true", help="everything except the MCU and the buttons prefers the wrist side")
    ap.add_argument("--lug-end", type=float, default=2.2, help="board material beyond the strap slot (mm)")
    ap.add_argument("--res-style", default="radial", choices=["radial", "tangential", "pack"], help="series resistors R1-R12: between the hour LEDs (radial/tangential) or packed with the other parts")
    ap.add_argument("--res-arc", type=float, default=2.2, help="distance along the hour ring from each hour LED to its resistor (mm)")
    ap.add_argument("--slots", type=int, default=2)
    ap.add_argument("--cell-y", type=float, default=0.0, help="shift the solar cell down (+) or up (-) from the centre, mm")
    ap.add_argument("--auto-cell-y", action="store_true", help="with a fixed --diameter: look for the smallest cell shift that lets everything fit")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    p = search(a)
    name = a.name or f"{a.cell}_{a.battery}mAh"
    out = os.path.join(HERE, "boards", name)
    os.makedirs(out, exist_ok=True)
    if not p or "leds" not in p:
        print("no solution:", p and p.get("why"))
        sys.exit(1)
    json.dump(p, open(os.path.join(out, "plan.json"), "w"))
    draw(p, os.path.join(out, name + ".png"))
    pcs = {q["ref"]: q["side"] for q in p["parts"]}
    print(f'{name}: LEDs off-board={len(p["led_outside"])} ' + f'D={p["D"]:.1f} mm  band={p["band"]:.2f}  free centre={2 * p["free_r"]:.1f} mm  ok={p["ok"]}  unplaced={p["unplaced"]}  front {p["front_used"]:.0f}%  back {p["back_used"]:.0f}%  MCU on {pcs.get("U1")}')


if __name__ == "__main__":
    main()
