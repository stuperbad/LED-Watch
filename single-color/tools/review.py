import sys, math, collections, pcbnew
from shapely_free import seg_seg_dist
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM; LN = b.GetLayerName
trk = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        s, e = t.GetStart(), t.GetEnd(); trk.append(dict(net=t.GetNetname(), layer=LN(t.GetLayer()), a=(mm(s.x), mm(s.y)), c=(mm(e.x), mm(e.y)), w=mm(t.GetWidth()), len=mm(t.GetLength())))
    elif t.GetClass() == "PCB_ARC":
        s, e = t.GetStart(), t.GetEnd(); trk.append(dict(net=t.GetNetname(), layer=LN(t.GetLayer()), a=(mm(s.x), mm(s.y)), c=(mm(e.x), mm(e.y)), w=mm(t.GetWidth()), len=mm(t.GetLength())))
vias = [dict(net=t.GetNetname(), p=(mm(t.GetPosition().x), mm(t.GetPosition().y))) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
# 1. what runs under the bodies (courtyard) of the interesting parts, any layer, foreign nets
print("== copper under part bodies (courtyard box, foreign nets)")
interest = ["L1", "L2", "Y1", "U1", "U2", "U4", "U5", "D50", "D51", "J2", "BZ1", "C54", "C52"]
for r in interest:
    f = b.FindFootprintByReference(r)
    if not f: continue
    own = {p.GetNetname() for p in f.Pads()}
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
    x0, y0, x1, y1 = mm(cy.GetX()), mm(cy.GetY()), mm(cy.GetRight()), mm(cy.GetBottom())
    cnt = collections.defaultdict(lambda: collections.Counter())
    for t in trk:
        if t["net"] in own or t["net"] == "": continue
        n = 0
        for i in range(11):
            x = t["a"][0]+(t["c"][0]-t["a"][0])*i/10; y = t["a"][1]+(t["c"][1]-t["a"][1])*i/10
            if x0 <= x <= x1 and y0 <= y <= y1: n += 1
        if n: cnt[t["layer"]][t["net"]] += t["len"] * n / 11
    vv = collections.Counter(v["net"] for v in vias if x0 <= v["p"][0] <= x1 and y0 <= v["p"][1] <= y1 and v["net"] not in own)
    print("%-4s %-24s side %s  box %.1f-%.1f x %.1f-%.1f" % (r, f.GetValue()[:24], "back" if f.IsFlipped() else "front", x0, x1, y0, y1))
    for L, c in cnt.items(): print("     %-7s %s" % (L, ", ".join("%s %.1f mm" % (n, l) for n, l in c.most_common(8))))
    if vv: print("     vias    %s" % dict(vv))
# 2. switching nodes against sensitive nets: closest approach on the same layer and on neighbouring layers
print("== aggressors vs victims: closest approach (mm centre to centre) and length closer than 0.5 mm")
agg = ["/LBUCK", "/LBOOST", "/SOLAR_IN"]; vic = ["/VREF_SAMP", "/VRDIV", "/VBAT_OV", "/VOUT_SET", "/OK_HYST", "/OK_PROG", "/BAT_OK", "/XTAL1", "/XTAL2"]
for a_ in agg:
    for v_ in vic:
        best = (9, None); close = 0.0
        for t1 in trk:
            if t1["net"] != a_: continue
            for t2 in trk:
                if t2["net"] != v_: continue
                if abs(t1["a"][0]-t2["a"][0]) > 6 and abs(t1["c"][0]-t2["c"][0]) > 6: continue
                d = seg_seg_dist(t1["a"], t1["c"], t2["a"], t2["c"])
                same = t1["layer"] == t2["layer"]
                if d < best[0]: best = (d, (t1["layer"], t2["layer"], t1["a"], t2["a"]))
                if d < 0.5: close += min(t1["len"], t2["len"]) * (1 if same else 0.5)
        if best[0] < 0.6: print("%-10s %-11s %.2f mm  (%s/%s at %s)  close-run ~%.1f mm" % (a_, v_, best[0], best[1][0], best[1][1], (round(best[1][2][0], 1), round(best[1][2][1], 1)), close))
# 3. via in pad / thermal pad vias
print("== vias inside big pads")
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetSizeX() > 1.5e6 and p.GetSizeY() > 1.5e6 and f.GetReference() in ("U1", "U4"):
            bb = p.GetBoundingBox(); x0, y0, x1, y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
            n = sum(1 for v in vias if x0 <= v["p"][0] <= x1 and y0 <= v["p"][1] <= y1)
            print(f.GetReference(), p.GetNumber(), p.GetNetname(), "vias in the exposed pad:", n)
# 4. widths
print("== track width by net (power nets)")
w = collections.defaultdict(collections.Counter)
for t in trk: w[t["net"]][round(t["w"], 3)] += t["len"]
for n in ["GND", "VBAT", "/BATT", "+3V3", "VBUS", "/SOLAR_IN", "/LBOOST", "/LBUCK", "SC_MID"]:
    if n in w: print("%-10s" % n, {k: round(v, 1) for k, v in w[n].items()})
tot = collections.Counter()
for t in trk: tot[round(t["w"], 3)] += t["len"]
print("all widths:", {k: round(v, 0) for k, v in tot.items()})
