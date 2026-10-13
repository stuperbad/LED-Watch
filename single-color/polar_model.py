"""
Polar routing capacity model and ring optimiser.

Question it answers: given an LED footprint, the number of LEDs per ring, the nets that have to travel ALL the way round the face ("long nets", drawn as
concentric arcs) and the design rules (track, space, via), how wide must the gaps between rings be, and so what is the smallest board / smallest free centre?

Model (all numbers are first-principles bounds, to be confirmed by the geometry generator + KiCad DRC):
  * LEDs sit on rings of radius r_i, pad axis radial, radial length L, tangential width W, pads at pitch pp.  Tangential rule: pitch 2*pi*r_i/N_i >= W + g_t.
  * Every long net is a closed arc ("lane") at a fixed radius in ONE gap; its LEDs reach it with a stub, a through via and a radial spoke on another layer.
  * A through via pierces EVERY copper layer.  So no other net may have a lane within (d_v + w)/2 + s of a lane that has a via.  Lanes of all layers therefore share
    one set of radii:  lane pitch p_lane = (d_v + w)/2 + s  (that is the via-driven spacing: wider than the bare w + s).  Blind/buried vias would remove this limit.
  * Stub vias (F.Cu pad -> via) sit in rows next to the ring edge.  Rows needed = ceil(vias per LED on that side / vias that fit side by side at the pad pitch).
  * Gap between ring i and i+1 = c + outer via rows + (w/2+s) + lane band + (w/2+s) + inner via rows (+ optional F.Cu lane) + c.
  * Spokes (radial tracks on a different layer from the arcs) cross the LED rings between LEDs.  Free tangential width per LED slot = pitch - W - 2c; spokes that fit = floor((free - w)/(w + s)) + 1.
Objectives: outer board diameter and free-centre (inner) diameter.
"""
import itertools, math, json, sys
from dataclasses import dataclass, field, replace


@dataclass
class Rules:
    w: float = 0.10            # track width
    s: float = 0.10            # track/via clearance
    d_v: float = 0.30          # via pad diameter (JLCPCB multilayer minimum 0.25 pad / 0.15 hole, see JLCPCB-RULES.md)
    drill: float = 0.15        # via drill
    hole_clr: float = 0.22     # via hole-to-copper (JLCPCB page: 0.20 via hole to track / inner copper; +0.02 margin)
    c: float = 0.10            # LED copper to via/track clearance
    edge: float = 0.20         # outermost copper to board edge
    g_t: float = 0.25          # tangential gap between neighbouring LED bodies
    through: bool = True       # True: through vias pierce every layer (lane pitch via-driven); False: blind/buried (lane pitch = w + s)
    conservative: bool = False  # extra margin between lane band and via rows


@dataclass
class Ring:
    name: str
    n: int                     # LEDs on the ring
    L: float                   # LED radial length (body)
    W: float                   # LED tangential width (body)
    pad_pitch: float           # tangential distance between the two pads of one row
    vias_in: int               # vias per LED on the inner side (pad -> via)
    vias_out: int              # vias per LED on the outer side
    f_lane_in: bool = False    # a short F.Cu lane (e.g. common-cathode group arc) sits on the inner side of the ring
    f_lane_out: bool = False
    long_net_leds: int = 0     # LEDs of EACH long net on this ring (for spoke-crossing demand)


@dataclass
class Design:
    name: str
    rings: list
    n_long: int                # number of long nets (full-circle arcs)
    spokes_per_led: int        # long-net connections per LED
    keep_free: float = 0.0     # extra free radius needed inside (e.g. for parts), mm


def lane_pitch(r: Rules):
    if not r.through:
        return r.w + r.s
    return max((r.d_v + r.w) / 2 + r.s, r.drill / 2 + r.w / 2 + r.hole_clr)


def via_rows(n, pad_pitch, r: Rules):
    if n <= 0:
        return 0
    per_row = 2 if pad_pitch >= r.d_v + r.s - 1e-9 else 1
    return math.ceil(n / per_row)


