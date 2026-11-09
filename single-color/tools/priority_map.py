"""priority_map.py BOARD OUT_PREFIX : colour-coded family pictures with a "keep close" indicator (system python; calls priority_dump.py with KiCad python).
Families (fill): EVERY footprint on the board is coloured: orange = solar charger and cell pads, purple = USB-C corner and charger, blue = battery clips, green = MCU, cyan = 32 kHz crystal, magenta = IMU and I2C pull-ups, brown = piezo, yellow = buttons, lime = mode indicators, grey = LED matrix and its resistors, light grey = dummy parts.
Indicator per part: badge number = the data-sheet priority within its chip (1 = keep closest; BQ25570: CBYP / CSTOR, CIN, L1, COUT, L2), H = high-impedance node (short trace, away from switching copper),
star = suggested for tightening; outline and distance line colour = straight pad-to-pin distance against the group's limit (green within, amber up to twice, red beyond); label = straight distance
and (in brackets) the copper path found by walking the net through vias.   Writes OUT_PREFIX-overview.png, OUT_PREFIX-back-power.png, OUT_PREFIX-front-mcu.png and prints the table."""
import sys, os, json, math, heapq, subprocess, collections
from PIL import Image, ImageDraw, ImageFont
from kirender import render
board, prefix = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__)); K = "C:/Program Files/KiCad/10.0/bin/"
gj = prefix + ".geom.json"
subprocess.run([K + "python.exe", os.path.join(HERE, "priority_dump.py"), board, gj], capture_output=True)
G = json.load(open(gj)); os.remove(gj); P = G["parts"]

FAM = {"solar": ((255, 150, 0), "Solar charger: U4, C50-C54, R50-R56, L1, L2, solar cell pads SC1+ / SC1-"), "usb": ((150, 60, 220), "USB-C corner: J2, charger U5, D50, D51, R68-R72, C55, C56"),
       "batt": ((30, 100, 235), "Battery clips J1, J1B"), "mcu": ((0, 170, 80), "Microcontroller U1 and its power capacitors C10-C13"), "xtal": ((0, 190, 220), "32 kHz crystal block Y1, C20, C21"),
       "imu": ((230, 60, 190), "IMU U2, its capacitors C30 / C31, I2C pull-ups R20 / R21"), "buzz": ((150, 90, 40), "Piezo buzzer BZ1"), "btn": ((240, 210, 0), "Buttons SW1, SW2"),
       "ind": ((140, 210, 0), "Mode indicator LEDs IND1-IND7"), "led": ((140, 140, 150), "LED matrix (hour / minute / second LEDs) and column resistors R1-R12"), "dummy": ((200, 200, 205), "Dummy parts with no net (R57-R67)")}
def family(ref, val, nets):
    if ref in ("U4", "L1", "L2", "SC1+", "SC1-") or (ref[:1] == "C" and ref[1:] in ("50", "51", "52", "53", "54")) or (ref[:1] == "R" and ref[1:] in ("50", "51", "52", "53", "54", "55", "56")): return "solar"
    if ref in ("J2", "U5", "D50", "D51", "R68", "R69", "R70", "R71", "R72", "C55", "C56"): return "usb"
    if ref in ("J1", "J1B"): return "batt"
    if ref in ("U1", "C10", "C11", "C12", "C13"): return "mcu"
    if ref in ("Y1", "C20", "C21"): return "xtal"
    if ref in ("U2", "C30", "C31", "R20", "R21"): return "imu"
    if ref == "BZ1": return "buzz"
    if ref in ("SW1", "SW2"): return "btn"
    if ref.startswith("IND"): return "ind"
    if (ref[:1] in "MSH" and val.startswith("LED")) or (ref[:1] == "R" and ref[1:].isdigit() and 1 <= int(ref[1:]) <= 12): return "led"
    if not any(nets): return "dummy"
    return None
NAME = {"U1": "MCU", "U2": "IMU", "U4": "BQ25570", "U5": "BQ21040", "J1": "LiPo clip", "J1B": "LiPo clip", "J2": "USB-C", "BZ1": "piezo", "SW1": "button", "SW2": "button", "Y1": "crystal", "SC1+": "cell +", "SC1-": "cell -"}
# ref: (family, chip it serves, badge, limit in mm for green)
S = {}
for r, b_ in (("C52", "1"), ("C53", "1"), ("C50", "2"), ("L1", "3"), ("C54", "4"), ("L2", "5")): S[r] = ("solar", "U4", b_, 3.0)
for r in ("C51", "R50", "R51", "R52", "R53", "R54", "R55", "R56"): S[r] = ("solar", "U4", "H", 3.0)
for r in ("C10", "C11", "C13"): S[r] = ("mcu", "U1", "1", 1.5)
for r in ("Y1", "C20", "C21"): S[r] = ("xtal", "U1", "1", 2.0)
for r in ("C30", "C31"): S[r] = ("imu", "U2", "1", 1.5)
S["D51"] = ("usb", "J2", "1", 3.0)
for r in ("C55", "C56"): S[r] = ("usb", "U5", "1", 3.0)
STAR = {"C50", "C54"}

