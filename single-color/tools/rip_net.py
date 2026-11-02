"""rip_net.py in out CX CY R NET...  remove every track/via of the given nets that has an end within R of (CX,CY) (poly boards only: straight tracks)"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); cx, cy, R = (float(x) for x in sys.argv[3:6]); nets = set(sys.argv[6:])
mm = lambda v: v / 1e6
kill = {}
for t in b.GetTracks():
    if t.GetNetname() not in nets: continue
    pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
    if any(abs(mm(p.x) - cx) <= R and abs(mm(p.y) - cy) <= R for p in pts):
        kill[t.m_Uuid.AsString()] = t
for t in kill.values(): b.Remove(t)
print("removed", len(kill))
pcbnew.SaveBoard(sys.argv[2], b)
