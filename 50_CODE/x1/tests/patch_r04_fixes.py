"""One-off patch (30 Oct 2026) answering review R04 before the X1 freeze.
lib: h2s ego pose = CTRV prediction from poses k-1, k (I_k-measurable; R04 m10).
full: G1 (a5) truth-oriented FAILS (R04 M1); K5 rule (c) significance-based and certified global comparator (M3, m9);
      prices and certification also at sigma_a = 0, K5 claimed only if supported at both (M2).
"""
import sys

lib, full = sys.argv[1], sys.argv[2]
s = open(lib, encoding="utf-8").read()
a = '''        x, y, sxx, sxy, syy = p[key]
        cx, cy = ego_centre(fut["ego_xyz"][0], fut["ego_xyz"][1], fut["ego_yaw"])
        h.update({"mx": x, "my": y, "S": (sxx, sxy, syy), "cx": cx, "cy": cy, "eyaw": fut["ego_yaw"],'''
b = '''        x, y, sxx, sxy, syy = p[key]
        now, prev = scene_tokens[r["scene"]][r["k"]], scene_tokens[r["scene"]][r["k"] - 1]
        dt = 1e-6 * (now["timestamp"] - prev["timestamp"])
        ex, ey, eyaw = now["ego_xyz"][0], now["ego_xyz"][1], now["ego_yaw"]
        v = ((ex - prev["ego_xyz"][0]) * math.cos(eyaw) + (ey - prev["ego_xyz"][1]) * math.sin(eyaw)) / dt
        w = wrap(eyaw - prev["ego_yaw"]) / dt
        th = steps * 0.5
        if abs(w) < 1e-4:
            px, py, pyaw = ex + v * th * math.cos(eyaw), ey + v * th * math.sin(eyaw), eyaw
        else:
            pyaw = eyaw + w * th
            px, py = ex + v / w * (math.sin(pyaw) - math.sin(eyaw)), ey - v / w * (math.cos(pyaw) - math.cos(eyaw))
        cx, cy = ego_centre(px, py, pyaw)
        h.update({"mx": x, "my": y, "S": (sxx, sxy, syy), "cx": cx, "cy": cy, "eyaw": pyaw,'''
assert s.count(a) == 1
s = s.replace(a, b)
s = s.replace('''    """Horizon family: predicted mean/covariance at k + steps keyframes against the paired instance's annotation and the
    logged ego pose at k + steps.''', '''    """Horizon family: predicted mean/covariance at k + steps keyframes against the paired instance's annotation at k + steps;
    ego pose at k + steps predicted by CTRV from the poses at k - 1 and k (I_k-measurable, R04 m10).''')
open(lib, "w", encoding="utf-8").write(s)

