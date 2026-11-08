#!/usr/bin/env python3
"""C1 criteria sensitivity (c1crit, v01, 5 Nov 2026): shared loaders and rules. nuScenes DEVELOPMENT DATA ONLY (the K8 Linux
replicate, 840 scenes, 68 logs, decision mode). No Argoverse 2 file is read by anything in 50_CODE/c1_criteria/.

Reuse, not reimplementation:
  - the per-scene x cell record / exceedance tables come from c1_power_counts_v02.load_tracker and log_map (imported, unchanged);
  - the validity rule on each arm is k8_analyse_v03.hk1_rule (imported, unchanged), which calls k6_analyse_v02.rates / flag /
    evaluable / power_family and m_lib_v04._simul. Power settings are changed only by setting the module globals of
    k6_analyse_v02 (POWER_P, POWER_RHO, POWER_REPS) inside this process; no file is edited;
  - the C1 status of an arm is c1_analyse_v02.arm_status (the v07c rule: ShownAbove includes failing HK1c), re-expressed here with
    F_MIN and the HK1c margin as parameters (status_from_hk1) and asserted equal to arm_status at F_MIN = 6, margin 0.03; the v07d
    rule (D16 v26 Choice 47e: ShownAbove only by a flag) is c1_analyse_v09.comparator_reasons, copied here as shown_above_flags
    because importing c1_analyse_v09 would import c1_guard_v05 (not needed for a development computation);
  - Forms A, B and C use c1_analyse_v02.paired (percentile log-bootstrap bounds of per-scene paired differences).
The K8 v03 analysis's own seeds are used for the reproduction: bootstrap default_rng([20261106, i, 0]) (i = 0 T1, 1 T3), power
[20261107, i] for M* and [20261107, i, 100 + ARM_INDEX[a]] for comparator a, then + [k] per population (hk1_rule).
"""
import hashlib
import json
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "c1_av2"))
import k6_analyse_v02 as A  # noqa: E402
import k8_analyse_v03 as K8  # noqa: E402
import c1_power_counts_v02 as PC2  # noqa: E402   (load_tracker / log_map on the K8 Linux replicate; reads no AV2 file)
import c1_analyse_v02 as CA2  # noqa: E402        (arm_status, paired, form_a, form_c)

