"""Make m_lib_v04.py from m_lib_v03.py (Claude line, 31 Oct 2026; review R07c). Kept as the record of the changes:
- X-M1: HM6b is the pooled val cell's significance check (fails if its simultaneous LB > delta), so its size does not hinge
  on a simulated between-log variance; the equivalence bound UB_bc <= delta + EPS_POOLED (EPS_POOLED = 0.03, derived
  from OC v02) is reported, not decided on.
- X-m5: the shorter of the two course-over-ground chords is kept per item ('chord'), for the E5 sensitivity 'omc_chord1'
  (heading rate counted as 0 when a chord is shorter than 1 m).
- X-m4: hypotheses_e1 reports the fixed rule alone and the intersection of both inferences under their own names.
- X-m13: stale docstrings corrected.
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(HERE, "m_lib_v03.py"), encoding="utf-8").read()
R = []
R.append(('"""Method-stage library v03 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION_v04 sections 3-7.\n',
          '"""Method-stage library v04 (Claude line, 31 Oct 2026). Implements 40_PROTOCOL/M_PREREGISTRATION_v05 sections 3-7.\n'
          'Changes from v03 (review R07c):\n'
          '- HM6b is the pooled val cell\'s significance check; the equivalence bound is reported only (X-M1);\n'
          '- items carry the shorter course-over-ground chord, for a sensitivity (X-m5);\n'
          '- the fixed-rule-alone and both-inference failures are reported under their own names (X-m4).\n'))
R.append(("- Pedestrians' heading rate comes from their velocity direction.",
          "- Pedestrians' heading rate came from their velocity direction (superseded in v03: course over ground for all groups)."))
R.append(('EPS_POOLED = 0.02  # HM6b tolerance on the pooled val exceedance',
          'EPS_POOLED = 0.03  # descriptive equivalence margin for the pooled val exceedance (from OC v02; plan v05 section 9)'))
R.append(('''    """(scene, tid, k) -> (yaw, velocity heading, time [s], speed) from the exported track estimates (I_k-measurable)."""''',
          '''    """(scene, tid, k) -> (yaw, velocity heading, time [s], speed, x, y) from the exported track estimates (I_k-measurable)."""'''))
R.append(('''    yaw, vh, t, spd, x, y = mi[(scene, tid, k)]
    prev = mi.get((scene, tid, k - 2)) or mi.get((scene, tid, k - 1))
    om, omv, omc = float("nan"), float("nan"), float("nan")''', '''    yaw, vh, t, spd, x, y = mi[(scene, tid, k)]
    prev = mi.get((scene, tid, k - 2)) or mi.get((scene, tid, k - 1))
    om, omv, omc, chord = float("nan"), float("nan"), float("nan"), float("nan")'''))
R.append(('''            omc = L.wrap(h2 - h1) / (0.5 * (t - a[2]))
            break
    return spd, om, omv, omc''', '''            omc = L.wrap(h2 - h1) / (0.5 * (t - a[2]))
            chord = min(math.hypot(b[4] - a[4], b[5] - a[5]), math.hypot(x - b[4], y - b[5]))
            break
    return spd, om, omv, omc, chord'''))
R.append(('''        spd, om, omv, omc = motion_features(mi, r["scene"], r["tid"], r["k"])''',
          '''        spd, om, omv, omc, chord = motion_features(mi, r["scene"], r["tid"], r["k"])'''))
R.append(('''                    for k_, v_ in (("g", g), ("r", rg), ("a", 0 if name == "long" else 1), ("spd", spd), ("om", om), ("omv", omv), ("omc", omc)):''',
          '''                    for k_, v_ in (("g", g), ("r", rg), ("a", 0 if name == "long" else 1), ("spd", spd), ("om", om), ("omv", omv), ("omc", omc),
                                   ("chord", chord)):'''))
