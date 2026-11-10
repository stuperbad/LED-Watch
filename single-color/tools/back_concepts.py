"""back_concepts.py BACKPARTS.json OUT_PREFIX [variants.py] : concept layouts for the BACK side (parts only, no copper): picture, rule checks and distances to the U4 pins.
BACKPARTS.json = footprint geometry of the back parts, dumped from the board (position, orientation, pad-box, pad offsets, nets).   variants.py defines VARIANTS = {name: {ref: (x, y, rot)}}.
Checks: part boxes (pads + 0.15 mm) must not overlap each other or the fixed parts (0.1 mm gap), stay 0.5 mm inside the board circle (R 21.05 about 100, 100), and parts taller than 1.1 mm must not sit
inside the LiPo envelopes (the batteries rest 1.1 mm above the board).   Distances: straight, part pad to the U4 pin it serves.   Picture: back view as drawn in KiCad, family colours, badge = data-sheet priority,
outline colour = distance verdict (see the key in the picture)."""
import sys, json, math, importlib.util
from PIL import Image, ImageDraw, ImageFont
P = json.load(open(sys.argv[1])); out = sys.argv[2]
HEIGHT = {"R": 0.35, "C": 0.5, "C54": 1.25, "L": 2.5, "D": 1.11, "U5": 1.55, "U4": 0.78, "J": 2.96}
def height(r): return HEIGHT.get(r) or HEIGHT.get(r[0], 0.5)
FIXED = {"BZ1": (80.4, 95.5, 90.1, 105.1, "piezo 1.9 mm"), "J1": (83.5, 89.17, 90.11, 95.03, "LiPo clip 3.0 mm"), "J1B": (83.5, 106.08, 90.11, 111.92, "LiPo clip 3.0 mm"), "J2": (111.27, 93.28, 120.25, 106.72, "USB-C 3.3 mm")}
BAT = [(90.67, 79.42, 109.33, 97.58), (90.67, 102.42, 109.33, 120.58)]          # outer outline (nominal + half tolerance): nothing taller than 1.1 mm may enter
NOM = [(91.67, 80.42, 108.33, 96.58), (91.67, 103.42, 108.33, 119.58)]          # nominal body: nothing may enter (small parts may sit in the ring between the two)
FAM = {"solar": (255, 150, 0), "usb": (150, 60, 220)}
SOLAR = {"U4", "L1", "L2", "C50", "C51", "C52", "C53", "C54", "R50", "R51", "R52", "R53", "R54", "R55", "R56"}
# (priority badge, U4 pin(s) served: list of (pad number of the part, U4 pin))
SERVE = {"C52": ("1", [("1", 19)]), "C53": ("1", [("1", 19)]), "C50": ("2", [("1", 2)]), "L1": ("3", [("1", 20), ("2", 2)]), "C54": ("4", [("1", 14)]), "L2": ("5", [("1", 16), ("2", 14)]),
         "C51": ("H", [("1", 4)]), "R50": ("H", [("1", 7)]), "R51": ("H", [("1", 7)]), "R52": ("H", [("2", 10)]), "R53": ("H", [("1", 10)]), "R54": ("H", [("1", 11)]), "R55": ("H", [("1", 8)]), "R56": ("H", [("1", 12)])}
