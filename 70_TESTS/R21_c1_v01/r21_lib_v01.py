#!/usr/bin/env python3
"""R21 library v01 (7 Nov 2026): the independent results review's own implementation of C1's statistics.

Written from the frozen plan's text (C1_AV2_CONFIRMATORY_PREREG_v07m.md sections 6.1 to 6.5) and the lead's criteria library
(50_CODE/c1_criteria, read only); see R21_DESIGN_v01.md for every definition and for the record of format looks. It imports
nothing from 50_CODE: no c1_analyse_*, c1_rules_*, k8_analyse_*, k6_analyse_* or m_lib_*. Standalone numpy only.
Every function is outcome-agnostic: it receives arrays and returns statistics.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import ctypes  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

# ------------------------------------------------------------------ constants (plan section 6.1, 6.2; R21 design section 2)
DELTA = 0.05
MIN_UNITS, MIN_LOGS = 39, 8
F_MIN, PD_MIN_EVALUABLE = 6, 1
LEVEL_M = 0.95                      # against M*: cell, family, pooled LB
LEVEL_RM = 1 - 0.0125 / 9           # comparator removal, H1's route and descriptive routes
LEVEL_RM4 = 1 - 0.0025 / 9          # removal on H4's route
LEVEL_RMJ = 1 - 0.0025 / 3          # V^J removal (H3)
L_HK1C, HK1C_MARGIN = 0.995, 0.03
ALPHA_FORM_B, ALPHA_FOR, C_FORM_C = 0.0125, 0.025, 0.03
P_PLANT, RHO, POWER_MIN, N_WEIGHTS, POWER_FLAG_LEVEL = 0.15, 0.5, 0.80, 500, 0.95
B_REGISTERED = 40000
H4_ROUTE = "transfer_lt3d"
SEED_BOOT, SEED_POWER = 20261110, 20261111          # registered (plan section 6.1)
R21_SEED_MC, R21_SEED_POWER = 20261121, 20261122    # R21's own, disjoint from every registered seed
TRACKER_INDEX = {"t1": 0, "t3": 1, "tab": 2}
ROUTE_INDEX = {"within_lt3d": 0, "transfer_lt3d": 1, "voxelnext_val": 2, "public_lt3d_val": 3, "source_transfer": 4}
COMPS = ["B0", "B1", "B3", "B4", "B6", "B9", "RETUNED"]
K_J = ["Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED"]
POPS = ["PD7_primary", "SD1_7_gap_le_5m", "PD_inpath"]
POPS4 = POPS + ["NIP_not_in_path"]
LAB = {"PD7_primary": "PD7", "SD1_7_gap_le_5m": "SD1_7", "PD_inpath": "PD", "NIP_not_in_path": "NIP"}
GROUPS, AXES, MOTIONS = ["car", "pedestrian", "two_wheeler", "large"], ["long", "lat"], ["static", "straight", "turning", "new"]
CELLNAMES = ["%s|%s|%s" % (g, a, m) for g in GROUPS for a in AXES for m in MOTIONS]
# decisions 'stats': 4 blocks x 11 fields; blocks 0 NIP-far, 1 IP-far, 2 NIP-near, 3 IP-near (verified on the rehearsal)
POP_BLOCKS = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3), "NIP_not_in_path": (0, 2)}
POP_TRK = {"PD7_primary": (0, 1, 2, 3, 4, 5), "SD1_7_gap_le_5m": (1, 2, 4, 5), "PD_inpath": (3, 4, 5), "NIP_not_in_path": (0, 1, 2)}
V2_VARIANTS = {"V2": ("n", "x"), "V2_viol": ("n", "v"), "V2_one_step": ("n_h0", "x_h0"), "V2_exec": ("ne", "xe"),
               "V2_binding": ("nb", "xb")}
# merged alpha / delta' curve (D14 A3): alpha_eq = alpha, or (z_{1-d'} / z_{0.95})^2
_Z = {0.5: 0.0, 0.3: 0.5244005127080407, 0.2: 0.8416212335729143, 0.1: 1.2815515655446004, 0.05: 1.6448536269514722,
      0.02: 2.0537489106318225, 0.01: 2.3263478740408408, 0.005: 2.5758293035489004, 0.001: 3.090232306167813}
CURVE = {"B0a0.03125": 1 / 32, "B0a0.0625": 1 / 16, "B0a0.125": 0.125, "B0a0.25": 0.25, "B0a0.333": 1 / 3, "B0a0.5": 0.5,
         "B0a1": 1.0, "B0a2": 2.0, "B0a3": 3.0, "B0a4": 4.0, "B0a5": 5.0, "B0a8": 8.0}
CURVE.update({"B0d%g" % d: (z / _Z[0.05]) ** 2 for d, z in _Z.items()})


# ------------------------------------------------------------------ small utilities
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdump(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=_jdefault)
    os.replace(tmp, path)


def _jdefault(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def fnum(x):
    """JSON-safe float (None for non-finite)."""
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


class _PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def memory_mb():
    """(current working set, peak working set, peak private bytes) in MB; Windows, else resource's max RSS."""
    try:
        pmc = _PMC()
        pmc.cb = ctypes.sizeof(_PMC)
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        fn = k32.K32GetProcessMemoryInfo
        fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PMC), ctypes.c_ulong]
        if not fn(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return {"working_set_mb": pmc.WorkingSetSize / 2 ** 20, "peak_working_set_mb": pmc.PeakWorkingSetSize / 2 ** 20,
                "peak_private_mb": pmc.PeakPagefileUsage / 2 ** 20}
    except Exception:  # noqa: BLE001
        try:
            import resource
            r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            return {"working_set_mb": None, "peak_working_set_mb": r, "peak_private_mb": None}
        except Exception:  # noqa: BLE001
            return {}


class MemGuard:
    """Raises if the process's private bytes exceed a limit (checked at call sites)."""

    def __init__(self, limit_mb):
        self.limit = limit_mb

    def check(self, where=""):
        if not self.limit:
            return
        m = memory_mb()
        cur = m.get("working_set_mb")
        if cur is not None and cur > self.limit:
            raise MemoryError("R21 memory guard: working set %.0f MB > %.0f MB at %s" % (cur, self.limit, where))


def tol_bound(b_r21, b_an=B_REGISTERED):
    return 4 * 0.0006 * math.sqrt(20000.0 / b_r21 + 20000.0 / b_an)


def tol_p(p, b_r21, b_an=B_REGISTERED):
    p = min(max(float(p), 0.0), 1.0)
    return 4 * math.sqrt(max(p * (1 - p), 1e-12) * (1.0 / b_r21 + 1.0 / b_an)) + 1.0 / (b_r21 + 1) + 1.0 / (b_an + 1)


def tol_power(n_r21, n_an=2000):
    return 4 * math.sqrt(0.16 * (1.0 / n_r21 + 1.0 / n_an))


# ------------------------------------------------------------------ the run tables of one route and tracker
class RouteData:
    """Per route and tracker: units, arms, (arm x unit x 32) N and X per population, per-unit infeasible rates, V2 tables,
    margins, folds. Reads only the run tables named by the run record (hashes checked) and the fits file."""

    def __init__(self, runs_dir, tag, tracker, fits_path=None, mem=None):
        t0 = time.time()
        self.runs_dir, self.tag, self.tracker = runs_dir, tag, tracker
        full = tag if tag.endswith("_decide") else tag + "_decide"
        self.full = full
        self.files = {k: os.path.join(runs_dir, "%s_%s%s" % (k, full, ext)) for k, ext in
                      (("run_record", ".json"), ("episodes", ".jsonl"), ("counts", ".npz"), ("decisions", ".npz"), ("cal", ".npz"))}
        with open(self.files["run_record"], encoding="utf-8") as f:
            self.rr = json.load(f)
        self.hash_checks = {}
        for k in ("episodes", "counts", "decisions", "cal"):
            rec = self.rr.get(k + "_sha256")
            now = sha256(self.files[k])
            self.hash_checks[k] = {"recorded": rec, "now": now, "equal": rec == now}
        self.input_sha256 = {k: sha256(p) if k == "run_record" else self.hash_checks[k]["now"] for k, p in self.files.items()}
        # ---- episodes
        eps = []
        with open(self.files["episodes"], encoding="utf-8") as f:
            for line in f:
                o = json.loads(line)
                eps.append((int(o["episode"]), o["arm"], o["scene"], bool(o.get("entered")), int(o.get("frames") or 0),
                            int(o.get("infeasible_frames") or 0), o.get("fold"), o.get("delay_kf")))
        self.n_episodes = len(eps)
        self.not_entered = [(e[2], e[1]) for e in eps if not e[3]]
        keep = [e for e in eps if e[3] and e[1] != "LOG"]
        self.units = sorted({e[2] for e in keep})
        self.U = len(self.units)
        uidx = {s: i for i, s in enumerate(self.units)}
        arms_rr = [a for a in self.rr.get("arms", []) if a != "LOG"]
        arms_ep = sorted({e[1] for e in keep})
        self.arms = [a for a in arms_rr if a in arms_ep] + [a for a in arms_ep if a not in arms_rr]
        self.ai = {a: i for i, a in enumerate(self.arms)}
        A = len(self.arms)
        maxep = max(e[0] for e in eps) + 1
        self.ep_arm = np.full(maxep, -1, np.int32)
        self.ep_unit = np.full(maxep, -1, np.int32)
        ep_frames = np.zeros(maxep, np.int64)
        ep_inf = np.zeros(maxep, np.int64)
        self.unit_fold_episode = {}
        dup = 0
        for e in keep:
            if self.ep_arm[e[0]] >= 0:
                dup += 1
            self.ep_arm[e[0]], self.ep_unit[e[0]] = self.ai[e[1]], uidx[e[2]]
            ep_frames[e[0]], ep_inf[e[0]] = e[4], e[5]
            if e[6] is not None:
                self.unit_fold_episode[e[2]] = int(e[6])
        self.duplicate_episodes = dup
        present = np.zeros((A, self.U), bool)
        present[self.ep_arm[self.ep_arm >= 0], self.ep_unit[self.ep_arm >= 0]] = True
        self.missing_arm_unit = [(self.arms[a], self.units[u]) for a, u in zip(*np.nonzero(~present))]
        del eps, keep
        # ---- decisions: infeasible rate, V2 tables
        zd = np.load(self.files["decisions"])
        dep = zd["episode"].astype(np.int64)
        ok = (dep < maxep)
        ok[ok] = self.ep_arm[dep[ok]] >= 0
        dep = dep[ok]
        dinf = zd["infeasible"][ok].astype(np.int64)
        cnt = np.bincount(dep, minlength=maxep)
        isum = np.bincount(dep, weights=dinf, minlength=maxep)
        self.decisions_vs_episodes_mismatch = int(np.sum(((cnt != ep_frames) | (isum != ep_inf)) & (self.ep_arm >= 0)))
        darm, dun = self.ep_arm[dep], self.ep_unit[dep]
        self.dec_count = np.zeros((A, self.U))
        self.inf_count = np.zeros((A, self.U))
        np.add.at(self.dec_count, (darm, dun), 1.0)
        np.add.at(self.inf_count, (darm, dun), dinf)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.inf_rate = self.inf_count / self.dec_count
        stf = [str(x) for x in zd["st_fields"]]
        si = {f: i for i, f in enumerate(stf)}
        ob = zd["ob"][ok]
        lam = zd["lam"][ok]
        trk = zd["trk"][ok].astype(np.float64)
        stats = zd["stats"][ok]
        del zd
        nf = len(stf)
        stats = stats.reshape(-1, 4, nf)
        self.v2 = {}
        for p in POPS4:
            bl = list(POP_BLOCKS[p])
            ntot = stats[:, bl, si["n"]].astype(np.float64).sum(1)
            has = (ntot > 0) & (ob == 0)
            hasf = has.astype(np.float64)
            den = np.zeros((A, self.U))
            np.add.at(den, (darm, dun), hasf)
            tracks = trk[:, list(POP_TRK[p])].sum(1)
            ref = np.zeros((A, self.U))
            np.add.at(ref, (darm, dun), np.where(has, 1 - (1 - DELTA) ** tracks, 0.0))
            trs = np.zeros((A, self.U))
            np.add.at(trs, (darm, dun), np.where(has, tracks, 0.0))
            out = {"den": den, "ref": ref, "tracks": trs}
            for var, (fn, fx) in V2_VARIANTS.items():
                if fn not in si or fx not in si:
                    continue
                nn = stats[:, bl, si[fn]].astype(np.float64).sum(1)
                xx = stats[:, bl, si[fx]].astype(np.float64).sum(1)
                hv = (nn > 0) & (ob == 0)
                dv = np.zeros((A, self.U))
                xv = np.zeros((A, self.U))
                np.add.at(dv, (darm, dun), hv.astype(np.float64))
                np.add.at(xv, (darm, dun), ((xx > 0) & hv).astype(np.float64))
                out[var] = (dv, xv)
            self.v2[p] = out
        self.lam_estop = np.zeros((A, self.U))
        np.add.at(self.lam_estop, (darm, dun), (lam == -1.0).astype(np.float64))
        del stats, trk, ob, lam, dep, dinf, darm, dun
        if mem:
            mem.check("decisions")
        # ---- counts: N, X per population
        zc = np.load(self.files["counts"])
        cep = zc["episode"].astype(np.int64)
        okc = cep < maxep
        okc[okc] = self.ep_arm[cep[okc]] >= 0
        self.count_rows_total, self.count_rows_kept = int(len(cep)), int(okc.sum())
        cep = cep[okc]
        cell = zc["cell"][okc].astype(np.int64)
        cn = zc["n"][okc].astype(np.float64)
        cx = zc["exceed"][okc].astype(np.float64)
        del zc, okc
        l0 = cell % 96
        col = (l0 // 24) * 8 + ((l0 // 4) % 2) * 4 + (l0 % 4)
        rest = cell // 96
        del cell, l0
        base = (rest % 8) < 4
        rest //= 8
        base &= (rest % 2) == 1          # relied-on
        rest //= 2
        near = (rest % 3) <= 1           # pair gap <= 5 m
        rest //= 3
        base &= (rest % 2) == 1          # satisfied
        rest //= 2
        base &= (rest % 2) == 1          # enforced
        rest //= 2
        inpath = (rest % 2) == 1
        base &= (rest // 2) == 0         # sensor-offset bin 0
        del rest
        masks = {"PD7_primary": base, "SD1_7_gap_le_5m": base & near, "PD_inpath": base & inpath, "NIP_not_in_path": base & ~inpath}
        carm, cun = self.ep_arm[cep], self.ep_unit[cep]
        del cep
        self.N, self.X = {}, {}
        for p, m in masks.items():
            idx = (carm[m].astype(np.int64) * self.U + cun[m]) * 32 + col[m]
            self.N[p] = np.bincount(idx, weights=cn[m], minlength=A * self.U * 32).reshape(A, self.U, 32)
            self.X[p] = np.bincount(idx, weights=cx[m], minlength=A * self.U * 32).reshape(A, self.U, 32)
        del masks, base, near, inpath, carm, cun, col, cn, cx
        if mem:
            mem.check("counts")
        # ---- cal: margins (record-weighted)
        zl = np.load(self.files["cal"])
        lf = [str(x) for x in zl["fields"]]
        lep = zl["episode"].astype(np.int64)
        okl = lep < maxep
        okl[okl] = self.ep_arm[lep[okl]] >= 0
        lv = zl["values"][okl]
        lkey = zl["key"][okl]
        larm = self.ep_arm[lep[okl]]
        del zl, lep
        self.margins = {}
        blk = lkey // 96
        for p in POPS4:
            m = np.isin(blk, POP_BLOCKS[p])
            s = np.zeros((A, 3))
            for j, fname in enumerate(("n", "mg_long_sum", "mg_lat_sum")):
                if fname in lf:
                    np.add.at(s[:, j], larm[m], lv[m, lf.index(fname)])
            self.margins[p] = s
        del lv, lkey, larm, blk
        # ---- fits: folds, transfer RETUNED, M*Jx lambda qualification
        self.fits_path = fits_path
        self.fold_of_unit, self.retuned_transfer_arm, self.lambda_qualified = None, None, None
        if fits_path:
            with open(fits_path, encoding="utf-8") as f:
                fits = json.load(f)
            self.input_sha256["fits"] = sha256(fits_path)
            fos = fits.get("fold_of_scene") or {}
            if all(u in fos for u in self.units):
                self.fold_of_unit = np.array([int(fos[u]) for u in self.units])
            self.retuned_transfer_arm = fits.get("retuned_transfer_arm")
            try:
                fl = fits["joint"]["fit"]["folds"]
                self.lambda_qualified = {str(k): bool(v["MstarJx"]["lambda_qualified"]) for k, v in fl.items() if "MstarJx" in v}
            except Exception:  # noqa: BLE001
                self.lambda_qualified = None
            del fits
        self.retuned = None
        self.seconds_load = time.time() - t0

    # ---- RETUNED (D14 A3): cross-fitted first qualifying point of the merged curve, or the transfer fit's arm
    def select_retuned(self):
        if self.retuned_transfer_arm:
            arm = self.retuned_transfer_arm
            self.retuned = {"rule": "transfer fit's retuned_transfer_arm", "arm_of_fold": {"all": arm},
                            "arm_of_unit": [arm] * self.U, "grid": None}
            return self.retuned
        if self.fold_of_unit is None:
            self.retuned = {"rule": "no folds: RETUNED not formed", "arm_of_fold": {}, "arm_of_unit": None, "grid": None}
            return self.retuned
        curve = sorted((CURVE[a], a) for a in CURVE if a in self.ai)
        pooled = {}
        for _, a in curve:
            k = self.ai[a]
            pooled[a] = {p: (self.N[p][k].sum(1), self.X[p][k].sum(1)) for p in POPS}
        sel, grid = {}, {}
        for f in sorted(set(self.fold_of_unit.tolist())):
            tr = self.fold_of_unit != f
            chosen, rows = None, []
            for al, a in curve:
                E = {}
                for p in POPS:
                    Nk, Xk = pooled[a][p]
                    m = tr & (Nk > 0)
                    E[p] = float(np.mean(Xk[m] / Nk[m])) if m.any() else None
                q = all(E[p] is not None and E[p] <= DELTA for p in POPS)
                rows.append({"arm": a, "alpha_eq": al, "E_train": E, "qualifies": q})
                if q and chosen is None:
                    chosen = a
            sel[str(f)] = chosen if chosen is not None else curve[-1][1]
            grid[str(f)] = rows
        aou = [sel[str(int(f))] for f in self.fold_of_unit]
        self.retuned = {"rule": "D14 A3: first qualifying merged-curve point (pooled PD7, SD1_7, PD <= delta on the other folds)",
                        "arm_of_fold": sel, "arm_of_unit": aou, "grid": grid}
        return self.retuned

    def arm_rows(self, arm):
        """Per-unit row index into the arm axis (RETUNED composite per unit)."""
        if arm == "RETUNED":
            if self.retuned is None:
                self.select_retuned()
            aou = self.retuned["arm_of_unit"]
            if aou is None:
                return None
            return np.array([self.ai[a] for a in aou])
        if arm not in self.ai:
            return None
        return np.full(self.U, self.ai[arm])

    def table(self, arm, pop):
        r = self.arm_rows(arm)
        if r is None:
            return None, None
        u = np.arange(self.U)
        return self.N[pop][r, u], self.X[pop][r, u]

    def inf(self, arm):
        r = self.arm_rows(arm)
        return None if r is None else self.inf_rate[r, np.arange(self.U)]

    def v2_table(self, arm, pop, var="V2"):
        r = self.arm_rows(arm)
        if r is None:
            return None
        u = np.arange(self.U)
        d, x = self.v2[pop][var]
        return d[r, u], x[r, u]

    def v2_ref(self, arm, pop):
        r = self.arm_rows(arm)
        u = np.arange(self.U)
        return self.v2[pop]["den"][r, u], self.v2[pop]["ref"][r, u], self.v2[pop]["tracks"][r, u]


# ------------------------------------------------------------------ bootstrap weights
class Weights:
    """Multinomial log-bootstrap weights (B x U), stored as int16, generated in row chunks from one generator:
    numpy.random.default_rng(seed).multinomial(U, 1/U, size=B) (the criteria library's documented scheme)."""

    def __init__(self, seed, U, B, chunk=4000, cache_mb=160):
        self.seed, self.U, self.B, self.chunk = list(seed), U, B, chunk
        g = np.random.default_rng(self.seed)
        p = np.full(U, 1.0 / U)
        self.W = np.empty((B, U), np.int16)
        for s in range(0, B, chunk):
            e = min(B, s + chunk)
            self.W[s:e] = g.multinomial(U, p, size=e - s)
        self.Wf = self.W.astype(np.float64) if B * U * 8 <= cache_mb * 2 ** 20 else None
        if self.Wf is not None:
            self.chunk = B

    def rows(self, s, e):
        if self.Wf is not None:
            return self.Wf[s:e]
        return self.W[s:e].astype(np.float64)

    def rates(self, N, X, nrows=None):
        """Bootstrap of the unit-level mean of X/N over units with N > 0, per column; N, X (U, J). Returns (B, J)."""
        B = self.B if nrows is None else nrows
        p = np.divide(X, N, out=np.zeros_like(X, dtype=np.float64), where=N > 0)
        pres = (N > 0).astype(np.float64)
        out = np.empty((B, N.shape[1]))
        with np.errstate(invalid="ignore", divide="ignore"):
            for s in range(0, B, self.chunk):
                e = min(B, s + self.chunk)
                w = self.rows(s, e)
                out[s:e] = (w @ p) / (w @ pres)
        return out

    def means(self, d):
        """Bootstrap of the plain unit mean of d (U,): every row sums to U."""
        d = np.asarray(d, np.float64)
        out = np.empty(self.B)
        for s in range(0, self.B, self.chunk):
            e = min(self.B, s + self.chunk)
            out[s:e] = (self.rows(s, e) @ d) / self.U
        return out


def point_rates(N, X):
    p = np.divide(X, N, out=np.zeros_like(X, dtype=np.float64), where=N > 0)
    pres = (N > 0).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return p.sum(0) / pres


def evaluable(N):
    k = (N > 0).sum(0)
    return (k >= MIN_UNITS) & (k >= MIN_LOGS)


# ------------------------------------------------------------------ Andrews-Buchinsky MC SE of a bootstrap quantile
def quantile_mcse(x, tau):
    """sqrt(tau (1 - tau) / B) / f(q_tau), f by the Siddiqui-Bloch-Gastwirth difference quotient (Andrews and Buchinsky 2000)."""
    x = np.asarray(x, np.float64)
    x = x[np.isfinite(x)]
    B = len(x)
    if B < 10 or not (0 < tau < 1):
        return float("nan")
    h = min(0.5 * B ** (-1.0 / 3.0), 0.9 * min(tau, 1 - tau))
    h = max(h, 2.0 / B)
    lo, hi = max(tau - h, 0.0), min(tau + h, 1.0)
    ql, qh = np.quantile(x, [lo, hi])
    if not qh > ql:
        return 0.0
    return math.sqrt(tau * (1 - tau) / B) * (qh - ql) / (hi - lo)


# ------------------------------------------------------------------ sup-t bounds
def supt(est, boot, fam, level, side="lower"):
    """One-sided simultaneous bound over the cells fam. side 'lower': LB = E - q SE with q the level quantile of
    max_c (E*_c - E_c)/SE_c; 'upper': UB = E + q' SE with q' of max_c (E_c - E*_c)/SE_c. SE = 0 cells get the estimate."""
    fam = np.asarray(fam, int)
    e = est[fam]
    b = boot[:, fam]
    with np.errstate(invalid="ignore", divide="ignore"):
        se = np.nanstd(b, axis=0, ddof=1) if b.shape[0] > 1 else np.full(len(fam), np.nan)
    ok = np.isfinite(se) & (se > 0)
    q, q_mcse = float("nan"), float("nan")
    if ok.any():
        sg = 1.0 if side == "lower" else -1.0
        dev = sg * (b[:, ok] - e[ok]) / se[ok]
        with np.errstate(invalid="ignore"):
            T = np.max(np.where(np.isnan(dev), -np.inf, dev), axis=1)
        T = T[np.isfinite(T)]
        if T.size:
            q = float(np.quantile(T, level))
            q_mcse = quantile_mcse(T, level)
    qf = math.isfinite(q)
    if side == "lower":
        bound = np.where(ok & qf, e - (q if qf else 0.0) * np.where(ok, se, 0.0), e)
    else:
        bound = np.where(ok & qf, e + (q if qf else 0.0) * np.where(ok, se, 0.0), e)
    mcse = np.where(ok & qf, (q_mcse if math.isfinite(q_mcse) else np.nan) * np.where(ok, se, 0.0), 0.0)
    return {"est": e, "se": se, "ok": ok, "q": q, "bound": bound, "q_mcse": q_mcse, "bound_mcse": mcse}


def flag_cells(est, boot, fam, level):
    """Plan section 6.2 Flag_cell: LB > delta, or SE = 0 and E > delta (a non-finite q judges every cell by E > delta)."""
    r = supt(est, boot, fam, level, "lower")
    qf = math.isfinite(r["q"])
    by_lb = r["ok"] & qf & (r["bound"] > DELTA)
    zero = (~(r["ok"] & qf)) & (r["est"] > DELTA)
    r["flag"] = by_lb | zero
    r["zero_flag"] = zero
    with np.errstate(invalid="ignore", divide="ignore"):
        r["t"] = np.where(r["ok"], (r["est"] - DELTA) / np.where(r["ok"], r["se"], 1.0), np.nan)
    return r


# ------------------------------------------------------------------ power rule (target-only planting; R21 implementation)
def power_target(N, ev_idx, W500, rng, n_datasets, P=P_PLANT, rho=RHO, level=POWER_FLAG_LEVEL, batch=25):
    """Per evaluable cell: share of datasets in which the cell, drawn at P (others at delta; beta-binomial per unit and cell
    with ICC rho; the arm's own N), is flagged in the all-evaluable lower sup-t at level on the weights W500."""
    ev_idx = np.asarray(ev_idx, int)
    J = len(ev_idx)
    if J == 0:
        return np.zeros(0)
    Nf = N[:, ev_idx].astype(np.float64)
    Ni = Nf.astype(np.int64)
    U = Nf.shape[0]
    pres = (Nf > 0).astype(np.float64)
    den = W500 @ pres                                  # (R, J), the same for every dataset
    eden = pres.sum(0)
    s = (1 - rho) / rho
    a0, b0 = DELTA * s, (1 - DELTA) * s
    a1, b1 = P * s, (1 - P) * s
    R = W500.shape[0]
    hits = np.zeros(J)
    done = 0
    ar = np.arange(J)
    while done < n_datasets:
        nb = min(batch, n_datasets - done)
        x0 = rng.binomial(np.broadcast_to(Ni, (nb, U, J)), rng.beta(a0, b0, size=(nb, U, J)))
        x1 = rng.binomial(np.broadcast_to(Ni, (nb, U, J)), rng.beta(a1, b1, size=(nb, U, J)))
        for xx, key in ((x0, 0), (x1, 1)):
            p = np.divide(xx, Nf[None], out=np.zeros(xx.shape), where=Nf[None] > 0)
            est = p.sum(1) / eden                                   # (nb, J)
            num = W500 @ p.transpose(1, 0, 2).reshape(U, nb * J)    # (R, nb J)
            with np.errstate(invalid="ignore", divide="ignore"):
                bt = num.reshape(R, nb, J) / den[:, None, :]
                se = np.nanstd(bt, axis=0, ddof=1)                  # (nb, J)
                okk = np.isfinite(se) & (se > 0)
                dev = np.where(okk[None], (bt - est[None]) / np.where(okk, se, 1.0)[None], -np.inf)
            if key == 0:
                e0, se0, ok0, D0 = est, se, okk, dev
            else:
                e1, se1, ok1, D1 = est, se, okk, dev
        # T for target j: max(max over c != j of base dev, target dev)
        top1 = D0.max(axis=2)                                       # (R, nb)
        arg = D0.argmax(axis=2)
        D0m = D0.copy()
        np.put_along_axis(D0m, arg[..., None], -np.inf, axis=2)
        top2 = D0m.max(axis=2)
        Mx = np.where(arg[..., None] == ar[None, None, :], top2[..., None], top1[..., None])   # (R, nb, J)
        T = np.maximum(Mx, D1)
        q = np.quantile(T, level, axis=0)                           # (nb, J)
        with np.errstate(invalid="ignore"):
            lb = e1 - q * se1
        flag = np.where(ok1 & np.isfinite(q), lb > DELTA, e1 > DELTA)
        hits += flag.sum(0)
        done += nb
    return hits / n_datasets


# ------------------------------------------------------------------ one arm and population: the validity pieces
def arm_population(N, X, W, level, family=None, power=None, ub_level=L_HK1C, want_upper=False):
    """Flags over all evaluable cells and over the family, the pooled cell (LB at level, UB at ub_level), U_max at 0.95."""
    est = point_rates(N, X)
    ev = np.flatnonzero(evaluable(N))
    boot = W.rates(N, X) if len(ev) else None
    out = {"evaluable": [CELLNAMES[j] for j in ev], "n_evaluable": int(len(ev)), "records": float(N.sum()),
           "exceed": float(X.sum()), "units_with_records": int(((N.sum(1)) > 0).sum())}
    cells = {}
    if len(ev):
        r = flag_cells(est, boot, ev, level)
        out["q_cells"] = fnum(r["q"])
        out["flagged"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(r["flag"])]
        out["zero_se_flagged"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(r["zero_flag"])]
        out["nonzero_flagged"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(r["flag"] & ~r["zero_flag"])]
        out["zero_se_cells"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(~r["ok"])]
        out["max_lb_minus_delta"] = fnum(np.max(r["bound"] - DELTA))
        for i, j in enumerate(ev):
            cells[CELLNAMES[j]] = {"E": fnum(est[j]), "se": fnum(r["se"][i]), "lb": fnum(r["bound"][i]), "t": fnum(r["t"][i]),
                                   "lb_mcse": fnum(r["bound_mcse"][i]),
                                   "flag": bool(r["flag"][i]), "records": float(N[:, j].sum()), "units": int((N[:, j] > 0).sum())}
        if want_upper:
            u = supt(est, boot, ev, LEVEL_M, "upper")
            out["U_cells_0.95"] = {CELLNAMES[j]: fnum(u["bound"][i]) for i, j in enumerate(ev)}
            out["U_max_0.95"] = fnum(np.max(u["bound"]))
            out["U_mcse_0.95"] = {CELLNAMES[j]: fnum(u["bound_mcse"][i]) for i, j in enumerate(ev)}
            out["U_max_cell"] = CELLNAMES[ev[int(np.argmax(u["bound"]))]]
            out["q_upper_0.95"] = fnum(u["q"])
        out["near_t_minus_q"] = [{"cell": CELLNAMES[ev[i]], "t": fnum(r["t"][i]), "q": fnum(r["q"])} for i in range(len(ev))
                                 if math.isfinite(r["q"]) and np.isfinite(r["t"][i]) and abs(r["t"][i] - r["q"]) < 0.2]
    else:
        out.update({"q_cells": None, "flagged": [], "zero_se_flagged": [], "nonzero_flagged": [], "zero_se_cells": [],
                    "max_lb_minus_delta": None, "near_t_minus_q": []})
    out["cells"] = cells
    # family
    if family is not None:
        fam = np.array([CELLNAMES.index(c) for c in family], int)
        out["family"] = list(family)
        out["family_size"] = int(len(fam))
        if len(fam):
            rf = flag_cells(est, boot, fam, level)
            out["family_q"] = fnum(rf["q"])
            out["family_flagged"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(rf["flag"])]
            out["family_zero_se_flagged"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(rf["zero_flag"])]
            out["family_nonzero_flagged"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(rf["flag"] & ~rf["zero_flag"])]
            out["family_max_lb_minus_delta"] = fnum(np.max(rf["bound"] - DELTA))
            out["family_lb"] = {CELLNAMES[fam[i]]: fnum(rf["bound"][i]) for i in range(len(fam))}
            out["family_lb_mcse"] = {CELLNAMES[fam[i]]: fnum(rf["bound_mcse"][i]) for i in range(len(fam))}
            out["family_near_t_minus_q"] = [{"cell": CELLNAMES[fam[i]], "t": fnum(rf["t"][i]), "q": fnum(rf["q"])}
                                            for i in range(len(fam)) if math.isfinite(rf["q"]) and np.isfinite(rf["t"][i])
                                            and abs(rf["t"][i] - rf["q"]) < 0.2]
        else:
            out.update({"family_q": None, "family_flagged": [], "family_zero_se_flagged": [], "family_nonzero_flagged": [],
                        "family_max_lb_minus_delta": None, "family_near_t_minus_q": [], "family_lb": {}})
        record_total = N.sum()
        out["family_record_share"] = fnum(N[:, fam].sum() / record_total) if record_total > 0 and len(fam) else 0.0
    if power is not None:
        out["power"] = {CELLNAMES[j]: fnum(v) for j, v in power.items()}
    # pooled
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    pe = point_rates(Np, Xp)
    pev = bool(evaluable(Np)[0])
    pooled = {"evaluable": pev, "E": fnum(pe[0]), "units": int((Np[:, 0] > 0).sum())}
    if (Np > 0).any():
        pb = W.rates(Np, Xp)
        lo = flag_cells(pe, pb, [0], level)
        up = supt(pe, pb, [0], ub_level, "upper")
        pooled.update({"se": fnum(lo["se"][0]), "lb": fnum(lo["bound"][0]), "flag": bool(lo["flag"][0]),
                       "zero_se_flag": bool(lo["zero_flag"][0]), "ub": fnum(up["bound"][0]),
                       "lb_mcse": fnum(lo["bound_mcse"][0]), "ub_mcse": fnum(up["bound_mcse"][0]),
                       "ub_percentile": fnum(np.nanquantile(pb[:, 0], ub_level)),
                       "lb_percentile": fnum(np.nanquantile(pb[:, 0], 1 - level)), "level": level, "ub_level": ub_level})
    out["pooled"] = pooled
    return out


def family_from_power(power_by_cell):
    return [c for c, v in power_by_cell.items() if v is not None and v >= POWER_MIN]


def removal_level(route):
    return LEVEL_RM4 if route == H4_ROUTE else LEVEL_RM


def pop_status(r, pop, mstar=False):
    """Plan section 6.2 per population: NoFlag, FamFlag, NoFlag_pool, Floor, HK1c; shown (the 3 removal conditions)."""
    pooled = r["pooled"]
    pe = pooled["evaluable"]
    nf = not r["flagged"]
    ff = bool(r.get("family_flagged"))
    nfp = bool(pe and not pooled.get("flag", False))
    floor = (r.get("family_size", 0) >= F_MIN) if pop != "PD_inpath" else (r["n_evaluable"] >= PD_MIN_EVALUABLE)
    ub = pooled.get("ub")
    hk = bool(pe and ub is not None and ub <= DELTA + HK1C_MARGIN)
    conds = {"cell": not nf, "family": ff, "pooled": bool(pe and pooled.get("flag", False))}
    conds_nz = {"cell": bool(r.get("nonzero_flagged")), "family": bool(r.get("family_nonzero_flagged")),
                "pooled": bool(pe and pooled.get("flag", False) and not pooled.get("zero_se_flag", False))}
    return {"NoFlag": nf, "FamFlag": ff, "pooled_evaluable": bool(pe), "NoFlag_pool": nfp, "Floor": bool(floor), "HK1c": hk,
            "valid": bool(nf and not ff and nfp and floor and hk), "shown_above": any(conds.values()), "conditions": conds,
            "shown_above_without_zero_se": any(conds_nz.values()), "conditions_without_zero_se": conds_nz,
            "family_size": r.get("family_size"), "n_evaluable": r["n_evaluable"], "pooled_ub": ub, "pooled_lb": pooled.get("lb")}


def paired(W, d, level):
    bm = W.means(d)
    k = int(np.sum(bm >= 0))
    return {"mean_diff": fnum(np.mean(d)), "ub": fnum(np.quantile(bm, level)), "ub_mcse": fnum(quantile_mcse(bm, level)),
            "level": level, "p_k": k, "p_B": W.B,
            "p": (k + 1.0) / (W.B + 1.0), "ci95": [fnum(np.quantile(bm, 0.025)), fnum(np.quantile(bm, 0.975))], "_bm": bm}


def form_b(W, rate_m, rates_c, V, level_alpha=ALPHA_FORM_B, p_multiplier=1):
    """Form B part (ii) over V at 1 - alpha/|V| (H1: alpha 0.0125; H3/H4 nominal: 0.025/2 with p doubled)."""
    if not V:
        return {"V": [], "n_V": 0, "level": None, "vs": {}, "all_lower": True, "vacuous": True, "p": 1.0, "max_ub": None}
    lev = 1 - level_alpha / len(V)
    vs = {}
    for c in V:
        r = paired(W, rate_m - rates_c[c], lev)
        r.pop("_bm")
        vs[c] = r
    pmax = max(v["p"] for v in vs.values())
    return {"V": list(V), "n_V": len(V), "level": lev, "vs": vs, "all_lower": all(v["ub"] < 0 for v in vs.values()),
            "vacuous": False, "p": min(1.0, p_multiplier * len(V) * pmax), "max_ub": max(v["ub"] for v in vs.values())}


# ------------------------------------------------------------------ validity of every H1 arm on one route and tracker
def h1_route_tracker(data, W, route, family_fn=None, fixed_families=None, power_n=500, power_seed=None, mem=None,
                     want_power=True, own_power_cache=None):
    """Family of each arm and population, in order: fixed_families[arm][pop] (a list) if given; else family_fn(arm, pop, N,
    ev_names, own_power) if it returns a list (e.g. the analysis's family, recovered); else R21's own power rule.
    own_power_cache {arm: {pop: {cell: power}}} skips recomputing R21's power."""
    lev_rm = removal_level(route)
    i, j = TRACKER_INDEX[data.tracker], ROUTE_INDEX[route]
    W500 = W.rows(0, min(N_WEIGHTS, W.B))
    res = {"arms": {}, "power": {}, "levels": {"Mstar": LEVEL_M, "comparators": lev_rm, "hk1c": L_HK1C}}
    for k, arm in enumerate(["Mstar"] + COMPS):
        level = LEVEL_M if arm == "Mstar" else lev_rm
        pops = {}
        for kp, pop in enumerate(POPS):
            N, X = data.table(arm, pop)
            if N is None:
                pops = None
                break
            ev = np.flatnonzero(evaluable(N))
            own_power, fam, src = None, None, None
            fixed = (fixed_families or {}).get(arm, {}).get(pop)
            if fixed is not None:
                fam, src = list(fixed), "fixed"
            cached = (own_power_cache or {}).get(arm, {}).get(pop)
            if cached is not None:
                own_power = {CELLNAMES.index(c): v for c, v in cached.items()}
            elif want_power and (fam is None or arm == "Mstar"):
                seed = list(power_seed) + [k, kp] if power_seed is not None else [R21_SEED_POWER, i, j, k, kp]
                pw = power_target(N, ev, W500, np.random.default_rng(seed), power_n)
                own_power = {int(c): float(v) for c, v in zip(ev, pw)}
                res["power"].setdefault(arm, {})[pop] = {"seed": seed, "datasets": power_n,
                                                         "per_cell": {CELLNAMES[c]: v for c, v in own_power.items()}}
            if fam is None and family_fn is not None:
                f2 = family_fn(arm, pop, N, [CELLNAMES[c] for c in ev],
                               None if own_power is None else {CELLNAMES[c]: v for c, v in own_power.items()})
                if f2 is not None:
                    fam, src = list(f2), "analysis"
            if fam is None and own_power is not None:
                fam, src = [CELLNAMES[c] for c, v in own_power.items() if v >= POWER_MIN], "R21 power rule (%d datasets)" % power_n
            if fam is None:
                fam, src = [], "none"
            r = arm_population(N, X, W, level, family=fam, power=own_power, want_upper=(arm == "Mstar"))
            r["family_source"] = src
            r["status"] = pop_status(r, pop)
            pops[pop] = r
            if mem:
                mem.check("%s %s" % (arm, pop))
        res["arms"][arm] = pops
    return res


def assemble_h1(data, W, res, route):
    """Valid(M*), V_t (and without zero-SE removals), Form B per tracker; plus H4's form on the transfer route."""
    m = res["arms"]["Mstar"]
    valid = bool(m is not None and all(m[p]["status"]["valid"] for p in POPS))
    shown, shown_nz, reasons = {}, {}, {}
    removal_stat, removal_mcse, pw_border = {}, {}, {}
    missing = []
    for c in COMPS:
        a = res["arms"].get(c)
        if a is None:
            missing.append(c)
            continue
        shown[c] = any(a[p]["status"]["shown_above"] for p in POPS)
        shown_nz[c] = any(a[p]["status"]["shown_above_without_zero_se"] for p in POPS)
        reasons[c] = {p: {k: v for k, v in a[p]["status"]["conditions"].items() if v} for p in POPS}
        reasons[c] = {p: v for p, v in reasons[c].items() if v}
        st = []
        for p in POPS:
            r = a[p]
            for cc, v in r["cells"].items():
                if v.get("lb") is not None:
                    st.append((v["lb"] - DELTA, v.get("lb_mcse")))
            for cc, v in (r.get("family_lb") or {}).items():
                if v is not None:
                    st.append((v - DELTA, (r.get("family_lb_mcse") or {}).get(cc)))
            if r["pooled"].get("evaluable") and r["pooled"].get("lb") is not None:
                st.append((r["pooled"]["lb"] - DELTA, r["pooled"].get("lb_mcse")))
        best = max(st, key=lambda x: x[0]) if st else (None, None)
        removal_stat[c], removal_mcse[c] = best
        pw_border[c] = sorted({"%s:%s" % (p, cc) for p in POPS for cc, v in (a[p].get("power") or {}).items()
                               if str(a[p].get("family_source", "")).startswith("R21") and v is not None and abs(v - POWER_MIN) <= 0.08})
    V = [c for c in COMPS if c in shown and not shown[c]]
    Vnz = [c for c in COMPS if c in shown_nz and not shown_nz[c]]
    rate_m = data.inf("Mstar")
    rates = {c: data.inf(c) for c in COMPS if c not in missing}
    if route == H4_ROUTE:
        fb = form_b(W, rate_m, rates, V, level_alpha=ALPHA_FOR / 2, p_multiplier=2)
        fbz = form_b(W, rate_m, rates, Vnz, level_alpha=ALPHA_FOR / 2, p_multiplier=2)
    else:
        fb = form_b(W, rate_m, rates, V)
        fbz = form_b(W, rate_m, rates, Vnz)
    met = bool(valid and not missing and fb["all_lower"])
    met_nz = bool(valid and not missing and fbz["all_lower"])
    zero_se_removed = [c for c in COMPS if c in shown and shown[c] and not shown_nz[c]]
    return {"valid_Mstar": valid, "V": V, "removed_shown_above": [c for c in COMPS if shown.get(c)], "missing": missing,
            "removal_reasons": reasons, "removal_stat_max_lb_minus_delta": removal_stat, "removal_stat_mcse": removal_mcse,
            "power_near_0.80": pw_border,
            "form_b": fb, "met": met, "vacuous": fb["vacuous"],
            "without_zero_se_removals": {"V": Vnz, "form_b": fbz, "met": met_nz, "zero_se_removed": zero_se_removed},
            "Mstar_pops": {p: m[p]["status"] for p in POPS} if m else None,
            "Mstar_hk1c_ub": {p: m[p]["pooled"].get("ub") for p in POPS} if m else None}


def form_c(W, data, c=C_FORM_C):
    d = data.inf("Mstar") - data.inf("B4")
    bm = W.means(d)
    k = int(np.sum(bm > c))
    return {"mean_diff": fnum(np.mean(d)), "ub": fnum(np.quantile(bm, 0.975)), "ub_mcse": fnum(quantile_mcse(bm, 0.975)), "c": c,
            "met": bool(np.quantile(bm, 0.975) <= c), "p_k": k, "p": (k + 1.0) / (W.B + 1.0)}


def joint_rates(data, arm, pop):
    t = data.v2_table(arm, pop, "V2")
    return None if t is None else (t[0][:, None], t[1][:, None])


def h3_route_tracker(data, W):
    """H3 (plan sections 6.2, 6.3) on the within route: ValidJ(M*Jx), V^J at 1 - 0.0025/3, the nominal bound and p."""
    out = {"pops": {}, "comparators": {}}
    jm = {}
    validJ = True
    for pop in POPS:
        t = joint_rates(data, "MstarJx", pop)
        if t is None:
            return {"available": False, "why": "no MstarJx arm in the run"}
        N, X = t
        e = point_rates(N, X)
        ev = bool(evaluable(N)[0])
        b = W.rates(N, X)
        lo = flag_cells(e, b, [0], LEVEL_M)
        up = supt(e, b, [0], L_HK1C, "upper")
        ok = bool(ev and lo["bound"][0] <= DELTA and up["bound"][0] <= DELTA + HK1C_MARGIN)
        jm[pop] = {"E": fnum(e[0]), "evaluable": ev, "lb": fnum(lo["bound"][0]), "ub": fnum(up["bound"][0]), "ok": ok,
                   "lb_mcse": fnum(lo["bound_mcse"][0]), "ub_mcse": fnum(up["bound_mcse"][0])}
        validJ = validJ and ok
    lq = data.lambda_qualified
    lam_ok = bool(lq) and all(lq.values()) if lq is not None else None
    out["pops"] = jm
    out["lambda_qualified_by_fold"] = lq
    out["validJ_method"] = bool(validJ and (lam_ok is not False))
    VJ = []
    for c in K_J:
        rem = []
        for pop in POPS:
            t = joint_rates(data, c, pop)
            if t is None:
                rem = None
                break
            N, X = t
            e = point_rates(N, X)
            if not evaluable(N)[0]:
                continue
            lo = flag_cells(e, W.rates(N, X), [0], LEVEL_RMJ)
            if lo["flag"][0]:
                rem.append({"pop": pop, "lb": fnum(lo["bound"][0]), "zero_se": bool(lo["zero_flag"][0]),
                            "lb_mcse": fnum(lo["bound_mcse"][0])})
        out["comparators"][c] = {"removed_by": rem, "in_VJ": rem == []}
        if rem == []:
            VJ.append(c)
    rate_m = data.inf("MstarJx")
    rates = {c: data.inf(c) for c in VJ}
    fb = form_b(W, rate_m, rates, VJ, level_alpha=ALPHA_FOR / 2, p_multiplier=2)
    out["VJ"] = VJ
    out["form"] = fb
    out["met_bound_form"] = bool(out["validJ_method"] and fb["all_lower"])      # vacuous part counts as holding
    out["met_family_S"] = bool(out["met_bound_form"] and not fb["vacuous"])        # a vacuous part gives p = 1
    out["p"] = 1.0 if fb["vacuous"] else fb["p"]
    return out


# ------------------------------------------------------------------ the K8 arm table ("Table XII")
def k8_table(data, W, route, mem=None, arms=None):
    """Per arm (every arm of the run and RETUNED): per population records, exceedances, units, evaluable cells, the cells at
    0.95 (Ê, SE, LB, UB, flag), validity at the arm's C1 level (comparators of K at the route's removal level, every other
    arm at 0.95: flagged cells, pooled LB and flag), pooled UB at 0.995 and HK1c, infeasibility (mean, percentile CI95),
    record-weighted mean margins, V2 and its variants with the reference."""
    arms = arms or (data.arms + (["RETUNED"] if data.arm_rows("RETUNED") is not None else []))
    out = {}
    for a in arms:
        row = {"pops": {}}
        level_c1 = removal_level(route) if a in COMPS else LEVEL_M
        row["level_C1"] = level_c1
        f = data.inf(a)
        if f is not None:
            bm = W.means(f)
            row["infeasible_rate"] = fnum(np.mean(f))
            row["infeasible_ci95"] = [fnum(np.quantile(bm, 0.025)), fnum(np.quantile(bm, 0.975))]
            row["infeasible_ci95_mcse"] = [fnum(quantile_mcse(bm, 0.025)), fnum(quantile_mcse(bm, 0.975))]
            r = data.arm_rows(a)
            row["decisions"] = float(data.dec_count[r, np.arange(data.U)].sum())
            if a != "Mstar":
                row["Mstar_minus_arm_infeasible"] = fnum(np.mean(data.inf("Mstar") - f))
        for pop in POPS4:
            N, X = data.table(a, pop)
            ev = np.flatnonzero(evaluable(N))
            pr = {"records": float(N.sum()), "exceed": float(X.sum()), "units": int((N.sum(1) > 0).sum()),
                  "n_evaluable": int(len(ev)), "evaluable": [CELLNAMES[j] for j in ev]}
            est = point_rates(N, X)
            boot = W.rates(N, X) if len(ev) else None
            if len(ev):
                rf = flag_cells(est, boot, ev, LEVEL_M)
                up = supt(est, boot, ev, LEVEL_M, "upper")
                pr["flagged_0.95"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(rf["flag"])]
                pr["cells"] = {CELLNAMES[j]: {"E": fnum(est[j]), "se": fnum(rf["se"][i]), "lb": fnum(rf["bound"][i]),
                                              "lb_mcse": fnum(rf["bound_mcse"][i]), "ub": fnum(up["bound"][i]),
                                              "ub_mcse": fnum(up["bound_mcse"][i]), "flag": bool(rf["flag"][i]),
                                              "records": float(N[:, j].sum()), "exceed": float(X[:, j].sum()),
                                              "units": int((N[:, j] > 0).sum())} for i, j in enumerate(ev)}
                rc = rf if level_c1 == LEVEL_M else flag_cells(est, boot, ev, level_c1)
                pr["flagged"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(rc["flag"])]
                pr["q_cells"] = fnum(rc["q"])
                pr["flag_lb_C1"] = {CELLNAMES[ev[i]]: fnum(rc["bound"][i]) for i in range(len(ev))}
                pr["flag_lb_C1_mcse"] = {CELLNAMES[ev[i]]: fnum(rc["bound_mcse"][i]) for i in range(len(ev))}
            else:
                pr["flagged_0.95"], pr["flagged"], pr["q_cells"], pr["cells"] = [], [], None, {}
                pr["flag_lb_C1"], pr["flag_lb_C1_mcse"] = {}, {}
            Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
            pe = point_rates(Np, Xp)
            pr["pooled_E"] = fnum(pe[0])
            pr["pooled_evaluable"] = bool(evaluable(Np)[0])
            pr["pooled_flagged"], pr["HK1c"] = False, False
            if (Np > 0).any():
                pb = W.rates(Np, Xp)
                lo = flag_cells(pe, pb, [0], level_c1)
                up1 = supt(pe, pb, [0], L_HK1C, "upper")
                pr["pooled_lb"] = fnum(lo["bound"][0])
                pr["pooled_lb_mcse"] = fnum(lo["bound_mcse"][0])
                pr["pooled_flagged"] = bool(lo["flag"][0])
                pr["pooled_ub"] = fnum(up1["bound"][0])
                pr["pooled_ub_mcse"] = fnum(up1["bound_mcse"][0])
                pr["pooled_ub_percentile"] = fnum(np.nanquantile(pb[:, 0], L_HK1C))
                pr["HK1c"] = bool(pr["pooled_evaluable"] and pr["pooled_ub"] is not None and pr["pooled_ub"] <= DELTA + HK1C_MARGIN)
            r_ = data.arm_rows(a)
            if a == "RETUNED":
                pr["mean_margin_long"] = pr["mean_margin_lat"] = None     # cal sums are per arm, not per unit: not composed
            else:
                sm = data.margins[pop][r_[0]]
                pr["cal_records"] = float(sm[0])
                pr["mean_margin_long"] = fnum(sm[1] / sm[0]) if sm[0] > 0 else None
                pr["mean_margin_lat"] = fnum(sm[2] / sm[0]) if sm[0] > 0 else None
            for var in V2_VARIANTS:
                if var not in data.v2[pop]:
                    continue
                d, x = data.v2_table(a, pop, var)
                m = d > 0
                v = {"E": fnum(np.mean(x[m] / d[m])) if m.any() else None, "decisions_with_records": float(d.sum()),
                     "decisions_any": float(x.sum()), "decision_level_rate": fnum(x.sum() / d.sum()) if d.sum() > 0 else None,
                     "units": int(m.sum())}
                if m.any():
                    bv = W.rates(d[:, None], x[:, None])[:, 0]
                    v["ci95"] = [fnum(np.nanquantile(bv, 0.025)), fnum(np.nanquantile(bv, 0.975))]
                    v["ci95_mcse"] = [fnum(quantile_mcse(bv, 0.025)), fnum(quantile_mcse(bv, 0.975))]
                if var == "V2":
                    den, ref, trs = data.v2_ref(a, pop)
                    mm = den > 0
                    v["reference_E"] = fnum(np.mean(ref[mm] / den[mm])) if mm.any() else None
                    v["mean_tracks_per_decision"] = fnum(trs.sum() / den.sum()) if den.sum() > 0 else None
                pr[var] = v
            row["pops"][pop] = pr
        out[a] = row
        if mem:
            mem.check("k8 table %s" % a)
    return out


def versions():
    import platform
    return {"python": platform.python_version(), "numpy": np.__version__, "executable": sys.executable}
