"""align_gct_step.py IN.STEP OUT.step : put GCT's own USB4110-GF-A STEP model (downloaded by hand, e.g. from SnapMagic / DigiKey) into KiCad's model frame for the project's J2 footprint.
GCT frame: x = width, y = height above the board (0 .. 3.26), z = depth (pegs at z = 0, opening towards +z).  KiCad frame for this footprint: x = width, y = -footprint y, z = up; the opening at y = -3.675,
the pegs at y = +2.605.  So: rotate 90 degrees about X (y' = -z, z' = y), then move +2.605 in y.  Check: the front face lands on y = -3.675 (the footprint's body outline).  Needs build123d."""
import sys, os
if os.environ.get("PYLIB"): sys.path.insert(0, os.environ["PYLIB"])
from build123d import import_step, export_step, Axis, Pos
s = Pos(0, 2.605, 0) * import_step(sys.argv[1]).rotate(Axis.X, 90); bb = s.bounding_box()
print("bbox x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z)); export_step(s, sys.argv[2])
