"""j2_options.py OUT.png : top view of the USB-C receptacle J2 at the rim for several east shifts: face line, mounting-peg holes against the ROW0 lane, shell pads against the ROW8 lane vias, plug overmold keep-out (12.35 mm wide, 1.85 mm in front of the face, GCT drawing + USB-IF compliance document)."""
import sys, math
from PIL import Image, ImageDraw, ImageFont
S = 60; X0, Y0, X1, Y1 = 109.0, 91.0, 129.0, 109.0
W, H = int((X1 - X0) * S), int((Y1 - Y0) * S); im = Image.new("RGB", (W, H), (250, 250, 250)); d = ImageDraw.Draw(im, "RGBA")
F = lambda s: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", s)
P = lambda x, y: ((x - X0) * S, (y - Y0) * S)
def circ(r, **kw): d.ellipse([P(100 - r, 100 - r), P(100 + r, 100 + r)], **kw)
d.rectangle([P(X0, Y0), P(X1, Y1)], fill=(236, 240, 236))
circ(21.05, fill=(255, 255, 255), outline=(60, 60, 60), width=4); circ(20.75, outline=(190, 190, 190), width=1)
d.rectangle([P(121.05, Y0), P(X1, Y1)], fill=(250, 250, 250))
circ(21.05, outline=(60, 60, 60), width=4)
# ring lanes
circ(14.63, outline=(200, 90, 0, 255), width=3); d.text(P(110.0, 107.6), "orange: ROW0 lane (In2), r 14.63", font=F(13), fill=(200, 90, 0))
circ(19.57, outline=(0, 120, 160, 255), width=3); d.text(P(110.0, 108.2), "blue circle: ROW8 lane, r 19.57 (its two via taps are the small rings)", font=F(13), fill=(0, 120, 160))
for vx, vy in ((118.76, 94.44), (119.03, 104.57)): d.ellipse([P(vx - .15, vy - .15), P(vx + .15, vy + .15)], outline=(0, 120, 160), width=2)
LEG = []
opts = [(0.0, (110, 110, 110), "now (face 1.33 inside the rim at y=100)"), (0.85, (30, 90, 200), "+0.85: corners on the rim"), (1.1, (30, 150, 60), "+1.1: halfway"), (1.5, (210, 30, 30), "+1.5: first shift that clears the ROW0 lane with the pegs")]
for s, col, lab in opts:
    face = 119.725 + s; x0 = face - 7.35
    d.rectangle([P(x0, 100 - 4.47), P(face, 100 + 4.47)], outline=col + (255,), width=3)
    for sy in (-1, 1):
        px = 113.445 + s; py = 100 + sy * 2.89
        d.ellipse([P(px - .325, py - .325), P(px + .325, py + .325)], fill=col + (90,), outline=col + (255,), width=2)
        d.ellipse([P(px - .525, py - .525), P(px + .525, py + .525)], outline=col + (255,), width=1)
        for dx in (117.03, 113.09):
            qx = dx + s; qy = 100 + sy * 5.11; d.rectangle([P(qx - 1.0, qy - 1.09), P(qx + 1.0, qy + 1.09)], outline=col + (200,), width=1)
    r = math.hypot(113.445 + s - 100, 2.89)
    LEG.append((col, '%s   pegs at r %.2f' % (lab, r)))
d.text((10, 8), "USB-C J2 at the rim - top view (back side, as in KiCad)", font=F(18), fill=(0, 0, 0))
y0 = 40
for col, t in LEG: d.rectangle([12, y0 + 2, 28, y0 + 14], outline=col, width=3); d.text((36, y0), t, font=F(13), fill=col); y0 += 20
d.text((12, y0 + 6), "circles at the pegs: hole + 0.2 mm clearance; the orange lane may not touch a circle", font=F(13), fill=(60, 60, 60))
d.text((12, y0 + 26), "squares at y +-5.1: the four shell pads; rim = heavy black circle, thin circle = 0.3 mm copper clearance", font=F(13), fill=(60, 60, 60))
im.save(sys.argv[1]); print("ok")
