"""
Courtyard placement test for the SOLAR (variant B) watch, board = circle, LED band outside, solar cell in the middle of the front.
Raster (0.1 mm) greedy first-fit packing of rectangular keep-outs, 90-degree rotations allowed.
  front free region = circle(R - band) minus the cell rectangle (+ clearance)
  back  free region = circle(R - edge) minus the battery rectangle (+ clearance)
Run:  python placement_test.py
"""
import numpy as np, itertools, json

STEP = 0.1
BAND = 8.17          # three LED rings + gaps + margin (Board size tab B19 for 0603/0402/0402, 0.5 mm LED gap)
EDGE = 1.0           # keep-out from the board edge on the back
CELL_CLR = 0.3
BATT_CLR = 0.5
OVERHEAD = 1.0       # pure courtyards here (the spreadsheet adds a 1.3x routing factor; see PACK_GAP)
PACK_GAP = 0.3       # extra space between courtyards to leave routing room

PARTS = [  # name, w, h, count
    ("MCU AVR128DB48", 10.39, 10.39, 1), ("BQ25570", 4.8, 4.8, 1), ("JST battery", 5.89, 6.65, 1), ("Button", 5.69, 3.69, 2),
    ("UPDI header", 3.19, 4.91, 1), ("Inductor 1210", 4.65, 3.25, 2), ("Crystal", 4.09, 2.39, 1), ("LIS2DW12", 2.59, 2.59, 1),
    ("0402 passive", 1.95, 1.03, 34),
]
BATTS = {"35 mAh (19.5x10.2)": (19.5, 10.2), "50 mAh (21x12.8)": (21.0, 12.8), "80 mAh (24x10)": (24.0, 10.0), "155 mAh (27.5x20.5)": (27.5, 20.5)}
FRONT_FIRST = ["Button", "Crystal", "LIS2DW12", "UPDI header", "0402 passive", "Inductor 1210", "BQ25570", "JST battery", "MCU AVR128DB48"]


def grid(R):
    n = int(2 * R / STEP) + 2
    c = n * STEP / 2
    xs = (np.arange(n) + 0.5) * STEP - c
    X, Y = np.meshgrid(xs, xs)
    return X, Y, c


def region(R, rect, clr):
    X, Y, c = grid(R)
    free = (X ** 2 + Y ** 2) <= R ** 2
    if rect:
        w, h = rect
        free &= ~((np.abs(X) <= w / 2 + clr) & (np.abs(Y) <= h / 2 + clr))
    return free


def fits_at(free_cs, w, h):
    """return list of top-left (iy, ix) where a w x h block fits entirely in free"""
    nw, nh = int(round(w / STEP)), int(round(h / STEP))
    S = free_cs
    H, W = S.shape[0] - 1, S.shape[1] - 1
    if nh > H or nw > W:
        return None
    tot = S[nh:, nw:] - S[:-nh, nw:] - S[nh:, :-nw] + S[:-nh, :-nw]
    ok = np.argwhere(tot == nw * nh)
    return ok


def cumsum2(a):
    s = np.zeros((a.shape[0] + 1, a.shape[1] + 1), dtype=np.int32)
    s[1:, 1:] = a.astype(np.int32).cumsum(0).cumsum(1)
    return s


def place_all(front, back, parts_order):
    """front/back: boolean free arrays. returns dict part -> (n_front, n_back, n_unplaced)"""
    res = {}
    fr, bk = front.copy(), back.copy()
    for name in parts_order:
        w, h, cnt = next((p[1], p[2], p[3]) for p in PARTS if p[0] == name)
        nf = nb = 0
        for _ in range(cnt):
            placed = False
            for tag, arr in (("f", fr), ("b", bk)):
                if tag == "f" and name in ("MCU AVR128DB48", "JST battery"):
                    continue     # these two are kept on the back by design (JST sits beside the battery)
                cs = cumsum2(arr)
                for (ww, hh) in ((w + PACK_GAP, h + PACK_GAP), (h + PACK_GAP, w + PACK_GAP)):
                    ok = fits_at(cs, ww, hh)
                    if ok is None or len(ok) == 0:
                        continue
                    # prefer the position nearest the outer edge so the middle stays free
                    iy, ix = ok[np.argmax(((ok[:, 0] - arr.shape[0] / 2) ** 2 + (ok[:, 1] - arr.shape[1] / 2) ** 2))]
                    nw, nh = int(round(ww / STEP)), int(round(hh / STEP))
                    arr[iy:iy + nh, ix:ix + nw] = False
                    placed = True
                    break
                if placed:
                    if tag == "f":
                        nf += 1
                    else:
                        nb += 1
                    break
        res[name] = (nf, nb, cnt - nf - nb)
    return res, fr, bk


