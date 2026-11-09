"""make_models.py OUT_DIR : the project's own 3D models (STEP, coloured), built from data-sheet dimensions.  Needs build123d (pip install build123d; optionally set PYLIB to a folder holding it).
  usbc_gct_usb4110.step   USB-C receptacle GCT USB4110 from GCT's drawing (8.94 x 7.35 x 3.26 mm shell with the 8.34 x 2.56 mm opening, mid plate, side tails, 12 contact tails, 2 pegs)
  qfn48_6x6_ep4p2.step    AVR128DB48 VQFN-48 6LX: 6.0 x 6.0 x 0.85 mm, 0.4 mm pitch, 4.2 x 4.2 mm exposed pad
  piezo_pkmcs0909.step    Murata PKMCS0909E4000-R1: 9.0 x 9.0 x 1.9 mm block (data sheet envelope)
  cell_kxob25.step        Anysolar KXOB25-05X3TF solar cell: 23 x 8 x 1.2 mm block (data sheet envelope)
  lipo_501515.step        TinyCircuits ASR00011 / 501515 70 mAh pouch: 15 x 15 x 5 mm block (data sheet nominal; +-2 / +-3 / +-0.5 mm tolerances), no wires
Model frame = KiCad's: x right, y up (= footprint -y), z up from the board surface (a part on the back is flipped by KiCad).   Written 2026-11-05."""
import sys, os
if os.environ.get("PYLIB"): sys.path.insert(0, os.environ["PYLIB"])
from build123d import Box, Cylinder, Compound, Pos, Color, export_step, fillet, Plane, Location, Axis, Align
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
C = Align.CENTER; MIN = Align.MIN
def box(x0, y0, z0, x1, y1, z1, rgb, label=""):
    b = Box(x1 - x0, y1 - y0, z1 - z0, align=(MIN, MIN, MIN)); b = Pos(x0, y0, z0) * b; b.color = Color(*rgb); b.label = label; return b
def save(name, parts):
    comp = Compound(children=parts, label=name); export_step(comp, os.path.join(out, name + ".step")); print("wrote", name)

STEEL = (0.72, 0.73, 0.76); BLACK = (0.08, 0.08, 0.09); GOLD = (0.85, 0.68, 0.25)
# ---- USB-C GCT USB4110 (model y = -footprint y: the opening is at y = -3.675, the contact tails at y = +3.68)
L, W, H, Z0 = 7.35, 8.94, 3.26, 0.10
shell = Pos(0, 0, (Z0 + H) / 2) * Box(W, L, H - Z0)
shell = fillet(shell.edges().filter_by(Axis.Y), 0.9); shell.color = Color(*STEEL)
cav = Box(8.34, 6.45, 2.56)                                    # opening: 8.34 x 2.56 mm, 6.45 mm deep from the front face
cav = fillet(cav.edges().filter_by(Axis.Y), 1.2)
cav = Pos(0, -L / 2 + 6.45 / 2, (Z0 + H) / 2) * cav
shell = shell - cav; shell.color = Color(*STEEL)
tongue = box(-3.3, -L / 2 + 0.7, (Z0 + H) / 2 - 0.35, 3.3, -L / 2 + 6.45, (Z0 + H) / 2 + 0.35, BLACK, "mid plate")
parts = [shell, tongue]
for sx in (-1, 1):
    for yc in (3.105, -0.825):                                  # shell tails at the footprint's SH pads
        x0, x1 = (4.2, 5.65) if sx > 0 else (-5.65, -4.2)
        parts.append(box(x0, yc - 1.0, 0.0, x1, yc + 1.0, 0.2, STEEL, "tail"))
    c = Pos(sx * 2.89, 2.605, (-1.42 + Z0) / 2) * Cylinder(0.25, Z0 + 1.42); c.color = Color(*STEEL); parts.append(c)   # pegs (0.65 mm holes)
for x in (-3.2, -2.4, -1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75, 2.4, 3.2):
    parts.append(box(x - 0.15, 3.0, 0.0, x + 0.15, 4.0, 0.15, GOLD, "contact tail"))
save("usbc_gct_usb4110", parts)

# ---- VQFN-48 6x6 (6LX)
parts = [box(-3.0, -3.0, 0.03, 3.0, 3.0, 0.83, BLACK, "body"), box(-2.1, -2.1, 0.0, 2.1, 2.1, 0.03, STEEL, "exposed pad")]
for i in range(12):
    p = -2.2 + 0.4 * i
    parts += [box(p - 0.1, 2.6, 0.0, p + 0.1, 3.0, 0.2, STEEL, "lead"), box(p - 0.1, -3.0, 0.0, p + 0.1, -2.6, 0.2, STEEL, "lead"),
              box(2.6, p - 0.1, 0.0, 3.0, p + 0.1, 0.2, STEEL, "lead"), box(-3.0, p - 0.1, 0.0, -2.6, p + 0.1, 0.2, STEEL, "lead")]
parts.append(box(-3.0, 2.4, 0.83, -2.4, 3.0, 0.84, STEEL, "pin 1 mark"))
save("qfn48_6x6_ep4p2", parts)

# ---- blocks
save("piezo_pkmcs0909", [box(-4.5, -4.5, 0.0, 4.5, 4.5, 1.9, (0.18, 0.18, 0.20), "piezo")])
save("cell_kxob25", [box(-11.5, -4.0, 0.05, 11.5, 4.0, 1.25, (0.10, 0.16, 0.38), "solar cell")])
save("lipo_501515", [box(-7.5, -7.5, 0.0, 7.5, 7.5, 5.0, (0.82, 0.83, 0.86), "LiPo pouch")])
