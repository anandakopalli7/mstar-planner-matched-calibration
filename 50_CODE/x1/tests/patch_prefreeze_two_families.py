"""One-off patch (30 Oct 2026): extend x1_prefreeze_v02.py to two families (t0, h2s) with Bonferroni level 0.975."""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
reps = [
    ('def sizes(export, gt, meta):\n    recs = L.load_export(export)',
     'def sizes(export, gt, meta, horizon=None):\n    recs = L.load_export(export)'),
    ('''    rng = np.random.default_rng(L.SEED)
    out = {"pairing_stats_counts_only"''',
     '''    rng = np.random.default_rng(L.SEED)
    fams = {"t0": rows}
    if horizon:
        hr, hst = L.build_horizon_rows(rows, L.load_horizon(horizon), samples, gtb, racks)
        fams["h2s"] = hr
    out = {"pairing_stats_counts_only"'''),
    ('''           "Q1_paired_share_of_inpath": st.get("paired_inpath", 0) / max(st.get("inpath_records", 1), 1), "cells": {}}
    for sa in (0.10, 0.20):
        cells, scenes, logs = L.cell_items(rows, sigma_a=sa)
        null = L.orientation_null(cells, rng)
        for c in L.CELLS:
            d = cells[c]
            key = "|".join(c)
            entry = out["cells"].setdefault(key, {})''',
     '''           "Q1_paired_share_of_inpath": st.get("paired_inpath", 0) / max(st.get("inpath_records", 1), 1), "families": {}}
    for fam, frows in fams.items():
      out["families"][fam] = {"cells": {}}
      for sa in (0.10, 0.20):
        cells, scenes, logs = L.cell_items(frows, sigma_a=sa)
        null = L.orientation_null(cells, rng)
        for c in L.CELLS:
            d = cells[c]
            key = "|".join(c)
            entry = out["families"][fam]["cells"].setdefault(key, {})'''),
    ('def fwer(sz, reps=500, B=2000, tau=0.5, logit=False):', 'def fwer(sz, reps=500, B=2000, tau=0.5, logit=False, level=0.975, alpha=0.025):'),
    ('''    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    counts = np.array([sz["cells"][c]["per_scene_counts"] for c in cells], dtype=float).T  # (S, G)''',
     '''    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    if not cells:
        return {"eligible_cells": 0, "ok": True, "note": "no eligible cell"}
    counts = np.array([sz["cells"][c]["per_scene_counts"] for c in cells], dtype=float).T  # (S, G)'''),
    ('        lo, hi, _, zero = L.sup_t_band(est, boot, logit=logit)\n        v = L.verdicts(est, lo, hi, zero, np.full(G, L.DELTA))',
     '        lo, hi, _, zero = L.sup_t_band(est, boot, logit=logit, level=level)\n        v = L.verdicts(est, lo, hi, zero, np.full(G, L.DELTA))'),
    ('''    mc_se = math.sqrt(0.05 * 0.95 / reps)
    return {"eligible_cells": G, "reps": reps, "B": B, "tau_logit": tau, "logit_band": logit, "P_any_FAILS": rate,
            "limit": 0.05 + 2 * mc_se, "ok": rate <= 0.05 + 2 * mc_se}''',
     '''    mc_se = math.sqrt(alpha * (1 - alpha) / reps)
    return {"eligible_cells": G, "reps": reps, "B": B, "tau_logit": tau, "logit_band": logit, "level": level, "P_any_FAILS": rate,
            "limit": alpha + 2 * mc_se, "ok": rate <= alpha + 2 * mc_se}'''),
    ('''    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    if len(cells) < 2:
        return {"note": "fewer than 2 eligible cells"}''',
     '''    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    if len(cells) < 2:
        return {"note": "fewer than 2 eligible cells", "targets_met": False}'''),
    ('    ap.add_argument("--sizes")\n', '    ap.add_argument("--sizes")\n    ap.add_argument("--horizon")\n'),
    ('        res = sizes(a.export, a.gt, a.meta)\n', '        res = sizes(a.export, a.gt, a.meta, a.horizon)\n'),
    ('''        sz = json.load(open(a.sizes))
        if a.mode == "fwer":
            r1 = fwer(sz)
            res = {"primary_linear_band": r1}
            if not r1["ok"]:
                res["fallback_logit_band"] = fwer(sz, logit=True)
            res["robustness_tau_1.0"] = fwer(sz, tau=1.0, logit=not r1["ok"])
        else:
            res = oc_q4(sz)''',
     '''        allsz = json.load(open(a.sizes))
        res = {}
        for fam, sz in allsz["families"].items():
            sz = dict(sz, n_scenes=allsz.get("n_scenes"))
            if a.mode == "fwer":
                r1 = fwer(sz)
                fr = {"primary_linear_band": r1}
                if not r1["ok"]:
                    fr["fallback_logit_band"] = fwer(sz, logit=True)
                fr["robustness_tau_1.0"] = fwer(sz, tau=1.0, logit=not r1["ok"])
                res[fam] = fr
            else:
                res[fam] = oc_q4(sz)
        if a.mode == "fwer":
            res["primary_linear_band"] = {"ok": all(res[f]["primary_linear_band"]["ok"] for f in allsz["families"])}
        else:
            res["targets_met"] = all(res[f].get("targets_met", False) for f in allsz["families"])'''),
]
for a, b in reps:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("patched")
