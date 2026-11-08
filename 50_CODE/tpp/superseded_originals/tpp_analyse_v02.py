#!/usr/bin/env python3
"""TPP arm analysis v02 (Claude line, 4 Nov 2026) PROPOSED for 90_DECISIONS/D17_TPP_ARM_PREREG_v02.md (draft, not frozen).
Run in canmot310. Written and tested on SYNTHETIC data only; real data need the freeze record (as v01).
v02 = v01 (kept; its loaders, item table, cross-fitting and A6 are imported unchanged) + D16 v10 Choices 27-29:
  * Choice 29: the 4 development scenes are excluded (keys `scene_is_dev`); the 146 remaining scenes are cut into 5
    cross-fitting folds of 30/29/29/29/29 (seeded permutation of the sorted names, numpy.array_split);
  * Choice 29: HK1a (iii) floors REPORTED, NOT GATING: per population, the power-qualified family of TPP_Mstar by K7's
    rule (k6_analyse_v02.power_family, imported unchanged: power >= 0.80 to be flagged at a true 0.15, beta-binomial
    rho = 0.5, 200 datasets, the first 500 bootstrap weights; seed [20261108, population index]), its size against
    F_MIN = 6, and whether any family cell is flagged;
  * Choice 27: S1 seed robustness: the identical analysis with the tracker-history run of each further seed (20261104,
    20261105; the ground-truth arm stays the primary run); a hypothesis is seed-robust only if it holds under all three;
  * Choice 27: S2 seed-pooled V2 (descriptive): at 2 s, the equal-weight mixture of the three seeds' stored
    25-component mixtures (75 components, weights w / 3), moment-matched, analysed as the TPP arm;
  * Choice 28: tail sensitivity (pre-stated): the primary analysis repeated without the records whose V2 trace exceeds
    100 m^2 in any Trajectron++ arm of the analysis (tracker or ground-truth histories), so the set stays paired.
Primary = seed 20261102, V2, tracker histories, int_ee; V1 secondary. Hypotheses and rules: D17 v02 sections 2, 6, 7.
Usage (synthetic): python -I tpp_analyse_v02.py --synthetic --keys K --runs trk=R gt=R [--seed-runs 20261104=R 20261105=R] --out J
       (real, after the freeze): ... --plan <D17 v02> --freeze-record <json> [--cache-dir <val cache>]
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(2, os.path.join(W_ROOT, "50_CODE", "k6"))
import tpp_common_v01 as C  # noqa: E402
import tpp_analyse_v01 as A1  # noqa: E402
import k6_analyse_v02 as K6A  # noqa: E402

M, L = A1.M, A1.L
DELTA, Z, SIGMA_A = A1.DELTA, A1.Z, A1.SIGMA_A
FOLD_SEED, N_FOLDS, B_BOOT, BOOT_SEED, H_PRIMARY, HK1C_EPS = A1.FOLD_SEED, A1.N_FOLDS, A1.B_BOOT, A1.BOOT_SEED, A1.H_PRIMARY, A1.HK1C_EPS
POWER_SEED_TPP = 20261108
TAIL_TRACE_M2 = 100.0
PRIMARY_SEED = 20261102
SYN_STAMP = A1.SYN_STAMP
POPS = ("PD7", "SD1_7", "PD")


def scene_folds_v02(scene_names, is_dev, seed=FOLD_SEED, k=N_FOLDS):
    """Fold per scene index: -1 for development scenes; the others by a seeded permutation of their sorted names cut by
    numpy.array_split into k near-equal blocks (146 scenes: 30, 29, 29, 29, 29)."""
    names = sorted(s for s, d in zip(scene_names, is_dev) if not d)
    perm = np.random.default_rng(seed).permutation(len(names))
    fold_of = {}
    for f, block in enumerate(np.array_split(perm, k)):
        for p in block:
            fold_of[names[p]] = f
    return np.array([fold_of.get(s, -1) for s in scene_names], np.int32)


def pooled_run(seed_runs, n_rec):
    """S2: for every record with a stored step-4 mixture and status ok in every seed run, the moment-matched V2 of the
    equal-weight mixture of all seeds' components (weights w_k / n_seeds). Other records get a non-ok status."""
    status = np.full(n_rec, C.ST_NOT_PREDICTED, np.int8)
    mu, cov = np.full((n_rec, 2), np.nan), np.full((n_rec, 3), np.nan)
    maps = [{int(j): i for i, j in enumerate(z["mix_rec"])} for z in seed_runs]
    ok_all = np.all([z["status"] == C.ST_OK for z in seed_runs], axis=0)
    rows = [j for j in maps[0] if ok_all[j] and all(j in mp for mp in maps)]
    if rows:
        rows = np.array(sorted(rows))
        W_, MU, S = [], [], []
        for z, mp in zip(seed_runs, maps):
            ii = np.array([mp[j] for j in rows])
            W_.append(z["mix_w"][ii].astype(float) / len(seed_runs))
            MU.append(z["mix_mu"][ii])
            S.append(C.cov22(z["mix_cov"][ii]))
        m2, S2 = C.v2_moment_match(np.concatenate(W_, -1), np.concatenate(MU, -2), np.concatenate(S, -3))
        mu[rows], cov[rows], status[rows] = m2, C.cov3(S2), C.ST_OK
    return {"status": status, "v2_mu": mu, "v2_cov": cov, "v1_mu": mu, "v1_cov": cov}


