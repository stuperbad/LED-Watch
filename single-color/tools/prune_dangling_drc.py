"""Remove the dangling tracks and vias that a re-route leaves behind, using the DRC report to find them and prune_leaves.py to remove them safely.
Each round: refill zones, DRC, take the positions of every track_dangling / via_dangling item, run prune_leaves.py with --targets on those positions (it deletes a dead-end via, or cuts a track back to the
place where other copper of its net touches its side, or deletes it), and keep the result only if the DRC unconnected count did not go up; otherwise the round is undone and the positions that caused it
are not tried again.  Stops when nothing dangles or nothing changes.
usage (any python): prune_dangling_drc.py in.kicad_pcb out.kicad_pcb [CX CY HALF = 100 92 40]      (a .kicad_pro with the base name of in.kicad_pcb must sit next to it)"""
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
CX, CY, HALF = (sys.argv[3:6] if len(sys.argv) > 5 else ("100", "92", "40"))
w = tempfile.mkdtemp()
pro = os.path.splitext(src)[0] + ".kicad_pro"


def drc(board):
    """refill + DRC; returns (dangling positions with net names, unconnected count, violation count excluding dangling/text/lib)"""
    shutil.copy(pro, os.path.join(w, "t.kicad_pro"))
    shutil.copy(pro, os.path.join(w, "cur.kicad_pro"))
    shutil.copy(pro, os.path.join(w, "next.kicad_pro"))
    subprocess.run([KPY, os.path.join(HERE, "refill.py"), board, os.path.join(w, "t.kicad_pcb")], capture_output=True)
    out = os.path.join(w, "d.json")
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, os.path.join(w, "t.kicad_pcb")], capture_output=True)
    d = json.load(open(out))
    dang = []
    for v in d["violations"]:
        if v["type"] in ("track_dangling", "via_dangling"):
            for i in v["items"]:
                import re
                m = re.search(r"\[([^\]]+)\]", i["description"])
                dang.append(((round(i["pos"]["x"], 3), round(i["pos"]["y"], 3)), m.group(1) if m else ""))
    other = [v for v in d["violations"] if v["type"] in ("clearance", "hole_clearance", "shorting_items", "tracks_crossing", "via_dangling_never")]
    return dang, len(d["unconnected_items"]), len(other)


cur = os.path.join(w, "cur.kicad_pcb")
shutil.copy(src, cur)
dang, unc0, bad0 = drc(cur)
print("start: %d dangling, %d unconnected, %d other violations" % (len(dang), unc0, bad0))
tried = set()
for rnd in range(10):
    todo = [(p, n) for p, n in dang if p not in tried]
    if not todo:
        break
    nets = sorted({n for _, n in todo if n})
    open(os.path.join(w, "nets.txt"), "w").write("\n".join(nets))
    tgt = repr([p for p, _ in todo])
    nxt = os.path.join(w, "next.kicad_pcb")
    r = subprocess.run([KPY, os.path.join(HERE, "prune_leaves.py"), cur, nxt, CX, CY, HALF, "--targets=" + tgt, "@" + os.path.join(w, "nets.txt")], capture_output=True, text=True)
    msgs = [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("swig")]
    nch = int([l for l in msgs if l.startswith("changes:")][0].split()[1]) if any(l.startswith("changes:") for l in msgs) else 0
    for l in msgs:
        print("  ", l[:110])
    if nch == 0:
        for p, _ in todo:
            tried.add(p)
        break
    d2, unc, bad = drc(nxt)
    print("round %d: %d changes -> %d dangling, %d unconnected, %d other violations" % (rnd, nch, len(d2), unc, bad))
    if unc > unc0:
        print("   made it worse: undone, these positions are left alone")
        for p, _ in todo:
            tried.add(p)
        continue
    for p, _ in todo:
        tried.add(p)
    shutil.copy(nxt, cur)
    dang, unc0, bad0 = d2, unc, bad
shutil.copy(cur, dst)
print("wrote", dst, "| left: %d dangling, %d unconnected" % (len(dang), unc0))