# ---- copper walk
R_VIA, R_PAD = 0.17, 0.30
adj = collections.defaultdict(list)
key = lambda n, l, x, y: (n, l, round(x * 1000), round(y * 1000))
for l, n, x1, y1, x2, y2, L in G["trk"]:
    a, c = key(n, l, x1, y1), key(n, l, x2, y2); adj[a].append((c, L)); adj[c].append((a, L))
nodes_by_net = collections.defaultdict(list)
for k in adj: nodes_by_net[k[0]].append(k)
def near(net, x, y, r): return [k for k in nodes_by_net.get(net, []) if (k[2] / 1000 - x) ** 2 + (k[3] / 1000 - y) ** 2 <= r * r]
for n, x, y in G["vias"]:
    ns = near(n, x, y, R_VIA)
    for a in ns:
        for c in ns:
            if a != c: adj[a].append((c, 0.0))
def walk(net, xa, ya, xb, yb):
    src = near(net, xa, ya, R_PAD); T = set(near(net, xb, yb, R_PAD))
    if not src or not T: return None
    dist = {k: 0.0 for k in src}; pq = [(0.0, i, k) for i, k in enumerate(src)]; cnt = len(src)
    while pq:
        d, _, k = heapq.heappop(pq)
        if k in T: return d
        if d > dist.get(k, 1e9): continue
        for k2, w in adj[k]:
            nd = d + w
            if nd < dist.get(k2, 1e9): dist[k2] = nd; cnt += 1; heapq.heappush(pq, (nd, cnt, k2))
    return None

# ---- measurements: every non-GND pad of the part to the nearest same-net pad of its chip
M = {}
for ref, (fam, chip, badge, lim) in S.items():
    if ref not in P: continue
    lines = []
    for num, net, x, y in P[ref]["pads"]:
        if not net or net == "GND": continue
        cand = [(math.hypot(x - tx, y - ty), tn, tx, ty) for tn, tnet, tx, ty in P[chip]["pads"] if tnet == net and tn not in ("49", "EP", "MP")]
        if not cand: continue
        d, tn, tx, ty = min(cand); w = walk(net, x, y, tx, ty)
        lines.append(dict(pad=num, net=net, pin=tn, d=d, w=w, a=(x, y), b=(tx, ty)))
    if lines: M[ref] = dict(lines=lines, worst=max(l["d"] for l in lines))
FAMOF = {r: family(r, v['value'], [p[1] for p in v['pads']]) for r, v in P.items()}
print('parts without a family:', [r for r, f in FAMOF.items() if f is None])
def verdict(ref):
    lim = S[ref][3]; w = M[ref]["worst"]
    return (40, 170, 60) if w <= lim else ((235, 160, 0) if w <= 2 * lim else (215, 30, 30))
print("%-4s %-5s %-6s %-30s %s" % ("part", "chip", "badge", "straight mm (copper mm)", "verdict"))
for ref in sorted(M, key=lambda r: (S[r][1], S[r][2], r)):
    v = verdict(ref); print("%-4s %-5s %-6s %-30s %s" % (ref, S[ref][1], S[ref][2], " / ".join("%.1f (%s)" % (l["d"], "%.1f" % l["w"] if l["w"] is not None else "?") for l in M[ref]["lines"]), {(40, 170, 60): "within", (235, 160, 0): "amber", (215, 30, 30): "far"}[v]))

# ---- drawing
LAY = {"back": ("B.Cu", (150, 175, 225)), "front": ("F.Cu", (232, 150, 150))}
svgs = {}
def base(side, box, ppm):
    ln, col = LAY[side]
    if side not in svgs:
        svg = prefix + "." + side + ".svg"
        subprocess.run([K + "kicad-cli.exe", "pcb", "export", "svg", "--layers", ln + ",Edge.Cuts", "--exclude-drawing-sheet", "--page-size-mode", "2", "--mode-single", "--output", svg, board], capture_output=True); svgs[side] = svg
    im = render(svgs[side], *box, ppm).convert("L"); mask = im.point(lambda v: 255 if v < 245 else 0)
    out = Image.new("RGB", im.size, (252, 252, 252)); pale = Image.new("RGB", im.size, tuple(int(c * 0.45 + 255 * 0.55) for c in col)); out.paste(pale, mask=mask); return out
