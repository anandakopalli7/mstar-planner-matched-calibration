#!/usr/bin/env python3
"""X3 analysis (h), the AB3DMOT diagnosis from the outputs of record (x3-stats, v01, 7 Nov 2026). Plan 2(h); referee concern M7.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

AB3DMOT (tab) is descriptive in the registered test; T1 and T3 are given beside it for comparison. Four parts, as the plan lists them:
  (h1) which cells and populations are flagged for M* on tab: the record's validity entry (k8 validity_by_arm.Mstar; c1 status) and
       the record's per-cell table (k8_within_lt3d_<t>_decide_cells.csv: E, simultaneous 0.95 bounds, records, logs, fallback share),
       with every M* cell whose point estimate exceeds delta;
  (h2) the fallback shares of the fits: the share of M*'s threshold entries (fold x calibrated step x L0 stratum x in-path) whose
       Mstar_ip_src > 0 (a coarser level), recomputed from fits_within_<t>.json and checked against the record's
       fallback_strata_fits_entries; by fallback level; and the record's record-weighted A13 shares per population;
  (h3) the share of relied records from low-score tracks: each record of the items (items_c1b_<t>_own375.npz: rec_s, rec_row) is
       joined to its track row in the frozen stage-B cache (30_DATA/av2_cache_stageB_c1b_<t>_own375/<scene>.npz) and binned by
       tr_score with plan P4's bins [0.4, 0.5), [0.5, 0.7), [0.7, 0.85), >= 0.85 (scores below 0.4 kept as their own bin if any);
       join checks: tr_k[rec_row] = rec_k and tr_inst[rec_row] = rec_inst for every record. The relied subset is the records whose
       reference-relied item is in the items (key scene, keyframe, step, pair);
  (h4) the share of enforced pairs whose track has no ground-truth match (false-positive tracks), counted directly by
       x3_stats_h_fpcount_v01.py (the items' own enumeration repeated over every track; it reproduces the items summaries exactly on
       the GT-matched tracks). The items summaries cannot give it: their enumeration skips unmatched tracks, so pairs_enforced -
       pairs_with_gt counts GT-matched tracks without a usable annotation at k + h (reported as such). Context: the share of cache
       track rows without a GT match (tr_inst < 0) by score bin.
Light step (no bootstrap). Run: python -B x3_stats_h_v01.py --out-dir <60_RESULTS/x3_explore_v01/h_ab3dmot>
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

TRACKERS = ("t1", "t3", "tab")
P4_EDGES = [0.4, 0.5, 0.7, 0.85]
P4_LABELS = ["<0.4", "[0.4,0.5)", "[0.5,0.7)", "[0.7,0.85)", ">=0.85"]
STEPS_CAL = ["h0p5s", "h1s", "h1p5s", "h2s"]      # k8_analyse_v04.STEPS (the calibrated steps, <= 2 s)


def score_bin(s):
    s = np.asarray(s, np.float64)
    b = np.full(s.shape, -1, np.int64)
    b[s < 0.4] = 0
    b[(s >= 0.4) & (s < 0.5)] = 1
    b[(s >= 0.5) & (s < 0.7)] = 2
    b[(s >= 0.7) & (s < 0.85)] = 3
    b[s >= 0.85] = 4
    return b


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ (h1)
def part_h1(t, rec):
    v = rec["validity"]["Mstar"]
    st = rec["status"]["Mstar"]
    cells = [r for r in read_csv(os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_cells.csv" % t)) if r["arm"] == "Mstar"]
    out = {"status": {"valid": st["valid"], "shown_above": st["shown_above"], "floor_only": st["floor_only"]}, "pops": {}}
    for pop in C.POPS:
        p = v["pops"][pop]
        pooled = p.get("pooled") or {}
        sp = st["pops"][pop]
        rows = [r for r in cells if r["population"] == pop]
        above = sorted([{"cell": r["cell"], "E": fnum(r["E"]), "lb_sim_0.95": fnum(r["lb_sim"]), "ub_sim_0.95": fnum(r["ub_sim"]),
                         "evaluable": r["evaluable"] == "True", "flag": r["sig_above"] == "True", "records": fnum(r["records"]),
                         "exceed": fnum(r["exceed"]), "E_record_pooled": fnum(r["E_rec"]), "logs": fnum(r["scenes"]),
                         "fallback_share": fnum(r["fallback_share_Mstar_record_weighted"]),
                         "coarser_bound_only": r["coarser_bound_only"] == "True"}
                        for r in rows if fnum(r["E"]) is not None and fnum(r["E"]) > C.DELTA], key=lambda x: -x["E"])
        tot = sum(fnum(r["records"]) or 0 for r in rows)
        out["pops"][pop] = {"NoFlag": sp["NoFlag"], "FamFlag": sp["FamFlag"], "NoFlag_pool": sp["NoFlag_pool"], "Floor": sp["Floor"],
                            "HK1c": sp["HK1c"], "valid": sp["valid"], "shown_above": sp["shown_above"],
                            "flagged_cells": list(p.get("flagged") or []), "family_flagged": list(p.get("family_flagged") or []),
                            "evaluable": p.get("evaluable"), "family_size": p.get("family_size"),
                            "pooled": {"E": pooled.get("E"), "lb_0.95": pooled.get("lb"), "ub_0.995": pooled.get("ub"),
                                       "flagged": pooled.get("flagged")},
                            "cells_above_delta": above,
                            "records_in_cells_above_delta_share": (sum(a["records"] for a in above) / tot) if tot else None,
                            "records": tot}
    return out


# ------------------------------------------------------------------ (h2)
def part_h2(t, rec):
    with open(C.fits_path(t), encoding="utf-8") as f:
        fits = json.load(f)
    src = np.array([[fits["fits"][fo][st]["Mstar_ip_src"] for st in STEPS_CAL] for fo in sorted(fits["fits"], key=int)], int)
    # (folds, 4, 192): index l0 + 96 * in-path
    share = float((src > 0).mean())
    levels = {str(lv): float((src == lv).mean()) for lv in sorted(set(src.ravel().tolist()))}
    by_ip = {"not_in_path": float((src[:, :, :96] > 0).mean()), "in_path": float((src[:, :, 96:] > 0).mean())}
    by_step = {st: float((src[:, i] > 0).mean()) for i, st in enumerate(STEPS_CAL)}
    by_fold = {fo: float((src[k] > 0).mean()) for k, fo in enumerate(sorted(fits["fits"], key=int))}
    fb_rec = rec.get("fallback_strata_fits_entries") or {}
    rec_l0 = np.asarray(fb_rec.get("by_l0_inpath") or [], float)
    mine_l0 = (src > 0).reshape(-1, src.shape[2]).mean(0)
    chk = float(np.max(np.abs(rec_l0 - mine_l0))) if rec_l0.size == mine_l0.size else None
    a13 = (rec.get("A13_fallback_record_weighted") or {}).get("by_population") or {}
    a13p = {p: (a13.get(p) or {}).get("pooled") for p in list(C.POPS) + ["NIP_not_in_path"]}
    coarse = {p: sorted(c for c, v in ((a13.get(p) or {}).get("by_cell") or {}).items() if v.get("coarser_bound_only"))
              for p in C.POPS}
    del fits
    return {"entries": int(src.shape[0] * src.shape[1]), "strata_per_entry": int(src.shape[2]),
            "share_coarser_entries": share, "share_by_level": levels, "by_in_path": by_ip, "by_step": by_step, "by_fold": by_fold,
            "check_vs_record_by_l0_inpath_max_abs_diff": chk, "record_weighted_A13_pooled": a13p,
            "record_weighted_coarser_bound_only_cells": coarse}


# ------------------------------------------------------------------ (h3), (h4)
def part_h34(t, log, out_dir):
    items = np.load(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375.npz" % t))
    rs, rr, rk, rh, rp = (items[k].astype(np.int64) for k in ("rec_s", "rec_row", "rec_k", "rec_h", "rec_pair"))
    rinst = items["rec_inst"].astype(np.int64)
    rinp = items["rec_inpath"].astype(bool)
    scenes = [str(x) for x in items["scene_names"]]
    assert rp.max() < 65536 and rk.max() < 64 and rh.max() < 16 and items["item_pair"].max() < 65536, "key encoding range"
    isel = items["item_ref_relied"].astype(bool)
    ikey = ((items["item_s"].astype(np.int64)[isel] * 64 + items["item_k"].astype(np.int64)[isel]) * 16
            + items["item_h"].astype(np.int64)[isel]) * 65536 + items["item_pair"].astype(np.int64)[isel]
    del items
    rkey = ((rs * 64 + rk) * 16 + rh) * 65536 + rp
    relied = np.isin(rkey, np.unique(ikey))
    del ikey, rkey
    with open(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375_summary.json" % t), encoding="utf-8") as f:
        summ = json.load(f)
    cache = os.path.join(C.CACHE_DIR, "av2_cache_stageB_c1b_%s_own375" % t)
    score = np.full(len(rs), np.nan)
    bad_k = bad_inst = 0
    tr_bins = np.zeros(5)
    tr_fp = np.zeros(5)
    t0 = time.time()
    order = np.argsort(rs, kind="stable")
    bounds = np.searchsorted(rs[order], np.arange(len(scenes) + 1))
    for si, name in enumerate(scenes):
        z = np.load(os.path.join(cache, name + ".npz"))
        sc, tk, ti = z["tr_score"], z["tr_k"], z["tr_inst"]
        del z
        b = score_bin(sc)
        tr_bins += np.bincount(b, minlength=5)
        tr_fp += np.bincount(b, weights=(ti < 0).astype(float), minlength=5)
        idx = order[bounds[si]:bounds[si + 1]]
        if len(idx):
            rows = rr[idx]
            score[idx] = sc[rows]
            bad_k += int(np.sum(tk[rows] != rk[idx]))
            bad_inst += int(np.sum(ti[rows] != rinst[idx]))
        if si % 75 == 74:
            log("%s cache join %d/%d (%.0f s)" % (t, si + 1, len(scenes), time.time() - t0))
    rb = score_bin(score)

    def shares(mask):
        c = np.bincount(rb[mask], minlength=5).astype(float)
        return {"records": int(mask.sum()), "share_by_bin": dict(zip(P4_LABELS, (c / c.sum()).tolist())),
                "share_below_0.5": float(c[:2].sum() / c.sum()), "share_below_0.7": float(c[:3].sum() / c.sum())}

    tot = summ.get("totals") or {}
    pe, pg = tot.get("pairs_enforced"), tot.get("pairs_with_gt")
    with open(os.path.join(out_dir, "x3_h_fpcount_%s_v01.json" % t), encoding="utf-8") as f:
        fp = json.load(f)
    assert fp["validated"], "direct count does not reproduce the items summary"
    out = {"join": {"records": int(len(rs)), "keyframe_mismatches": bad_k, "instance_mismatches": bad_inst,
                    "records_without_score": int(np.isnan(score).sum()), "relied_records": int(relied.sum())},
           "relied_records_by_score": shares(relied), "all_records_by_score": shares(np.ones(len(rs), bool)),
           "relied_in_path_by_score": shares(relied & rinp),
           "enforced_pairs": {"decisions": fp["decisions"], "pairs_enforced_all_tracks": fp["pairs_enforced_all_tracks"],
                              "pairs_enforced_no_gt_track": fp["pairs_enforced_no_gt_track"],
                              "share_without_gt_match": fp["share_enforced_without_gt_match"],
                              "per_decision_without_gt": fp["per_decision_enforced_without_gt_match"],
                              "decisions_with_an_enforced_no_gt_track_share": fp["decisions_with_an_enforced_no_gt_track_share"],
                              "share_without_gt_by_score_bin": fp["share_without_gt_by_score_bin"],
                              "enforced_by_score_bin": fp["enforced_by_score_bin"],
                              "direct_count_file": "x3_h_fpcount_%s_v01.json" % t,
                              "direct_count_sha256": C.sha256(os.path.join(out_dir, "x3_h_fpcount_%s_v01.json" % t)),
                              "validation_against_items_summary": fp["validation_against_items_summary"]},
           "items_summary_gt_matched_pairs": {"pairs_enforced": pe, "pairs_with_gt": pg,
                                              "share_without_usable_annotation": (1 - pg / pe) if pe else None,
                                              "note": "GT-matched tracks only (the items skip unmatched tracks): the complement is a "
                                                      "GT-matched track without an annotation (>= 1 point, not in a rack) at k + h"},
           "cache_track_rows": {"rows_by_score_bin": dict(zip(P4_LABELS, tr_bins.tolist())),
                                "share_by_score_bin": dict(zip(P4_LABELS, (tr_bins / tr_bins.sum()).tolist())),
                                "share_without_gt_by_bin": dict(zip(P4_LABELS, [float(a / b) if b else None for a, b in zip(tr_fp, tr_bins)])),
                                "share_without_gt_all": float(tr_fp.sum() / tr_bins.sum()),
                                "share_of_no_gt_rows_below_0.5": float(tr_fp[:2].sum() / tr_fp.sum()) if tr_fp.sum() else None},
           "items_summary_sha256": C.sha256(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375_summary.json" % t)),
           "items_sha256": C.sha256(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375.npz" % t))}
    return out


def write_md(path, out):
    f3 = lambda v: "-" if v is None else "%.3f" % v  # noqa: E731
    f4 = lambda v: "-" if v is None else "%.4f" % v  # noqa: E731
    R = out["trackers"]
    lines = ["# X3 (h): the AB3DMOT diagnosis (v01)", "", "**%s**" % C.STAMP, "",
             "Plan 2(h) (sha256 %s...); referee concern M7. Outputs of record only (within_lt3d, decision mode); AB3DMOT (tab) is "
             "descriptive in the registered test; T1 and T3 are shown for comparison. JSON: `x3_h_ab3dmot_v01.json`." % C.PLAN_SHA[:8], "",
             "## (h1) M*'s screen by population", "",
             "| Tracker | Population | Valid | Shown above | Flagged cells | Family flagged | Pooled E | Pooled LB 0.95 | Pooled flag | HK1c UB 0.995 | Cells with E > 0.05 (records share) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in TRACKERS:
        h = R[t]["h1"]
        for p in C.POPS:
            x = h["pops"][p]
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d (%s) |" % (
                t, p, x["valid"], x["shown_above"], ", ".join(x["flagged_cells"]) or "-", ", ".join(x["family_flagged"]) or "-",
                f4(x["pooled"]["E"]), f4(x["pooled"]["lb_0.95"]), x["pooled"]["flagged"], f4(x["pooled"]["ub_0.995"]),
                len(x["cells_above_delta"]), f3(x["records_in_cells_above_delta_share"])))
    lines += ["", "### tab: M*'s cells with a point estimate above 0.05 (record's per-cell table; simultaneous 0.95 bounds)", "",
              "| Population | Cell | E | LB | UB | Flag | Records | Logs | Fallback share | Coarser bound only |", "|---|---|---|---|---|---|---|---|---|---|"]
    for p in C.POPS:
        for a in R["tab"]["h1"]["pops"][p]["cells_above_delta"]:
            lines.append("| %s | %s | %s | %s | %s | %s | %d | %d | %s | %s |" % (
                p, a["cell"], f4(a["E"]), f4(a["lb_sim_0.95"]), f4(a["ub_sim_0.95"]), a["flag"], a["records"] or 0, a["logs"] or 0,
                f3(a["fallback_share"]), a["coarser_bound_only"]))
    lines += ["", "## (h2) Fallback shares of M*'s fits (threshold entries from a coarser level; calibrated steps <= 2 s)", "",
              "| Tracker | Entries | Coarser share | By level | Not in path / in path | Record-weighted (A13) P_rel / P_near / P_ip | Check vs record |",
              "|---|---|---|---|---|---|---|"]
    for t in TRACKERS:
        h = R[t]["h2"]
        a = h["record_weighted_A13_pooled"]
        lines.append("| %s | %d x %d | %s | %s | %s / %s | %s / %s / %s | %s |" % (
            t, h["entries"], h["strata_per_entry"], f3(h["share_coarser_entries"]),
            ", ".join("%s: %.3f" % kv for kv in h["share_by_level"].items()), f3(h["by_in_path"]["not_in_path"]), f3(h["by_in_path"]["in_path"]),
            *[f4((a.get(p) or {}).get("share")) for p in C.POPS], "%.1e" % h["check_vs_record_by_l0_inpath_max_abs_diff"]
            if h["check_vs_record_by_l0_inpath_max_abs_diff"] is not None else "-"))
    lines += ["", "## (h3) Relied records by track score (plan P4 bins)", "",
              "| Tracker | Relied records | " + " | ".join(P4_LABELS) + " | below 0.5 | below 0.7 | Join mismatches (k / inst) |",
              "|---|---|" + "---|" * len(P4_LABELS) + "---|---|---|"]
    for t in TRACKERS:
        h = R[t]["h34"]
        s = h["relied_records_by_score"]
        lines.append("| %s | %d | %s | %s | %s | %d / %d |" % (t, s["records"], " | ".join(f3(s["share_by_bin"][b]) for b in P4_LABELS),
                                                         f3(s["share_below_0.5"]), f3(s["share_below_0.7"]),
                                                         h["join"]["keyframe_mismatches"], h["join"]["instance_mismatches"]))
    lines += ["", "In-path relied records only:", "", "| Tracker | Records | " + " | ".join(P4_LABELS) + " |", "|---|---|" + "---|" * len(P4_LABELS)]
    for t in TRACKERS:
        s = R[t]["h34"]["relied_in_path_by_score"]
        lines.append("| %s | %d | %s |" % (t, s["records"], " | ".join(f3(s["share_by_bin"][b]) for b in P4_LABELS)))
    lines += ["", "## (h4) Enforced pairs whose track has no ground-truth match", "",
              "Counted directly (items' enumeration over every track; validated: reproduces the items summaries' decisions, "
              "pairs_considered, pairs_enforced and pairs_with_gt exactly on the GT-matched tracks). Pairs = (track, calibrated step) at "
              "the 11288 decision states of the reference run.", "",
              "| Tracker | Enforced pairs (all tracks) | Without GT match | Share | Per decision | Decisions with >= 1 | " +
              " | ".join("share in %s" % b for b in P4_LABELS[1:]) + " | Items: GT-matched pairs without usable annotation at k+h |",
              "|---|---|---|---|---|---|" + "---|" * (len(P4_LABELS) - 1) + "---|"]
    for t in TRACKERS:
        e = R[t]["h34"]["enforced_pairs"]
        ii = R[t]["h34"]["items_summary_gt_matched_pairs"]
        lines.append("| %s | %d | %d | %s | %s | %s | %s | %s |" % (
            t, e["pairs_enforced_all_tracks"], e["pairs_enforced_no_gt_track"], f4(e["share_without_gt_match"]),
            f3(e["per_decision_without_gt"]), f3(e["decisions_with_an_enforced_no_gt_track_share"]),
            " | ".join(f3(e["share_without_gt_by_score_bin"][b]) for b in P4_LABELS[1:]), f4(ii["share_without_usable_annotation"])))
    lines += ["", "The cache's in-path flag is set only for GT-matched tracks (verified on the caches: no unmatched track row is flagged "
              "in path), so false-positive tracks cannot be split by in-path."]
    lines += ["", "Track rows in the cache (every track at every keyframe, not only enforced pairs): share of rows and share without a GT "
              "match, by score bin.", "", "| Tracker | " + " | ".join("%s rows / no GT" % b for b in P4_LABELS) + " |",
              "|---|" + "---|" * len(P4_LABELS)]
    for t in TRACKERS:
        c = R[t]["h34"]["cache_track_rows"]
        lines.append("| %s | %s |" % (t, " | ".join("%s / %s" % (f3(c["share_by_score_bin"][b]), f3(c["share_without_gt_by_bin"][b]))
                                                     for b in P4_LABELS)))
    lines += ["", "## Reading", ""] + ["- " + x for x in out["reading"]]
    lines += ["", "## Choices", ""] + ["- " + c for c in out["choices"]]
    lines += ["", "Code: `50_CODE/x3/x3_stats_h_v01.py` (sha256 in the JSON). Nothing here changes a status or table of record.", ""]
    C.text_new(path, "\n".join(lines))


CHOICES = [
    "(h1) reads the record's own validity entry and per-cell table; nothing is recomputed (the per-cell bounds are the record's "
    "simultaneous 0.95 bounds over the evaluable cells, the flag rule of the screen for M*).",
    "(h2) 'fallback share' = share of M*'s in-path-split threshold entries (Mstar_ip_src > 0) over folds x the 4 calibrated steps x "
    "192 strata, the record's fallback_strata_fits_entries definition (recomputed and checked); the record-weighted A13 share is read "
    "from the record.",
    "(h3) 'relied records' = the items' records whose reference-relied item is present (joined on scene, keyframe, step, pair); the "
    "items are the arm-independent reference-relied records of every enforced pair with a GT match, so they are the certificate's "
    "outcome set. Scores come from the cache row rec_row of the record's scene; the join is checked on keyframe and GT instance.",
    "(h4) the items summaries' pairs_enforced - pairs_with_gt is NOT the false-positive share (the items enumerate GT-matched tracks "
    "only); the false-positive share is counted directly by x3_stats_h_fpcount_v01.py with the items' own enumeration (k6_sim_v02's "
    "functions, read-only) over every track, validated exactly against the summaries on the GT-matched tracks. The cache-wide share "
    "of track rows without GT is added as context (all tracks, not only enforced).",
    "The exceedance of M* by score bin (partition P4 of analysis (b)) is not computed here: it needs M*'s per-record margins, which (b)'s "
    "partition-tagged re-run provides.",
]


def reading(R):
    out = []
    h = R["tab"]["h1"]
    pops_flag = [p for p in C.POPS if h["pops"][p]["shown_above"]]
    out.append("tab: M* is %s; shown above delta in %s (flagged cells: %s; family flagged: %s; pooled flagged: %s)." % (
        "valid" if h["status"]["valid"] else "not valid", ", ".join(pops_flag) or "no population",
        {p: h["pops"][p]["flagged_cells"] for p in C.POPS}, {p: h["pops"][p]["family_flagged"] for p in C.POPS},
        {p: h["pops"][p]["pooled"]["flagged"] for p in C.POPS}))
    for t in TRACKERS:
        a = R[t]["h2"]
        s = R[t]["h34"]["relied_records_by_score"]
        e = R[t]["h34"]["enforced_pairs"]
        out.append("%s: coarser-level threshold entries %.3f (record-weighted on P_rel %.4f); relied records below score 0.5: %.3f, "
                   "below 0.7: %.3f; enforced pairs whose track has no GT match %.4f (%.2f per decision)." % (
                       t, a["share_coarser_entries"], (a["record_weighted_A13_pooled"].get("PD7_primary") or {}).get("share") or float("nan"),
                       s["share_below_0.5"], s["share_below_0.7"], e["share_without_gt_match"] or float("nan"),
                       e["per_decision_without_gt"] or float("nan")))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    jpath = os.path.join(a.out_dir, "x3_h_ab3dmot_v01.json")
    mpath = os.path.join(a.out_dir, "x3_h_ab3dmot_v01.md")
    for p in (jpath, mpath):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)

    def log(*x):
        print(time.strftime("%H:%M:%S"), *x, flush=True)

    assert C.sha256(C.PLAN) == C.PLAN_SHA, "plan hash differs"
    ext = C.load_record_extract(TRACKERS)
    R = {}
    for i, t in enumerate(TRACKERS):
        C.live("(h) AB3DMOT diagnosis %s" % t, i, 3)
        rec = ext["trackers"][t]
        R[t] = {"h1": part_h1(t, rec), "h2": part_h2(t, rec), "h34": part_h34(t, log, a.out_dir)}
        log("%s done" % t)
    out = {"stamp": C.STAMP, "analysis": "X3 (h) AB3DMOT diagnosis, plan 2(h); referee M7",
           "plan": {"path": "20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md", "sha256": C.PLAN_SHA},
           "inputs": {"analysis_sha256": ext["analysis_sha256"],
                      "fits_sha256": {t: C.sha256(C.fits_path(t)) for t in TRACKERS},
                      "cells_csv_sha256": {t: C.sha256(os.path.join(C.CSV_DIR, "k8_within_lt3d_%s_decide_cells.csv" % t)) for t in TRACKERS},
                      "cache_manifest_sha256": {t: C.sha256(os.path.join(C.CACHE_DIR, "av2_cache_stageB_c1b_%s_own375" % t, "MANIFEST.json"))
                                                for t in TRACKERS}},
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__)},
           "versions": C.versions(), "score_bins_P4": P4_LABELS, "trackers": R, "choices": CHOICES, "reading": reading(R)}
    C.jdump_new(jpath, out)
    write_md(mpath, out)
    C.live("(h) AB3DMOT diagnosis done", 3, 3, "outputs written")
    log("wrote", jpath, mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
