#!/usr/bin/env python3
"""Method stage run v04 (Claude line, 31 Oct 2026): evaluations of 40_PROTOCOL/M_PREREGISTRATION_v05 for one tracker setting.
v04 (R07c):
- the v04 modules;
- the minimum-chord sensitivity;
- fault-tolerant 1 s and 4 s sections;
- turning shares by speed band.
Changes from v02 (R07b):
- the m_data_v03 loader (Poly-MOT velocity correction);
- the course-over-ground heading rate;
- partial results are written after every section;
- a failing sensitivity is recorded, not fatal;
- the B2 cap flag and the peak memory are reported.
- E1: held-out logs on train, 20 repetitions of the 5-fold log split. Fixed-rule log bootstrap, plus a refit-CV log
  bootstrap at the decision horizon (2 s).
- E2: train to val, deployable fit; two-sample refit log bootstrap.
- E4: 1 s and 4 s.
- E5: sensitivities.
It refuses to run unless the plan's hash equals its sidecar, every frozen file is unchanged, every run input is in the
frozen list, and numpy and scipy match the frozen environment listing. Each bootstrap uses its own generator seeded by
(20261031, crc32 of its label), so results do not depend on evaluation order.
"""
import argparse
import json
import os
import sys
import time
import zlib

import numpy as np

import m_data_v04 as MD
import m_lib_v04 as M

