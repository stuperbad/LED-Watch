"""Prepare a Specctra DSN for freerouting around locked polar copper.
 - every existing wire/via becomes (type protect)  ('fix' makes freerouting 2.1 throw silent exceptions)
 - via clearances are set in BOTH the structure rule and the net-class rule (the class rule overrides the structure rule):
   JLCPCB via hole to track / inner copper = 0.2 mm; via pad 0.30 / hole 0.15 -> pad-to-copper clearance 0.125, plus margin = VIA_CLR um
usage: python prep_dsn.py in.dsn out.dsn [via_clr_um=140]
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
clr = int(sys.argv[3]) if len(sys.argv) > 3 else 140
s = open(src, encoding="utf8").read()
i = s.index("(wiring")
head, w = s[:i], s[i:]
w = re.sub(r"\(type \w+\)\)", "(type protect))", w)
w = re.sub(r'(\(via "[^"]*"\s+[-\d.]+\s+[-\d.]+\s*\(net [^)]*\))\)', r"\1(type protect))", w)

TYPES = ("wire_via", "via_via", "smd_via", "pin_via")


def typed(ind):
    return "".join(f"\n{ind}(clearance {clr} (type {t}))" for t in TYPES)


out, lines = [], head.split("\n")
for k, ln in enumerate(lines):
    out.append(ln)
    m = re.match(r"^( +)\(clearance (?:100|25 \(type smd_smd\))\)$", ln)
    nxt = lines[k + 1] if k + 1 < len(lines) else ""
    if m and "(type wire_via" not in nxt and "smd_smd" not in nxt and "(type" not in nxt:
        out.append(typed(m.group(1)).lstrip("\n"))
head = "\n".join(out)
head = re.sub(r"\(clearance (?:2\d\d) \(type", f"(clearance {clr} (type", head)
# freerouting 2.1 throws a NullPointerException when In2.Cu is (type power), so In2 stays a signal layer; instead nothing but the
# ground plane may sit under the crystal circuit (AVR datasheet 4.5.1): keep a keepout on In2 around Y1 and its load caps
m_ = re.search(r"\(place Y1 ([-\d.]+) ([-\d.]+)", head)
if m_:
    yx_, yy_ = float(m_.group(1)), float(m_.group(2))
    ko = "    (keepout xtal_in2 (polygon In2.Cu 0  %d %d  %d %d  %d %d  %d %d))\n" % (
        yx_ - 1500, yy_ - 3000, yx_ + 5000, yy_ - 3000, yx_ + 5000, yy_ + 3000, yx_ - 1500, yy_ + 3000)
    k_ = head.index("    (via ")
    head = head[:k_] + ko + head[k_:]
open(dst, "w", encoding="utf8").write(head + w)
print("protect items:", w.count("(type protect)"), "| typed clearance sets:", head.count("(type wire_via"))
