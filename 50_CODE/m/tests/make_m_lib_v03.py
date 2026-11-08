"""Make m_lib_v03.py from m_lib_v02.py (Claude line, 31 Oct 2026; review R07b). Kept as the record of the changes:
- N-M1: course-over-ground heading rate (from the track's own exported positions) is the default turning signal for every
  group; yaw and velocity-direction rates kept for sensitivities.
- N-M2: a baseline fails on the refit-CV inference (primary); the fixed rule is reported beside it.
- N-m2: HM3 testability recorded.
- N-m6: HM6b uses a bias-corrected upper bound.
- N-m7: sd floor so that sigma_a = 0 cannot divide by zero.
- N-m13: B2 cap flag kept.
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(HERE, "m_lib_v02.py"), encoding="utf-8").read()
R = []
R.append(('"""Method-stage library v02 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION_v03 sections 3-7.',
          '"""Method-stage library v03 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION_v04 sections 3-7.\n'
          'Changes from v02 (review R07b):\n'
          '- the default turning signal is the course-over-ground turn rate from the track\'s own positions, for every group (N-M1);\n'
          '- a baseline fails on the refit-CV inference, with the fixed rule reported beside it (N-M2);\n'
          '- HM3 testability is recorded (N-m2);\n'
          '- HM6b uses a bias-corrected upper bound (N-m6);\n'
          '- sd has a floor (N-m7);\n'
          '- the B2 cap flag is kept (N-m13).'))
# motion index and features
R.append(('''    return {(r["scene"], r["tid"], r["k"]): (r["yaw"], math.atan2(r["vy"], r["vx"]), ts[(r["scene"], r["k"])], math.hypot(r["vx"], r["vy"]))
            for r in recs}''',
          '''    return {(r["scene"], r["tid"], r["k"]): (r["yaw"], math.atan2(r["vy"], r["vx"]), ts[(r["scene"], r["k"])], math.hypot(r["vx"], r["vy"]),
                                             r["x"], r["y"])
            for r in recs}'''))
R.append(('''def motion_features(mi, scene, tid, k):
    yaw, vh, t, spd = mi[(scene, tid, k)]
    prev = mi.get((scene, tid, k - 2)) or mi.get((scene, tid, k - 1))
    if prev is None:
        return spd, float("nan"), float("nan")
    dt = t - prev[2]
    return spd, wrap_half(yaw - prev[0]) / dt, L.wrap(vh - prev[1]) / dt''',
          '''def motion_features(mi, scene, tid, k):
    """Speed and three heading rates from the track's own exported estimates (I_k-measurable):
    yaw rate (yaw at k against k-2, else k-1; half-angle wrap), velocity-direction rate (same records), and the
    course-over-ground rate: the change in the displacement direction between [k-4, k-2] and [k-2, k] (else [k-2, k-1]
    and [k-1, k]) divided by the time between the two midpoints. Undefined (NaN) without the needed history."""
    yaw, vh, t, spd, x, y = mi[(scene, tid, k)]
    prev = mi.get((scene, tid, k - 2)) or mi.get((scene, tid, k - 1))
    om, omv, omc = float("nan"), float("nan"), float("nan")
    if prev is not None:
        dt = t - prev[2]
        om, omv = wrap_half(yaw - prev[0]) / dt, L.wrap(vh - prev[1]) / dt
    for j in (2, 1):
        a, b = mi.get((scene, tid, k - 2 * j)), mi.get((scene, tid, k - j))
        if a is not None and b is not None:
            h1 = math.atan2(b[5] - a[5], b[4] - a[4])
            h2 = math.atan2(y - b[5], x - b[4])
            omc = L.wrap(h2 - h1) / (0.5 * (t - a[2]))
            break
    return spd, om, omv, omc'''))
R.append(('''        spd, om, omv = motion_features(mi, r["scene"], r["tid"], r["k"])''',
          '''        spd, om, omv, omc = motion_features(mi, r["scene"], r["tid"], r["k"])'''))
R.append(('''                    for k_, v_ in (("g", g), ("r", rg), ("a", 0 if name == "long" else 1), ("spd", spd), ("om", om), ("omv", omv)):''',
          '''                    for k_, v_ in (("g", g), ("r", rg), ("a", 0 if name == "long" else 1), ("spd", spd), ("om", om), ("omv", omv), ("omc", omc)):'''))
R.append(('''                           ("spd", spd), ("om", om), ("omv", omv), ("V", var), ("contested", bool(r.get("contested"))),''',
          '''                           ("spd", spd), ("om", om), ("omv", omv), ("omc", omc), ("V", var), ("contested", bool(r.get("contested"))),'''))
