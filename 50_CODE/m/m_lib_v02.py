#!/usr/bin/env python3
"""Method-stage library v02 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION_v03 sections 3-7.
Changes from v01 (review R07):
- Evaluation cells: unions of level-0 strata, built from counts (>= 39 scenes and >= 8 logs), with remainder cells.
- Paired contrasts of a baseline against M*.
- Upper bounds, NaN shares and bootstrap bias are reported.
- A zero-SE cell is flagged when its estimate exceeds delta.
- Two more baselines: B9 (norm-ball CRC, pooled) and B10 (stratified empirical quantile without the finite-sample term).
- Pedestrians' heading rate comes from their velocity direction.
- M-LS halves are split by original scene, also inside bootstrap replicates.
- A log-unit arm without a threshold no longer crashes the run.
- The deployable covariance uses max(c, 1e-3).
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
MIN_CELL_SCENES, MIN_CELL_LOGS = 39, 8
SEED = 20261031
B_BOOT = 2000      # E1 fixed-rule log bootstrap
B_E1R = 200        # E1 refit-CV log bootstrap (decision horizon only)
B_REFIT = 1000     # E2 two-sample refit log bootstrap
K_FOLDS = 5
R_CV = 20          # repetitions of the 5-fold log split (E1); results are averaged over them
V_STATIC = 1.0
W_TURN = 0.10
EPS_POOLED = 0.02  # HM6b tolerance on the pooled val exceedance
GROUPS, RANGES, AXES = L.GROUPS, L.RANGES, ["long", "lat"]
MOTIONS = ["static", "straight", "turning", "new"]
HSTEPS = {"h1s": 2, "h2s": 4, "h4s": 8}
N_L0 = 96
METHODS = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B6c", "B7", "B8", "B9", "B10", "Mstar", "MLS", "Mstar_log"]
PRACTITIONER = ("B1", "B4", "B9")          # NEES-guided, pooled conformal, norm-ball conformal
ABLATIONS = ("B5", "B7", "B8", "B10")      # per-axis, learned-scale marginal, variance matching, no finite-sample term
RATIOS = (("Mstar", "B3"), ("Mstar", "B6c"), ("Mstar", "B9"), ("MLS", "Mstar"), ("Mstar", "B7"), ("Mstar", "B6"),
          ("Mstar", "B2"), ("Mstar", "B8"), ("MLS", "B3"))


def decode(l0):
    l1, m = divmod(int(l0), 4)
    g, rem = divmod(l1, 6)
    r, a = divmod(rem, 2)
    return g, r, a, m


def l0_name(i):
    g, r, a, m = decode(i)
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
    """Flat item arrays (plan section 3) and per-record arrays for the NEES and norm-ball baselines. With outcomes=False no
    residual is computed (D and the record residuals are NaN): used for the pre-freeze counts. Also counts, per L0 stratum,
    the in-path items censored at the horizon (rows paired at k but not at k + h)."""
    sidx = {s: i for i, s in enumerate(scene_names)}
    logs = sorted(set(scene_log[s] for s in scene_names))
    lidx = {l: i for i, l in enumerate(logs)}
    it, rc = defaultdict(list), defaultdict(list)
    cens = defaultdict(list)
    for r in hrows:
        if not r["inpath"]:
            continue
        spd, om, omv = motion_features(mi, r["scene"], r["tid"], r["k"])
        g, rg, si = GROUPS.index(r["group"]), RANGES.index(r["range"]), sidx[r["scene"]]
        sxx, sxy, syy = r["S"]
        if not r["paired"]:
            for name, a, sep, hsum in L.axis_candidates(r):
                if abs(sep) > hsum:
                    for k_, v_ in (("g", g), ("r", rg), ("a", 0 if name == "long" else 1), ("spd", spd), ("om", om), ("omv", omv)):
                        cens[k_].append(v_)
            continue
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
    c = {k: np.asarray(v) for k, v in cens.items()}
    if c:
        for k in ("g", "r", "a"):
            c[k] = c[k].astype(int)
        lc = levels(c, motion_state(c))[0]
        items["censored_by_l0"] = np.bincount(lc, minlength=N_L0)
    else:
        items["censored_by_l0"] = np.zeros(N_L0, int)
    return items, recs


def omega_used(items, omega="default"):
    """Heading rate used for the motion state: yaw-based, except velocity-direction-based for pedestrians (default)."""
    if omega == "default":
        return np.where(items["g"] == 1, items["omv"], items["om"])
    return items[omega]


def motion_state(items, v_static=V_STATIC, w_turn=W_TURN, omega="default"):
    spd, om = items["spd"], omega_used(items, omega)
    m = np.where(spd < v_static, 0, np.where(~np.isfinite(om), 3, np.where(np.abs(np.nan_to_num(om)) >= w_turn, 2, 1)))
    return m.astype(int)


def levels(items, m):
    l1 = (items["g"] * 3 + items["r"]) * 2 + items["a"]
    return [l1 * 4 + m, l1, items["g"] * 2 + items["a"], items["a"].copy()]


def counts_by_l0(items, m):
    l0 = levels(items, m)[0]
    lg = items["scene_log_idx"][items["s"]]
    out = {}
    for c in range(N_L0):
        sel = l0 == c
        if sel.any():
            out[l0_name(c)] = {"items": int(sel.sum()), "scenes": int(len(np.unique(items["s"][sel]))), "logs": int(len(np.unique(lg[sel])))}
    return out


def _ok(items, l0, ids):
    sel = np.isin(l0, ids)
    if not sel.any():
        return False, 0, 0
    ns, nl = len(np.unique(items["s"][sel])), len(np.unique(items["scene_log_idx"][items["s"][sel]]))
    return ns >= MIN_CELL_SCENES and nl >= MIN_CELL_LOGS, ns, nl


def make_cells(items, m, kind):
    """Evaluation cells from counts only. kind 'E1': level-0 strata, then remainder per (group, axis), then per axis.
    kind 'E2' (val): (group, axis, motion) pooled over range, then each motion state pooled over groups, axes and ranges,
    then remainder per (group, axis), then per axis.
    A cell needs >= 39 scenes and >= 8 logs. Returns [(name, [l0 ids])]."""
    l0 = levels(items, m)[0]
    present = sorted(set(int(x) for x in np.unique(l0)))
    cells, used = [], set()
    if kind == "E1":
        first = [(l0_name(g), [g]) for g in present]
    else:
        first = []
        for g in range(4):
            for a in range(2):
                for mo in range(4):
                    ids = [x for x in present if decode(x)[0] == g and decode(x)[2] == a and decode(x)[3] == mo]
                    if ids:
                        first.append(("%s|all ranges|%s|%s" % (GROUPS[g], AXES[a], MOTIONS[mo]), ids))
    for name, ids in first:
        if _ok(items, l0, ids)[0]:
            cells.append((name, ids))
            used |= set(ids)
    if kind == "E2":  # val is small: pool what is left of each motion state over groups, axes and ranges (turning on val)
        for mo in range(4):
            ids = [x for x in present if x not in used and decode(x)[3] == mo]
            if ids and _ok(items, l0, ids)[0]:
                cells.append(("all groups|all ranges|both axes|%s" % MOTIONS[mo], ids))
                used |= set(ids)
    for g in range(4):
        for a in range(2):
            ids = [x for x in present if x not in used and decode(x)[0] == g and decode(x)[2] == a]
            if ids and _ok(items, l0, ids)[0]:
                cells.append(("%s|%s|remainder" % (GROUPS[g], AXES[a]), ids))
                used |= set(ids)
    for a in range(2):
        ids = [x for x in present if x not in used and decode(x)[2] == a]
        if ids and _ok(items, l0, ids)[0]:
            cells.append(("all groups|%s|remainder" % AXES[a], ids))
            used |= set(ids)
    return cells


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


def folds_by_original_log(items, seed, k=K_FOLDS):
    """Folds for a log-resampled split: every copy of one original log goes to the same fold (no copy is both calibration
    and test); original logs permuted with the seed and assigned greedily by their resampled scene load."""
    orig_of_scene = items["orig_log"][items["scene_log_idx"]]
    load_by = Counter(orig_of_scene.tolist())
    origs = sorted(load_by)
    load, fold_of = [0] * k, {}
    for i in np.random.default_rng(seed).permutation(len(origs)):
        f = int(np.argmin(load))
        fold_of[origs[i]] = f
        load[f] += load_by[origs[i]]
    return np.array([fold_of[o] for o in orig_of_scene.tolist()], int)


# ---------------------------------------------------------------- methods

def fit_hier(U, unit, lv, start=0, n_min=N_CRC, stat=None):
    """Threshold for every L0 stratum: own cell at the first level >= start with n_min units, else the next level.
    stat: replacement statistic of (U, unit) per cell; default the CRC threshold."""
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
    """Per-configuration derived arrays: motion state, levels, sd, U, record NEES and record error norm."""
    sa = cfg.get("sigma_a", SIGMA_A)
    omega = cfg.get("omega", "default")
    m = motion_state(items, cfg.get("v_static", V_STATIC), cfg.get("w_turn", W_TURN), omega)
    items["_om_used"] = omega_used(items, omega)
    sd = np.sqrt(items["V"] + sa ** 2)
    S11, S12, S22 = recs["sxx"] + sa ** 2, recs["sxy"], recs["syy"] + sa ** 2
    det = S11 * S22 - S12 ** 2
    nees = (S22 * recs["dx"] ** 2 - 2 * S12 * recs["dx"] * recs["dy"] + S11 * recs["dy"] ** 2) / det
    return {"m": m, "lv": levels(items, m), "sd": sd, "U": items["D"] / sd, "sa": sa, "nees": nees,
            "nrm": np.hypot(recs["dx"], recs["dy"])}


def fit_methods(items, recs, P, cal_scene, cfg):
    """Fit every method on the calibration scenes (boolean per scene index)."""
    n_min = cfg.get("n_min", N_CRC)
    cal = cal_scene[items["s"]]
    U, s, lg = P["U"][cal], items["s"][cal], items["lg"][cal]
    lv = [x[cal] for x in P["lv"]]
    fit = {}
    fit["Mstar"], fit["Mstar_src"] = fit_hier(U, s, lv, 0, n_min)
    fit["Mstar_log"], fit["Mstar_log_src"] = fit_hier(U, lg, lv, 0, N_CRC)  # the n_min sensitivity concerns scene units only
    fit["Mstar_log_incomplete"] = bool(np.isnan(fit["Mstar_log"]).any())
    if fit["Mstar_log_incomplete"]:  # fewer than 19 calibration logs even at L3 (not expected with real E1/E2 log counts)
        fit["Mstar_log"] = np.where(np.isnan(fit["Mstar_log"]), np.nanmax(fit["Mstar"]), fit["Mstar_log"])
    fit["B6"], fit["B6_src"] = fit_hier(U, s, lv, 1, n_min)
    fit["B5"], _ = fit_hier(U, s, lv, 3, n_min)
    fit["B8"], fit["B8_src"] = fit_hier(U, s, lv, 0, n_min, stat=lambda u, _unit: Z * math.sqrt(float(np.mean(u * u))))
    fit["B10"], _ = fit_hier(U, s, lv, 0, n_min, stat=lambda u, _unit: float(np.quantile(u, 1 - DELTA)))
    fit["B4"] = L.crc_threshold(U, s)
    fit["B3"] = float(np.nanmax(fit["Mstar"]))
    fit["B6c"] = np.array([np.nanmax(fit["Mstar"][(l0 // 4) * 4:(l0 // 4) * 4 + 4]) for l0 in range(N_L0)])
    # B1: NEES-guided k per group x range; B9: norm-ball radius, both on calibration records
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
    fit["B9"] = L.crc_threshold(P["nrm"][rcal], rs)
    # B2: largest needed variance factor over L1 cells
    D, V = items["D"][cal], items["V"][cal]
    SA = np.full(len(D), P["sa"])
    svals = []
    for c in np.unique(lv[1]):
        sel = lv[1] == c
        if len(np.unique(s[sel])) >= n_min:
            svals.append(L.inflation_needed(D[sel], V[sel], SA[sel])[0])
    fit["B2"] = max(svals)
    # B7 and M-LS: learned scale on a seeded half of the calibration scenes, split by original scene id
    orig = items.get("orig_scene", np.arange(items["n_scenes"]))
    cal_orig = np.unique(orig[cal_scene])
    perm = np.random.default_rng(SEED).permutation(cal_orig)
    fit_half = np.isin(orig, perm[: len(perm) // 2]) & cal_scene
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
           "B7": fit["B7"] * scale * sd, "B8": fit["B8"][l0] * sd, "B9": np.full(len(sd), fit["B9"]), "B10": fit["B10"][l0] * sd,
           "Mstar": fit["Mstar"][l0] * sd, "MLS": fit["MLS"][l0] * scale * sd, "Mstar_log": fit["Mstar_log"][l0] * sd}
    for k, v in out.items():
        assert np.all(np.isfinite(v)), "non-finite margin for " + k
    return out


def cv_once(items, recs, P, cfg, folds_scene):
    """One K-fold cross-validation: per item, the held-out exceedance indicator and margin of every method; the M*
    threshold source level per item."""
    n = len(items["D"])
    exc = {m: np.zeros(n) for m in METHODS}
    marg = {m: np.zeros(n) for m in METHODS}
    src = np.full(n, -1)
    for f in range(K_FOLDS):
        cal = folds_scene != f
        if cal.all():
            continue
        fit = fit_methods(items, recs, P, cal, cfg)
        sel = ~cal[items["s"]]
        for k, v in margins(items, P, fit, sel).items():
            exc[k][sel] = items["D"][sel] > v
            marg[k][sel] = v
        src[sel] = fit["Mstar_src"][P["lv"][0][sel]]
    return exc, marg, src


# ---------------------------------------------------------------- statistics

def boot_scene_weights(items, B, rng, unit="log"):
    if unit == "log":
        return L.log_cluster_weights(items["scene_log_idx"], items["n_logs"], B, rng)
    return L.boot_weights(items["n_scenes"], B, rng)


def resample_logs(items, recs, mult):
    """Log-cluster bootstrap copy of a split: log l enters mult[l] times; every copy of a scene (and of its log) gets
    its own id, so duplicated scenes count as distinct calibration units. Keeps the original scene and log of each copy."""
    sm = mult[items["scene_log_idx"]].astype(int)
    soff = np.concatenate([[0], np.cumsum(sm)[:-1]]).astype(int)
    loff = np.concatenate([[0], np.cumsum(mult)[:-1]]).astype(int)
    out = {"n_scenes": int(sm.sum()), "n_logs": int(mult.sum())}
    out["scene_log_idx"] = np.concatenate([loff[items["scene_log_idx"][i]] + np.arange(sm[i]) for i in range(len(sm))]).astype(int)
    out["orig_scene"] = np.repeat(np.arange(len(sm)), sm)
    out["orig_log"] = np.repeat(np.arange(len(mult)), mult.astype(int))

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


def _layout(items, P, cells, sel):
    if sel is None:
        sel = np.ones(len(items["D"]), bool)
    S = items["n_scenes"]
    s, l0, a, D = items["s"][sel], P["lv"][0][sel], items["a"][sel], items["D"][sel]
    cell_of = np.full(N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        cell_of[np.asarray(ids, int)] = j
    col = cell_of[l0]
    in_eval = col >= 0
    n_ig = np.zeros((S, len(cells)))
    np.add.at(n_ig, (s[in_eval], col[in_eval]), 1.0)
    return {"S": S, "sel": sel, "s": s, "l0": l0, "a": a, "D": D, "cells": cells, "col": col, "in_eval": in_eval,
            "n_ig": n_ig, "pres": (n_ig > 0).astype(float), "lg_of_scene": items["scene_log_idx"]}


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


def _point(lay, tab):
    with np.errstate(invalid="ignore", divide="ignore"):
        return (tab["p"].sum(0) / lay["pres"].sum(0), tab["msum"].sum() / tab["cnt"].sum(),
                [ms.sum() / cn.sum() for ms, cn in tab["ax"]])


def _boot_rows(lay, tab, W):
    with np.errstate(invalid="ignore", divide="ignore"):
        est = (W @ tab["p"]) / (W @ lay["pres"])
        mb = (W @ tab["msum"]) / (W @ tab["cnt"])
        ax = [(W @ ms) / (W @ cn) for ms, cn in tab["ax"]]
    return est, mb, ax


def _simul(est, boot, level, side):
    """One-sided simultaneous bounds with bootstrap SE: side 'lower' (for under-coverage) or 'upper'."""
    se = np.nanstd(boot, axis=0, ddof=1)
    ok = se > 0
    sgn = 1.0 if side == "lower" else -1.0
    with np.errstate(invalid="ignore", divide="ignore"):
        dev = np.where(ok, sgn * (boot - est) / np.where(ok, se, 1.0), np.nan)
        T = np.nanmax(dev, axis=1) if ok.any() else np.full(len(boot), np.nan)
    q = float(np.nanquantile(T, level)) if np.isfinite(T).any() else float("nan")
    bound = np.where(ok, est - sgn * q * se, est)
    return bound, se, q, ok


def _summary(lay, tabs, boots, delta=DELTA, level=0.95, pairs=()):
    """tabs: point tables per method; boots: per method (B x cells estimates, B margin means, [B axis margin means]).
    pairs: (numerator method, reference method, list of cell indices, label) for paired contrasts."""
    cells, n_ig, pres = lay["cells"], lay["n_ig"], lay["pres"]
    res = {}
    for meth, tab in tabs.items():
        boot, mb, axb = boots[meth]
        est, mpt, axpt = _point(lay, tab)
        lb, se, q, ok = _simul(est, boot, level, "lower")
        ub, _, qu, _ = _simul(est, boot, level, "upper")
        sig = (ok & (lb > delta)) | (~ok & (est > delta))
        nan_share = np.mean(~np.isfinite(boot), axis=0)
        full = nan_share == 0
        ebar_boot = np.nanmean(boot[:, full] if full.any() else boot, axis=1)
        rec_share = tab["e"].sum(0) / n_ig.sum(0)
        mg, ie = tab["mg"], lay["in_eval"]
        res[meth] = {
            "cells": {name: {"E_scene": float(est[j]), "E_rec": float(rec_share[j]), "lb_sim": float(lb[j]), "ub_sim": float(ub[j]),
                             "se": float(se[j]), "boot_bias": float(np.nanmean(boot[:, j]) - est[j]), "nan_share": float(nan_share[j]),
                             "sig_under": bool(sig[j]), "n_items": int(n_ig[:, j].sum()), "n_scenes": int(pres[:, j].sum()),
                             "n_logs": int(len(np.unique(lay["lg_of_scene"][pres[:, j] > 0]))),
                             "mean_margin_m": float(np.sum(mg[ie & (lay["col"] == j)]) / max(n_ig[:, j].sum(), 1))}
                      for j, (name, _) in enumerate(cells)},
            "q_lower": q, "q_upper": qu, "any_sig_under": bool(sig.any()), "sig_under_cells": [cells[j][0] for j in np.flatnonzero(sig)],
            "E_bar": float(np.mean(est[full] if full.any() else est)), "E_bar_ub95": float(np.nanquantile(ebar_boot, level)),
            "E_bar_cells": int(full.sum()), "max_E_scene": float(np.max(est)) if len(est) else float("nan"),
            "mean_margin_m": float(mpt), "mean_margin_ci": [float(x) for x in np.nanquantile(mb, [0.025, 0.975])],
            "mean_margin_by_axis": {AXES[i]: {"mean_margin_m": float(axpt[i]), "ci": [float(x) for x in np.nanquantile(axb[i], [0.025, 0.975])]}
                                    for i in (0, 1)}}
    ratios = {}
    for num, den in RATIOS:
        if num in tabs and den in tabs:
            rb = boots[num][1] / boots[den][1]
            ratios["%s/%s" % (num, den)] = {"point": res[num]["mean_margin_m"] / res[den]["mean_margin_m"],
                                            "ci": [float(x) for x in np.nanquantile(rb, [0.025, 0.975])]}
    paired = {}
    for num, den, fam, label in pairs:
        if num not in tabs or den not in tabs or not fam:
            continue
        fam = list(fam)
        e_n, e_d = _point(lay, tabs[num])[0][fam], _point(lay, tabs[den])[0][fam]
        dbo = boots[num][0][:, fam] - boots[den][0][:, fam]
        dlb, dse, dq, dok = _simul(e_n - e_d, dbo, level, "lower")
        pos = (dok & (dlb > 0)) | (~dok & (e_n - e_d > 0))
        paired[label] = {"q": dq, "cells": {cells[c][0]: {"diff": float(e_n[i] - e_d[i]), "lb_sim": float(dlb[i]), "positive": bool(pos[i])}
                                            for i, c in enumerate(fam)}}
    return {"methods": res, "ratios": ratios, "paired": paired, "cells": [c[0] for c in cells],
            "n_items_eval": int(lay["in_eval"].sum()), "n_boot": int(len(next(iter(boots.values()))[1]))}


def eval_stats(items, P, marg, cells, W, sel=None, delta=DELTA, level=0.95, exc_frac=None, pairs=()):
    """Fixed-rule inference: the fitted rules (or their repetition averages) are held fixed and scenes are reweighted by
    W, a (B, n_scenes) matrix of bootstrap scene weights shared by all methods. exc_frac: per-item exceedance fractions."""
    lay = _layout(items, P, cells, sel)
    tabs, boots = {}, {}
    for meth, mg in marg.items():
        mg = mg[lay["sel"]]
        exc = (lay["D"] > mg).astype(float) if exc_frac is None else exc_frac[meth][lay["sel"]]
        tabs[meth] = _tables(lay, mg, exc)
        boots[meth] = _boot_rows(lay, tabs[meth], W)
    return _summary(lay, tabs, boots, delta, level, pairs)


def eval_stats_replicates(items, P, marg_point, families, replicates, delta=DELTA, level=0.95, exc_point=None, pairs=None):
    """Refit inference for several cell families at once (dict name -> cells): replicates yields, per bootstrap
    replicate, (items_b, P_b, exc_b, marg_b, w_b): the replicate's evaluation items and derived arrays, per-item exceedance
    and margins of every method's refitted rule, and scene weights (None = 1). The point estimate uses marg_point (and
    exc_point if given) on the original items. pairs: dict family -> paired contrasts. Returns dict family -> summary."""
    pairs = pairs or {}
    lays = {f: _layout(items, P, cells, None) for f, cells in families.items()}
    tabs = {f: {} for f in families}
    for f, lay in lays.items():
        for m, mg in marg_point.items():
            exc = (lay["D"] > mg).astype(float) if exc_point is None else exc_point[m]
            tabs[f][m] = _tables(lay, mg, exc)
    acc = {f: {m: ([], [], [], []) for m in marg_point} for f in families}
    for it_b, P_b, exc_b, marg_b, w_b in replicates:
        w = np.ones(it_b["n_scenes"]) if w_b is None else w_b
        for f, cells in families.items():
            lay_b = _layout(it_b, P_b, cells, None)
            for m in marg_point:
                est, mb, ax = _boot_rows(lay_b, _tables(lay_b, marg_b[m], exc_b[m].astype(float)), w[None, :])
                acc[f][m][0].append(est[0])
                acc[f][m][1].append(mb[0])
                acc[f][m][2].append(ax[0][0])
                acc[f][m][3].append(ax[1][0])
    out = {}
    for f in families:
        boots = {m: (np.array(v[0]), np.array(v[1]), [np.array(v[2]), np.array(v[3])]) for m, v in acc[f].items()}
        out[f] = _summary(lays[f], tabs[f], boots, delta, level, pairs.get(f, ()))
    return out


# ---------------------------------------------------------------- hypotheses

def turning_family(cells):
    """Pre-specified HM3 family: evaluated single-stratum car cells whose motion state is turning."""
    return [j for j, (name, ids) in enumerate(cells) if len(ids) == 1 and decode(ids[0])[0] == 0 and decode(ids[0])[3] == 2]


def standard_pairs(cells):
    allc = list(range(len(cells)))
    pairs = [(b, "Mstar", allc, "%s-Mstar" % b) for b in PRACTITIONER + ABLATIONS]
    pairs.append(("B6", "Mstar", turning_family(cells), "B6-Mstar|car turning"))
    return pairs


def failures(st_list, b, label):
    """Cells where baseline b is significantly under-covered, M* is not, and the paired difference b - M* is significantly
    positive, in every inference of st_list."""
    out = None
    for st in st_list:
        pc = st["paired"].get(label, {}).get("cells", {})
        here = {c for c, v in pc.items() if v["positive"] and st["methods"][b]["cells"][c]["sig_under"]
                and not st["methods"]["Mstar"]["cells"][c]["sig_under"]}
        out = here if out is None else out & here
    return sorted(out or [])


def hypotheses_e1(st_fixed, st_refit):
    both = [st_fixed, st_refit]
    h = {"HM1": not any(st["methods"]["Mstar"]["any_sig_under"] for st in both),
         "Mstar_flagged_cells": sorted(set(c for st in both for c in st["methods"]["Mstar"]["sig_under_cells"]))}
    h["HM2"] = {b: failures(both, b, "%s-Mstar" % b) for b in PRACTITIONER}
    h["HM2_any"] = any(bool(v) for v in h["HM2"].values())
    h["HM2b"] = {b: failures(both, b, "%s-Mstar" % b) for b in ABLATIONS}
    h["HM3"] = failures(both, "B6", "B6-Mstar|car turning")
    h["HM3_holds"] = bool(h["HM3"])
    h["MLS_consistent"] = not any(st["methods"]["MLS"]["any_sig_under"] for st in both)
    h["Mstar_log_consistent"] = not any(st["methods"]["Mstar_log"]["any_sig_under"] for st in both)
    return h


def hypotheses_e2(st_cells, st_all, eps=EPS_POOLED):
    m, a = st_cells["methods"]["Mstar"], st_all["methods"]["Mstar"]["cells"]["all val items"]
    h = {"HM6a": not m["any_sig_under"], "HM6a_flagged": m["sig_under_cells"],
         "HM6b": a["ub_sim"] <= DELTA + eps, "pooled_E": a["E_scene"], "pooled_ub": a["ub_sim"], "eps": eps}
    h["HM6"] = bool(h["HM6a"] and h["HM6b"])
    ml = st_all["methods"]["MLS"]["cells"]["all val items"]
    h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] <= DELTA + eps)
    return h


def deploy_covariance(S, yaw, c_long, c_lat, sigma_a=SIGMA_A):
    """PM2: recalibrated xy covariance A (S + sa^2 I) A with A = (c_long/z) a_l a_l' + (c_lat/z) a_t a_t'; a threshold
    <= 0 is replaced by 1e-3 (P02 remark), which keeps validity because the loss is non-increasing in c."""
    al = np.array([math.cos(yaw), math.sin(yaw)])
    at = np.array([-math.sin(yaw), math.cos(yaw)])
    A = (max(c_long, 1e-3) / Z) * np.outer(al, al) + (max(c_lat, 1e-3) / Z) * np.outer(at, at)
    return A @ (np.asarray(S, float) + sigma_a ** 2 * np.eye(2)) @ A