def row_thickness(rows, r: Rules):
    return 0.0 if rows == 0 else r.d_v + (rows - 1) * (r.d_v + r.s)


def side_depth(ring: Ring, side: str, r: Rules):
    """radial depth from the LED edge to the end of the stub-via rows (+ optional F.Cu lane) on one side"""
    n = ring.vias_out if side == "out" else ring.vias_in
    rows = via_rows(n, ring.pad_pitch, r)
    depth = r.c + row_thickness(rows, r)
    if (ring.f_lane_out if side == "out" else ring.f_lane_in):
        depth += r.s + r.w + r.s
    return depth


def gap_width(ring_a: Ring, ring_b: Ring, n_lanes: int, r: Rules):
    """radial gap between the outer edge of ring_a (or None = free centre) and the inner edge of ring_b (or None = board edge)"""
    out_a = side_depth(ring_a, "out", r) if ring_a else r.c
    in_b = side_depth(ring_b, "in", r) if ring_b else r.edge
    e = (r.w / 2 + r.s) + (r.d_v / 2 if r.conservative else 0.0)
    band = 0.0 if n_lanes == 0 else (n_lanes - 1) * lane_pitch(r) + r.w + 2 * e
    return out_a + band + in_b


def spoke_capacity(r_i, ring: Ring, r: Rules):
    pitch = 2 * math.pi * r_i / ring.n
    free = pitch - ring.W - 2 * r.c
    return 0 if free < r.w else int((free - r.w) // (r.w + r.s)) + 1


def min_radius_tangential(ring: Ring, r: Rules):
    return ring.n * (ring.W + r.g_t) / (2 * math.pi)


def crossing_demand(design: Design, dist):
    """spokes (F.Cu stubs to lane vias) per LED slot that must cross each ring.
    Zones, inside out: gap0, ring0, gap1, ring1, ..., ring(K-1), gapK  (2K+1 zones); dist[z] = lanes in zone z."""
    rings = design.rings
    K = len(rings)
    out = []
    for i in range(K):
        demand = 0
        for z, n_lanes in enumerate(dist):
            if n_lanes == 0:
                continue
            for j in range(K):
                zj = 2 * j + 1
                if z == zj:
                    continue
                lo, hi = (zj, z) if zj < z else (z, zj)
                zi = 2 * i + 1
                inside = lo < zi < hi
                lands_in_ring = (z == zi)                    # the via lands in this ring's slot
                if inside or lands_in_ring:
                    demand += n_lanes * rings[j].long_net_leds
        out.append(demand / rings[i].n)
    return out


def ring_zone_capacity(ring: Ring, r: Rules):
    """lanes that fit under one LED ring (inner-layer copper under the LED bodies) without growing the board"""
    return int((ring.L - r.w) // lane_pitch(r)) + 1 if ring.L >= r.w else 0


def layout(design: Design, dist, r: Rules, usage=0.8):
    """dist has 2K+1 entries (gap0, ring0, gap1, ring1, ..., gapK).  Lanes in a ring zone are free up to the ring zone capacity; lanes in gaps widen the gap.
    Spoke crossings widen the LED pitch, which pushes rings outward (the tangential driver)."""
    rings = design.rings
    K = len(rings)
    lanes_gap = [dist[2 * g] for g in range(K + 1)]
    lanes_ring = [dist[2 * j + 1] for j in range(K)]
    extra = 0.0
    for j in range(K):                                   # lanes beyond the ring-zone capacity spill into the neighbouring gaps (cost them as extra lane pitch)
        spill = max(0, lanes_ring[j] - ring_zone_capacity(rings[j], r))
        extra += spill * lane_pitch(r)
    gaps = [gap_width(rings[g - 1] if g >= 1 else None, rings[g] if g < K else None, lanes_gap[g], r) for g in range(K + 1)]
    gaps[0] += extra
    per_slot = crossing_demand(design, dist)
    radii, ks = [], []
    pos = max(design.keep_free, 0.0) + gaps[0]
    for i, ring in enumerate(rings):
        k = math.ceil(per_slot[i] / usage - 1e-9) if per_slot[i] > 0 else 0
        need_t = ring.W + 2 * r.c + (k * r.w + (k - 1) * r.s if k > 0 else 0.0)
        rad_t = ring.n * max(ring.W + r.g_t, need_t) / (2 * math.pi)
        rad = max(pos + ring.L / 2, rad_t)
        radii.append(rad); ks.append(k)
        pos = rad + ring.L / 2 + gaps[i + 1]
    free_diam = 2 * (radii[0] - rings[0].L / 2 - gaps[0])
    outer_diam = 2 * (radii[-1] + rings[-1].L / 2 + gaps[K])
    return dict(radii=radii, gaps=gaps, spokes_per_slot=ks, free_diam=free_diam, outer_diam=outer_diam, dist=list(dist))


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, parts - 1):
            yield (first,) + rest


def optimise(design: Design, r: Rules, weight_outer=1.0, weight_inner=0.0, top=5):
    K = len(design.rings)
    results = []
    for dist in compositions(design.n_long, 2 * K + 1):
        lay = layout(design, dist, r)
        lay["score"] = weight_outer * lay["outer_diam"] + weight_inner * lay["free_diam"]
        results.append(lay)
    results.sort(key=lambda x: x["score"])
    return results[:top], len(results)


# ---------------------------------------------------------------- presets
def rgb_design(group=6, r: Rules = None):
    """RGB version: 132 RGB LEDs (0.83 mm, 4 pads 0.3 mm at 0.5 pitch), rings H=12, M=60, S=60 (inner to outer).
    Rows (common cathode) are short groups of `group` consecutive LEDs; the long nets are the 3*group colour columns (R_p, G_p, B_p)."""
    long_nets = 3 * group
    per_net = lambda n: n // group          # LEDs of ONE colour column on a ring = one per group
    rings = [Ring("hour", 12, 0.83, 0.83, 0.5, vias_in=1, vias_out=2, f_lane_in=True, long_net_leds=per_net(12)),
             Ring("minute", 60, 0.83, 0.83, 0.5, vias_in=1, vias_out=2, f_lane_in=True, long_net_leds=per_net(60)),
             Ring("second", 60, 0.83, 0.83, 0.5, vias_in=1, vias_out=2, f_lane_in=True, long_net_leds=per_net(60))]
    return Design(f"RGB group={group}", rings, long_nets, 3)


def white_design(r: Rules = None):
    """White version: 132 two-pad LEDs, 12 sectors x 11 slots; columns are short radial spokes, the 11 rows are the long arcs."""
    rings = [Ring("hour", 12, 1.56, 0.95, 0.0, vias_in=1, vias_out=1, long_net_leds=12),
             Ring("minute", 60, 1.10, 0.64, 0.0, vias_in=1, vias_out=1, long_net_leds=12),
             Ring("second", 60, 0.65, 0.40, 0.0, vias_in=1, vias_out=1, long_net_leds=12)]
    # hour row has 12 LEDs on the hour ring only; minute rows: 5 rows x 12 LEDs; second rows: 5 rows x 12 LEDs
    return Design("white 12x11", rings, 11, 1)


if __name__ == "__main__":
    r = Rules()
    print("lane pitch", round(lane_pitch(r), 3), "mm  (bare track pitch would be", r.w + r.s, ")")
    for d in (rgb_design(6), white_design()):
        best, n = optimise(d, r)
        print(d.name, "lane distributions tried:", n)
        for b in best[:3]:
            print("  lanes per gap", b["dist"], "radii", [round(x, 2) for x in b["radii"]], "spokes/slot", b["spokes_per_slot"], "outer D", round(b["outer_diam"], 2), "free D", round(b["free_diam"], 2))
