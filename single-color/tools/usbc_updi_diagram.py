"""usbc_updi_diagram.py OUT.png : picture of the USB-C receptacle pinout (GCT USB4110, 16 pins) with the board's connections, the UPDI path over the SBU pins, and the SBU-to-VBUS fault path.
Connections taken from hardware/LED Watch - Single Color.kicad_pcb on 2026-11-05 (J2, R72, D50, D51, R68, R69, U1 pin 41).  usage (system python): usbc_updi_diagram.py out.png"""
import sys
from PIL import Image, ImageDraw, ImageFont
F = lambda s, b=True: ImageFont.truetype("C:/Windows/Fonts/%s.ttf" % ("arialbd" if b else "arial"), s)
W, H = 2300, 1500; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
GND = (120, 120, 130); VBUS = (210, 40, 40); CC = (240, 150, 0); UPDI = (30, 110, 235); NC = (200, 200, 205); DAT = (150, 150, 160)
d.text((30, 20), "USB-C receptacle (GCT USB4110, USB 2.0 type, 16 pins): what each pin does and where ours go", font=F(34), fill=(0, 0, 0))
d.text((30, 66), "Standard USB 2.0 (type A/B) has 4 wires: VBUS, D-, D+, GND.  USB-C keeps those four and adds CC (cable and role detect), SBU (sideband) and, on bigger receptacles, SuperSpeed pairs.", font=F(19, False), fill=(60, 60, 60))
# pin rows (viewed from the front of the receptacle: A row on top left to right A1..A12; B row below, B12..B1)
A = [("A1", "GND", GND), ("A4", "VBUS", VBUS), ("A5", "CC1", CC), ("A6", "D+", DAT), ("A7", "D-", DAT), ("A8", "SBU1", UPDI), ("A9", "VBUS", VBUS), ("A12", "GND", GND)]
B = [("B12", "GND", GND), ("B9", "VBUS", VBUS), ("B8", "SBU2", UPDI), ("B7", "D-", DAT), ("B6", "D+", DAT), ("B5", "CC2", CC), ("B4", "VBUS", VBUS), ("B1", "GND", GND)]
x0, y0, w, h, g = 40, 150, 138, 74, 8
def row(pins, y, tag):
    d.text((x0, y - 34), tag, font=F(22), fill=(0, 0, 0))
    for i, (p, s, c) in enumerate(pins):
        x = x0 + i * (w + g); d.rectangle([x, y, x + w, y + h], fill=c, outline=(0, 0, 0), width=3)
        d.text((x + w / 2, y + 22), p, font=F(26), fill=(255, 255, 255), anchor="mm"); d.text((x + w / 2, y + 52), s, font=F(24), fill=(255, 255, 255), anchor="mm")
row(A, y0 + 20, "Row A (front view of the receptacle, left to right)")
row(B, y0 + 190, "Row B (same view; the plug is reversible, so the two rows mirror each other)")
d.text((x0, y0 + 285), "Not on this receptacle: the SuperSpeed pairs (A2/A3, A10/A11, B2/B3, B10/B11).  A shared pair of ground and VBUS pins is doubled for current.", font=F(18, False), fill=(60, 60, 60))
# adjacency warning
xa8 = x0 + 5 * (w + g); xa9 = x0 + 6 * (w + g)
d.rounded_rectangle([xa8 - 6, y0 + 14, xa9 + w + 6, y0 + 20 + h + 8], radius=10, outline=(215, 30, 30), width=5)
xb8 = x0 + 2 * (w + g); xb9 = x0 + 1 * (w + g)
d.rounded_rectangle([xb9 - 6, y0 + 184, xb8 + w + 6, y0 + 190 + h + 8], radius=10, outline=(215, 30, 30), width=5)
d.text((x0 + 3 * (w + g), y0 + 112), "red frames: SBU sits right next to a VBUS pin (0.5 mm pitch)", font=F(19), fill=(215, 30, 30))

# connection diagram
def box(x, y, wd, ht, text, col, tc=(255, 255, 255), fs=22):
    d.rectangle([x, y, x + wd, y + ht], fill=col, outline=(0, 0, 0), width=3)
    for i, t in enumerate(text.split("\n")): d.text((x + wd / 2, y + ht / 2 + (i - (len(text.split("\n")) - 1) / 2) * (fs + 4)), t, font=F(fs), fill=tc, anchor="mm")
def arrow(p, q, col, wd=5, head=True):
    d.line([p, q], fill=col, width=wd)
    if head:
        import math
        a = math.atan2(q[1] - p[1], q[0] - p[0])
        for s in (-0.45, 0.45): d.line([q, (q[0] - 18 * math.cos(a + s), q[1] - 18 * math.sin(a + s))], fill=col, width=wd)
