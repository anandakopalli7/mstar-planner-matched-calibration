"""Fig. 3 (single column): infeasible-decision rate per arm, run of record r1.

Usage:
  python -B make_fig03_v01.py <arms_t1.csv> <arms_t3.csv> <paired_t1.csv> \
         <paired_t3.csv> <c1_decision_r1.json> <figs_v01_manifest.json> <out_dir>

Reads result files only.
(a) infeasible_rate per arm with the record's 95 % log-bootstrap interval
    (infeasible_ci95_lo / _hi of the arms CSV);
(b) the paired per-log difference M* - arm (paired CSV, endpoint
    infeasible_rate) with its two-sided 95 % interval (ci95_lo / ci95_hi);
    filled = comparator in V_t (decision H1.by_tracker.V), open = removed.
Checks: every plotted value equals figs_v01 (fig10) exactly; the paired values
for V_t members equal the decision's H1 entries.
Writes fig03_infeasible_arms.pdf/.png (300 dpi) and fig03_points_v01.csv.
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

A1, A3, P1, P3, DEC, OLD, OUT = sys.argv[1:8]
if not os.path.isdir(OUT):
    raise SystemExit("output folder missing: " + OUT)
OUTS = ("fig03_infeasible_arms.pdf", "fig03_infeasible_arms.png",
        "fig03_points_v01.csv")
for name in OUTS:
    if os.path.exists(os.path.join(OUT, name)):
        raise SystemExit("refusing to overwrite " + name)

ARMS = ["Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED"]  # Table IV
LABEL = {"Mstar": "M*"}
TRACKERS = (("t1", "T1 (CANMOT)", A1, P1, "o", "#0072B2", 3.6),
            ("t3", "T3 (Poly-MOT)", A3, P3, "s", "#E69F00", 3.3))

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
dec = json.load(open(DEC, encoding="utf-8"))
old = json.load(open(OLD, encoding="utf-8"))["fig10"]["plotted"]
vals = {}
for tr, _, apath, ppath, *_ in TRACKERS:
    arms = {r["arm"]: r for r in csv.DictReader(open(apath, encoding="utf-8"))}
    prs = {}
    for r in csv.DictReader(open(ppath, encoding="utf-8")):
        if r["endpoint"] != "infeasible_rate":
            continue
        a, b = r["arm_a"], r["arm_b"]
        if b == "Mstar" and a in ARMS:      # mean_diff = a - M*: negate
            prs[a] = (-float(r["mean_diff"]), -float(r["ci95_hi"]),
                      -float(r["ci95_lo"]), r["n_scenes"])
        elif a == "Mstar" and b in ARMS:    # mean_diff = M* - b
            prs[b] = (float(r["mean_diff"]), float(r["ci95_lo"]),
                      float(r["ci95_hi"]), r["n_scenes"])
    V = set(dec["hypotheses"]["H1"]["by_tracker"][tr]["V"])
    vals[tr] = {}
    for a in ARMS:
        r = arms[a]
        e = {"rate": float(r["infeasible_rate"]),
             "lo": float(r["infeasible_ci95_lo"]),
             "hi": float(r["infeasible_ci95_hi"])}
        if a != "Mstar":
            d, dlo, dhi, n = prs[a]
            e.update({"d": d, "dlo": dlo, "dhi": dhi, "n_logs": n,
                      "in_V": a in V})
        vals[tr][a] = e

checks = []
for tr, *_ in TRACKERS:
    same = True
    for a in ARMS:
        e, o = vals[tr][a], old[tr][a]
        same &= (e["rate"] == o["infeasible_rate"]
                 and [e["lo"], e["hi"]] == o["ci95"])
        if a != "Mstar":
            same &= (e["d"] == o["Mstar_minus_arm"]
                     and [e["dlo"], e["dhi"]] == o["Mstar_minus_arm_ci95"]
                     and e["in_V"] == o["in_V_t"])
    checks.append(("%s: all 8 rates, 7 paired differences, their intervals "
                   "and V_t membership identical to figs_v01 fig10 (exact)"
                   % tr, same))
    h1 = dec["hypotheses"]["H1"]["by_tracker"][tr]
    ok = all(abs(vals[tr][a]["d"] - h1["vs"][a]["mean_diff"]) < 1e-12 and
             max(abs(vals[tr][a]["dlo"] - h1["vs"][a]["ci95"][0]),
                 abs(vals[tr][a]["dhi"] - h1["vs"][a]["ci95"][1])) < 1e-12
             for a in h1["V"])
    checks.append(("%s: V_t = %s; paired M* - arm and ci95 equal the "
                   "decision's H1 entries" % (tr, sorted(h1["V"])), ok))
    checks.append(("%s: every point inside its interval" % tr, all(
        e["lo"] <= e["rate"] <= e["hi"] and
        ("d" not in e or e["dlo"] <= e["d"] <= e["dhi"])
        for e in vals[tr].values())))
    checks.append(("%s: paired differences over %s logs" % (tr, sorted(
        {e["n_logs"] for a, e in vals[tr].items() if a != "Mstar"})),
        all(e["n_logs"] == "375" for a, e in vals[tr].items()
            if a != "Mstar")))
if not all(ok for _, ok in checks):
    for msg, ok in checks:
        print("CHECK", "PASS" if ok else "FAIL", msg)
    raise SystemExit("a check failed; nothing written")

# ---------------------------------------------------------------- figure
FW = 3.5
LAB = 0.62
RM = 0.10
PW = FW - LAB - RM
ROW = 0.215
PH = len(ARMS) * ROW
TOP = 0.52
XB = 0.46
FH = TOP + 2 * (PH + XB) + 0.10
fig = plt.figure(figsize=(FW, FH))
ax_a = fig.add_axes([LAB / FW, (FH - TOP - PH) / FH, PW / FW, PH / FH])
ax_b = fig.add_axes([LAB / FW, (FH - TOP - 2 * PH - XB) / FH, PW / FW,
                     PH / FH])
OFF = {"t1": -0.2, "t3": 0.2}
EB = dict(elinewidth=1.0, capsize=2.4, capthick=1.0, ls="none")
points = []
for tr, tname, _, _, mk, col, ms in TRACKERS:
    for i, a in enumerate(ARMS):
        e = vals[tr][a]
        y = i + OFF[tr]
        ax_a.errorbar(e["rate"], y, xerr=[[e["rate"] - e["lo"]],
                                          [e["hi"] - e["rate"]]],
                      ecolor=col, zorder=3, **EB)
        ax_a.plot(e["rate"], y, marker=mk, ms=ms, mfc=col, mec="#000000",
                  mew=0.45, ls="none", zorder=4)
        row = {"tracker": tr, "arm": a, "infeasible_rate": e["rate"],
               "ci95_lo": e["lo"], "ci95_hi": e["hi"]}
        if a != "Mstar":
            ax_b.errorbar(e["d"], y, xerr=[[e["d"] - e["dlo"]],
                                           [e["dhi"] - e["d"]]],
                          ecolor=col, zorder=3, **EB)
            ax_b.plot(e["d"], y, marker=mk, ms=ms,
                      mfc=col if e["in_V"] else "#FFFFFF", mec=col
                      if not e["in_V"] else "#000000",
                      mew=0.45 if e["in_V"] else 1.2, ls="none", zorder=4)
            row.update({"Mstar_minus_arm": e["d"], "paired_ci95_lo": e["dlo"],
                        "paired_ci95_hi": e["dhi"], "in_V_t": e["in_V"],
                        "paired_logs": e["n_logs"]})
        points.append(row)

for ax, xl, xlim, xt in (
        (ax_a, "(a)  Infeasible-decision rate (mean over logs), 95 % interval",
         (0, 1.0), [0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        (ax_b, "(b)  M* − arm, paired per-log difference, 95 % interval",
         (-0.85, 0.1), [-0.8, -0.6, -0.4, -0.2, 0])):
    ax.set_ylim(len(ARMS) - 0.5, -0.5)
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels([LABEL.get(a, a) for a in ARMS])
    ax.set_xlim(*xlim)
    ax.set_xticks(xt)
    ax.set_xticklabels(["%g" % t if t >= 0 else "−%g" % -t for t in xt])
    ax.grid(axis="x", color="#E3E3E3", lw=0.4, zorder=0)
    for i in range(1, len(ARMS)):
        ax.axhline(i - 0.5, color="#EFEFEF", lw=0.4, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", pad=2)
    ax.tick_params(axis="x", pad=2)
    ax.set_xlabel(xl, labelpad=3)
ax_b.axvline(0, color="#000000", lw=0.8, zorder=1)
ax_b.text(0.5 * (-0.85 + 0.1), 0, "(reference arm)", ha="center",
          va="center", fontsize=8, color="#555555")

h = [Line2D([], [], ls="none", marker=mk, ms=ms, mfc=col, mec="#000000",
            mew=0.45, label=tname)
     for _, tname, _, _, mk, col, ms in TRACKERS]
h += [Line2D([], [], ls="none", marker="o", ms=3.6, mfc="#555555",
             mec="#000000", mew=0.45, label=r"in $V_t$"),
      Line2D([], [], ls="none", marker="o", ms=3.6, mfc="#FFFFFF",
             mec="#555555", mew=1.0, label="removed from $V_t$")]
leg1 = fig.legend(handles=h[:2], loc="upper center", ncol=2, frameon=False,
                  bbox_to_anchor=(0.5, (FH - 0.03) / FH), borderaxespad=0,
                  handletextpad=0.3, columnspacing=1.6)
leg2 = fig.legend(handles=h[2:], loc="upper center", ncol=2, frameon=False,
                  bbox_to_anchor=(0.5, (FH - 0.23) / FH), borderaxespad=0,
                  handletextpad=0.3, columnspacing=1.6,
                  title=None)

# layout check
fig.canvas.draw()
rend = fig.canvas.get_renderer()
ok = True
for lg in (leg1, leg2):
    bb = lg.get_window_extent(rend)
    if bb.x0 < 0 or bb.x1 > FW * fig.dpi or \
            bb.y0 < (FH - TOP) * fig.dpi - 1:
        ok = False
for ax in (ax_a, ax_b):
    bb = ax.get_tightbbox(rend)
    if bb.x0 < 0 or bb.x1 > FW * fig.dpi + 1 or bb.y0 < 0:
        ok = False
bb_a = ax_a.get_tightbbox(rend)
bb_b = ax_b.get_tightbbox(rend)
if bb_a.y0 < bb_b.y1:
    ok = False
checks.append(("layout: legends above panel (a); panels inside the page and "
               "not overlapping", ok))
if not ok:
    raise SystemExit("layout check failed; nothing written")

fig.savefig(os.path.join(OUT, "fig03_infeasible_arms.pdf"))
fig.savefig(os.path.join(OUT, "fig03_infeasible_arms.png"), dpi=300)
cols = ["tracker", "arm", "infeasible_rate", "ci95_lo", "ci95_hi",
        "Mstar_minus_arm", "paired_ci95_lo", "paired_ci95_hi", "in_V_t",
        "paired_logs"]
with open(os.path.join(OUT, "fig03_points_v01.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for p in points:
        w.writerow({k: p.get(k, "") for k in cols})
for p in points:
    s = "%s %-8s rate %.4f [%.4f, %.4f]" % (p["tracker"], p["arm"],
                                            p["infeasible_rate"],
                                            p["ci95_lo"], p["ci95_hi"])
    if "Mstar_minus_arm" in p:
        s += "   M*-arm %+.4f [%+.4f, %+.4f]  in V_t %s" % (
            p["Mstar_minus_arm"], p["paired_ci95_lo"], p["paired_ci95_hi"],
            p["in_V_t"])
    print(s)
print("figure %.2f x %.2f in" % (FW, FH))
for msg, ok in checks:
    print("CHECK", "PASS" if ok else "FAIL", msg)
