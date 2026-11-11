"""rework_clear.py (5th argument = optional JSON list of item uuids that must never be removed)
rework_clear.py IN.kicad_pcb OUT.kicad_pcb x0,y0,x1,y1 [rounds=4] : remove the tracks / vias that DRC reports as shorting / clearance / hole-clearance items inside a window (any python; needs kicad-cli, a .kicad_pro next to IN).
Each round: DRC (json), the track / via items (position, net, layer) are matched to board items and deleted.  Pads are never touched.  Prints the nets that lost copper."""
import sys, os, re, json, subprocess, shutil, collections
KC = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"; PY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
protect = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 else set()
src, dst, win = sys.argv[1], sys.argv[2], tuple(map(float, sys.argv[3].split(","))); rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 4
cur = os.path.abspath(src); d = os.path.dirname(cur); base = os.path.splitext(os.path.basename(cur))[0]
work = os.path.join(d, "_clr.kicad_pcb"); shutil.copy(cur, work); shutil.copy(os.path.join(d, base + ".kicad_pro"), os.path.join(d, "_clr.kicad_pro"))
TYPES = ("shorting_items", "tracks_crossing", "clearance", "hole_clearance", "track_width", "via_diameter", "annular_width", "copper_edge_clearance")
lost = collections.Counter()
for rd in range(rounds):
    subprocess.run([KC, "pcb", "drc", "--severity-all", "--units", "mm", "--format", "json", "--output", os.path.join(d, "_clr_drc.json"), work], capture_output=True)
    rep = json.load(open(os.path.join(d, "_clr_drc.json"))); todo = []
    for v in rep["violations"]:
        if v["type"] not in TYPES: continue
        for it in v["items"]:
            if not re.match(r"(Track|Via|Arc)\s*\[", it["description"]): continue
            x, y = it["pos"]["x"], it["pos"]["y"]
            if win[0] <= x <= win[2] and win[1] <= y <= win[3] and it["uuid"] not in protect: todo.append(it["uuid"])
    if not todo: print("round", rd, ": nothing to remove"); break
    code = """
import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1]); ids = set(json.loads(sys.argv[2])); names = {}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ids: names[t.GetNetname()] = names.get(t.GetNetname(), 0) + 1; b.Remove(t)
pcbnew.SaveBoard(sys.argv[3], b); print(json.dumps(names))
"""
    out = subprocess.run([PY, "-c", code, work, json.dumps(sorted(set(todo))), work], capture_output=True, text=True).stdout.strip().splitlines()
    out = [l for l in out if l.startswith("{")]; names = json.loads(out[-1]) if out else {}
    print("round", rd, ": removed", sum(names.values()), names)
    for k, v in names.items(): lost[k] += v
    if not names: break
shutil.copy(work, dst); print("nets that lost copper:", dict(lost))