R.append(('''                           ("spd", spd), ("om", om), ("omv", omv), ("omc", omc), ("V", var), ("contested", bool(r.get("contested"))),''',
          '''                           ("spd", spd), ("om", om), ("omv", omv), ("omc", omc), ("chord", chord), ("V", var), ("contested", bool(r.get("contested"))),'''))
R.append(('''    """Heading rate used for the motion state: course over ground for every group (default, 'omc'); 'om' yaw rate and 'omv'
    velocity-direction rate for sensitivities."""
    return items["omc" if omega == "default" else omega]''',
          '''    """Heading rate used for the motion state: course over ground for every group (default, 'omc'); 'om' yaw rate, 'omv'
    velocity-direction rate, and 'omc_chord1' (course over ground counted as 0 when either chord is shorter than 1 m) for
    sensitivities."""
    if omega == "omc_chord1":
        return np.where(np.isfinite(items["omc"]) & (items["chord"] < 1.0), 0.0, items["omc"])
    return items["omc" if omega == "default" else omega]'''))
R.append(('''    for k in ("g", "r", "a", "spd", "om", "omv", "omc", "V", "contested", "D"):''',
          '''    for k in ("g", "r", "a", "spd", "om", "omv", "omc", "chord", "V", "contested", "D"):'''))
R.append(('''    h["fixed_rule_also"] = {"HM2": {b: failures(both, b, "%s-Mstar" % b) for b in PRACTITIONER},
                            "HM2b": {b: failures(both, b, "%s-Mstar" % b) for b in ABLATIONS},
                            "HM3": failures(both, "B6", "B6-Mstar|car turning")}''',
          '''    h["fixed_rule_alone"] = {"HM2": {b: failures([st_fixed], b, "%s-Mstar" % b) for b in PRACTITIONER},
                             "HM2b": {b: failures([st_fixed], b, "%s-Mstar" % b) for b in ABLATIONS},
                             "HM3": failures([st_fixed], "B6", "B6-Mstar|car turning")}
    h["both_inferences"] = {"HM2": {b: failures(both, b, "%s-Mstar" % b) for b in PRACTITIONER},
                            "HM2b": {b: failures(both, b, "%s-Mstar" % b) for b in ABLATIONS},
                            "HM3": failures(both, "B6", "B6-Mstar|car turning")}'''))
R.append(('''    ub_bc = a["ub_sim"] + max(a["boot_bias"], 0.0)  # bias-corrected (R07b N-m6): replicate means run high
    h = {"HM6a": not m["any_sig_under"], "HM6a_flagged": m["sig_under_cells"],
         "HM6b": ub_bc <= DELTA + eps, "pooled_E": a["E_scene"], "pooled_ub": a["ub_sim"], "pooled_ub_bias_corrected": ub_bc, "eps": eps}''',
          '''    ub_bc = a["ub_sim"] + max(a["boot_bias"], 0.0)  # bias-corrected (R07b N-m6): replicate means run high
    # R07c X-M1: HM6b is the pooled cell's significance check; the equivalence bound is descriptive
    h = {"HM6a": not m["any_sig_under"], "HM6a_flagged": m["sig_under_cells"],
         "HM6b": not a["sig_under"], "pooled_E": a["E_scene"], "pooled_lb": a["lb_sim"], "pooled_ub": a["ub_sim"],
         "pooled_ub_bias_corrected": ub_bc, "pooled_equivalence_at_eps": ub_bc <= DELTA + eps, "eps_descriptive": eps}'''))
R.append(('''        h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and ml["ub_sim"] + max(ml["boot_bias"], 0.0) <= DELTA + eps)''',
          '''        h["MLS_HM6"] = bool(not st_cells["methods"]["MLS"]["any_sig_under"] and not ml["sig_under"])'''))
for a, b in R:
    assert t.count(a) == 1, a[:90]
    t = t.replace(a, b)
open(os.path.join(HERE, "m_lib_v04.py"), "w", encoding="utf-8", newline="\n").write(t)
print("m_lib_v04.py written,", len(R), "changes")
