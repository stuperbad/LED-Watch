"""
Parametric LED-ring generator for the single-colour watch.

Run with KiCad's python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" gen_rings.py [--order S,M,H] [--tang-gap 0.5] ...

Clock geometry
  * 60 minute LEDs, 60 second LEDs, 12 hour LEDs, each ring concentric about the board centre.
  * Position k of N is at clock angle theta = k * 360/N degrees clockwise from 12 o'clock
    (minutes/seconds: 6 degree steps; hours: 30 degree steps).
  * Every LED is rotated so its pad axis points RADIALLY (pad 1 = cathode inward, pad 2 = anode outward).
    KiCad orientation (CCW, degrees) = 90 - theta.
  * Only the LED's short side (pad width) counts for spacing around the ring, so rings pack tightly.

Outputs (next to this script):
  rings.kicad_pcb   board with LED footprints + circular edge cut
  rings_report.txt  radii, board diameter, pitches, and the LED position/rotation table
  rings_cpl.csv     placement list (Designator, Mid X, Mid Y, Layer, Rotation)
"""
import argparse, math, os, sys
import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

LIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints\LED_SMD.pretty"
# name -> (footprint, pad-axis length mm, pad width mm) taken from KiCad's own footprints
SIZES = {
    "0201": ("LED_0201_0603Metric", 2 * 0.32 + 0.46, 0.40),
    "0402": ("LED_0402_1005Metric", 2 * 0.485 + 0.59, 0.64),
    "0603": ("LED_0603_1608Metric", 2 * 0.787 + 0.875, 0.95),
    "0805": ("LED_0805_2012Metric", 2 * 0.938 + 0.975, 1.40),
}
RING = {  # key -> (count, prefix, label)
    "S": (60, "S", "seconds"),
    "M": (60, "M", "minutes"),
    "H": (12, "H", "hours"),
}


def solve(order, sizes, tang_gap, rad_gap, center_keepout, edge_margin):
    """order: inner->outer, e.g. ['H','S','M']. Returns radii dict and board radius."""
    radii, prev_outer = {}, center_keepout
    for key in order:
        n = RING[key][0]
        _, length, width = SIZES[sizes[key]]
        r_tang = (width + tang_gap) / (2 * math.sin(math.pi / n))     # neighbours must not touch
        r_rad = prev_outer + rad_gap + length / 2                      # clear the ring inside
        r = max(r_tang, r_rad)
        radii[key] = r
        prev_outer = r + length / 2
    return radii, prev_outer + edge_margin


def tang_min_radius(key, sizes, tang_gap):
    n = RING[key][0]
    _, length, width = SIZES[sizes[key]]
    return (width + tang_gap) / (2 * math.sin(math.pi / n))


def solve_outward(order, sizes, tang_gap, rad_gap, edge_margin, diameter=0.0, free_min=0.0):
    """Pack rings against the board edge, outermost first (order is inner->outer).
    Returns (radii, board_radius, free_centre_radius). If `diameter` is 0 the smallest board that
    satisfies every spacing constraint is used; otherwise rings are pushed out against that edge."""
    def pack(D):
        r_out_edge = D / 2 - edge_margin
        radii = {}
        for key in reversed(order):                 # outermost ring first
            _, length, _ = SIZES[sizes[key]]
            radii[key] = r_out_edge - length / 2
            r_out_edge = radii[key] - length / 2 - rad_gap
        return radii

    def ok(D):
        radii = pack(D)
        inner = order[0]
        _, L, _ = SIZES[sizes[inner]]
        if radii[inner] - L / 2 <= max(0.0, free_min):
            return False
        return all(radii[k] >= tang_min_radius(k, sizes, tang_gap) for k in order)

    lo = 5.0
    D = max(lo, diameter)
    if diameter and not ok(D):
        raise SystemExit(f"diameter {diameter} mm is too small for the spacing constraints")
    if not diameter:
        D = lo
        while not ok(D):
            D += 0.01
    radii = pack(D)
    inner = order[0]
    _, L, _ = SIZES[sizes[inner]]
    return radii, D / 2, radii[inner] - L / 2


