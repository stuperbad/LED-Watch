"""usage: python drc_sum.py board.kicad_pcb [baseline.json]  -> runs kicad-cli DRC, prints counts; with a baseline list only NEW violations"""
import collections, json, re, subprocess, sys
b = sys.argv[1]
out = b.replace(".kicad_pcb", "_drc.json")
subprocess.run([r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", "pcb", "drc", "--format", "json", "--severity-error", "--all-track-errors", "-o", out, b], capture_output=True)
d = json.load(open(out))
c = collections.Counter(v["type"] for v in d["violations"])
un = collections.Counter(re.search(r"\[([^\]]+)\]", u["items"][0]["description"]).group(1) for u in d["unconnected_items"])
print(dict(c), "unconnected", sum(un.values()), dict(un) if len(un) < 12 else len(un))
if len(sys.argv) > 2:
    base = json.load(open(sys.argv[2]))
    key = lambda v: (v["type"], tuple(sorted((i["pos"]["x"] // 0.01, i["pos"]["y"] // 0.01) for i in v["items"])))
    bk = {key(v) for v in base["violations"]}
    for v in d["violations"]:
        if key(v) not in bk:
            print(" NEW", v["type"], v["description"][:90], [(round(i["pos"]["x"], 2), round(i["pos"]["y"], 2)) for i in v["items"]][:2])
