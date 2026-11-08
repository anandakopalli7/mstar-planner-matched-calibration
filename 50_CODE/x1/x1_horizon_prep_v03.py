#!/usr/bin/env python3
"""Horizon family (Claude line, v03, 31 Oct 2026): v02 generalised to every filter and motion model in CANMOT, so that the
same propagation also serves Poly-MOT (paper/baseline/poly_mot). For each exported track, the class's own filter
prediction is repeated without measurement updates, exactly as in canmot.motion_module.kalman_filter:
  LinearKalmanFilter:          F fixed (getTransitionF(None)); x = F x;               P = F P F' + Q
  ExtendKalmanFilter:          F = getTransitionF(x);          x = stateTransition(x); P = F P F' + Q
  ExtendedKalmanFilterRotate:  F = getTransitionF(x); R = rotation(x); x = F x;       P = F P F' + R Q R'
with Q = getProcessNoiseQ(class label) and dt = LiDAR_interval. For the CV/EKF-rotate settings this is identical to v02.
Outputs the mean and xy covariance at 1, 2 and 4 s.
Run inside the CANMOT environment from the CANMOT repository root:
  python -B x1_horizon_prep_v03.py --environment my_machine --experiment <id> --workers <w...> --out <jsonl.gz>
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

import numpy as np

STEPS_OUT = {2: "h1s", 4: "h2s", 8: "h4s"}
APPROVED_EXPERIMENTS = ("paper/local/canmot/sc", "paper/local/sample/trainval", "paper/baseline/poly_mot")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--environment", required=True)
    ap.add_argument("--experiment", required=True, choices=APPROVED_EXPERIMENTS)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    repo = os.path.realpath(os.getcwd())
    sys.path.insert(0, os.path.join(repo, "src"))
    from canmot.cli import _compose
    from omegaconf import OmegaConf
    from canmot.motion_module import motion_model as MM
    from canmot.data.script.NUSC_CONSTANT import CLASS_SEG_TO_STR_CLASS
    cfg = OmegaConf.to_container(_compose(a.environment, a.experiment), resolve=True)
    assert cfg.get("experiment_id") == a.experiment
    for w in a.workers:
        er = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert er["resolved_config"].get("experiment_id") == a.experiment, "export was made with another experiment: " + w
    dt, hv = cfg["basic"]["LiDAR_interval"], cfg["basic"]["has_velo"]
    mq, mr = cfg["model_cfg"].get("matrix_q"), cfg["model_cfg"].get("matrix_r")
    models, kinds = {}, {}
    for lab, name in cfg["motion_model"]["model"].items():
        lab = int(lab)
        models[lab] = MM.get_model_class_by_name(name)(hv, dt, mq, mr)
        kinds[lab] = cfg["motion_model"]["filter"][lab] if lab in cfg["motion_model"]["filter"] else cfg["motion_model"]["filter"][str(lab)]
        assert kinds[lab] in ("LinearKalmanFilter", "ExtendKalmanFilter", "ExtendedKalmanFilterRotate"), kinds[lab]
    Qs = {lab: np.asarray(models[lab].getProcessNoiseQ(lab), dtype=float) for lab in models}
    Fl = {lab: np.asarray(models[lab].getTransitionF(None), dtype=float) for lab in models if kinds[lab] == "LinearKalmanFilter"}
    q_sha = hashlib.sha256(json.dumps({str(k): v.tolist() for k, v in sorted(Qs.items())}).encode()).hexdigest()
    n = 0
    with gzip.open(a.out, "wt") as fo:
        for w in a.workers:
            with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt") as f:
                for line in f:
                    r = json.loads(line)
                    lab = int(CLASS_SEG_TO_STR_CLASS[r["tracking_name"]])
                    model, kind, Q = models[lab], kinds[lab], Qs[lab]
                    st = np.asarray(r["state10"], dtype=float).reshape(-1, 1)
                    P = np.asarray(r["P10"], dtype=float)
                    assert P.shape == (st.shape[0], st.shape[0]) == Q.shape, "state, P and Q dimensions differ"
                    out = {"scene": r["scene"], "k": r["frame_id"], "tid": r["tracking_id"]}
                    for step in range(1, 9):
                        if kind == "LinearKalmanFilter":
                            F = Fl[lab]
                            st = F @ st
                            P = F @ P @ F.T + Q
                        elif kind == "ExtendKalmanFilter":
                            F = np.asarray(model.getTransitionF(st), dtype=float)
                            st = np.asarray(model.stateTransition(st), dtype=float).reshape(-1, 1)
                            P = F @ P @ F.T + Q
                        else:
                            F = model.getTransitionF(st)
                            rot = model.get_rotation_matrix_for_state(st)
                            st = F @ st
                            P = F @ P @ F.T + rot @ Q @ rot.T
                        if step in STEPS_OUT:
                            out[STEPS_OUT[step]] = [float(st[0, 0]), float(st[1, 0]), float(P[0, 0]), float(P[0, 1]), float(P[1, 1])]
                    fo.write(json.dumps(out) + "\n")
                    n += 1
    print("records", n, "dt", dt, "experiment", a.experiment, "filters", sorted(set(kinds.values())), "Q_sha256", q_sha)
    print("HORIZON PREP DONE")


if __name__ == "__main__":
    sys.exit(main())
