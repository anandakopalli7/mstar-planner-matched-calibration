#!/usr/bin/env python3
"""Method-stage library v01 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION sections 3-7:
items with motion-state features, DP-SCRC (M*) and its learned-scale variant (M-LS), baselines B0-B7 and B6c, the
log-disjoint folds, and the log-cluster bootstrap with one-sided simultaneous lower bounds.
Item construction reuses x1_lib_v03 (build_table, build_horizon_rows, axis_candidates, crc_threshold) unchanged.
Stratum ids: L1 = (group*3 + range)*2 + axis (0..23); L0 = L1*4 + motion (0..95); L2 = group*2 + axis; L3 = axis.
Motion: 0 static, 1 straight, 2 turning, 3 new.
"""
import gzip
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "x1"))
import x1_lib_v03 as L  # noqa: E402

DELTA = 0.05
Z = L.Z95
SIGMA_A = 0.10
N_CRC = 19
N_EVAL = 39
SEED = 20261031
B_BOOT = 2000
K_FOLDS = 5
R_CV = 20  # repetitions of the 5-fold log split (E1); results are averaged over them
B_REFIT = 1000  # E2: replicates of the two-sample log bootstrap that refits every rule on resampled train logs
V_STATIC = 1.0
W_TURN = 0.10
GROUPS, RANGES, AXES = L.GROUPS, L.RANGES, ["long", "lat"]
MOTIONS = ["static", "straight", "turning", "new"]
HSTEPS = {"h1s": 2, "h2s": 4, "h4s": 8}
N_L0 = 96
METHODS = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B6c", "B7", "B8", "Mstar", "MLS", "Mstar_log"]


def l0_name(i):
    l1, m = divmod(int(i), 4)
    g, rem = divmod(l1, 6)
    r, a = divmod(rem, 2)
    return "%s|%s|%s|%s" % (GROUPS[g], RANGES[r], AXES[a], MOTIONS[m])


def parents(l0):
    l1 = l0 // 4
    g, a = l1 // 6, l1 % 2
    return l1, g * 2 + a, a


def wrap_half(x):
    return (x + math.pi / 2) % math.pi - math.pi / 2


# ---------------------------------------------------------------- inputs

def load_horizon_all(path, keys):
    pred = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            key = (r["scene"], r["k"], r["tid"])
            if key in keys:
                pred[key] = {h: r[h] for h in HSTEPS}
    return pred


def motion_index(recs, samples):
    """(scene, tid, k) -> (yaw, velocity heading, time [s], speed) from the exported track estimates (I_k-measurable)."""
    ts = {(s["scene"], s["index"]): 1e-6 * s["timestamp"] for s in samples.values()}
    return {(r["scene"], r["tid"], r["k"]): (r["yaw"], math.atan2(r["vy"], r["vx"]), ts[(r["scene"], r["k"])], math.hypot(r["vx"], r["vy"]))
            for r in recs}


def motion_features(mi, scene, tid, k):
    yaw, vh, t, spd = mi[(scene, tid, k)]
    prev = mi.get((scene, tid, k - 2)) or mi.get((scene, tid, k - 1))
    if prev is None:
        return spd, float("nan"), float("nan")
    dt = t - prev[2]
    return spd, wrap_half(yaw - prev[0]) / dt, L.wrap(vh - prev[1]) / dt