L = M.L
ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "chord", "V", "contested", "D")
REC_KEYS = ("s", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")
SENS = {"static_0.5": {"v_static": 0.5}, "static_2.0": {"v_static": 2.0}, "turn_0.05": {"w_turn": 0.05},
        "turn_0.20": {"w_turn": 0.20}, "omega_velocity_all": {"omega": "omv"}, "omega_yaw_all": {"omega": "om"},
        "sigma_0": {"sigma_a": 0.0}, "sigma_0.20": {"sigma_a": 0.20}, "n_min_39": {"n_min": 39}, "cog_min_chord_1m": {"omega": "omc_chord1"}}
B_E2_SECONDARY = 300  # E2 replicates at the descriptive horizons (1 s, 4 s)


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


def check_versions(pip_freeze):
    import scipy
    pins = dict(ln.strip().split("==", 1) for ln in open(pip_freeze, encoding="utf-8", errors="replace") if "==" in ln)
    for mod, ver in (("numpy", np.__version__), ("scipy", scipy.__version__)):
        assert pins.get(mod) == ver, "%s %s differs from the frozen listing %s" % (mod, ver, pins.get(mod))


def rng_for(label):
    return np.random.default_rng([M.SEED, zlib.crc32(label.encode())])


def subset(items, recs, keep_item, keep_rec):
    it = dict(items)
    for k in ITEM_KEYS:
        it[k] = items[k][keep_item]
    rc = {k: recs[k][keep_rec] for k in REC_KEYS}
    return it, rc


def cells_from(js):
    return [(n, list(ids)) for n, ids in js]


def fit_summary(fit, full=False):
    out = {"B3": fit["B3"], "B4": fit["B4"], "B9_radius_m": fit["B9"], "B2_s": fit["B2"], "B2_cap_hit": fit["B2_cap_hit"], "B7": fit["B7"],
           "B5": {"long": fit["B5"][0], "lat": fit["B5"][4]}, "B1_k": fit["B1_k"], "Mstar_log_incomplete": fit["Mstar_log_incomplete"],
           "Mstar_source_levels": {str(l): int((fit["Mstar_src"] == l).sum()) for l in range(4)}}
    if full:
        for k in ("Mstar", "MLS", "Mstar_log", "B6", "B8"):
            out[k] = {M.l0_name(i): [float(fit[k][i]), int(fit[k + "_src"][i])] for i in range(M.N_L0)}
        out["B10"] = {M.l0_name(i): float(fit["B10"][i]) for i in range(M.N_L0)}
        out["scale_beta"] = [float(x) for x in fit["scale_beta"]]
    return out


def run_e1(items, recs, cfg, names, slog, cells, label, unit="log", B=M.B_BOOT, reps=M.R_CV, refit_B=0, only=None):
    P = M.prepare(items, recs, cfg)
    n = len(items["D"])
    meths = M.METHODS if only is None else ["Mstar"] + [x for x in ("B6",) if x in only]
    exc = {m: np.zeros(n) for m in meths}
    marg = {m: np.zeros(n) for m in meths}
    own, tot = np.zeros(M.N_L0), np.zeros(M.N_L0)
    for rep in range(reps):
        folds, _ = M.log_folds(names, slog, seed=M.SEED + rep)
        e, mg, src = M.cv_once(items, recs, P, cfg, folds, only)
        assert np.all(src >= 0), "an item was not held out in repetition %d" % rep
        for k in meths:
            exc[k] += e[k]
            marg[k] += mg[k]
        np.add.at(own, P["lv"][0], (src == 0).astype(float))
        np.add.at(tot, P["lv"][0], 1.0)
    exc = {k: v / reps for k, v in exc.items()}
    marg = {k: v / reps for k, v in marg.items()}
    pairs = M.standard_pairs(cells)
    W = M.boot_scene_weights(items, B, rng_for(label), unit)
    out = {"config": cfg, "repetitions": reps,
           "fixed": M.eval_stats(items, P, marg, cells, W, exc_frac=exc, pairs=pairs),
           "pooled_fixed": compact(M.eval_stats(items, P, marg, [("all train items", list(range(M.N_L0)))], W, exc_frac=exc)),
           "Mstar_own_threshold_share": {name: float(own[ids].sum() / max(tot[ids].sum(), 1)) for name, ids in cells}}
    if refit_B:
        rng = rng_for(label + "|refit")

        def replicates():
            for b in range(refit_B):
                mult = rng.multinomial(items["n_logs"], np.full(items["n_logs"], 1.0 / items["n_logs"]))
                tb, tbr = M.resample_logs(items, recs, mult)
                Pb = M.prepare(tb, tbr, cfg)
                e, mg, _ = M.cv_once(tb, tbr, Pb, cfg, M.folds_by_original_log(tb, seed=M.SEED + 1000 + b), only)
                yield tb, Pb, e, mg, None
        st = M.eval_stats_replicates(items, P, marg, {"cells": cells, "pooled": [("all train items", list(range(M.N_L0)))]},
                                     replicates(), exc_point=exc, pairs={"cells": pairs})
        out["refit"], out["pooled_refit"] = st["cells"], compact(st["pooled"])
        out["hypotheses"] = M.hypotheses_e1(out["fixed"], out["refit"])
    return out


def run_e2(tr, trr, va, var, cfg, cells, label, B=M.B_REFIT, only=None):
    """Point: every method fitted on all train scenes (deployable rule), evaluated on val. Inference: two-sample log
    bootstrap; each replicate resamples train logs and val logs, refits every method on the resampled train and evaluates
    it on the resampled val."""
    Pt, Pv = M.prepare(tr, trr, cfg), M.prepare(va, var, cfg)
    allv = np.ones(len(va["D"]), bool)
    fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), cfg, only)
    rng = rng_for(label)

    def replicates():
        for _ in range(B):
            mt = rng.multinomial(tr["n_logs"], np.full(tr["n_logs"], 1.0 / tr["n_logs"]))
            mv = rng.multinomial(va["n_logs"], np.full(va["n_logs"], 1.0 / va["n_logs"]))
            tb, tbr = M.resample_logs(tr, trr, mt)
            fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, cfg), np.ones(tb["n_scenes"], bool), cfg, only)
            mg = M.margins(va, Pv, fb, allv)
            yield va, Pv, {k: va["D"] > v for k, v in mg.items()}, mg, mv[va["scene_log_idx"]].astype(float)
    fams = {"cells": cells, "all": [("all val items", list(range(M.N_L0)))]}
    st = M.eval_stats_replicates(va, Pv, M.margins(va, Pv, fit, allv), fams, replicates(), pairs={"cells": M.standard_pairs(cells)})
    return {"config": cfg, "cells": st["cells"], "all": st["all"], "hypotheses": M.hypotheses_e2(st["cells"], st["all"]),
            "fit_on_all_train": fit_summary(fit, full=True) if only is None else None, "n_boot": B}