R.append(('''def omega_used(items, omega="default"):
    """Heading rate used for the motion state: yaw-based, except velocity-direction-based for pedestrians (default)."""
    if omega == "default":
        return np.where(items["g"] == 1, items["omv"], items["om"])
    return items[omega]''',
          '''def omega_used(items, omega="default"):
    """Heading rate used for the motion state: course over ground for every group (default, 'omc'); 'om' yaw rate and 'omv'
    velocity-direction rate for sensitivities."""
    return items["omc" if omega == "default" else omega]'''))
R.append(('''    for k in ("g", "r", "a", "spd", "om", "omv", "V", "contested", "D"):''',
          '''    for k in ("g", "r", "a", "spd", "om", "omv", "omc", "V", "contested", "D"):'''))
# sd floor
R.append(('''    sd = np.sqrt(items["V"] + sa ** 2)
    S11, S12, S22''', '''    sd = np.sqrt(np.maximum(items["V"] + sa ** 2, 1e-6))
    S11, S12, S22'''))
# B2 cap flag
R.append(('''    svals = []
    for c in np.unique(lv[1]):
        sel = lv[1] == c
        if len(np.unique(s[sel])) >= n_min:
            svals.append(L.inflation_needed(D[sel], V[sel], SA[sel])[0])
    fit["B2"] = max(svals)''', '''    svals, caps = [], []
    for c in np.unique(lv[1]):
        sel = lv[1] == c
        if len(np.unique(s[sel])) >= n_min:
            sv, cap = L.inflation_needed(D[sel], V[sel], SA[sel])
            svals.append(sv)
            caps.append(bool(cap))
    fit["B2"] = max(svals)
    fit["B2_cap_hit"] = bool(any(caps))'''))
# hypotheses
R.append(('''def hypotheses_e1(st_fixed, st_refit):
    both = [st_fixed, st_refit]
    h = {"HM1": not any(st["methods"]["Mstar"]["any_sig_under"] for st in both),
         "Mstar_flagged_cells": sorted(set(c for st in both for c in st["methods"]["Mstar"]["sig_under_cells"]))}
    h["HM2"] = {b: failures(both, b, "%s-Mstar" % b) for b in PRACTITIONER}
    h["HM2_any"] = any(bool(v) for v in h["HM2"].values())
    h["HM2b"] = {b: failures(both, b, "%s-Mstar" % b) for b in ABLATIONS}
    h["HM3"] = failures(both, "B6", "B6-Mstar|car turning")
    h["HM3_holds"] = bool(h["HM3"])''',
          '''def hypotheses_e1(st_fixed, st_refit):
    """HM1 (consistency) under both inferences. Baseline failures (HM2, HM2b, HM3) on the refit-CV inference, which carries
    calibration randomness and is conservative for fitted rules (R07b N-M2); the fixed-rule result is reported beside it."""
    both = [st_fixed, st_refit]
    h = {"HM1": not any(st["methods"]["Mstar"]["any_sig_under"] for st in both),
         "Mstar_flagged_cells": sorted(set(c for st in both for c in st["methods"]["Mstar"]["sig_under_cells"]))}
    h["HM2"] = {b: failures([st_refit], b, "%s-Mstar" % b) for b in PRACTITIONER}
    h["HM2_any"] = any(bool(v) for v in h["HM2"].values())
    h["HM2b"] = {b: failures([st_refit], b, "%s-Mstar" % b) for b in ABLATIONS}
    h["HM3_testable"] = bool(st_refit["paired"].get("B6-Mstar|car turning", {}).get("cells"))
    h["HM3"] = failures([st_refit], "B6", "B6-Mstar|car turning")
    h["HM3_holds"] = bool(h["HM3"])
    h["fixed_rule_also"] = {"HM2": {b: failures(both, b, "%s-Mstar" % b) for b in PRACTITIONER},
                            "HM2b": {b: failures(both, b, "%s-Mstar" % b) for b in ABLATIONS},
                            "HM3": failures(both, "B6", "B6-Mstar|car turning")}'''))
R.append(('''    m, a = st_cells["methods"]["Mstar"], st_all["methods"]["Mstar"]["cells"]["all val items"]
    h = {"HM6a": not m["any_sig_under"], "HM6a_flagged": m["sig_under_cells"],
         "HM6b": a["ub_sim"] <= DELTA + eps, "pooled_E": a["E_scene"], "pooled_ub": a["ub_sim"], "eps": eps}''',
          '''    m, a = st_cells["methods"]["Mstar"], st_all["methods"]["Mstar"]["cells"]["all val items"]
    ub_bc = a["ub_sim"] + max(a["boot_bias"], 0.0)  # bias-corrected (R07b N-m6): replicate means run high
    h = {"HM6a": not m["any_sig_under"], "HM6a_flagged": m["sig_under_cells"],
         "HM6b": ub_bc <= DELTA + eps, "pooled_E": a["E_scene"], "pooled_ub": a["ub_sim"], "pooled_ub_bias_corrected": ub_bc, "eps": eps}'''))
