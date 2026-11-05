"""composite.py BOARD OUT.png x0 y0 x1 y1 ppmm [net,net,...] : all three copper layers in ONE picture (front red, inner green, back blue, multiplied so every trace stays visible), pad labels from the back, optional highlighted nets (thick outline in black-orange)"""
import sys, json, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageChops
from kirender import render
board, out = sys.argv[1], sys.argv[2]; box = tuple(map(float, sys.argv[3:7])); ppm = float(sys.argv[7]); hi = sys.argv[8].split(",") if len(sys.argv) > 8 else []
K = "C:/Program Files/KiCad/10.0/bin/"
layers = {"F.Cu": (235, 70, 70), "In1.Cu": (60, 190, 90), "B.Cu": (70, 110, 235)}
base = None
for L, col in layers.items():
    svg = out + "." + L[:2] + ".svg"
    subprocess.run([K + "kicad-cli.exe", "pcb", "export", "svg", "--layers", L + ",Edge.Cuts", "--exclude-drawing-sheet", "--page-size-mode", "2", "--mode-single", "--output", svg, board], capture_output=True)
    im = render(svg, *box, ppm).convert("L")
    # KiCad draws copper in its layer colour on white: anything not white is copper
    mask = im.point(lambda v: 255 if v < 245 else 0)
    tint = Image.new("RGB", im.size, (255, 255, 255)); tint.paste(Image.new("RGB", im.size, col), mask=mask)
    base = tint if base is None else ImageChops.multiply(base, tint)
    os.remove(svg)
subprocess.run([K + "python.exe", os.path.join(os.path.dirname(os.path.abspath(__file__)), "dumpparts.py"), board, out + ".parts.json"], capture_output=True)
P = json.load(open(out + ".parts.json")); d = ImageDraw.Draw(base)
F = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)
if hi:
    G = json.load(open(out + ".g.json")) if os.path.exists(out + ".g.json") else None
for r, f in P.items():
    for num, net, x, y in f["pads"]:
        px, py = (x - box[0]) * ppm, (y - box[1]) * ppm
        if 0 <= px < base.width and 0 <= py < base.height and r[0] not in "HMS" and net and f["back"]:
            d.text((px, py), "%s.%s %s" % (r, num, net.lstrip("/")), fill=(0, 0, 0), font=F, anchor="mm", stroke_width=2, stroke_fill=(255, 255, 255))
base.save(out); os.remove(out + ".parts.json")
