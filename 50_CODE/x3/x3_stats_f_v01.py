#!/usr/bin/env python3
"""X3 analysis (f), the infeasibility-violation trade-off from the outputs of record (x3-stats, v01, 7 Nov 2026). Plan 2(f); M10.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

For every arm of record on the within_lt3d route (the 32 arms of the runs, the sweep arms B0a* and B0d*, RETUNED, and RETUNED-HK1),
on T1, T3 and AB3DMOT (tab):
  * figure 1: infeasible-decision rate against V2 (P_rel: the log-mean share of decisions with an exceeded relied constraint);
  * figure 2: infeasible-decision rate against V2_viol (the same with a violated relied constraint, D > G);
  * marker = the arm's screen status of record (c1_analysis_r1.json c1.<route>.<tracker>.status, the code of record's arm_status:
    valid, shown above delta, or floor only; RETUNED-HK1 from c1...RETUNED_HK1.status);
  * the back-off table: shares of decisions by executed back-off level lambda in {1, 0.75, 0.5, 0.25, 0} and the emergency stop
    (lambda = -1), for M* and each comparator, from decisions_*.npz 'lam'; pooled over decisions (the record's
    backoff_distribution) and as log means (the record's estimand for rates); also among infeasible decisions only.
Every plotted number is recomputed from the run tables (episodes + decisions, read-only) and checked against the record's CSV
(k8_within_lt3d_<t>_decide_v2.csv, _tradeoff.csv, _arms.csv) and c1_analysis_r1.json; the check table is in the JSON.
Light step (no bootstrap): about 150 MB per tracker. Run: python -B x3_stats_f_v01.py --out-dir <60_RESULTS/x3_explore_v01/f_tradeoff>
"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_stats_common_v01 as C  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TRACKERS = ("t1", "t3", "tab")
LAMS = (1.0, 0.75, 0.5, 0.25, 0.0, -1.0)
LAM_KEY = {1.0: "1", 0.75: "0.75", 0.5: "0.5", 0.25: "0.25", 0.0: "0", -1.0: "estop"}
BACKOFF_ARMS = ("Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")
PD7_BLOCKS = (0, 1, 2, 3)
STATUS_STYLE = {   # colour slots 1-3 of the reference palette (validated all-pairs); shape repeats the status
    "valid": {"color": "#2a78d6", "marker": "o", "label": "valid (passes the screen)"},
    "shown_above": {"color": "#eb6834", "marker": "X", "label": "shown above δ"},
    "floor_only": {"color": "#1baf7a", "marker": "s", "label": "floor only (not valid, not shown above)"},
}
LABELLED = ("Z0", "B0", "B1", "B3", "B4", "B6", "B9", "Mstar", "MstarJ", "MstarJx", "RETUNED", "RETUNED-HK1")


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def per_arm_tables(t, arm_of_scene):
    """Per arm and log: decisions, infeasible, V2 and V2_viol numerators / denominators on P_rel, lambda counts; read-only."""
    tag = C.tag_of(t)
    eps = {}
    with open(os.path.join(C.RUNS, "episodes_%s.jsonl" % tag), encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            if o.get("entered") and o["arm"] != "LOG":
                eps[int(o["episode"])] = (o["arm"], o["scene"], o.get("backoff_counts"), int(o.get("frames") or 0),
                                          int(o.get("infeasible_frames") or 0))
    arms = sorted({v[0] for v in eps.values()})
    scenes = sorted({v[1] for v in eps.values()})
    ai, si = {a: i for i, a in enumerate(arms)}, {s: i for i, s in enumerate(scenes)}
    maxep = max(eps) + 1
    ep_arm = np.full(maxep, -1, np.int64)
    ep_sc = np.full(maxep, -1, np.int64)
    ep_bo = {}
    for e, (a, s, bo, fr, inf) in eps.items():
        ep_arm[e], ep_sc[e] = ai[a], si[s]
        ep_bo[(a, s)] = (bo, fr, inf)
    z = np.load(os.path.join(C.RUNS, "decisions_%s.npz" % tag))
    dep = z["episode"].astype(np.int64)
    ok = dep < maxep
    ok[ok] = ep_arm[dep[ok]] >= 0
    dep = dep[ok]
    a_ = ep_arm[dep]
    s_ = ep_sc[dep]
    inf = z["infeasible"][ok].astype(np.float64)
    lam = z["lam"][ok].astype(np.float64)
    ob = z["ob"][ok]
    stf = [str(x) for x in z["st_fields"]]
    st = z["stats"][ok].reshape(-1, 4, len(stf))
    del z
    nn = st[:, list(PD7_BLOCKS), stf.index("n")].astype(np.float64).sum(1)
    xx = st[:, list(PD7_BLOCKS), stf.index("x")].astype(np.float64).sum(1)
    vv = st[:, list(PD7_BLOCKS), stf.index("v")].astype(np.float64).sum(1)
    del st
    has = (nn > 0) & (ob == 0)
    A, S = len(arms), len(scenes)

    def acc(w):
        m = np.zeros((A, S))
        np.add.at(m, (a_, s_), w)
        return m

    T = {"dec": acc(np.ones_like(inf)), "inf": acc(inf), "v2_den": acc(has.astype(float)), "v2_x": acc(((xx > 0) & has).astype(float)),
         "v2v_x": acc(((vv > 0) & has).astype(float))}
    for l_ in LAMS:
        T["lam_" + LAM_KEY[l_]] = acc((lam == l_).astype(float))
        T["lam_inf_" + LAM_KEY[l_]] = acc(((lam == l_) & (inf > 0)).astype(float))
    other = ~np.isin(lam, LAMS)
    cross = {"infeasible_and_lam1": int(((inf > 0) & (lam == 1.0)).sum()), "feasible_and_lam_lt1": int(((inf == 0) & (lam != 1.0)).sum()),
             "lam_outside_levels": int(other.sum()), "decisions": int(len(lam))}
    del dep, a_, s_, inf, lam, ob, nn, xx, vv, has
    # composites: RETUNED (record's arm_of_scene) and RETUNED-HK1 (the record's choice_by_fold; asserted below to be one arm)
    comp = {}
    if arm_of_scene:
        rows = np.array([ai[arm_of_scene[s]] for s in scenes])
        comp["RETUNED"] = rows
    return {"arms": arms, "scenes": scenes, "ai": ai, "T": T, "cross": cross, "composites": comp, "ep_bo": ep_bo}


def arm_row(D, arm):
    S = len(D["scenes"])
    if arm in D["composites"]:
        return D["composites"][arm], np.arange(S)
    return np.full(S, D["ai"][arm]), np.arange(S)


def summaries(D, arm):
    r, c = arm_row(D, arm)
    T = D["T"]
    g = lambda k: T[k][r, c]  # noqa: E731
    dec, inf = g("dec"), g("inf")
    m = dec > 0
    out = {"logs": int(m.sum()), "decisions": float(dec.sum()), "infeasible_rate": float(np.mean(inf[m] / dec[m]))}
    den = g("v2_den")
    mm = den > 0
    out["V2"] = float(np.mean(g("v2_x")[mm] / den[mm]))
    out["V2_viol"] = float(np.mean(g("v2v_x")[mm] / den[mm]))
    out["V2_logs"] = int(mm.sum())
    bo = {}
    infd = inf.sum()
    for l_ in LAMS:
        k = LAM_KEY[l_]
        cnt = g("lam_" + k)
        bo[k] = {"pooled_share": float(cnt.sum() / dec.sum()), "log_mean_share": float(np.mean(cnt[m] / dec[m])),
                 "share_of_infeasible_decisions": float(g("lam_inf_" + k).sum() / infd) if infd > 0 else None}
    out["backoff"] = bo
    lam_mean = sum((max(l_, 0.0)) * g("lam_" + LAM_KEY[l_]) for l_ in LAMS)
    out["mean_backoff_level_log_mean"] = float(np.mean(lam_mean[m] / dec[m]))
    return out


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def status_of(st):
    if st is None:
        return None
    return "valid" if st["valid"] else ("shown_above" if st["shown_above"] else "floor_only")


def build(t, ext, log):
    rec = ext["trackers"][t]
    t0 = time.time()
    D = per_arm_tables(t, rec["retune_arm_of_scene"])
    log("%s tables (%.0f s)" % (t, time.time() - t0))
    choice = {k: v["arm"] for k, v in (rec["RETUNED_HK1"]["choice_by_fold"] or {}).items()}
    hk1_arms = sorted(set(choice.values()))
    assert len(hk1_arms) == 1, "RETUNED-HK1 is a composite of several arms; not handled by v01"
    D["composites"]["RETUNED-HK1"] = np.full(len(D["scenes"]), D["ai"][hk1_arms[0]])
    arms = [a for a in rec["arms"] if a != "LOG"] + ["RETUNED", "RETUNED-HK1"]
    arms = list(dict.fromkeys(arms))
    v2csv = read_csv(os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_v2.csv" % t))
    v2rec = {(r["arm"], r["variant"]): fnum(r["E"]) for r in v2csv if r["population"] == "PD7_primary"}
    trade = {r["arm"]: r for r in read_csv(os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_tradeoff.csv" % t))}
    armsc = {r["arm"]: r for r in read_csv(os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_arms.csv" % t))}
    rows, checks = [], []
    for a in arms:
        s = summaries(D, a)
        ra = hk1_arms[0] if a == "RETUNED-HK1" else a
        st = rec["RETUNED_HK1"]["status"] if a == "RETUNED-HK1" else rec["status"].get(a)
        row = {"arm": a, "status": status_of(st), "infeasible_rate": s["infeasible_rate"], "V2": s["V2"], "V2_viol": s["V2_viol"],
               "decisions": s["decisions"], "logs": s["logs"], "backoff": s["backoff"],
               "mean_backoff_level_log_mean": s["mean_backoff_level_log_mean"],
               "kind": "sweep" if (a.startswith("B0a") or a.startswith("B0d")) else "arm"}
        if a == "RETUNED-HK1":
            row["equals_arm"] = ra
        rows.append(row)
        # checks against the record
        inf_rec = rec["infeasible_rate"].get("RETUNED_HK1" if a == "RETUNED-HK1" else a)
        pairs = [("infeasible_rate vs c1 json", s["infeasible_rate"], inf_rec),
                 ("V2 vs v2.csv", s["V2"], v2rec.get((ra, "V2"))), ("V2_viol vs v2.csv", s["V2_viol"], v2rec.get((ra, "V2_viol")))]
        if a in trade:
            pairs.append(("infeasible_rate vs tradeoff.csv", s["infeasible_rate"], fnum(trade[a]["infeasible_rate"])))
            pairs.append(("status valid vs tradeoff.csv valid_form_B", float(st["valid"]) if st else None,
                          float(trade[a]["valid_form_B"] == "True")))
        if a in armsc:
            ar = armsc[a]
            for l_ in LAMS:
                k = LAM_KEY[l_]
                pairs.append(("backoff pooled share %s vs arms.csv" % k, s["backoff"][k]["pooled_share"], fnum(ar.get("backoff_share_" + k))))
            pairs.append(("estop log-mean share vs arms.csv estop_share", s["backoff"]["estop"]["log_mean_share"], fnum(ar.get("estop_share"))))
            pairs.append(("mean back-off level vs arms.csv", s["mean_backoff_level_log_mean"], fnum(ar.get("mean_backoff_level"))))
            pairs.append(("decisions vs arms.csv", s["decisions"], fnum(ar.get("decisions"))))
        for name, x, y in pairs:
            checks.append({"arm": a, "check": name, "x3": x, "record": y,
                           "abs_diff": None if (x is None or y is None) else abs(x - y)})
    # the episodes' own back-off counts (record per episode) against the decision rows, for the back-off arms
    ep_bad = 0
    tot_bo = {}
    for (a, s_), (bo, fr, inf) in D["ep_bo"].items():
        if not bo:
            continue
        d = tot_bo.setdefault(a, {k: 0 for k in LAM_KEY.values()})
        for k in d:
            d[k] += int(bo.get(k, 0))
    for a, d in tot_bo.items():
        r = D["ai"][a]
        for l_ in LAMS:
            k = LAM_KEY[l_]
            if int(D["T"]["lam_" + k][r].sum()) != d[k]:
                ep_bad += 1
    out = {"rows": rows, "checks": checks, "cross_tab": D["cross"], "RETUNED_HK1_arm": hk1_arms[0],
           "episode_backoff_counts_vs_decisions": {"arms": len(tot_bo), "mismatching_levels": ep_bad}}
    out["max_abs_diff"] = max([c["abs_diff"] for c in checks if c["abs_diff"] is not None] or [0.0])
    out["unchecked"] = [c for c in checks if c["abs_diff"] is None]
    log("%s built: %d arms, max abs diff %.2e (%.0f s)" % (t, len(rows), out["max_abs_diff"], time.time() - t0))
    del D
    return out


OFFSETS = [(6, 4), (6, -11), (-6, 4), (-6, -11), (6, 14), (6, -21), (-6, 14), (-6, -21), (14, 24), (14, -31), (-14, 24), (-14, -31),
           (22, 34), (22, -41), (-22, 34), (-22, -41)]


def place_labels(fig, ax, items, points):
    """Greedy label placement: each label takes the first offset whose box overlaps no marker and no earlier label box and stays
    in the axes (offsets beyond the first four get a thin leader line); if none fits, the first offset is used."""
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    taken = []
    for (px, py) in points:
        dx_, dy_ = ax.transData.transform((px, py))
        taken.append(Bbox.from_extents(dx_ - 5, dy_ - 5, dx_ + 5, dy_ + 5))
    axbox = ax.get_window_extent(rend)
    for (x, y, lab, strong) in items:
        placed = None
        for k, (dx, dy) in enumerate(OFFSETS):
            ha = "left" if dx >= 0 else "right"
            tx = ax.annotate(lab, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, ha=ha,
                             color="#0b0b0b" if strong else "#52514e", fontweight="bold" if strong else "normal", zorder=5)
            bb = tx.get_window_extent(rend).expanded(1.05, 1.15)
            inside = axbox.x0 <= bb.x0 and bb.x1 <= axbox.x1 and axbox.y0 <= bb.y0 and bb.y1 <= axbox.y1
            if inside and not any(bb.overlaps(o) for o in taken):
                placed = tx
                taken.append(bb)
                if k >= 4:
                    tx.set_text(lab)
                    tx.arrow_patch = None
                    tx.remove()
                    tx = ax.annotate(lab, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, ha=ha,
                                     color="#0b0b0b" if strong else "#52514e", fontweight="bold" if strong else "normal", zorder=5,
                                     arrowprops={"arrowstyle": "-", "color": "#9a9893", "lw": 0.6, "shrinkA": 0, "shrinkB": 3})
                break
            tx.remove()
        if placed is None:
            ax.annotate(lab, (x, y), xytext=OFFSETS[0], textcoords="offset points", fontsize=7.5,
                        color="#0b0b0b" if strong else "#52514e", fontweight="bold" if strong else "normal", zorder=5)


def figure(res, xkey, xlabel, fname_stem, out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 6.0), sharey=True)
    for ax, t in zip(axes, TRACKERS):
        rows = res[t]["rows"]
        sw = sorted([r for r in rows if r["kind"] == "sweep"], key=lambda r: r["infeasible_rate"])
        ax.plot([r[xkey] for r in sw], [r["infeasible_rate"] for r in sw], color="#9a9893", lw=1.0, zorder=1)
        for r in rows:
            stl = STATUS_STYLE[r["status"]]
            big = r["arm"] in ("Mstar",)
            ax.scatter([r[xkey]], [r["infeasible_rate"]], s=(110 if big else (26 if r["kind"] == "sweep" else 52)),
                       marker=stl["marker"], color=stl["color"], edgecolors="white", linewidths=1.0, zorder=3)
        ax.set_title(C.TRACKER_NAME[t], fontsize=11)
        ax.set_xlabel(xkey, fontsize=9.5)
        ax.grid(True, color="#e6e5e1", lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=8.5)
    axes[0].set_ylabel("Infeasible-decision rate (log mean)", fontsize=9.5)
    axes[0].set_ylim(-0.02, 1.04)
    handles = [plt.Line2D([], [], ls="", marker=s["marker"], color=s["color"], markersize=8, label=s["label"])
               for s in STATUS_STYLE.values()]
    handles.append(plt.Line2D([], [], color="#9a9893", lw=1.0, label="B0 sweep arms (B0a*, B0d*; small markers), joined"))
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.supxlabel(xlabel, fontsize=9.5, y=0.03)
    fig.text(0.5, 0.005, C.STAMP + "  |  within_lt3d, decision mode; status of record (comparators of K at 1 - 0.0125/9, other arms at 0.95)",
             ha="center", fontsize=7, color="#52514e")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    prio = ["Mstar", "B6", "B4", "B0", "B3", "RETUNED", "B1", "B9", "RETUNED-HK1", "Z0", "MstarJ", "MstarJx"]
    for ax, t in zip(axes, TRACKERS):
        rows = {r["arm"]: r for r in res[t]["rows"]}
        items = []
        for a in prio:
            r = rows[a]
            lab = "M*" if a == "Mstar" else ("RETUNED-HK1 (=%s)" % r["equals_arm"] if a == "RETUNED-HK1" else a)
            items.append((r[xkey], r["infeasible_rate"], lab, a == "Mstar"))
        place_labels(fig, ax, items, [(r[xkey], r["infeasible_rate"]) for r in res[t]["rows"]])
    paths = []
    for ext in ("pdf", "png"):
        p = os.path.join(out_dir, "%s.%s" % (fname_stem, ext))
        if os.path.exists(p):
            raise FileExistsError(p)
        fig.savefig(p, dpi=200, metadata={"Title": fname_stem, "Subject": C.STAMP} if ext == "pdf" else None)
        paths.append(p)
    plt.close(fig)
    return paths


def write_md(path, out):
    f3 = lambda v: "-" if v is None else "%.3f" % v  # noqa: E731
    lines = ["# X3 (f): the infeasibility-violation trade-off (v01)", "", "**%s**" % C.STAMP, "",
             "Plan 2(f) (sha256 %s...); referee concern M10. Outputs of record only: within_lt3d, decision mode, 375 logs. "
             "V2 = log-mean share of decisions (with a P_rel record) in which some relied constraint is exceeded; V2_viol = the same with a "
             "relied constraint violated (D > G); infeasible = log-mean infeasible-decision share. Status of record: comparators of K (B0, "
             "B1, B3, B4, B6, B9, RETUNED) judged at their removal level 1 - 0.0125/9, every other arm at 0.95 (c1_analyse_v02.arm_status)."
             % C.PLAN_SHA[:8], "",
             "Figures: `x3_f_infeasible_vs_V2_v01.pdf/.png`, `x3_f_infeasible_vs_V2viol_v01.pdf/.png`. JSON: `x3_f_tradeoff_v01.json`.", "",
             "## Checks against the record", ""]
    for t in TRACKERS:
        r = out["trackers"][t]
        lines.append("- %s: %d checks, largest absolute difference %.2e, %d unchecked (no record value); decision cross-tab: %s; "
                     "episode back-off counts vs decision rows: %d mismatching levels over %d arms." % (
                         t, len(r["checks"]), r["max_abs_diff"], len(r["unchecked"]), r["cross_tab"],
                         r["episode_backoff_counts_vs_decisions"]["mismatching_levels"], r["episode_backoff_counts_vs_decisions"]["arms"]))
    for t in TRACKERS:
        r = out["trackers"][t]
        lines += ["", "## %s: every arm" % C.TRACKER_NAME[t], "", "| Arm | Status | Infeasible | V2 | V2_viol |", "|---|---|---|---|---|"]
        for row in sorted(r["rows"], key=lambda x: (x["kind"] == "sweep", x["infeasible_rate"])):
            lines.append("| %s | %s | %s | %s | %s |" % (row["arm"] + (" (= %s)" % row["equals_arm"] if row.get("equals_arm") else ""),
                                                       row["status"], f3(row["infeasible_rate"]), f3(row["V2"]), f3(row["V2_viol"])))
    for t in TRACKERS:
        r = out["trackers"][t]
        lines += ["", "## %s: back-off levels executed (share of decisions, pooled over decisions; log mean in brackets)" % C.TRACKER_NAME[t], "",
                  "| Arm | Infeasible | lambda 1 | 0.75 | 0.5 | 0.25 | 0 | e-stop (-1) | among infeasible: 0.75 / 0.5 / 0.25 / 0 / e-stop |",
                  "|---|---|---|---|---|---|---|---|---|"]
        rows = {x["arm"]: x for x in r["rows"]}
        for a in BACKOFF_ARMS:
            x = rows[a]
            b = x["backoff"]
            inf_part = " / ".join(f3(b[k]["share_of_infeasible_decisions"]) for k in ("0.75", "0.5", "0.25", "0", "estop"))
            lines.append("| %s | %s | %s |  %s |" % ("M*" if a == "Mstar" else a, f3(x["infeasible_rate"]), " | ".join(
                "%s (%s)" % (f3(b[k]["pooled_share"]), f3(b[k]["log_mean_share"])) for k in ("1", "0.75", "0.5", "0.25", "0", "estop")), inf_part))
    lines += ["", "## Reading", ""] + ["- " + x for x in out["reading"]]
    lines += ["", "## Choices", ""] + ["- " + c for c in out["choices"]]
    lines += ["", "Code: `50_CODE/x3/x3_stats_f_v01.py` (sha256 in the JSON). Nothing here changes a status or table of record.", ""]
    C.text_new(path, "\n".join(lines))


CHOICES = [
    "V2 and V2_viol are read on P_rel (PD7_primary), the population of the record's headline V2 (D19 section 2; referee M10's numbers).",
    "The screen status is the record's own arm_status (c1 section), so comparators of K carry their removal-level status and the sweep, "
    "Z0 and the joint arms their 0.95 status; RETUNED-HK1's status is the record's RETUNED_HK1.status.",
    "RETUNED-HK1 chose B0a8 in every fold on all three trackers (record choice_by_fold), so its point coincides with B0a8's; it is drawn "
    "and labelled separately.",
    "The sweep arms are joined in order of infeasible rate (the merged alpha / delta' curve is monotone in the margin scale); the line is "
    "a visual guide only.",
    "Back-off shares: pooled over decisions (the record's backoff_distribution, checked against arms.csv) and log means; lambda = -1 is "
    "the emergency stop. 'Among infeasible' divides by the arm's infeasible decisions.",
]


def reading(res):
    out = []
    for t in TRACKERS:
        rows = {r["arm"]: r for r in res[t]["rows"]}
        m = rows["Mstar"]
        valid_others = [r for r in res[t]["rows"] if r["status"] == "valid" and r["arm"] != "Mstar"]
        lower_inf_valid = [r["arm"] for r in valid_others if r["infeasible_rate"] < m["infeasible_rate"]]
        out.append("%s: M* (%s) infeasible %.3f, V2 %.3f, V2_viol %.3f. Arms with status valid besides M*: %s; of these, less often "
                   "infeasible than M*: %s. M*'s infeasible decisions: e-stop share %.3f, lambda 0 share %.3f of them." % (
                       t, m["status"], m["infeasible_rate"], m["V2"], m["V2_viol"],
                       ", ".join("%s (%.3f / %.3f / %.3f)" % (r["arm"], r["infeasible_rate"], r["V2"], r["V2_viol"]) for r in valid_others) or "none",
                       ", ".join(lower_inf_valid) or "none", m["backoff"]["estop"]["share_of_infeasible_decisions"] or 0.0,
                       m["backoff"]["0"]["share_of_infeasible_decisions"] or 0.0))
        dom = [r["arm"] for r in res[t]["rows"] if r["arm"] != "Mstar" and r["infeasible_rate"] <= m["infeasible_rate"]
               and r["V2_viol"] <= m["V2_viol"]]
        dom2 = [r["arm"] for r in res[t]["rows"] if r["arm"] != "Mstar" and r["infeasible_rate"] <= m["infeasible_rate"]
                and r["V2"] <= m["V2"]]
        lower_viol = [r["arm"] for r in res[t]["rows"] if r["arm"] != "Mstar" and r["V2_viol"] < m["V2_viol"]
                      and r["arm"] in BACKOFF_ARMS]
        es = sorted({round(rows[a]["backoff"]["estop"]["pooled_share"], 6) for a in BACKOFF_ARMS})
        out.append("%s: arms at or below M* on both infeasible rate and V2_viol: %s; on both infeasible rate and V2: %s. Comparators "
                   "of K with lower V2_viol than M*: %s. Emergency-stop share of decisions across M* and the comparators: %s "
                   "(the same for every arm when a single value)." % (t, ", ".join(dom) or "none", ", ".join(dom2) or "none",
                                                                    ", ".join(lower_viol) or "none", es))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    jpath = os.path.join(a.out_dir, "x3_f_tradeoff_v01.json")
    mpath = os.path.join(a.out_dir, "x3_f_tradeoff_v01.md")
    for p in (jpath, mpath):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)

    def log(*x):
        print(time.strftime("%H:%M:%S"), *x, flush=True)

    assert C.sha256(C.PLAN) == C.PLAN_SHA, "plan hash differs"
    ext = C.load_record_extract(TRACKERS)
    res = {}
    for i, t in enumerate(TRACKERS):
        C.live("(f) trade-off tables %s" % t, i, 3)
        res[t] = build(t, ext, log)
    figs = figure(res, "V2", "V2: share of decisions with an exceeded relied constraint (P_rel, log mean)", "x3_f_infeasible_vs_V2_v01", a.out_dir)
    figs += figure(res, "V2_viol", "V2_viol: share of decisions with a violated relied constraint (P_rel, log mean)",
                   "x3_f_infeasible_vs_V2viol_v01", a.out_dir)
    out = {"stamp": C.STAMP, "analysis": "X3 (f) infeasibility-violation trade-off, plan 2(f); referee M10",
           "plan": {"path": "20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md", "sha256": C.PLAN_SHA},
           "inputs": {"analysis_sha256": ext["analysis_sha256"],
                      "csv_sha256": {os.path.basename(p): C.sha256(p) for t in TRACKERS for p in (
                          os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_%s.csv" % (t, k)) for k in ("v2", "tradeoff", "arms"))},
                      "runs_sha256": {"%s_%s" % (k, t): C.sha256(os.path.join(C.RUNS, "%s_%s%s" % (k, C.tag_of(t), e)))
                                      for t in TRACKERS for k, e in (("episodes", ".jsonl"), ("decisions", ".npz"))}},
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__)},
           "versions": dict(C.versions(), matplotlib=matplotlib.__version__), "figures": [os.path.basename(p) for p in figs],
           "trackers": res, "choices": CHOICES, "reading": reading(res)}
    C.jdump_new(jpath, out)
    write_md(mpath, out)
    C.live("(f) trade-off done", 3, 3, "figures and tables written")
    log("wrote", jpath, mpath, figs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
