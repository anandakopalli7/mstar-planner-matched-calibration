#!/usr/bin/env python3
"""Method stage run v01 (Claude line, 31 Oct 2026): evaluations E1 (held-out logs on train), E2 (train -> val), E4 (1 s and
4 s) and E5 (sensitivities) of 40_PROTOCOL/M_PREREGISTRATION for one tracker setting. Refuses to run unless the plan's
hash equals its sidecar, every frozen file is unchanged and every run input is in the frozen list. Each bootstrap uses its
own generator seeded by (20261031, crc32 of the evaluation label), so results do not depend on evaluation order.
"""
import argparse
import json
import os
import sys
import time
import zlib

import numpy as np

import m_data_v01 as MD
import m_lib_v01 as M

L = M.L
ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "V", "contested", "D")
REC_KEYS = ("s", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")
SENS = {"static_0.5": {"v_static": 0.5}, "static_2.0": {"v_static": 2.0}, "turn_0.05": {"w_turn": 0.05},
        "turn_0.20": {"w_turn": 0.20}, "omega_velocity": {"omega": "omv"}, "sigma_0": {"sigma_a": 0.0},
        "sigma_0.20": {"sigma_a": 0.20}, "n_min_39": {"n_min": 39}}


def frozen_block(prereg):
    txt = open(prereg, encoding="utf-8").read()
    return txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]


def check_freeze(prereg):
    side = open(prereg.replace(".md", ".sha256")).read().split()[0]
    if L.sha256_path(prereg) != side:
        raise SystemExit("pre-registration hash mismatch")
    n = 0
    for ln in frozen_block(prereg).strip().splitlines():
        if not ln.strip() or ln.startswith(("#", "(", "setting")):
            continue
        h, p = ln.split("  ", 1)
        if L.sha256_path(p.strip()) != h:
            raise SystemExit("frozen file changed: " + p)
        n += 1
    assert n > 10, "frozen block is empty"
    return side


def bind_inputs(prereg, paths):
    hashes = {ln.split("  ", 1)[0] for ln in frozen_block(prereg).strip().splitlines() if ln.strip() and not ln.startswith(("setting", "(", "#"))}
    for p in paths:
        assert L.sha256_path(p) in hashes, "run input not frozen: " + p


def rng_for(label):
    return np.random.default_rng([M.SEED, zlib.crc32(label.encode())])


def subset(items, recs, keep_item, keep_rec):
    it = dict(items)
    for k in ITEM_KEYS:
        it[k] = items[k][keep_item]
    rc = {k: recs[k][keep_rec] for k in REC_KEYS}
    return it, rc


def fit_summary(fit, full=False):
    out = {"B3": fit["B3"], "B4": fit["B4"], "B2_s": fit["B2"], "B7": fit["B7"], "B5": {"long": fit["B5"][0], "lat": fit["B5"][4]},
           "B1_k": fit["B1_k"],
           "Mstar_source_levels": {str(l): int((fit["Mstar_src"] == l).sum()) for l in range(4)},
           "MLS_source_levels": {str(l): int((fit["MLS_src"] == l).sum()) for l in range(4)},
           "Mstar_log_source_levels": {str(l): int((fit["Mstar_log_src"] == l).sum()) for l in range(4)}}
    if full:
        for k in ("Mstar", "MLS", "Mstar_log", "B6", "B8"):
            out[k] = {M.l0_name(i): [float(fit[k][i]), int(fit[k + "_src"][i])] for i in range(M.N_L0)}
        out["scale_beta"] = [float(x) for x in fit["scale_beta"]]
    return out


def strata_ids(names):
    rev = {M.l0_name(i): i for i in range(M.N_L0)}
    return [rev[n] for n in names]


def eval_strata_now(items, cfg):
    cnt = M.counts_by_l0(items, M.motion_state(items, cfg.get("v_static", M.V_STATIC), cfg.get("w_turn", M.W_TURN), cfg.get("omega", "om")))
    return sorted(strata_ids([k for k, v in cnt.items() if v["scenes"] >= M.N_EVAL]))


