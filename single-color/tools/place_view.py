"""place_view.py DETAIL.json POS.json OUT.png [x0 y0 x1 y1 ppmm] : picture + checks of a back-side placement (pads with net labels, courtyards, battery outlines).
DETAIL.json from rework_dump.py, POS.json = {ref: [x, y, rot]} for the parts that move (the others stay).  Checks: pad-to-pad gaps of different nets (< 0.20 mm flagged, < 0.10 error),
courtyard overlaps, tall parts (L1 / L2 2.5 mm, C54 1.25, U5 1.55) outside the nominal battery bodies, parts inside the board circle; loop distances (straight, pad to pad)."""
import sys, json, math
from PIL import Image, ImageDraw, ImageFont
D = json.load(open(sys.argv[1])); POS = json.load(open(sys.argv[2])); out = sys.argv[3]
X0, Y0, X1, Y1, S = (list(map(float, sys.argv[4:9])) if len(sys.argv) > 8 else (88.0, 93.5, 114.5, 106.5, 70.0))
NOM = [(91.67, 80.42, 108.33, 96.58), (91.67, 103.42, 108.33, 119.58)]; OUTER = [(90.67, 79.42, 109.33, 97.58), (90.67, 102.42, 109.33, 120.58)]
TALL = {"L1": 2.5, "L2": 2.5, "C54": 1.25, "U5": 1.55, "D50": 1.11, "D51": 1.11}
FIXED = {"J1", "J1B", "BZ1", "J2", "MECH2", "MECH3"}
def rotv(dx, dy, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return dx * c - dy * s, dx * s + dy * c
def place(r):
    d = D[r]; x, y, rot = POS.get(r, [d["x"], d["y"], d["rot"]]); a = rot - d["rot"]; pads = []
    for p in d["pads"]:
        cx, cy = rotv(p["cx"], p["cy"], a); sw = round(a / 90) % 2
        hx, hy = (p["hy"], p["hx"]) if sw else (p["hx"], p["hy"]); pads.append((p["n"], p["net"], x + cx, y + cy, hx, hy))
    b = d["body"]; cs = [rotv(px, py, a) for px in (b[0], b[2]) for py in (b[1], b[3])]
    body = (x + min(c[0] for c in cs), y + min(c[1] for c in cs), x + max(c[0] for c in cs), y + max(c[1] for c in cs))
    return pads, body
G = {r: place(r) for r in D}
def gap(a, b):
    dx = max(abs(a[2] - b[2]) - a[4] - b[4], 0); dy = max(abs(a[3] - b[3]) - a[5] - b[5], 0); return math.hypot(dx, dy)
issues = []
refs = sorted(G)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        if a in FIXED and b in FIXED: continue
        A, B = G[a][1], G[b][1]
        if A[0] < B[2] - 0.001 and B[0] < A[2] - 0.001 and A[1] < B[3] - 0.001 and B[1] < A[3] - 0.001 and not (a in ("MECH2", "MECH3") or b in ("MECH2", "MECH3")): issues.append("courtyard %s / %s" % (a, b))
        if max(abs(A[0] + A[2] - B[0] - B[2]) / 2 - (A[2] - A[0] + B[2] - B[0]) / 2, abs(A[1] + A[3] - B[1] - B[3]) / 2 - (A[3] - A[1] + B[3] - B[1]) / 2) > 3: continue
        for p in G[a][0]:
            for q in G[b][0]:
                if p[1] and p[1] == q[1]: continue
                g = gap(p, q)
                if g < 0.2: issues.append("pad gap %.2f %s.%s / %s.%s" % (g, a, p[0], b, q[0]))
for r, (pads, body) in G.items():
    if r in FIXED: continue
    if r in TALL and TALL[r] > 1.1:
        for bt in NOM:
            if body[0] < bt[2] and bt[0] < body[2] and body[1] < bt[3] and bt[1] < body[3]: issues.append("%s (%.2f mm tall) inside the nominal battery body by %.2f mm" % (r, TALL[r], min(body[3] - bt[1], bt[3] - body[1], body[2] - bt[0], bt[2] - body[0]) if True else 0))
    else:
        for bt in NOM:
            if body[0] < bt[2] and bt[0] < body[2] and body[1] < bt[3] and bt[1] < body[3]: issues.append("%s inside the nominal battery body" % r)
    for cx in (body[0], body[2]):
        for cy in (body[1], body[3]):
            if math.hypot(cx - 100, cy - 100) > 20.55: issues.append("%s too close to the board edge" % r); break
        else: continue
        break
def pad(r, n):
    for p in G[r][0]:
        if p[0] == n: return p
LOOPS = [("L1.LBOOST - U4.20", ("L1", "1"), ("U4", "20")), ("L1.SOLAR_IN - U4.2", ("L1", "2"), ("U4", "2")), ("C50.SOLAR_IN - L1.SOLAR_IN", ("C50", "1"), ("L1", "2")), ("C50.SOLAR_IN - U4.2", ("C50", "1"), ("U4", "2")),
         ("L2.LBUCK - U4.16", ("L2", "1"), ("U4", "16")), ("L2.3V3 - U4.14", ("L2", "2"), ("U4", "14")), ("C54.3V3 - L2.3V3", ("C54", "1"), ("L2", "2")), ("C54.3V3 - U4.14", ("C54", "1"), ("U4", "14")),
         ("C52.VBAT - U4.19", ("C52", "1"), ("U4", "19")), ("C53.VBAT - U4.19", ("C53", "1"), ("U4", "19")), ("C51 - U4.4", ("C51", "1"), ("U4", "4")),
         ("R50 - U4.8", ("R50", "1"), ("U4", "8")), ("R50 - U4.7", ("R50", "2"), ("U4", "7")), ("R51 - U4.7", ("R51", "1"), ("U4", "7")), ("R52 - U4.8", ("R52", "1"), ("U4", "8")), ("R52 - U4.10", ("R52", "2"), ("U4", "10")),
         ("R53 - U4.10", ("R53", "1"), ("U4", "10")), ("R53 - U4.11", ("R53", "2"), ("U4", "11")), ("R54 - U4.11", ("R54", "1"), ("U4", "11")), ("R55 - U4.8", ("R55", "1"), ("U4", "8")), ("R55 - U4.12", ("R55", "2"), ("U4", "12")), ("R56 - U4.12", ("R56", "1"), ("U4", "12"))]
rep = []
for name, a, b in LOOPS:
    p, q = pad(*a), pad(*b)
    if p and q: rep.append((name, math.hypot(p[2] - q[2], p[3] - q[3])))
F = lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", s)
W, H = int((X1 - X0) * S), int((Y1 - Y0) * S); im = Image.new("RGB", (W, H), (252, 252, 252)); d = ImageDraw.Draw(im, "RGBA")
P = lambda x, y: ((x - X0) * S, (y - Y0) * S)
for bt, col in ((NOM, (60, 90, 170)), ):
    for r in bt: d.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=(180, 200, 235, 70), outline=col, width=3)
