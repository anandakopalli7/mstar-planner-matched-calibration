#!/usr/bin/env python3
"""av2_horizon_prep_v02 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md sections 6 and 9) = av2_horizon_prep_v01 with
one change: an export counts as AV2 when its record's dataset tag starts with "av2" (v01: equals "av2_sensor_val"), so both
guards (--allow-av2-propagation for --propagate-only; the frozen-plan hash for the residual mode) also hold for the v02 tag
"av2_sensor_val_train". It refuses to overwrite --out. The propagation (propagate, build_models) is v01's, unchanged.

av2_horizon_prep_v01: the horizon step of the Programme A pipeline, ported for Argoverse 2 (Claude line, 1 Nov 2026).

OUTCOME BOUNDARY (AV2_TRACKER_PORT_DESIGN_v01.md section 9). Two parts:
  propagate()     = x1_horizon_prep_v04: each exported track's own filter prediction repeated without measurement
                    updates for 8 steps of LiDAR_interval (0.5 s): LinearKalmanFilter x = F x, P = F P F' + Q;
                    ExtendKalmanFilter F = J(x), x = f(x), P = F P F' + Q; ExtendedKalmanFilterRotate F = J(x), R = rot(x),
                    x = F x, P = F P F' + R Q R'. Tracker output only (no ground truth).
                    For has_velo = False exports (VoxelNeXt) the models are built with has_velo = False; Q does not
                    depend on it, so the propagation is the same algebra.
  horizon_rows()  = x1_lib_v03.build_horizon_rows: pairs each prediction at k + h with the paired instance's GT at k + h.
                    THE FIRST FUNCTION THAT READS A GROUND-TRUTH POSITION AT A LATER TIME. The AV2 GT table has the
                    x1_gt_prep format (av2_gt_prep_v01), so the nuScenes function is used unchanged.
Guards: on AV2 input (export record dataset == "av2_sensor_val") the residual mode refuses to run unless
--frozen-plan-sha256 is given and equals the SHA-256 of --frozen-plan; the propagate-only mode refuses unless
--allow-av2-propagation is given (a researcher decision; not used in v01). Tested on nuScenes only
(test_av2_horizon_on_nuscenes_v01.py).

Usage (CANMOT environment):
  python -B av2_horizon_prep_v01.py --experiment <id> --workers <export dirs> --out <horizon jsonl.gz> [--propagate-only]
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
CANMOT_ROOT = os.path.join(W_ROOT, "50_CODE", "third_party", "CANMOT")
STEPS_OUT = {1: "h0p5s", 2: "h1s", 3: "h1p5s", 4: "h2s", 5: "h2p5s", 6: "h3s", 7: "h3p5s", 8: "h4s"}
APPROVED_EXPERIMENTS = ("paper/local/canmot/sc", "paper/local/sample/trainval", "paper/baseline/poly_mot")
AV2_DATASET = "av2_sensor_val"


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build_models(environment, experiment, has_velo=None):
    sys.path.insert(0, os.path.join(CANMOT_ROOT, "src"))
    from canmot.cli import _compose
    from omegaconf import OmegaConf
    from canmot.motion_module import motion_model as MM
    cfg = OmegaConf.to_container(_compose(environment, experiment), resolve=True)
    assert cfg.get("experiment_id") == experiment
    dt, hv = cfg["basic"]["LiDAR_interval"], cfg["basic"]["has_velo"] if has_velo is None else has_velo
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
    return {"models": models, "kinds": kinds, "Qs": Qs, "Fl": Fl, "dt": dt, "q_sha": q_sha}


def propagate(r, M):
    """One export line -> {scene, k, tid, h0p5s..h4s: [x, y, Pxx, Pxy, Pyy]} (x1_horizon_prep_v04, line for line)."""
    from canmot.data.script.NUSC_CONSTANT import CLASS_SEG_TO_STR_CLASS
    lab = int(CLASS_SEG_TO_STR_CLASS[r["tracking_name"]])
    model, kind, Q = M["models"][lab], M["kinds"][lab], M["Qs"][lab]
    st = np.asarray(r["state10"], dtype=float).reshape(-1, 1)
    P = np.asarray(r["P10"], dtype=float)
    assert P.shape == (st.shape[0], st.shape[0]) == Q.shape, "state, P and Q dimensions differ"
    out = {"scene": r["scene"], "k": r["frame_id"], "tid": r["tracking_id"]}
    for step in range(1, 9):
        if kind == "LinearKalmanFilter":
            F = M["Fl"][lab]
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
    return out


def horizon_rows(rows, pred, samples, gt_by_sample, racks_by_sample, key="h2s", steps=4):
    """THE OUTCOME BOUNDARY: first read of a GT position at k + steps. x1_lib_v03.build_horizon_rows, unchanged."""
    sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "x1"))
    import x1_lib_v03 as L
    return L.build_horizon_rows(rows, pred, samples, gt_by_sample, racks_by_sample, key=key, steps=steps)


def _dataset_of(worker):
    er = json.load(open(os.path.join(worker, "x1_export_record.json")))
    return er.get("dataset", "nuscenes"), er


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--environment", default="my_machine")
    ap.add_argument("--experiment", required=True, choices=APPROVED_EXPERIMENTS)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--propagate-only", action="store_true")
    ap.add_argument("--allow-av2-propagation", action="store_true")
    ap.add_argument("--frozen-plan", default=None)
    ap.add_argument("--frozen-plan-sha256", default=None)
    a = ap.parse_args()
    datasets = set()
    hv = None
    for w in a.workers:
        ds, er = _dataset_of(w)
        datasets.add(ds)
        assert er["resolved_config"].get("experiment_id") == a.experiment, "export was made with another experiment: " + w
        hv_w = er["resolved_config"]["basic"]["has_velo"]
        assert hv in (None, hv_w)
        hv = hv_w
    if any(str(d).lower().startswith("av2") for d in datasets):   # v02 (v01: AV2_DATASET in datasets)
        if a.propagate_only and not a.allow_av2_propagation:
            raise SystemExit("refused: AV2 export; propagation on AV2 needs --allow-av2-propagation (researcher decision)")
        if not a.propagate_only:
            if not (a.frozen_plan and a.frozen_plan_sha256 and sha256_path(a.frozen_plan) == a.frozen_plan_sha256):
                raise SystemExit("refused: AV2 export; the residual step needs a frozen plan and its SHA-256 (D15 section 4)")
    if not a.propagate_only:
        raise SystemExit("the residual step is a library call (horizon_rows); this CLI writes predictions only")
    if os.path.exists(a.out):
        raise SystemExit("refused: %s exists (v02 never overwrites)" % a.out)
    M = build_models(a.environment, a.experiment, has_velo=hv)
    n = 0
    with gzip.open(a.out, "wt") as fo:
        for w in a.workers:
            with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt") as f:
                for line in f:
                    fo.write(json.dumps(propagate(json.loads(line), M)) + "\n")
                    n += 1
    print("records", n, "dt", M["dt"], "experiment", a.experiment, "filters", sorted(set(M["kinds"].values())), "Q_sha256", M["q_sha"])
    print("HORIZON PREP DONE")


if __name__ == "__main__":
    sys.exit(main())