def floors(items, lv, cells, exc_m, pop_index, W):
    """HK1a (iii), reported not gating: K7's power-qualified family for TPP_Mstar and whether a family cell is flagged."""
    lay = M._layout(items, {"lv": lv}, cells, None)
    N = lay["n_ig"]
    X = np.zeros_like(N)
    np.add.at(X, (lay["s"][lay["in_eval"]], lay["col"][lay["in_eval"]]), exc_m[lay["in_eval"]])
    scene_of = np.arange(N.shape[0])
    logs = items["scene_log_idx"]
    ev = K6A.evaluable(N, scene_of, logs)
    pw, _ = K6A.power_family(N, ev, scene_of, W[:500], np.random.default_rng([POWER_SEED_TPP, pop_index]))
    qual = np.flatnonzero(ev & (pw >= K6A.POWER_MIN))
    one = np.ones((1, N.shape[0]))
    flagged = []
    if len(qual):
        est, boot = K6A.rates(N, X, one)[0], K6A.rates(N, X, W)
        _, _, _, sig, _ = K6A.flag(est, boot, qual, 0.95)
        flagged = [cells[j][0] for i, j in enumerate(qual) if sig[i]]
    return {"evaluable_cells": int(ev.sum()), "power_at_0.15": {cells[j][0]: float(pw[j]) for j in np.flatnonzero(ev)},
            "family": [cells[j][0] for j in qual], "family_size": int(len(qual)), "F_MIN": K6A.F_MIN,
            "family_flagged": flagged, "floor_met": bool(len(qual) >= K6A.F_MIN and not flagged),
            "role": "reported, not gating (D16 v10 Choice 29)"}


