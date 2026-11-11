"""dead_copper.py IN.kicad_pcb OUT.kicad_pcb x0,y0,x1,y1 [SKIP_NETS comma list] [rounds=6] (any python; kicad-cli DRC, a .kicad_pro next to IN):
inside a window delete the straight pieces and vias that DRC reports as 'unconnected end' (track_dangling / via_dangling), round after round, so chains of dead copper disappear completely.
Copper that carries nothing: the connectivity does not change (each round the number of open connections must stay the same, otherwise the round is undone and the run stops).
Never touched: arcs, the ring nets (/ROWn, /COLn), the nets in SKIP_NETS (nets that are not finished yet)."""
import sys, os, re, json, subprocess, shutil
KC = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"; PY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
src, dst, win = sys.argv[1], sys.argv[2], tuple(map(float, sys.argv[3].split(",")))
skip = set(sys.argv[4].split(",")) if len(sys.argv) > 4 and sys.argv[4] else set(); rounds = int(sys.argv[5]) if len(sys.argv) > 5 else 6
cur = os.path.abspath(src); d = os.path.dirname(cur); base = os.path.splitext(os.path.basename(cur))[0]
work = os.path.join(d, "_dc.kicad_pcb"); shutil.copy(cur, work); shutil.copy(os.path.join(d, base + ".kicad_pro"), os.path.join(d, "_dc.kicad_pro"))
ring = re.compile(r"^/(ROW\d+|COL\d+)$")
def drc():
    subprocess.run([KC, "pcb", "drc", "--severity-all", "--units", "mm", "--format", "json", "--output", os.path.join(d, "_dc_drc.json"), work], capture_output=True)
    return json.load(open(os.path.join(d, "_dc_drc.json")))
rep = drc(); opens = len(rep["unconnected_items"]); total = 0
for rd in range(rounds):
    todo = []
    for v in rep["violations"]:
        if v["type"] not in ("track_dangling", "via_dangling"): continue
        for it in v["items"]:
            m = re.match(r"(Track|Via)\s*(\(arc\))?\s*\[([^\]]*)\]", it["description"])
            if not m or m.group(2): continue
            net = m.group(3); x, y = it["pos"]["x"], it["pos"]["y"]
            if net in skip or (ring.match(net) and not os.environ.get("DC_RING")) or not net: continue
            if win[0] <= x <= win[2] and win[1] <= y <= win[3]: todo.append(it["uuid"])
    if not todo: print("round", rd, ": nothing dangling"); break
    backup = work + ".bak"; shutil.copy(work, backup)
    code = "import pcbnew, sys, json\nb = pcbnew.LoadBoard(sys.argv[1]); ids = set(json.loads(sys.argv[2])); n = {}\nfor t in list(b.GetTracks()):\n    if t.m_Uuid.AsString() in ids: n[t.GetNetname()] = n.get(t.GetNetname(), 0) + 1; b.Remove(t)\npcbnew.SaveBoard(sys.argv[1], b); print(json.dumps(n))\n"
    out = subprocess.run([PY, "-c", code, work, json.dumps(sorted(set(todo)))], capture_output=True, text=True).stdout.strip().splitlines()
    names = json.loads([l for l in out if l.startswith("{")][-1])
    rep2 = drc()
    if len(rep2["unconnected_items"]) > opens:
        print("round", rd, ": removing all", sum(names.values()), "at once would open", len(rep2["unconnected_items"]) - opens, "connections - trying one by one"); shutil.copy(backup, work)
        kept = 0
        for u in sorted(set(todo)):
            shutil.copy(work, backup)
            subprocess.run([PY, "-c", code, work, json.dumps([u])], capture_output=True, text=True)
            r3 = drc()
            if len(r3["unconnected_items"]) > opens: shutil.copy(backup, work)
            else: kept += 1
        rep = drc(); total += kept; print("round", rd, ": removed", kept, "of", len(set(todo)), "one by one"); continue
    rep = rep2; total += sum(names.values()); print("round", rd, ": removed", sum(names.values()), names)
shutil.copy(work, dst); print("dead copper removed:", total, "; open connections:", opens, "->", len(rep["unconnected_items"]))
