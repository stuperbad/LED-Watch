"""place_sa.py DETAIL.json FIXED.json OUT.json [iters seed] : place the free back parts around a hand-made core (annealing, 0.05 mm grid, rotations 0/90/180/270).
FIXED.json = {ref: [x, y, rot]} parts that stay (backbone).   Cost = weighted straight distance of each part's pads to the U4 pins it serves (+ USB-C / U5 pulls) + 100 per rule violation
(courtyard overlap, pad gap < 0.20 mm of other nets, nominal battery bodies, board edge) + 100 for sitting in the via fan-out ring of U4 or the two inductor corridors."""
import sys, json, math, random
from placelib import Lib, checks, FIXED, rotv
L = Lib(sys.argv[1]); fixed = json.load(open(sys.argv[2])); out = sys.argv[3]; iters = int(sys.argv[4]) if len(sys.argv) > 4 else 60000; seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
FREE = ["C56", "R68", "R70", "R71", "R72", "C55"]
DIV = set()
SERVE = {"C51": [("1", "U4", "4", 2)], "R50": [("1", "U4", "8", 1), ("2", "U4", "7", 1)], "R51": [("1", "U4", "7", 1.5)], "R52": [("1", "U4", "8", 1), ("2", "U4", "10", 1)], "R53": [("1", "U4", "10", 1), ("2", "U4", "11", 1)],
         "R54": [("1", "U4", "11", 1.5)], "R55": [("1", "U4", "8", 1), ("2", "U4", "12", 1)], "R56": [("1", "U4", "12", 1.5)], "C53": [("1", "U4", "19", 6), ("1", "C52", "1", 3)],
         "C56": [("1", "U5", "2", 3)], "C55": [("1", "U5", "6", 3)], "R70": [("1", "U5", "4", 2)], "R71": [("1", "U5", "1", 2)], "R68": [("1", "J2", "A5", 1)], "R72": [("1", "J2", "A8", 1.5)], "U5": [("6", "J2", "A4", 2), ("2", "C56", "1", 1)], "D50": [("2", "J2", "A8", 1.5)], "D51": [("1", "J2", "A4", 1.5)], "R69": [("1", "J2", "B5", 1)]}
u4 = fixed["U4"]; xu, yu = u4[0], u4[1]
NOGO = [(xu - 2.1, yu - 2.1, xu + 2.1, yu + 2.1)]
for k in ("corr",):
    NOGO += [(xu - 2.9, yu + 1.4, xu - 0.7, yu + 3.0), (xu + 0.7, yu + 1.4, xu + 2.9, yu + 3.0)]
def region_ok(r, x, y):
    if r in DIV: return 90.4 <= x <= 108.0 and 96.7 <= y <= 103.3
    return 104.0 <= x <= 111.8 and 93.0 <= y <= 107.0
def build(POS):
    P = dict(fixed); P.update(POS); return L.all(P)
def pad(G, r, n):
    for p in G[r][0]:
        if p[0] == n: return p
def cost(POS, detail=False):
    G = build(POS); c = 0.0; info = []
    for r in FREE:
        for pn, tr, tn, w in SERVE.get(r, []):
            p, q = pad(G, r, pn), pad(G, tr, tn); c += w * math.hypot(p[2] - q[2], p[3] - q[3])
        body = G[r][1]
        if not region_ok(r, POS[r][0], POS[r][1]): c += 100
        for z in NOGO:
            if body[0] < z[2] and z[0] < body[2] and body[1] < z[3] and z[1] < body[3]: c += 100; info.append("nogo " + r)
    for kind, text, size in checks(G, set(FREE)): c += 100 + 50 * size; info.append(kind + " " + text)
    return (c, info) if detail else c
rnd = random.Random(seed)
POS = {r: [L.D[r]["x"], L.D[r]["y"], L.D[r]["rot"]] for r in FREE}
# start: spread along the bottom row
for i, r in enumerate(FREE): POS[r] = [rnd.uniform(91, 107) if r in DIV else rnd.uniform(105, 111), rnd.uniform(97, 103), rnd.choice([0, 90])]
best = cost(POS); cur = best; bestPOS = json.loads(json.dumps(POS)); T0 = 6.0
for it in range(iters):
    r = rnd.choice(FREE); x, y, rot = POS[r]; sig = 0.1 + 2.0 * (1 - it / iters) ** 2
    nx, ny, nr = x + rnd.gauss(0, sig), y + rnd.gauss(0, sig), rot
    if rnd.random() < 0.15: nr = rnd.choice([0, 90, 180, 270])
    if rnd.random() < 0.03: nx, ny = (rnd.uniform(90.5, 108), rnd.uniform(96.8, 103.2)) if r in DIV else (rnd.uniform(104, 111.8), rnd.uniform(93, 107))
    nx, ny = round(nx * 20) / 20, round(ny * 20) / 20
    old = POS[r]; POS[r] = [nx, ny, nr]; c = cost(POS)
    T = max(T0 * (1 - it / iters), 1e-3)
    if c < cur or rnd.random() < math.exp((cur - c) / T):
        cur = c
        if c < best: best = c; bestPOS = json.loads(json.dumps(POS))
    else: POS[r] = old
c, info = cost(bestPOS, True); print("best cost %.1f" % c, info)
allpos = dict(fixed); allpos.update(bestPOS); json.dump(allpos, open(out, "w"), indent=0)
