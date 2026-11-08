#!/usr/bin/env python3
"""X3 analysis (c2), model-fidelity check of the simulation (x3-stats, v01, 7 Nov 2026). Supplement to plan 2(c2); referee M4.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Added, not pre-specified.

The (c2) simulation draws per-log rates from Beta(mean r_c, ICC rho_c) with rho_c the ANOVA ICC of the observed cell (plan 2(c2)).
This check asks whether that model reproduces the observed sampling variability of the record's estimator (the mean over logs of the
per-log rate) in each cell. For every evaluable cell of M* (and of each comparator removed in r1, on P_rel) it compares
  * the model SE at the cell's observed rate r: sqrt(sum_u r (1 - r) (rho + (1 - rho) / n_u)) / m  (exact under the model, given the
    per-log record counts n_u of the m logs with records), with
  * the record's bootstrap SE of the same cell, (E - LB) / q from the (c1) reproduction on the record's weights (B = 40000), which
    equals the record's own bounds to 5e-15.
A ratio below 1 means the simulated data are less dispersed across logs than the observed data, so power-like quantities at observed
rates are overstated; sizes and coverages are scale-free to first order and depend on the shape (skewness, logs per cell).
No bootstrap is run (light step). Run: python -B x3_stats_c2_modelcheck_v01.py --out-dir <60_RESULTS/x3_explore_v01/c_intervals>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_stats_common_v01 as C  # noqa: E402

L = C.L
REMOVED_R1 = {"t1": ["B0", "B1", "B4", "B6", "B9", "RETUNED"], "t3": ["B1", "B4", "B6", "B9", "RETUNED"]}


def model_se(N, r, rho):
    """(J,) model SE of the mean over logs with records of X/N, per column, under Beta(r, rho)-binomial."""
    pres = N > 0
    m = pres.sum(0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        inv = np.where(pres, 1.0 / np.where(pres, N, 1.0), 0.0)
        v = (r * (1 - r))[None, :] * (rho[None, :] * pres + (1 - rho[None, :]) * inv)
        return np.sqrt(v.sum(0)) / m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    jpath = os.path.join(a.out_dir, "x3_c2_modelcheck_v01.json")
    mpath = os.path.join(a.out_dir, "x3_c2_modelcheck_v01.md")
    for p in (jpath, mpath):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)
    c1p = os.path.join(a.out_dir, "x3_c1_intervals_v01.json")
    with open(c1p, encoding="utf-8") as f:
        c1 = json.load(f)
    out = {"stamp": C.STAMP, "analysis": "X3 (c2) supplement: model-fidelity check of the beta-binomial simulation (added, not pre-specified)",
           "inputs": {"c1_json_sha256": C.sha256(c1p)},
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__, L.__file__)},
           "trackers": {}}
    for t in ("t1", "t3"):
        data = C.load_data(t)
        rt = {}
        for arm in ["Mstar"] + REMOVED_R1[t]:
            pops = C.POPS if arm == "Mstar" else ("PD7_primary",)
            for pop in pops:
                N, X = data.table(arm, pop)
                ev = np.flatnonzero(L.evaluable(N))
                est = L.point_rates(N, X)
                dt = C.deff_table(N, X)
                ms = model_se(N, np.where(np.isfinite(est), est, 0.0), dt["rho"])
                r0 = c1["trackers"][t]["arms"][arm][pop]["i_rec"]
                q = r0["q_cells"]
                rows = {}
                ratios = []
                for j in ev:
                    c = C.CELLNAMES[j]
                    lb = r0["cell_lb"][c]
                    se_obs = (est[j] - lb) / q if q else None
                    ratio = (ms[j] / se_obs) if (se_obs and se_obs > 0) else None
                    rows[c] = {"E": float(est[j]), "rho": float(dt["rho"][j]), "logs": int(dt["k"][j]), "records": float(dt["n"][j]),
                               "se_record_bootstrap": se_obs, "se_model": float(ms[j]), "ratio_model_to_record": ratio}
                    if ratio is not None:
                        ratios.append(ratio)
                rt["%s|%s" % (arm, pop)] = {"cells": rows, "ratio_median": float(np.median(ratios)) if ratios else None,
                                            "ratio_min": float(np.min(ratios)) if ratios else None,
                                            "ratio_max": float(np.max(ratios)) if ratios else None,
                                            "share_cells_ratio_below_0.8": float(np.mean(np.array(ratios) < 0.8)) if ratios else None}
        out["trackers"][t] = rt
        del data
    C.jdump_new(jpath, out)
    lines = ["# X3 (c2) supplement: does the simulation reproduce the observed log-level dispersion? (v01)", "", "**%s**" % C.STAMP, "",
             "Added, not pre-specified. Model SE (beta-binomial with the ANOVA ICC, at the cell's observed rate) against the record's "
             "bootstrap SE of the same cell, evaluable cells only. JSON: `x3_c2_modelcheck_v01.json`.", "",
             "| Tracker | Arm / population | Cells | Median ratio model/record | Min | Max | Share of cells below 0.8 |", "|---|---|---|---|---|---|---|"]
    for t, rt in out["trackers"].items():
        for k, v in rt.items():
            lines.append("| %s | %s | %d | %s | %s | %s | %s |" % (t, k, len(v["cells"]), *["-" if v[x] is None else "%.2f" % v[x] for x in (
                "ratio_median", "ratio_min", "ratio_max", "share_cells_ratio_below_0.8")]))
    lines += ["", "Reading: a ratio below 1 means the simulated per-log rates are less dispersed than the observed ones, so quantities "
              "that depend on the scale (power or flag rates at the observed rates) are overstated by the simulation; the false-removal "
              "rates and coverages at truth delta are computed inside the simulated world and depend mainly on the shape.", "",
              "Code: `50_CODE/x3/x3_stats_c2_modelcheck_v01.py`.", ""]
    C.text_new(mpath, "\n".join(lines))
    print(time.strftime("%H:%M:%S"), "wrote", jpath, mpath, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