FB = lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", s)
def panel(side, box, ppm, fs):
    img = base(side, box, ppm).convert("RGBA"); ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); f = FB(fs)
    px = lambda x, y: ((x - box[0]) * ppm, (y - box[1]) * ppm)
    inbox = lambda bx: bx[2] >= box[0] and bx[0] <= box[2] and bx[3] >= box[1] and bx[1] <= box[3]
    allp = {r: v for r, v in P.items() if v["box"] and v["back"] == (side == "back") and inbox(v["box"]) and FAMOF[r]}
    order = sorted(allp, key=lambda r: (0 if FAMOF[r] in ("led", "dummy") else 1 if r not in M else 2))
    for r in order:
        fam = FAMOF[r]; x0, y0, x1, y1 = allp[r]["box"]; m = 0.1 if fam not in ("led", "dummy") else 0.0
        a_, b_ = px(x0 - m, y0 - m), px(x1 + m, y1 + m); alpha = 70 if fam in ("led", "dummy") else 120
        if r in M: d.rectangle([a_, b_], fill=FAM[fam][0] + (alpha,), outline=verdict(r) + (255,), width=max(3, int(ppm / 12)))
        else: d.rectangle([a_, b_], fill=FAM[fam][0] + (alpha,), outline=((60, 60, 70, 255) if fam not in ("led", "dummy") else FAM[fam][0] + (200,)), width=(2 if fam in ("led", "dummy") else 3))
    mine = [r for r in M if r in allp]
    for r in mine:
        for l in M[r]["lines"]:
            d.line([px(*l["a"]), px(*l["b"])], fill=verdict(r) + (255,), width=max(2, int(ppm / 20)))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img); placed = []
    labelled = [r for r in allp if FAMOF[r] not in ("led", "dummy") or r in M]
    boxes = [(px(allp[r]["box"][0], allp[r]["box"][1]), px(allp[r]["box"][2], allp[r]["box"][3])) for r in allp if FAMOF[r] not in ("led", "dummy")]
    def free(rc):
        if rc[0] < 0 or rc[1] < 0 or rc[2] > img.width or rc[3] > img.height: return False
        return all(rc[2] < q[0] or rc[0] > q[2] or rc[3] < q[1] or rc[1] > q[3] for q in placed)
    for r in sorted(labelled, key=lambda r: (allp[r]["box"][1], allp[r]["box"][0])):
        if r in M:
            ls = M[r]["lines"]; txt = "%s  %s mm" % (r, "/".join("%.1f" % l["d"] for l in ls))
            if any(l["w"] is not None for l in ls): txt += "  (%s)" % "/".join("%.1f" % l["w"] if l["w"] is not None else "?" for l in ls)
            v = verdict(r)
        else: txt = r + (" " + NAME[r] if r in NAME else ""); v = (60, 60, 70)
        tw = d.textlength(txt, font=f); th = fs + 6; (ax, ay), (bx, by) = px(allp[r]["box"][0], allp[r]["box"][1]), px(allp[r]["box"][2], allp[r]["box"][3]); cx, cy = (ax + bx) / 2, (ay + by) / 2
        spot = None
        for ring in (6, 30, 70, 120, 180, 260):
            for ang in (-45, 45, 0, 180, -90, 90, -135, 135, -20, 20, 160, -160):
                ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                ex = (bx - ax) / 2 + ring if abs(ux) > 0.3 else 0; ey = (by - ay) / 2 + ring if abs(uy) > 0.3 else 0
                lx = cx + (ex * (1 if ux > 0.3 else -1 if ux < -0.3 else 0)); ly = cy + (ey * (1 if uy > 0.3 else -1 if uy < -0.3 else 0))
                rc0 = (lx - (0 if ux > 0.3 else tw + 10 if ux < -0.3 else (tw + 10) / 2), ly - (0 if uy > 0.3 else th if uy < -0.3 else th / 2))
                rc = (rc0[0], rc0[1], rc0[0] + tw + 10, rc0[1] + th)
                if free(rc) and all(rc[2] < q0[0] - 2 or rc[0] > q1[0] + 2 or rc[3] < q0[1] - 2 or rc[1] > q1[1] + 2 for q0, q1 in boxes): spot = rc; break
            if spot: break
        spot = spot or (cx + 40, cy + 40, cx + 40 + tw + 10, cy + 40 + th); placed.append(spot)
        if not (spot[0] <= cx <= spot[2] and spot[1] <= cy <= spot[3]): d.line([(cx, cy), ((spot[0] + spot[2]) / 2, (spot[1] + spot[3]) / 2)], fill=(60, 60, 60, 255), width=1)
        d.rectangle(spot, fill=(255, 255, 255, 235), outline=v + (255,), width=(3 if r in M else 2)); d.text((spot[0] + 5, spot[1] + 2), txt, fill=(0, 0, 0, 255), font=f)
        if r in M:
            br = int(fs * 0.78); bxy = (ax - 2, ay - 2); d.ellipse([bxy[0] - br, bxy[1] - br, bxy[0] + br, bxy[1] + br], fill=(30, 30, 40, 255), outline=v + (255,), width=3)
            d.text(bxy, S[r][2], fill=(255, 255, 255, 255), font=f, anchor="mm")
            if r in STAR: d.text((bx + 2, ay - 2), "*", fill=(220, 0, 0, 255), font=FB(fs * 3), anchor="lm")
    return img.convert("RGB")
