"""Make m_run_v03.py from m_run_v02.py (Claude line, 31 Oct 2026; review R07b). Kept as the record of the changes:
- imports m_data_v03 (Poly-MOT velocity correction) and m_lib_v03;
- items carry the course-over-ground rate 'omc';
- the result JSON is written after every section (N-m7);
- a failing sensitivity is recorded, not fatal (N-m7);
- the B2 cap flag is reported (N-m13);
- the peak working set is reported (N-m10).
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(HERE, "m_run_v02.py"), encoding="utf-8").read()
R = [
    ('"""Method stage run v02 (Claude line, 31 Oct 2026): evaluations of 40_PROTOCOL/M_PREREGISTRATION_v03 for one tracker setting.',
     '"""Method stage run v03 (Claude line, 31 Oct 2026): evaluations of 40_PROTOCOL/M_PREREGISTRATION_v04 for one tracker setting.\n'
     'Changes from v02 (R07b):\n'
     '- the m_data_v03 loader (Poly-MOT velocity correction);\n'
     '- the course-over-ground heading rate;\n'
     '- partial results are written after every section;\n'
     '- a failing sensitivity is recorded, not fatal;\n'
     '- the B2 cap flag and the peak memory are reported.'),
    ("import m_data_v02 as MD\nimport m_lib_v02 as M", "import m_data_v03 as MD\nimport m_lib_v03 as M"),
    ('ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "V", "contested", "D")',
     'ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "V", "contested", "D")'),
    ('    out = {"B3": fit["B3"], "B4": fit["B4"], "B9_radius_m": fit["B9"], "B2_s": fit["B2"], "B7": fit["B7"],',
     '    out = {"B3": fit["B3"], "B4": fit["B4"], "B9_radius_m": fit["B9"], "B2_s": fit["B2"], "B2_cap_hit": fit["B2_cap_hit"], "B7": fit["B7"],'),
    ('''    res["Q0"] = {"train": tinfo, "val": vinfo}
    print("loaded %.0f s" % (time.time() - t0), flush=True)''',
     '''    res["Q0"] = {"train": tinfo, "val": vinfo}
    print("loaded %.0f s" % (time.time() - t0), flush=True)

    def save(stage):
        res["completed_through"] = stage
        res["peak_working_set_mb"] = MD.peak_mb()
        res["wall_s"] = round(time.time() - t0, 1)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1, default=float)'''),
    ('''        print(h, "E1", json.dumps(res["E1_" + h].get("hypotheses", {}))[:900], "| E2", json.dumps(res["E2_" + h]["hypotheses"]),
              "| %.0f s" % (time.time() - t0), flush=True)''',
     '''        print(h, "E1", json.dumps(res["E1_" + h].get("hypotheses", {}))[:900], "| E2", json.dumps(res["E2_" + h]["hypotheses"]),
              "| %.0f s" % (time.time() - t0), flush=True)
        save(h)'''),
    ('''    for name, cfg in SENS.items():
        m = M.motion_state(ti, cfg.get("v_static", M.V_STATIC), cfg.get("w_turn", M.W_TURN), cfg.get("omega", "default"))
        e = run_e1(ti, trc, cfg, tr_names, tr_log, M.make_cells(ti, m, "E1"), "%s|E5|%s" % (a.tracker, name), B=B1_)
        sens[name] = {"fixed": compact(e["fixed"]), "pooled": e["pooled_fixed"]}
    ci, cr = subset(ti, trc, ~ti["contested"], ~trc["contested"])
    e = run_e1(ci, cr, {}, tr_names, tr_log, M.make_cells(ci, M.motion_state(ci), "E1"), "%s|E5|contested" % a.tracker, B=B1_)
    sens["contested_excluded"] = {"fixed": compact(e["fixed"]), "pooled": e["pooled_fixed"]}
    e = run_e1(ti, trc, {}, tr_names, tr_log, cells_from(sizes["train"]["h2s"]["cells"]), "%s|E5|scene_boot" % a.tracker, unit="scene", B=B1_)
    sens["scene_bootstrap"] = {"fixed": compact(e["fixed"]), "pooled": e["pooled_fixed"]}
    res["E5_h2s"] = sens
    print("E5", {k: (v["fixed"]["methods"]["Mstar"]["any_sig_under"], v["fixed"]["methods"]["B6"]["any_sig_under"]) for k, v in sens.items()}, flush=True)''',
     '''    res["E5_h2s"] = sens

    def sens_run(name, fn):
        try:
            e = fn()
            sens[name] = {"fixed": compact(e["fixed"]), "pooled": e["pooled_fixed"]}
        except Exception as ex:  # recorded, not fatal (R07b N-m7)
            sens[name] = {"error": "%s: %s" % (type(ex).__name__, ex)}
        save("E5 " + name)
    for name, cfg in SENS.items():
        def fn(cfg=cfg, name=name):
            m = M.motion_state(ti, cfg.get("v_static", M.V_STATIC), cfg.get("w_turn", M.W_TURN), cfg.get("omega", "default"))
            return run_e1(ti, trc, cfg, tr_names, tr_log, M.make_cells(ti, m, "E1"), "%s|E5|%s" % (a.tracker, name), B=B1_)
        sens_run(name, fn)
    ci, cr = subset(ti, trc, ~ti["contested"], ~trc["contested"])
    sens_run("contested_excluded", lambda: run_e1(ci, cr, {}, tr_names, tr_log, M.make_cells(ci, M.motion_state(ci), "E1"),
                                                  "%s|E5|contested" % a.tracker, B=B1_))
    sens_run("scene_bootstrap", lambda: run_e1(ti, trc, {}, tr_names, tr_log, cells_from(sizes["train"]["h2s"]["cells"]),
                                               "%s|E5|scene_boot" % a.tracker, unit="scene", B=B1_))
    print("E5", {k: (v["fixed"]["methods"]["Mstar"]["any_sig_under"], v["fixed"]["methods"]["B6"]["any_sig_under"]) if "fixed" in v else v
                 for k, v in sens.items()}, flush=True)'''),
    ('''    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print("M RUN DONE", a.tracker, res["wall_s"], flush=True)''',
     '''    save("all")
    print("M RUN DONE", a.tracker, res["wall_s"], flush=True)'''),
]
# optional method subset for the operating-characteristic simulation (same functions; the frozen run uses every method)
R += [
    ('''def run_e1(items, recs, cfg, names, slog, cells, label, unit="log", B=M.B_BOOT, reps=M.R_CV, refit_B=0):
    P = M.prepare(items, recs, cfg)
    n = len(items["D"])
    exc = {m: np.zeros(n) for m in M.METHODS}
    marg = {m: np.zeros(n) for m in M.METHODS}''',
     '''def run_e1(items, recs, cfg, names, slog, cells, label, unit="log", B=M.B_BOOT, reps=M.R_CV, refit_B=0, only=None):
    P = M.prepare(items, recs, cfg)
    n = len(items["D"])
    meths = M.METHODS if only is None else ["Mstar"] + [x for x in ("B6",) if x in only]
    exc = {m: np.zeros(n) for m in meths}
    marg = {m: np.zeros(n) for m in meths}'''),
    ('''        e, mg, src = M.cv_once(items, recs, P, cfg, folds)
        assert np.all(src >= 0), "an item was not held out in repetition %d" % rep
        for k in M.METHODS:''', '''        e, mg, src = M.cv_once(items, recs, P, cfg, folds, only)
        assert np.all(src >= 0), "an item was not held out in repetition %d" % rep
        for k in meths:'''),
    ('''                e, mg, _ = M.cv_once(tb, tbr, Pb, cfg, M.folds_by_original_log(tb, seed=M.SEED + 1000 + b))''',
     '''                e, mg, _ = M.cv_once(tb, tbr, Pb, cfg, M.folds_by_original_log(tb, seed=M.SEED + 1000 + b), only)'''),
    ('''def run_e2(tr, trr, va, var, cfg, cells, label, B=M.B_REFIT):''', '''def run_e2(tr, trr, va, var, cfg, cells, label, B=M.B_REFIT, only=None):'''),
    ('''    fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), cfg)
    rng = rng_for(label)''', '''    fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), cfg, only)
    rng = rng_for(label)'''),
    ('''            fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, cfg), np.ones(tb["n_scenes"], bool), cfg)''',
     '''            fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, cfg), np.ones(tb["n_scenes"], bool), cfg, only)'''),
    ('''            "fit_on_all_train": fit_summary(fit, full=True), "n_boot": B}''',
     '''            "fit_on_all_train": fit_summary(fit, full=True) if only is None else None, "n_boot": B}'''),
]
for x, y in R:
    assert t.count(x) == 1, x[:80]
    t = t.replace(x, y)
open(os.path.join(HERE, "m_run_v03.py"), "w", encoding="utf-8", newline="\n").write(t)
print("m_run_v03.py written,", len(R), "changes")