RUNS = os.path.join(W_ROOT, "70_TESTS", "k8_expl_v02_linux")
ANALYSIS = os.path.join(W_ROOT, "70_TESTS", "k8_expl_v02_linux_analysis_v03", "k8_exploratory_analysis_v03.json")
OUT = os.path.join(W_ROOT, "60_RESULTS", "c1_criteria_sensitivity_v01")
CACHE = os.path.join(OUT, "cache")
TAGS = ("t1", "t3")
TIDX = {"t1": 0, "t3": 1}
ARMS = list(PC2.ARMS)                     # ['Mstar', 'B0', 'B1', 'B3', 'B4', 'B6', 'B9', 'RETUNED']
COMPS = [a for a in ARMS if a != "Mstar"]
POPS = K8.CONF_POPS                       # PD7_primary, SD1_7_gap_le_5m, PD_inpath
FLOOR_POPS = K8.FLOOR_POPS
LAB = {"PD7_primary": "PD7", "SD1_7_gap_le_5m": "SD1_7", "PD_inpath": "PD"}
CELLS = A.cell_family()
CELL_NAMES = [c[0] for c in CELLS]
DELTA = 0.05
SEED_BOOT_K8, SEED_POWER_K8 = K8.SEED, K8.POWER_SEED     # 20261106, 20261107
DEFAULTS = {"POWER_P": A.POWER_P, "POWER_RHO": A.POWER_RHO, "POWER_REPS": A.POWER_REPS, "F_MIN": 6, "HK1C": 0.03, "C": 0.03}
assert (DEFAULTS["POWER_P"], DEFAULTS["POWER_RHO"], DEFAULTS["POWER_REPS"]) == (0.15, 0.5, 200)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdump(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    os.replace(tmp, path)


def load_analysis():
    with open(ANALYSIS) as f:
        return json.load(f)


# ------------------------------------------------------------------ data
def cache_path(tag):
    return os.path.join(CACHE, "dev_tables_%s_v01.npz" % tag)


def build_cache(tag, J=None):
    """Per tracker: scenes, log index, the (arm x scene x cell) N and X tables of PD7, SD1_7, PD, and the per-scene infeasible rate
    of every arm (episodes' infeasible_frames / frames, as k8_analyse_v03.analyse_decide). RETUNED per the analysis's
    arm_of_scene (cross-fitted selection)."""
    os.makedirs(CACHE, exist_ok=True)
    J = J or load_analysis()
    aos = J["decide"][tag]["retune"]["arm_of_scene"]
    scenes, tab, _F = PC2.load_tracker(tag, aos)
    del _F
    log_idx, logs = PC2.log_map(scenes)
    inf = {}
    with open(os.path.join(RUNS, "episodes_%s_decide.jsonl" % tag)) as f:
        for line in f:
            o = json.loads(line)
            if o.get("entered") and o["scene"] not in PC2.DEV_SCENES and o["arm"] != "LOG":
                inf[(o["scene"], o["arm"])] = (o["infeasible_frames"], o["frames"])
    rate = np.zeros((len(ARMS), len(scenes)))
    for i, a in enumerate(ARMS):
        for k, s in enumerate(scenes):
            src = aos[s] if a == "RETUNED" else a
            x, n = inf[(s, src)]
            rate[i, k] = x / max(n, 1)
    arrs = {"scenes": np.array(scenes), "log_idx": np.asarray(log_idx), "logs": np.array(logs), "rate": rate, "arms": np.array(ARMS)}
    for p in POPS:
        arrs["N_" + LAB[p]] = tab[p][0]
        arrs["X_" + LAB[p]] = tab[p][1]
    np.savez_compressed(cache_path(tag), **arrs)
    return cache_path(tag)


class Dev:
    """One tracker's development tables."""

    def __init__(self, tag):
        z = np.load(cache_path(tag), allow_pickle=False)
        self.tag, self.i = tag, TIDX[tag]
        self.scenes = z["scenes"]
        self.log_idx = z["log_idx"].astype(int)
        self.n_logs = int(len(z["logs"]))
        self.rate = {a: z["rate"][k] for k, a in enumerate(ARMS)}
        self.N = {p: z["N_" + LAB[p]] for p in POPS}
        self.X = {p: z["X_" + LAB[p]] for p in POPS}

    def T(self, arm):
        k = ARMS.index(arm)
        return {p: (self.N[p][k], self.X[p][k]) for p in POPS}

    def weights(self, seed=None, B=None):
        """K8 v03's log bootstrap: W_logs = default_rng(seed).multinomial(n_logs, 1/n_logs, B); returns (W per scene, W_logs)."""
        seed = [SEED_BOOT_K8, self.i, 0] if seed is None else seed
        B = B or A.B_BOOT
        rng = np.random.default_rng(seed)
        Wl = rng.multinomial(self.n_logs, np.full(self.n_logs, 1.0 / self.n_logs), size=B).astype(float)
        return Wl[:, self.log_idx], Wl


def power_key(i, arm, base=None):
    base = SEED_POWER_K8 if base is None else base
    return [base, i] if arm == "Mstar" else [base, i, 100 + K8.ARM_INDEX[arm]]


class power_settings:
    """Context manager: temporarily set k6_analyse_v02's power globals (P, rho, reps) in this process."""

    def __init__(self, P=None, rho=None, reps=None):
        self.new = {"POWER_P": P, "POWER_RHO": rho, "POWER_REPS": reps}

    def __enter__(self):
        self.old = {k: getattr(A, k) for k in self.new}
        for k, v in self.new.items():
            if v is not None:
                setattr(A, k, v)
        return self

    def __exit__(self, *exc):
        for k, v in self.old.items():
            setattr(A, k, v)
        return False


def validity_all(dev, W, power_base=None, arms=ARMS, fams=None, strict_mstar=False):
    """k8_analyse_v03.hk1_rule on every arm with the K8 power keys. strict_mstar=False records a non-finite M* quantile as None
    (as v09's m13) instead of raising; on the development data it is finite at the K8 seeds."""
    old = K8.STRICT_Q
    K8.STRICT_Q = bool(strict_mstar)
    try:
        out = {}
        for a in arms:
            out[a] = K8.hk1_rule(dev.T(a), CELLS, dev.scenes, dev.log_idx, W, power_key(dev.i, a, power_base),
                                 fams=None if fams is None else fams.get(a), arm=a)
        return out
    finally:
        K8.STRICT_Q = old


# ------------------------------------------------------------------ rules (parametrised)
def status_from_hk1(v, f_min=6, hk1c=0.03):
    """c1_analyse_v02.arm_status with F_MIN and the HK1c margin as parameters, plus the v07d ShownAbove (flags only).
    Returns valid (C1 Valid), shown_v07c (v02/v07c: a flag, a family flag, the pooled cell flagged, or HK1c failed),
    shown_v07d (D16 Choice 47e: a flag, a family flag or the pooled cell flagged), valid_k8 (k8_analyse_v03.form_valid with the
    floor at f_min and HK1c at margin hk1c), and the per-population parts."""
    per, valid, sh7c, sh7d, valid_k8 = {}, True, False, False, True
    for p in POPS:
        r = v["pops"][p]
        pooled = r.get("pooled")
        nf, ff, pe = not r.get("flagged"), bool(r.get("family_flagged")), pooled is not None
        nfp = pe and not pooled["flagged"]
        hk = pe and bool(pooled["ub"] <= DELTA + hk1c)
        floor = (int(r.get("family_size") or 0) >= f_min) if p in FLOOR_POPS else (int(r.get("evaluable") or 0) >= 1)
        ok = bool(nf and not ff and nfp and floor and hk)
        s7c = bool((not nf) or ff or (pe and not nfp) or (pe and not hk))
        s7d = bool((not nf) or ff or (pe and not nfp))
        # k8_analyse_v03: HK1a = no flag, >= 1 evaluable, floor (PD7, SD1_7) and no family flag; HK1b = pooled evaluable, not flagged
        a_ok = (not r.get("flagged")) and int(r.get("evaluable") or 0) >= 1 and not ff
        if p in FLOOR_POPS:
            a_ok = a_ok and int(r.get("family_size") or 0) >= f_min
        k8ok = bool(a_ok and nfp and hk)
        per[p] = {"NoFlag": nf, "FamFlag": ff, "pooled_evaluable": pe, "NoFlag_pool": nfp, "Floor": floor, "HK1c": hk,
                  "valid": ok, "shown_v07c": s7c, "shown_v07d": s7d, "family_size": r.get("family_size"),
                  "evaluable": r.get("evaluable"), "n_flagged": len(r.get("flagged") or []),
                  "n_family_flagged": len(r.get("family_flagged") or []), "pooled_ub": pooled["ub"] if pe else None}
        valid, sh7c, sh7d, valid_k8 = valid and ok, sh7c or s7c, sh7d or s7d, valid_k8 and k8ok
    return {"valid": bool(valid), "shown_v07c": bool(sh7c), "shown_v07d": bool(sh7d), "valid_k8": bool(valid_k8), "pops": per}


def check_status_equivalence(vba):
    """At F_MIN 6 and HK1c 0.03, status_from_hk1 must equal c1_analyse_v02.arm_status (valid, shown_above) and
    k8_analyse_v03.form_valid for every arm."""
    bad = []
    for a, v in vba.items():
        s = status_from_hk1(v)
        ref = CA2.arm_status(v)
        if s["valid"] != ref["valid"] or s["shown_v07c"] != ref["shown_above"] or s["valid_k8"] != K8.form_valid(v):
            bad.append(a)
    return bad


def forms(dev, Ws, status, c=0.03):
    """Forms A, B (three comparator rules) and C on the per-scene infeasible rates; percentile log-bootstrap bounds
    (c1_analyse_v02.paired; Ws = per-scene weights, scenes are the keys in decision mode)."""
    rate = dev.rate
    out = {"valid_Mstar": status["Mstar"]["valid"]}
    fa = CA2.form_a({"Mstar": {"valid": status["Mstar"]["valid"]}}, rate, Ws)
    out["A"] = {"met": fa["met"], "ub": {k: v["ub"] for k, v in fa["vs"].items()}}
    rules = {"v07d_flags_only": lambda s: not s["shown_v07d"], "v07c_flags_or_hk1c": lambda s: not s["shown_v07c"],
             "k8_valid_only": lambda s: s["valid_k8"]}
    for name, keep in rules.items():
        V = [x for x in COMPS if keep(status[x])]
        level = 1 - 0.05 / max(len(V), 1)
        ubs = {x: CA2.paired(rate, Ws, "Mstar", x, level)["ub"] for x in V}
        valid_m = status["Mstar"]["valid_k8"] if name == "k8_valid_only" else status["Mstar"]["valid"]
        out["B_" + name] = {"V": V, "level": level, "ub": ubs, "met": bool(valid_m and all(u < 0 for u in ubs.values())),
                            "vacuous": not V}
    r = CA2.paired(rate, Ws, "Mstar", "B4", 0.95)
    out["C"] = {"ub": r["ub"], "mean_diff": r["mean_diff"], "c": c, "met": bool(r["ub"] <= c)}
    return out


def verdict_summary(status, fm):
    """Compact verdict line per tracker."""
    return {"valid_Mstar": status["Mstar"]["valid"],
            "not_shown_v07d": [x for x in COMPS if not status[x]["shown_v07d"]],
            "not_shown_v07c": [x for x in COMPS if not status[x]["shown_v07c"]],
            "valid_k8": [x for x in COMPS if status[x]["valid_k8"]],
            "formA": fm["A"]["met"], "formB_v07d": fm["B_v07d_flags_only"]["met"], "formB_v07c": fm["B_v07c_flags_or_hk1c"]["met"],
            "formB_k8": fm["B_k8_valid_only"]["met"], "formC": fm["C"]["met"],
            "family_sizes_Mstar": {LAB[p]: status["Mstar"]["pops"][p]["family_size"] for p in POPS}}
