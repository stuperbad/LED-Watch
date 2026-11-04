"""via_cands.py BOARD OUT.json : candidates for removing vias without changing what a net connects: a 'hop' = via V1 -- chain on layer B -- via V2 where both vias have exactly the layers {A, B} and A is the same on both sides (A -> B -> A);
the chain on B has no branch. Replacing the chain by a direct route on A removes two vias. Also lists plain statistics per net."""
import pcbnew, sys, json, re, collections, math
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
ring = re.compile(r"^/(ROW|COL)\d+$")
LN = lambda l: b.GetLayerName(l)
pt = lambda p: (p.x, p.y)
pieces = collections.defaultdict(list)   # net -> straight pieces
vias = collections.defaultdict(list)
arcs_at = set()
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA": vias[t.GetNetname()].append(t)
    elif t.GetClass() == "PCB_TRACK": pieces[t.GetNetname()].append(t)
    else: arcs_at.add((t.GetLayer(), pt(t.GetStart()))); arcs_at.add((t.GetLayer(), pt(t.GetEnd())))
padpos = collections.defaultdict(set)
for f in b.GetFootprints():
    for p in f.Pads(): padpos[p.GetNetname()].add(pt(p.GetPosition()))
stats = {}
cands = []
for net, vs in vias.items():
    if net == "GND" or ring.match(net) or not net: continue
    ends = collections.defaultdict(list)          # (layer, point) -> pieces
    for t in pieces[net]:
        ends[(t.GetLayer(), pt(t.GetStart()))].append(t); ends[(t.GetLayer(), pt(t.GetEnd()))].append(t)
    viaat = {pt(v.GetPosition()): v for v in vs}
    def layers_at(p): return sorted({k[0] for k in ends if k[1] == p} | {l for l, q in arcs_at if q == p})
    pass_vias = {}
    for p, v in viaat.items():
        L = layers_at(p)
        if len(L) == 2 and p not in padpos[net] and all(len(ends[(l, p)]) == 1 for l in L if (l, p) in ends): pass_vias[p] = L
    stats[net] = dict(vias=len(vs), pass_vias=len(pass_vias))
    for p1, L1 in pass_vias.items():
        for B in L1:
            A = [l for l in L1 if l != B][0]
            # walk along layer B from p1
            cur = p1; chain = []; prev = None
            while True:
                nxt = [t for t in ends.get((B, cur), []) if t not in chain]
                if len(nxt) != 1: break
                t = nxt[0]; chain.append(t)
                o = pt(t.GetEnd()) if pt(t.GetStart()) == cur else pt(t.GetStart())
                if o in viaat or o in padpos[net] or (B, o) in arcs_at: cur = o; break
                if len(ends.get((B, o), [])) != 2 or any(k[1] == o and k[0] != B for k in ends): cur = o; break   # branch / other layer
                cur = o
            if cur == p1 or not chain: continue
            p2 = cur
            if p2 in pass_vias and p2 != p1 and B in pass_vias[p2] and ((A, p1) in ends):
                C_ = [l for l in pass_vias[p2] if l != B][0]
                if C_ != A and (C_, p2) not in ends: continue
                if C_ == A and (A, p2) not in ends: continue
                key = tuple(sorted((p1, p2)))
                if any(c["key"] == key for c in cands): continue
                lenB = sum(mm(t.GetLength()) for t in chain)
                cands.append(dict(kind='hop' if C_ == A else 'bridge', C=LN(C_), net=net, key=key, v1=[mm(p1[0]), mm(p1[1])], v2=[mm(p2[0]), mm(p2[1])], A=LN(A), B=LN(B), lenB=round(lenB, 3), npieces=len(chain),
                                  chain=[[mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y)] for t in chain], w=mm(chain[0].GetWidth())))
tot = sum(s["vias"] for s in stats.values())
print("non-GND, non-ring nets with vias:", len(stats), " vias:", tot, " pass-through vias (exactly two layers, no pad):", sum(s["pass_vias"] for s in stats.values()))
print("via-heaviest nets:", sorted(((s["vias"], n) for n, s in stats.items()), reverse=True)[:12])
print("candidates: hop (A -> B -> A):", sum(1 for c in cands if c["kind"]=="hop"), " bridge (A -> B -> C):", sum(1 for c in cands if c["kind"]=="bridge"))
for c in sorted(cands, key=lambda c: c["lenB"]): print("  %-12s %s %s via (%.3f, %.3f) - (%.3f, %.3f): chain on %s %d piece(s) %.2f mm, outer layer %s" % (c["net"], c["kind"], "", c["v1"][0], c["v1"][1], c["v2"][0], c["v2"][1], c["B"], c["npieces"], c["lenB"], c["A"]))
for c in cands: c["key"] = list(c["key"])
json.dump(cands, open(sys.argv[2], "w"))
