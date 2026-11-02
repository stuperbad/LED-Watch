"""ripzone.py in.kicad_pcb out.kicad_pcb : delete every track / via of another net inside a keep-out zone of zonespec.py (arcs and ring nets /COLn /ROWn are never touched;
baseline.kicad_pcb in the 4th argument lists accepted items: pieces that exist unchanged in that board stay). Prints the nets cut. KiCad python."""
import sys, re, collections
import pcbnew
sys.path.insert(0, __file__.rsplit("/", 1)[0].rsplit("\\", 1)[0])
import zonespec as zs
tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
Z = zs.build(b)
ring = re.compile(r"^/(COL\d+|ROW\d+)$")
accept = set()
if len(sys.argv) > 3:
    base = pcbnew.LoadBoard(sys.argv[3])
    for t in base.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            accept.add((t.GetLayerName(), t.GetNetname(), tuple(sorted([(round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3)), (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))]))))
        elif t.GetClass() == "PCB_VIA":
            accept.add(("via", t.GetNetname(), (round(tomm(t.GetPosition().x), 3), round(tomm(t.GetPosition().y), 3))))
cut = collections.Counter(); grave = []
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_ARC" or ring.match(t.GetNetname()):
        continue
    h = zs.hits(t, Z)
    if not h:
        continue
    if t.GetClass() == "PCB_VIA":
        k = ("via", t.GetNetname(), (round(tomm(t.GetPosition().x), 3), round(tomm(t.GetPosition().y), 3)))
    else:
        k = (t.GetLayerName(), t.GetNetname(), tuple(sorted([(round(tomm(t.GetStart().x), 3), round(tomm(t.GetStart().y), 3)), (round(tomm(t.GetEnd().x), 3), round(tomm(t.GetEnd().y), 3))])))
    if k in accept and not any(x.startswith(("imu", "u4")) for x in h):
        continue
    b.Remove(t); grave.append(t); cut[(t.GetNetname(), h[0].split()[0])] += 1
for k, v in sorted(cut.items()):
    print("cut", k, v)
print("nets:", ",".join(sorted({k[0] for k in cut})))
pcbnew.SaveBoard(sys.argv[2], b)
