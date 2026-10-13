"""Filter a Specctra session so it can be imported onto the UNROUTED base board and then topped up with polar_rows.py.
Removes the (placement) block and, for each ROW net, every wire/via that lies entirely in the LED band (radius >= KEEP_R):
those are the polar stubs/lanes polar_rows.py draws itself. Wires reaching the free centre (lane -> MCU pin) are kept.
usage: python ses_keep_nonpolar.py in.ses out.ses [keep_radius_mm]"""
import math, re, sys
src, dst = sys.argv[1], sys.argv[2]
KEEP_R = float(sys.argv[3]) if len(sys.argv) > 3 else 13.8
t = open(src, encoding="utf8").read()

def block_end(s, i):
    d = 0
    for k in range(i, len(s)):
        d += (s[k] == "(") - (s[k] == ")")
        if d == 0:
            return k + 1
    raise ValueError

i = t.index("  (placement"); t = t[:i] + t[block_end(t, i):]
pos = 0
while True:
    m = re.search(r"\(net /ROW\d+\n", t[pos:])
    if not m:
        break
    i = pos + m.start(); j = block_end(t, i); blk = t[i:j]
    name = re.match(r"\(net (\S+)", blk).group(1); body = blk[blk.index("\n"):]
    keep, p = [], 0
    while True:
        mm = re.search(r"\((wire|via)\b", body[p:])
        if not mm:
            break
        s0 = p + mm.start(); e0 = block_end(body, s0); item = body[s0:e0]; p = e0
        radii = [math.hypot(float(a) / 1e4 - 100, -float(b) / 1e4 - 100) for a, b in re.findall(r"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)", item)]
        if radii and any(r < KEEP_R for r in radii):
            keep.append(item)
    nb = ("(net " + name + "\n      " + "\n      ".join(keep) + "\n    )") if keep else ""
    t = t[:i] + nb + t[j:]
    pos = i + len(nb)
open(dst, "w", encoding="utf8").write(t)
print("written", dst)
