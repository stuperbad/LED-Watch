"""via_route.py grid.json cands.json OUT.json [--detour 0.6] : for every candidate (hop A-B-A: remove both vias; bridge A-B-C: remove one via) route the two via centres together on a single layer with an
8-direction A* (turns of at most 90 degrees), 0.10 mm clearance to every other net's copper on that layer, grid 0.025 mm; the result is simplified to straight pieces and, when the second via is
off the grid, refitted so it ends exactly on the via centre; each piece >= 0.15 mm; accepted when the new route is at most (old chain + detour) long."""
import json, math, sys, heapq
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon
args = sys.argv[1:]; detour = 0.6
if "--detour" in args: detour = float(args[args.index("--detour") + 1])
G = json.load(open(args[0])); C = json.load(open(args[1]))
STEP = 0.025; CLR = 0.10
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]

def obstacles(layer, net, box):
    """shapely shapes (already inflated by the track half width is added by the caller) of other nets' copper on `layer` near box"""
    out = []
    for t in G["trk"]:
        if "arc" in t or t["layer"] != layer or t["net"] == net: continue
        if max(t["x1"], t["x2"]) < box[0] or min(t["x1"], t["x2"]) > box[2] or max(t["y1"], t["y2"]) < box[1] or min(t["y1"], t["y2"]) > box[3]: continue
        out.append(LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2))
    for p in G["pads"]:
        if p["layer"] != layer or p["net"] == net or len(p["pts"]) < 3: continue
        xs = [q[0] for q in p["pts"]]; ys = [q[1] for q in p["pts"]]
        if max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3]: continue
        out.append(Polygon(p["pts"]))
    for v in G["via"]:
        if v["net"] != net and box[0] < v["x"] < box[2] and box[1] < v["y"] < box[3]: out.append(Point(v["x"], v["y"]).buffer(v["d"] / 2))
    for c in G["circles"]:
        if c["net"] != net and box[0] < c["x"] < box[2] and box[1] < c["y"] < box[3]: out.append(Point(c["x"], c["y"]).buffer(c["r"]))
    return out

def solve(c, layer, p1, p2):
    w = c["w"]; maxlen = c["lenB"] + detour
    box = [min(p1[0], p2[0]) - 3, min(p1[1], p2[1]) - 3, max(p1[0], p2[0]) + 3, max(p1[1], p2[1]) + 3]
    obs = obstacles(layer, c["net"], [box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1])
    ox = p1[0] - round((p1[0] - box[0]) / STEP) * STEP; oy = p1[1] - round((p1[1] - box[1]) / STEP) * STEP
    W = int((box[2] - ox) / STEP) + 2; H = int((box[3] - oy) / STEP) + 2
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for o in obs:
        g = o.buffer(w / 2 + CLR)
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.geom_type == "Polygon": d.polygon([((x - ox) / STEP, (y - oy) / STEP) for x, y in part.exterior.coords], fill=255)
    M = np.array(im) > 0
    sx, sy = round((p1[0] - ox) / STEP), round((p1[1] - oy) / STEP); gx, gy = round((p2[0] - ox) / STEP), round((p2[1] - oy) / STEP)
    offgrid = abs(ox + gx * STEP - p2[0]) > 0.003 or abs(oy + gy * STEP - p2[1]) > 0.003
    best = {(sx, sy, -1): 0.0}; came = {}; pq = [(0.0, 0.0, sx, sy, -1)]; found = None
    while pq:
        f, g, x, y, dr = heapq.heappop(pq)
        if best.get((x, y, dr), 1e9) < g - 1e-9: continue
        if (x, y) == (gx, gy): found = (x, y, dr); break
        for k, (dx, dy) in enumerate(DIRS):
            turn = 0
            if dr >= 0:
                turn = min((k - dr) % 8, (dr - k) % 8)
                if turn > 2: continue
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H) or M[ny, nx]: continue
            ng = g + STEP * (math.sqrt(2) if dx and dy else 1) + (0.15 if turn else 0.0)
            if ng > maxlen + 1.0: continue
            key = (nx, ny, k)
            if ng < best.get(key, 1e9) - 1e-9:
                best[key] = ng; came[key] = (x, y, dr); heapq.heappush(pq, (ng + math.hypot(gx - nx, gy - ny) * STEP, ng, nx, ny, k))
    if not found: return dict(ok=False, why="no path")
    path = []; key = found
    while True:
        path.append(key)
        if key[:2] == (sx, sy) and key[2] == -1: break
        key = came[key]
    path.reverse()
    pts = [(ox + path[0][0] * STEP, oy + path[0][1] * STEP)]
    for i in range(1, len(path)):
        if i == len(path) - 1 or path[i][2] != path[i + 1][2]: pts.append((ox + path[i][0] * STEP, oy + path[i][1] * STEP))
    if offgrid:
        if len(pts) < 3: return dict(ok=False, why="end off the grid, straight route")
        def dv(a, b): n = math.hypot(b[0] - a[0], b[1] - a[1]); return ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
        dl = dv(pts[-2], pts[-1]); dp = dv(pts[-3], pts[-2])
        det = dp[0] * (-dl[1]) - (-dl[0]) * dp[1]
        if abs(det) < 1e-9: return dict(ok=False, why="refit parallel")
        rx, ry = p2[0] - pts[-3][0], p2[1] - pts[-3][1]
        t = (rx * (-dl[1]) - (-dl[0]) * ry) / det
        if t <= 0: return dict(ok=False, why="refit reversed")
        pts = pts[:-2] + [(pts[-3][0] + t * dp[0], pts[-3][1] + t * dp[1]), (p2[0], p2[1])]
    pts[0] = (p1[0], p1[1])
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    L = sum(segs)
    line = LineString(pts).buffer(w / 2 + CLR)
    if any(o.intersects(line) for o in obs): return dict(ok=False, why="clearance after refit")
    if min(segs) < 0.15 - 1e-6: return dict(ok=False, why="piece under 0.15 mm")
    if L > maxlen: return dict(ok=False, why="too long (%.2f mm)" % L)
    return dict(ok=True, newlen=round(L, 3), path=[[round(a, 4), round(b, 4)] for a, b in pts], bends=len(pts) - 2, layer=layer)

res = []
for c in C:
    options = []
    if c["kind"] == "hop":
        r = solve(c, c["A"], c["v1"], c["v2"]); r["remove"] = "both"; options.append(r)
    else:
        r = solve(c, c["A"], c["v1"], c["v2"]); r["remove"] = "v1"; options.append(r)       # route on A, keep the second via
        r2 = solve(c, c["C"], c["v1"], c["v2"]); r2["remove"] = "v2"; options.append(r2)    # route on C, keep the first via
    good = [o for o in options if o["ok"]]
    pick = min(good, key=lambda o: o["newlen"]) if good else options[0]
    res.append(dict(c, **pick))
ok = [r for r in res if r["ok"]]
print("candidates: %d, routable: %d  -> vias removed: %d" % (len(res), len(ok), sum(2 if r["remove"] == "both" else 1 for r in ok)))
for r in res: print("  %-11s %-6s (%.2f, %.2f)-(%.2f, %.2f) chain on %s %.2f mm -> %s" % (r["net"], r["kind"], r["v1"][0], r["v1"][1], r["v2"][0], r["v2"][1], r["B"], r["lenB"], ("%s %.2f mm, %d bend(s), remove %s" % (r["layer"], r["newlen"], r["bends"], r["remove"])) if r["ok"] else r["why"]))
json.dump(res, open(args[2], "w"))
