"""retry grid_route.py with the nets that failed moved to the front, keep the run with the fewest failures
usage: python grid_loop.py grid.json in.kicad_pcb best_out.kicad_pcb nets.txt [rounds=6]  (extra grid_route options via env GR_OPTS)"""
import os, re, shutil, subprocess, sys
grid, src, best_out, nets = sys.argv[1:5]
rounds = int(sys.argv[5]) if len(sys.argv) > 5 else 6
here = os.path.dirname(os.path.abspath(__file__))
tag = os.path.splitext(os.path.basename(best_out))[0]      # unique file names per loop, so two loops can run side by side
order = [l.strip() for l in open(nets) if l.strip()]
best = None
seen = {}
for r in range(rounds):
    open(tag + "_nets.txt", "w").write("\n".join(order) + "\n")
    out = tag + "_try.kicad_pcb"
    p = subprocess.run([sys.executable, os.path.join(here, "grid_route.py"), grid, src, out, "@" + tag + "_nets.txt"] + os.environ.get("GR_OPTS", "").split(), capture_output=True, text=True)
    open(tag + "_%d.log" % r, "w").write(p.stdout + p.stderr)
    m = re.search(r"failed: \[(.*)\]", p.stdout)
    failed = [x.strip().strip("'") for x in m.group(1).split(",")] if m and m.group(1).strip() else []
    print("round", r, "failed", len(failed), failed, flush=True)
    if best is None or len(failed) < best[0]:
        best = (len(failed), failed)
        shutil.copy(out, best_out)
    if not failed:
        break
    key = tuple(order)
    seen[key] = True
    order = failed + [n for n in order if n not in failed]
    if tuple(order) in seen:
        order = failed[::-1] + [n for n in order if n not in failed]
print("best", best, flush=True)
