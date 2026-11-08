"""make_c1_figs_v01: Figs. 9 and 10 of manuscript Section V-F7 (C1 run of record r1).

Reads only the decision of record, and the analysis CSVs of the run of record:
  60_RESULTS/c1_av2_v01/c1_decision_r1.json
  60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_{t1,t3}_decide_cells.csv
  60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_{t1,t3}_decide_arms.csv
  60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_{t1,t3}_decide_paired.csv
Writes (and refuses to overwrite any of them):
  95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf / .png
  95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf / .png
  95_SUBMISSION/figs_v01/figs_v01_manifest.json (inputs and outputs with SHA-256, values plotted)

Fig. 9: M*'s per-cell exceedance (point) with its simultaneous one-sided 95 % band
(sup-t over the population's evaluable cells; the lower end decides M*'s flags, the
upper end is the approximate cell bound whose maximum is U_max), per population and
tracker, with the delta = 0.05 line.
Fig. 10: (a) infeasible-decision rate per arm with its 95 % log-bootstrap interval;
(b) the paired log-level difference M* - arm with its two-sided 95 % interval; filled
markers are comparators in V_t (not shown above delta), open markers comparators
removed from V_t.

Descriptive figure code: it decides nothing and computes no new statistic.
Colours: categorical slots 1 and 2 of the dataviz reference palette (blue #2a78d6,
orange #eb6834; the first three slots validate all-pairs for colour-vision deficiency),
with marker shape as a second encoding (circle T1, square T3).
Run: python -I make_c1_figs_v01.py  (no arguments; workspace root from this file's path)
"""
import csv
import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(W, "60_RESULTS", "c1_av2_v01")
CSV = os.path.join(RES, "c1_analysis_csv_r1")
DEC = os.path.join(RES, "c1_decision_r1.json")
OUT = os.path.join(W, "95_SUBMISSION", "figs_v01")
OUTPUTS = ["fig09_mstar_cells.pdf", "fig09_mstar_cells.png",
           "fig10_infeasible_arms.pdf", "fig10_infeasible_arms.png",
           "figs_v01_manifest.json"]