f = open(full, encoding="utf-8").read()
reps = [
    # certified global comparator (vi) and significance-based rule (c)
    ('''    fit["pooled"] = L.crc_threshold(np.concatenate(pu), np.concatenate(ps)) if pu else None
    return fit''',
     '''    fit["pooled"] = L.crc_threshold(np.concatenate(pu), np.concatenate(ps)) if pu else None
    fit["certified_global"] = max(v for v in fit["crc"].values() if v is not None) if any(v is not None for v in fit["crc"].values()) else None
    return fit'''),
    ('''        def summ(ex, margin):
            return {"exc_rec": float(np.mean(ex)), "exc_scene": float(np.mean([np.mean(ex[s == j]) for j in us])),
                    "margin_median_m": float(np.median(margin)), "margin_mean_m": float(np.mean(margin))}''',
     '''        def summ(ex, margin):
            sc_ex = np.array([ex[s == j].sum() for j in us], float)
            sc_n = np.array([(s == j).sum() for j in us], float)
            brng = np.random.default_rng(L.SEED + 7)
            bw = brng.multinomial(len(us), np.full(len(us), 1.0 / len(us)), size=500).astype(float)
            lo = float(np.quantile((bw @ sc_ex) / np.maximum(bw @ sc_n, 1e-12), 0.05))
            return {"exc_rec": float(np.mean(ex)), "exc_rec_lo95": lo, "exc_scene": float(np.mean(sc_ex / sc_n)),
                    "margin_median_m": float(np.median(margin)), "margin_mean_m": float(np.mean(margin))}'''),
    ('''        row["uncalibrated"] = summ(U > L.Z95, L.Z95 * sd)''',
     '''        if fit.get("certified_global") is not None:
            row["certified_global_multiplier"] = summ(U > fit["certified_global"], fit["certified_global"] * sd)
        row["uncalibrated"] = summ(U > L.Z95, L.Z95 * sd)'''),
    ('''    res = {"split_seed": L.SEED, "fit": {"crc": {"|".join(c): v for c, v in fit["crc"].items()}, "c_star": fit["c_star"],
                                          "s_star": fit["s_star"], "pooled": fit["pooled"]},''',
     '''    res = {"split_seed": L.SEED, "fit": {"crc": {"|".join(c): v for c, v in fit["crc"].items()}, "c_star": fit["c_star"],
                                          "s_star": fit["s_star"], "pooled": fit["pooled"], "certified_global": fit.get("certified_global")},'''),
    ('''        k5["b_ok"] = k5["b_total_margin_crc"] < k5["b_total_margin_cstar"] and k5["b_total_margin_crc"] < k5["b_total_margin_sstar"]
        k5["c_any_cell_exceeds_under_pooled_or_uncal"] = any(ho[k].get(m_, {}).get("exc_rec", 0) > L.DELTA for k in ho for m_ in ("pooled_conformal", "uncalibrated"))
        k5["K5_supported"] = bool(k5["a_ok"] and k5["b_ok"] and k5["c_any_cell_exceeds_under_pooled_or_uncal"])''',
     '''        k5["b_total_margin_certified_global"] = tot("certified_global_multiplier")
        k5["b_note"] = "magnitude only (R04 m9): (ii) and (iii) are uncertified; vs the certified global multiplier the saving is the Thm 4 price"
        k5["c_cells_significantly_undercovered"] = [k for k in ho for m_ in ("pooled_conformal", "uncalibrated")
                                                    if ho[k].get(m_, {}).get("exc_rec_lo95", 0) > L.DELTA]
        k5["c_ok"] = len(k5["c_cells_significantly_undercovered"]) > 0
        k5["K5_supported"] = bool(k5["a_ok"] and k5["c_ok"])'''),
    # a5 truth-oriented, prices and certification at sigma_a = 0
    ('''               "a4_contested_excluded": cex.get(key, {}).get("verdict") == "FAILS",''',
     '''               "a4_contested_excluded": cex.get(key, {}).get("verdict") == "FAILS",
               "a5_truth_oriented_fails": sens["truth_oriented_not_measurable"].get(key, {}).get("verdict") == "FAILS",'''),
    ('''        row["holds"] = bool(row["a2_material"] and row["a3_sigma_0.20"] and row["a4_contested_excluded"]
                            and (row["b1_nees_not_overconfident"] or b2))''',
     '''        row["holds"] = bool(row["a2_material"] and row["a3_sigma_0.20"] and row["a4_contested_excluded"] and row["a5_truth_oriented_fails"]
                            and (row["b1_nees_not_overconfident"] or b2))'''),
    ('''    res["certification"] = certification(cells, elig, scene_names, scene_log)
    sens, by_sigma = {}, {}''',
     '''    res["certification"] = certification(cells, elig, scene_names, scene_log)
    cells0, null0, _, elig0, _ = analyse_cells(rows, 0.0, rng, n_sc, scene_names, logit, W)
    pr0, _, _, _ = prices(cells0, elig0, {c: null0[c][1] for c in L.CELLS}, n_sc, rng)
    res["prices_sigma0"] = pr0
    res["certification_sigma0"] = certification(cells0, elig0, scene_names, scene_log)
    res["K5_both_sigma"] = bool(res["certification"]["K5"].get("K5_supported") and res["certification_sigma0"]["K5"].get("K5_supported"))
    sens, by_sigma = {}, {}'''),
]
for a_, b_ in reps:
    assert f.count(a_) == 1, a_[:80]
    f = f.replace(a_, b_)
open(full, "w", encoding="utf-8").write(f)
print("patched lib and full")