for r in OUTER: d.rectangle([P(r[0], r[1]), P(r[2], r[3])], outline=(150, 150, 150), width=2)
NETC = {"GND": (80, 80, 80), "VBAT": (200, 40, 40), "/BATT": (230, 110, 0), "+3V3": (0, 140, 70), "/SOLAR_IN": (180, 0, 200), "/LBOOST": (0, 120, 220), "/LBUCK": (0, 170, 200), "VBUS": (150, 100, 40)}
for r, (pads, body) in G.items():
    fixed = r in FIXED
    d.rectangle([P(body[0], body[1]), P(body[2], body[3])], fill=(200, 200, 205, 60) if fixed else (255, 230, 170, 50), outline=(110, 110, 120) if fixed else (200, 150, 30), width=1)
    for n, net, cx, cy, hx, hy in pads:
        c = NETC.get(net, (120, 120, 160) if net else (200, 200, 200)); d.rectangle([P(cx - hx, cy - hy), P(cx + hx, cy + hy)], fill=c + (170,), outline=c + (255,))
        if hx > 0.2 and hy > 0.2 and S >= 60: d.text(P(cx, cy), n, font=F(9), fill=(255, 255, 255), anchor="mm")
    if not fixed or r in ("J2",):
        bx, by = P((body[0] + body[2]) / 2, (body[1] + body[3]) / 2); d.text((bx, by), r, font=F(13), fill=(0, 0, 0), anchor="mm")
for name, a, b in LOOPS:
    p, q = pad(*a), pad(*b)
    if p and q: d.line([P(p[2], p[3]), P(q[2], q[3])], fill=(0, 0, 0, 90), width=1)
y = 6
for t in (["issues: none"] if not issues else ["issues:"] + issues[:14]): d.text((8, y), t, font=F(12), fill=(200, 0, 0) if issues else (0, 120, 0)); y += 15
im.save(out)
print("\n".join(issues) if issues else "no issues"); print("; ".join("%s %.1f" % (n, v) for n, v in rep))
