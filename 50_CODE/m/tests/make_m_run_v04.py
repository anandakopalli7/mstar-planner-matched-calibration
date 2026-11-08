"""Make m_run_v04.py from m_run_v03.py (Claude line, 31 Oct 2026; review R07c). Kept as the record of the changes:
- imports m_data_v04 / m_lib_v04;
- items carry 'chord', and E5 gains 'cog_min_chord_1m' (X-m5);
- the 1 s and 4 s sections are fault-tolerant like E5 (X-m9);
- turning shares of moving items by speed band are reported from counts (X-m5).
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(HERE, "m_run_v03.py"), encoding="utf-8").read()
R = [
    ('"""Method stage run v03 (Claude line, 31 Oct 2026): evaluations of 40_PROTOCOL/M_PREREGISTRATION_v04 for one tracker setting.',
     '"""Method stage run v04 (Claude line, 31 Oct 2026): evaluations of 40_PROTOCOL/M_PREREGISTRATION_v05 for one tracker setting.\n'
     'v04 (R07c):\n'
     '- the v04 modules;\n'
     '- the minimum-chord sensitivity;\n'
     '- fault-tolerant 1 s and 4 s sections;\n'
     '- turning shares by speed band.'),
    ("import m_data_v03 as MD\nimport m_lib_v03 as M", "import m_data_v04 as MD\nimport m_lib_v04 as M"),
    ('ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "V", "contested", "D")',
     'ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "chord", "V", "contested", "D")'),
    ('''        "sigma_0": {"sigma_a": 0.0}, "sigma_0.20": {"sigma_a": 0.20}, "n_min_39": {"n_min": 39}}''',
     '''        "sigma_0": {"sigma_a": 0.0}, "sigma_0.20": {"sigma_a": 0.20}, "n_min_39": {"n_min": 39}, "cog_min_chord_1m": {"omega": "omc_chord1"}}'''),
    ('''    for h in ("h2s", "h1s", "h4s"):
        (ti, trc), (vi, vrc) = tr[h], va[h]
        c1, c2 = cells_from(sizes["train"][h]["cells"]), cells_from(sizes["val"][h]["cells"])
        dec = h == "h2s"
        res["E1_" + h] = run_e1(ti, trc, {}, tr_names, tr_log, c1, "%s|E1|%s" % (a.tracker, h), B=B1_, refit_B=BR if dec else 0)
        res["E2_" + h] = run_e2(ti, trc, vi, vrc, {}, c2, "%s|E2|%s" % (a.tracker, h), B=B2_ if dec else B2s)
        print(h, "E1", json.dumps(res["E1_" + h].get("hypotheses", {}))[:900], "| E2", json.dumps(res["E2_" + h]["hypotheses"]),
              "| %.0f s" % (time.time() - t0), flush=True)
        save(h)''',
     '''    res["turning_share_by_speed_band"] = {}
    for split, data in (("train", tr), ("val", va)):
        it2 = data["h2s"][0]
        m2 = M.motion_state(it2)
        out_b = {}
        for gname, gi in (("car", 0), ("pedestrian", 1)):
            for lo, hi in ((1, 3), (3, 8), (8, 1e9)):
                sel = (it2["g"] == gi) & (m2 != 0) & (it2["spd"] >= lo) & (it2["spd"] < hi)
                out_b["%s|%g-%s m/s" % (gname, lo, "inf" if hi > 1e8 else "%g" % hi)] = [int(sel.sum()), float(np.mean(m2[sel] == 2)) if sel.any() else None]
        res["turning_share_by_speed_band"][split] = out_b
    for h in ("h2s", "h1s", "h4s"):
        (ti, trc), (vi, vrc) = tr[h], va[h]
        c1, c2 = cells_from(sizes["train"][h]["cells"]), cells_from(sizes["val"][h]["cells"])
        dec = h == "h2s"
        try:
            res["E1_" + h] = run_e1(ti, trc, {}, tr_names, tr_log, c1, "%s|E1|%s" % (a.tracker, h), B=B1_, refit_B=BR if dec else 0)
            res["E2_" + h] = run_e2(ti, trc, vi, vrc, {}, c2, "%s|E2|%s" % (a.tracker, h), B=B2_ if dec else B2s)
        except Exception as ex:
            if dec:
                raise
            res["E1_" + h] = res.get("E1_" + h) or {"error": "%s: %s" % (type(ex).__name__, ex)}
            res["E2_" + h] = {"error": "%s: %s" % (type(ex).__name__, ex), "hypotheses": {}}  # descriptive horizons: recorded, not fatal (R07c X-m9)
        print(h, "E1", json.dumps(res["E1_" + h].get("hypotheses", {}))[:900], "| E2", json.dumps(res["E2_" + h].get("hypotheses", {})),
              "| %.0f s" % (time.time() - t0), flush=True)
        save(h)'''),
]
for x, y in R:
    assert t.count(x) == 1, x[:80]
    t = t.replace(x, y)
open(os.path.join(HERE, "m_run_v04.py"), "w", encoding="utf-8", newline="\n").write(t)
print("m_run_v04.py written,", len(R), "changes")
