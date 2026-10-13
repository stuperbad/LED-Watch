"""remove the tracks / vias of the named nets that are NOT in the baseline board (= what an autorouter added), keep everything else
usage: python strip_added.py baseline.kicad_pcb routed.kicad_pcb out.kicad_pcb @nets.txt"""
import re, sys
base, routed, out, nets = sys.argv[1:5]
names = {l.strip() for l in open(nets[1:]) if l.strip()}
def blocks(txt, kind):
    return list(re.finditer(r"\t\(%s\n(.*?)\n\t\)\n" % kind, txt, re.S))
def key(kind, body):
    net = re.search(r'\(net "([^"]*)"\)', body).group(1)
    if kind == "segment":
        s = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", body).groups(); e = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", body).groups()
        lay = re.search(r'\(layer "([^"]*)"\)', body).group(1)
        return (kind, lay, net, tuple(round(float(v), 3) for v in s + e))
    a = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", body).groups()
    return (kind, net, tuple(round(float(v), 3) for v in a))
bt = open(base, encoding="utf8").read()
bset = {key(k, m.group(1)) for k in ("segment", "via") for m in blocks(bt, k)}
rt = open(routed, encoding="utf8").read()
drop, n = [], 0
for k in ("segment", "via"):
    for m in blocks(rt, k):
        kk = key(k, m.group(1))
        if kk[2 if k == "via" else 2] in names and kk not in bset:
            drop.append((m.start(), m.end())); n += 1
for a, b in sorted(drop, reverse=True):
    rt = rt[:a] + rt[b:]
open(out, "w", encoding="utf8").write(rt)
print("removed", n, "added items of", len(names), "nets")
