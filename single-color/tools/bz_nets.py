"""Wire the piezo BZ1 to the two spare MCU pins PB4 (pad 8) and PB5 (pad 9): nets /BUZ_A and /BUZ_B.  usage (KiCad python): bz_nets.py in out"""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
fp = {f.GetReference(): f for f in b.GetFootprints()}
for p in fp["U1"].Pads():
    if p.GetNumber() in ("8", "9"):
        assert not p.GetNetname(), "U1 pad %s already has net %s" % (p.GetNumber(), p.GetNetname())
for n in ("/BUZ_A", "/BUZ_B"):
    if not b.FindNet(n):
        b.Add(pcbnew.NETINFO_ITEM(b, n))
for ref, pad, net in (("U1", "8", "/BUZ_A"), ("U1", "9", "/BUZ_B"), ("BZ1", "1", "/BUZ_A"), ("BZ1", "2", "/BUZ_B")):
    for p in fp[ref].Pads():
        if p.GetNumber() == pad:
            p.SetNet(b.FindNet(net))
pcbnew.SaveBoard(sys.argv[2], b)
print("U1 pads 8/9 and BZ1 pads 1/2 now on /BUZ_A and /BUZ_B")
