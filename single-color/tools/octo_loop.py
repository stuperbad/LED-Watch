"""Run octo_opt.py, refill the ground plane, run DRC; every chain next to a new violation (or any unconnected item) is put on the skip list and the run is repeated, until DRC is as clean as the input.
usage (any python): octo_loop.py in.kicad_pcb out.kicad_pcb      (a .kicad_pro with the same base name as in.kicad_pcb must sit next to it)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

KCLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
KPY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]

w = tempfile.mkdtemp()
shutil.copy(src, os.path.join(w, "in.kicad_pcb"))
for n in ("in", "a", "b"):
    shutil.copy(os.path.splitext(src)[0] + ".kicad_pro", os.path.join(w, n + ".kicad_pro"))


def drc(board):
    out = os.path.join(w, "d.json")
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, board], capture_output=True)
    d = json.load(open(out))
    v = [x for x in d["violations"] if x["type"] not in ("text_height", "lib_footprint_issues")]
    return v, d["unconnected_items"]


v0, u0 = drc(os.path.join(w, "in.kicad_pcb"))
print("input: %d violations, %d unconnected" % (len(v0), len(u0)))
skip = []
for rnd in range(12):
    json.dump(skip, open(os.path.join(w, "skip.json"), "w"))
    r = subprocess.run([KPY, os.path.join(HERE, "octo_opt.py"), os.path.join(w, "in.kicad_pcb"), os.path.join(w, "a.kicad_pcb"), os.path.join(w, "skip.json")], capture_output=True, text=True)
    print(" ", [l for l in r.stdout.splitlines() if l.startswith("chains")])
    subprocess.run([KPY, os.path.join(HERE, "fix_gnd_zone.py"), os.path.join(w, "a.kicad_pcb"), os.path.join(w, "b.kicad_pcb")], capture_output=True)
    v, u = drc(os.path.join(w, "b.kicad_pcb"))
    print("round %d: %d violations, %d unconnected, %d chains skipped" % (rnd, len(v), len(u), len(skip)))
    if len(v) <= len(v0) and len(u) <= len(u0):
        shutil.copy(os.path.join(w, "b.kicad_pcb"), dst)
        print("wrote", dst)
        print("skipped chains:", skip)
        break
    chains = json.load(open(os.path.join(w, "a.kicad_pcb.chains.json")))
    pts = [i["pos"] for x in v for i in x["items"]] + [i["pos"] for x in u for i in x["items"]]
    added = 0
    import math

    def near(c, q, tol=0.25):
        P = c["pts"]
        if len(P) == 1:
            return math.hypot(P[0][0] - q["x"], P[0][1] - q["y"]) < tol
        for (ax, ay), (bx, by) in zip(P[:-1], P[1:]):
            ux, uy, wx, wy = bx - ax, by - ay, q["x"] - ax, q["y"] - ay
            L2 = ux * ux + uy * uy
            s = max(0.0, min(1.0, (wx * ux + wy * uy) / L2)) if L2 else 0.0
            if math.hypot(wx - s * ux, wy - s * uy) < tol:
                return True
        return False
    for c in chains:
        if c["id"] not in skip and any(near(c, p) for p in pts):
            skip.append(c["id"])
            added += 1
    if not added:
        print("no chain to blame, stopping")
        break
