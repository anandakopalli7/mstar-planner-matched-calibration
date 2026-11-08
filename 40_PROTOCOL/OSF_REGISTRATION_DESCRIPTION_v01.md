Frozen pre-registration of the C1 Argoverse 2 confirmatory analysis; ground-truth stage B is built only after this registration. Frozen plan: C1_AV2_CONFIRMATORY_PREREG_v07m.md, SHA-256 0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c, frozen 2026-11-06 20:08:13 UTC.

PURPOSE
Motion planners for automated driving use the uncertainty that a multi-object tracker reports (its covariance) to enforce chance constraints, for example "keep clear of this object with probability at least 1 − δ". Standard tracker consistency checks such as NEES can pass while the particular constraints a planner relies on are violated far more often than δ. This project studies decision-projected calibration: the tracker's uncertainty is calibrated along exactly the constraint directions that the planner uses, by split conformal risk control (DP-SCRC). The aim is that each relied constraint is exceeded at no more than the nominal rate δ = 0.05, without making the planner unusable. Development work on nuScenes (two trackers) supported the method. This registration fixes, before any outcome exists, a single confirmatory test on independent data.

DATA
375 Argoverse 2 Sensor logs that the detector never saw: 225 held-out training logs and the 150 validation logs.
- Detections come from our own CenterPoint detector, trained only on the other 475 training logs.
- Two trackers are primary, CANMOT and Poly-MOT, with their nuScenes settings and no re-tuning. AB3DMOT is a descriptive third tracker.
- Tracker outputs, counts, folds and other outcome-free quantities were fixed before the freeze.
- The prepared ground truth is held in a verified quarantine. Annotation positions after the decision time are read only after this registration.

DESIGN AND ANALYSIS
- Five-fold cross-fitting over logs (75 logs per fold, fixed seed). The log is the unit of analysis and of the bootstrap (B = 40,000).
- The method M* (per-constraint DP-SCRC) is compared with seven pre-specified comparator arms in a tracker–planner loop, in decision mode:
  - raw covariance;
  - NEES-scaled;
  - a certified single multiplier;
  - pooled conformal;
  - conformal without motion strata;
  - a norm-ball;
  - a re-tuned nominal risk.
- Every calibration threshold is decided in exact rational arithmetic. Every rule, criterion, seed, code file and post-registration command is frozen by hash.

HYPOTHESES
Primary (H1; one-sided 0.025 in total), required on both trackers:
- no evaluable cell (object group × axis × motion), family cell or pooled cell of M* is shown above δ on three pre-specified item populations;
- the power floors hold;
- M* is less often infeasible than every comparator that is not itself shown above δ.

Secondary (pre-registered, multiplicity-controlled):
- the operability price against the pooled conformal baseline is at most 0.03 (H2);
- a trajectory-level certificate (H3);
- transfer of thresholds fitted on nuScenes (H4);
- validity of the method within Argoverse 2 and under transfer, and failure of a practitioner baseline (H6a, H6b, H7);
- replication of the development diagnosis in in-path lateral cells (H8);
- a motion-strata ablation (H10).

Descriptive only, never claimed:
- a learned trajectory predictor (Trajectron++);
- public-detector and VoxelNeXt routes;
- AB3DMOT.

EXPECTED OUTCOMES AND HOW THEY WILL BE READ
- **GO requires H1 on both trackers.** A GO would show that decision-projected calibration keeps the planner's relied constraints within δ on unseen data while staying operable, that is, less often infeasible than any comparator that is itself valid.
- **A NO-GO is reported in full, with its reason** (validity, power floors or superiority). It leads to diagnosis and new data, never to a re-run on these logs.
- **What the development data predict.** A pass on both trackers. Projected chances of meeting H1 under the frozen rules are about 0.88 to 0.97 (reported only, never used as a criterion). On one tracker the result is expected to turn on one comparator, conformal without motion strata.
- **Power.** The study is powered to detect per-cell excesses of about 0.15, not smaller ones.
- **Not claimed:** a closed-loop safety guarantee, validity in cells too small to evaluate, or any confirmatory statement about a learned predictor.

SAFEGUARDS
- The plan text was uploaded to this project before any confirmation-set build.
- The ground truth is quarantined. Scans for copies outside the workspace found none, before or after the quarantine.
- Every outcome step refuses to run until this registration is recorded.
- Every run is written to an append-only, hash-chained log. That log and the stage-B log will be uploaded here with the results.
