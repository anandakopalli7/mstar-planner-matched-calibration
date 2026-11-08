#!/usr/bin/env python3
"""X3 analysis (h4), direct count of enforced pairs whose track has no ground-truth match (x3-stats, v01, 7 Nov 2026). Plan 2(h); M7.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

Why a direct count: the items of record (50_CODE/k8/k8_items_v08.py, scene_items) enumerate pairs only over the tracks WITH a
ground-truth match (`for j in np.nonzero(inst >= 0)[0]`), so its totals pairs_enforced and pairs_with_gt both exclude false-positive
tracks; pairs_enforced - pairs_with_gt counts GT-matched tracks without a usable annotation at k + h, not false positives.
This tool repeats the items' enumeration exactly (same decision states, same considered set, same enforcement rule at the
arm-independent reference margin 0, computed by the frozen simulator k6_sim_v02's own functions, imported read-only; k6_sim_v02 imports
only numpy and the standard library and has no entry point), over EVERY considered track, and counts enforced (track, step) pairs by
whether the track has a GT match (tr_inst >= 0), by tr_score bin (plan P4) and by in-path flag.
Validation: on the GT-matched tracks it must reproduce the items summaries' decisions, pairs_considered, pairs_enforced and
pairs_with_gt exactly (checked and recorded).
The items script itself is never imported or run (it imports a guard module). Reads the frozen caches only.
One new JSON per tracker (<out-dir>/x3_h_fpcount_<t>_v01.json); a tracker whose file exists is skipped (resume).
Run: python -B x3_stats_h_fpcount_v01.py --out-dir <60_RESULTS/x3_explore_v01/h_ab3dmot> [--trackers t1,t3,tab]
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_stats_common_v01 as C  # noqa: E402

sys.path.insert(0, os.path.join(C.W, "50_CODE", "k6"))
import k6_sim_v02 as S  # noqa: E402

P4_LABELS = ["<0.4", "[0.4,0.5)", "[0.5,0.7)", "[0.7,0.85)", ">=0.85"]


def score_bin(s):
    s = np.asarray(s, np.float64)
    return np.where(s < 0.4, 0, np.where(s < 0.5, 1, np.where(s < 0.7, 2, np.where(s < 0.85, 3, 4))))


def count_scene(path):
    """k8_items_v08.scene_items' enumeration (decision states 1 <= k <= K-2, considered set, enforcement at margin 0), every track."""
    st = {"decisions": 0, "pairs_considered_gt_tracks": 0, "pairs_enforced_gt_tracks": 0, "pairs_with_gt": 0,
          "pairs_considered_all": 0, "pairs_enforced_all": 0, "pairs_enforced_no_gt_track": 0,
          "enforced_by_bin_gt": np.zeros(5), "enforced_by_bin_nogt": np.zeros(5),
          "enforced_inpath_gt": 0, "enforced_inpath_nogt": 0, "decisions_with_nogt_enforced": 0}
    sc = S.Scene(path)
    if sc.K < 3 or not len(sc.tr.get("k", [])):
        return st
    vmax = sc.v_log_max + 2.0
    tr = sc.tr
    inpath_all = tr["inpath"] if "inpath" in tr else np.zeros(len(tr["k"]), bool)
    inrack = sc.gt["inrack"] if "inrack" in sc.gt else np.zeros(len(sc.gt["k"]), bool)
    for k in range(1, sc.K - 1):
        st["decisions"] += 1
        tk = float(sc.kf_t[k])
        s, v = float(sc.s_log(tk)), max(sc.v_log(tk), 0.0)
        ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
        rows = sc.tr_by_k[k]
        if not len(rows):
            continue
        cxe, cye = ex + S.R2C * math.cos(eyaw), ey + S.R2C * math.sin(eyaw)
        dx, dy = tr["x"][rows] - cxe, tr["y"][rows] - cye
        sel = rows[(np.hypot(dx, dy) < S.R_CONSIDER) & (dx * math.cos(eyaw) + dy * math.sin(eyaw) >= -S.EGO_L / 2)]
        if not len(sel):
            continue
        sens_pose, sens_v, sens_w = S.sensor_ctrv(sc, k)
        g, r, m, sd, l0, ax = S.strata(sc, sel, k, sens_pose, sens_v, sens_w)
        pred = tr["pred"][sel]
        pred_xy = pred[:, :, :2]
        cur = np.stack([tr["x"][sel], tr["y"][sel]], -1)[:, None, :]
        prev = np.concatenate([cur, pred_xy[:, :-1]], 1)
        xy16 = np.empty((len(sel), S.N_EVAL, 2))
        xy16[:, 1::2] = pred_xy
        xy16[:, 0::2] = 0.5 * (prev + pred_xy)
        half = np.stack([0.5 * tr["l"][sel], 0.5 * tr["w"][sel]], -1)
        lead = sc.s_log(tk + S.EVAL_T)
        splan = np.minimum(S.plan_positions(s, v, vmax), lead[None, :])
        gap, _ = S.gaps(sc, splan, xy16, ax, half)
        ctrl = (np.max(gap, axis=-1) >= 0.0).any(axis=0)[:S.CC_EVAL]
        ghold, _ = S.gaps(sc, np.full((1, S.N_EVAL), s), xy16, ax, half)
        hold_ok = (np.max(ghold[0], axis=-1) >= 0.0)[:S.CC_EVAL]
        enf = (ctrl & hold_ok)[1::2]
        inst, inp = tr["inst"][sel], inpath_all[sel]
        sb = score_bin(tr["score"][sel])
        gtm = inst >= 0
        any_nogt = False
        for h in range(S.CC_STEPS):
            kk = k + h + 1
            if kk >= sc.K:
                break
            e = enf[h]
            st["pairs_considered_all"] += len(sel)
            st["pairs_enforced_all"] += int(e.sum())
            st["pairs_considered_gt_tracks"] += int(gtm.sum())
            st["pairs_enforced_gt_tracks"] += int((e & gtm).sum())
            st["pairs_enforced_no_gt_track"] += int((e & ~gtm).sum())
            any_nogt = any_nogt or bool((e & ~gtm).any())
            st["enforced_by_bin_gt"] += np.bincount(sb[e & gtm], minlength=5)
            st["enforced_by_bin_nogt"] += np.bincount(sb[e & ~gtm], minlength=5)
            st["enforced_inpath_gt"] += int((e & gtm & inp).sum())
            st["enforced_inpath_nogt"] += int((e & ~gtm & inp).sum())
            gat = sc.gt_at[kk]
            for j in np.nonzero(e & gtm)[0]:
                row = gat.get(int(inst[j]))
                if row is None or inrack[row]:
                    continue
                st["pairs_with_gt"] += 1
        st["decisions_with_nogt_enforced"] += int(any_nogt)
    return st


