# Planner-matched calibration of tracker covariances (M\*): code, protocol and results

[![DOI](https://zenodo.org/badge/1449989385.svg)](https://doi.org/10.5281/zenodo.24048339)

This repository accompanies the paper *Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2*, by Ananda Siva Kumar Kopalli Naga Venkata (Independent Researcher; ORCID [0009-0002-5241-9922](https://orcid.org/0009-0002-5241-9922)). The paper is submitted to IEEE Access.

Archived on Zenodo: release v1.0, https://doi.org/10.5281/zenodo.24048340 (all versions: https://doi.org/10.5281/zenodo.24048339).

It holds the code, the registered protocol, the run log and the results behind every table and figure. Data are not included. The folder layout is the one used during the study, so every file path cited in the paper or its supplement resolves here.

## What is here

| Folder | Contents |
|---|---|
| `40_PROTOCOL/` | The registered plan (`C1_AV2_CONFIRMATORY_PREREG_v07m.md`, SHA-256 0817e600…; OSF registration https://osf.io/v8qfk/, under embargo, with a view-only link for reviewers), the run log of record (`C1_RUN_LOG.txt`), the stage-B log, the freeze-time record, the run commands, the deviation log, the provenance record and the development-stage plans. |
| `50_CODE/` | All code written for the study. **`c1_av2/`** is the registered test; its files are bound by hash in the plan. **`k8/`** is the development planner and its analysis. **`av2/`** is the Argoverse 2 port. **`x3/`** holds the exploratory analyses of Section V-E. **`m/`, `x1/`, `k6/`, `k7/`** are the earlier nuScenes stages. **`tpp/`, `qcnet/`** are the learned-predictor arms. **`owndet/`** is our detector's training split and design. **`c1_criteria/`** is the criteria audit. |
| `60_RESULTS/` | **`c1_av2_v01/`** holds the results of record: `c1_decision_r1.json`, `c1_analysis_r1.json` and `c1_analysis_csv_r1/`. **`x3_explore_v01/`** holds the exploratory results, amendments A1–A5 included. Also: the tracker and detector notes and metrics, the folds, the transfer fits, E⁰, and the nuScenes-stage summaries. |
| `70_TESTS/` | The separate re-derivation of the registered results (`R21_c1_v01/`), the development analyses and the integrity reports of the exploratory analyses. |
| `10_PROOFS/` | Numeric checks of the proofs (Appendix A and Supplement S8). |
| `20_DESIGN/` | The manuscript (Markdown, `MANUSCRIPT_DRAFT_v06i.md`), the supplement, the exploratory plan and its five amendments (with hash sidecars), the reference list, and the abstract fixed before the verdict. |
| `90_DECISIONS/` | The GO decision report, the authors' decision record (`D16_DELEGATED_CHOICES_v61.md`), the criteria register and the errata. |
| `95_SUBMISSION/` | The LaTeX source for IEEE Access (`latex_v06/`), the figures, and the plotted values of each figure (`figs_v02/*points*.csv`). |
| `80_LOGS/` | The scripts that assembled the manuscript, drew the figures and built this repository. |

## Checking the registered files

```bash
python tools/verify_release_v01.py
```

The script checks two things:
- every file in `MANIFEST_SHA256.txt` has the hash shown there;
- the 190 code and protocol files of the registration's frozen list match the hashes registered on 6 Nov 2026, as does the plan itself.

The other 164 frozen files are data. They are listed with their hashes in `EXCLUDED_FROZEN.tsv`, or included where they are small aggregates. `DATA.md` explains.

## Reproducing

1. **Data.** Obtain nuScenes v1.0 (trainval) and the Argoverse 2 Sensor dataset from their providers, under their terms (`DATA.md`).
2. **Third-party code.** Clone the trackers, the learned predictor and the detector code base at the commits in `THIRD_PARTY.md`.
3. **Environments.** Use the package versions in `ENVIRONMENT.md`.
4. **Run.** `40_PROTOCOL/C1_RUN_COMMANDS_v01.txt` gives the commands of record. The registered entry points in `50_CODE/c1_av2/` check a deposit record and append to the run log. **Work in a copy:** a re-run then writes its own log.

## Licence

- **Code:** MIT (`LICENSE`).
- **Documents, protocol, results and figures:** CC BY 4.0 (`LICENSE-docs`).
- **Not included:** the datasets and the third-party code, which keep their own terms.

## Tools and author responsibility

> The author conceived the study, determined its direction and objectives, and made the scientific decisions. Under the author's instructions, Claude (Anthropic) assisted with literature searches, mathematical derivations and checks, programming, analysis, and manuscript preparation. The author takes responsibility for the work.

Code comments and records keep their original wording, which names the tools and the roles in which they worked. The files bound by the registration must stay byte-identical.