DELTA = 0.05
TRACKERS = [("t1", "T1 (CANMOT)"), ("t3", "T3 (Poly-MOT)")]
POPS = [("PD7_primary", "P_rel"), ("SD1_7_gap_le_5m", "P_near"), ("PD_inpath", "P_ip")]
ARMS = ["Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED"]
ARM_LABEL = {"Mstar": "M*", "RETUNED": "RETUNED"}
COL = {"t1": "#2a78d6", "t3": "#eb6834"}
MARK = {"t1": "o", "t3": "s"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#d9d8d4"
WIDTH_IN = 3.5
DPI = 300

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7.5,
    "axes.titlesize": 7.5,
    "axes.labelsize": 7.5,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 6.8,
    "axes.edgecolor": INK2,
    "axes.linewidth": 0.6,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "text.color": INK,
    "axes.labelcolor": INK,
    "pdf.fonttype": 42,
    "savefig.dpi": DPI,
})


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(name):
    with open(os.path.join(CSV, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def refuse_overwrite():
    os.makedirs(OUT, exist_ok=True)
    existing = [p for p in OUTPUTS if os.path.exists(os.path.join(OUT, p))]
    if existing:
        sys.exit("refusing to overwrite existing output(s) in %s: %s" % (OUT, ", ".join(existing)))


def load():
    with open(DEC, encoding="utf-8") as f:
        dec = json.load(f)
    if dec.get("C1_verdict") is None:
        sys.exit("decision has no C1_verdict")
    inputs = {DEC: sha256(DEC)}
    cells, arms, paired = {}, {}, {}
    for t, _ in TRACKERS:
        for kind in ("cells", "arms", "paired"):
            name = "k8_within_lt3d_%s_decide_%s.csv" % (t, kind)
            inputs[os.path.join(CSV, name)] = sha256(os.path.join(CSV, name))
        rows = [r for r in read_csv("k8_within_lt3d_%s_decide_cells.csv" % t)
                if r["arm"] == "Mstar" and r["evaluable"] == "True"]
        cells[t] = {P: [r for r in rows if r["population"] == P] for P, _ in POPS}
        arms[t] = {r["arm"]: r for r in read_csv("k8_within_lt3d_%s_decide_arms.csv" % t)}
        prs = {}
        for r in read_csv("k8_within_lt3d_%s_decide_paired.csv" % t):
            if r["endpoint"] != "infeasible_rate":
                continue
            a, b = r["arm_a"], r["arm_b"]
            if b == "Mstar" and a in ARMS:      # mean_diff = a - M*  ->  M* - a = -mean_diff
                prs[a] = (-float(r["mean_diff"]), -float(r["ci95_hi"]), -float(r["ci95_lo"]))
            elif a == "Mstar" and b in ARMS:    # mean_diff = M* - b
                prs[b] = (float(r["mean_diff"]), float(r["ci95_lo"]), float(r["ci95_hi"]))
        paired[t] = prs
    return dec, cells, arms, paired, inputs


def check_against_decision(dec, cells):
    """The CSV's upper band ends must equal the decision's simultaneous upper bounds."""
    mu = dec["Mstar_simultaneous_upper_bounds"]["by_route"]["within_lt3d"]
    out = {}
    for t, _ in TRACKERS:
        for P, _ in POPS:
            ref = mu[t][P]
            rows = cells[t][P]
            if len(rows) != ref["evaluable"]:
                sys.exit("evaluable-cell count differs from the decision: %s %s" % (t, P))
            for r in rows:
                if abs(float(r["ub_sim"]) - ref["cells"][r["cell"]]) > 1e-12:
                    sys.exit("cell upper bound differs from the decision: %s %s %s" % (t, P, r["cell"]))
            out["%s/%s" % (t, P)] = {"U_max": ref["max_ub"], "U_max_cell": ref["max_cell"], "evaluable": ref["evaluable"]}
    return out


def fig09(cells, umax):
    fig, axes = plt.subplots(2, 1, figsize=(WIDTH_IN, 4.1), sharey=True)
    plotted = {}
    for ax, (t, tname) in zip(axes, TRACKERS):
        x0 = 0
        centres, names = [], []
        for i, (P, pname) in enumerate(POPS):
            rows = cells[t][P]
            xs = list(range(x0, x0 + len(rows)))
            est = [float(r["E"]) for r in rows]
            lo = [float(r["lb_sim"]) for r in rows]
            hi = [float(r["ub_sim"]) for r in rows]
            ax.vlines(xs, lo, hi, color=COL[t], linewidth=0.9, alpha=0.85, zorder=2)
            ax.plot(xs, est, linestyle="none", marker=MARK[t], markersize=2.6,
                    markerfacecolor=COL[t], markeredgecolor="white", markeredgewidth=0.4, zorder=3)
            u = umax["%s/%s" % (t, P)]["U_max"]
            ax.hlines(u, xs[0] - 0.4, xs[-1] + 0.4, color=INK2, linewidth=0.6, linestyle=(0, (1, 1)), zorder=1)
            ax.text((xs[0] + xs[-1]) / 2.0, u + 0.004, "U$_{max}$ %.3f" % u, ha="center", va="bottom",
                    fontsize=6.3, color=INK2)
            centres.append((xs[0] + xs[-1]) / 2.0)
            names.append("%s (%d)" % (pname, len(rows)))
            plotted["%s/%s" % (t, P)] = [{"cell": r["cell"], "E": float(r["E"]), "lb_sim": float(r["lb_sim"]),
                                          "ub_sim": float(r["ub_sim"])} for r in rows]
            if i < len(POPS) - 1:
                ax.axvline(xs[-1] + 1.0, color=GRID, linewidth=0.6, zorder=0)
            x0 = xs[-1] + 2
        ax.axhline(DELTA, color=INK, linewidth=0.8, linestyle=(0, (4, 2)), zorder=1)
        ax.axhline(0.0, color=GRID, linewidth=0.5, zorder=0)
        ax.set_xlim(-1.0, x0 - 0.5)
        ax.set_xticks(centres)
        ax.set_xticklabels(names)
        ax.tick_params(axis="x", length=0)
        ax.set_ylabel("Exceedance")
        ax.set_title(tname, loc="left", fontsize=7.5, color=INK, pad=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylim(-0.045, 0.18)
    handles = [Line2D([0], [0], color=COL[t], marker=MARK[t], markersize=3.2, linewidth=0.9,
                      markeredgecolor="white", markeredgewidth=0.4, label=n.split(" ")[0]) for t, n in TRACKERS]
    handles.append(Line2D([0], [0], color=INK, linewidth=0.8, linestyle=(0, (4, 2)), label="δ = 0.05"))
    handles.append(Line2D([0], [0], color=INK2, linewidth=0.6, linestyle=(0, (1, 1)), label="U$_{max}$"))
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.8, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.955), h_pad=0.8)
    return fig, plotted


def fig10(dec, arms, paired):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(WIDTH_IN, 2.75), sharey=True,
                                   gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.08})
    off = {"t1": -0.17, "t3": 0.17}
    ys = {a: i for i, a in enumerate(ARMS)}
    V = {t: set(dec["hypotheses"]["H1"]["by_tracker"][t]["V"]) for t, _ in TRACKERS}
    plotted = {}
    for t, _ in TRACKERS:
        plotted[t] = {}
        for a in ARMS:
            r = arms[t][a]
            y = ys[a] + off[t]
            rate, lo, hi = float(r["infeasible_rate"]), float(r["infeasible_ci95_lo"]), float(r["infeasible_ci95_hi"])
            ax1.hlines(y, lo, hi, color=COL[t], linewidth=0.9, zorder=2)
            ax1.plot(rate, y, marker=MARK[t], markersize=3.2, color=COL[t], markeredgecolor="white",
                     markeredgewidth=0.4, linestyle="none", zorder=3)
            entry = {"infeasible_rate": rate, "ci95": [lo, hi]}
            if a != "Mstar":
                d, dlo, dhi = paired[t][a]
                inv = a in V[t]
                ax2.hlines(y, dlo, dhi, color=COL[t], linewidth=0.9, zorder=2)
                ax2.plot(d, y, marker=MARK[t], markersize=3.4, linestyle="none", zorder=3,
                         markerfacecolor=COL[t] if inv else "white", markeredgecolor=COL[t], markeredgewidth=0.8)
                entry.update({"Mstar_minus_arm": d, "Mstar_minus_arm_ci95": [dlo, dhi], "in_V_t": inv})
            plotted[t][a] = entry
    ax1.set_yticks(range(len(ARMS)))
    ax1.set_yticklabels([ARM_LABEL.get(a, a) for a in ARMS])
    ax1.invert_yaxis()  # the y axis is shared: invert once, so M* is the top row
    for ax in (ax1, ax2):
        ax.grid(axis="x", color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
    ax1.set_xlim(0.0, 1.0)
    ax1.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax1.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax1.set_xlabel("(a) Infeasible-decision rate")
    ax2.axvline(0.0, color=INK, linewidth=0.8, zorder=1)
    ax2.set_xlim(-0.85, 0.15)
    ax2.set_xticks([-0.75, -0.5, -0.25, 0.0])
    ax2.set_xticklabels(["−0.75", "−0.5", "−0.25", "0"])
    ax2.set_xlabel("(b) M* − arm, paired")
    handles = [Line2D([0], [0], color=COL[t], marker=MARK[t], markersize=3.2, linewidth=0.9,
                      markeredgecolor="white", markeredgewidth=0.4, label=n) for t, n in TRACKERS]
    handles.append(Line2D([0], [0], color=INK2, marker="o", markersize=3.4, linestyle="none",
                          markerfacecolor=INK2, markeredgecolor=INK2, label="in V$_t$"))
    handles.append(Line2D([0], [0], color=INK2, marker="o", markersize=3.4, linestyle="none",
                          markerfacecolor="white", markeredgecolor=INK2, label="removed"))
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.5, columnspacing=0.8, handletextpad=0.4)
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.17, top=0.88)
    return fig, plotted