def run_e1(items, recs, cfg, names, slog, ev, label, unit="log", B=M.B_BOOT, reps=M.R_CV):
    """E1: R_CV repetitions of the 5-fold log split (repetition r uses fold seed SEED + r; r = 0 is the primary split).
    Per item, the exceedance indicator and the margin are averaged over repetitions (each item is held out once in each)."""
    P = M.prepare(items, recs, cfg)
    n = len(items["D"])
    exc = {m: np.zeros(n) for m in M.METHODS}
    marg = {m: np.zeros(n) for m in M.METHODS}
    seen = np.zeros(n)
    fsum = []
    for rep in range(reps):
        folds, _ = M.log_folds(names, slog, seed=M.SEED + rep)
        for f in range(M.K_FOLDS):
            cal = folds != f
            fit = M.fit_methods(items, recs, P, cal, cfg)
            sel = ~cal[items["s"]]
            seen[sel] += 1
            for k, v in M.margins(items, P, fit, sel).items():
                exc[k][sel] += items["D"][sel] > v
                marg[k][sel] += v
            if rep == 0:
                fsum.append(fit_summary(fit))
    assert np.all(seen == reps), "an item was not held out exactly once per repetition"
    exc = {k: v / reps for k, v in exc.items()}
    marg = {k: v / reps for k, v in marg.items()}
    st = M.eval_stats(items, P, marg, ev, M.boot_scene_weights(items, B, rng_for(label), unit), exc_frac=exc)
    st["hypotheses"] = M.hypotheses(st)
    st["folds_rep0"] = fsum
    st["repetitions"] = reps
    st["config"] = cfg
    return st


def run_e2(tr, trr, va, var, cfg, ev, label, B=M.B_REFIT):
    """E2: every rule fitted on all train scenes (the deployable rule) and evaluated on val. Inference by a two-sample
    log bootstrap: each replicate resamples train logs and val logs, refits every rule on the resampled train, and
    evaluates it on the resampled val, so calibration and test randomness both enter."""
    Pt, Pv = M.prepare(tr, trr, cfg), M.prepare(va, var, cfg)
    allv = np.ones(len(va["D"]), bool)
    fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), cfg)
    rng = rng_for(label)

    def replicates():
        for _ in range(B):
            mt = rng.multinomial(tr["n_logs"], np.full(tr["n_logs"], 1.0 / tr["n_logs"]))
            mv = rng.multinomial(va["n_logs"], np.full(va["n_logs"], 1.0 / va["n_logs"]))
            tb, tbr = M.resample_logs(tr, trr, mt)
            fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, cfg), np.ones(tb["n_scenes"], bool), cfg)
            yield M.margins(va, Pv, fb, allv), mv[va["scene_log_idx"]].astype(float)
    st = M.eval_stats_refit(va, Pv, M.margins(va, Pv, fit, allv), ev, replicates())
    st["hypotheses"] = M.hypotheses(st, ub_margin=0.03)
    st["fit_on_all_train"] = fit_summary(fit, full=True)
    st["config"] = cfg
    return st