R.append(('''    ml = st_all["methods"]["MLS"]["cells"]["all val items"]
    h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] <= DELTA + eps)''',
          '''    ml = st_all["methods"]["MLS"]["cells"]["all val items"]
    h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] + max(ml["boot_bias"], 0.0) <= DELTA + eps)'''))
# OC speed (R07b N-M3): optional method subset through the same functions; the frozen run fits every method
R.append(('''def fit_methods(items, recs, P, cal_scene, cfg):
    """Fit every method on the calibration scenes (boolean per scene index)."""
    n_min = cfg.get("n_min", N_CRC)''', '''def fit_methods(items, recs, P, cal_scene, cfg, only=None):
    """Fit every method on the calibration scenes (boolean per scene index). only: optional subset of {'Mstar', 'B6'} for
    the operating-characteristic simulation (same code path, fewer methods); the frozen run fits every method."""
    if only is not None:
        return _fit_subset(items, P, cal_scene, cfg, only)
    n_min = cfg.get("n_min", N_CRC)'''))
R.append(('''def margins(items, P, fit, sel):
    """Margin (m) of every method for the selected items."""
    sd, l0 = P["sd"][sel], P["lv"][0][sel]''', '''def _fit_subset(items, P, cal_scene, cfg, only):
    n_min = cfg.get("n_min", N_CRC)
    cal = cal_scene[items["s"]]
    U, s = P["U"][cal], items["s"][cal]
    lv = [x[cal] for x in P["lv"]]
    fit = {"only": tuple(only)}
    fit["Mstar"], fit["Mstar_src"] = fit_hier(U, s, lv, 0, n_min)
    if "B6" in only:
        fit["B6"], fit["B6_src"] = fit_hier(U, s, lv, 1, n_min)
    return fit


def margins(items, P, fit, sel):
    """Margin (m) of every method for the selected items."""
    sd, l0 = P["sd"][sel], P["lv"][0][sel]
    if "only" in fit:
        return {k: fit[k][l0] * sd for k in ("Mstar", "B6") if k in fit}'''))
R.append(('''def cv_once(items, recs, P, cfg, folds_scene):
    """One K-fold cross-validation: per item, the held-out exceedance indicator and margin of every method; the M*
    threshold source level per item."""
    n = len(items["D"])
    exc = {m: np.zeros(n) for m in METHODS}
    marg = {m: np.zeros(n) for m in METHODS}''', '''def cv_once(items, recs, P, cfg, folds_scene, only=None):
    """One K-fold cross-validation: per item, the held-out exceedance indicator and margin of every method (or of the
    subset `only`); the M* threshold source level per item."""
    n = len(items["D"])
    meths = METHODS if only is None else [m for m in ("Mstar", "B6") if m in only or m == "Mstar"]
    exc = {m: np.zeros(n) for m in meths}
    marg = {m: np.zeros(n) for m in meths}'''))
R.append(('''        fit = fit_methods(items, recs, P, cal, cfg)
        sel = ~cal[items["s"]]
        for k, v in margins(items, P, fit, sel).items():
            exc[k][sel] = items["D"][sel] > v''', '''        fit = fit_methods(items, recs, P, cal, cfg, only)
        sel = ~cal[items["s"]]
        for k, v in margins(items, P, fit, sel).items():
            exc[k][sel] = items["D"][sel] > v'''))
R.append(('''    out = None
    for st in st_list:
        pc = st["paired"].get(label, {}).get("cells", {})''', '''    out = None
    for st in st_list:
        if b not in st["methods"]:
            return []
        pc = st["paired"].get(label, {}).get("cells", {})'''))
R.append(('''    h["MLS_consistent"] = not any(st["methods"]["MLS"]["any_sig_under"] for st in both)
    h["Mstar_log_consistent"] = not any(st["methods"]["Mstar_log"]["any_sig_under"] for st in both)''',
          '''    h["MLS_consistent"] = not any(st["methods"].get("MLS", {}).get("any_sig_under", False) for st in both)
    h["Mstar_log_consistent"] = not any(st["methods"].get("Mstar_log", {}).get("any_sig_under", False) for st in both)'''))
R.append(('''    ml = st_all["methods"]["MLS"]["cells"]["all val items"]
    h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] + max(ml["boot_bias"], 0.0) <= DELTA + eps)''',
          '''    if "MLS" in st_all["methods"]:
        ml = st_all["methods"]["MLS"]["cells"]["all val items"]
        h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] + max(ml["boot_bias"], 0.0) <= DELTA + eps)'''))
for a, b in R:
    assert t.count(a) == 1, a[:90]
    t = t.replace(a, b)
open(os.path.join(HERE, "m_lib_v03.py"), "w", encoding="utf-8", newline="\n").write(t)
print("m_lib_v03.py written,", len(R), "changes")
