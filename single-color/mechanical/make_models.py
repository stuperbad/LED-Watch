"""3D-printable test models for the single-colour LED watch (CadQuery).

Writes to ./print/:
  01_pcb_blank.stl              the bare board: exact outline and strap slots from the KiCad board, 1.6 mm thick
  02_pcb_dummy_with_parts.stl   same board plus stand-ins for the big parts (batteries, battery connectors, buzzer on the back;
                                solar cell, MCU, two buttons on the front). Exported FRONT DOWN so it prints with only thin supports.
  03_bumper.stl                 skin-side bumper: a tray under the board that holds the strap against the batteries, snaps onto
                                the strap lugs with four hooks, and comes off again. Print floor-down as exported.
  variants/                     the bumper 0.4 mm tighter and 0.4 mm looser, for finding the right strap squeeze

Coordinates inside the script: X = KiCad x (to the right when looking at the FRONT), Y = -KiCad y (up the page), Z = up out of the
FRONT of the board. The board's back face is z = 0, its front face z = PCB_T. Everything on the back has z < 0.
Board data (outline polygons) comes from outline.json, dumped once from the .kicad_pcb (see README.md).

usage: python make_models.py
"""
import json
import math
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "print")
os.makedirs(os.path.join(OUT, "variants"), exist_ok=True)

# ---------------------------------------------------------------- numbers you may want to change
PCB_T = 1.6                      # board thickness
BATT = (16.5, 16.0, 5.25)        # battery (x, y, thickness): nominal 15 x 15 x 5 plus half the datasheet tolerance (same as the board's keep-out)
BATT_Y = 11.5                    # battery centres at (0, +-BATT_Y)
JST_H = 2.96                     # SM02B-SRSS-TB body height above the board (KiCad 3D model)
BUZ = (9.0, 9.0, 1.9)            # Murata PKMCS0909E4000-R1
CELL = (23.0, 8.0, 1.35)         # Anysolar KXOB25-05X3TF, 1.2 +- 0.3 mm
MCU = (6.0, 6.0, 0.9)            # AVR128DB48 VQFN
BTN = (4.6, 2.8, 1.9)            # KMR2 tactile switch

STRAP_T = 1.75                   # strap thickness (1.5 to 2 mm, compressible)
COMPRESS = 0.30                  # how much the bumper squeezes the strap against the batteries
FLOOR_T = 1.4                    # bumper floor thickness (the part against the skin)
R_OUT = 21.6                     # bumper outside radius (board is 21.0)
WALL_T = 1.4
WALL_GAP = 0.15                  # wall stops this far short of the board's back face
NOTCH_X = 10.6                   # strap exit notches: |x| < NOTCH_X ...
NOTCH_Y = 19.7                   # ... and |y| > NOTCH_Y the floor stops (the strap goes up through the slots there)
WALL_NOTCH_Y = 17.3              # the wall is open from here outwards: the battery corners reach out to R 21.3 there
LUG_X = 12.55                    # strap-lug side edge (from the board outline)
HOOK_Y = 20.2                    # hook centre |y| (the lug side is straight from |y| 17.12 to 23.28)
HOOK_W = 4.5                     # hook width along y
ARM_T = 1.4                      # hook arm thickness
ARM_GAP = 0.30                   # clearance between lug edge and arm
LIP_IN = 0.95                    # how far the hook lip reaches in from the arm (engages 0.65 mm onto the lug top)
LIP_LEN = 1.4                    # lip height incl. the lead-in ramp
LIP_GAP = 0.05                   # play between the lip underside and the board front face
TAB_OUT = 1.3                    # fingernail tab sticking out at the top of each arm

with open(os.path.join(HERE, "outline.json")) as f:
    OUTLINE = json.load(f)       # {"outer": [[x, y], ...], "slots": [[[x, y], ...], ...]} in KiCad coordinates (y down)


def poly(points, z0, h):
    pts = [(x, -y) for x, y in points]
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(h)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def pcb():
    body = poly(OUTLINE["outer"], 0, PCB_T)
    for s in OUTLINE["slots"]:
        body = body.cut(poly(s, -0.5, PCB_T + 1.0))
    return body


def rbox(cx, cy, sx, sy, z0, z1, r=0.0):
    b = cq.Workplane("XY").box(sx, sy, abs(z1 - z0), centered=(True, True, False)).translate((cx, cy, min(z0, z1)))
    if r > 0:
        b = b.edges("|Z").fillet(r)
    return b