def analyse_v02(kz, runs, gt_xy, trk_mu, trk_cov, variant="v2", B=B_BOOT, tail_cap=None):
    it = A1.item_table(kz, runs, gt_xy, trk_mu, trk_cov, H_PRIMARY, variant)
    names = [str(x) for x in kz["scene_names"]]
    is_dev = np.asarray(kz["scene_is_dev"], bool)
    folds = scene_folds_v02(names, is_dev)
    arms = ["TRK"] + [a for a in ("TPP", "TPPgt") if a + "_ok" in it]
    keep = ~is_dev[it["s"]]
    common = keep.copy()
    for a in arms:
        common &= it[a + "_ok"]
    tail_drop = np.zeros(len(common), bool)
    if tail_cap is not None:
        for src, z in runs.items():
            c3 = z["v2_cov"][it["rec"]]
            tail_drop |= np.nan_to_num(c3[:, 0] + c3[:, 2], nan=0.0) > tail_cap
        common &= ~tail_drop
    res = {"variant": variant, "h": H_PRIMARY, "tail_cap_m2": tail_cap,
           "folds": {str(f): sorted(np.array(names)[folds == f].tolist()) for f in range(N_FOLDS)},
           "excluded_dev_scenes": sorted(np.array(names)[is_dev].tolist()),
           "counts": {"relied_items_h": int(len(common)), "in_dev_scenes": int((~keep).sum()), "tail_dropped": int((tail_drop & keep).sum()),
                      "common_ok": int(common.sum()), **{a + "_ok_nondev": int((it[a + "_ok"] & keep).sum()) for a in arms}},
           "populations": {}}
    pops = {"PD7": common, "SD1_7": common & (it["gap"] <= 5.0), "PD": common & it["inpath"]}
    items7, m7, lv7 = A1.mlib_items(it, pops["PD7"], kz)
    EXC, MARG, fitinfo = {}, {}, {}
    for a in arms:
        D, V = it[a + "_D"][pops["PD7"]], it[a + "_V"][pops["PD7"]]
        sd = np.sqrt(np.maximum(V + SIGMA_A ** 2, 1e-6))
        thr, src, fits = A1.crossfit(D / sd, items7["s"], lv7, folds)
        for meth, mg in (("B0", Z * sd), ("B4", thr["B4"] * sd), ("B3", thr["B3"] * sd), ("Mstar", thr["Mstar"] * sd)):
            EXC[a + "_" + meth] = (D > mg).astype(float)
            MARG[a + "_" + meth] = mg
        fitinfo[a] = {"folds": fits, "Mstar_own_threshold_share": float(np.mean(src == 0))}
    idx7 = np.nonzero(pops["PD7"])[0]
    for k, (pname, sel) in enumerate(pops.items()):
        items, m, lv = A1.mlib_items(it, sel, kz)
        sub = np.isin(idx7, np.nonzero(sel)[0])
        exc = {q: v[sub] for q, v in EXC.items()}
        marg = {q: v[sub] for q, v in MARG.items()}
        W = M.boot_scene_weights(items, B, np.random.default_rng(BOOT_SEED), "log")
        cells = M.make_cells(items, m, "E2")
        pairs = []
        if "TPP" in arms:
            pairs.append(("TPP_B0", "TRK_B0", list(range(len(cells))), "TPP_B0 - TRK_B0"))
            if "TPPgt" in arms:
                pairs.append(("TPP_B0", "TPPgt_B0", list(range(len(cells))), "TPP_B0 - TPPgt_B0 (input-noise share)"))
        st = M.eval_stats(items, {"lv": lv}, marg, cells, W, exc_frac=exc, pairs=pairs) if cells else None
        pooled = M.eval_stats(items, {"lv": lv}, marg, [("pooled", list(range(M.N_L0)))], W, exc_frac=exc,
                              pairs=[(p[0], p[1], [0], p[3]) for p in pairs])
        hk = {}
        for meth in marg:
            pc = pooled["methods"][meth]["cells"]["pooled"]
            hk[meth] = {"no_flagged_cell": (not st["methods"][meth]["any_sig_under"]) if st else None,
                        "flagged_cells": st["methods"][meth]["sig_under_cells"] if st else [],
                        "pooled_E": pc["E_scene"], "pooled_lb": pc["lb_sim"], "pooled_ub": pc["ub_sim"],
                        "pooled_not_flagged": not pc["sig_under"], "HK1c_pooled_ub_le_delta_plus_0.03": pc["ub_sim"] <= DELTA + HK1C_EPS,
                        "mean_margin_m": pc["mean_margin_m"]}
            hk[meth]["HK1"] = bool(hk[meth]["no_flagged_cell"] is not False and hk[meth]["pooled_not_flagged"] and cells)
        fl = floors(items, lv, cells, exc["TPP_Mstar"], k, W) if ("TPP" in arms and cells) else None
        res["populations"][pname] = {"items": int(sel.sum()), "scenes": int(len(np.unique(items["s"]))), "cells": [c[0] for c in cells],
                                     "validity": hk, "HK1a_iii_floor_TPP_Mstar": fl, "cells_stats": st, "pooled_stats": pooled}
    res["fits"] = fitinfo
    recs = np.unique(it["rec"][pops["PD7"]])
    s_rec = kz["rec_s"][recs].astype(int)
    res["A6"] = {"TRK": A1.a6(gt_xy[recs] - trk_mu[recs], trk_cov[recs], s_rec, len(names))}
    for src, z in runs.items():
        res["A6"]["TPP" if src == "trk" else "TPPgt"] = A1.a6(gt_xy[recs] - z[variant + "_mu"][recs], z[variant + "_cov"][recs], s_rec, len(names))
    v = {p: res["populations"][p]["validity"] for p in POPS}
    cs = res["populations"]["PD7"]["pooled_stats"]["paired"]
    lab = "TPP_B0 - TPPgt_B0 (input-noise share)"
    res["hypotheses"] = {
        "H1_raw_TPP_overconfident": bool(v["PD7"]["TPP_B0"]["pooled_lb"] > DELTA) if "TPP_B0" in v["PD7"] else None,
        "H2_Mstar_TPP_valid_HK1_all_pops": bool(all(v[p]["TPP_Mstar"]["HK1"] for p in POPS)) if "TPP_Mstar" in v["PD7"] else None,
        "H2_HK1c_PD7": bool(v["PD7"]["TPP_Mstar"]["HK1c_pooled_ub_le_delta_plus_0.03"]) if "TPP_Mstar" in v["PD7"] else None,
        "H3_gt_history_less_exceedance": bool(cs[lab]["cells"]["pooled"]["positive"]) if lab in cs else None}
    res["key_numbers"] = {"TPP_B0_pooled_E_PD7": v["PD7"].get("TPP_B0", {}).get("pooled_E"),
                          "TPP_Mstar_pooled_E_PD7": v["PD7"].get("TPP_Mstar", {}).get("pooled_E"),
                          "TPP_Mstar_mean_margin_m_PD7": v["PD7"].get("TPP_Mstar", {}).get("mean_margin_m"),
                          "TRK_Mstar_mean_margin_m_PD7": v["PD7"].get("TRK_Mstar", {}).get("mean_margin_m")}
    return res


