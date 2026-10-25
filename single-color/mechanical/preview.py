"""Makes previews/overview.png (three isometric views) and previews/sections.png (two cross-sections with the strap drawn in)."""
import os, tempfile
import numpy as np, trimesh, cadquery as cq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import make_models as m

os.makedirs(os.path.join(m.HERE, "previews"), exist_ok=True)

def mesh_of(shape):
    f = os.path.join(tempfile.gettempdir(), "mm_tmp.stl")
    cq.exporters.export(shape, f, tolerance=0.02, angularTolerance=0.15)
    return trimesh.load(f)

def iso(ax, meshes, az=-35, el=35, colors=None, title="", size=620):
    """small z-buffer renderer (orthographic, Lambert shading)"""
    allv = np.vstack([mm.vertices for mm in meshes]); c = (allv.max(axis=0) + allv.min(axis=0)) / 2
    a, e = np.radians(az), np.radians(el)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    R = Rx @ Rz
    light = R @ (np.array([0.35, -0.45, 0.85]) / np.linalg.norm([0.35, -0.45, 0.85]))
    V = [(mm.vertices - c) @ R.T for mm in meshes]
    ext = max(np.abs(np.vstack(V)[:, [0, 2]]).max(), 1) * 1.05
    img = np.ones((size, size, 3)); zb = np.full((size, size), -1e9)
    for mm, v, col in zip(meshes, V, colors):
        sx = (v[:, 0] / ext * 0.5 + 0.5) * (size - 1); sy = (1 - (v[:, 2] / ext * 0.5 + 0.5)) * (size - 1); dz = v[:, 1] * -1
        for tri, n in zip(mm.faces, mm.face_normals):
            x = sx[tri]; y = sy[tri]; z = dz[tri]
            x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), size - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), size - 1))
            if x1 < x0 or y1 < y0: continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-9: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            l1 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            l2 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            l3 = 1 - l1 - l2
            ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
            if not ins.any(): continue
            zz = l1 * z[0] + l2 * z[1] + l3 * z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]; upd = ins & (zz > sub)
            sub[upd] = zz[upd]
            nv = R @ n; sh = 0.30 + 0.70 * abs(float(np.dot(nv, light)))
            img[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(np.array(col) * sh, 0, 1)
    ax.imshow(img); ax.axis("off"); ax.set_title(title, fontsize=11)

H = m.BATT[2] + m.STRAP_T - m.COMPRESS
board = m.pcb(); dummy = board.union(m.parts()); bump = m.bumper(H)
mb, md, mu = mesh_of(board), mesh_of(dummy), mesh_of(bump)
fig, axs = plt.subplots(2, 3, figsize=(16, 10.5), facecolor="white")
green = (0.18, 0.55, 0.30); grey = (0.75, 0.78, 0.85); amber = (0.95, 0.65, 0.2)
iso(axs[0, 0], [mb], colors=[green], title="01 blank board (front)")
iso(axs[0, 1], [md], az=-35, el=35, colors=[green], title="02 board with part stand-ins (front)")
iso(axs[0, 2], [mu], colors=[amber], title="03 bumper seen from the skin side", az=-35, el=-35)
# assembled, seen from the back (rotate so the back is visible)
iso(axs[1, 0], [md, mu], az=-35, el=-40, colors=[green, amber], title="assembled, seen from the back")
iso(axs[1, 1], [mu], az=-30, el=30, colors=[amber], title="03 bumper from inside (hooks on the lug sides)")
# bumper only, plan view
iso(axs[1, 2], [mb, mu], az=0, el=89, colors=[green, amber], title="plan view: board (green) and bumper (amber)")
fig.tight_layout(); fig.savefig(os.path.join(m.HERE, "previews", "overview.png"), dpi=110); plt.close(fig)

# cross sections
def section(meshes, colors, origin, normal, axes, ax, title, strap=None):
    for mm, col in zip(meshes, colors):
        s = mm.section(plane_origin=origin, plane_normal=normal)
        if s is None: continue
        for ent in s.entities:
            pts = s.vertices[ent.points]
            ax.plot(pts[:, axes[0]], pts[:, axes[1]], color=col, lw=1.4)
    if strap: ax.add_patch(plt.Polygon(strap, closed=True, fc=(0.5, 0.3, 0.1, 0.45), ec="brown", lw=1))
    ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(title, fontsize=10); ax.set_xlabel("mm"); ax.set_ylabel("z (mm), board back face = 0")
fig, axs = plt.subplots(2, 1, figsize=(14, 9.5), facecolor="white")
strap_len = 19.2
# section at x = 0 (YZ plane): along the strap
strap_poly = [(-19.6, -H + m.COMPRESS * 0 - 0.0), (19.6, -H), (19.6, -H + m.STRAP_T - m.COMPRESS), (-19.6, -H + m.STRAP_T - m.COMPRESS)]
strap_poly = [(-19.6, -m.BATT[2] - m.STRAP_T + m.COMPRESS), (19.6, -m.BATT[2] - m.STRAP_T + m.COMPRESS), (19.6, -m.BATT[2]), (-19.6, -m.BATT[2])]
section([md, mu], ["tab:green", "tab:orange"], [0, 0, 0], [1, 0, 0], (1, 2), axs[0], "section x = 0 (along the strap): board, battery (5.25), strap (brown, compressed), bumper floor", strap_poly)
# section at y = 20.2 (XZ plane): through the hooks
section([md, mu], ["tab:green", "tab:orange"], [0, -m.HOOK_Y, 0], [0, 1, 0], (0, 2), axs[1], "section through the hooks (y = 20.2): lugs of the board and the four-hook bumper")
axs[1].set_xlim(-18, 18); axs[0].set_xlim(-24, 24)
fig.tight_layout(); fig.savefig(os.path.join(m.HERE, "previews", "sections.png"), dpi=110); plt.close(fig)
print("previews written")
