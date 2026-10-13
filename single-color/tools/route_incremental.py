"""
Incremental autoroute with a wall-clock watchdog (freerouting 2.1 ignores its own pass / time limits, and writes no result when it is killed).

Instead of one big run that may never finish, the remaining nets are routed in small groups.  For each group:
  - the Specctra file keeps only the nets already routed + the current group (every other net is dropped, its pads are just obstacles),
  - everything already on the board is locked (type protect),
  - freerouting runs with a time limit; if it does not finish in time it is killed and that group is reported as failed (nothing is lost).
usage: python route_incremental.py BOARD_DIR NAME [minutes_per_group=10]
needs  BOARD_DIR/NAME_pass1_poly.kicad_pcb (output of route_two_pass.py pass 1) and NAME_poly / NAME_arc
writes NAME_inc_poly.kicad_pcb (all groups merged) and NAME_routed.kicad_pcb (merged onto the true-arc board)
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_two_pass import EASY, drop_nets, KP, JAR, HERE   # noqa: E402  (reuses the helpers; importing it does not run the router)

board_dir, name = Path(sys.argv[1]).resolve(), sys.argv[2]
limit = float(sys.argv[3]) * 60 if len(sys.argv) > 3 else 600.0

GROUPS = [
    ["/COL0", "/COL1", "/COL2", "/COL3", "/COL4", "/COL5"],                      # indicator LED anodes to their column trunks
    ["/ROW0", "/ROW1", "/ROW2", "/ROW3", "/ROW4", "/ROW5"],                      # hour + minute lane vias to the MCU
    ["/ROW6", "/ROW7", "/ROW8", "/ROW9", "/ROW10"],                              # second lane vias to the MCU
    ["/COL2_MCU", "/COL3_MCU", "/COL4_MCU", "/COL5_MCU", "/COL6_MCU"],           # column resistors to the MCU
    ["/COL7_MCU", "/COL8_MCU", "/COL9_MCU", "/COL10_MCU"],
    ["/BTN1", "/BTN2", "/IMU_INT"],
]
poly = board_dir / f"{name}_poly.kicad_pcb"
arc = board_dir / f"{name}_arc.kicad_pcb"
cur = board_dir / f"{name}_pass1_poly.kicad_pcb"
if not cur.exists():
    sys.exit("run route_two_pass.py first (pass 1)")
keep = set(EASY)
results = []


def run(cmd, log=None, timeout=None):
    t0 = time.time()
    f = open(log, "w", encoding="utf8") if log else subprocess.DEVNULL
    p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    while p.poll() is None:
        if timeout and time.time() - t0 > timeout:
            p.kill()
            return None
        time.sleep(3)
    return p.returncode


for gi, grp in enumerate(GROUPS, 1):
    keep |= set(grp)
    tag = f"g{gi}"
    run([KP, str(HERE / "export_dsn.py"), str(cur), str(board_dir / f"{tag}_raw.dsn")])
    run([sys.executable, str(HERE / "prep_dsn.py"), str(board_dir / f"{tag}_raw.dsn"), str(board_dir / f"{tag}_all.dsn"), "140"])
    drop_nets(board_dir / f"{tag}_all.dsn", board_dir / f"{tag}.dsn", keep)
    ses = board_dir / f"{name}_{tag}.ses"
    ses.unlink(missing_ok=True)
    t0 = time.time()
    rc = run(["java", "-jar", JAR, "-de", str(board_dir / f"{tag}.dsn"), "-do", str(ses), "--gui.enabled=false"], board_dir / f"route_{tag}.log", timeout=limit)
    dt = time.time() - t0
    if rc is None or not ses.exists():
        results.append((tag, grp, "TIMEOUT/none", dt))
        print(f"group {gi} {grp}: no result after {dt / 60:.1f} min (killed); skipped", flush=True)
        keep -= set(grp)
        subprocess.run(["taskkill", "/F", "/IM", "java.exe"], capture_output=True)
        continue
    nxt = board_dir / f"{name}_{tag}_poly.kicad_pcb"
    run([KP, str(HERE / "import_ses.py"), str(cur), str(ses), str(nxt)])
    cur = nxt
    results.append((tag, grp, "ok", dt))
    print(f"group {gi} {grp}: routed in {dt / 60:.1f} min", flush=True)

final_poly = board_dir / f"{name}_inc_poly.kicad_pcb"
final_poly.write_bytes(cur.read_bytes())
run([KP, str(HERE / "merge_new.py"), str(poly), str(final_poly), str(arc), str(board_dir / f"{name}_routed.kicad_pcb")], board_dir / "merge.log")
print("done:", board_dir / f"{name}_routed.kicad_pcb", flush=True)
for r in results:
    print(r, flush=True)
