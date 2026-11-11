"""rework_edit.py IN.kicad_pcb OUT.kicad_pcb EDITS.json (KiCad python) : add tracks / vias to a board.
EDITS = [{"track": [net, layer, width, [[x, y], [x, y], ...]]}, {"via": [net, x, y]}, {"del_track_net_near": [net, x, y, r]}]   (mm; a polyline becomes one track piece per leg, ends exactly on the given points)"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); E = json.load(open(sys.argv[3])); FM = pcbnew.FromMM; V = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))
nets = b.GetNetsByName(); nt = 0; nv = 0
for e in E:
    if "track" in e:
        net, layer, w, pts = e["track"]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetWidth(FM(w)); t.SetLayer(b.GetLayerID(layer)); t.SetNet(nets[net]); b.Add(t); nt += 1
    elif "via" in e:
        net, x, y = e["via"]; v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(FM(0.3)); v.SetDrill(FM(0.15)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); b.Add(v); nv += 1
pcbnew.SaveBoard(sys.argv[2], b); print("added", nt, "track pieces,", nv, "vias")