def seed_robust(primary, by_seed):
    """A hypothesis is seed-robust iff it holds (True) under the primary seed and every further seed."""
    out = {}
    for h, val in primary["hypotheses"].items():
        vals = [val] + [r["hypotheses"][h] for r in by_seed.values()]
        out[h] = {"by_seed": {str(PRIMARY_SEED): val, **{s: r["hypotheses"][h] for s, r in by_seed.items()}},
                  "seed_robust": bool(all(x is True for x in vals))}
    keys = primary["key_numbers"]
    out["key_number_ranges"] = {k: [min(x for x in [keys[k]] + [r["key_numbers"][k] for r in by_seed.values()] if x is not None),
                                    max(x for x in [keys[k]] + [r["key_numbers"][k] for r in by_seed.values()] if x is not None)]
                                for k in keys if keys[k] is not None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--runs", nargs="+", required=True, help="trk=<primary-seed run> gt=<run>")
    ap.add_argument("--seed-runs", nargs="*", default=[], help="<seed>=<tracker-history run of that seed> (S1, S2)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--freeze-record", default=None)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--boot", type=int, default=B_BOOT)
    a = ap.parse_args()
    t0 = time.time()
    me = C.sha256_path(os.path.abspath(__file__))
    if not a.synthetic:
        assert a.plan and a.freeze_record, "real data: the frozen plan and its freeze record are required (D17 v02 is a draft)"
        fr = json.load(open(a.freeze_record))
        assert fr.get("analysis_sha256") == me, "this analysis file is not the frozen one"
        assert fr.get("plan_sha256") == C.sha256_path(a.plan), "the plan file is not the frozen one"
    run_paths = dict(x.split("=", 1) for x in a.runs)
    seed_paths = dict(x.split("=", 1) for x in a.seed_runs)
    kz, runs, gt_xy, trk_mu, trk_cov = A1.load_inputs(a.keys, run_paths, a.synthetic, a.cache_dir)
    seeds = {}
    for sd, p in seed_paths.items():
        _, r1, _, _, _ = A1.load_inputs(a.keys, {"trk": p}, a.synthetic, a.cache_dir)
        seeds[sd] = r1["trk"]
    out = {"stamp": SYN_STAMP if a.synthetic else "TPP arm analysis v02 on the frozen D17 v02 plan", "analysis_sha256": me,
           "imports_sha256": {"tpp_analyse_v01": C.sha256_path(A1.__file__), "k6_analyse_v02": C.sha256_path(K6A.__file__),
                              "m_lib_v04": C.sha256_path(M.__file__)},
           "keys_sha256": C.sha256_path(a.keys), "runs_sha256": {k: C.sha256_path(v) for k, v in run_paths.items()},
           "seed_runs_sha256": {k: C.sha256_path(v) for k, v in seed_paths.items()}, "results": {}}
    R = out["results"]
    R["primary_v2"] = analyse_v02(kz, runs, gt_xy, trk_mu, trk_cov, "v2", a.boot)
    R["secondary_v1"] = analyse_v02(kz, runs, gt_xy, trk_mu, trk_cov, "v1", a.boot)
    R["sensitivity_tail_excluded_v2"] = analyse_v02(kz, runs, gt_xy, trk_mu, trk_cov, "v2", a.boot, tail_cap=TAIL_TRACE_M2)
    if seeds:
        by_seed = {sd: analyse_v02(kz, {"trk": z, **{k: v for k, v in runs.items() if k != "trk"}}, gt_xy, trk_mu, trk_cov, "v2", a.boot)
                   for sd, z in seeds.items()}
        R["S1_seed_robustness"] = {"per_seed": by_seed, "summary": seed_robust(R["primary_v2"], by_seed)}
        pooled = pooled_run([runs["trk"]] + list(seeds.values()), len(kz["rec_k"]))
        R["S2_seed_pooled_v2_descriptive"] = analyse_v02(kz, {"trk": pooled, **{k: v for k, v in runs.items() if k != "trk"}},
                                                         gt_xy, trk_mu, trk_cov, "v2", a.boot)
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({k: R[k]["hypotheses"] for k in R if "hypotheses" in R[k]}))
    if "S1_seed_robustness" in R:
        print(json.dumps({h: v["seed_robust"] for h, v in R["S1_seed_robustness"]["summary"].items() if isinstance(v, dict) and "seed_robust" in v}))
    print("TPP ANALYSE V02 DONE")


if __name__ == "__main__":
    main()
