"""
KiCad-python half of the board generator: boards/<name>/plan.json -> boards/<name>/<name>.kicad_pcb  (placement only, no nets/routing yet)
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" write_pcb.py [name ...]      (no names = every folder under boards/)
"""
import json, os, re, sys
import pcbnew
from pcbnew import FromMM as F, VECTOR2I as V

HERE = os.path.dirname(os.path.abspath(__file__))
KI = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
CX, CY = 100.0, 100.0


def load(fpid):
    lib, name = fpid.split(":", 1)
    base = os.path.join(HERE, "footprints") if lib == "LEDWatch" else KI            # our own footprints (BQ25570 RGR) live in footprints/LEDWatch.pretty
    return pcbnew.FootprintLoad(os.path.join(base, lib + ".pretty"), name)


def poly(board, pts, layer, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetLayer(layer)
    s.SetFilled(False)
    s.SetWidth(F(width))
    ps = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts[:-1] if pts[0] == pts[-1] else pts:
        ps.Append(F(CX + x), F(CY + y))
    ps.SetClosed(True)
    s.SetPolyShape(pcbnew.SHAPE_POLY_SET(ps))
    board.Add(s)


def rect(board, x, y, w, h, layer, width=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetLayer(layer)
    s.SetFilled(False)
    s.SetStart(V(F(CX + x - w / 2), F(CY + y - h / 2)))
    s.SetEnd(V(F(CX + x + w / 2), F(CY + y + h / 2)))
    s.SetWidth(F(width))
    board.Add(s)


def text(board, s_, x, y, layer, size=1.2, thick=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s_)
    t.SetLayer(layer)
    t.SetPosition(V(F(CX + x), F(CY + y)))
    t.SetTextSize(V(F(size), F(size)))
    if thick:
        t.SetTextThickness(F(thick))
    board.Add(t)


def build(name):
    d = os.path.join(HERE, "boards", name)
    p = json.load(open(os.path.join(d, "plan.json")))
    b = pcbnew.BOARD()
    poly(b, p["outline"], pcbnew.Edge_Cuts)
    for s in p["slots"]:
        poly(b, s, pcbnew.Edge_Cuts)
    for L in p["leds"]:
        fp = load(L["fp"])
        fp.SetReference(L["ref"]); fp.SetValue("LED white " + L["size"])
        fp.SetPosition(V(F(CX + L["x"]), F(CY + L["y"])))
        fp.SetOrientationDegrees(L["rot"])
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
    for q in p["parts"]:
        fp = load(q["fp"])
        if fp is None:
            print("missing footprint", q["fp"]); continue
        fp.SetReference(q["ref"]); fp.SetValue(q["value"]); fp.Value().SetVisible(False)
        pos = V(F(CX + q["x"]), F(CY + q["y"]))
        fp.SetPosition(pos)
        fp.Reference().SetVisible(False)
        b.Add(fp)
        if q["side"] == "back":
            fp.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(q["rot"])
        # centre the courtyard on the planned position (many footprints, e.g. headers and connectors, have their origin off-centre)
        try:
            bb = fp.GetCourtyard(pcbnew.B_CrtYd if q["side"] == "back" else pcbnew.F_CrtYd).BBox()
            if bb.GetWidth() > 0:
                dx_ = F(CX + q["x"]) - (bb.GetX() + bb.GetWidth() // 2)
                dy_ = F(CY + q["y"]) - (bb.GetY() + bb.GetHeight() // 2)
                fp.Move(V(int(dx_), int(dy_)))
        except Exception as e_:
            print("courtyard centring failed for", q["ref"], e_)
    if p["cell"]:
        c = p["cell"]
        for cc in p.get("cells", [dict(x=c.get("x", 0), y=c.get("y", 0))]):
            rect(b, cc["x"], cc["y"], c["w"], c["h"], pcbnew.User_1)
            text(b, f'solar cell {c["name"]} {c["w"]:g}x{c["h"]:g} (keep-out, front)', cc["x"], cc["y"], pcbnew.User_1, 0.9)
    for lb in p.get("labels", []):
        text(b, lb["text"], lb["x"], lb["y"], pcbnew.F_SilkS, p.get("args", {}).get("label_h", 1.0), p.get("args", {}).get("label_w", 0.15))
    bt = p["battery"]
    for bc in p.get("batteries", [dict(x=bt["x"], y=bt["y"])]):
        if not bt.get("round"):
            rect(b, bc["x"], bc["y"], bt["w"] + 2.0, bt["h"] + 2.0, pcbnew.User_3)       # shield / foam-tape zone
    for bc in p.get("batteries", [dict(x=bt["x"], y=bt["y"])])[1:]:
        rect(b, bc["x"], bc["y"], bt["w"], bt["h"], pcbnew.User_2)
    if bt.get("round"):
        c_ = pcbnew.PCB_SHAPE(b); c_.SetShape(pcbnew.SHAPE_T_CIRCLE); c_.SetLayer(pcbnew.User_2); c_.SetFilled(False)
        c_.SetStart(V(F(CX + bt["x"]), F(CY + bt["y"]))); c_.SetEnd(V(F(CX + bt["x"] + bt["w"] / 2), F(CY + bt["y"]))); c_.SetWidth(F(0.15)); b.Add(c_)
    else:
        rect(b, bt["x"], bt["y"], bt["w"], bt["h"], pcbnew.User_2)
    text(b, f'LiPo {bt["name"]} {bt["w"]:g}x{bt["h"]:g}x{bt["t"]:g} (back)', bt["x"], bt["y"], pcbnew.User_2, 0.9)
    text(b, f'free centre {2 * p["free_r"]:.1f} mm, LED band {p["band"]:.2f} mm, board {p["D"]:.1f} mm', 0, -p["R"] - 6, pcbnew.Dwgs_User, 1.0)
    # ---- nets: copy every pad's net from the schematic netlist (n_usb.xml / n_solar.xml)
    import xml.etree.ElementTree as ET
    variant = "solar" if p["cell"] else "usb"
    root = ET.parse(os.path.join(HERE, "schematic", f"n_{variant}.xml")).getroot()
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    n_assigned = n_missing = 0
    missing = []
    for net in root.find("nets"):
        nm = net.get("name")
        if not nm or nm.startswith("unconnected"):
            continue
        ni = pcbnew.NETINFO_ITEM(b, nm)
        b.Add(ni)
        for node in net.findall("node"):
            ref, pin = node.get("ref"), node.get("pin")
            targets = [ref] + (["J1B"] if ref == "J1" and "J1B" in fps else [])      # the second battery plug is wired in parallel with J1
            for tref in targets:
                f = fps.get(tref)
                pad = f.FindPadByNumber(pin) if f else None
                if pad is None:
                    n_missing += 1
                    missing.append(f"{tref}.{pin}")
                    continue
                pad.SetNet(ni)
                n_assigned += 1
    ncell = len(p.get("cells", [])) if p["cell"] else 0
    extra_nets = {}
    for ref_, f_ in fps.items():
        m_ = re.fullmatch(r"SC(\d)([+-])", ref_)
        if m_:
            ci_, sg_ = int(m_.group(1)), m_.group(2)
            nm_ = ("GND" if sg_ == "-" else ("SC_MID" if ncell == 2 else "SOLAR_IN")) if ci_ == 1 else ("SC_MID" if sg_ == "-" else "SOLAR_IN")
            ni_ = extra_nets.get(nm_)
            if ni_ is None:
                ni_ = b.FindNet(nm_) or pcbnew.NETINFO_ITEM(b, nm_)
                if not b.FindNet(nm_):
                    b.Add(ni_)
                extra_nets[nm_] = ni_
            pad_ = f_.FindPadByNumber("1")
            if pad_:
                pad_.SetNet(ni_); n_assigned += 1
    print(f"{name}: nets assigned to {n_assigned} pads, {n_missing} netlist pins without a pad {missing[:8]}")
    ds = b.GetDesignSettings()
    try:
        ds.SetCopperLayerCount(4)
        # JLCPCB multilayer rules read from their capability page 2026-10-09 (see JLCPCB-RULES.md)
        ds.m_TrackMinWidth = F(0.1)
        ds.m_ViasMinSize = F(0.3)
        ds.m_MinThroughDrill = F(0.15)
        ds.m_HoleClearance = F(0.30)
        ds.m_CopperEdgeClearance = F(0.3)
        ds.m_HoleToHoleMin = F(0.2)
        nc = ds.m_NetSettings.GetDefaultNetclass()
        nc.SetClearance(F(0.1)); nc.SetTrackWidth(F(0.1)); nc.SetViaDiameter(F(0.3)); nc.SetViaDrill(F(0.15))
    except Exception as e:
        print("design rules not set:", e)
    out = os.path.join(d, name + ".kicad_pcb")
    pcbnew.SaveBoard(out, b)
    # minimal project file so KiCad opens it as its own project
    pro = os.path.join(d, name + ".kicad_pro")
    if not os.path.exists(pro):
        open(pro, "w").write('{"meta":{"filename":"%s.kicad_pro","version":3}}' % name)
    print("wrote", out)


if __name__ == "__main__":
    names = sys.argv[1:] or [n for n in os.listdir(os.path.join(HERE, "boards")) if os.path.exists(os.path.join(HERE, "boards", n, "plan.json"))]
    for n in names:
        build(n)