def build_items(hrows, mi, scene_names, scene_log, outcomes=True):
    """Flat item arrays (section 3 of the plan) and per-record arrays for the NEES baseline. With outcomes=False no
    residual is computed (D and the record residuals are NaN): used for the pre-freeze counts."""
    sidx = {s: i for i, s in enumerate(scene_names)}
    logs = sorted(set(scene_log[s] for s in scene_names))
    lidx = {l: i for i, l in enumerate(logs)}
    it, rc = defaultdict(list), defaultdict(list)
    for r in hrows:
        if not (r["paired"] and r["inpath"]):
            continue
        spd, om, omv = motion_features(mi, r["scene"], r["tid"], r["k"])
        g, rg, si = GROUPS.index(r["group"]), RANGES.index(r["range"]), sidx[r["scene"]]
        sxx, sxy, syy = r["S"]
        dx, dy = (r["gx"] - r["mx"], r["gy"] - r["my"]) if outcomes else (float("nan"), float("nan"))
        for k_, v_ in (("s", si), ("g", g), ("r", rg), ("dx", dx), ("dy", dy), ("sxx", sxx), ("sxy", sxy), ("syy", syy),
                       ("contested", bool(r.get("contested")))):
            rc[k_].append(v_)
        for name, a, sep, hsum in L.axis_candidates(r):
            if abs(sep) <= hsum:
                continue
            var = a[0] * a[0] * sxx + 2 * a[0] * a[1] * sxy + a[1] * a[1] * syy
            sign = 1.0 if sep >= 0 else -1.0
            for k_, v_ in (("s", si), ("lg", lidx[scene_log[r["scene"]]]), ("g", g), ("r", rg), ("a", 0 if name == "long" else 1),
                           ("spd", spd), ("om", om), ("omv", omv), ("V", var), ("contested", bool(r.get("contested"))),
                           ("D", sign * (a[0] * dx + a[1] * dy))):
                it[k_].append(v_)
    items = {k: np.asarray(v) for k, v in it.items()}
    recs = {k: np.asarray(v) for k, v in rc.items()}
    for d, ks in ((items, ("s", "lg", "g", "r", "a")), (recs, ("s", "g", "r"))):
        for k in ks:
            if k in d:
                d[k] = d[k].astype(int)
    items["scene_log_idx"] = np.array([lidx[scene_log[s]] for s in scene_names], int)
    items["n_scenes"], items["n_logs"] = len(scene_names), len(logs)
    return items, recs


def motion_state(items, v_static=V_STATIC, w_turn=W_TURN, omega="om"):
    spd, om = items["spd"], items[omega]
    m = np.where(spd < v_static, 0, np.where(~np.isfinite(om), 3, np.where(np.abs(np.nan_to_num(om)) >= w_turn, 2, 1)))
    return m.astype(int)


def levels(items, m):
    l1 = (items["g"] * 3 + items["r"]) * 2 + items["a"]
    return [l1 * 4 + m, l1, items["g"] * 2 + items["a"], items["a"].copy()]


def counts_by_l0(items, m):
    l0 = levels(items, m)[0]
    out = {}
    for c in range(N_L0):
        sel = l0 == c
        if sel.any():
            out[l0_name(c)] = {"items": int(sel.sum()), "scenes": int(len(np.unique(items["s"][sel])))}
    return out


def log_folds(scene_names, scene_log, k=K_FOLDS, seed=SEED):
    """Logs permuted with the seed, then assigned in that order to the fold with the fewest scenes so far."""
    logs = sorted(set(scene_log[s] for s in scene_names))
    cnt = Counter(scene_log[s] for s in scene_names)
    load, fold_of = [0] * k, {}
    for i in np.random.default_rng(seed).permutation(len(logs)):
        f = int(np.argmin(load))
        fold_of[logs[i]] = f
        load[f] += cnt[logs[i]]
    return np.array([fold_of[scene_log[s]] for s in scene_names], int), load


# ---------------------------------------------------------------- methods

def fit_hier(U, unit, lv, start=0, n_min=N_CRC, stat=None):
    """CRC threshold for every L0 stratum: own cell at the first level >= start with n_min units, else the next level.
    stat: optional replacement statistic of (U, unit) per cell (B8 uses the multiplier z sqrt(mean U^2))."""
    stat = stat or L.crc_threshold
    thr = [dict() for _ in range(4)]
    for level in range(start, 4):
        ids = lv[level]
        for c in np.unique(ids):
            sel = ids == c
            n = len(np.unique(unit[sel]))
            if n >= n_min:
                thr[level][int(c)] = (stat(U[sel], unit[sel]), n)
    out, src = np.full(N_L0, np.nan), np.full(N_L0, -1)
    for l0 in range(N_L0):
        keys = (l0,) + parents(l0)
        for level in range(start, 4):
            if keys[level] in thr[level]:
                out[l0], src[l0] = thr[level][keys[level]][0], level
                break
    return out, src


