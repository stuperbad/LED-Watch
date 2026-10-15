"""Remove what KiCad itself reports as dangling (via_dangling / track_dangling), round after round, until nothing is left, never letting the unconnected count grow.
Needs KiCad's python for the editing step (run through its own interpreter) and kicad-cli for the DRC.  Only the nets given are touched.
usage (any python): prune_dangling_loop.py in.kicad_pcb out.kicad_pcb NET [NET ...]       (a .kicad_pro with the same base name as in.kicad_pcb must sit next to it)
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

KCLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
KPY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
src, dst = sys.argv[1], sys.argv[2]
NETS = set(sys.argv[3:])
work = tempfile.mkdtemp()
base = os.path.splitext(os.path.basename(src))[0]
shutil.copy(src, os.path.join(work, "cur.kicad_pcb"))
pro = os.path.splitext(src)[0] + ".kicad_pro"
shutil.copy(pro, os.path.join(work, "cur.kicad_pro"))

REMOVER = r'''
import json, math, sys
import pcbnew
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
items = json.load(open(sys.argv[3]))
kill = set()
for it in items:
    for t in b.GetTracks():
        if t.GetNetname() != it["net"]:
            continue
        if it["kind"] == "via" and t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if math.hypot(mm(p.x) - it["x"], mm(p.y) - it["y"]) < 0.02:
                kill.add(t.m_Uuid.AsString())
                # a junction: track ends of this net on ONE layer that touch the via (within its copper) but not each other are joined by a short track
                ends = []
                for o in b.GetTracks():
                    if o.GetNetname() == it["net"] and o.GetClass() == "PCB_TRACK":
                        for q in (o.GetStart(), o.GetEnd()):
                            if math.hypot(mm(q.x) - it["x"], mm(q.y) - it["y"]) < 0.17:
                                ends.append((o.GetLayer(), q, o.GetWidth(), o.m_Uuid.AsString()))
                for i in range(len(ends)):
                    for j in range(i + 1, len(ends)):
                        la, qa, w, ua = ends[i]
                        lb, qb, _w, ub = ends[j]
                        if la == lb and ua != ub and math.hypot(mm(qa.x - qb.x), mm(qa.y - qb.y)) > 0.005:
                            tr = pcbnew.PCB_TRACK(b)
                            tr.SetStart(qa)
                            tr.SetEnd(qb)
                            tr.SetWidth(w)
                            tr.SetLayer(la)
                            tr.SetNet(t.GetNet())
                            b.Add(tr)
        elif it["kind"] == "track" and t.GetClass() == "PCB_TRACK":
            s, e = t.GetStart(), t.GetEnd()
            d0 = min(math.hypot(mm(q.x) - it["x"], mm(q.y) - it["y"]) for q in (s, e, pcbnew.VECTOR2I((s.x + e.x) // 2, (s.y + e.y) // 2)))   # DRC reports a start point
            if not (d0 < 0.03 and abs(mm(t.GetLength()) - it["len"]) < 0.01 and b.GetLayerName(t.GetLayer()) == it["layer"]):
                continue
            net = it["net"]
            others = [o for o in b.GetTracks() if o.GetNetname() == net and o.m_Uuid.AsString() != t.m_Uuid.AsString()]
            pads = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]

            def touches(q):
                for o in others:
                    if o.GetClass() == "PCB_VIA":
                        pp = o.GetPosition()
                        if math.hypot(mm(pp.x - q.x), mm(pp.y - q.y)) < 0.17:
                            return True
                    elif o.GetLayer() == t.GetLayer() and o.GetClass() == "PCB_TRACK":
                        a, c = o.GetStart(), o.GetEnd()
                        ux, uy, wx, wy = mm(c.x - a.x), mm(c.y - a.y), mm(q.x - a.x), mm(q.y - a.y)
                        L2 = ux * ux + uy * uy
                        tt = max(0.0, min(1.0, (wx * ux + wy * uy) / L2)) if L2 else 0.0
                        if math.hypot(wx - tt * ux, wy - tt * uy) < 0.06:      # an end within the other track's copper (width 0.1) is connected, T junctions included
                            return True
                return any(pd.IsOnLayer(t.GetLayer()) and pd.HitTest(q, 0) for pd in pads)
            free = [(q, which) for q, which in ((s, "s"), (e, "e")) if not touches(q)]
            if not free:
                continue
            q_free, which = free[0]
            q_other = e if which == "s" else s
            # a T junction: another track of the net that ends ON the body of this track between its ends -> shorten to the T instead of removing it
            L = math.hypot(mm(e.x - s.x), mm(e.y - s.y))
            best = None
            for o in others:
                if o.GetClass() == "PCB_VIA" or o.GetLayer() != t.GetLayer():
                    continue
                for q2 in (o.GetStart(), o.GetEnd()):
                    ux, uy = mm(e.x - s.x), mm(e.y - s.y)
                    wx, wy = mm(q2.x - s.x), mm(q2.y - s.y)
                    tt = (wx * ux + wy * uy) / (L * L) if L else 0
                    if 0.01 < tt < 0.99:
                        dist = abs(wx * uy - wy * ux) / L
                        if dist < 0.06:
                            dfree = math.hypot(mm(q2.x - q_free.x), mm(q2.y - q_free.y))
                            proj = pcbnew.VECTOR2I(int(s.x + tt * (e.x - s.x)), int(s.y + tt * (e.y - s.y)))   # the T point on this track's own axis
                            if best is None or dfree < best[0]:
                                best = (dfree, proj)
            if best is not None:
                if which == "s":
                    t.SetStart(best[1])
                else:
                    t.SetEnd(best[1])
            else:
                kill.add(t.m_Uuid.AsString())
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in kill:
        b.Remove(t)
pcbnew.SaveBoard(sys.argv[2], b)
print(len(kill))
'''
open(os.path.join(work, "remover.py"), "w").write(REMOVER)


def drc(board):
    out = os.path.join(work, "drc.json")
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, board], capture_output=True)
    d = json.load(open(out))
    dang = []
    for v in d["violations"]:
        if v["type"] in ("via_dangling", "track_dangling"):
            for it in v["items"]:
                desc = it["description"]
                net = desc.split("[")[1].split("]")[0] if "[" in desc else ""
                if net not in NETS:
                    continue
                if "Via" in desc:
                    dang.append(dict(kind="via", net=net, x=it["pos"]["x"], y=it["pos"]["y"]))
                elif "(arc)" not in desc:
                    length = float(desc.split("length")[1].split("mm")[0])
                    layer = desc.split(" on ")[1].split(",")[0]
                    dang.append(dict(kind="track", net=net, x=it["pos"]["x"], y=it["pos"]["y"], len=length, layer=layer))
    return dang, len(d["unconnected_items"])


cur = os.path.join(work, "cur.kicad_pcb")
dang, unc0 = drc(cur)
print("start: %d dangling items on the chosen nets, %d unconnected" % (len(dang), unc0))
for rnd in range(1, 40):
    if not dang:
        break
    json.dump(dang, open(os.path.join(work, "items.json"), "w"))
    nxt = os.path.join(work, "next.kicad_pcb")
    shutil.copy(os.path.join(work, "cur.kicad_pro"), os.path.join(work, "next.kicad_pro"))
    r = subprocess.run([KPY, os.path.join(work, "remover.py"), cur, nxt, os.path.join(work, "items.json")], capture_output=True, text=True)
    d2, unc = drc(nxt)
    print("   items:", [(i["kind"], i["net"], round(i["x"],3), round(i["y"],3), i.get("len")) for i in dang])
    print("round %d: removed %s items -> %d dangling, %d unconnected" % (rnd, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?", len(d2), unc))
    if r.stdout.strip().splitlines()[-1:] == ["0"]:
        print("  nothing matched, stuck on:", [(i["kind"], i["net"], round(i["x"], 3), round(i["y"], 3), i.get("len"), i.get("layer")) for i in dang])
        break
    if unc > unc0:
        print("  the unconnected count grew: undone, stopping")
        shutil.copy(nxt, os.path.join(os.path.dirname(dst), "pruned_but_broken.kicad_pcb"))
        break
    shutil.copy(nxt, cur)
    dang = d2
shutil.copy(cur, dst)
print("wrote", dst)