def main():
    refuse_overwrite()
    dec, cells, arms, paired, inputs = load()
    umax = check_against_decision(dec, cells)
    f9, p9 = fig09(cells, umax)
    f10, p10 = fig10(dec, arms, paired)
    paths = {}
    for fig, stem in ((f9, "fig09_mstar_cells"), (f10, "fig10_infeasible_arms")):
        for ext in ("pdf", "png"):
            p = os.path.join(OUT, "%s.%s" % (stem, ext))
            if os.path.exists(p):
                sys.exit("refusing to overwrite %s" % p)
            fig.savefig(p, dpi=DPI)
            paths[p] = sha256(p)
        plt.close(fig)
    manifest = {
        "tool": os.path.relpath(os.path.abspath(__file__), W).replace("\\", "/"),
        "tool_sha256": sha256(os.path.abspath(__file__)),
        "verdict_read": dec["C1_verdict"],
        "inputs": {os.path.relpath(k, W).replace("\\", "/"): v for k, v in inputs.items()},
        "outputs": {os.path.relpath(k, W).replace("\\", "/"): v for k, v in paths.items()},
        "width_in": WIDTH_IN, "dpi_png": DPI,
        "fig09": {"U_max": umax, "plotted": p9},
        "fig10": {"plotted": p10,
                  "V_t": {t: dec["hypotheses"]["H1"]["by_tracker"][t]["V"] for t, _ in TRACKERS}},
        "matplotlib": matplotlib.__version__,
    }
    mpath = os.path.join(OUT, "figs_v01_manifest.json")
    if os.path.exists(mpath):
        sys.exit("refusing to overwrite %s" % mpath)
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    for p, h in paths.items():
        print(h, os.path.relpath(p, W))


if __name__ == "__main__":
    main()
