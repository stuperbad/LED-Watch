"""refill all zones and save: usage (KiCad python) refill.py in.kicad_pcb out.kicad_pcb"""
import sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print("refilled", len(b.Zones()), "zones")
