"""Port the v03 tests to the v04 modules (Claude line, 31 Oct 2026; review R07c). Kept as the record of the changes."""
import os

T = os.path.dirname(os.path.abspath(__file__))


def port(src, dst, reps):
    t = open(os.path.join(T, src), encoding="utf-8").read()
    for a, b in reps:
        assert t.count(a) >= 1, (src, a[:60])
        t = t.replace(a, b)
    open(os.path.join(T, dst), "w", encoding="utf-8", newline="\n").write(t)


port("test_m_units_v03.py", "test_m_units_v04.py", [
    ('"""Unit and Monte Carlo tests of m_lib_v03 on simulated item tables (Claude line, v03, 31 Oct 2026). Simulated data only.',
     '"""Unit and Monte Carlo tests of m_lib_v04 on simulated item tables (Claude line, v04, 31 Oct 2026). Simulated data only.\n'
     'v04: the minimum-chord sensitivity (T11d) and HM6b as the pooled significance check (T23).'),
    ("import m_lib_v03 as M", "import m_lib_v04 as M"),
    ('"omc": om.copy(), "V": V,', '"omc": om.copy(), "chord": np.full(n, 5.0), "V": V,'),
    ('''    ok["T11c_cog_rate"] =''', '''    itc = {"g": np.zeros(3, int), "spd": np.full(3, 2.0), "omc": np.array([0.3, 0.3, np.nan]), "chord": np.array([0.5, 2.0, np.nan]),
           "om": np.zeros(3), "omv": np.zeros(3)}
    ok["T11d_min_chord_rule"] = M.motion_state(itc, omega="omc_chord1").tolist() == [1, 2, 3] and M.motion_state(itc).tolist() == [2, 2, 3]
    stc = {"methods": {"Mstar": {"any_sig_under": False, "sig_under_cells": [], "cells": {"all val items": {"sig_under": True, "E_scene": 0.07,
           "lb_sim": 0.055, "ub_sim": 0.08, "boot_bias": 0.001}}}}}
    h6 = M.hypotheses_e2(stc, stc)
    ok["T23_HM6b_significance"] = (h6["HM6b"] is False) and (h6["HM6"] is False) and abs(h6["pooled_ub_bias_corrected"] - 0.081) < 1e-12 \\
        and h6["pooled_equivalence_at_eps"] is False
    ok["T11c_cog_rate"] ='''),
])
port("test_m_refit_v03.py", "test_m_refit_v04.py", [
    ("(Claude line, v03, 31 Oct 2026; ported to m_lib_v03/m_run_v03)", "(Claude line, v04, 31 Oct 2026; ported to m_lib_v04/m_run_v04)"),
    ("through m_run_v03.run_e2", "through m_run_v04.run_e2"), ("import m_lib_v03 as M", "import m_lib_v04 as M"),
    ("import m_run_v03 as R", "import m_run_v04 as R"), ("from test_m_units_v03 import", "from test_m_units_v04 import"),
    ("Usage: python test_m_refit_v03.py", "Usage: python test_m_refit_v04.py")])
port("test_m_b8_v03.py", "test_m_b8_v04.py", [
    ("(Claude line, v03, 31 Oct 2026; ported to m_lib_v03/m_run_v03)", "(Claude line, v04, 31 Oct 2026; ported to m_lib_v04)"),
    ("import m_lib_v03 as M", "import m_lib_v04 as M"), ("from test_m_units_v03 import", "from test_m_units_v04 import"),
    ("Usage: python test_m_b8_v03.py", "Usage: python test_m_b8_v04.py")])
port("test_m_freeze_check_v02.py", "test_m_freeze_check_v03.py", [
    ("(Claude line, v02, 31 Oct 2026; R07 M11 item 8; ported to m_run_v03)", "(Claude line, v03, 31 Oct 2026; R07 M11 item 8; ported to m_run_v04)"),
    ("import m_run_v03 as R", "import m_run_v04 as R"), ("Usage: python test_m_freeze_check_v02.py", "Usage: python test_m_freeze_check_v03.py")])
port("make_sim_dataset_v02.py", "make_sim_dataset_v03.py", [
    ('"""Fully simulated train/val dataset in the export, ground-truth and horizon formats (Claude line, v02, 31 Oct 2026).',
     '"""Fully simulated train/val dataset in the export, ground-truth and horizon formats (Claude line, v03, 31 Oct 2026; v02 with\n'
     'corrected documentation, R07c X-m6).'),
    ("car E merges into the ego lane with a 0.30 rad/s turn (its CV prediction is laterally wrong toward the ego), car F drifts",
     "car E starts beside the ego lane and turns at 0.30 rad/s, so over the 10 s scene it circles (3 rad, radius 20 m); its CV\n"
     "prediction is wrong in both object axes, and in the run B6 fails in a longitudinal car-turning cell. Car F drifts"),
    ("For an end-to-end test of m_sizes_v01 and m_run_v01", "For an end-to-end test of m_sizes_v04 and m_run_v04"),
    ("Usage: python make_sim_dataset_v01.py", "Usage: python make_sim_dataset_v03.py")])