def phi(items, m, sd, sel):
    lat = items["a"][sel].astype(float)
    mm, g, r = m[sel], items["g"][sel], items["r"][sel]
    st, tu, nw = (mm == 0).astype(float), (mm == 2).astype(float), (mm == 3).astype(float)
    om_raw = items["_om_used"][sel]
    om = np.where(np.isfinite(om_raw) & (mm != 0), np.minimum(np.abs(np.nan_to_num(om_raw)), 0.5), 0.0)
    cols = [np.ones_like(lat), lat, st, tu, nw, lat * st, lat * tu, lat * nw, (g == 1) * 1.0, (g == 2) * 1.0, (g == 3) * 1.0,
            (r == 1) * 1.0, (r == 2) * 1.0, np.log(sd[sel]), np.minimum(items["spd"][sel], 20.0), om * (1 - lat), om * lat]
    return np.column_stack(cols)


def prepare(items, recs, cfg):
    """Per-configuration derived arrays: motion state, levels, sd, U, record NEES."""
    sa = cfg.get("sigma_a", SIGMA_A)
    m = motion_state(items, cfg.get("v_static", V_STATIC), cfg.get("w_turn", W_TURN), cfg.get("omega", "om"))
    items["_om_used"] = items[cfg.get("omega", "om")]
    sd = np.sqrt(items["V"] + sa ** 2)
    S11, S12, S22 = recs["sxx"] + sa ** 2, recs["sxy"], recs["syy"] + sa ** 2
    det = S11 * S22 - S12 ** 2
    nees = (S22 * recs["dx"] ** 2 - 2 * S12 * recs["dx"] * recs["dy"] + S11 * recs["dy"] ** 2) / det
    return {"m": m, "lv": levels(items, m), "sd": sd, "U": items["D"] / sd, "sa": sa, "nees": nees}