def run(D, cell, batt):
    R = D / 2
    front = region(R - BAND, cell, CELL_CLR)
    back = region(R - EDGE, batt, BATT_CLR)
    res, fr, bk = place_all(front, back, FRONT_FIRST)
    left = {k: v[2] for k, v in res.items() if v[2]}
    return res, left, 100 * (1 - fr.sum() / max(1, front.sum())), 100 * (1 - bk.sum() / max(1, back.sum()))


if __name__ == "__main__":
    out = []
    for cell_name, cell in (("cell 23 wide x 25 tall", (23.0, 25.0)), ("cell 25 wide x 23 tall", (25.0, 23.0))):
        for bn, batt in BATTS.items():
            first_ok = None
            for D in np.arange(46.0, 58.01, 1.0):
                if (cell[0] ** 2 + cell[1] ** 2) ** 0.5 / 2 > D / 2 - BAND:
                    continue                                    # cell corners would hit the LED band
                res, left, fpct, bpct = run(D, cell, batt)
                if not left:
                    first_ok = (D, res, fpct, bpct)
                    break
            if first_ok:
                D, res, fpct, bpct = first_ok
                front_parts = {k: v[0] for k, v in res.items() if v[0]}
                out.append(f"{cell_name:24s} | {bn:22s} | smallest board that packs: {D:.0f} mm | front used {fpct:.0f}% back used {bpct:.0f}% | on FRONT: {front_parts}")
            else:
                out.append(f"{cell_name:24s} | {bn:22s} | does not pack up to 58 mm")
    print("\n".join(out))
    # detail for the headline case
    res, left, fpct, bpct = run(51.0, (23.0, 25.0), BATTS["80 mAh (24x10)"])
    print("\n51 mm board, 23x25 cell, 80 mAh battery:", json.dumps({k: {"front": v[0], "back": v[1], "unplaced": v[2]} for k, v in res.items()}), f"front {fpct:.0f}% back {bpct:.0f}%")


def variant_a():
    """no solar cell: front free centre is a plain circle; parts = MCU, sensor, crystal, charger, LDO, JST, 2 buttons, UPDI, 2 pads, 20 passives"""
    global PARTS, FRONT_FIRST
    keep = (PARTS, FRONT_FIRST)
    PARTS = [("MCU AVR128DB48", 10.39, 10.39, 1), ("JST battery", 5.89, 6.65, 1), ("Button", 5.69, 3.69, 2), ("UPDI header", 3.19, 4.91, 1), ("Crystal", 4.09, 2.39, 1),
             ("LIS2DW12", 2.59, 2.59, 1), ("Charger SOT-23-5", 4.19, 3.49, 1), ("LDO SOT-23", 3.95, 3.49, 1), ("Charge pad", 3.09, 3.10, 2), ("0402 passive", 1.95, 1.03, 20)]
    FRONT_FIRST = ["Button", "Charge pad", "Crystal", "LIS2DW12", "UPDI header", "Charger SOT-23-5", "LDO SOT-23", "0402 passive", "JST battery", "MCU AVR128DB48"]
    lines = []
    for bn, batt in BATTS.items():
        for D in np.arange(32.0, 56.01, 1.0):
            res, left, fpct, bpct = run(D, None, batt)
            if not left:
                lines.append(f"VARIANT A | {bn:22s} | smallest board that packs: {D:.0f} mm | front {fpct:.0f}% back {bpct:.0f}% | front: { {k: v[0] for k, v in res.items() if v[0]} }")
                break
        else:
            lines.append(f"VARIANT A | {bn:22s} | does not pack up to 56 mm")
    PARTS, FRONT_FIRST = keep
    return "\n".join(lines)


if __name__ == "__main__":
    print()
    print(variant_a())
