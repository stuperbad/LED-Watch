p = "plan_board.py"
s = open(p, encoding="utf8", newline="").read().replace("\r\n", "\n")


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


# 1. keep every part off the LED band: the band's vias go through the whole board (front AND back)
rep('''    front_poly = Point(0, 0).buffer(free_r - a.part_clr, 128)''', '''    front_poly = Point(0, 0).buffer(free_r - a.part_clr - a.band_keepout, 128)''')
rep('''    back_poly = Point(0, 0).buffer(R - a.back_edge, 128)
    bx, by = 0.0, a.batt_y''', '''    back_poly = Point(0, 0).buffer(R - a.back_edge, 128)
    parts_circle = Point(0, 0).buffer(free_r - a.part_clr - a.band_keepout, 128)
    bx, by = 0.0, a.batt_y''')
rep('''    reg = {"front": Region(front_poly, R), "back": Region(back_poly, R)}''', '''    back_poly = back_poly.intersection(parts_circle)                  # back parts stay inside the free circle (batteries are not parts: they may overlap the band)
    reg = {"front": Region(front_poly, R), "back": Region(back_poly, R)}''')
# plugs placed beside the cells are explicit: they must also lie in the free circle
rep('''            if not r_.within(back_poly):
                return dict(ok=False, D=D, why="battery plug does not fit beside the cell")''', '''            if not r_.within(back_poly.intersection(parts_circle)):
                return dict(ok=False, D=D, why="battery plug does not fit beside the cell (inside the free circle)")''')
# 2. series resistors ON the column trunk line: angle offset in degrees and a 180 degree flip so pad 1 (LED side) points outward
rep('''            th = c * 30.0 + math.degrees(a.res_arc / rh)
            rot = (90.0 - th) % 360.0 if a.res_style == "radial" else (-th) % 360.0''', '''            th = c * 30.0 + (a.res_angle if a.res_angle is not None else math.degrees(a.res_arc / rh))
            rot = (90.0 - th + (180.0 if a.res_flip else 0.0)) % 360.0 if a.res_style == "radial" else (-th) % 360.0''')
rep('''ap.add_argument("--cell-count"''', '''ap.add_argument("--band-keepout", type=float, default=0.0, help="extra radial margin (mm) between the free circle and any part, front and back (room for polar vias)")
    ap.add_argument("--res-angle", type=float, default=None, help="series resistors: angle in degrees from the hour LED (negative = counter-clockwise) instead of --res-arc")
    ap.add_argument("--res-flip", action="store_true", help="series resistors: pad 1 (LED side) outward")
    ap.add_argument("--cell-count"''')
open(p, "w", encoding="utf8", newline="").write(s)

p = "write_pcb.py"
s = open(p, encoding="utf8", newline="").read().replace("\r\n", "\n")
rep('text(b, lb["text"], lb["x"], lb["y"], pcbnew.F_SilkS, 0.8)', 'text(b, lb["text"], lb["x"], lb["y"], pcbnew.F_SilkS, 1.0)')
rep('''        ds.m_TrackMinWidth = F(0.1)
        ds.m_ViasMinSize = F(0.4)
        ds.m_MinThroughDrill = F(0.2)
        nc = ds.m_NetSettings.GetDefaultNetclass()
        nc.SetClearance(F(0.1)); nc.SetTrackWidth(F(0.1)); nc.SetViaDiameter(F(0.4)); nc.SetViaDrill(F(0.2))''', '''        # JLCPCB multilayer rules read from their capability page 2026-10-09 (see JLCPCB-RULES.md)
        ds.m_TrackMinWidth = F(0.1)
        ds.m_ViasMinSize = F(0.3)
        ds.m_MinThroughDrill = F(0.15)
        ds.m_HoleClearance = F(0.30)
        ds.m_CopperEdgeClearance = F(0.2)
        ds.m_HoleToHoleMin = F(0.2)
        nc = ds.m_NetSettings.GetDefaultNetclass()
        nc.SetClearance(F(0.1)); nc.SetTrackWidth(F(0.1)); nc.SetViaDiameter(F(0.3)); nc.SetViaDrill(F(0.15))''')
open(p, "w", encoding="utf8", newline="").write(s)
print("patched")
