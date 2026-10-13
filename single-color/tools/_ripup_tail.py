# footprint / board rule areas (keepouts): no vias / no tracks inside, as flagged in the rule area
for ko in d.get("keepouts", []):
    kg = Polygon(ko["pts"]).buffer(0)
    for ln in range(4):
        if ko["vias"]:
            paint(vstack, kg.buffer(VIA_D / 2 + MARGIN, 4), -1, ln)
        if ko["tracks"]:
            paint(tstack, kg.buffer(W / 2 + MARGIN, 4), -1, ln)

routes = {}                       # net -> list of ops ('seg', layer, p1, p2) / ('via', p)
added = {}                        # net -> copper pieces added by the router (for connectivity)
base_items = {n: list(v) for n, v in by_net.items()}
failed = []
IN2 = LI["In2.Cu"]
rips = {}


def paint_op(net, o, op):
    if op[0] == "seg":
        g = LineString([op[2], op[3]]).buffer(W / 2, 4)
        for st, inf in ((tsoft, INF_T), (vsoft, INF_V)):
            paint(st, g.buffer(inf, 4), o, LI[op[1]])
    else:
        g = Point(*op[1]).buffer(VIA_D / 2, 8)
        for ln in range(4):
            paint(tsoft, g.buffer(INF_TV, 4), o, ln)
            paint(vsoft, g.buffer(INF_V, 4), o, ln)
            paint(vsoft, Point(*op[1]).buffer(VIA_DRILL + 0.2 + MARGIN, 8), -1, ln)      # hole to hole


def rebuild_soft():
    for st in tsoft + vsoft:
        st[:] = 0
    for net, ops in routes.items():
        o = nid(net)
        for op in ops:
            paint_op(net, o, op)


def pieces_of(net):
    by_net[net] = base_items.get(net, []) + added.get(net, [])
    return components(net)


def commit(net, o, segs):
    ops = []
    pcs = []
    for s_ in segs:
        if s_[0] == "seg":
            op = ("seg", s_[1], s_[2], s_[3])
            pcs.append((LI[s_[1]], LineString([s_[2], s_[3]]).buffer(W / 2, 4), None))
        else:
            op = ("via", s_[1])
            g = Point(*s_[1]).buffer(VIA_D / 2, 8)
            vid = "newvia_%s_%.4f_%.4f" % (net, s_[1][0], s_[1][1])
            for ln in range(4):
                pcs.append((ln, g, vid))
        ops.append(op)
        paint_op(net, o, op)
    routes.setdefault(net, []).extend(ops)
    added.setdefault(net, []).extend(pcs)
    return pcs


def report(path, pops, t1, tag=""):
    segs = simplify(path)
    nseg = sum(1 for s_ in segs if s_[0] == "seg")
    nvia = sum(1 for s_ in segs if s_[0] == "via")
    ln_mm = sum(math.dist(s_[2], s_[3]) for s_ in segs if s_[0] == "seg")
    print(f"   routed{tag}: {nseg} segments, {nvia} vias, {ln_mm:.1f} mm, {pops} nodes, {time.time() - t1:.0f} s", flush=True)
    return segs


def geom_of(op):
    return LineString([op[2], op[3]]) if op[0] == "seg" else Point(*op[1])


def half(op):
    return W / 2 if op[0] == "seg" else VIA_D / 2


def victims_of(net, segs):
    """routed nets whose copper the new path would touch (clearance not met)"""
    vs = set()
    mine = [(a, geom_of(a)) for a in segs]
    for v, ops in routes.items():
        if v == net:
            continue
        hit = False
        for b in ops:
            gb = geom_of(b)
            for a, ga in mine:
                if a[0] == "seg" and b[0] == "seg" and a[1] != b[1]:
                    continue
                if ga.distance(gb) < half(a) + half(b) + CLR + MARGIN + (0.1 if "via" in (a[0], b[0]) else 0.0):
                    hit = True
                    break
            if hit:
                break
        if hit:
            vs.add(v)
    return vs


def rip_net(v):
    routes.pop(v, None)
    added.pop(v, None)
    rips[v] = rips.get(v, 0) + 1
    rebuild_soft()
    print(f"   ripped up {v} (x{rips[v]})", flush=True)