def parts():
    p = None
    items = []
    # back (z < 0)
    for sy in (1, -1):
        items.append(rbox(0, sy * BATT_Y, BATT[0], BATT[1], -BATT[2], 0, 1.2))                       # batteries
    items.append(box(-15.2, -11.2, 5.42, 10.38, -JST_H, 0))                                          # J1 (KiCad y -10.38..-5.42)
    items.append(box(-15.5, -11.5, -11.48, -6.52, -JST_H, 0))                                        # J1B (KiCad y 6.52..11.48)
    items.append(rbox(-14.75, -0.3, BUZ[0], BUZ[1], -BUZ[2], 0, 0.8))                                # BZ1 (KiCad y 0.3)
    # front (z > PCB_T)
    items.append(rbox(0, 0, CELL[0], CELL[1], PCB_T, PCB_T + CELL[2], 0.3))                          # solar cell
    items.append(rbox(0, 8.13, MCU[0], MCU[1], PCB_T, PCB_T + MCU[2], 0.2))                          # MCU (KiCad y -8.13)
    for sx in (-1, 1):
        items.append(rbox(sx * 4.45, -9.1, BTN[0], BTN[1], PCB_T, PCB_T + BTN[2], 0.3))              # buttons (KiCad y 9.1)
    for it in items:
        p = it if p is None else p.union(it)
    return p


def bumper(h_batt_strap):
    """h_batt_strap: distance from the board's back face down to the bumper floor's top surface"""
    H = h_batt_strap
    z_floor_top, z_floor_bot = -H, -H - FLOOR_T
    floor = cq.Workplane("XY").workplane(offset=z_floor_bot).circle(R_OUT).extrude(FLOOR_T)
    floor = floor.faces("<Z").edges().fillet(0.8)                                                    # comfortable skin edge
    wall = (cq.Workplane("XY").workplane(offset=z_floor_top).circle(R_OUT).circle(R_OUT - WALL_T)
            .extrude(H - WALL_GAP))
    for sgn in (1, -1):
        lo, hi = (WALL_NOTCH_Y, 40) if sgn > 0 else (-40, -WALL_NOTCH_Y)
        wall = wall.cut(box(-NOTCH_X, NOTCH_X, lo, hi, -H - 5, 5))
        lo, hi = (NOTCH_Y, 40) if sgn > 0 else (-40, -NOTCH_Y)
        floor = floor.cut(box(-NOTCH_X, NOTCH_X, lo, hi, -H - 5, 5))
    body = floor.union(wall)
    # wings under the lug sides, then the hooks
    z_l = PCB_T + LIP_GAP                                                                              # lip underside
    z_top = z_l + LIP_LEN
    ax0 = LUG_X + ARM_GAP                                                                              # arm inner face
    ax1 = ax0 + ARM_T
    xt = ax0 - LIP_IN
    for sx in (1, -1):
        for sy in (1, -1):
            wing = box(NOTCH_X, ax1 + TAB_OUT, HOOK_Y - 3.6, HOOK_Y + 2.8, z_floor_bot, z_floor_top)
            wing = wing.translate((0, 0, 0))
            prof = [(ax0, z_floor_top), (ax1, z_floor_top), (ax1, z_top), (ax0 + 0.15, z_top), (xt, z_l + 0.5), (xt, z_l), (ax0, z_l)]
            arm = (cq.Workplane("XZ").polyline(prof).close().extrude(HOOK_W / 2, both=True)
                   .translate((0, HOOK_Y, 0)))
            tab = box(ax1, ax1 + TAB_OUT, HOOK_Y - HOOK_W / 2, HOOK_Y + HOOK_W / 2, z_top - 0.9, z_top)
            piece = wing.union(arm).union(tab)
            if sx < 0:
                piece = piece.mirror("YZ")
            if sy < 0:
                piece = piece.mirror("XZ")
            body = body.union(piece)
    return body


def save(shape, name, rotate_front_down=False, to_bed=False):
    s = shape
    if rotate_front_down:
        s = s.rotate((0, 0, 0), (1, 0, 0), 180)
    if rotate_front_down or to_bed:
        bb = s.val().BoundingBox()
        s = s.translate((0, 0, -bb.zmin))                                                          # lowest point on the bed (z = 0)
    path = os.path.join(OUT, name)
    cq.exporters.export(s, path, tolerance=0.01, angularTolerance=0.1)
    print("wrote", path)
    return s


if __name__ == "__main__":
    board = pcb()
    save(board, "01_pcb_blank.stl")
    dummy = board.union(parts())
    save(dummy, "02_pcb_dummy_with_parts.stl", rotate_front_down=True)
    H = BATT[2] + STRAP_T - COMPRESS
    save(bumper(H), "03_bumper.stl", to_bed=True)
    save(bumper(H - 0.4), os.path.join("variants", "03_bumper_tighter_minus0.4.stl"), to_bed=True)
    save(bumper(H + 0.4), os.path.join("variants", "03_bumper_looser_plus0.4.stl"), to_bed=True)
    # interference check in the assembled position (bumper vs board + parts; the strap is not modelled)
    clash = bumper(H).intersect(dummy)
    print("bumper / dummy overlap volume (mm^3):", round(clash.val().Volume(), 4) if clash.vals() else 0.0)
