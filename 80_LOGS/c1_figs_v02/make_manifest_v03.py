"""Write figs_v02_manifest_v03.json (keeps the v01 and v02 manifests).

Covers every file in 95_SUBMISSION/figs_v02 (Figs. 1-4, Fig. 4 v01, v02 and
v03, points tables, all caption files, earlier manifests), the scripts and run
logs, and every input read, with sha256.
Usage: python -B make_manifest_v03.py <workspace_root> "<time stamp from date>"
"""
import hashlib
import json
import os
import platform
import sys

import matplotlib
import numpy

W, STAMP = sys.argv[1], sys.argv[2]
OUTDIR = os.path.join(W, "95_SUBMISSION", "figs_v02")
MAN = os.path.join(OUTDIR, "figs_v02_manifest_v03.json")
if os.path.exists(MAN):
    raise SystemExit("refusing to overwrite " + MAN)


def sha(rel):
    h = hashlib.sha256()
    with open(os.path.join(W, rel), "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def table(rels):
    return {r: sha(r) for r in rels}


X3 = "60_RESULTS/x3_explore_v01/"
C1 = "60_RESULTS/c1_av2_v01/"
CSV = C1 + "c1_analysis_csv_r1/"
O = "95_SUBMISSION/figs_v02/"
LG = "80_LOGS/c1_figs_v02/"

inputs = {
    "fig02": [CSV + "k8_within_lt3d_t1_decide_cells.csv",
              CSV + "k8_within_lt3d_t3_decide_cells.csv",
              C1 + "c1_decision_r1.json",
              "95_SUBMISSION/figs_v01/figs_v01_manifest.json"],
    "fig03": [CSV + "k8_within_lt3d_t1_decide_arms.csv",
              CSV + "k8_within_lt3d_t3_decide_arms.csv",
              CSV + "k8_within_lt3d_t1_decide_paired.csv",
              CSV + "k8_within_lt3d_t3_decide_paired.csv",
              C1 + "c1_decision_r1.json",
              "95_SUBMISSION/figs_v01/figs_v01_manifest.json"],
    "fig04_v01": [X3 + "a3_review/x3_a3_i_infeasible_cost_v01.json",
                  X3 + "a4_review/x3_a4_1_neutral_v01.json",
                  X3 + "f_tradeoff/x3_f_tradeoff_v01.json"],
    "fig04_v02": [X3 + "a3_review/x3_a3_i_infeasible_cost_v01.json",
                  X3 + "a4_review/x3_a4_1_neutral_v01.json",
                  X3 + "f_tradeoff/x3_f_tradeoff_v01.json",
                  X3 + "a5_review/x3_a5_reduced_screen_v01.json",
                  X3 + "a5_review/x3_a5_points_v01.csv"],
    "fig04_v03": [X3 + "a3_review/x3_a3_i_infeasible_cost_v01.json",
                  X3 + "a4_review/x3_a4_1_neutral_v01.json",
                  X3 + "f_tradeoff/x3_f_tradeoff_v01.json",
                  X3 + "a5_review/x3_a5_reduced_screen_v01.json",
                  X3 + "a5_review/x3_a5_points_v01.csv"],
}
checking = ["20_DESIGN/ms_v06_parts/04_method_v04.md",
            "20_DESIGN/ms_v06_parts/05D_registered_v06.md",
            "20_DESIGN/ms_v06_parts/05E_x3_v07.md",
            "20_DESIGN/ms_v06_parts/C_statsbox_terms_v06.md",
            "40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md",
            "70_TESTS/V06C_REFEREE_REVIEW_v01.md",
            "70_TESTS/V06D_REFEREE_REVIEW_v01.md",
            "80_LOGS/c1_manuscript_v01/make_c1_figs_v01.py",
            "95_SUBMISSION/figs_v01/fig09_mstar_cells.png",
            "95_SUBMISSION/figs_v01/fig10_infeasible_arms.png",
            X3 + "a5_review/x3_a5_reduced_screen_v01.md"]
outputs = [O + n for n in (
    "fig01_pipeline.pdf", "fig01_pipeline.png",
    "fig02_mstar_cells.pdf", "fig02_mstar_cells.png", "fig02_points_v01.csv",
    "fig03_infeasible_arms.pdf", "fig03_infeasible_arms.png",
    "fig03_points_v01.csv",
    "fig04_tradeoff.pdf", "fig04_tradeoff.png", "fig04_points_v01.csv",
    "fig04_tradeoff_v02.pdf", "fig04_tradeoff_v02.png",
    "fig04_points_v02.csv",
    "fig04_tradeoff_v03.pdf", "fig04_tradeoff_v03.png",
    "fig04_points_v03.csv",
    "FIG_CAPTIONS_v01.md", "FIG_CAPTIONS_v02.md", "FIG_CAPTIONS_v03.md",
    "figs_v02_manifest.json", "figs_v02_manifest_v02.json")]
scripts = [LG + n for n in (
    "make_fig01_v01.py", "make_fig02_v01.py", "make_fig03_v01.py",
    "make_fig04_v01.py", "make_fig04_v02.py", "make_fig04_v03.py",
    "make_manifest_v01.py", "make_manifest_v02.py", "make_manifest_v03.py")]
logs = [LG + n for n in (
    "fig01_run_v01.log", "fig02_run_v01.log", "fig03_run_v01.log",
    "fig04_run_v01.log", "fig04_run_v02.log", "fig04_run_v03.log")]

man = {
    "written": STAMP,
    "what": "figs_v02 manifest v03: as v02, plus Fig. 4 v03 (referee V06D "
            "minor 4 and 18) and FIG_CAPTIONS_v03.md (Figs. 1-3 captions "
            "copied unchanged from v02, Fig. 4 revised). The v01 and v02 "
            "manifests are kept unchanged; Figs. 1-3 files are unchanged.",
    "interpreter": {"executable": sys.executable,
                    "python": platform.python_version(),
                    "numpy": numpy.__version__,
                    "matplotlib": matplotlib.__version__},
    "outputs_sha256": table(outputs),
    "scripts_sha256": table(scripts),
    "run_logs_sha256": table(logs),
    "inputs_sha256_by_figure": {k: table(v) for k, v in inputs.items()},
    "inputs_read_for_checking_sha256": table(checking),
    "style": "Times New Roman 8 pt (TrueType embedded), STIX math; Okabe-Ito "
             "colours with shape as second encoding (T1 #0072B2 circle, T3 "
             "#E69F00 square in Figs. 2-3); checked on greyscale renders.",
    "fig02": {
        "size_in": [7.16, 4.85],
        "plotted": "M* (arm Mstar), evaluable cells only: P_rel 27, P_near "
                   "16, P_ip 8 per tracker (102 points); E (marker) and ub_sim "
                   "(bar end); lb_sim not drawn (kept in fig02_points_v01.csv "
                   "as lb_sim_not_drawn)",
        "interval": "upper end of the one-sided simultaneous 95 % sup-t band, "
                    "log bootstrap over the population's evaluable cells "
                    "(decision: Mstar_simultaneous_upper_bounds)",
        "checks": ["ub_sim equals the decision's per-cell bounds; evaluable "
                   "counts and U_max/cell equal the decision (6 of 6)",
                   "E and ub_sim identical (exact float) to figs_v01 fig09 "
                   "plotted values (6 of 6 populations)",
                   "T1 and T3 have the same cells in the same order",
                   "U_max T1 0.127/0.118/0.129, T3 0.122/0.110/0.157"],
    },
    "fig03": {
        "size_in": [3.50, 4.98],
        "plotted": "8 arms (Table IV order) x 2 trackers; (a) infeasible_rate "
                   "with infeasible_ci95_lo/hi (two-sided 95 % log bootstrap, "
                   "arms CSV); (b) M* - arm from the paired CSV (endpoint "
                   "infeasible_rate, 375 logs) with ci95_lo/hi (two-sided 95 "
                   "%, percentile log bootstrap per register C3c); filled = in "
                   "V_t (decision H1), open = removed",
        "checks": ["all rates, differences, intervals and V_t membership "
                   "identical (exact float) to figs_v01 fig10",
                   "paired values of V_t members equal the decision's H1 "
                   "entries; V_t: T1 {B3}, T3 {B0, B3}"],
    },
    "fig04_v02": {
        "size_in": [7.16, 6.82],
        "added_to_v01": "M*(0.03) in all three rows (A5 composite_six, equal "
                        "to A4); A5 reduced-screen composites of B0/B4/B6/B9 "
                        "(rings, family colour); A4 neutral-screen composites "
                        "(crosses, family colour), from x3_a5_reduced_screen_"
                        "v01.json families.<fam>.<A4|A5>.composite_six",
        "checks": ["M*(0.03) T1 infeasible 0.2603, V2 0.3412, V2_exec 0.4480, "
                   "V2_viol 0.0128; T3 0.3505, 0.3480, 0.5044, 0.0149: PASS",
                   "M*(0.03) and the four A4 composites: infeasible and "
                   "V2_exec equal x3_a4_1_neutral_v01.json composite_endpoints",
                   "single-choice composites equal their grid point in "
                   "x3_a5_points_v01.csv (8 cases)",
                   "arms of record and sweep unchanged from v01 (same checks)"],
        "data_notes": ["A5 B9 composite = B9@0.05 in every fold on both "
                       "trackers = the B9 arm of record (ring on the filled "
                       "pentagon)",
                       "A5 B0 composite on T1 = B0d0.02 in every fold (on the "
                       "sweep)"],
        "points": 240,
    },
    "fig04_v03": {
        "size_in": [7.16, 6.82],
        "changes_from_v02": [
            "registered-screen B6 composite (A_B6_composite) drawn on T3 only, "
            "labelled 'B6 matched on the registered screen (T3 only)'; on T1 "
            "its folds are B6@0.015/B6@0.005/B6@0.015/B6@0.015/B6@0.015 "
            "(fold 1 substituted, not a matched point)",
            "B9 neutral-screen (cross) and reduced-screen (ring) composites "
            "marked censored by the grid with a downward arrow; folds at the "
            "grid end B9@0.05: T1 neutral 4/5, reduced 5/5; T3 neutral 2/5, "
            "reduced 5/5; no other family has a fold at its grid's least "
            "conservative end",
            "neutral-screen crosses drawn on top; stated horizontal offsets "
            "(data units): B9 cross T1 -0.020 (a), -0.013 (b), -0.0012 (c); "
            "T3 -0.020 (a), +0.013 (b); B8 T1 (c) +0.0020; recorded per point "
            "in fig04_points_v03.csv (x_drawn_offset), plotted values "
            "unchanged",
            "legend: 'censored by the grid (B9)' entry; shorter screen labels"],
        "checks": "as v02 (27 PASS, 0 FAIL; fig04_run_v03.log)",
        "points": 237,
    },
}
with open(MAN, "w", encoding="utf-8") as f:
    json.dump(man, f, indent=2, ensure_ascii=False)
    f.write("\n")
for p, h in man["outputs_sha256"].items():
    print(h[:12], p)
for p, h in man["scripts_sha256"].items():
    print(h[:12], p)
print("wrote", MAN)