def compact(st):
    out = {"ratios": st["ratios"], "cells": st["cells"], "paired": st.get("paired", {}), "methods": {}}
    for k, v in st["methods"].items():
        out["methods"][k] = {x: v[x] for x in ("any_sig_under", "sig_under_cells", "E_bar", "E_bar_ub95", "max_E_scene", "mean_margin_m",
                                               "mean_margin_ci", "mean_margin_by_axis")}
        if k in ("Mstar", "B6", "B0") or len(st["cells"]) <= 2:
            out["methods"][k]["cells"] = v["cells"]
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("prereg", "tracker", "experiment", "train-gt", "val-gt", "meta", "train-horizon", "val-horizon", "sizes", "out", "pip-freeze"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--train-workers", nargs="+", required=True)
    ap.add_argument("--val-workers", nargs="+", required=True)
    ap.add_argument("--test-mode", action="store_true", help="simulated-data tests only: skips the freeze, input and version checks")
    ap.add_argument("--boot", type=int, default=0, help="test mode only: overrides every bootstrap size")
    a = ap.parse_args()
    t0 = time.time()
    if a.test_mode:
        pre_sha = "TEST MODE"
        B1_, BR, B2_, B2s = (a.boot,) * 4
    else:
        assert a.boot == 0, "--boot is for test mode only"
        pre_sha = check_freeze(a.prereg)
        check_versions(a.pip_freeze)
        ins = [a.train_gt, a.val_gt, a.train_horizon, a.val_horizon, a.sizes, os.path.join(a.meta, "scene.json"), a.pip_freeze]
        ins += [os.path.join(w, f) for w in a.train_workers + a.val_workers for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
        bind_inputs(a.prereg, ins)
        B1_, BR, B2_, B2s = M.B_BOOT, M.B_E1R, M.B_REFIT, B_E2_SECONDARY
    sizes = json.load(open(a.sizes))
    assert sizes["tracker"] == a.tracker and sizes["experiment"] == a.experiment
    res = {"prereg_sha256": pre_sha, "tracker": a.tracker, "experiment": a.experiment, "delta": M.DELTA,
           "B": {"E1_fixed": B1_, "E1_refit": BR, "E2_refit": B2_, "E2_secondary": B2s}}
    tr, tinfo, tr_names, tr_log = MD.load_split(a.train_workers, a.train_gt, a.meta, a.train_horizon, a.experiment)
    va, vinfo, _, _ = MD.load_split(a.val_workers, a.val_gt, a.meta, a.val_horizon, a.experiment)
    res["Q0"] = {"train": tinfo, "val": vinfo}
    print("loaded %.0f s" % (time.time() - t0), flush=True)

    def save(stage):
        res["completed_through"] = stage
        res["peak_working_set_mb"] = MD.peak_mb()
        res["wall_s"] = round(time.time() - t0, 1)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1, default=float)
    for split, data in (("train", tr), ("val", va)):
        for h, (items, _) in data.items():
            m = M.motion_state(items)
            assert M.counts_by_l0(items, m) == sizes[split][h]["strata"], "stratum counts differ from the frozen sizes: %s %s" % (split, h)
            assert [[n, ids] for n, ids in M.make_cells(items, m, "E1" if split == "train" else "E2")] == sizes[split][h]["cells"], \
                "evaluation cells differ from the frozen sizes: %s %s" % (split, h)
    res["turning_share_by_speed_band"] = {}
    for split, data in (("train", tr), ("val", va)):
        it2 = data["h2s"][0]
        m2 = M.motion_state(it2)
        out_b = {}
        for gname, gi in (("car", 0), ("pedestrian", 1)):
            for lo, hi in ((1, 3), (3, 8), (8, 1e9)):
                sel = (it2["g"] == gi) & (m2 != 0) & (it2["spd"] >= lo) & (it2["spd"] < hi)
                out_b["%s|%g-%s m/s" % (gname, lo, "inf" if hi > 1e8 else "%g" % hi)] = [int(sel.sum()), float(np.mean(m2[sel] == 2)) if sel.any() else None]
        res["turning_share_by_speed_band"][split] = out_b
    for h in ("h2s", "h1s", "h4s"):
        (ti, trc), (vi, vrc) = tr[h], va[h]
        c1, c2 = cells_from(sizes["train"][h]["cells"]), cells_from(sizes["val"][h]["cells"])
        dec = h == "h2s"
        try:
            res["E1_" + h] = run_e1(ti, trc, {}, tr_names, tr_log, c1, "%s|E1|%s" % (a.tracker, h), B=B1_, refit_B=BR if dec else 0)
            res["E2_" + h] = run_e2(ti, trc, vi, vrc, {}, c2, "%s|E2|%s" % (a.tracker, h), B=B2_ if dec else B2s)
        except Exception as ex:
            if dec:
                raise
            res["E1_" + h] = res.get("E1_" + h) or {"error": "%s: %s" % (type(ex).__name__, ex)}
            res["E2_" + h] = {"error": "%s: %s" % (type(ex).__name__, ex), "hypotheses": {}}  # descriptive horizons: recorded, not fatal (R07c X-m9)
        print(h, "E1", json.dumps(res["E1_" + h].get("hypotheses", {}))[:900], "| E2", json.dumps(res["E2_" + h].get("hypotheses", {})),
              "| %.0f s" % (time.time() - t0), flush=True)
        save(h)
    ti, trc = tr["h2s"]
    sens = {}
    res["E5_h2s"] = sens

    def sens_run(name, fn):
        try:
            e = fn()
            sens[name] = {"fixed": compact(e["fixed"]), "pooled": e["pooled_fixed"]}
        except Exception as ex:  # recorded, not fatal (R07b N-m7)
            sens[name] = {"error": "%s: %s" % (type(ex).__name__, ex)}
        save("E5 " + name)
    for name, cfg in SENS.items():
        def fn(cfg=cfg, name=name):
            m = M.motion_state(ti, cfg.get("v_static", M.V_STATIC), cfg.get("w_turn", M.W_TURN), cfg.get("omega", "default"))
            return run_e1(ti, trc, cfg, tr_names, tr_log, M.make_cells(ti, m, "E1"), "%s|E5|%s" % (a.tracker, name), B=B1_)
        sens_run(name, fn)
    ci, cr = subset(ti, trc, ~ti["contested"], ~trc["contested"])
    sens_run("contested_excluded", lambda: run_e1(ci, cr, {}, tr_names, tr_log, M.make_cells(ci, M.motion_state(ci), "E1"),
                                                  "%s|E5|contested" % a.tracker, B=B1_))
    sens_run("scene_bootstrap", lambda: run_e1(ti, trc, {}, tr_names, tr_log, cells_from(sizes["train"]["h2s"]["cells"]),
                                               "%s|E5|scene_boot" % a.tracker, unit="scene", B=B1_))
    print("E5", {k: (v["fixed"]["methods"]["Mstar"]["any_sig_under"], v["fixed"]["methods"]["B6"]["any_sig_under"]) if "fixed" in v else v
                 for k, v in sens.items()}, flush=True)
    save("all")
    print("M RUN DONE", a.tracker, res["wall_s"], flush=True)


if __name__ == "__main__":
    sys.exit(main())
