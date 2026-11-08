#!/usr/bin/env python3
"""Horizon family (Claude line, v02, 31 Oct 2026): v01 with --experiment, so the same propagation can be run for CANMOT's
sample-covariance configuration (paper/local/sample/trainval) as well as the primary paper/local/canmot/sc.
Propagates each exported track's filter state (10) and covariance P (10x10) with the experiment's own constant-velocity
model and process noise, exactly as ExtendedKalmanFilterRotate.predict does (F P F' + R(yaw) Q R(yaw)'), without
measurement updates. Outputs the mean and xy covariance at 1, 2 and 4 s. The propagation is unchanged from v01.
Run inside the CANMOT environment from the CANMOT repository root:
  python -B x1_horizon_prep_v02.py --environment my_machine --experiment <id> --workers <w...> --out <jsonl.gz>
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

import numpy as np

STEPS_OUT = {2: "h1s", 4: "h2s", 8: "h4s"}
APPROVED_EXPERIMENTS = ("paper/local/canmot/sc", "paper/local/sample/trainval")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--environment", required=True)
    ap.add_argument("--experiment", default="paper/local/canmot/sc", choices=APPROVED_EXPERIMENTS)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    repo = os.path.realpath(os.getcwd())
    sys.path.insert(0, os.path.join(repo, "src"))
    from canmot.cli import _compose
    from omegaconf import OmegaConf
    from canmot.motion_module.motion_model import CV
    from canmot.data.script.NUSC_CONSTANT import CLASS_SEG_TO_STR_CLASS
    cfg = OmegaConf.to_container(_compose(a.environment, a.experiment), resolve=True)
    assert cfg.get("experiment_id") == a.experiment
    assert set(cfg["motion_model"]["model"].values()) == {"CV"}, "horizon propagation assumes the CV model"
    model = CV(cfg["basic"]["has_velo"], cfg["basic"]["LiDAR_interval"], cfg["model_cfg"]["matrix_q"], cfg["model_cfg"]["matrix_r"])
    for w in a.workers:
        er = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert er["resolved_config"].get("experiment_id") == a.experiment, "export was made with another experiment: " + w
    q_sha = hashlib.sha256(json.dumps(cfg["model_cfg"]["matrix_q"], sort_keys=True).encode()).hexdigest()
    n = 0
    with gzip.open(a.out, "wt") as fo:
        for w in a.workers:
            with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt") as f:
                for line in f:
                    r = json.loads(line)
                    st = np.asarray(r["state10"], dtype=float).reshape(-1, 1)
                    P = np.asarray(r["P10"], dtype=float)
                    Q = model.getProcessNoiseQ(CLASS_SEG_TO_STR_CLASS[r["tracking_name"]])
                    out = {"scene": r["scene"], "k": r["frame_id"], "tid": r["tracking_id"]}
                    for step in range(1, 9):
                        F = model.getTransitionF(st)
                        rot = model.get_rotation_matrix_for_state(st)
                        st = F @ st
                        P = F @ P @ F.T + rot @ Q @ rot.T
                        if step in STEPS_OUT:
                            out[STEPS_OUT[step]] = [float(st[0, 0]), float(st[1, 0]), float(P[0, 0]), float(P[0, 1]), float(P[1, 1])]
                    fo.write(json.dumps(out) + "\n")
                    n += 1
    print("records", n, "dt", cfg["basic"]["LiDAR_interval"], "experiment", a.experiment, "matrix_q_sha256", q_sha)
    print("HORIZON PREP DONE")


if __name__ == "__main__":
    sys.exit(main())