def route_net(net, rip=None):
    """connect all pieces of `net`; with rip: may cross rippable copper.  returns (ok, victims)"""
    o = nid(net)
    victims = set()
    if net == "GND":
        # ground is the In2 plane: every piece with no copper on In2 (no via, no through-hole pad) needs a via to it
        comps = pieces_of(net)
        todo = [c for c in comps if not any(it[0] == IN2 for it in c)]
        todo.sort(key=lambda c: -len(c))
        ok = True
        for c in todo:
            ma = comp_mask(c, (Hc, Wc))
            mb = np.zeros_like(ma)
            t2 = tstack[IN2]
            mb[IN2] = (t2 == 0) | (t2 == o)
            t1 = time.time()
            path, pops = astar(o, ma, mb, rip)
            if path is None:
                ok = False
                continue
            segs = report(path, pops, t1, " GND")
            if rip:
                vs = victims_of(net, segs)
                victims |= vs
                for v in vs:
                    rip_net(v)
            commit(net, o, segs)
        return ok, victims
    comps = pieces_of(net)
    tries = 0
    while len(comps) > 1 and tries < 12:
        tries += 1
        best = None
        for a in range(len(comps)):
            for b in range(a + 1, len(comps)):
                dd = comp_dist(comps[a], comps[b])
                if best is None or dd < best[0]:
                    best = (dd, a, b)
        _, a, b = best
        ma, mb = comp_mask(comps[a], (Hc, Wc)), comp_mask(comps[b], (Hc, Wc))
        t1 = time.time()
        path, pops = astar(o, ma, mb, rip)
        if path is None:
            print(f"   {net}: FAILED{' (rip mode)' if rip else ''}, closest pieces {best[0]:.2f} mm, {pops} nodes, {time.time() - t1:.0f} s", flush=True)
            if rip is None and "--dump" in sys.argv:
                pa_, pb_ = astar(o, mb, ma)[1], pops
                print(f"      reach from piece A: {pb_} cells, from piece B: {pa_} cells (the small one is boxed in)", flush=True)
                small = ma if pa_ > pb_ else mb
                other = mb if pa_ > pb_ else ma
                dump_fail(net, small, other)
            return False, victims
        segs = report(path, pops, t1, " (rip mode)" if rip else "")
        if rip:
            vs = victims_of(net, segs)
            victims |= vs
            for v in vs:
                rip_net(v)
        commit(net, o, segs)
        comps = pieces_of(net)
    return len(comps) <= 1, victims


def still_open(net):
    comps = pieces_of(net)
    if net == "GND":
        return any(not any(it[0] == IN2 for it in c) for c in comps)
    return len(comps) > 1



SEED = None
for a_i, a_v in enumerate(sys.argv):
    if a_v == "--seed":
        SEED = sys.argv[a_i + 1]
if SEED:
    import re as _re

    def _items(path):
        txt = open(path, encoding="utf8").read()
        out = {}
        for m in _re.finditer(r"\t\(segment\n(.*?)\n\t\)\n", txt, _re.S):
            b = m.group(1)
            st = _re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", b).groups()
            en = _re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", b).groups()
            out[("seg", _re.search(r'\(layer "([^"]*)"', b).group(1), _re.search(r'\(net "([^"]*)"', b).group(1), tuple(round(float(v), 4) for v in st + en))] = (st, en)
        for m in _re.finditer(r"\t\(via\n(.*?)\n\t\)\n", txt, _re.S):
            b = m.group(1)
            at = _re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", b).groups()
            out[("via", _re.search(r'\(net "([^"]*)"', b).group(1), tuple(round(float(v), 4) for v in at))] = at
        return out
    base_keys = set(_items(SRC))
    n_seed = 0
    for key, val in _items(SEED).items():
        if key in base_keys:
            continue
        if key[0] == "seg":
            net = key[2]
            op = ("seg", key[1], (float(val[0][0]), float(val[0][1])), (float(val[1][0]), float(val[1][1])))
            pc = [(LI[key[1]], LineString([op[2], op[3]]).buffer(W / 2, 4), None)]
        else:
            net = key[1]
            p_ = (float(val[0]), float(val[1]))
            op = ("via", p_)
            g_ = Point(*p_).buffer(VIA_D / 2, 8)
            pc = [(ln, g_, "newvia_%s_%.4f_%.4f" % (net, p_[0], p_[1])) for ln in range(4)]
        routes.setdefault(net, []).append(op)
        added.setdefault(net, []).extend(pc)
        n_seed += 1
    rebuild_soft()
    print("seeded", n_seed, "routed items from", SEED, flush=True)
    NETS_RUN = [n for n in NETS if still_open(n)]
    print("open after seeding:", NETS_RUN, flush=True)
    NETS = NETS_RUN

# phase 1: greedy in the given order
for net in NETS:
    print(net, flush=True)
    ok, _ = route_net(net)
    if not ok:
        failed.append(net)
print("phase 1 failed:", failed, flush=True)

# phase 2: rip-up and reroute
queue = list(failed)
failed = []
frozen = set()
attempts = 0
while queue and attempts < opt["--max-attempts"]:
    net = queue.pop(0)
    attempts += 1
    print(f"[attempt {attempts}] {net} (queue {len(queue)})", flush=True)
    if not still_open(net):
        continue
    ok, _ = route_net(net)
    if ok:
        continue
    if net in frozen:
        failed.append(net)
        continue
    ok, victims = route_net(net, rip=opt["--rip-cost"])
    for v in victims:
        if v not in queue and v != net:
            queue.append(v)
    if not ok:
        failed.append(net)
        frozen.add(net)
failed = [n for n in dict.fromkeys(failed + queue) if still_open(n)]
new = []
for net, ops in routes.items():
    for op in ops:
        new.append(op + (net,))
print("failed:", failed, flush=True)
