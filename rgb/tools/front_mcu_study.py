"""How large must the free disc inside the LED rings be to put the MCU on the FRONT?
Packs the front items (solar cell keep-out, MCU, two buttons, accelerometer, the 7 mode lights) into a disc of free radius F by simulated annealing (courtyard rectangles, 0/90 degree turns),
for several vertical offsets of the solar cell, and reports the smallest F that works.  Pure python.
usage: front_mcu_study.py [--mcu 10.29x10.29] [--tries 6] [--iters 60000]
Sizes are the KiCad courtyards: AVR128DB64 VQFN-64 10.29 x 10.29, AVR128DB48 QFN-48 7.68 x 7.31 (single-colour board), KMR2 button 5.69 x 3.69, LIS2DW12 2.59 x 2.59, LED 1.5 x 1.5.
The free radius F = inner ring radius - 0.5 (LED half size) - 0.4 (clearance); the cell keep-out is the cell body (23.15 x 8.15) plus its pads (24.2 wide) centred at (0, s)."""
import argparse
import math
import random

ap = argparse.ArgumentParser()
ap.add_argument("--mcu", default="10.29x10.29")
ap.add_argument("--tries", type=int, default=3)
ap.add_argument("--iters", type=int, default=20000)
ap.add_argument("--gap", type=float, default=0.2)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--modes", type=int, default=7, help="number of mode lights that have to be on the front")
ap.add_argument("--support", action="store_true", help="also place the MCU decoupling capacitors, crystal and load capacitors next to the MCU")
ap.add_argument("--caps", type=int, default=7)
args = ap.parse_args()
random.seed(args.seed)
mw, mh = (float(v) for v in args.mcu.split("x"))
GAP = args.gap

ITEMS = [("MCU", mw, mh), ("SW1", 5.69, 3.69), ("SW2", 5.69, 3.69), ("IMU", 2.59, 2.59)] + [("IND%d" % (i + 1), 1.5, 1.5) for i in range(args.modes)]
NEAR = {}                                    # item index -> (target index, largest edge-to-edge gap in mm): parts that must sit next to the MCU
if args.support:
    for k in range(args.caps):               # supply decoupling capacitors (0402) within 1.5 mm of the MCU edge
        ITEMS.append(("CM%d" % (k + 1), 1.95, 1.03))
        NEAR[len(ITEMS) - 1] = (0, 1.5)
    ITEMS.append(("Y1", 3.7, 1.9))           # 32.768 kHz crystal and its two load capacitors within 4 mm
    NEAR[len(ITEMS) - 1] = (0, 4.0)
    for k in range(2):
        ITEMS.append(("C2%d" % k, 1.95, 1.03))
        NEAR[len(ITEMS) - 1] = (0, 4.0)
CELL_W, CELL_H = 24.2, 8.2


def rect(it, st):
    name, w, h = it
    x, y, rot = st
    if rot:
        w, h = h, w
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def cell_corner_radius(s):
    """the cell body and its pads must lie inside the free disc themselves"""
    return max(math.hypot(CELL_W / 2, abs(s) + CELL_H / 2), 0)


def penalty(states, F, s):
    p = 0.0
    rs = [rect(it, st) for it, st in zip(ITEMS, states)]
    cell = (-CELL_W / 2, s - CELL_H / 2, CELL_W / 2, s + CELL_H / 2)
    for r in rs:
        for cx, cy in ((r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])):
            e = math.hypot(cx, cy) - F
            if e > 0:
                p += e * 4
        ox = min(r[2], cell[2]) - max(r[0], cell[0]) + GAP
        oy = min(r[3], cell[3]) - max(r[1], cell[1]) + GAP
        if ox > 0 and oy > 0:
            p += min(ox, oy) * 3 + 0.01
    for i, (tgt, lim) in NEAR.items():
        a, b = rs[i], rs[tgt]
        gx = max(a[0] - b[2], b[0] - a[2], 0.0)
        gy = max(a[1] - b[3], b[1] - a[3], 0.0)
        g = math.hypot(gx, gy)
        if g > lim:
            p += (g - lim) * 2
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            a, b = rs[i], rs[j]
            ox = min(a[2], b[2]) - max(a[0], b[0]) + GAP
            oy = min(a[3], b[3]) - max(a[1], b[1]) + GAP
            if ox > 0 and oy > 0:
                p += min(ox, oy) * 3 + 0.01
    return p


def anneal(F, s, iters):
    if cell_corner_radius(s) > F:
        return False, None
    st = [[random.uniform(-F * 0.6, F * 0.6), random.uniform(-F * 0.6, F * 0.6), random.random() < 0.5] for _ in ITEMS]
    cur = penalty(st, F, s)
    best = cur
    T0 = 2.0
    for k in range(iters):
        T = T0 * (1 - k / iters) + 0.01
        i = random.randrange(len(ITEMS))
        old = list(st[i])
        r = random.random()
        if r < 0.1:
            st[i][2] = not st[i][2]
        elif r < 0.2:
            st[i][0] = random.uniform(-F, F)
            st[i][1] = random.uniform(-F, F)
        else:
            sc = 2.0 if r < 0.4 else 0.3
            st[i][0] += random.gauss(0, sc)
            st[i][1] += random.gauss(0, sc)
        new = penalty(st, F, s)
        if new <= cur or random.random() < math.exp((cur - new) / T):
            cur = new
            best = min(best, cur)
            if cur < 1e-9:
                return True, st
        else:
            st[i] = old
    return False, st


def feasible(F, s):
    for _ in range(args.tries):
        ok, st = anneal(F, s, args.iters)
        if ok:
            return st
    return None


print("MCU courtyard %.2f x %.2f; %d mode lights; gap %.2f mm" % (mw, mh, args.modes, GAP))
print("cell offset s | smallest free radius F | inner ring radius | board radius R (rings 2.5 mm apart, 2.0 mm ring to edge)")
res = {}
for s in (-2.5, -2.0, -1.5, -1.0, 0.0):
    lo, hi = max(11.0, cell_corner_radius(s) - 0.05), 18.0
    sol = None
    while hi - lo > 0.1:
        mid = (lo + hi) / 2
        st = feasible(mid, s)
        if st:
            hi, sol = mid, st
        else:
            lo = mid
    res[s] = (hi, sol)
    if sol is None:
        sol = feasible(hi, s)
        res[s] = (hi, sol)
    print("  s = %+4.1f      F = %5.2f              r_in = %5.2f           R = %5.2f" % (s, hi, hi + 0.9, hi + 0.9 + 5.0 + 2.0))
best_s = min(res, key=lambda k: res[k][0])
F, sol = res[best_s]
print("best: cell offset %+.1f mm, F = %.2f" % (best_s, F))
for it, st in zip(ITEMS, sol):
    r = rect(it, st)
    print("   %-5s centre (%6.2f, %6.2f)  %s" % (it[0], (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, "turned 90" if st[2] else ""))
