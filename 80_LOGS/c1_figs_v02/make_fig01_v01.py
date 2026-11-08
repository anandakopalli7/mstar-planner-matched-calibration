"""Fig. 1 (single column): M* between tracker and planner. Schematic only, no data.

Usage: python -B make_fig01_v01.py <out_dir>
Writes <out_dir>/fig01_pipeline.pdf and <out_dir>/fig01_pipeline.png (300 dpi).
Content follows 20_DESIGN/ms_v06_parts/04_method_v04.md, Sections IV-A to IV-F.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = sys.argv[1]
if not os.path.isdir(OUT):
    raise SystemExit("output folder missing: " + OUT)
for name in ("fig01_pipeline.pdf", "fig01_pipeline.png"):
    if os.path.exists(os.path.join(OUT, name)):
        raise SystemExit("refusing to overwrite " + name)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

FW, FH = 3.5, 4.2           # inches; FH is provisional, trimmed at the end
INK = "#000000"
MUTED = "#555555"
OFF_FILL = "#EDEDED"       # offline region
BOX_FILL = "#FFFFFF"
MSTAR_EDGE = "#D55E00"     # Okabe-Ito vermillion (same hue as M* in Fig. 4)
MSTAR_FILL = "#FBE5D6"
PLAN_FILL = "#D9D9D9"

fig = plt.figure(figsize=(FW, FH))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.axis("off")
fig.canvas.draw()
renderer = fig.canvas.get_renderer()


BOX_ARTISTS = {}


def remove_box(b):
    for a in BOX_ARTISTS.pop(b):
        a.remove()


def text_extent(t):
    bb = t.get_window_extent(renderer=renderer)
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    return x0, y0, x1, y1


def box(cx, ytop, w, lines, fill=BOX_FILL, edge=INK, lw=0.7, pad=0.06,
        title=None, z=3, top_pad=None):
    """Draw a text box whose top edge is at ytop; return (x0, y0, x1, y1)."""
    y = ytop - (pad if top_pad is None else top_pad)
    items = []
    if title is not None:
        t = ax.text(cx, y, title, ha="center", va="top", fontsize=8,
                    fontweight="bold", color=INK, zorder=z + 1)
        items.append(t)
        y = text_extent(t)[1] - 0.025
    t = ax.text(cx, y, lines, ha="center", va="top", fontsize=8,
                color=INK, linespacing=1.25, zorder=z + 1)
    items.append(t)
    ybot = text_extent(t)[1] - pad
    p = FancyBboxPatch((cx - w / 2, ybot), w, ytop - ybot,
                       boxstyle="round,pad=0,rounding_size=0.05",
                       fc=fill, ec=edge, lw=lw, zorder=z)
    ax.add_patch(p)
    items.append(p)
    BOX_ARTISTS[(cx - w / 2, ybot, cx + w / 2, ytop)] = items
    return cx - w / 2, ybot, cx + w / 2, ytop


def arrow(p0, p1, color=INK, lw=0.8, ls="-"):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7,
                        color=color, lw=lw, linestyle=ls,
                        shrinkA=0, shrinkB=0, zorder=5)
    ax.add_patch(a)


# Regions (x extents now; the bottom edge is set after layout) ----------------
LX0, LX1 = 0.03, 1.74
RX0, RX1 = 1.81, 3.47
RY1 = FH - 0.03
LCX = (LX0 + LX1) / 2
RCX = (RX0 + RX1) / 2
ax.text(LCX, RY1 - 0.06, "Calibration (offline)", ha="center", va="top",
        fontsize=9, fontweight="bold", zorder=2)
ax.text(LCX, RY1 - 0.22, "on annotated logs",
        ha="center", va="top", fontsize=8, style="italic", color=INK, zorder=2)
ax.text(RCX, RY1 - 0.06, "Deployment (online)", ha="center", va="top",
        fontsize=9, fontweight="bold", zorder=2)
ax.text(RCX, RY1 - 0.22, "per track and check time",
        ha="center", va="top", fontsize=8, style="italic", color=INK, zorder=2)

GAP = 0.15
LW_BOX = LX1 - LX0 - 0.10
RW_BOX = RX1 - RX0 - 0.10
TOP = RY1 - 0.44

# Left column: calibration --------------------------------------------------
L1 = box(LCX, TOP, LW_BOX,
         "Tracker prediction\n"
         r"$\hat{m}_h,\ \hat{\Sigma}_h$ at each check time $h$")
L2 = box(LCX, L1[1] - GAP, LW_BOX,
         "Constraints the planner enforces,\n"
         "at the logged reference ego pose")
L3 = box(LCX, L2[1] - GAP, LW_BOX,
         "One-sided error against the\n"
         "annotation along each separating\n"
         r"object axis $a$:  $U = D/\mathrm{sd}$")
L4 = box(LCX, L3[1] - GAP, LW_BOX,
         "strata: object group × range\n"
         "× axis × course-change state\n"
         "(per check time, in-path or not)\n"
         "count-based fallback\n"
         "logs exchangeable; cross-fitted\n"
         "over log folds",
         title="Per-stratum conformal risk\n"
               r"control thresholds $\hat{c}_g$",
         fill=MSTAR_FILL, edge=MSTAR_EDGE, lw=1.1, top_pad=0.11)
for upper, lower in ((L1, L2), (L2, L3), (L3, L4)):
    arrow((LCX, upper[1]), (LCX, lower[3]))

# Right column: deployment --------------------------------------------------
R1 = box(RCX, TOP, RW_BOX,
         "Tracker prediction\n"
         r"$\hat{m}_h,\ \hat{\Sigma}_h$")
# R2 is placed so that the threshold arrow from L4 runs horizontally.
r2_lines = (r"$\tilde{\Sigma} = A\,(\hat{\Sigma}_h + \sigma_a^2 I)\,A$" "\n"
            r"$A$: diagonal scaling along" "\n"
            "the box axes, per axis\n"
            r"$\alpha = \max(\hat{c}, \varepsilon)\,/\,z$")
R3_TITLE = "Chance-constrained speed\nplanner (unchanged)"
R3_LINES = ("margin " r"$z\sqrt{a^{\mathrm{T}}\tilde{\Sigma}\,a}$" "\n"
            "along each constraint\n"
            r"normal $a$")


def right_pair(top):
    r2 = box(RCX, top, RW_BOX, r2_lines, title="Recalibrated covariance",
             fill=MSTAR_FILL, edge=MSTAR_EDGE, lw=1.1, top_pad=0.11)
    r3 = box(RCX, r2[1] - GAP, RW_BOX, R3_LINES, title=R3_TITLE,
             fill=PLAN_FILL, edge=INK, lw=0.7)
    return r2, r3


R2, R3 = right_pair(R1[1] - GAP)              # measuring pass
height = R2[3] - R3[1]
remove_box(R2)
remove_box(R3)
R2, R3 = right_pair(L4[1] + height)           # R3 bottom = L4 bottom
arrow((RCX, R1[1]), (RCX, R2[3]))
arrow((RCX, R2[1]), (RCX, R3[3]))

# thresholds handed from calibration to deployment
ya = (max(L4[1], R2[1]) + min(L4[3], R2[3])) / 2
arrow((L4[2], ya), (R2[0], ya), color=MSTAR_EDGE, lw=1.1)
ax.text((L4[2] + R2[0]) / 2, ya + 0.04, r"$\hat{c}_g$", ha="center",
        va="bottom", fontsize=8, color=INK, zorder=6,
        bbox=dict(boxstyle="round,pad=0.08", fc="white", ec="none"))

# "M*" tags on the two parts that M* adds
for b in (L4, R2):
    ax.text(b[0] + 0.07, b[3], "M*", ha="left", va="center",
            fontsize=8, fontweight="bold", color=INK, zorder=7,
            bbox=dict(boxstyle="round,pad=0.12,rounding_size=0.08",
                      fc="#FFFFFF", ec=MSTAR_EDGE, lw=1.1))

RY0 = min(L4[1], R3[1]) - 0.08
for (x0, x1, fc, ls) in ((LX0, LX1, OFF_FILL, (0, (3, 2))),
                         (RX0, RX1, "#FFFFFF", "-")):
    ax.add_patch(FancyBboxPatch((x0, RY0), x1 - x0, RY1 - RY0,
                                boxstyle="round,pad=0,rounding_size=0.06",
                                fc=fc, ec=MUTED, lw=0.6, ls=ls, zorder=1))
YMIN = RY0 - 0.03
fig.set_size_inches(FW, FH - YMIN)
ax.set_ylim(YMIN, FH)
print("final figure size: %.2f x %.2f in" % (FW, FH - YMIN))

# sanity: nothing may fall outside the regions
for name, b, (x0, x1) in (("L1", L1, (LX0, LX1)), ("L2", L2, (LX0, LX1)),
                          ("L3", L3, (LX0, LX1)), ("L4", L4, (LX0, LX1)),
                          ("R1", R1, (RX0, RX1)), ("R2", R2, (RX0, RX1)),
                          ("R3", R3, (RX0, RX1))):
    if b[1] < RY0 + 0.02 or b[0] < x0 or b[2] > x1:
        raise SystemExit("layout overflow in box " + name + ": " + repr(b))
    print(name, "x %.2f-%.2f  y %.2f-%.2f in" % (b[0], b[2], b[1], b[3]))

fig.savefig(os.path.join(OUT, "fig01_pipeline.pdf"))
fig.savefig(os.path.join(OUT, "fig01_pipeline.png"), dpi=300)
print("wrote fig01_pipeline.pdf/.png to", OUT)
