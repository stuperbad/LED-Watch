import pcbnew, math
board = pcbnew.GetBoard()
cx, cy = 100, 100  # mm
rings = [(35, range(2,14)), (37, range(14,74)), (39, range(74,134))]
for radius, nums in rings:
    refs = [f"U{i}" for i in nums if board.FindFootprintByReference(f"U{i}")]
    for j, ref in enumerate(refs):
        fp = board.FindFootprintByReference(ref)
        angle = math.radians(360*j/len(refs))
        fp.SetPosition(pcbnew.VECTOR2I(int((cx+radius*math.cos(angle))*1e6),
                                       int((cy+radius*math.sin(angle))*1e6)))
        fp.SetOrientationDegrees(0)
pcbnew.Refresh()

