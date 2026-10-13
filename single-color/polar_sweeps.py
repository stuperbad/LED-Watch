"""Sweeps the polar model: what drives the ring band thickness and the board size (writes polar_sweeps.png and prints tables)."""
import dataclasses, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polar_model as pm

def best(design, rules, free_d):
    d = dataclasses.replace(design, keep_free=free_d / 2)
    res, n = pm.optimise(d, rules, 1.0, 0.0, top=1)
    b = res[0]; b["band"] = (b["outer_diam"] - b["free_diam"]) / 2
    return b

def row(design, rules, F):
    b = best(design, rules, F)
    return b["outer_diam"], b["band"], b["dist"], [round(x, 1) for x in b["radii"]], b["spokes_per_slot"]

R0 = pm.Rules()
print("== BASELINE RGB (group 6, JLC via 0.3/0.15, hole clr 0.22, track 0.1/0.1), by required free-centre diameter")
for F in (16, 20, 24, 28):
    o, bd, dist, rad, k = row(pm.rgb_design(6), R0, F)
    print(f" free {F} mm -> outer {o:.1f} mm, band {bd:.2f} mm, lanes/gap {dist}, ring radii {rad}, spokes/slot {k}")
print("   hand-built RGB board (Evan): radii 14.0 / 16.5 / 19.0 -> free about 27 mm, outer about 40 mm, band about 6.5 mm")
print("== BASELINE WHITE")
for F in (16, 20, 24, 28):
    o, bd, dist, rad, k = row(pm.white_design(), R0, F)
    print(f" free {F} mm -> outer {o:.1f} mm, band {bd:.2f} mm, lanes/gap {dist}, radii {rad}, spokes/slot {k}")

variants = {
  "baseline (JLC: via 0.30/0.15, hole clr 0.22, track/space 0.10)": R0,
  "old assumption (via 0.40/0.20, hole clr 0.20)": dataclasses.replace(R0, d_v=0.40, drill=0.20, hole_clr=0.20),
  "via 0.25 pad / 0.15 drill (JLC minimum)": dataclasses.replace(R0, d_v=0.25),
  "hole clearance 0.20 (JLC minimum, no margin)": dataclasses.replace(R0, hole_clr=0.20),
  "hole clearance 0.30 (what I wrongly used: PTH row)": dataclasses.replace(R0, hole_clr=0.30),
  "track/space 0.127 (5 mil)": dataclasses.replace(R0, w=0.127, s=0.127),
  "track/space 0.09 (JLC multilayer minimum)": dataclasses.replace(R0, w=0.09, s=0.09),
  "blind/buried vias (HDI, no piercing)": dataclasses.replace(R0, through=False),
}
F = 24
print(f"== DRIVERS, RGB group 6, free centre {F} mm")
base = best(pm.rgb_design(6), R0, F)
names, outer = [], []
for k, rr in variants.items():
    b = best(pm.rgb_design(6), rr, F)
    print(f" {k:55s} outer {b['outer_diam']:.1f}  band {b['band']:.2f}  lanes/gap {b['dist']}  d_outer {b['outer_diam'] - base['outer_diam']:+.1f}")
    names.append(k); outer.append(b["outer_diam"])
print(f"== MATRIX ORGANISATION (group size m), RGB, free centre {F} mm")
groups = {}
for m in (2, 3, 4, 6, 12):
    pins = 3 * m + 132 // m
    b = best(pm.rgb_design(m), R0, F)
    groups[m] = (pins, b["outer_diam"], b["band"], b["dist"])
    print(f" m={m:2d}: long nets {3*m:2d}, row nets {132//m:3d}, MCU pins for the matrix {pins:3d} -> outer {b['outer_diam']:.1f}  band {b['band']:.2f}  lanes/gap {b['dist']}")
fig, ax = plt.subplots(1, 3, figsize=(18, 5.2))
Fs = [12, 16, 20, 24, 28, 32]
for name, des in (("RGB group 6", pm.rgb_design(6)), ("white 12x11", pm.white_design())):
    ax[0].plot(Fs, [best(des, R0, f)["outer_diam"] for f in Fs], marker="o", label=name)
ax[0].plot([27], [40], "k*", ms=12, label="Evan's hand-built RGB (about)")
ax[0].set_xlabel("free centre diameter wanted (mm)"); ax[0].set_ylabel("outer diameter needed (mm)"); ax[0].set_title("Outer size vs free centre"); ax[0].grid(alpha=.3); ax[0].legend()
ax[1].barh(range(len(names)), outer, color="#3b7ddd"); ax[1].set_yticks(range(len(names))); ax[1].set_yticklabels([n.split(" (")[0] for n in names], fontsize=8)
ax[1].set_xlim(min(outer) - 2, max(outer) + 1); ax[1].set_xlabel(f"outer diameter (mm), RGB, free centre {F} mm"); ax[1].set_title("What drives the size"); ax[1].invert_yaxis(); ax[1].grid(alpha=.3, axis="x")
ms = sorted(groups); ax[2].plot([groups[m][0] for m in ms], [groups[m][1] for m in ms], marker="o")
for m in ms:
    ax[2].annotate(f"m={m}", (groups[m][0], groups[m][1]), textcoords="offset points", xytext=(4, 4))
ax[2].set_xlabel("MCU pins used by the LED matrix"); ax[2].set_ylabel("outer diameter (mm)"); ax[2].set_title("Matrix shape: fewer long nets vs more pins"); ax[2].grid(alpha=.3)
fig.tight_layout(); fig.savefig("polar_sweeps.png", dpi=90)