def build(args):
    sizes = {"S": args.sec, "M": args.min, "H": args.hr}
    order = args.order.split(",")
    rect = None
    free_min = 0.0
    if args.keepout_rect:
        rw, rh = [float(v) for v in args.keepout_rect.lower().split("x")]
        rect = (rw, rh)
        free_min = math.hypot(rw / 2, rh / 2) + args.keepout_margin      # circle that clears the rectangle's corners
    radii, board_r, free_r = solve_outward(order, sizes, args.tang_gap, args.rad_gap, args.edge_margin, args.diameter, free_min)

    cx, cy = args.cx, args.cy
    board = pcbnew.BOARD()
    rows, lines = [], []
    for key in order:
        n, prefix, label = RING[key]
        fp_name, length, width = SIZES[sizes[key]]
        r = radii[key]
        pitch = 2 * math.pi * r / n
        lines.append(f"{label:8s} {n:3d} x {sizes[key]}  radius {r:6.3f} mm  pitch {pitch:5.2f} mm  "
                     f"copper gap around ring {pitch - width:5.2f} mm")
        for k in range(n):
            theta = k * 360.0 / n
            x = cx + r * math.sin(math.radians(theta))
            y = cy - r * math.cos(math.radians(theta))
            rot = (90.0 - theta) % 360.0
            fp = pcbnew.FootprintLoad(LIB, fp_name)
            fp.SetReference(f"{prefix}{k if key != 'H' else (k if k else 12)}")
            fp.SetValue(f"LED white {sizes[key]}")
            fp.SetPosition(V(F(x), F(y)))
            fp.SetOrientationDegrees(rot)
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
            board.Add(fp)
            rows.append((fp.GetReference(), x, -y, rot, theta))
    # circular board outline
    c = pcbnew.PCB_SHAPE(board)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.Edge_Cuts)
    c.SetStart(V(F(cx), F(cy)))
    c.SetEnd(V(F(cx + board_r), F(cy)))
    c.SetWidth(F(0.1))
    board.Add(c)
    seg_info = []
    if rect:
        rw, rh = rect
        x0, y0, x1, y1 = cx - rw / 2, cy - rh / 2, cx + rw / 2, cy + rh / 2
        for a, b in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)) if False else (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            ln = pcbnew.PCB_SHAPE(board); ln.SetShape(pcbnew.SHAPE_T_SEGMENT); ln.SetLayer(pcbnew.Dwgs_User)
            ln.SetStart(V(F(a[0]), F(a[1]))); ln.SetEnd(V(F(b[0]), F(b[1]))); ln.SetWidth(F(0.15)); board.Add(ln)
        fr = pcbnew.PCB_SHAPE(board); fr.SetShape(pcbnew.SHAPE_T_CIRCLE); fr.SetLayer(pcbnew.Dwgs_User)
        fr.SetStart(V(F(cx), F(cy))); fr.SetEnd(V(F(cx + free_r), F(cy))); fr.SetWidth(F(0.1)); board.Add(fr)
        # the four circular segments between the rectangle's sides and the free circle
        for name, half in (("left/right sides (beyond the %.0f mm width)" % rw, rw / 2), ("top/bottom sides (beyond the %.0f mm height)" % rh, rh / 2)):
            depth = free_r - half
            chord = 2 * math.sqrt(max(free_r ** 2 - half ** 2, 0))
            seg_info.append(f"segment at {name}: depth {depth:.2f} mm x chord {chord:.2f} mm")

    out = os.path.dirname(os.path.abspath(__file__))
    pcbnew.SaveBoard(os.path.join(out, args.name + ".kicad_pcb"), board)
    with open(os.path.join(out, args.name + "_cpl.csv"), "w", encoding="utf8") as f:
        f.write("Designator,Mid X,Mid Y,Layer,Rotation\n")
        for ref, x, y, rot, th in rows:
            f.write(f"{ref},{x:.4f}mm,{y:.4f}mm,Top,{rot:.1f}\n")
    rep = [f"order inner->outer: {order}   sizes: {sizes}",
           f"tangential gap {args.tang_gap} mm, radial gap {args.rad_gap} mm, edge margin {args.edge_margin} mm"]
    rep += lines
    rep.append(f"BOARD DIAMETER: {2 * board_r:.2f} mm (radius {board_r:.2f})")
    rep += seg_info
    rep.append(f"FREE CENTRE (no LEDs): radius {free_r:.2f} mm = {2 * free_r:.2f} mm diameter (a {free_r * math.sqrt(2):.1f} mm square fits)")
    rep.append("")
    rep.append("Designator, clock angle (deg cw from 12), KiCad rotation (deg ccw), x, y")
    rep += [f"{ref},{th:.1f},{rot:.1f},{x:.3f},{-y:.3f}" for ref, x, y, rot, th in rows]
    open(os.path.join(out, args.name + "_report.txt"), "w", encoding="utf8").write("\n".join(rep))
    print("\n".join(rep[: 3 + len(lines) + 1]))
    return 2 * board_r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", default="H,M,S", help="inner->outer ring order using H,M,S (default hours, minutes, seconds outermost)")
    ap.add_argument("--sec", default="0402"); ap.add_argument("--min", default="0603"); ap.add_argument("--hr", default="0805")
    ap.add_argument("--tang-gap", type=float, default=0.5, help="copper gap between neighbouring LEDs around a ring (mm)")
    ap.add_argument("--rad-gap", type=float, default=0.8, help="radial gap between rings, for trace channels (mm)")
    ap.add_argument("--edge-margin", type=float, default=1.0, help="outermost LED edge to board edge (mm)")
    ap.add_argument("--diameter", type=float, default=0.0, help="board diameter (mm); rings are pushed out against this edge. 0 = smallest board that fits")
    ap.add_argument("--keepout-rect", default="", help="e.g. 23x25: keep a W x H mm rectangle (solar cell) clear in the middle")
    ap.add_argument("--keepout-margin", type=float, default=0.5, help="clearance from the rectangle corners to the innermost LED edge (mm)")
    ap.add_argument("--cx", type=float, default=100.0); ap.add_argument("--cy", type=float, default=100.0)
    ap.add_argument("--name", default="rings")
    build(ap.parse_args())