def fit_methods(items, recs, P, cal_scene, cfg):
    """Fit every method on the calibration scenes (boolean per scene index)."""
    n_min = cfg.get("n_min", N_CRC)
    cal = cal_scene[items["s"]]
    U, s, lg = P["U"][cal], items["s"][cal], items["lg"][cal]
    lv = [x[cal] for x in P["lv"]]
    fit = {}
    fit["Mstar"], fit["Mstar_src"] = fit_hier(U, s, lv, 0, n_min)
    fit["Mstar_log"], fit["Mstar_log_src"] = fit_hier(U, lg, lv, 0, N_CRC)  # the n_min sensitivity concerns scene units only
    fit["B6"], fit["B6_src"] = fit_hier(U, s, lv, 1, n_min)
    fit["B5"], _ = fit_hier(U, s, lv, 3, n_min)
    fit["B8"], fit["B8_src"] = fit_hier(U, s, lv, 0, n_min, stat=lambda u, _unit: Z * math.sqrt(float(np.mean(u * u))))
    fit["B4"] = L.crc_threshold(U, s)
    fit["B3"] = float(np.nanmax(fit["Mstar"]))
    fit["B6c"] = np.array([np.nanmax(fit["Mstar"][(l0 // 4) * 4:(l0 // 4) * 4 + 4]) for l0 in range(N_L0)])
    # B1: NEES-guided k per group x range
    rcal = cal_scene[recs["s"]]
    ne, rs, rg, rr = P["nees"][rcal], recs["s"][rcal], recs["g"][rcal], recs["r"][rcal]
    kg = float(np.mean(ne)) / 2.0
    fit["B1_k"] = {"global": kg}
    kk = np.full(12, kg)
    for g in range(4):
        for r in range(3):
            sel = (rg == g) & (rr == r)
            if sel.any() and len(np.unique(rs[sel])) >= n_min:
                kk[g * 3 + r] = float(np.mean(ne[sel])) / 2.0
                fit["B1_k"]["%s|%s" % (GROUPS[g], RANGES[r])] = kk[g * 3 + r]
    fit["B1"] = kk
    # B2: largest needed variance factor over L1 cells
    D, V = items["D"][cal], items["V"][cal]
    SA = np.full(len(D), P["sa"])
    svals = []
    for c in np.unique(lv[1]):
        sel = lv[1] == c
        if len(np.unique(s[sel])) >= n_min:
            svals.append(L.inflation_needed(D[sel], V[sel], SA[sel])[0])
    fit["B2"] = max(svals)
    # B7 and M-LS: learned scale on a seeded half of the calibration scenes
    cal_ids = np.flatnonzero(cal_scene)
    perm = np.random.default_rng(SEED).permutation(cal_ids)
    fit_half = np.zeros_like(cal_scene)
    fit_half[perm[: len(perm) // 2]] = True
    fsel = cal & fit_half[items["s"]]
    csel = cal & ~fit_half[items["s"]]
    X = phi(items, P["m"], P["sd"], fsel)
    y = np.log(np.maximum(np.abs(P["U"][fsel]), 0.05))
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    fit["scale_beta"] = beta
    Uc = P["U"][csel] / np.exp(phi(items, P["m"], P["sd"], csel) @ beta)
    fit["B7"] = L.crc_threshold(Uc, items["s"][csel])
    fit["MLS"], fit["MLS_src"] = fit_hier(Uc, items["s"][csel], [x[csel] for x in P["lv"]], 0, n_min)
    return fit


def margins(items, P, fit, sel):
    """Margin (m) of every method for the selected items."""
    sd, l0 = P["sd"][sel], P["lv"][0][sel]
    g, r, V = items["g"][sel], items["r"][sel], items["V"][sel]
    scale = np.exp(phi(items, P["m"], P["sd"], sel) @ fit["scale_beta"])
    out = {"B0": Z * sd, "B1": Z * np.sqrt(fit["B1"][g * 3 + r]) * sd, "B2": Z * np.sqrt(fit["B2"] * V + P["sa"] ** 2),
           "B3": fit["B3"] * sd, "B4": fit["B4"] * sd, "B5": fit["B5"][l0] * sd, "B6": fit["B6"][l0] * sd, "B6c": fit["B6c"][l0] * sd,
           "B7": fit["B7"] * scale * sd, "Mstar": fit["Mstar"][l0] * sd, "MLS": fit["MLS"][l0] * scale * sd,
           "Mstar_log": fit["Mstar_log"][l0] * sd, "B8": fit["B8"][l0] * sd}
    for k, v in out.items():
        assert np.all(np.isfinite(v)), "non-finite margin for " + k
    return out


# ---------------------------------------------------------------- statistics

def boot_scene_weights(items, B, rng, unit="log"):
    if unit == "log":
        return L.log_cluster_weights(items["scene_log_idx"], items["n_logs"], B, rng)
    return L.boot_weights(items["n_scenes"], B, rng)


def resample_logs(items, recs, mult):
    """Log-cluster bootstrap copy of a split: log l enters mult[l] times; every copy of a scene (and of its log) gets
    its own id, so duplicated scenes count as distinct calibration units."""
    sm = mult[items["scene_log_idx"]].astype(int)
    soff = np.concatenate([[0], np.cumsum(sm)[:-1]]).astype(int)
    loff = np.concatenate([[0], np.cumsum(mult)[:-1]]).astype(int)
    out = {"n_scenes": int(sm.sum()), "n_logs": int(mult.sum())}
    out["scene_log_idx"] = np.concatenate([loff[items["scene_log_idx"][i]] + np.arange(sm[i]) for i in range(len(sm))]).astype(int)

    def rep(sidx):
        r = sm[sidx]
        idx = np.repeat(np.arange(len(sidx)), r)
        copy = np.arange(len(idx)) - np.repeat(np.cumsum(r) - r, r)
        return idx, copy
    idx, copy = rep(items["s"])
    for k in ("g", "r", "a", "spd", "om", "omv", "V", "contested", "D"):
        out[k] = items[k][idx]
    out["s"] = soff[items["s"][idx]] + copy
    out["lg"] = loff[items["lg"][idx]] + copy
    ridx, rcopy = rep(recs["s"])
    rc = {k: recs[k][ridx] for k in ("g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")}
    rc["s"] = soff[recs["s"][ridx]] + rcopy
    return out, rc


def _layout(items, P, eval_strata, sel):
    if sel is None:
        sel = np.ones(len(items["D"]), bool)
    S = items["n_scenes"]
    s, l0, a, D = items["s"][sel], P["lv"][0][sel], items["a"][sel], items["D"][sel]
    G = list(eval_strata)
    gpos = {g: j for j, g in enumerate(G)}
    in_eval = np.isin(l0, G)
    col = np.array([gpos.get(int(x), -1) for x in l0])
    n_ig = np.zeros((S, len(G)))
    np.add.at(n_ig, (s[in_eval], col[in_eval]), 1.0)
    return {"S": S, "sel": sel, "s": s, "l0": l0, "a": a, "D": D, "G": G, "col": col, "in_eval": in_eval, "n_ig": n_ig,
            "pres": (n_ig > 0).astype(float)}


def _tables(lay, mg, exc):
    S, s, ie, col, n_ig = lay["S"], lay["s"], lay["in_eval"], lay["col"], lay["n_ig"]
    e_ig = np.zeros_like(n_ig)
    np.add.at(e_ig, (s[ie], col[ie]), exc[ie])
    tab = {"e": e_ig, "p": np.divide(e_ig, n_ig, out=np.zeros_like(e_ig), where=n_ig > 0), "mg": mg,
           "msum": np.bincount(s[ie], weights=mg[ie], minlength=S), "cnt": np.bincount(s[ie], minlength=S).astype(float), "ax": []}
    for ax in (0, 1):
        k = ie & (lay["a"] == ax)
        tab["ax"].append((np.bincount(s[k], weights=mg[k], minlength=S), np.bincount(s[k], minlength=S).astype(float)))
    return tab


def _boot_rows(lay, tab, W):
    with np.errstate(invalid="ignore", divide="ignore"):
        est = (W @ tab["p"]) / (W @ lay["pres"])
        mb = (W @ tab["msum"]) / (W @ tab["cnt"])
        ax = [(W @ ms) / (W @ cn) for ms, cn in tab["ax"]]
    return est, mb, ax


def _summary(lay, tabs, boots, delta, level):
    G, n_ig, pres = lay["G"], lay["n_ig"], lay["pres"]
    res = {}
    for meth, tab in tabs.items():
        boot, mb, axb = boots[meth]
        est = tab["p"].sum(0) / pres.sum(0)
        se = np.nanstd(boot, axis=0, ddof=1)
        ok = se > 0
        with np.errstate(invalid="ignore", divide="ignore"):
            T = np.nanmax(np.where(ok, (boot - est) / np.where(ok, se, 1.0), np.nan), axis=1) if ok.any() else np.full(len(boot), np.nan)
        q = float(np.nanquantile(T, level)) if np.isfinite(T).any() else float("nan")
        lb = np.where(ok, est - q * se, est)
        sig = ok & (lb > delta)
        rec_share = tab["e"].sum(0) / n_ig.sum(0)
        mg, ie = tab["mg"], lay["in_eval"]
        by_axis = {AXES[i]: {"mean_margin_m": float(tab["ax"][i][0].sum() / tab["ax"][i][1].sum()),
                             "ci": [float(x) for x in np.nanquantile(axb[i], [0.025, 0.975])]} for i in (0, 1)}
        res[meth] = {
            "strata": {l0_name(g): {"E_scene": float(est[j]), "E_rec": float(rec_share[j]), "lb_sim": float(lb[j]), "se": float(se[j]),
                                    "sig_under": bool(sig[j]), "n_items": int(n_ig[:, j].sum()), "n_scenes": int(pres[:, j].sum()),
                                    "mean_margin_m": float(np.sum(mg[ie & (lay["l0"] == g)]) / max(n_ig[:, j].sum(), 1))}
                       for j, g in enumerate(G)},
            "q_sim": q, "any_sig_under": bool(sig.any()), "sig_under_strata": [l0_name(G[j]) for j in np.flatnonzero(sig)],
            "E_bar": float(np.mean(est)), "E_bar_ub95": float(np.nanquantile(np.nanmean(boot, axis=1), level)),
            "max_E_scene": float(np.max(est)),
            "mean_margin_m": float(tab["msum"].sum() / tab["cnt"].sum()), "mean_margin_ci": [float(x) for x in np.nanquantile(mb, [0.025, 0.975])],
            "mean_margin_by_axis": by_axis}
    ratios = {}
    for num, den in (("Mstar", "B3"), ("Mstar", "B6c"), ("MLS", "Mstar"), ("Mstar", "B7"), ("Mstar", "B6"), ("Mstar", "B2"), ("MLS", "B3"), ("Mstar", "B8")):
        if num in tabs and den in tabs:
            rb = boots[num][1] / boots[den][1]
            ratios["%s/%s" % (num, den)] = {"point": res[num]["mean_margin_m"] / res[den]["mean_margin_m"],
                                            "ci": [float(x) for x in np.nanquantile(rb, [0.025, 0.975])]}
    return {"methods": res, "ratios": ratios, "evaluated_strata": [l0_name(g) for g in G], "n_items_eval": int(lay["in_eval"].sum()),
            "n_boot": int(len(next(iter(boots.values()))[1]))}


def eval_stats(items, P, marg, eval_strata, W, sel=None, delta=DELTA, level=0.95, exc_frac=None):
    """Exceedance (scene mean, primary; record share), one-sided simultaneous lower bounds, mean-exceedance upper bound,
    and mean margins with paired bootstrap ratios, the fitted rules held fixed. W: (B, n_scenes) bootstrap scene weights
    shared by all methods. exc_frac: optional per-item exceedance fractions (average over repeated fits)."""
    lay = _layout(items, P, eval_strata, sel)
    tabs, boots = {}, {}
    for meth, mg in marg.items():
        mg = mg[lay["sel"]]
        exc = (lay["D"] > mg).astype(float) if exc_frac is None else exc_frac[meth][lay["sel"]]
        tabs[meth] = _tables(lay, mg, exc)
        boots[meth] = _boot_rows(lay, tabs[meth], W)
    return _summary(lay, tabs, boots, delta, level)


def eval_stats_refit(items, P, marg_point, eval_strata, replicates, delta=DELTA, level=0.95):
    """As eval_stats, but every bootstrap replicate refits every rule: replicates yields (margins of the replicate's
    refitted rules on all evaluation items, the replicate's evaluation scene weights). The point estimate uses marg_point."""
    lay = _layout(items, P, eval_strata, None)
    tabs = {m: _tables(lay, mg, (lay["D"] > mg).astype(float)) for m, mg in marg_point.items()}
    acc = {m: ([], [], [], []) for m in marg_point}
    for marg_b, w_b in replicates:
        for m, mg in marg_b.items():
            est, mb, ax = _boot_rows(lay, _tables(lay, mg, (lay["D"] > mg).astype(float)), w_b[None, :])
            acc[m][0].append(est[0])
            acc[m][1].append(mb[0])
            acc[m][2].append(ax[0][0])
            acc[m][3].append(ax[1][0])
    boots = {m: (np.array(v[0]), np.array(v[1]), [np.array(v[2]), np.array(v[3])]) for m, v in acc.items()}
    return _summary(lay, tabs, boots, delta, level)


def hypotheses(st, delta=DELTA, ub_margin=0.02):
    m = st["methods"]
    h = {"HM1a": not m["Mstar"]["any_sig_under"], "HM1b": m["Mstar"]["E_bar_ub95"] <= delta + ub_margin}
    h["HM1"] = bool(h["HM1a"] and h["HM1b"])
    h["HM2"] = {b: m[b]["any_sig_under"] for b in ("B0", "B1", "B4")}
    h["HM2_count"] = int(sum(h["HM2"].values()))
    h["HM2b"] = m["B5"]["any_sig_under"]
    h["HM3"] = m["B6"]["any_sig_under"]
    h["HM3b"] = m["B7"]["any_sig_under"]
    h["HM2c"] = m["B8"]["any_sig_under"]
    h["MLS_HM1"] = bool((not m["MLS"]["any_sig_under"]) and m["MLS"]["E_bar_ub95"] <= delta + ub_margin)
    h["Mstar_log_HM1"] = bool((not m["Mstar_log"]["any_sig_under"]) and m["Mstar_log"]["E_bar_ub95"] <= delta + ub_margin)
    h["ub_margin"] = ub_margin
    return h


def deploy_covariance(S, yaw, c_long, c_lat, sigma_a=SIGMA_A):
    """PM2: recalibrated xy covariance A (S + sa^2 I) A with A = (c_long/z) a_l a_l' + (c_lat/z) a_t a_t'."""
    al = np.array([math.cos(yaw), math.sin(yaw)])
    at = np.array([-math.sin(yaw), math.cos(yaw)])
    A = (c_long / Z) * np.outer(al, al) + (c_lat / Z) * np.outer(at, at)
    return A @ (np.asarray(S, float) + sigma_a ** 2 * np.eye(2)) @ A
