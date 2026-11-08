#!/usr/bin/env python3
"""X3 stats agent (x3-stats), common library v01 (7 Nov 2026) for X3 analyses (c), (f) and (h).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md (sha256 38e2526d...), sections 0, 2(c), 2(f), 2(h).
Imports, read-only: the R21 re-derivation library 70_TESTS/R21_c1_v01/r21_lib_v01.py (standalone numpy; it reproduced the analysis of
record exactly: same weights, same sup-t rule, same estimator). Nothing from 50_CODE/c1_av2, k8 or av2 is imported here, so no guarded
entry point can run. Importing this module has no side effect beyond setting single-thread BLAS variables (done by r21_lib_v01).

What it adds to R21's library:
  * interval methods (ii) studentised log bootstrap with an SE floor and (iii) the design-effect Wilson interval;
  * the ANOVA intraclass correlation across logs per cell (also used for the SE floor and the simulation of (c2));
  * the four disjoint record blocks of the counts (far/near x not-in-path/in-path), whose sums are the three populations;
  * output helpers: new-file-only JSON writer, the live progress line, the stamp.
"""
import json
import math
import os
import statistics
import sys
import time

import numpy as np

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
sys.path.insert(0, os.path.join(W, "70_TESTS", "R21_c1_v01"))
import r21_lib_v01 as L  # noqa: E402

STAMP = "X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)"
PLAN = os.path.join(W, "20_DESIGN", "X3_POSTREG_EXPLORATORY_PLAN_v01.md")
PLAN_SHA = "38e2526d9f43f202fe4c8fe345be03d21421d6c7ada585022abf34a649362dc6"
REC = os.path.join(W, "60_RESULTS", "c1_av2_v01")
RUNS = os.path.join(REC, "runs")
ANALYSIS = os.path.join(REC, "c1_analysis_r1.json")
DECISION = os.path.join(REC, "c1_decision_r1.json")
CSV_DIR = os.path.join(REC, "c1_analysis_csv_r1")
ITEMS_DIR = os.path.join(REC, "items")
FITS_DIR = os.path.join(REC, "fits")
CACHE_DIR = os.path.join(W, "30_DATA")
OUT = os.path.join(W, "60_RESULTS", "x3_explore_v01")
LIVE = os.path.join(W, "00_PROGRESS", "live", "x3_stats.txt")
ROUTE = "within_lt3d"
TRACKER_I = {"t1": 0, "t3": 1, "tab": 2}
TRACKER_NAME = {"t1": "T1 (CANMOT)", "t3": "T3 (Poly-MOT)", "tab": "AB3DMOT (tab, descriptive)"}
SEED_X3_BOOT = 20261201          # plan section 0: bootstrap [20261201, i, j]
J_C = 3                          # analysis (c)
B_X3 = 4000                      # plan section 0
B_REC = 40000                    # B of record
SEED_REC_BOOT = 20261110         # the record's bootstrap seed [20261110, i, route index 0] (c1_analysis_r1.json seeds)
DELTA = L.DELTA
LEVEL_M = L.LEVEL_M              # 0.95
LEVEL_RM = L.LEVEL_RM            # 1 - 0.0125/9
L_HK1C, HK1C_MARGIN = L.L_HK1C, L.HK1C_MARGIN
POPS = L.POPS
CELLNAMES = L.CELLNAMES
COMPS = L.COMPS
_ND = statistics.NormalDist()


def tag_of(t):
    return "%s_%s_decide" % (t, ROUTE)


def fits_path(t):
    return os.path.join(FITS_DIR, "fits_within_%s.json" % t)


def sha256(p):
    return L.sha256(p)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def live(step, done, total, note=""):
    """The one-line live progress file (rewritten at each milestone)."""
    line = "%s | x3-stats | %s | %s/%s%s\n" % (now(), step, done, total, (" | " + note) if note else "")
    tmp = LIVE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(line)
        os.replace(tmp, LIVE)
    except OSError:
        pass


def jdump_new(path, obj):
    """Write a NEW json file (refuses to overwrite)."""
    if os.path.exists(path):
        raise FileExistsError("refusing to overwrite " + path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=L._jdefault)
    os.replace(tmp, path)


