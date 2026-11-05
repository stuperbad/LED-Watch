import math
def seg_pt_dist(p, a, c):
    dx, dy = c[0]-a[0], c[1]-a[1]; L2 = dx*dx+dy*dy
    if L2 == 0: return math.hypot(p[0]-a[0], p[1]-a[1])
    u = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2)); return math.hypot(p[0]-a[0]-u*dx, p[1]-a[1]-u*dy)
def seg_seg_dist(a, b, c, d):
    # min distance between segments (non crossing assumed for different nets)
    best = min(seg_pt_dist(a, c, d), seg_pt_dist(b, c, d), seg_pt_dist(c, a, b), seg_pt_dist(d, a, b))
    # crossing check
    def o(p, q, r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    if o(a, b, c)*o(a, b, d) < 0 and o(c, d, a)*o(c, d, b) < 0: return 0.0
    return best