def legend(w, title):
    f = FB(15); h = 352; im = Image.new("RGB", (w, h), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((8, 4), "COLOUR FILL = which family the part belongs to", font=FB(14), fill=(90, 90, 90))
    for i, (fam, (col, txt)) in enumerate(FAM.items()):
        cx, cy = (8, 24 + 19 * i) if i < 6 else (600, 24 + 19 * (i - 6)); d.rectangle([cx, cy + 2, cx + 18, cy + 16], fill=col, outline=(0, 0, 0)); d.text((cx + 26, cy), txt, font=FB(14), fill=(0, 0, 0))
    # key panel: three things drawn on every part that serves a chip pin
    kx, ky = 8, 150
    d.text((kx, ky - 4), "KEY to the marks on the parts that must stay close to a chip pin", font=FB(14), fill=(90, 90, 90))
    # example: badge
    d.rectangle([kx + 10, ky + 30, kx + 70, ky + 62], fill=(255, 150, 0), outline=(40, 170, 60), width=5); d.ellipse([kx - 2, ky + 18, kx + 22, ky + 42], fill=(30, 30, 40), outline=(40, 170, 60), width=3); d.text((kx + 10, ky + 30), "2", font=FB(15), fill=(255, 255, 255), anchor="mm")
    d.text((kx + 85, ky + 24), "1) The small DARK CIRCLE on the corner holds a NUMBER or the letter H:", font=FB(14), fill=(0, 0, 0))
    d.text((kx + 85, ky + 43), "number = the data-sheet priority for sitting close to its chip pin (1 = closest first; BQ25570: CBYP and CSTOR 1, CIN 2, L1 3, COUT 4, L2 5; MCU, IMU, crystal caps 1)", font=FB(13), fill=(0, 0, 0))
    d.text((kx + 85, ky + 60), "H = high-impedance node (divider): short trace, keep away from switching copper", font=FB(13), fill=(0, 0, 0))
    ox = kx + 10
    d.text((kx, ky + 86), "2) The OUTLINE colour of the part box (and its line to the pin) = how far it is now:", font=FB(14), fill=(0, 0, 0))
    for j, (col, t) in enumerate((((40, 170, 60), "green: within the limit"), ((235, 160, 0), "amber: up to twice the limit"), ((215, 30, 30), "red: farther than that"))):
        x = kx + 680 + j * 250; d.rectangle([x, ky + 84, x + 36, ky + 104], fill=(255, 150, 0), outline=col, width=5); d.text((x + 46, ky + 86), t, font=FB(14), fill=(0, 0, 0))
    d.text((kx, ky + 110), "   Limits (straight pad-to-pin): 3 mm solar and USB parts, 1.5 mm MCU and IMU caps, 2 mm crystal.   The label gives the straight distance in mm, then (the copper path in mm).", font=FB(13), fill=(0, 0, 0))
    d.text((kx, ky + 130), "3) RED STAR next to a part = suggested for tightening (C50, C54).   Parts with no badge only carry their name; the dark box around a chip (U1, U2, U4, U5, J2) marks the chip the parts serve.", font=FB(14), fill=(0, 0, 0))
    d.text((8, h - 40), title, font=FB(22), fill=(0, 0, 0)); return im
def sheet(panels, title):
    w = max(1260, sum(p.width for p in panels) + 10 * (len(panels) - 1)); hh = max(p.height for p in panels); L = legend(w, title)
    out = Image.new("RGB", (w, L.height + hh), (255, 255, 255)); out.paste(L, (0, 0)); x = 0
    for p in panels: out.paste(p, (x, L.height)); x += p.width + 10
    return out
bb = (78.0, 73.4, 122.0, 126.6)
over = sheet([panel("back", bb, 27, 12), panel("front", bb, 27, 12)], "Overview: BACK (B.Cu, as drawn in KiCad) | FRONT (F.Cu)"); over.save(prefix + "-overview.png")
sheet([panel("back", (84, 88, 116, 112), 56, 15)], "Detail: BACK, power block and USB-C corner").save(prefix + "-back-power.png")
sheet([panel("front", (84, 85, 106, 112), 46, 14)], "Detail: FRONT, MCU decoupling, crystal block and IMU").save(prefix + "-front-mcu.png")
for s in svgs.values(): os.remove(s)
print("written:", prefix + "-overview.png", prefix + "-back-power.png", prefix + "-front-mcu.png")