Y = 560
d.text((30, Y - 50), "Where our wires go", font=F(30), fill=(0, 0, 0))
# SBU chain
box(40, Y + 20, 210, 120, "A8  SBU1\nB8  SBU2\n(tied together)", UPDI)
box(380, Y + 40, 170, 80, "R72  1 k", (90, 90, 100))
box(690, Y + 20, 250, 120, "UPDI node", UPDI)
box(1100, Y + 20, 310, 120, "MCU U1 pin 41 (UPDI)\nrun from VBAT 3.0-4.2 V", (0, 150, 80))
arrow((250, Y + 80), (380, Y + 80), UPDI); arrow((550, Y + 80), (690, Y + 80), UPDI); arrow((940, Y + 80), (1100, Y + 80), UPDI)
box(660, Y + 250, 310, 80, "D50 BAT54WS clamp", (90, 90, 100))
arrow((815, Y + 140), (815, Y + 250), (90, 90, 100))
box(1110, Y + 250, 290, 80, "+3V3 rail (buck output)\nIMU, I2C pull-ups", (200, 120, 0), fs=20)
arrow((970, Y + 290), (1110, Y + 290), (90, 90, 100))
d.text((1440, Y + 22), "Why SBU: the UPDI programming interface is ONE wire plus ground,", font=F(21, False), fill=(0, 0, 0))
d.text((1440, Y + 52), "and a USB 2.0 receptacle leaves SBU1/SBU2 free. Both are tied because", font=F(21, False), fill=(0, 0, 0))
d.text((1440, Y + 82), "the plug is reversible (the cable's SBU wire lands on A8 or B8).", font=F(21, False), fill=(0, 0, 0))
d.text((1440, Y + 112), "R72 limits fault current; D50 keeps the node from going above the rail.", font=F(21, False), fill=(0, 0, 0))
d.text((1440, Y + 142), "Needs a cable that carries SBU (charge-only cables do not).", font=F(21, False), fill=(0, 0, 0))
# other pins
for k, (lt, lc, rt, rc, rtc) in enumerate((("A4 B9 A9 B4  VBUS", VBUS, "D51 TVS to GND + U5 charger", (90, 90, 100), (255, 255, 255)), ("A5 CC1   B5 CC2", CC, "5.1 k each to GND (R68, R69)", (90, 90, 100), (255, 255, 255)),
                                         ("A6 A7 B6 B7  D+ D-", DAT, "not connected", NC, (60, 60, 60)), ("A1 B1 A12 B12  GND, shell", GND, "ground plane", (90, 90, 100), (255, 255, 255)))):
    yy = Y + 400 + k * 100
    box(40, yy, 310, 70, lt, lc, fs=20); box(440, yy, 340, 70, rt, rc, tc=rtc, fs=20); arrow((350, yy + 35), (440, yy + 35), lc)
# fault panel
fx = 860; fy = Y + 400
d.rectangle([fx, fy, W - 40, fy + 380], outline=(215, 30, 30), width=5, fill=(255, 245, 245))
d.text((fx + 20, fy + 12), "The case to worry about: SBU shorted to the neighbouring VBUS pin (sweat, debris, bent or damaged cable)", font=F(23), fill=(215, 30, 30))
lines = ["5.0 V on SBU -> R72 1 k -> UPDI node. D50 clamps the node to the +3V3 rail plus about 0.3 V, so the MCU pin itself sees about 3.6 V.",
         "The fault current flows into the +3V3 rail: (5.0 - 3.6) / 1 k = about 1.4 mA. The BQ25570 buck output can only source current, it cannot sink it.",
         "The rail's own load is microamps (IMU, pull-ups), so the rail is pushed up until the current balances: toward about 4.7 V.",
         "That is above the IMU's recommended 3.6 V, and above the MCU's own supply (battery, 3.0-4.2 V) on the I2C pull-up pins.",
         "Clamping to VBAT instead (the MCU's own supply): the pin follows its own supply + 0.3 V, and the battery absorbs 0.5-1.4 mA (it just charges).",
         "CC is safe by design (only 5.1 k resistors behind it). SBU is the one receptacle pin that reaches a silicon pin.",
         "No power-delivery negotiation on CC, so a compliant charger offers 5 V only; 9-20 V would need a damaged or non-compliant source."]
for i, t in enumerate(lines): d.text((fx + 20, fy + 62 + i * 44), t, font=F(20, False), fill=(40, 40, 40))
im.save(sys.argv[1]); print("written", sys.argv[1])
