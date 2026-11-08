"""Fig. 4 v02 (double column): the infeasibility-exceedance trade-off on Argoverse 2,
with the neutral-matched composites of amendments A4 and A5.

Usage:
  python -B make_fig04_v02.py <a3_infeasible_cost.json> <a4_neutral.json> \
         <f_tradeoff.json> <a5_reduced_screen.json> <a5_points.csv> <out_dir>

Reads result files only (no recomputation beyond selecting values).
As v01, plus: M* at delta' = 0.03 (matched on both neutral screens) in all
three rows; the four comparator composites matched on the A5 reduced neutral
screen (hollow rings, family colour) and on the A4 neutral screen (small
crosses, family colour), from families.<fam>.<A4|A5>.composite_six.
Writes <out_dir>/fig04_tradeoff_v02.pdf, fig04_tradeoff_v02.png (300 dpi) and
fig04_points_v02.csv (every plotted point with its source values).
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

A3, A4, FTR, A5, A5P, OUT = sys.argv[1:7]
if not os.path.isdir(OUT):
    raise SystemExit("output folder missing: " + OUT)
OUTS = ("fig04_tradeoff_v02.pdf", "fig04_tradeoff_v02.png",
        "fig04_points_v02.csv")
for name in OUTS:
    if os.path.exists(os.path.join(OUT, name)):
        raise SystemExit("refusing to overwrite " + name)

a3 = json.load(open(A3, encoding="utf-8"))
a4 = json.load(open(A4, encoding="utf-8"))
ftr = json.load(open(FTR, encoding="utf-8"))
a5 = json.load(open(A5, encoding="utf-8"))
a5pts = list(csv.DictReader(open(A5P, encoding="utf-8")))
FAMS = ["B4", "B6", "B9", "B0"]          # comparator families of A4/A5

TRACKERS = (("t1", "T1 (CANMOT)"), ("t3", "T3 (Poly-MOT)"))

# ---------------------------------------------------------------- styles
# Okabe-Ito colours; identity is also carried by marker shape (greyscale).
RECORD = [  # key, legend label, marker, colour, size
    ("B0", "B0", "o", "#0072B2", 4.6),
    ("B1", "B1", "s", "#E69F00", 4.2),
    ("B3", "B3", "^", "#56B4E9", 5.0),
    ("B4", "B4", "v", "#009E73", 5.0),
    ("B6", "B6", "D", "#CC79A7", 4.0),
    ("B9", "B9", "p", "#F0E442", 5.2),
    ("RETUNED", "RETUNED", "X", "#000000", 5.0),
]
MSTAR = ("Mstar", "M*", "*", "#D55E00", 9.5)
HOLLOW = [  # key, legend label, marker, edge colour, size
    ("A_B6_composite", "B6 composite, registered screen", "D",
     "#CC79A7", 4.6),
    ("X3E1_B8", "B8 (variance matching)", "h", "#000000", 5.4),
]
PRIME = "′"   # prime after an italic delta (renders tighter than $\delta'$)
NEUTRAL = ("Mstar@0.03", r"M* at $\delta$" + PRIME + " = 0.03 (both neutral screens)",
           "*", "#D55E00", 9.0)
FAMCOL = {k: c for k, _, _, c, _ in RECORD}
A5_STYLE = dict(marker="o", ms=6.2, mew=1.3)    # ring, family colour
A4_STYLE = dict(marker="x", ms=4.4, mew=1.1)    # cross, family colour
SWEEP_C = "#8C8C8C"

ROWS = [  # x key, x label, x limits, ticks
    ("V2",
     r"(a)  V2: share of decisions with some relied constraint exceeded at full margin",
     (-0.02, 1.02), [0, 0.2, 0.4, 0.6, 0.8, 1.0]),
    ("V2_exec",
     r"(b)  $\mathrm{V2}_{\mathrm{exec}}$: share of decisions with some relied "
     r"constraint exceeded at the executed margin",
     (0.30, 1.01), [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    ("V2_viol",
     r"(c)  $\mathrm{V2}_{\mathrm{viol}}$: share of decisions with some relied "
     r"constraint violated at the chosen plan",
     (-0.0012, 0.0612), [0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]),
]
YLABEL = "Share of decisions infeasible (margin backed off)"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# ---------------------------------------------------------------- data
points = []   # rows for the CSV


def arm(tr, key):
    return a3["by_tracker"][tr]["arms"][key]


def add_point(tr, row_key, series, key, label, rec, src, note=""):
    points.append({
        "tracker": tr, "row": row_key, "series": series, "arm_key": key,
        "label": label,
        "infeasible_rate": rec.get("infeasible_rate"),
        "V2": rec.get("V2"), "V2_exec": rec.get("V2_exec"),
        "V2_viol": rec.get("V2_viol"),
        "x_plotted": rec.get(row_key), "y_plotted": rec.get("infeasible_rate"),
        "source_file": src, "source_note": note or rec.get("source", ""),
    })


# M* check values required by the brief
EXPECT = {"t1": (0.1864, 0.4909, 0.5509, 0.0161),
          "t3": (0.2466, 0.4963, 0.5805, 0.0176)}
checks = []
for tr, _ in TRACKERS:
    m = arm(tr, "Mstar")
    got = tuple(round(m[k], 4) for k in
                ("infeasible_rate", "V2", "V2_exec", "V2_viol"))
    ok = got == EXPECT[tr]
    checks.append(("M* %s values %s == expected %s" % (tr, got, EXPECT[tr]), ok))

# neutral screens (A4 = P1-P7, A5 = P2, P4-P7): matched composites
SIX = ("infeasible_rate", "V2", "V2_exec", "V2_viol")
EXPECT_N = {"t1": (0.2603, 0.3412, 0.4480, 0.0128),
            "t3": (0.3505, 0.3480, 0.5044, 0.0149)}
neutral, comp_a4, comp_a5 = {}, {}, {}
for tr, _ in TRACKERS:
    fams = a5["by_tracker"][tr]["families"]
    m4, m5 = fams["Mstar"]["A4"], fams["Mstar"]["A5"]
    ok = (m4["result"] == m5["result"] == "matched"
          and set(m4["choice_by_fold"].values()) == {"Mstar@0.03"}
          and set(m5["choice_by_fold"].values()) == {"Mstar@0.03"}
          and all(m4["composite_six"][k] == m5["composite_six"][k] for k in SIX))
    checks.append(("M*(0.03) %s: every fold chose Mstar@0.03 under A4 and A5; "
                   "same composite" % tr, ok))
    neutral[tr] = m5["composite_six"]
    got = tuple(round(neutral[tr][k], 4) for k in SIX)
    checks.append(("M*(0.03) %s (infeasible, V2, V2_exec, V2_viol) %s == "
                   "expected %s" % (tr, got, EXPECT_N[tr]), got == EXPECT_N[tr]))
    # agrees with the A4 file's own composite endpoints
    e4 = a4["by_tracker"][tr]["families"]["Mstar"]["composite_endpoints"]
    checks.append(("M*(0.03) %s infeasible and V2_exec equal the A4 file's "
                   "composite endpoints" % tr,
                   all(abs(e4[k] - neutral[tr][k]) < 1e-12
                       for k in ("infeasible_rate", "V2_exec"))))
    comp_a4[tr], comp_a5[tr] = {}, {}
    pts = {r["point"]: r for r in a5pts if r["tracker"] == tr}
    for f in FAMS:
        for scr, store in (("A4", comp_a4), ("A5", comp_a5)):
            rec = fams[f][scr]
            if rec["result"] != "matched":
                checks.append(("%s %s %s: result %s" % (tr, f, scr,
                                                         rec["result"]), False))
                continue
            store[tr][f] = dict(rec["composite_six"])
            store[tr][f]["choice"] = sorted(set(rec["choice_by_fold"].values()))
            # single-choice composites must equal that grid point (points CSV)
            ch = store[tr][f]["choice"]
            if len(ch) == 1:
                p = pts[ch[0]]
                same = all(abs(float(p[k]) - rec["composite_six"][k]) < 1e-12
                           for k in SIX)
                checks.append(("%s %s %s composite (every fold %s) equals the "
                               "points CSV row" % (tr, f, scr, ch[0]), same))
        # A4 composite agrees with the A4 file (infeasible, V2_exec)
        e4 = a4["by_tracker"][tr]["families"][f]["composite_endpoints"]
        checks.append(("%s %s A4 composite infeasible and V2_exec equal the A4 "
                       "file" % (tr, f), all(abs(e4[k] - comp_a4[tr][f][k])
                                             < 1e-12 for k in
                                             ("infeasible_rate", "V2_exec"))))

# cross-check against the earlier trade-off record (reading only)
maxdiff = 0.0
ncmp = 0
for tr, _ in TRACKERS:
    rows = {r["arm"]: r for r in ftr["trackers"][tr]["rows"]}
    for key, r in rows.items():
        if key not in a3["by_tracker"][tr]["arms"]:
            continue
        rec = arm(tr, key)
        for k in ("infeasible_rate", "V2", "V2_viol"):
            maxdiff = max(maxdiff, abs(rec[k] - r[k]))
            ncmp += 1
checks.append(("a3 vs earlier trade-off record: %d values, max |diff| = %.2e"
               % (ncmp, maxdiff), maxdiff < 1e-9))
if not all(ok for _, ok in checks):
    for msg, ok in checks:
        print("CHECK", "PASS" if ok else "FAIL", msg)
    raise SystemExit("a check failed; nothing written")

# ---------------------------------------------------------------- figure
FW = 7.16
L, R, WS = 0.62, 0.10, 0.34          # inches
TOPPAD, LEG_H, COLT = 0.04, 0.64, 0.24
PH, XLAB = 1.52, 0.44                # panel height, x-label band
FH = TOPPAD + LEG_H + COLT + 3 * (PH + XLAB) + 0.02
PW = (FW - L - R - WS) / 2

fig = plt.figure(figsize=(FW, FH))
axes = {}
for i, (rk, _, _, _) in enumerate(ROWS):
    top = FH - TOPPAD - LEG_H - COLT - i * (PH + XLAB)
    for j, (tr, _) in enumerate(TRACKERS):
        x0 = L + j * (PW + WS)
        axes[(rk, tr)] = fig.add_axes([x0 / FW, (top - PH) / FH, PW / FW,
                                       PH / FH])

for i, (rk, xlabel, xlim, xticks) in enumerate(ROWS):
    for j, (tr, title) in enumerate(TRACKERS):
        ax = axes[(rk, tr)]
        arms = a3["by_tracker"][tr]["arms"]
        # B0 sweep: B0a* (scaled by alpha) and B0d* (level delta'), merged,
        # ordered by V2 (descending V2 = increasing margin)
        sweep = sorted((k for k in arms if k.startswith(("B0a", "B0d"))),
                       key=lambda k: (-arms[k]["V2"], k))
        xs = [arms[k][rk] for k in sweep]
        ys = [arms[k]["infeasible_rate"] for k in sweep]
        ax.plot(xs, ys, "-", color=SWEEP_C, lw=0.7, zorder=2)
        ax.plot(xs, ys, "o", color=SWEEP_C, ms=2.2, mew=0, zorder=3)
        for k in sweep:
            add_point(tr, rk, "B0 sweep", k, k, arms[k], "a3")
        # arms of record (filled); Z0 omitted
        for key, lab, mk, col, ms in RECORD:
            rec = arms[key]
            ax.plot(rec[rk], rec["infeasible_rate"], mk, ms=ms, mfc=col,
                    mec="#000000", mew=0.5, zorder=9, clip_on=False)
            # comparators sit above M* so that none is hidden by its star
            add_point(tr, rk, "arm of record", key, lab, rec, "a3")
        # exploratory hollow markers
        for key, lab, mk, col, ms in HOLLOW:
            rec = arms[key]
            ax.plot(rec[rk], rec["infeasible_rate"], mk, ms=ms, mfc="none",
                    mec=col, mew=1.1, zorder=6, clip_on=False)
            add_point(tr, rk, "exploratory (hollow)", key, lab, rec, "a3")
        # neutral screens: A4 composites (crosses), A5 composites (rings),
        # each in its family's colour, with a thin dark under-stroke
        for f in FAMS:
            col = FAMCOL[f]
            rec = comp_a4[tr][f]
            ax.plot(rec[rk], rec["infeasible_rate"], ls="none", color="#000000",
                    marker=A4_STYLE["marker"], ms=A4_STYLE["ms"] + 0.5,
                    mew=A4_STYLE["mew"] + 0.9, zorder=6, clip_on=False)
            ax.plot(rec[rk], rec["infeasible_rate"], ls="none", color=col,
                    zorder=6.1, clip_on=False, **A4_STYLE)
            add_point(tr, rk, "neutral screen P1-P7 (A4) composite", f, f,
                      rec, "a5", "families.%s.A4.composite_six; folds %s"
                      % (f, "/".join(rec["choice"])))
            rec = comp_a5[tr][f]
            ax.plot(rec[rk], rec["infeasible_rate"], ls="none",
                    marker="o", ms=A5_STYLE["ms"] + 1.5, mfc="none",
                    mec="#000000", mew=0.45, zorder=6.2, clip_on=False)
            ax.plot(rec[rk], rec["infeasible_rate"], ls="none", mfc="none",
                    mec=col, zorder=6.3, clip_on=False, **A5_STYLE)
            add_point(tr, rk, "reduced neutral screen P2,P4-P7 (A5) composite",
                      f, f, rec, "a5", "families.%s.A5.composite_six; folds %s"
                      % (f, "/".join(rec["choice"])))
        # M*(0.03), matched on both neutral screens
        rec = neutral[tr]
        ax.plot(rec[rk], rec["infeasible_rate"], NEUTRAL[2],
                ms=NEUTRAL[4], mfc="none", mec=NEUTRAL[3], mew=1.0,
                zorder=7, clip_on=False)
        add_point(tr, rk, "neutral screens (hollow star)", NEUTRAL[0],
                  "M*(0.03)", rec, "a5",
                  "families.Mstar.A5.composite_six (= A4)")
        # M*, emphasised and labelled directly
        rec = arms["Mstar"]
        ax.plot(rec[rk], rec["infeasible_rate"], MSTAR[2], ms=MSTAR[4],
                mfc=MSTAR[3], mec="#000000", mew=0.6, zorder=8,
                clip_on=False)
        ax.annotate("M*", (rec[rk], rec["infeasible_rate"]),
                    xytext=(-7, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=8, fontweight="bold", zorder=9)
        add_point(tr, rk, "M* (arm of record)", "Mstar", "M*", rec, "a3")

        ax.set_xlim(*xlim)
        ax.set_ylim(-0.03, 1.03)
        ax.set_xticks(xticks)
        ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        if rk == "V2_viol":
            ax.set_xticklabels(["0"] + ["%.2f" % t for t in xticks[1:]])
        else:
            ax.set_xticklabels(["%g" % t for t in xticks])
        ax.set_yticklabels(["%g" % t for t in [0, 0.2, 0.4, 0.6, 0.8, 1.0]])
        ax.grid(True, color="#E3E3E3", lw=0.4, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(pad=2)
        if i == 0:
            ax.set_title(title, fontsize=9, fontweight="bold", pad=6)
    # one x label per row, centred under both panels
    bottom = FH - TOPPAD - LEG_H - COLT - i * (PH + XLAB) - PH
    fig.text((L + (FW - L - R) / 2) / FW, (bottom - 0.25) / FH, xlabel,
             ha="center", va="top", fontsize=8)

# one y label for the figure
plot_top = FH - TOPPAD - LEG_H - COLT
plot_bot = plot_top - 3 * PH - 2 * XLAB
fig.text(0.10 / FW, ((plot_top + plot_bot) / 2) / FH, YLABEL,
         rotation=90, ha="left", va="center", fontsize=8)

# shared legend: two rows
h1 = [Line2D([], [], ls="none", marker=MSTAR[2], ms=MSTAR[4] - 1.5,
             mfc=MSTAR[3], mec="#000000", mew=0.6, label="M*")]
h1 += [Line2D([], [], ls="none", marker=mk, ms=ms, mfc=col, mec="#000000",
              mew=0.5, label=lab) for _, lab, mk, col, ms in RECORD]
h2 = [Line2D([], [], color=SWEEP_C, lw=0.7, marker="o", ms=2.2, mew=0,
             label=r"B0 sweep (scaled by $\alpha$ or at level $\delta$" + PRIME
             + ")")]
h2 += [Line2D([], [], ls="none", marker=mk, ms=ms, mfc="none", mec=col,
              mew=1.1, label=lab) for _, lab, mk, col, ms in HOLLOW]
h3 = [Line2D([], [], ls="none", marker=NEUTRAL[2], ms=NEUTRAL[4] - 1.5,
              mfc="none", mec=NEUTRAL[3], mew=1.0, label=NEUTRAL[1]),
      Line2D([], [], ls="none", marker="o", ms=A5_STYLE["ms"],
             mfc="none", mec="#555555", mew=A5_STYLE["mew"],
             label="matched composite, reduced neutral screen"),
      Line2D([], [], ls="none", color="#555555",
             label="matched composite, neutral screen", **A4_STYLE)]
ly1 = (FH - TOPPAD) / FH
LEGX = 0.5 + 0.12 / FW     # slightly right of centre, towards the panels
leg1 = fig.legend(handles=h1, loc="upper center", ncol=len(h1),
                  bbox_to_anchor=(LEGX, ly1), frameon=False,
                  handlelength=1.0, handletextpad=0.35, columnspacing=1.3,
                  borderaxespad=0, title=None)
leg2 = fig.legend(handles=h2, loc="upper center", ncol=len(h2),
                  bbox_to_anchor=(LEGX, ly1 - 0.21 / FH), frameon=False,
                  handlelength=1.6, handletextpad=0.35, columnspacing=1.2,
                  borderaxespad=0)
leg3 = fig.legend(handles=h3, loc="upper center", ncol=len(h3),
                  bbox_to_anchor=(LEGX, ly1 - 0.41 / FH), frameon=False,
                  handlelength=1.6, handletextpad=0.35, columnspacing=1.2,
                  borderaxespad=0)

# layout check: legends inside the page and above the column titles
fig.canvas.draw()
rend = fig.canvas.get_renderer()
title_top = max(axes[("V2", tr)].title.get_window_extent(rend).y1
                for tr, _ in TRACKERS) / fig.dpi
for name, lg in (("legend 1", leg1), ("legend 2", leg2), ("legend 3", leg3)):
    bb = lg.get_window_extent(rend)
    x0, x1, y0 = bb.x0 / fig.dpi, bb.x1 / fig.dpi, bb.y0 / fig.dpi
    ok = x0 >= 0.02 and x1 <= FW - 0.02 and y0 > title_top
    print("%s: x %.2f-%.2f in, bottom %.2f in (titles top %.2f): %s"
          % (name, x0, x1, y0, title_top, "ok" if ok else "OVERLAP"))
    if not ok:
        raise SystemExit("legend layout overlap; nothing written")

fig.savefig(os.path.join(OUT, "fig04_tradeoff_v02.pdf"))
fig.savefig(os.path.join(OUT, "fig04_tradeoff_v02.png"), dpi=300)

# ---------------------------------------------------------------- table
cols = ["tracker", "row", "series", "arm_key", "label", "infeasible_rate",
        "V2", "V2_exec", "V2_viol", "x_plotted", "y_plotted", "source_file",
        "source_note"]
with open(os.path.join(OUT, "fig04_points_v02.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for p in points:
        w.writerow({k: ("" if p[k] is None else
                        ("%.6f" % p[k] if isinstance(p[k], float) else p[k]))
                    for k in cols})


def fmt(v):
    return "   -   " if v is None else "%.4f" % v


print("%-3s %-8s %-28s %-20s %7s %7s %7s %7s" % (
    "tr", "row", "series", "arm", "infeas", "V2", "V2exec", "V2viol"))
for p in points:
    print("%-3s %-8s %-28s %-20s %7s %7s %7s %7s" % (
        p["tracker"], p["row"], p["series"][:28], p["arm_key"][:20],
        fmt(p["infeasible_rate"]), fmt(p["V2"]), fmt(p["V2_exec"]),
        fmt(p["V2_viol"])))
print("plotted points:", len(points), "figure %.2f x %.2f in" % (FW, FH))
for msg, ok in checks:
    print("CHECK", "PASS" if ok else "FAIL", msg)