def run_tracker(t, out_dir, log):
    path = os.path.join(out_dir, "x3_h_fpcount_%s_v01.json" % t)
    if os.path.exists(path):
        log("%s exists, skipped" % t)
        return
    with open(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375_summary.json" % t), encoding="utf-8") as f:
        summ = json.load(f)
    cache = os.path.join(C.CACHE_DIR, "av2_cache_stageB_c1b_%s_own375" % t)
    names = summ["scene_names"]
    tot = None
    t0 = time.time()
    for i, name in enumerate(names):
        st = count_scene(os.path.join(cache, name + ".npz"))
        if tot is None:
            tot = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in st.items()}
        else:
            for k_, v in st.items():
                tot[k_] = tot[k_] + v
        if i % 25 == 24:
            C.live("(h4) direct count of enforced pairs %s" % t, i + 1, len(names), "scenes")
            log("%s %d/%d scenes (%.0f s)" % (t, i + 1, len(names), time.time() - t0))
    rec = summ["totals"]
    checks = {"decisions": (tot["decisions"], rec["decisions"]), "pairs_considered": (tot["pairs_considered_gt_tracks"], rec["pairs_considered"]),
              "pairs_enforced": (tot["pairs_enforced_gt_tracks"], rec["pairs_enforced"]), "pairs_with_gt": (tot["pairs_with_gt"], rec["pairs_with_gt"])}
    ea, en = tot["pairs_enforced_all"], tot["pairs_enforced_no_gt_track"]
    out = {"stamp": C.STAMP, "tracker": t, "scenes": len(names),
           "validation_against_items_summary": {k: {"x3": int(a), "record": int(b), "equal": int(a) == int(b)} for k, (a, b) in checks.items()},
           "validated": all(int(a) == int(b) for a, b in checks.values()),
           "decisions": int(tot["decisions"]), "pairs_considered_all_tracks": int(tot["pairs_considered_all"]),
           "pairs_enforced_all_tracks": int(ea), "pairs_enforced_no_gt_track": int(en),
           "share_enforced_without_gt_match": en / ea if ea else None,
           "per_decision_enforced_without_gt_match": en / tot["decisions"] if tot["decisions"] else None,
           "decisions_with_an_enforced_no_gt_track_share": tot["decisions_with_nogt_enforced"] / tot["decisions"] if tot["decisions"] else None,
           "enforced_by_score_bin": {"gt_matched": dict(zip(P4_LABELS, tot["enforced_by_bin_gt"].tolist())),
                                     "no_gt_match": dict(zip(P4_LABELS, tot["enforced_by_bin_nogt"].tolist()))},
           "share_without_gt_by_score_bin": dict(zip(P4_LABELS, [float(b / (a + b)) if (a + b) else None for a, b in zip(
               tot["enforced_by_bin_gt"], tot["enforced_by_bin_nogt"])])),
           "enforced_in_path": {"gt_matched": int(tot["enforced_inpath_gt"]), "no_gt_match": int(tot["enforced_inpath_nogt"]),
                                "share_without_gt": tot["enforced_inpath_nogt"] / (tot["enforced_inpath_gt"] + tot["enforced_inpath_nogt"])
                                if (tot["enforced_inpath_gt"] + tot["enforced_inpath_nogt"]) else None},
           "note": "pairs = (track, calibrated step) at the decision states of the items' reference run (logged ego, margin 0)",
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__, S.__file__)},
           "items_summary_sha256": C.sha256(os.path.join(C.ITEMS_DIR, "items_c1b_%s_own375_summary.json" % t)),
           "seconds": time.time() - t0, "written": C.now()}
    C.jdump_new(path, out)
    log("%s written: validated %s, share without GT %.4f (%.0f s)" % (t, out["validated"], out["share_enforced_without_gt_match"] or -1,
                                                                     time.time() - t0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--trackers", default="t1,t3,tab")
    a = ap.parse_args(argv)

    def log(*x):
        print(time.strftime("%H:%M:%S"), *x, flush=True)

    for t in a.trackers.split(","):
        run_tracker(t, a.out_dir, log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