def text_new(path, text):
    if os.path.exists(path):
        raise FileExistsError("refusing to overwrite " + path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def fnum(x, nd=None):
    x = L.fnum(x)
    return None if x is None else (round(x, nd) if nd else x)


# ------------------------------------------------------------------ the record (read-only extracts)
def load_record_extract(trackers=("t1", "t3", "tab")):
    """The parts of c1_analysis_r1.json used by (c), (f), (h): families, validity entries, statuses, RETUNED selection, V_t."""
    with open(ANALYSIS, encoding="utf-8") as f:
        an = json.load(f)
    out = {"analysis_sha256": sha256(ANALYSIS), "trackers": {}}
    for t in trackers:
        k8 = an["k8"][ROUTE].get(t)
        c1 = an["c1"][ROUTE].get(t)
        if k8 is None:
            continue
        vba = k8["validity_by_arm"]
        rec = {"seeds": c1.get("seeds"), "status": c1.get("status"), "form_b": c1.get("form_b"),
               "infeasible_rate": c1.get("infeasible_rate"), "retune_arm_of_scene": k8["retune"].get("arm_of_scene"),
               "retune_arm_of_fold": k8["retune"].get("arm_of_fold"), "validity": {}, "families": {},
               "RETUNED_HK1": c1.get("RETUNED_HK1"), "k8_infeasible_rate": k8.get("infeasible_rate"), "V2": k8.get("V2"),
               "sweep": k8.get("sweep"), "endpoints_by_arm": k8.get("endpoints_by_arm"),
               "fallback_strata_fits_entries": k8.get("fallback_strata_fits_entries"),
               "A13_fallback_record_weighted": k8.get("A13_fallback_record_weighted"), "arms": k8.get("arms")}
        for arm, v in vba.items():
            rec["validity"][arm] = v
            rec["families"][arm] = {p: list((v["pops"].get(p) or {}).get("family") or []) for p in POPS}
        rec["Mstar_desc_ub"] = (c1["status"]["Mstar"].get("descriptive_simultaneous_ub_0.95") or {}).get("pops")
        out["trackers"][t] = rec
    del an
    return out


# ------------------------------------------------------------------ data
def load_data(t):
    d = L.RouteData(RUNS, tag_of(t), t, fits_path=fits_path(t))
    d.select_retuned()
    return d


def block_tables(data, arms):
    """N and X per (arm row, unit, cell, block) for the four disjoint blocks of the base (relied, satisfied, enforced, offset 0)
    records: 0 far & not in-path, 1 far & in-path, 2 near & not in-path, 3 near & in-path ('near' = pair gap <= 5 m). The decoding
    is R21's (r21_lib_v01.RouteData), whose population sums the analysis reproduced exactly: PD7 = all four blocks, SD1_7 = 2 + 3,
    PD = 1 + 3. Returns {arm: (N (U, 32, 4), X (U, 32, 4))} with the RETUNED composite per unit."""
    zc = np.load(data.files["counts"])
    cep = zc["episode"].astype(np.int64)
    maxep = len(data.ep_arm)
    okc = cep < maxep
    okc[okc] = data.ep_arm[cep[okc]] >= 0
    cep = cep[okc]
    cell = zc["cell"][okc].astype(np.int64)
    cn = zc["n"][okc].astype(np.float64)
    cx = zc["exceed"][okc].astype(np.float64)
    del zc, okc
    l0 = cell % 96
    col = (l0 // 24) * 8 + ((l0 // 4) % 2) * 4 + (l0 % 4)
    rest = cell // 96
    base = (rest % 8) < 4
    rest //= 8
    base &= (rest % 2) == 1
    rest //= 2
    near = (rest % 3) <= 1
    rest //= 3
    base &= (rest % 2) == 1
    rest //= 2
    base &= (rest % 2) == 1
    rest //= 2
    inpath = (rest % 2) == 1
    base &= (rest // 2) == 0
    blk = near.astype(np.int64) * 2 + inpath.astype(np.int64)
    A, U = len(data.arms), data.U
    m = base
    carm, cun = data.ep_arm[cep[m]].astype(np.int64), data.ep_unit[cep[m]].astype(np.int64)
    idx = ((carm * U + cun) * 32 + col[m]) * 4 + blk[m]
    Nall = np.bincount(idx, weights=cn[m], minlength=A * U * 32 * 4).reshape(A, U, 32, 4)
    Xall = np.bincount(idx, weights=cx[m], minlength=A * U * 32 * 4).reshape(A, U, 32, 4)
    del cep, cell, cn, cx, l0, col, rest, base, near, inpath, blk, carm, cun, idx
    out = {}
    u = np.arange(U)
    for a in arms:
        r = data.arm_rows(a)
        out[a] = (Nall[r, u].copy(), Xall[r, u].copy())
    del Nall, Xall
    return out


POP_BLOCKS4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3)}


def pop_from_blocks(Nb, pop):
    return Nb[:, :, list(POP_BLOCKS4[pop])].sum(2)


# ------------------------------------------------------------------ ANOVA intraclass correlation across logs (per column)
def icc_from_sums(k, n_tot, x_tot, a_sum, q_sum):
    """One-way ANOVA ICC for binary records clustered in logs, from sums over the logs with records:
    k logs, n_tot records, x_tot exceedances, a_sum = sum_u x_u^2 / n_u, q_sum = sum_u n_u^2.
    MSB = (a - x^2/n) / (k - 1); MSW = (x - a) / (n - k); n0 = (n - q/n) / (k - 1); rho = (MSB - MSW) / (MSB + (n0 - 1) MSW),
    truncated to [0, 1]; 0 where undefined (k < 2, no exceedance, or a zero denominator). Arrays broadcast."""
    k = np.asarray(k, np.float64)
    n_tot = np.asarray(n_tot, np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        msb = (a_sum - x_tot ** 2 / n_tot) / (k - 1.0)
        msw = np.where(n_tot - k > 0, (x_tot - a_sum) / (n_tot - k), 0.0)
        n0 = (n_tot - q_sum / n_tot) / (k - 1.0)
        den = msb + (n0 - 1.0) * msw
        rho = np.where(np.isfinite(den) & (den > 0), (msb - msw) / den, 0.0)
    rho = np.where(np.isfinite(rho), rho, 0.0)
    return np.clip(rho, 0.0, 1.0)


def cell_sums(N, X):
    """Per column: k (logs with records), n_tot, x_tot, a = sum x^2/n, q = sum n^2; N, X (U, J)."""
    pres = N > 0
    a = np.divide(X * X, N, out=np.zeros_like(X, dtype=np.float64), where=pres)
    return pres.sum(0).astype(np.float64), N.sum(0), X.sum(0), a.sum(0), (N * N).sum(0)


def deff_table(N, X):
    """rho (ANOVA ICC across logs), m_bar = n_tot / k, deff = 1 + (m_bar - 1) rho, n_eff = n_tot / deff; per column."""
    k, n, x, a, q = cell_sums(N, X)
    rho = icc_from_sums(k, n, x, a, q)
    with np.errstate(invalid="ignore", divide="ignore"):
        mbar = np.where(k > 0, n / k, np.nan)
        deff = 1.0 + (mbar - 1.0) * rho
        neff = np.where(k > 0, n / deff, np.nan)
    return {"k": k, "n": n, "x": x, "rho": rho, "mbar": mbar, "deff": deff, "neff": neff}


# ------------------------------------------------------------------ (iii) the design-effect Wilson interval
def zq(level):
    return _ND.inv_cdf(level)


def wilson(p, n, z):
    """One-sided Wilson bounds (lower, upper) at the normal quantile z for proportion p on n (effective) units."""
    p = np.asarray(p, np.float64)
    n = np.asarray(n, np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        z2 = z * z
        den = 1.0 + z2 / n
        cen = (p + z2 / (2 * n)) / den
        half = z / den * np.sqrt(np.maximum(p * (1 - p) / n + z2 / (4 * n * n), 0.0))
    return cen - half, cen + half


def wilson_family(est, dt, fam, level, side, pooled_record_rate=None):
    """Design-effect Wilson bounds for the cells fam at simultaneous level by Bonferroni over |fam| cells (plan 2(c1)(iii)).
    est: the record's estimate (mean over logs of the per-log rate); dt: deff_table. pooled_record_rate: if given, the
    record-pooled proportion x/n is used as the centre instead (a variant reported alongside)."""
    fam = np.asarray(fam, int)
    if not len(fam):
        return np.zeros(0), float("nan")
    z = zq(1.0 - (1.0 - level) / len(fam))
    p = est[fam] if pooled_record_rate is None else pooled_record_rate[fam]
    lo, hi = wilson(p, dt["neff"][fam], z)
    return (lo if side == "lower" else hi), z


# ------------------------------------------------------------------ (ii) the studentised log bootstrap with the SE floor
class Stud:
    """For a (U, J) table: the record's estimate (mean over the logs with records of the per-log rate X/N; in the bootstrap the
    ratio sum_u w_u p_u / sum_u w_u 1[N_u > 0]), its cluster delta-method SE
        SE_d^2 = U / (U - 1) * sum_u 1[N_u > 0] (p_u - R)^2 / (sum_u 1[N_u > 0])^2,
    floored at sqrt(delta (1 - delta) / N_eff), N_eff = N / deff (deff from the ANOVA ICC, as (iii)), and the bootstrap pivots
    t*_b = (R*_b - R) / SE*_b with SE*_b the same floored formula recomputed on replicate b (multiplicities as weights)."""

    def __init__(self, N, X, Wobj, nrows=None, delta=DELTA):
        N = np.asarray(N, np.float64)
        X = np.asarray(X, np.float64)
        U = N.shape[0]
        self.U = U
        pres = (N > 0).astype(np.float64)
        p = np.divide(X, N, out=np.zeros_like(X), where=N > 0)
        a = np.divide(X * X, N, out=np.zeros_like(X), where=N > 0)
        cols = [pres, p, p * p, N, X, a, N * N]
        self.est, self.se, self.se_d, self.floor, self.deff, self.rho, self.neff = self._se(
            *[c.sum(0) for c in cols], delta=delta)
        B = Wobj.B if nrows is None else nrows
        M = np.concatenate(cols, axis=1)        # (U, 7J)
        J = N.shape[1]
        self.t = np.empty((B, J))
        for s in range(0, B, Wobj.chunk):
            e = min(B, s + Wobj.chunk)
            S = Wobj.rows(s, e) @ M
            parts = [S[:, i * J:(i + 1) * J] for i in range(7)]
            r, se, _, _, _, _, _ = self._se(*parts, delta=delta)
            with np.errstate(invalid="ignore", divide="ignore"):
                self.t[s:e] = (r - self.est[None, :]) / se
        self.B = B

    def _se(self, sz, sy, syy, sn, sx, sa, sq, delta):
        U = self.U
        with np.errstate(invalid="ignore", divide="ignore"):
            r = sy / sz
            var = np.maximum(syy - r * r * sz, 0.0)
            se_d = np.sqrt(U / (U - 1.0) * var) / sz
            rho = icc_from_sums(sz, sn, sx, sa, sq)
            mbar = sn / sz
            deff = 1.0 + (mbar - 1.0) * rho
            neff = sn / deff
            floor = np.sqrt(delta * (1 - delta) / neff)
            se = np.fmax(se_d, floor)
        return r, se, se_d, floor, deff, rho, neff

    def bounds(self, fam, level, side):
        """Simultaneous one-sided studentised bounds over fam: lower R - q SE, q the level quantile of max_c t*_c; upper
        R + q' SE, q' of max_c (-t*_c). Non-finite pivots are skipped (as the record's nanmax / nanquantile)."""
        fam = np.asarray(fam, int)
        if not len(fam):
            return np.zeros(0), float("nan"), float("nan")
        sg = 1.0 if side == "lower" else -1.0
        T = sg * self.t[:, fam]
        T = np.where(np.isfinite(T), T, -np.inf).max(1)
        T = T[np.isfinite(T)]
        q = float(np.quantile(T, level)) if T.size else float("nan")
        qm = L.quantile_mcse(T, level) if T.size else float("nan")
        e, se = self.est[fam], self.se[fam]
        b = e - q * se if side == "lower" else e + q * se
        return b, q, qm * se if np.isfinite(qm) else np.full(len(fam), np.nan)


# ------------------------------------------------------------------ misc
def cells_idx(names):
    return np.array([CELLNAMES.index(c) for c in names], int)


def versions():
    import platform
    return {"python": platform.python_version(), "numpy": np.__version__, "executable": sys.executable}
