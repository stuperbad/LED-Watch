"""
Route the nets still unconnected after pass 1 ONE AT A TIME with freerouting 2.1 (which only exits by itself when nothing is left to route:
a group that contains an unroutable connection loops until it is killed and then writes no result).
For every net: Specctra file with only that net's pins (every other net is blanked = obstacle only), all existing copper locked,
short watchdog; a net that routes is merged into the running board, a net that does not is skipped.
usage: python route_pernet.py BOARD_DIR NAME [minutes_per_net=8]
needs  BOARD_DIR/NAME_pass1_poly.kicad_pcb, NAME_poly, NAME_arc and drc_NAME_pass1_poly.json (kicad-cli drc --format json of that board)
writes NAME_pn_poly.kicad_pcb (running result, updated after every net) and NAME_routed.kicad_pcb at the end
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_two_pass import drop_nets, KP, JAR, HERE   # noqa: E402

board_dir, name = Path(sys.argv[1]).resolve(), sys.argv[2]
limit = float(sys.argv[3]) * 60 if len(sys.argv) > 3 else 480.0
poly = board_dir / f"{name}_poly.kicad_pcb"
arc = board_dir / f"{name}_arc.kicad_pcb"
cur = board_dir / f"{name}_pn_poly.kicad_pcb"
cur.write_bytes((board_dir / f"{name}_pass1_poly.kicad_pcb").read_bytes())

drc = json.load(open(board_dir / f"drc_{name}_pass1_poly.json"))
todo = []
for u in drc["unconnected_items"]:
    for it in u["items"]:
        m = re.search(r"\[([^\]]+)\]", it["description"])
        if m and m.group(1) not in todo:
            todo.append(m.group(1))
first = [n for n in todo if n in ("+3V3", "VBAT", "/LBOOST")]
todo = first + [n for n in todo if n not in first]
print("nets to route:", todo, flush=True)


def run(cmd, log=None, timeout=None):
    t0 = time.time()
    f = open(log, "w", encoding="utf8") if log else subprocess.DEVNULL
    p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    while p.poll() is None:
        if timeout and time.time() - t0 > timeout:
            p.kill()
            subprocess.run(["taskkill", "/F", "/IM", "java.exe"], capture_output=True)
            return None
        time.sleep(3)
    return p.returncode


results = []
for k, net in enumerate(todo, 1):
    tag = "pn"
    run([KP, str(HERE / "export_dsn.py"), str(cur), str(board_dir / f"{tag}_raw.dsn")])
    run([sys.executable, str(HERE / "prep_dsn.py"), str(board_dir / f"{tag}_raw.dsn"), str(board_dir / f"{tag}_all.dsn"), "140"])
    drop_nets(board_dir / f"{tag}_all.dsn", board_dir / f"{tag}.dsn", {net})
    ses = board_dir / f"{name}_{tag}.ses"
    ses.unlink(missing_ok=True)
    t0 = time.time()
    rc = run(["java", "-jar", JAR, "-de", str(board_dir / f"{tag}.dsn"), "-do", str(ses), "--gui.enabled=false"], board_dir / "route_pn.log", timeout=limit)
    dt = time.time() - t0
    if rc is None or not ses.exists():
        results.append((net, "none", dt))
        print(f"[{k}/{len(todo)}] {net}: no result after {dt / 60:.1f} min; skipped", flush=True)
        continue
    nxt = board_dir / f"{name}_pn_next.kicad_pcb"
    run([KP, str(HERE / "import_ses.py"), str(cur), str(ses), str(nxt)])
    nxt.replace(cur)
    results.append((net, "ok", dt))
    print(f"[{k}/{len(todo)}] {net}: routed in {dt:.0f} s", flush=True)

run([KP, str(HERE / "merge_new.py"), str(poly), str(cur), str(arc), str(board_dir / f"{name}_routed.kicad_pcb")], board_dir / "merge.log")
print("done:", board_dir / f"{name}_routed.kicad_pcb", flush=True)
for r in results:
    print(r, flush=True)
