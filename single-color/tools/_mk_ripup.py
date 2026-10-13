"""one-off generator: builds grid_route2.py (grid router with rip-up) from grid_route.py"""
from pathlib import Path

here = Path(__file__).resolve().parent
s = (here / "grid_route.py").read_text(encoding="utf8")

s = s.replace("Small grid router for", "Grid router WITH RIP-UP (grid_route.py + negotiated rip-up of the nets in the way) for", 1)
s = s.replace('"--in2-cost": 2.5,', '"--in2-cost": 2.5, "--rip-cost": 25.0, "--max-attempts": 400, "--max-nodes": 1500000,')
s = s.replace("cstack = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]   # raw copper (net ids), for sources / targets",
              "cstack = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]   # raw copper (net ids), for sources / targets\n"
              "tsoft = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]    # copper routed in this run (rippable), inflated for tracks\n"
              "vsoft = [np.zeros((Hc, Wc), dtype=np.int32) for _ in ALL_LAYERS]    # same, inflated for via centres")
s = s.replace("def astar(net_o, src_mask, dst_mask):", "def astar(net_o, src_mask, dst_mask, rip=None):")
old = """    free = []
    for ln in RL:
        t = tstack[ln]
        free.append(((t == 0) | (t == net_o)).ravel())"""
new = """    free = []
    soft = []
    for ln in RL:
        t = tstack[ln]
        f = (t == 0) | (t == net_o)
        sf = (tsoft[ln] != 0) & (tsoft[ln] != net_o)
        if rip is None:
            f &= ~sf                      # hard mode: routed copper of other nets is an obstacle
        free.append(f.ravel())
        soft.append(sf.ravel().tolist())"""
assert old in s
s = s.replace(old, new)
old = """    vok = np.ones((Hc, Wc), dtype=bool)
    for ln in range(4):
        v = vstack[ln]
        vok &= (v == 0) | (v == net_o)
    vok = vok.ravel()"""
new = """    vok = np.ones((Hc, Wc), dtype=bool)
    vsf = np.zeros((Hc, Wc), dtype=bool)
    for ln in range(4):
        v = vstack[ln]
        vok &= (v == 0) | (v == net_o)
        vsf |= (vsoft[ln] != 0) & (vsoft[ln] != net_o)
    if rip is None:
        vok &= ~vsf
    vok = vok.ravel()
    vsf = vsf.ravel().tolist()"""
assert old in s
s = s.replace(old, new)
old = "            ng = gc + c * LCOST[k]\n"
assert old in s
s = s.replace(old, "            ng = gc + c * LCOST[k] + (rip if (rip and soft[k][j]) else 0.0)\n")
old = "                    ng = gc + VIA_COST\n"
assert old in s
s = s.replace(old, "                    ng = gc + VIA_COST + (rip if (rip and vsf[i]) else 0.0)\n")
old = "        pops += 1\n        if dsts[k][i]:"
assert old in s
s = s.replace(old, "        pops += 1\n        if pops > MAX_NODES:\n            return None, pops\n        if dsts[k][i]:")
s = s.replace("RL = [LI[n] for n in ROUTE]       # routing layer indices", "MAX_NODES = opt['--max-nodes']\nRL = [LI[n] for n in ROUTE]       # routing layer indices")

i = s.index("new = []   # ('seg'")
j = s.index("# ---- write")
tail = (here / "_ripup_tail.py").read_text(encoding="utf8")
s = s[:i] + tail + "\n" + s[j:]
(here / "grid_route2.py").write_text(s, encoding="utf8")
print("written grid_route2.py")
