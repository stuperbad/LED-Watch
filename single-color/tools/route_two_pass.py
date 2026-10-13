"""
Autoroute of the part of the board the polar router does not draw: pass 1 = the easy nets only (power, local, short); the other nets keep their
wires and vias (obstacles) but lose their pins, so nothing is routed for them.  Everything already on the board is locked (type protect).

usage: python route_two_pass.py BOARD_DIR NAME [pass1_max_passes] [pass2_max_passes] [p1only]
reads  BOARD_DIR/NAME_poly.kicad_pcb  (polar copper as short segments) and NAME_arc.kicad_pcb (true arcs)
NB freerouting 2.1 ignores -mp and its job timeout and writes no result when killed: for the hard nets use route_incremental.py (small groups + watchdog).
"""
import re
import subprocess
import sys
from pathlib import Path

KP = r"C:\Program Files\KiCad\10.0\bin\python.exe"
JAR = r"C:\Users\evanf\AppData\Local\freerouting\app\freerouting-executable.jar"
HERE = Path(__file__).resolve().parent

# nets routed in pass 1: power, harvester/charger, the programming and status lines, the small local nets
EASY = ["GND", "VBAT", "+3V3", "/SOLAR_IN", "/BATT", "/LBOOST", "/LBUCK", "/VBAT_OV", "/VRDIV", "/OK_PROG", "/OK_HYST", "/VOUT_SET",
        "/VREF_SAMP", "/BAT_OK", "/UPDI", "/ROW11", "/COL0_MCU", "/COL1_MCU", "/COL11_MCU", "/SCL", "/SDA"]


def run(cmd, log=None):
    print(">", " ".join(str(c) for c in cmd)[:200], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if log:
        Path(log).write_text(r.stdout + r.stderr, encoding="utf8")
    return r


def drop_nets(src, dst, keep):
    """nets not in `keep` stay defined (their wires and vias must still be read as obstacles) but lose all their pins, so nothing is routed for them"""
    s = Path(src).read_text(encoding="utf8")
    i = s.index("(network")
    j = s.index("(wiring")
    head, net, tail = s[:i], s[i:j], s[j:]
    dropped = []
    nl = chr(10)

    def blank(m):
        if m.group(1).strip('"') in keep:
            return m.group(0)
        dropped.append(m.group(1))
        return "    (net " + m.group(1) + nl + "      (pins)" + nl + "    )"

    net2 = re.sub(r"(?s)    \(net (\S+)\s*\(pins[^)]*\)\s*\)", blank, net)
    Path(dst).write_text(head + net2 + tail, encoding="utf8")
    return dropped


def main():
    board_dir, name = Path(sys.argv[1]).resolve(), sys.argv[2]
    mp1 = sys.argv[3] if len(sys.argv) > 3 else "60"
    mp2 = sys.argv[4] if len(sys.argv) > 4 else "130"
    poly = board_dir / f"{name}_poly.kicad_pcb"
    arc = board_dir / f"{name}_arc.kicad_pcb"

    # ---- pass 1
    run([KP, str(HERE / "export_dsn.py"), str(poly), str(board_dir / "p1_raw.dsn")])
    run([sys.executable, str(HERE / "prep_dsn.py"), str(board_dir / "p1_raw.dsn"), str(board_dir / "p1_all.dsn"), "140"])
    dropped = drop_nets(board_dir / "p1_all.dsn", board_dir / "p1.dsn", set(EASY))
    print("pass 1 routes", len(EASY), "nets, blanks", len(dropped), flush=True)
    ses1 = board_dir / f"{name}_pass1.ses"
    ses1.unlink(missing_ok=True)
    run(["java", "-jar", JAR, "-de", str(board_dir / "p1.dsn"), "-do", str(ses1), "-mp", mp1, "--gui.enabled=false"], board_dir / "route_pass1.log")
    if not ses1.exists():
        sys.exit("pass 1 wrote no SES, see route_pass1.log")
    pass1 = board_dir / f"{name}_pass1_poly.kicad_pcb"
    run([KP, str(HERE / "import_ses.py"), str(poly), str(ses1), str(pass1)])
    if len(sys.argv) > 5 and sys.argv[5] == "p1only":
        return

    # ---- pass 2 (everything; may never finish: prefer route_incremental.py)
    run([KP, str(HERE / "export_dsn.py"), str(pass1), str(board_dir / "p2_raw.dsn")])
    run([sys.executable, str(HERE / "prep_dsn.py"), str(board_dir / "p2_raw.dsn"), str(board_dir / "p2.dsn"), "140"])
    ses2 = board_dir / f"{name}_pass2.ses"
    ses2.unlink(missing_ok=True)
    run(["java", "-jar", JAR, "-de", str(board_dir / "p2.dsn"), "-do", str(ses2), "-mp", mp2, "--gui.enabled=false"], board_dir / "route_pass2.log")
    if not ses2.exists():
        sys.exit("pass 2 wrote no SES, see route_pass2.log")
    pass2 = board_dir / f"{name}_pass2_poly.kicad_pcb"
    run([KP, str(HERE / "import_ses.py"), str(pass1), str(ses2), str(pass2)])
    run([KP, str(HERE / "merge_new.py"), str(poly), str(pass2), str(arc), str(board_dir / f"{name}_routed.kicad_pcb")], board_dir / "merge.log")
    print("done:", board_dir / f"{name}_routed.kicad_pcb", flush=True)


if __name__ == "__main__":
    main()
