"""Write figs_v02_manifest.json: sha256 of every output and every input read.

Usage: python -B make_manifest_v01.py <workspace_root> "<time stamp from date>"
Refuses to overwrite an existing manifest.
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
LOGDIR = os.path.join(W, "80_LOGS", "c1_figs_v02")
MAN = os.path.join(OUTDIR, "figs_v02_manifest.json")
if os.path.exists(MAN):
    raise SystemExit("refusing to overwrite " + MAN)


def sha(rel):
    h = hashlib.sha256()
    with open(os.path.join(W, rel), "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def table(rels):
    return {r.replace("\\", "/"): sha(r) for r in rels}


X3 = "60_RESULTS/x3_explore_v01/"
inputs_scripts = [X3 + "a3_review/x3_a3_i_infeasible_cost_v01.json",
                  X3 + "a4_review/x3_a4_1_neutral_v01.json",
                  X3 + "f_tradeoff/x3_f_tradeoff_v01.json"]
inputs_checking = ["20_DESIGN/ms_v06_parts/04_method_v04.md",
                   "20_DESIGN/ms_v06_parts/05E_x3_v04.md",
                   X3 + "a3_review/x3_a3_i_infeasible_cost_v01.md",
                   X3 + "a4_review/x3_a4_1_neutral_v01.md",
                   X3 + "f_tradeoff/x3_f_tradeoff_v01.md",
                   X3 + "f_tradeoff/x3_f_infeasible_vs_V2_v01.png"]
outputs = ["95_SUBMISSION/figs_v02/fig01_pipeline.pdf",
           "95_SUBMISSION/figs_v02/fig01_pipeline.png",
           "95_SUBMISSION/figs_v02/fig04_tradeoff.pdf",
           "95_SUBMISSION/figs_v02/fig04_tradeoff.png",
           "95_SUBMISSION/figs_v02/fig04_points_v01.csv",
           "95_SUBMISSION/figs_v02/FIG_CAPTIONS_v01.md"]
scripts = ["80_LOGS/c1_figs_v02/make_fig01_v01.py",
           "80_LOGS/c1_figs_v02/make_fig04_v01.py",
           "80_LOGS/c1_figs_v02/make_manifest_v01.py"]
logs = ["80_LOGS/c1_figs_v02/fig01_run_v01.log",
        "80_LOGS/c1_figs_v02/fig04_run_v01.log"]

man = {
    "written": STAMP,
    "what": "Figs. 1 and 4 for the v06c manuscript (IEEE Access), vector PDF "
            "+ 300 dpi PNG; Fig. 4 reads result files only (no new "
            "quantities beyond selecting values).",
    "interpreter": {"executable": sys.executable,
                    "python": platform.python_version(),
                    "numpy": numpy.__version__,
                    "matplotlib": matplotlib.__version__},
    "commands": [
        "python -B 80_LOGS/c1_figs_v02/make_fig01_v01.py 95_SUBMISSION/figs_v02",
        "python -B 80_LOGS/c1_figs_v02/make_fig04_v01.py "
        + " ".join(inputs_scripts) + " 95_SUBMISSION/figs_v02",
        "python -B 80_LOGS/c1_figs_v02/make_manifest_v01.py <W> \"<date>\"",
    ],
    "scripts_sha256": table(scripts),
    "run_logs_sha256": table(logs),
    "inputs_read_by_scripts_sha256": table(inputs_scripts),
    "inputs_read_for_checking_sha256": table(inputs_checking),
    "outputs_sha256": table(outputs),
    "style": {
        "font": "Times New Roman (TrueType embedded, pdf.fonttype 42); math in "
                "STIX; 8 pt text, 9 pt panel and region titles",
        "palette": "Okabe-Ito (M* vermillion #D55E00, B0 #0072B2, B1 #E69F00, "
                   "B3 #56B4E9, B4 #009E73, B6 #CC79A7, B9 #F0E442, RETUNED "
                   "black); identity also carried by marker shape and fill, "
                   "checked on a greyscale conversion of the PNG. The "
                   "palette validator script was not run (no Node.js runtime "
                   "on this machine).",
        "fig01_size_in": [3.50, 3.45],
        "fig04_size_in": [7.16, 6.62],
    },
    "fig01": {
        "source_checked": "04_method_v04.md Sections IV-A to IV-F "
                          "(Algorithm 1, Proposition 5)",
        "differences_from_brief_followed_part": [
            "Brief: 'tracker 2 s predicted covariance V-hat'. Part: predicted "
            "mean and 2x2 covariance Sigma-hat_h at every check time h in "
            "{0.5, 1, 1.5, 2} s. Drawn as 'm-hat_h, Sigma-hat_h at each check "
            "time h' (no numbers), symbol Sigma-hat as in the part.",
            "Brief: 'enforced and relied constraint items'. Part IV-A: fitting "
            "uses every separating axis of every enforced pair at the "
            "reference pose; the relied axis is used only for scoring. Drawn "
            "as 'constraints the planner enforces, at the logged reference "
            "ego pose' and 'each separating object axis'.",
            "Strata as in the brief (group x range x axis x course-change "
            "state); the part adds that thresholds are fitted separately per "
            "check time and for in-path and other tracks; drawn.",
            "'5-fold cross-fitting' drawn as 'cross-fitted over log folds' "
            "to keep the figure free of numbers; the caption keeps it "
            "general too.",
            "Deployed covariance identical to the brief and Proposition 5: "
            "Sigma-tilde = A (Sigma-hat_h + sigma_a^2 I) A, A diagonal along "
            "the box axes; alpha = max(c-hat, eps)/z added from Algorithm 1 "
            "line 12.",
        ],
    },
    "fig04": {
        "rows": {"a": "V2", "b": "V2_exec", "c": "V2_viol"},
        "y": "infeasible_rate (log mean)",
        "axis_ranges": {"x_a": [-0.02, 1.02], "x_b": [0.30, 1.01],
                        "x_c": [-0.0012, 0.0612], "y_all": [-0.03, 1.03]},
        "plotted": {
            "arms_of_record_filled": ["Mstar", "B0", "B1", "B3", "B4", "B6",
                                      "B9", "RETUNED"],
            "b0_sweep_grey_line": "all 21 B0a*/B0d* keys of the a3 file, "
                                  "joined in order of descending V2",
            "exploratory_hollow": ["A_B6_composite", "X3E1_B8"],
            "neutral_screen_hollow_star": "Mstar@0.03 (families.Mstar."
                                          "composite_endpoints of the a4 "
                                          "file), row (b) only",
            "points_total": 188,
        },
        "omitted": {
            "per_brief": ["Z0", "X3G_* (learning curve)",
                          "X3D_Mstar_d1", "X3D_Mstar_d2"],
            "not_in_design_list": ["A_B4_composite", "A_B9_composite",
                                   "X3E1_B5", "X3E1_B7", "X3E2_B0_qrefit",
                                   "X3E2_B0_qrefit_ext",
                                   "RETUNED_HK1 (identical to B0a8, drawn "
                                   "as a sweep point)"],
            "neutral_matched_composites": "B4, B6, B9 and B0 families on the "
                                          "neutral screen carry only "
                                          "infeasible_rate and V2_exec (no V2, "
                                          "no V2_viol); not drawn, because the "
                                          "design list names only M*(0.03) "
                                          "from the neutral screen.",
            "neutral_Mstar_rows_a_c": "V2 and V2_viol are absent from the a4 "
                                      "file for Mstar@0.03, so it appears in "
                                      "row (b) only.",
        },
        "checks": [
            "M* T1 infeasible 0.1864, V2 0.4909, V2_exec 0.5509, V2_viol "
            "0.0161: PASS",
            "M* T3 infeasible 0.2466, V2 0.4963, V2_exec 0.5805, V2_viol "
            "0.0176: PASS",
            "Mstar@0.03 chosen in every fold on both trackers; composite "
            "endpoints equal the in-sample curve point: PASS",
            "a3 values vs the earlier trade-off record (x3_f_tradeoff_v01."
            "json rows): 180 values, max |diff| 3.33e-16: PASS",
            "Legends inside the page and clear of the column titles: PASS",
        ],
        "data_notes": [
            "B0a1, B0d0.05 and B0 have identical values (the raw margin).",
            "B0a2 and B0d0.01 agree to 1e-4 (T1 V2_exec 0.4609 vs 0.4608; "
            "T3 identical), consistent with alpha scaling the covariance "
            "(sqrt(2) x 1.645 = 2.326 = z_0.99).",
            "B0d0.5 has the same values as Z0 (z = 0, zero margin); it is "
            "drawn as the end of the sweep and Z0 is not marked separately.",
            "RETUNED_HK1 has the same values as B0a8 (chosen in every fold).",
            "T1 carries X3G_n25_r1; T3 does not (51 vs 50 arm entries). Not "
            "plotted.",
        ],
        "points_table": "95_SUBMISSION/figs_v02/fig04_points_v01.csv "
                        "(one row per plotted point; source a3 = x3_a3_i_"
                        "infeasible_cost_v01.json, a4 = x3_a4_1_neutral_v01."
                        "json)",
    },
}
with open(MAN, "w", encoding="utf-8") as f:
    json.dump(man, f, indent=2, ensure_ascii=False)
    f.write("\n")
for k in ("outputs_sha256", "scripts_sha256"):
    for p, h in man[k].items():
        print(h[:12], p)
print("wrote", MAN)
