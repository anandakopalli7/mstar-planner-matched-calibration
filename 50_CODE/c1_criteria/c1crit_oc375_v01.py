#!/usr/bin/env python3
"""c1crit_oc375_v01 (5 Nov 2026): the lead's item 7 (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6; plan C8, A2): P(H1 fails) when M*
is (marginally) valid, at 375-unit layouts built from development data ONLY. No AV2 file is read: c1_power_counts_v02.run_oc is
called with matched = False (no AV2 layout match; AV2's counts file is never opened) and theta_d = 1 (every decision kept).

A synthetic confirmation set = 375 nuScenes development scenes drawn with replacement, each its own log (AV2: a log is a scene), with
every arm's per-scene cell counts and per-decision infeasibility flags kept together (c1_power_counts_v02.synth); on each, the coded
validity rule (c1_power_counts_v02.validity: k6_analyse_v02.rates / flag, 200 log-bootstrap weights, the analytic power family at the
module's POWER_P / POWER_RHO) and Forms A, B, C (c1_power_counts_v02.forms) for T1 and T3; H1 = Form B on both.
Variants:
  plugin_v07d  M* and comparators at their development counts; the v07d comparator rule (D16 Choices 47e and 49c: failing HK1c alone
               does not remove a comparator from V_t; the same 3-line wrapper as c1_power_counts_v05.validity_v05, re-stated here
               because importing v05 would import the Trajectron++ tools).
  capped_v07d  M*'s exceedances thinned to delta in every cell whose 840-scene estimate exceeds delta (c1_power_counts_v03.cap_mstar):
               M* is then valid at cell level on the development population, so P(H1 fails) is the rule's false-failure rate.
  plugin_v07c, capped_rho<r>  the older comparator rule; the analytic family at another rho.
What is NOT simulated: new threshold fits. The development data carry one cross-fitted fit (5 log folds of the 850 nuScenes scenes),
and resampling scenes keeps each scene's fold fit; refitting per fold would need a decision-mode planner rerun per refit (see the
note's item 8 cost estimate).
Seeds default_rng([20261212, variant index]). Checkpoint: one JSON per variant in oc375_ckpt/.
Usage: python -B c1crit_oc375_v01.py [--reps 300] [--variants plugin_v07d,capped_v07d,plugin_v07c] [--rho-alt 0.3]
"""
import argparse
import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402
import c1_power_counts_v03 as V3  # noqa: E402   (cap_mstar; imports c1_power_counts_v02 as V2 = C.PC2)

PC2 = C.PC2
assert V3.V2 is PC2
SEED = 20261212
CKPT = os.path.join(C.OUT, "oc375_ckpt")
N_UNITS = 375
_VALIDITY_V02 = PC2.validity


def validity_v07d(T, W_, ev_fn):
    """c1_power_counts_v05.validity_v05's rule: shown = a flagged cell, a flagged power-family cell or a flagged pooled cell."""
    strict, shown, det = _VALIDITY_V02(T, W_, ev_fn)
    shown7d = any(det[p]["flagged"] > 0 or det[p]["family_flagged"] > 0 or det[p]["pooled_flagged"] for p in PC2.CONF_POPS)
    return strict, bool(shown7d), det


def load_trk(J):
    trk = {}
    for tag in C.TAGS:
        aos = J["decide"][tag]["retune"]["arm_of_scene"]
        scenes, tab, F = PC2.load_tracker(tag, aos)
        log_idx, logs = PC2.log_map(scenes)
        trk[tag] = {"scenes": scenes, "tab": tab, "F": F, "log_idx": log_idx, "c": 0.03, "lay": None}
    assert trk["t1"]["scenes"] == trk["t3"]["scenes"]
    return trk


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--variants", default="plugin_v07d,capped_v07d,plugin_v07c")
    ap.add_argument("--rho-alt", type=float, default=0.3)
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    J = C.load_analysis()
    trk = load_trk(J)
    del J
    allv = ["plugin_v07d", "capped_v07d", "plugin_v07c", "capped_rho", "plugin_rho"]
    for var in a.variants.split(","):
        vi = allv.index(var)
        name = var if "rho" not in var else "%s%.4f" % (var, a.rho_alt)
        path = os.path.join(CKPT, "oc375_%s.json" % name)
        if os.path.exists(path):
            print("skip (checkpoint)", name, flush=True)
            continue
        t1 = time.time()
        seed = [SEED, vi] + ([int(round(a.rho_alt * 10000))] if "rho" in var else [])
        rng = np.random.default_rng(seed)
        rho_old = PC2.POWER_RHO
        PC2.validity = _VALIDITY_V02 if var.endswith("v07c") else validity_v07d
        if "rho" in var:
            PC2.POWER_RHO = a.rho_alt
        try:
            if var.startswith("capped"):
                tk, caps = V3.cap_mstar(trk, np.random.default_rng(seed + [7]))
            else:
                tk, caps = trk, None
            out = PC2.run_oc(tk, "scene", False, 1.0, a.reps, rng, N_UNITS)
        finally:
            PC2.validity = _VALIDITY_V02
            PC2.POWER_RHO = rho_old
        out.update({"variant": name, "seed": seed, "caps": caps, "rule": "v07c" if var.endswith("v07c") else "v07d",
                    "power_rho_analytic": a.rho_alt if "rho" in var else rho_old, "n_units": N_UNITS,
                    "P_H1_fails": 1.0 - out["P_H1"], "seconds": time.time() - t1})
        C.jdump(path, out)
        print(name, "P_H1", out["P_H1"], {t: out[t]["P_Mstar_failure_reason"] for t in C.TAGS}, round(out["seconds"], 1), "s", flush=True)
    print("OC375 DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
