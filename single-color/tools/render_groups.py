"""Low-res colour-coded placement picture (front | back).  usage: render_groups.py grid.json out.png title [bodyfront|bodyback x y w h]..."""
import json, math, sys
from PIL import Image, ImageDraw, ImageFont
d = json.load(open(sys.argv[1]))
out, title = sys.argv[2], sys.argv[3]
GR = {}
for refs, col in ((["C10", "C11", "C12", "C20", "C21", "Y1"], (0, 200, 255)),
                  (["C50", "C51", "C52", "C53", "C54", "R50", "R51", "R52", "R53", "R54", "R55", "R56"], (255, 150, 0)),
                  (["C30", "C31"], (255, 60, 220)),
                  (["C60", "C61", "C62", "R57", "R58", "R59"], (255, 60, 60)),
                  (["J2"], (255, 235, 0)),
                  (["BZ1", "Q1", "D1", "R60"], (80, 255, 80))):
    for r in refs:
        GR[r] = col
S = 17
X0, Y0, R = 100, 100, 22.5
Wp = int(2 * R * S)
img = Image.new("RGB", (Wp * 2 + 30, Wp + 80), (22, 22, 26))
dr = ImageDraw.Draw(img)
try:
    ft = ImageFont.truetype("arial.ttf", 15)
except Exception:
    ft = ImageFont.load_default()
bodies = sys.argv[4:]
for side, ox in (("F.Cu", 10), ("B.Cu", Wp + 20)):
    def P(x, y):
        if side == "B.Cu":
            x = 2 * X0 - x                    # mirror: view the back as if flipped over
        return (ox + (x - X0 + R) * S, 70 + (y - Y0 + R) * S)
    cx, cy = P(100, 100)
    dr.ellipse([cx - 21.75 * S, cy - 21.75 * S, cx + 21.75 * S, cy + 21.75 * S], outline=(120, 120, 130), width=2)
    for p in d["pads"]:
        if p["layer"] != side:
            continue
        ref = p["ref"].split(".")[0]
        col = GR.get(ref, (95, 95, 100) if ref[0] not in "HMSI" or ref.startswith("IND") is False and not ref[1:].isdigit() else (70, 70, 74))
        if ref[0] in "HMS" and ref[1:].isdigit() or ref.startswith("IND"):
            col = (60, 60, 66)
        dr.polygon([P(x, y) for x, y in p["pts"]], fill=col)
    for i in range(0, len(bodies), 5):
        sd, bx, by, bw, bh = bodies[i], *map(float, bodies[i + 1:i + 5])
        if (sd in ("bodyfront",)) == (side == "F.Cu"):
            (a, b_), (c, e) = P(bx - bw / 2, by - bh / 2), P(bx + bw / 2, by + bh / 2)
            dr.rectangle([min(a, c), min(b_, e), max(a, c), max(b_, e)], outline=(80, 255, 80) if sd.startswith("body") else (90, 150, 255), width=2)
    # labels for grouped parts
    seen = set()
    for p in d["pads"]:
        if p["layer"] != side:
            continue
        ref = p["ref"].split(".")[0]
        if ref in GR and ref not in seen:
            seen.add(ref)
            x = sum(q[0] for q in p["pts"]) / len(p["pts"]); y = sum(q[1] for q in p["pts"]) / len(p["pts"])
            px, py = P(x, y)
            dr.text((px + 4, py - 14), ref, fill=GR[ref], font=ft)
    dr.text((ox, 46), "FRONT" if side == "F.Cu" else "BACK (seen flipped, buttons side up = left/right mirrored)", fill=(220, 220, 220), font=ft)
dr.text((10, 4), title, fill=(255, 255, 255), font=ft)
leg = [("MCU/crystal decoupling", (0, 200, 255)), ("BQ25570 support", (255, 150, 0)), ("IMU decoupling", (255, 60, 220)), ("dummy (no net)", (255, 60, 60)), ("tag-connect J2", (255, 235, 0)), ("new buzzer parts", (80, 255, 80))]
x = 10
for t, c in leg:
    dr.rectangle([x, 28, x + 12, 40], fill=c); dr.text((x + 16, 26), t, fill=(220, 220, 220), font=ft); x += 16 + len(t) * 8 + 14
img.save(out)
print("saved", out, img.size)