port("run_m_sim_e2e_v03.sh", "run_m_sim_e2e_v04.sh", [
    ("# End-to-end test of the v03 pipeline on a fully simulated dataset (Claude line, v03, 31 Oct 2026):",
     "# End-to-end test of the v04 pipeline on a fully simulated dataset (Claude line, v04, 31 Oct 2026):"),
    ("# make_sim_dataset_v02 -> m_sizes_v03 (outcomes off) -> m_run_v03 --test-mode (every bootstrap 120) -> m_decide_v03",
     "# make_sim_dataset_v03 -> m_sizes_v04 (outcomes off) -> m_run_v04 --test-mode (every bootstrap 120) -> m_decide_v04"),
    ("pass criteria (check_sim_e2e_v03.py).", "pass criteria (check_sim_e2e_v04.py)."),
    ('S="$W/70_TESTS/m_scratch/sim_e2e_v03"', 'S="$W/70_TESTS/m_scratch/sim_e2e_v04"'),
    ("tests/make_sim_dataset_v02.py", "tests/make_sim_dataset_v03.py"), ("m_sizes_v03.py", "m_sizes_v04.py"), ("m_run_v03.py", "m_run_v04.py"),
    ("m_decide_v03.py", "m_decide_v04.py"), ("tests/check_sim_e2e_v03.py", "tests/check_sim_e2e_v04.py"), ("SIM E2E V03 DONE", "SIM E2E V04 DONE")])
port("check_sim_e2e_v03.py", "check_sim_e2e_v04.py", [
    ('"""Pass criteria for the simulated end-to-end run (Claude line, v03, 31 Oct 2026; R07 M11 item 7, R07b N-m3).',
     '"""Pass criteria for the simulated end-to-end run (Claude line, v04, 31 Oct 2026; R07 M11 item 7, R07b N-m3, R07c X-m6).'),
    ("5. Known answer (dataset v02): HM3 is testable and holds at 2 s (car E turns toward the ego; B6 pools it with car F).\n"
     "The relaxation of criterion 3 (HM6a on 2 of 3 horizons) dates from v02 and is disclosed in M_SYNTHETIC_TESTS.",
     "5. Known answer (dataset v03): HM3 is testable and holds at 2 s in any car-turning cell (car E circles at 0.30 rad/s; B6 pools\n"
     "   it with straight cars). A first try at 0.15 rad/s was not detectable (B6 lateral turning E 0.088, refit LB 0.045); both\n"
     "   tries and the change are disclosed in M_SYNTHETIC_TESTS v04.\n"
     "The relaxation of criterion 3 (HM6a on 2 of 3 horizons) dates from v02 and is disclosed in M_SYNTHETIC_TESTS.\n"
     "Rates of HM6 and HM3 are measured by the OC study, not here."),
    ("rates are measured by test_m_refit_v02 and test_m_oc_v01", "rates are measured by test_m_refit_v04 and the OC study"),
    ('''    ok["HM3_known_answer"] = bool(r["E1_h2s"]["hypotheses"]["HM3_testable"] and r["E1_h2s"]["hypotheses"]["HM3_holds"])''',
     '''    ok["HM3_known_answer"] = bool(r["E1_h2s"]["hypotheses"]["HM3_testable"] and r["E1_h2s"]["hypotheses"]["HM3_holds"])
    out_cells = r["E1_h2s"]["hypotheses"]["HM3"]'''),
    ('''    out = {"ok": ok, "all_ok": all(ok.values()), "decision": d["METHOD_DECISION"],''',
     '''    out = {"ok": ok, "all_ok": all(ok.values()), "decision": d["METHOD_DECISION"], "HM3_cells": out_cells,'''),
    ("Usage: python check_sim_e2e_v02.py", "Usage: python check_sim_e2e_v04.py"),
    ('len(r["E5_h2s"]) == 11', 'len(r["E5_h2s"]) == 12'),
    ("1. Every evaluation section is present (E1, E2 at 1/2/4 s; refit E1 and hypotheses at 2 s; all E5 sensitivities).",
     "1. Every evaluation section is present (E1, E2 at 1/2/4 s; refit E1 and hypotheses at 2 s; all 12 E5 sensitivities).")])
print("ported")