LIM = 3.0
def rotvec(dx, dy, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return dx * c - dy * s, dx * s + dy * c
def geom(ref, x, y, rot):
    d = P[ref]; a = rot - d["rot"]; x0, y0, x1, y1 = d["box"]
    cs = [rotvec(px, py, a) for px in (x0, x1) for py in (y0, y1)]
    box = (x + min(c[0] for c in cs), y + min(c[1] for c in cs), x + max(c[0] for c in cs), y + max(c[1] for c in cs))
    pads = {n: (x + rotvec(px, py, a)[0], y + rotvec(px, py, a)[1], net) for n, net, px, py in d["pads"]}
    return box, pads
def evaluate(V):
    G = {r: geom(r, *V[r]) for r in V}; issues = []
    boxes = {r: (b[0] - 0.15, b[1] - 0.15, b[2] + 0.15, b[3] + 0.15) for r, (b, p) in G.items()}
    rs = sorted(boxes)
    for i, a in enumerate(rs):
        for b in rs[i + 1:]:
            A, B = boxes[a], boxes[b]
            if A[0] < B[2] + 0.1 and B[0] < A[2] + 0.1 and A[1] < B[3] + 0.1 and B[1] < A[3] + 0.1: issues.append("overlap %s / %s" % (a, b))
        for f, (fx0, fy0, fx1, fy1, _) in FIXED.items():
            A = boxes[a]
            if A[0] < fx1 + 0.1 and fx0 < A[2] + 0.1 and A[1] < fy1 + 0.1 and fy0 < A[3] + 0.1: issues.append("%s on fixed %s" % (a, f))
        A = boxes[a]
        if any(math.hypot(cx - 100, cy - 100) > 20.55 for cx in (A[0], A[2]) for cy in (A[1], A[3])): issues.append("%s too close to the board edge" % a)
        for bt in (BAT if height(a) > 1.1 else NOM):
            if A[0] < bt[2] and bt[0] < A[2] and A[1] < bt[3] and bt[1] < A[3]: issues.append("%s (%.2f mm) %s" % (a, height(a), "in the battery outline" if height(a) > 1.1 else "in the nominal battery body"))
    dist = {}
    u4 = G["U4"][1]
    for r, (bdg, serves) in SERVE.items():
        if r not in G: continue
        ds = []
        for pn, pin in serves:
            p = G[r][1][pn]; q = u4[str(pin)]; ds.append(math.hypot(p[0] - q[0], p[1] - q[1]))
        dist[r] = ds
    return G, issues, dist
def colour(r, ds):
    w = max(ds); return (40, 170, 60) if w <= LIM else ((235, 160, 0) if w <= 2 * LIM else (215, 30, 30))
S = 30; X0, Y0, X1, Y1 = 78.0, 77.0, 122.0, 123.0
def draw(name, V, G, issues, dist):
    W, H = int((X1 - X0) * S), int((Y1 - Y0) * S); im = Image.new("RGB", (W, H), (250, 250, 250)); d = ImageDraw.Draw(im, "RGBA"); F = lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", s)
    p = lambda x, y: ((x - X0) * S, (y - Y0) * S)
    d.ellipse([p(100 - 21.05, 100 - 21.05), p(100 + 21.05, 100 + 21.05)], outline=(120, 120, 120), width=3, fill=(236, 240, 236))
    d.ellipse([p(100 - 20.55, 100 - 20.55), p(100 + 20.55, 100 + 20.55)], outline=(190, 190, 190), width=1)
    for bt in BAT:
        d.rectangle([p(bt[0], bt[1]), p(bt[2], bt[3])], fill=(180, 200, 235, 90), outline=(60, 90, 170), width=3)
        d.rectangle([p(bt[0] + 1, bt[1] + 1), p(bt[2] - 1, bt[3] - 1)], outline=(60, 90, 170, 120), width=1)
    d.text(p(95, 84), "LiPo 15 x 15 x 5 mm: only parts up to 1.1 mm under it", font=F(15), fill=(40, 70, 150))
    d.text(p(95, 115), "LiPo 15 x 15 x 5 mm", font=F(15), fill=(40, 70, 150))
    for f, (x0, y0, x1, y1, t) in FIXED.items():
        d.rectangle([p(x0, y0), p(x1, y1)], fill=(150, 150, 160, 160), outline=(70, 70, 80), width=3); d.text(p(x0 + 0.3, y0 + 0.2), "%s %s" % (f, t), font=F(13), fill=(0, 0, 0))
    for r, (b, pads) in G.items():
        fam = (255, 150, 0) if r in SOLAR else (150, 60, 220)
        if r in dist: oc = colour(r, dist[r])
        else: oc = (60, 60, 70)
        d.rectangle([p(b[0], b[1]), p(b[2], b[3])], fill=fam + (140,), outline=oc + (255,), width=4 if r in dist else 2)
        cx, cy = p((b[0] + b[2]) / 2, (b[1] + b[3]) / 2); d.text((cx, cy), r, font=F(12), fill=(0, 0, 0), anchor="mm")
        if r in SERVE:
            bx, by = p(b[0], b[1]); d.ellipse([bx - 11, by - 11, bx + 11, by + 11], fill=(30, 30, 40, 255), outline=oc + (255,), width=3); d.text((bx, by), SERVE[r][0], font=F(13), fill=(255, 255, 255), anchor="mm")
            for pn, pin in SERVE[r][1]:
                a = G[r][1][pn]; q = G["U4"][1][str(pin)]; d.line([p(a[0], a[1]), p(q[0], q[1])], fill=oc + (255,), width=2)
    kx, ky = 10, H - 150
    d.rectangle([kx - 4, ky - 6, kx + 560, ky + 112], fill=(255, 255, 255, 235), outline=(120, 120, 120))
    d.text((kx, ky), "KEY", font=F(14), fill=(0, 0, 0))
    d.rectangle([kx, ky + 22, kx + 16, ky + 36], fill=(255, 150, 0), outline=(0, 0, 0)); d.text((kx + 22, ky + 21), "solar charger parts", font=F(13), fill=(0, 0, 0))
    d.rectangle([kx + 180, ky + 22, kx + 196, ky + 36], fill=(150, 60, 220), outline=(0, 0, 0)); d.text((kx + 202, ky + 21), "USB-C corner parts", font=F(13), fill=(0, 0, 0))
    d.rectangle([kx + 360, ky + 22, kx + 376, ky + 36], fill=(150, 150, 160), outline=(70, 70, 80)); d.text((kx + 382, ky + 21), "fixed: clips, buzzer, USB-C", font=F(13), fill=(0, 0, 0))
    d.ellipse([kx, ky + 44, kx + 18, ky + 62], fill=(30, 30, 40), outline=(40, 170, 60), width=3); d.text((kx + 9, ky + 53), "1", font=F(12), fill=(255, 255, 255), anchor="mm")
    d.text((kx + 26, ky + 46), "dark circle = number (data-sheet priority, 1 = closest) or H (high-impedance divider)", font=F(13), fill=(0, 0, 0))
    for j, (col, t) in enumerate((((40, 170, 60), "within 3 mm"), ((235, 160, 0), "3-6 mm"), ((215, 30, 30), "over 6 mm"))):
        x = kx + j * 150; d.rectangle([x, ky + 70, x + 24, ky + 84], fill=(255, 150, 0, 140), outline=col, width=4); d.text((x + 30, ky + 69), t, font=F(13), fill=(0, 0, 0))
    d.text((kx + 450, ky + 69), "outline = distance to the U4 pin", font=F(11), fill=(0, 0, 0))
    d.text((kx, ky + 90), "tall parts (L1, L2 2.5 mm; U5 1.55; C54 1.25) must stay out of the batteries' footprint; thin lines run from each part to the U4 pin it serves", font=F(11), fill=(0, 0, 0))
    d.text((10, 6), name, font=F(24), fill=(0, 0, 0))
    bad = [i for i in issues]
    d.text((10, H - 24 - 18 * min(len(bad), 6)), "rule issues: %s" % (", ".join(bad[:5]) if bad else "none"), font=F(14), fill=(215, 30, 30) if bad else (40, 130, 40))
    return im

import random
USB = {"R68": [("1", "J2:A5")], "R69": [("1", "J2:B5")], "D51": [("1", "J2:A4")], "R72": [("1", "J2:A8")], "D50": [("2", "J2:A8")]}
def pull_cost(G):
    c = 0.0; j2 = G_FIXED["J2"]
    for r, lst in USB.items():
        if r not in G: continue
        for pn, tgt in lst:
            q = j2[tgt.split(":")[1]]; p = G[r][1][pn]; c += math.hypot(p[0] - q[0], p[1] - q[1])
    u5 = G["U5"][1]
    for r, pn, pin in (("C55", "1", "6"), ("C56", "1", "2"), ("R70", "1", "4"), ("R71", "1", "1")):
        if r in G and str(pin) in u5:
            p = G[r][1][pn]; q = u5[str(pin)]; c += 0.6 * math.hypot(p[0] - q[0], p[1] - q[1])
    return c
J2 = P["J2"]; G_FIXED = {"J2": {n: (J2["x"] + dx, J2["y"] + dy) for n, net, dx, dy in J2["pads"] if n}}
WEIGHT = {"C52": 10, "C53": 10, "C50": 6, "L1": 2.5, "C54": 4, "L2": 2, "C51": 2, "R50": 1.5, "R51": 1.5, "R52": 1.5, "R53": 1.5, "R54": 1.5, "R55": 1.5, "R56": 2}
def cost(V, rules):
    G = {r: geom(r, *V[r]) for r in V}; c = 0.0
    boxes = {r: (b[0] - 0.15, b[1] - 0.15, b[2] + 0.15, b[3] + 0.15) for r, (b, p) in G.items()}; rs = sorted(boxes)
    for i, a in enumerate(rs):
        A = boxes[a]
        for b in rs[i + 1:]:
            B = boxes[b]
            if A[0] < B[2] + 0.1 and B[0] < A[2] + 0.1 and A[1] < B[3] + 0.1 and B[1] < A[3] + 0.1: c += 50
        for f, (fx0, fy0, fx1, fy1, _) in FIXED.items():
            if A[0] < fx1 + 0.1 and fx0 < A[2] + 0.1 and A[1] < fy1 + 0.1 and fy0 < A[3] + 0.1: c += 50
        if any(math.hypot(cx - 100, cy - 100) > 20.55 for cx in (A[0], A[2]) for cy in (A[1], A[3])): c += 50
        for bt in (BAT if height(a) > 1.1 else NOM):
            if A[0] < bt[2] and bt[0] < A[2] and A[1] < bt[3] and bt[1] < A[3]: c += 50
        for fb in rules.get('forbid', {}).get(a, []) + rules.get('forbid', {}).get('*', []):
            if A[0] < fb[2] and fb[0] < A[2] and A[1] < fb[3] and fb[1] < A[3]: c += 50
        if a in rules.get('rot0', []) and V[a][2] % 180 != 0: c += 50
        reg = rules.get("region", {}).get(a)
        if reg and not any(A[0] >= q[0] and A[2] <= q[2] and A[1] >= q[1] and A[3] <= q[3] for q in reg): c += 50
    u4 = G["U4"][1]
    for r, (bdg, serves) in SERVE.items():
        if r in G:
            for pn, pin in serves:
                p = G[r][1][pn]; q = u4[str(pin)]; c += WEIGHT[r] * math.hypot(p[0] - q[0], p[1] - q[1])
    c += pull_cost(G)
    for a, b in rules.get('mirrorx', []):
        xc = rules['xc']; c += 4.0 * (abs((G[a][0][0] + G[a][0][2]) / 2 + (G[b][0][0] + G[b][0][2]) / 2 - 2 * xc) + abs(V[a][1] - V[b][1]) * 2)
    for a, b in rules.get("mirror", []):
        c += 1.2 * (abs(G[a][0][0] - G[b][0][0]) + abs((G[a][0][1] + G[b][0][3]) - 200) * 0.5 + abs(V[a][2] - V[b][2]) % 180 * 0.02)
    return c
def optimise(V0, rules, seed=1, iters=60000):
    rnd = random.Random(seed); V = dict(V0); V.update(rules.get('init', {})); best = cost(V, rules); free = [r for r in V if r not in rules.get('pinned', []) or r in rules.get('rotfree', [])]; T = 4.0
    for it in range(iters):
        r = rnd.choice(free); x, y, rot = V[r]; sig = 0.15 + 2.5 * (1 - it / iters) ** 2
        nx, ny, nr = x + rnd.gauss(0, sig), y + rnd.gauss(0, sig), rot
        if r in rules.get('pinned', []): nx, ny = x, y
        if rnd.random() < (0.25 if r in rules.get('rotfree', []) else 0.04): nr = rnd.choice([0, 180] if r in rules.get('rot0', []) else [0, 90, 180, 270]) if r != 'U4' or rules.get('u4rot') else rot
        reg = rules.get('region', {}).get(r)
        if reg and rnd.random() < 0.05:
            q = rnd.choice(reg); nx, ny = rnd.uniform(q[0] + 1.5, q[2] - 1.5), rnd.uniform(q[1] + 1.5, q[3] - 1.5)
        nx, ny = round(nx * 20) / 20, round(ny * 20) / 20
        W = dict(V); W[r] = (nx, ny, nr); c = cost(W, rules)
        if c < best or rnd.random() < math.exp((best - c) / max(T * (1 - it / iters), 1e-3)): V, best = W, c
    return V, best
mod = importlib.import_module("concept_rules") if False else None
V0 = {r: (P[r]["x"], P[r]["y"], P[r]["rot"] % 360) for r in P if r not in FIXED}
for r in V0: V0[r] = (V0[r][0], V0[r][1], {0: 0, 90: 90, 180: 180, 270: 270}.get(round(V0[r][2]) % 360, round(V0[r][2]) % 360))
BAND = [(91.0, 97.58, 111.0, 102.42)]
NE = [(109.5, 80.5, 119.5, 92.9)]; SE = [(109.5, 107.1, 119.5, 119.5)]
def make(xu, y0=99.2, u5="east", mirror=True):
    """one row of small parts under U4 (rot 0 / 180 only), U4 / L1 / L2 pushed up to y0, nothing else above or below U4, tall parts out of the battery outline"""
    ROW = ["C50", "C51", "R50", "R51", "R52", "R53"]
    SOLAR_REST = [r for r in V0 if r in SOLAR and r not in ROW and r not in ("U4", "L1", "L2")]
    north = (89.0, 80.0, 112.0, y0 - 2.05); south = (89.0, y0 + 2.05, 112.0, 120.0)
    forbid = {"*": []}
    for r in SOLAR_REST + ["L1", "L2"]: forbid[r] = [north, south]
    for r in ROW: forbid[r] = [north]
    region = {r: [(xu - 9.5, 100.9, xu + 9.5, 102.5)] for r in ROW}
    for r in ("L1", "L2"): region[r] = [(90.5, y0 - 1.6, 111.0, y0 + 1.6)]
    rules = {"init": {"U4": (xu, y0, 90), "L1": (xu + 6.3, y0, 0), "L2": (xu - 6.3, y0, 0)}, "pinned": ["U4"], "rotfree": ["U4"], "u4rot": True, "xc": xu, "forbid": forbid, "region": region, "rot0": ROW + ["L1", "L2"]}
    if mirror: rules["mirrorx"] = [("L1", "L2")]
    corner = [(109.4, 80.0, 119.8, 93.0), (109.4, 107.0, 119.8, 119.8)]
    for r in ("C54",): forbid[r] = forbid.get(r, []) + corner
    if u5 == "se": region["U5"] = [(109.6, 107.3, 119.0, 118.0)]; forbid["U5"] = []
    elif u5 == "ne": region["U5"] = [(109.6, 82.0, 119.0, 92.7)]; forbid["U5"] = []
    else: region["U5"] = [(90.6, 97.6, 111.0, 102.4)]
    return rules
CONCEPTS = {
    "A now": (None, None),
    "E U5 southeast": (make(101.5, u5="se"), 5),
    "F U5 northeast": (make(100.5, u5="ne"), 6),
    "G U5 in the band": (make(100.5, u5="band"), 7),
}
only = sys.argv[3].split(",") if len(sys.argv) > 3 else list(CONCEPTS)
iters = int(sys.argv[4]) if len(sys.argv) > 4 else 40000
summary = {}
for name in only:
    rules, seed = CONCEPTS[name]
    if rules is None: V = V0; c = cost(V0, {})
    elif False: pass
    else:
        V, c = None, 1e18
        for sd in range(seed * 10, seed * 10 + 4):
            W, cw = optimise(V0, rules, sd, iters)
            if cw < c: V, c = W, cw
    G, issues, dist = evaluate(V); im = draw(name, V, G, issues, dist); fn = "%s-%s.png" % (out, name.split()[0]); im.save(fn)
    json.dump({r: V[r] for r in V}, open("%s-%s.json" % (out, name.split()[0]), "w"))
    print("== %s cost %.1f -> %s" % (name, c, fn)); print("   issues:", issues if issues else "none")
    print("   straight mm:", {r: [round(v, 1) for v in ds] for r, ds in sorted(dist.items())})
