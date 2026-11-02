"""zonecount.py board.kicad_pcb baseline.kicad_pcb : number of tracks / vias that break a keep-out rule (zonespec.py) and are not unchanged items of the baseline; prints the count, then the nets. KiCad python."""
import sys, re, collections
import pcbnew
sys.path.insert(0, __file__.rsplit("/", 1)[0].rsplit("\\", 1)[0])
import zonespec as zs
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); base = pcbnew.LoadBoard(sys.argv[2]); Z = zs.build(b)
ring = re.compile(r"^/(COL\d+|ROW\d+)$")
key = lambda t: ("via", t.GetNetname(), (round(tomm(t.GetPosition().x), 3), round(tomm(t.GetPosition().y), 3))) if t.GetClass() == "PCB_VIA" else (t.GetLayerName(), t.GetNetname(), tuple(sorted([(round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3)), (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))])))
accept = {key(t) for t in base.GetTracks() if t.GetClass() != "PCB_ARC"}
n = 0; nets = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == "PCB_ARC" or ring.match(t.GetNetname()):
        continue
    h = zs.hits(t, Z)
    if h and (key(t) not in accept or any(x.startswith(("imu", "u4")) for x in h)):
        n += 1; nets[(t.GetNetname(), h[0].split()[0])] += 1
print(n)
if len(sys.argv) > 3:
    for k, v in sorted(nets.items()):
        print("  ", k, v)