def compact(st):
    """Sensitivity summary: per method the decision quantities, without per-stratum tables (except M* and B6)."""
    out = {"hypotheses": st["hypotheses"], "ratios": st["ratios"], "evaluated_strata": st["evaluated_strata"], "methods": {}}
    for k, v in st["methods"].items():
        out["methods"][k] = {x: v[x] for x in ("any_sig_under", "sig_under_strata", "E_bar", "E_bar_ub95", "max_E_scene", "mean_margin_m", "mean_margin_ci")}
        if k in ("Mstar", "B6"):
            out["methods"][k]["strata"] = v["strata"]
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("prereg", "tracker", "experiment", "train-gt", "val-gt", "meta", "train-horizon", "val-horizon", "sizes", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--train-workers", nargs="+", required=True)
    ap.add_argument("--val-workers", nargs="+", required=True)
    ap.add_argument("--test-mode", action="store_true", help="simulated-data tests only: skips the freeze and input checks")
    ap.add_argument("--boot", type=int, default=M.B_BOOT, help="test mode only")
    a = ap.parse_args()
    t0 = time.time()
    if a.test_mode:
        pre_sha, B = "TEST MODE", a.boot
    else:
        assert a.boot == M.B_BOOT, "--boot is for test mode only"
        pre_sha, B = check_freeze(a.prereg), M.B_BOOT
        ins = [a.train_gt, a.val_gt, a.train_horizon, a.val_horizon, a.sizes, os.path.join(a.meta, "scene.json")]
        ins += [os.path.join(w, f) for w in a.train_workers + a.val_workers for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
        bind_inputs(a.prereg, ins)
    sizes = json.load(open(a.sizes))
    assert sizes["tracker"] == a.tracker and sizes["experiment"] == a.experiment
    res = {"prereg_sha256": pre_sha, "tracker": a.tracker, "experiment": a.experiment, "B_boot": B, "delta": M.DELTA}
    tr, tinfo, tr_names, tr_log = MD.load_split(a.train_workers, a.train_gt, a.meta, a.train_horizon, a.experiment)
    va, vinfo, _, _ = MD.load_split(a.val_workers, a.val_gt, a.meta, a.val_horizon, a.experiment)
    res["Q0"] = {"train": tinfo, "val": vinfo}
    print("loaded %.0f s" % (time.time() - t0), flush=True)
    _, load = M.log_folds(tr_names, tr_log)
    res["folds"] = {"scenes_per_fold_rep0": load, "repetitions": M.R_CV}
    for split, data in (("train", tr), ("val", va)):
        for h, (items, _) in data.items():
            got = M.counts_by_l0(items, M.motion_state(items))
            assert got == sizes[split][h]["strata"], "stratum counts differ from the frozen sizes: %s %s" % (split, h)
    for h in M.HSTEPS:
        (ti, trc), (vi, vrc) = tr[h], va[h]
        e1 = run_e1(ti, trc, {}, tr_names, tr_log, strata_ids(sizes["train"][h]["evaluated"]), "%s|E1|%s" % (a.tracker, h), B=B)
        e2 = run_e2(ti, trc, vi, vrc, {}, strata_ids(sizes["val"][h]["evaluated"]), "%s|E2|%s" % (a.tracker, h), B=min(B, 200) if a.test_mode else M.B_REFIT)
        res["E1_" + h], res["E2_" + h] = e1, e2
        print(h, "E1", json.dumps(e1["hypotheses"]), "| E2 HM6", e2["hypotheses"]["HM1"], "| %.0f s" % (time.time() - t0), flush=True)
    ti, trc = tr["h2s"]
    sens = {}
    for name, cfg in SENS.items():
        sens[name] = compact(run_e1(ti, trc, cfg, tr_names, tr_log, eval_strata_now(ti, cfg), "%s|E5|%s" % (a.tracker, name), B=B))
    keep = ~ti["contested"]
    ci, cr = subset(ti, trc, keep, ~trc["contested"])
    sens["contested_excluded"] = compact(run_e1(ci, cr, {}, tr_names, tr_log, eval_strata_now(ci, {}), "%s|E5|contested" % a.tracker, B=B))
    sens["scene_bootstrap"] = compact(run_e1(ti, trc, {}, tr_names, tr_log, strata_ids(sizes["train"]["h2s"]["evaluated"]),
                                             "%s|E5|scene_boot" % a.tracker, unit="scene", B=B))
    res["E5_h2s"] = sens
    print("E5", {k: (v["hypotheses"]["HM1"], v["hypotheses"]["HM3"]) for k, v in sens.items()}, flush=True)
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print("M RUN DONE", a.tracker, res["wall_s"], flush=True)


if __name__ == "__main__":
    sys.exit(main())
