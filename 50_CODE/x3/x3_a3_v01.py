#!/usr/bin/env python3
"""X3 amendment A3 (x3-core agent, x3_a3_v01, 7 Nov 2026). Added after review (amendment A3).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).
Amendment: 20_DESIGN/X3_PLAN_AMENDMENT_A3_v01.md (sha256 009a0aad...).

(i) cost of infeasible decisions: per arm, by k8_analyse_v04's own definitions (dec_rows, arm_endpoints, v2_summary on P_rel = PD7,
    offset bin 0): infeasible rate, progress ratio, mean executed back-off level, V2, V2_exec, V2_viol, share of decisions with a
    minimum enforced gap < 1 m (the point estimates are the key means of record; intervals: log bootstrap B = 4000, seed
    [20261201, i, 9]); M* - arm paired for the progress ratio and V2_exec (k8_analyse_v04.wmean_ci on the per-log differences, as
    paired_rows). Check: on the arms of record the values equal c1_analysis_csv_r1/k8_within_lt3d_<t>_decide_{arms,v2}.csv.
    Matched composites of (a): per log, the decisions of the grid point chosen for its fold.
(ii) analysis (b)'s partition screen (same bins, rule, seeds [20261201, i, 2]) on the (a) composites (B6 T1 and T3; RETUNED-HK1 T1 =
    B0a8 in every fold), the passing in-sample grid points of (a), and B8, from re-runs with partition counts (x3_run_v02 --parts;
    the (a) and (e1) runs of rounds 1-2 were made without --parts); each re-run is checked equal to its earlier run (or the record's).
(iii) M*'s cross-fitted exceedance on its own calibration items (every separating axis at the reference pose: the items of record),
    each held-out fold's fits_within thresholds applied to that fold's items, U = D / sd > c; per own-threshold L0 stratum (the
    item's threshold is its stratum's own fit, source level L0) and in-path part, check times pooled; log-weighted rate
    (k6_analyse_v02.rates), one-sided simultaneous sup-t flags at 0.95 over the evaluable strata (>= 39 logs); the fallback share
    (items whose threshold comes from a coarser level) and their pooled rate. Bootstrap B = 4000, seed [20261201, i, 9].
(iv) (b)'s flags recomputed for every arm at the per-partition one-sided level 1 - 0.05/7.
(v) the B0-sweep infeasible rate at M*'s V2 (P_rel) by linear interpolation along the sweep in V2 order (record CSV values).
Commands: i | spec | check_ii | ii | iii | iv | sweep
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
import x3_screen_v01 as SC  # noqa: E402

K, A, S = SC.K, SC.A, SC.S
LABEL = "added after review (amendment A3)"
OUT = os.path.join(C.OUT, "a3_review")
RUN_DIR = os.path.join(C.OUT, "runs")
CSV_DIR = os.path.join(C.REC, "c1_analysis_csv_r1")
AMEND = os.path.join(C.W, "20_DESIGN", "X3_PLAN_AMENDMENT_A3_v01.md")
J_A3 = 9
PD7 = (0, 1, 2, 3)
ENDP = ("infeasible_rate", "progress_ratio", "mean_backoff_level", "min_gap_share_lt_1m")
V2V = ("V2", "V2_exec", "V2_viol")
REC_ARMS = ["Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED", "Z0"] + list(S.SWEEP_ARMS)


def seeds_a3(t):
    return [C.SEED_BOOT_X3, C.TRACKER_I[t], J_A3]


def stamp():
    return {"stamp": C.STAMP, "label": LABEL, "amendment_sha256": C.sha256(AMEND)}


def load_dec(run_dir, tag):
    eps = SC.entered([json.loads(l) for l in open(os.path.join(run_dir, "episodes_%s.jsonl" % tag))])
    D = dict(np.load(os.path.join(run_dir, "decisions_%s.npz" % tag)))
    return eps, D


def kw_for(t, scenes):
    eps = [{"scene": s, "delay_kf": 0, "arm": "x", "entered": True} for s in scenes]
    return SC.keys_W(eps, C.B_X3, seeds_a3(t))


def endpoints(rows, kix, n, W):
    res, vecs = K.arm_endpoints(rows, kix, n, W)
    out = {e: res[e]["mean"] for e in ENDP}
    out["ci95"] = {e: res[e]["ci95"] for e in ENDP}
    pk = {"progress_ratio": vecs["progress_ratio"]}
    for var in V2V:
        nf, xf, near_only, ref = K.V2_VARIANTS[var]
        s_, per_key = K.v2_summary(rows, kix, n, W, PD7, (0,), nf, xf, ref)
        out[var] = s_["E"]
        out["ci95"][var] = s_["ci95"]
        pk[var] = per_key
    out["decisions"] = int(len(kix))
    return out, pk


def compose(parts_by_arm, choice_of_fold, fold_of_key):
    """Per log, the rows of the arm chosen for its fold (a composite)."""
    rows, kix = {}, []
    for f, arm in choice_of_fold.items():
        r_, k_ = parts_by_arm[arm]
        m = fold_of_key[k_] == int(f)
        for fld, v in r_.items():
            rows.setdefault(fld, []).append(v[m])
        kix.append(k_[m])
    return {fld: np.concatenate(v) for fld, v in rows.items()}, np.concatenate(kix)


def part_i(t):
    am = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")))["by_tracker"][t]
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    aos = an["k8"]["within_lt3d"][t]["retune"]["arm_of_scene"]
    hk1 = an["c1"]["within_lt3d"][t]["RETUNED_HK1"]["choice_by_fold"]
    del an
    eps, D = load_dec(C.REC_RUNS, "%s_decide" % C.TAG_REC[t])
    scenes = sorted({o["scene"] for o in eps})
    kw = kw_for(t, scenes)
    keys, W = kw["keys"], kw["W"]
    n = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    D0 = {"episode": np.zeros(0, np.int64)}
    eps, _, D, _ = K.add_composite_arm(eps, dict(D0), D, dict(D0), aos)
    rba = K.dec_rows(D, eps, kidx)
    del D
    folds = json.load(open(C.FOLDS))["fold_of_log"]
    fold_of_key = np.array([int(folds[k[0]]) for k in keys])
    res, pks = {}, {}
    for a in REC_ARMS:
        res[a], pks[a] = endpoints(*rba[a], n, W)
        res[a]["source"] = "run of record"
    rhk = compose(rba, {f: c["arm"] for f, c in hk1.items()}, fold_of_key)
    res["RETUNED_HK1"], pks["RETUNED_HK1"] = endpoints(*rhk, n, W)
    res["RETUNED_HK1"]["source"] = "record's per-fold choice %s" % {f: c["arm"] for f, c in hk1.items()}
    # the check against the record's CSVs
    arms_csv = {r["arm"]: r for r in csv.DictReader(open(os.path.join(CSV_DIR, "k8_within_lt3d_%s_decide_arms.csv" % t)))}
    v2_csv = {(r["population"], r["arm"], r["variant"]): r for r in csv.DictReader(open(os.path.join(CSV_DIR, "k8_within_lt3d_%s_decide_v2.csv" % t)))}
    chk, worst = {}, 0.0
    for a in REC_ARMS:
        for e in ENDP:
            d = abs(res[a][e] - float(arms_csv[a][e]))
            worst = max(worst, d)
            chk["%s/%s" % (a, e)] = d
        for var in V2V:
            d = abs(res[a][var] - float(v2_csv[("PD7_primary", a, var)]["E"]))
            worst = max(worst, d)
            chk["%s/%s" % (a, var)] = d
    del rba
    # X3 arms
    rb = {}
    for tag in ("core_%s" % t, "a_%s" % t, "e1_%s" % t, "e2_%s" % t, "d_%s" % t, "g_%s" % t):
        e_, D_ = load_dec(RUN_DIR, tag)
        assert sorted({(o["scene"], o["delay_kf"]) for o in e_}) == keys
        r_ = K.dec_rows(D_, e_, kidx)
        del D_
        for a, v in r_.items():
            lab = "%s@0.05" % a if (tag.startswith("core") and a in ("B4", "B6", "B9")) else a
            if tag.startswith("core") and a not in ("B4", "B6", "B9", "Mstar"):
                continue
            rb[lab] = v
    x3 = {}
    for fam, f in am["families"].items():
        lab = "A_%s_composite" % fam
        x3[lab] = compose(rb, {k_: c["point"] for k_, c in f["choice_by_fold"].items()}, fold_of_key)
    for a in ("X3E1_B5", "X3E1_B8", "X3E1_B7", "X3E2_B0_qrefit", "X3E2_B0_qrefit_ext", "X3D_Mstar_d1", "X3D_Mstar_d2"):
        x3[a] = rb[a]
    for a in sorted(rb):
        if a.startswith("X3G_n"):
            x3[a] = rb[a]
    mx, _ = endpoints(*rb["Mstar"], n, W)
    assert all(abs(mx[e] - res["Mstar"][e]) < 1e-12 for e in ENDP + V2V), "the core run's M* differs from the record's"
    for a, (r_, k_) in x3.items():
        res[a], pks[a] = endpoints(r_, k_, n, W)
        res[a]["source"] = "X3 run" + (" (composite by fold: %s)" % {k2: c["point"] for k2, c in am["families"][a.split("_")[1]]["choice_by_fold"].items()}
                                       if a.startswith("A_") else "")
    paired = {}
    for a in res:
        if a == "Mstar":
            continue
        paired[a] = {}
        for e in ("progress_ratio", "V2_exec"):
            r = K.wmean_ci(pks["Mstar"][e] - pks[a][e], W)
            paired[a][e] = {"mean_diff": r["mean"], "ci95": r["ci95"], "n_logs": r["n"]}
        paired[a]["progress_cost_reading"] = ("progress ratio differs by < 0.02: no progress cost in this leashed replay"
                                              if abs(res["Mstar"]["progress_ratio"] - res[a]["progress_ratio"]) < 0.02 else
                                              "progress ratio differs by >= 0.02")
    return {"tracker": t, "seed_bootstrap": seeds_a3(t), "B": C.B_X3, "arms": res, "Mstar_minus_arm": paired,
            "check_vs_record_csv": {"max_abs_diff": worst, "passed": bool(worst < 1e-12), "compared": len(chk)}}


def md_i(r):
    L = ["# X3 A3 (i): what an infeasible decision costs", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "k8_analyse_v04's own definitions (arm_endpoints, v2_summary on P_rel = PD7): log means. M* - arm: per-log paired, log bootstrap "
         "95 % interval (B = 4000, seed [20261201, i, 9]). Reading fixed by A3: a progress-ratio difference < 0.02 = no progress cost in this "
         "leashed replay. An infeasible decision is one at which the planner cannot keep its per-constraint risk statement (Proposition 1 "
         "covers feasible decisions only); V2_exec is reported, arms are not ranked on it.", ""]
    for t, x in r["by_tracker"].items():
        L += ["## %s" % t.upper(), "", "Check against the record's CSVs (%d values, arms of record): max |diff| = %.2e, **%s**." % (
            x["check_vs_record_csv"]["compared"], x["check_vs_record_csv"]["max_abs_diff"], x["check_vs_record_csv"]["passed"]), "",
              "| arm | infeasible | progress ratio | mean back-off | V2 | V2_exec | V2_viol | min gap < 1 m | M* - arm progress (95 % CI) | M* - arm V2_exec (95 % CI) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for a, v in x["arms"].items():
            p = x["Mstar_minus_arm"].get(a)
            f2 = lambda q: "%.4f [%.4f, %.4f]" % (q["mean_diff"], q["ci95"][0], q["ci95"][1]) if q and q.get("ci95") else "-"  # noqa: E731
            L.append("| %s | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f | %s | %s |" % (
                a, v["infeasible_rate"], v["progress_ratio"], v["mean_backoff_level"], v["V2"], v["V2_exec"], v["V2_viol"], v["min_gap_share_lt_1m"],
                f2(p["progress_ratio"]) if p else "-", f2(p["V2_exec"]) if p else "-"))
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- (ii) re-runs with partition counts
def ii_variants(t):
    fd = os.path.join(C.OUT, "a_matched", "fits")
    e1 = os.path.join(C.OUT, "e_alternatives", "fits", "fits_x3e1_B8_%s.json" % t)
    am = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")))["by_tracker"][t]
    pts = set()
    for fam in ("B6",):
        pts |= {c["point"] for c in am["families"][fam]["choice_by_fold"].values()}
    for fam, f in am["families"].items():
        pts |= {c["point"] for c in f["curve"] if c["in_sample"]["valid"]}
    vs = [{"label": p, "base": p.split("@")[0], "fits": os.path.join(fd, "fits_x3a_%s_d%s.json" % (t, p.split("@")[1])), "cov_dir": None}
          for p in sorted(pts)]
    if t == "t1":
        vs.append({"label": "B0a8", "base": "B0a8", "fits": None, "cov_dir": None})
    vs.append({"label": "X3E1_B8", "base": "Mstar", "fits": e1, "cov_dir": None})
    return vs


def write_spec():
    for t in ("t1", "t3"):
        C.jdump(os.path.join(RUN_DIR, "specs", "spec_a3p_%s_v01.json" % t),
                dict(stamp(), purpose="A3 (ii): (a) composite points, passing in-sample grid points, RETUNED-HK1 (B0a8, T1) and B8, "
                                      "re-run with partition counts", variants=ii_variants(t)))
        print(t, [v["label"] for v in ii_variants(t)])


def check_ii(t):
    """The partition re-runs equal the earlier runs (decisions, counts, cal, summaries) and their partition sums equal the counts."""
    import x3_gates_v01 as GV
    tag = "a3p_%s" % t
    mine = GV.load_outputs(RUN_DIR, tag)
    labels = sorted({o["arm"] for o in mine["eps"]})
    res = {}
    for lab in labels:
        src_dir, src_tag = ((C.REC_RUNS, "%s_decide" % C.TAG_REC[t]) if lab == "B0a8" else
                            (RUN_DIR, ("e1_%s" % t) if lab.startswith("X3E1") else ("core_%s" % t) if lab.endswith("@0.05") else ("a_%s" % t)))
        rec = GV.load_outputs(src_dir, src_tag)
        rlab = lab.split("@")[0] if lab.endswith("@0.05") else lab
        rec["eps"] = [dict(o, arm=lab) if o["arm"] == rlab else o for o in rec["eps"]]
        for o in mine["eps"] + rec["eps"]:
            o.pop("margin_rule", None)
            o.pop("cov_dir", None)
        r = GV.v0(rec, mine, [lab])[lab]
        parts = dict(np.load(os.path.join(RUN_DIR, "parts_%s.npz" % tag)))
        v2 = GV.v2(rec, mine["eps"], parts, [lab], GV.pop_masks())[lab]
        res[lab] = {"equal_to_earlier_run": r["equal"], "earlier_run": src_tag, "partition_sums_equal_counts": v2["equal"]}
        del rec
    ok = all(v["equal_to_earlier_run"] and v["partition_sums_equal_counts"] for v in res.values())
    C.jdump(os.path.join(OUT, "x3_a3_ii_check_%s_v01.json" % t), dict(stamp(), tracker=t, by_arm=res, passed=ok))
    print("check ii", t, ok)
    if not ok:
        raise SystemExit("X3 STOP (A3 ii): a partition re-run differs from its earlier run")


def part_ii_iv(t, level_iv=1 - 0.05 / 7):
    import x3_analysis_b_v01 as AB
    import x3_run_v01 as RR
    sb, _ = C.x3_seeds(t, "b")
    eb = SC.entered([json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_core_%s.jsonl" % t))])
    pb = dict(np.load(os.path.join(RUN_DIR, "parts_core_%s.npz" % t)))
    kw = SC.keys_W(eb, C.B_X3, sb)
    arms, ch = {}, None
    if t != "tab":
        eps = SC.entered([json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_a3p_%s.jsonl" % t))])
        assert sorted({(o["scene"], o["delay_kf"]) for o in eps}) == kw["keys"]
        parts = dict(np.load(os.path.join(RUN_DIR, "parts_a3p_%s.npz" % t)))
        folds = json.load(open(C.FOLDS))["fold_of_log"]
        fold_of_key = np.array([int(folds[k[0]]) for k in kw["keys"]])
        am = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")))["by_tracker"][t]
        acc = {lab: AB.acc_by_key(eps, parts, lab, kw["keys"]) for lab in sorted({o["arm"] for o in eps})}
        arms = dict(acc)
        ch = {f: c["point"] for f, c in am["families"]["B6"]["choice_by_fold"].items()}
        comp = np.zeros_like(next(iter(acc.values())))
        for f, p in ch.items():
            m = fold_of_key == int(f)
            comp[m] = acc[p][m]
        arms["A_B6_composite"] = comp
        if t == "t1":
            arms["RETUNED_HK1 (B0a8 in every fold)"] = acc["B0a8"]
    barms = {a: AB.acc_by_key(eb, pb, a, kw["keys"]) for a in AB.ARMS[t]}
    b_json = json.load(open(os.path.join(C.OUT, "b_partitions", "x3_b_partitions_v01.json")))["by_tracker"][t]["arms"]

    def screen_all(acc6, level):
        out = {}
        for pi, pn in enumerate(RR.PARTS):
            labels = RR.BIN_LABELS[pn]
            nb = len(labels)
            names = ["%s|%s" % (labels[b], ax) for b in range(nb) for ax in ("long", "lat")]
            out[pn] = {}
            for p, c4 in AB.POP_C4.items():
                sub = acc6[:, list(c4), pi, :nb, :, :].sum(1)
                N = sub[..., 0].reshape(len(kw["keys"]), nb * 2)
                X = sub[..., 1].reshape(len(kw["keys"]), nb * 2)
                r = SC.partition_screen(N, X, kw, names, level=level)
                out[pn][p] = {"flagged": r["flagged"], "evaluable": len(r["evaluable"]), "largest": r.get("largest")}
        return out

    ii = {}
    for a, acc6 in arms.items():
        ii[a] = screen_all(acc6, 0.95)
    mflags = {pn: {p: b_json["Mstar"][pn][p]["flagged"] for p in AB.POP_C4} for pn in RR.PARTS}
    iv = {}
    for a, acc6 in list(barms.items()) + list(arms.items()):
        s95 = ii[a] if a in ii else {pn: {p: {"flagged": b_json[a][pn][p]["flagged"]} for p in AB.POP_C4} for pn in RR.PARTS}
        sbf = screen_all(acc6, level_iv)
        iv[a] = {lv: {p: {"P1_P7": sum(len(s_[pn][p]["flagged"]) for pn in RR.PARTS if pn != "P0_distance_range"),
                          "P0": len(s_["P0_distance_range"][p]["flagged"])} for p in AB.POP_C4}
                 for lv, s_ in (("0.95", s95), ("%.6f" % level_iv, sbf))}
        iv[a]["cells_at_corrected_level"] = {pn: {p: sbf[pn][p]["flagged"] for p in AB.POP_C4} for pn in RR.PARTS}
    return {"tracker": t, "seed_bootstrap": sb, "B": C.B_X3, "ii": ii, "Mstar_flags_b": mflags, "iv": iv, "level_iv": level_iv,
            "composite_choice_B6": ch}


def md_ii_iv(r):
    import x3_run_v01 as RR
    L = ["# X3 A3 (ii) partition screens of the matched arms and (iv) multiplicity across partitions", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "(ii): analysis (b)'s screen (same bins, populations, flag rule at 0.95 over each partition's evaluable cells, seeds [20261201, i, 2], "
         "B = 4000) on re-runs with partition counts (x3_run_v02 --parts; each checked equal to its earlier run and its partition sums equal "
         "to its counts). RETUNED-HK1 (T1) = B0a8 in every fold, rebuilt with the X3 runner (no partition counts of record exist). "
         "(iv): the same flags at the per-partition one-sided level 1 - 0.05/7 = %.6f." % r["level_iv"], ""]
    for t, x in r["by_tracker"].items():
        L += ["## %s (ii): flagged cells, P_rel / P_near / P_ip ('-' none)" % t.upper(), "",
              "| arm | " + " | ".join(p.split("_", 1)[0] for p in RR.PARTS) + " |", "|---|" + "---|" * len(RR.PARTS)]
        rows = [("M* (b)", {pn: {p: {"flagged": x["Mstar_flags_b"][pn][p]} for p in x["Mstar_flags_b"][pn]} for pn in RR.PARTS})] + list(x["ii"].items())
        for a, s_ in rows:
            L.append("| %s | %s |" % (a, " | ".join(" / ".join((", ".join(s_[pn][p]["flagged"]) or "-") for p in ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath"))
                                                   for pn in RR.PARTS)))
        L += ["", "## %s (iv): flagged-cell counts, P1-P7 total (P0) per population, at 0.95 and at 1 - 0.05/7" % t.upper(), "",
              "| arm | P_rel 0.95 | P_rel corr. | P_near 0.95 | P_near corr. | P_ip 0.95 | P_ip corr. |", "|---|---|---|---|---|---|---|"]
        for a, v in x["iv"].items():
            lv = [k for k in v if k not in ("0.95", "cells_at_corrected_level")][0]
            cell = lambda q: "%d (%d)" % (q["P1_P7"], q["P0"])  # noqa: E731
            L.append("| %s | %s | %s | %s | %s | %s | %s |" % (a, cell(v["0.95"]["PD7_primary"]), cell(v[lv]["PD7_primary"]), cell(v["0.95"]["SD1_7_gap_le_5m"]),
                                                          cell(v[lv]["SD1_7_gap_le_5m"]), cell(v["0.95"]["PD_inpath"]), cell(v[lv]["PD_inpath"])))
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- (iii)
def part_iii(t):
    import k8_joint_fit_v02 as J
    rec = json.load(open(C.FITS_REC[t]))
    items = [x["file"] for x in rec["items"]]
    it, names, _ = J.load_items(items)
    names = list(names)
    folds = json.load(open(C.FOLDS))["fold_of_log"]
    fold_unit = np.array([int(folds[n]) for n in names])
    U = it["D"] / it["sd"]
    ip = it["inpath"].astype(int)
    col = it["l0"] + 96 * ip
    thr = np.empty(len(U))
    src = np.empty(len(U), int)
    STEPS = ["h0p5s", "h1s", "h1p5s", "h2s"]
    f_item = fold_unit[it["s"]]
    for f in range(5):
        for h in range(4):
            m = (f_item == f) & (it["h"] == h)
            fd = rec["fits"][str(f)][STEPS[h]]
            thr[m] = np.asarray(fd["Mstar_ip"], float)[col[m]]
            src[m] = np.asarray(fd["Mstar_ip_src"], int)[col[m]]
    exc = (U > thr).astype(float)
    own = src == 0
    kw = kw_for(t, names)
    assert [k[0] for k in kw["keys"]] == names
    n_keys = len(names)
    Nc = np.zeros((n_keys, 192))
    Xc = np.zeros((n_keys, 192))
    np.add.at(Nc, (it["s"][own], col[own]), 1.0)
    np.add.at(Xc, (it["s"][own], col[own]), exc[own])
    one = np.ones((1, n_keys))
    ev = A.evaluable(Nc, kw["scene_of_ep"], kw["log_of_ep"])
    fam = np.flatnonzero(ev)
    est, boot = A.rates(Nc, Xc, one)[0], A.rates(Nc, Xc, kw["W"])
    lb, ub, se, sig, q = A.flag(est, boot, fam, 0.95)
    import m_lib_v04 as M
    cells = {}
    for i, j in enumerate(fam):
        cells["%s|%s" % (M.l0_name(int(j % 96)), "inpath" if j >= 96 else "not_inpath")] = {
            "E": float(est[j]), "lb_sim": float(lb[i]), "ub_sim": float(ub[i]), "flagged": bool(sig[i]), "logs": int((Nc[:, j] > 0).sum()),
            "items": int(Nc[:, j].sum())}

    def pooled(mask):
        N = np.bincount(it["s"][mask], minlength=n_keys)[:, None].astype(float)
        X_ = np.bincount(it["s"][mask], weights=exc[mask], minlength=n_keys)[:, None]
        if N.sum() == 0:
            return None
        b = A.rates(N, X_, kw["W"])[:, 0]
        return {"E_log_weighted": float(A.rates(N, X_, one)[0][0]), "ci95": [float(np.nanquantile(b, 0.025)), float(np.nanquantile(b, 0.975))],
                "items": int(mask.sum()), "item_rate": float(exc[mask].mean())}
    out = {"tracker": t, "seed_bootstrap": seeds_a3(t), "B": C.B_X3, "items": int(len(U)),
           "own_threshold_strata_evaluable": int(len(fam)), "flagged": [c for c, v in cells.items() if v["flagged"]], "sup_t_q": float(q),
           "max_E_cell": max(cells.items(), key=lambda kv: kv[1]["E"])[0] if cells else None, "cells": cells,
           "fallback_share_items": float(np.mean(~own)), "fallback_share_by_level": {str(l_): float(np.mean(src == l_)) for l_ in (0, 1, 2, 3)},
           "pooled_own": pooled(own), "pooled_fallback": pooled(~own), "pooled_all": pooled(np.ones(len(U), bool)),
           "pooled_own_by_inpath": {str(p): pooled(own & (ip == p)) for p in (0, 1)},
           "pooled_fallback_by_level": {str(l_): pooled(src == l_) for l_ in (1, 2, 3)}}
    return out


def md_iii(r):
    L = ["# X3 A3 (iii): M*'s cross-fitted exceedance on its own calibration items", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "Items of record (every separating axis at the reference pose); each held-out fold's fits_within thresholds applied to that fold's "
         "items, exceedance U = D / sd > c. Strata: own-threshold L0 stratum (the item's threshold is its stratum's own fit) x in-path part, "
         "check times pooled; log-weighted rate; one-sided simultaneous sup-t at 0.95 over the evaluable strata (>= 39 logs); B = 4000, seed "
         "[20261201, i, 9]. A consistency check of the theory on the data, not a test of the planner-facing claim.", ""]
    for t, x in r["by_tracker"].items():
        po, pf = x["pooled_own"], x["pooled_fallback"]
        L += ["## %s" % t.upper(), "",
              "- items %d; evaluable own-threshold strata %d; flagged %d: %s" % (x["items"], x["own_threshold_strata_evaluable"], len(x["flagged"]), ", ".join(x["flagged"]) or "none"),
              "- pooled own-threshold items: %.4f [%.4f, %.4f] (%d items); fallback items: share %.3f, pooled %.4f [%.4f, %.4f]" % (
                  po["E_log_weighted"], po["ci95"][0], po["ci95"][1], po["items"], x["fallback_share_items"], pf["E_log_weighted"], pf["ci95"][0], pf["ci95"][1]),
              "- fallback by level (share of items): %s; pooled rate by level: %s" % (
                  json.dumps({k: round(v, 3) for k, v in x["fallback_share_by_level"].items()}),
                  json.dumps({k: (round(v["E_log_weighted"], 4) if v else None) for k, v in x["pooled_fallback_by_level"].items()})),
              "- largest stratum estimate: %s %.4f (UB %.4f)" % (x["max_E_cell"], x["cells"][x["max_E_cell"]]["E"], x["cells"][x["max_E_cell"]]["ub_sim"]), ""]
    return "\n".join(L)


# ---------------------------------------------------------------- (v) the sweep at M*'s V2
def sweep():
    out = {}
    for t in ("t1", "t3"):
        rows = {r["arm"]: r for r in csv.DictReader(open(os.path.join(CSV_DIR, "k8_within_lt3d_%s_decide_arms.csv" % t)))}
        v_m = float(rows["Mstar"]["V2_PD7_E"])
        pts = sorted((float(rows[a]["V2_PD7_E"]), float(rows[a]["infeasible_rate"]), a) for a in S.SWEEP_ARMS)
        res = None
        for (v0, i0, a0), (v1, i1, a1) in zip(pts, pts[1:]):
            if v0 <= v_m <= v1 and v1 > v0:
                w = (v_m - v0) / (v1 - v0)
                res = {"infeasible_at_Mstar_V2": i0 + w * (i1 - i0), "bracket": [[a0, v0, i0], [a1, v1, i1]], "weight": w}
                break
        out[t] = {"Mstar_V2_PD7": v_m, "Mstar_infeasible": float(rows["Mstar"]["infeasible_rate"]), "interpolation": res,
                  "sweep_points_in_V2_order": [[a, v, i] for v, i, a in pts], "source": "c1_analysis_csv_r1 (record)"}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["i", "spec", "check_ii", "ii", "iii", "sweep"])
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3"])
    a = ap.parse_args(argv)
    C.assert_run_log("A3 %s start" % a.cmd)
    SC.setup()
    t0 = time.time()
    if a.cmd == "spec":
        write_spec()
    elif a.cmd == "check_ii":
        for t in a.trackers:
            check_ii(t)
    elif a.cmd == "i":
        r = dict(stamp(), part="(i)", by_tracker={})
        for t in a.trackers:
            r["by_tracker"][t] = part_i(t)
            print("(i) %s done; check %s" % (t, r["by_tracker"][t]["check_vs_record_csv"]), flush=True)
        r["seconds"] = round(time.time() - t0, 1)
        C.jdump(os.path.join(OUT, "x3_a3_i_infeasible_cost_v01.json"), r)
        C.wtext(os.path.join(OUT, "x3_a3_i_infeasible_cost_v01.md"), md_i(r))
    elif a.cmd == "ii":
        r = dict(stamp(), part="(ii) and (iv)", by_tracker={})
        for t in a.trackers:
            r["by_tracker"][t] = part_ii_iv(t)
            print("(ii, iv) %s done" % t, flush=True)
        r["by_tracker"]["tab"] = part_ii_iv("tab")
        r["level_iv"] = 1 - 0.05 / 7
        r["seconds"] = round(time.time() - t0, 1)
        C.jdump(os.path.join(OUT, "x3_a3_ii_iv_partitions_v01.json"), r)
        C.wtext(os.path.join(OUT, "x3_a3_ii_iv_partitions_v01.md"), md_ii_iv(r))
    elif a.cmd == "iii":
        r = dict(stamp(), part="(iii)", by_tracker={})
        for t in a.trackers:
            r["by_tracker"][t] = part_iii(t)
            print("(iii) %s done" % t, flush=True)
        r["seconds"] = round(time.time() - t0, 1)
        C.jdump(os.path.join(OUT, "x3_a3_iii_own_items_v01.json"), r)
        C.wtext(os.path.join(OUT, "x3_a3_iii_own_items_v01.md"), md_iii(r))
    elif a.cmd == "sweep":
        r = dict(stamp(), part="B0-sweep infeasible rate at M*'s V2 (linear interpolation in V2 order)", by_tracker=sweep())
        C.jdump(os.path.join(OUT, "x3_a3_sweep_at_Mstar_V2_v01.json"), r)
        L = ["# X3 A3: the B0 sweep at M*'s V2", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
             "Record CSV values (P_rel V2 and infeasible rate per sweep point), sorted by V2; linear interpolation at M*'s V2.", ""]
        for t, x in r["by_tracker"].items():
            ip_ = x["interpolation"]
            L.append("- %s: M* V2 %.4f, M* infeasible %.4f; sweep infeasible at that V2 = **%.4f** (between %s V2 %.4f / %.4f and %s V2 %.4f / %.4f)" % (
                t.upper(), x["Mstar_V2_PD7"], x["Mstar_infeasible"], ip_["infeasible_at_Mstar_V2"], ip_["bracket"][0][0], ip_["bracket"][0][1],
                ip_["bracket"][0][2], ip_["bracket"][1][0], ip_["bracket"][1][1], ip_["bracket"][1][2]))
        C.wtext(os.path.join(OUT, "x3_a3_sweep_at_Mstar_V2_v01.md"), "\n".join(L) + "\n")
        print(json.dumps({t: x["interpolation"]["infeasible_at_Mstar_V2"] for t, x in r["by_tracker"].items()}))
    C.assert_run_log("A3 %s end" % a.cmd)


if __name__ == "__main__":
    main()
