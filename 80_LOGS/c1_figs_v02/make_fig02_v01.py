"""Fig. 2 (double column): M*'s per-cell exceedance on Argoverse 2, run of record r1.

Usage:
  python -B make_fig02_v01.py <cells_t1.csv> <cells_t3.csv> <c1_decision_r1.json> \
         <figs_v01_manifest.json> <out_dir>

Reads result files only. Plots, for every evaluable cell of M* (arm Mstar,
evaluable True) in P_rel (PD7_primary), P_near (SD1_7_gap_le_5m) and P_ip
(PD_inpath), the exceedance rate E (point) and the upper end ub_sim of the
one-sided simultaneous 95 % sup-t band (bar to the right). The lower end is
not drawn. Checks: ub_sim equals the decision's simultaneous upper bounds and
U_max; E and ub_sim equal the values plotted in figs_v01 (fig09).
Writes fig02_mstar_cells.pdf/.png (300 dpi) and fig02_points_v01.csv.
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

C1, C3, DEC, OLD, OUT = sys.argv[1:6]
if not os.path.isdir(OUT):
    raise SystemExit("output folder missing: " + OUT)
OUTS = ("fig02_mstar_cells.pdf", "fig02_mstar_cells.png", "fig02_points_v01.csv")
for name in OUTS:
    if os.path.exists(os.path.join(OUT, name)):
        raise SystemExit("refusing to overwrite " + name)

TRACKERS = (("t1", "T1 (CANMOT)", C1, "o", "#0072B2", 3.6),
            ("t3", "T3 (Poly-MOT)", C3, "s", "#E69F00", 3.3))
POPS = (("PD7_primary", r"$P_{\mathrm{rel}}$: all relied records"),
        ("SD1_7_gap_le_5m", r"$P_{\mathrm{near}}$: pair gap $\leq$ 5 m"),
        ("PD_inpath", r"$P_{\mathrm{ip}}$: in-path tracks"))
GROUP = {"car": "car", "pedestrian": "pedestrian", "two_wheeler": "two-wheeler",
         "large": "large veh."}
AXIS = {"long": "long.", "lat": "lat."}
DELTA = 0.05

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 0,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ---------------------------------------------------------------- data
data = {}
for tr, _, path, _, _, _ in TRACKERS:
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8"))
            if r["arm"] == "Mstar" and r["evaluable"] == "True"]
    data[tr] = {P: [r for r in rows if r["population"] == P] for P, _ in POPS}
dec = json.load(open(DEC, encoding="utf-8"))
old = json.load(open(OLD, encoding="utf-8"))

checks = []
mu = dec["Mstar_simultaneous_upper_bounds"]["by_route"]["within_lt3d"]
umax = {}
for tr, *_ in TRACKERS:
    for P, _ in POPS:
        rows = data[tr][P]
        ref = mu[tr][P]
        n_ok = len(rows) == ref["evaluable"]
        ub_ok = all(abs(float(r["ub_sim"]) - ref["cells"][r["cell"]]) <= 1e-12
                    for r in rows)
        mx = max(rows, key=lambda r: float(r["ub_sim"]))
        mx_ok = (abs(float(mx["ub_sim"]) - ref["max_ub"]) <= 1e-12
                 and mx["cell"] == ref["max_cell"])
        umax[(tr, P)] = ref["max_ub"]
        checks.append(("%s %s: %d evaluable cells = decision; ub_sim = decision "
                       "bounds; U_max %.4f in %s" % (tr, P, len(rows),
                                                     ref["max_ub"],
                                                     ref["max_cell"]),
                       n_ok and ub_ok and mx_ok))
        prev = old["fig09"]["plotted"]["%s/%s" % (tr, P)]
        same = (len(prev) == len(rows) and all(
            p["cell"] == r["cell"] and p["E"] == float(r["E"])
            and p["ub_sim"] == float(r["ub_sim"])
            for p, r in zip(prev, rows)))
        checks.append(("%s %s: E and ub_sim identical to figs_v01 fig09 "
                       "(%d cells, exact float equality)" % (tr, P, len(prev)),
                       same))
        checks.append(("%s %s: E <= ub_sim in every cell" % (tr, P),
                       all(float(r["E"]) <= float(r["ub_sim"]) for r in rows)))
for P, _ in POPS:
    a = [r["cell"] for r in data["t1"][P]]
    b = [r["cell"] for r in data["t3"][P]]
    checks.append(("%s: T1 and T3 share the same cells in the same order" % P,
                   a == b))
if not all(ok for _, ok in checks):
    for msg, ok in checks:
        print("CHECK", "PASS" if ok else "FAIL", msg)
    raise SystemExit("a check failed; nothing written")


def label(cell):
    g, a, s = cell.split("|")
    return "%s · %s · %s" % (GROUP[g], AXIS[a], s)


# ---------------------------------------------------------------- figure
FW = 7.16
ROW = 0.128                 # inches per cell
LAB = 1.38                  # y-label band
GAPX = 0.22
RM = 0.06
PW = (FW - 2 * LAB - GAPX - RM) / 2
TOP = 0.50                  # legend band
TT = 0.20                   # panel title band
XB = 0.40                   # x tick labels + x label
n_rel = len(data["t1"]["PD7_primary"])
n_near = len(data["t1"]["SD1_7_gap_le_5m"])
n_ip = len(data["t1"]["PD_inpath"])
H_left = TT + (n_rel + 0.6) * ROW + XB
H_right = 2 * TT + (n_near + n_ip + 1.2) * ROW + 2 * XB - 0.12
FH = TOP + max(H_left, H_right) + 0.04
fig = plt.figure(figsize=(FW, FH))


def add_panel(x0, ytop, n):
    h = (n + 0.6) * ROW
    return fig.add_axes([x0 / FW, (ytop - h) / FH, PW / FW, h / FH]), ytop - h


x_left = LAB
x_right = LAB + PW + GAPX + LAB
y0 = FH - TOP - TT
ax_rel, b_rel = add_panel(x_left, y0, n_rel)
ax_near, b_near = add_panel(x_right, y0, n_near)
ax_ip, b_ip = add_panel(x_right, b_near - XB + 0.12 - TT, n_ip)
AXES = {"PD7_primary": ax_rel, "SD1_7_gap_le_5m": ax_near, "PD_inpath": ax_ip}

OFF = {"t1": -0.19, "t3": 0.19}
points = []
for P, title in POPS:
    ax = AXES[P]
    cells = [r["cell"] for r in data["t1"][P]]
    # light separators between object groups
    groups = [c.split("|")[0] for c in cells]
    for i in range(1, len(cells)):
        if groups[i] != groups[i - 1]:
            ax.axhline(i - 0.5, color="#BDBDBD", lw=0.5, zorder=0)
    ax.axvline(DELTA, color="#000000", lw=0.8, ls=(0, (4, 2)), zorder=1)
    for tr, tname, _, mk, col, ms in TRACKERS:
        for i, r in enumerate(data[tr][P]):
            y = i + OFF[tr]
            e, ub = float(r["E"]), float(r["ub_sim"])
            ax.plot([e, ub], [y, y], "-", color=col, lw=1.1,
                    solid_capstyle="butt", zorder=3)
            ax.plot(ub, y, marker="|", ms=4.2, mew=1.1, color=col, zorder=3)
            ax.plot(e, y, marker=mk, ms=ms, mfc=col, mec="#000000",
                    mew=0.45, ls="none", zorder=4)
            points.append({"tracker": tr, "population": P, "cell": r["cell"],
                           "E": r["E"], "ub_sim": r["ub_sim"],
                           "lb_sim_not_drawn": r["lb_sim"],
                           "logs_with_records": r["scenes"],
                           "records": r["records"]})
    ax.set_ylim(len(cells) - 0.5 + 0.1, -0.5 - 0.1)
    ax.set_yticks(range(len(cells)))
    ax.set_yticklabels([label(c) for c in cells])
    ax.set_xlim(0, 0.17)
    ax.set_xticks([0, 0.05, 0.10, 0.15])
    ax.set_xticklabels(["0", "0.05", "0.10", "0.15"])
    ax.grid(axis="x", color="#E3E3E3", lw=0.4, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", pad=2)
    ax.tick_params(axis="x", pad=2)
    t = r"%s ($n$ = %d evaluable cells); $U_{\max}$: T1 %.3f, T3 %.3f" % (
        title, len(cells), umax[("t1", P)], umax[("t3", P)])
    ax.set_title(t, fontsize=8, loc="left", pad=4, x=-LAB / PW + 0.01)

XL = "Exceedance rate in the cell (mean over logs)"
for ax in (ax_rel, ax_ip):
    ax.set_xlabel(XL, labelpad=2)

h = [Line2D([], [], color=col, lw=1.1, marker=mk, ms=ms, mfc=col,
            mec="#000000", mew=0.45, label=tname)
     for _, tname, _, mk, col, ms in TRACKERS]
h.append(Line2D([], [], color="#000000", lw=0.8, ls=(0, (4, 2)),
                label=r"$\delta$ = 0.05"))
leg = fig.legend(handles=h, loc="upper center", ncol=3, frameon=False,
                 bbox_to_anchor=(0.5, (FH - 0.03) / FH), borderaxespad=0,
                 handlelength=2.2, columnspacing=2.0)
fig.text(0.5, (FH - 0.27) / FH,
         "Marker: exceedance rate.  Bar to the right: upper end of the "
         "one-sided simultaneous 95 % band (lower end not drawn).",
         ha="center", va="top", fontsize=8)

# layout check: nothing outside the page, titles clear of the legend
fig.canvas.draw()
rend = fig.canvas.get_renderer()
ok = True
for ax in AXES.values():
    bb = ax.get_tightbbox(rend)
    if bb.x0 < 0 or bb.x1 > FW * fig.dpi + 1 or bb.y0 < 0 or \
            bb.y1 > (FH - TOP + 0.02) * fig.dpi:
        ok = False
        print("layout: panel outside its band", bb.x0 / fig.dpi,
              bb.x1 / fig.dpi, bb.y0 / fig.dpi, bb.y1 / fig.dpi)
bb_near = ax_near.get_tightbbox(rend)
bb_ip_title = ax_ip.title.get_window_extent(rend)
if bb_ip_title.y1 > bb_near.y0 + 1:
    ok = False
    print("layout: P_ip title overlaps P_near axis labels")
checks.append(("layout: panels inside the page and below the legend band; "
               "P_ip title clear of P_near", ok))
if not ok:
    raise SystemExit("layout check failed; nothing written")

fig.savefig(os.path.join(OUT, "fig02_mstar_cells.pdf"))
fig.savefig(os.path.join(OUT, "fig02_mstar_cells.png"), dpi=300)
cols = ["tracker", "population", "cell", "E", "ub_sim", "lb_sim_not_drawn",
        "logs_with_records", "records"]
with open(os.path.join(OUT, "fig02_points_v01.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(points)
for p in points:
    print("%s %-16s %-26s E %.4f  ub %.4f" % (p["tracker"], p["population"],
                                             p["cell"], float(p["E"]),
                                             float(p["ub_sim"])))
print("plotted cells:", len(points), "figure %.2f x %.2f in" % (FW, FH))
for msg, ok in checks:
    print("CHECK", "PASS" if ok else "FAIL", msg)
