"""exposure.py BOARD [--min 0.15] : for every pad of the board with exactly one piece or more leaving at its centre: how far does the first straight piece run OUTSIDE the pad copper before it ends (a bend or a junction)?
The owner's rule (2026-11-04): at least 1.5 track widths exposed before the first bend; 45-degree pieces at least width x 1.414 long."""
import pcbnew, sys, math
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
MIN = float(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 0.15
rows = []; n = 0
for f in b.GetFootprints():
    for p in f.Pads():
        if not p.GetNetname(): continue
        pc = p.GetPosition(); layer = None
        for lid in (pcbnew.F_Cu, pcbnew.B_Cu):
            if p.IsOnLayer(lid) and p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH: layer = lid
        if layer is None: continue
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetLayer() != layer or t.GetNetname() != p.GetNetname(): continue
            for e, o in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
                if (e.x, e.y) != (pc.x, pc.y): continue
                L = t.GetLength(); dx, dy = (o.x - e.x) / L, (o.y - e.y) / L
                # distance along the piece until it is outside the pad copper (0.005 mm steps)
                exit_d = 0.0; k = 0
                while k * 5000 < L:
                    q = pcbnew.VECTOR2I(int(e.x + dx * k * 5000), int(e.y + dy * k * 5000))
                    if p.HitTest(q): exit_d = k * 0.005
                    k += 1
                expo = mm(L) - exit_d - 0.005; n += 1
                if expo < MIN - 1e-9: rows.append((round(expo, 3), f.GetReference() + "." + p.GetNumber(), b.GetLayerName(layer), round(mm(L), 3), round(exit_d, 3), round(math.degrees(math.atan2(-(o.y - e.y), o.x - e.x)) % 360, 1)))
print("pad exits measured: %d, with less than %.2f mm of piece outside the pad before it ends: %d" % (n, MIN, len(rows)))
for r in sorted(rows): print("  %-8s %s  exposed %.3f mm (piece %.3f mm, %.3f mm of it inside the pad), leaves at %.1f deg" % (r[1], r[2], r[0], r[3], r[4], r[5]))
