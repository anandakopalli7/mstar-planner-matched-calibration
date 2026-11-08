#!/usr/bin/env python3
"""av2_track_v02 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md sections 6, 7, 9) = av2_track_v01 with:
  * av2_common_v02 (detector "owncp" = our own CenterPoint, has_velo True);
  * the export record's "dataset" is "av2_sensor_val" when every log of the adapter receipt resolves to 30_DATA/av2_val
    (as v01), otherwise "av2_sensor_val_train" (both normalise to "av2" in the C1 guard; av2_horizon_prep_v02 treats both
    as AV2);
  * per-log checkpoints: after each log, its export lines go to <out>/parts/<log>.jsonl.gz and its per-frame records,
    visited frames, K1 violations, counts, minimum eigenvalues, class counts and tokens to <out>/parts/<log>.state.json
    (written atomically, last). On a restart a log whose state matches (harness, subset SHA-256, experiment, detector,
    has_velo, fast-convex flag, sequence and frame indices) and whose part decompresses to the recorded SHA-256 is reused
    (the recorded hash is of the bytes the text-mode gzip writer emits, with v01's platform newline: CR LF on Windows).
    CANMOT's Tracker.reset() runs at every log's first frame (all trajectories and id_seed cleared), so a log's lines do
    not depend on the logs before it. At the end x1_tracks.jsonl.gz (parts in selection order), x1_per_frame.json and
    x1_export_record.json are assembled with v01's code and parts/ is removed. A run that fails its gates keeps parts/ and
    writes x1_export_record_FAILED.json instead;
  * --test-stop-after N (tests only): exit with code 3 after N newly tracked logs, before assembling (a simulated crash).
The tracking loop, the record criteria and the export lines are v01's.

av2_track_v01: CANMOT (T1 paper/local/canmot/sc, T2 paper/local/sample/trainval) and Poly-MOT through CANMOT
(T3 paper/baseline/poly_mot) on Argoverse 2 val, one detector subset per process (Claude line, 1 Nov 2026).

Design: AV2_TRACKER_PORT_DESIGN_v01.md sections 4.4, 5, 6, 8. The export record is written by the same code as
x1_export_v06.py: this runner imports that file and uses its verbatim copies of run.py's loop body (filter_classes,
export_frame, postprocess_token) and its read-only state capture (state_export, mat_check, find_trajectory).
Differences from x1_export_v06, all recorded in the run record:
  * frames come from av2_tracker_input_v01 subsets (tokens "<log>_<ts_ns>", one sequence per log) instead of nuScenes
    scene chains; P5 checks the subset hash against the adapter receipt; run.py's nuScenes dataset/detector checks are
    replaced by its Python-version and locked-dependency checks (shim S2);
  * has_velo is set from the detector (False for VoxelNeXt) and, when False, shim S3 is installed in memory:
    the 9 x 9 measurement noise of CV (T1/T2) and CA (T3 two-wheelers, trailer) is reduced to its (x, y, z, w, l, h, yaw)
    block, and the EKF-rotate initial covariance gets variance 10 for the unobserved vx, vy (CANMOT's own vz rule);
  * the native covariance is 9 x 9 or 7 x 7 (C1 checks the dimension the configuration implies);
  * per-frame records carry timestamp_ns and the actual dt to the previous frame.
No ground truth is read; no evaluation is called (CANMOT's evaluate path computes NEES; design section 9).

Usage (CANMOT environment):
  python -I -B av2_track_v02.py --experiment paper/local/canmot/sc --detector owncp --receipt <receipt.json> --worker 0
         --out <dir> [--fast-convex] [--logs <log ids>]
"""
import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import av2_common_v02 as C  # noqa: E402

X1_DIR = os.path.join(C.W_ROOT, "50_CODE", "x1")
sys.path.insert(0, X1_DIR)
import x1_export_v06 as X  # noqa: E402  (verbatim run.py copies and state capture; nothing is executed at import)

HARNESS_VERSION = "av2_track_v02 (2026-11-05, checkpoint hash fix): av2_track_v01's x1_export_v06 loop and record on AV2 subsets; shims S2, S3; per-log checkpoints"
CANMOT_ROOT = os.path.join(C.W_ROOT, "50_CODE", "third_party", "CANMOT")
KEEP7 = [0, 1, 2, 3, 4, 5, 8]
CRITERIA = dict(X.CRITERIA)
CRITERIA["P5"] = "detection subset SHA-256 equals the adapter receipt; receipt detector equals the requested detector"
CRITERIA["P6"] = "experiment in APPROVED_EXPERIMENTS and composed as requested; has_velo equals the detector's"
CRITERIA["T1"] = "frames visited in subset order with frame ids 0..n-1 per log"
CRITERIA["F1"] = "expected token set = the receipt's tokens of the selected logs; all present"
CRITERIA["C1"] = "every emitted track has a native covariance of the configured measurement dimension (9, or 7 without velocity) and a recorded P of its state dimension"
COUNT_KEYS = ("tracks", "shape_ok", "finite_ok", "sym_ok", "pd_ok", "hph_ok")


def install_no_velocity_shim():
    """Shim S3 (design section 8), in memory only; returns a description for the run record."""
    from canmot.motion_module import motion_model as MM
    from canmot.motion_module import kalman_filter as KF
    cv_r, ca_r = MM.CV.getMeaNoiseR, MM.CA.getMeaNoiseR
    rot_init = KF.ExtendedKalmanFilterRotate.initialize

    def cv_getMeaNoiseR(self, cls_label):
        R = np.asarray(cv_r(self, cls_label))
        return R[np.ix_(KEEP7, KEEP7)] if (not self.has_velo and R.shape == (9, 9)) else R

    def ca_getMeaNoiseR(self, cls_label):
        R = np.asarray(ca_r(self, cls_label))
        return R[np.ix_(KEEP7, KEEP7)] if (not self.has_velo and R.shape == (9, 9)) else R

    def rot_initialize(self, det_infos):
        rot_init(self, det_infos)
        if not self.has_velo:
            assert self.P.shape == (10, 10) and self.P[6, 6] == 0 and self.P[7, 7] == 0
            self.P[6, 6] = 10.0
            self.P[7, 7] = 10.0

    MM.CV.getMeaNoiseR = cv_getMeaNoiseR
    MM.CA.getMeaNoiseR = ca_getMeaNoiseR
    KF.ExtendedKalmanFilterRotate.initialize = rot_initialize
    return {"S3": "CV/CA getMeaNoiseR -> R[(x,y,z,w,l,h,yaw)] block when has_velo is False; "
                  "ExtendedKalmanFilterRotate.initialize: P[6,6] = P[7,7] = 10 when has_velo is False"}


def gz_sha256(path):
    """SHA-256 and byte count of a gzip file's decompressed content."""
    h, n = hashlib.sha256(), 0
    with gzip.open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def _plain(o):
    return o.item() if hasattr(o, "item") else str(o)


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, default=_plain)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def receipt_dataset(receipt):
    logs = sorted({lg for s in receipt["subsets"] for lg in s["logs"]})
    return "av2_sensor_val" if all(C.log_part(lg) == "val150" for lg in logs) else "av2_sensor_val_train"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--environment", default="my_machine")
    ap.add_argument("--experiment", required=True, choices=X.APPROVED_EXPERIMENTS)
    ap.add_argument("--detector", required=True, choices=sorted(C.DET_PATHS))
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--worker", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fast-convex", action="store_true")
    ap.add_argument("--logs", nargs="*", default=None, help="restrict to these logs of the subset (equivalence tests)")
    ap.add_argument("--test-stop-after", type=int, default=0, help="tests only: exit 3 after N newly tracked logs")
    a = ap.parse_args(argv)
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    if os.path.exists(os.path.join(a.out, "x1_export_record.json")):
        raise SystemExit("refused: %s already holds an export record (v02 never overwrites)" % a.out)
    parts_dir = os.path.join(a.out, "parts")
    os.makedirs(parts_dir, exist_ok=True)
    repo = os.path.realpath(CANMOT_ROOT)
    rec = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "harness_version": HARNESS_VERSION,
           "python": sys.version, "executable": sys.executable, "argv": sys.argv, "criteria": {},
           "criteria_text": CRITERIA, "reasons": [], "status": None, "dataset": None,
           "detector": a.detector, "shims": {"S1": "AV2 -> nuScenes-format detection JSON (av2_tracker_input_v01 / v02)",
                                             "S2": "run.py validate_config replaced by its version and dependency checks"}}
    t0 = time.time()
    counts = {k: 0 for k in COUNT_KEYS}
    min_eig_native = min_eig_P = None
    per_frame, visited, kviol, seen_tokens, bad_assoc = [], [], [], set(), 0
    class_counts = {}
    reused, ran, log_seconds = [], [], {}
    try:
        sys.path.insert(0, os.path.join(repo, "src"))
        import canmot  # noqa: F401
        import nuscenes  # noqa: F401
        from canmot.cli import _compose
        from omegaconf import OmegaConf
        spec = importlib.util.spec_from_file_location("canmot_run", os.path.join(repo, "run.py"))
        run_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_mod)
        cfg = OmegaConf.to_container(_compose(a.environment, a.experiment), resolve=True)
        has_velo = C.DET_HAS_VELO[a.detector]
        cfg["basic"]["has_velo"] = has_velo
        receipt = json.load(open(a.receipt))
        rec["dataset"] = receipt_dataset(receipt)
        sub = receipt["subsets"][a.worker]
        prov = X.verify_provenance(repo, sub["path"], {"canmot": canmot, "nuscenes": nuscenes})
        prov["P5_nuscenes_hash_check_replaced"] = True
        prov["P5"] = (C.sha256_path(sub["path"]) == sub["sha256"]) and receipt["detector"] == a.detector and receipt["partition_exact"]
        prov["ok"] = all(prov[k] for k in ("P1", "P2", "P3", "P4", "P5"))
        rec["provenance"] = prov
        for k in ("P1", "P2", "P3", "P4", "P5"):
            rec["criteria"][k] = bool(prov[k])
        if not prov["ok"]:
            raise RuntimeError("provenance failed: " + ", ".join(k for k in ("P1", "P2", "P3", "P4", "P5") if not prov[k]))
        import platform
        dep = run_mod.dependency_version_mismatches()
        rec["environment_checks"] = {"python": platform.python_version(), "dependency_mismatches": dep}
        if platform.python_version_tuple()[:2] != ("3", "10") or dep:
            raise RuntimeError("environment check failed: %s" % dep)
        if not has_velo:
            rec["shims"].update(install_no_velocity_shim())
        if a.fast_convex:
            import fast_convex_v01
            rec["fast_convex"] = {"patched": fast_convex_v01.install(), "module_sha256": C.sha256_path(fast_convex_v01.__file__)}
            rec["shims"]["S4"] = "fast_convex_v01 (numba hull area)"
        rec["criteria"]["P6"] = (cfg.get("experiment_id") == a.experiment and a.experiment in X.APPROVED_EXPERIMENTS
                                 and cfg["basic"]["has_velo"] == has_velo)
        rec["resolved_config"] = cfg
        rec["subset"] = {"receipt": os.path.abspath(a.receipt), "worker": a.worker, "path": sub["path"], "sha256": sub["sha256"],
                         "logs": sub["logs"]}
        from canmot.dataloader.nusc_loader import NuScenesloader
        from canmot.tracking.nusc_tracker import Tracker
        from nuscenes.eval.common.config import config_factory
        loader = NuScenesloader(sub["path"], receipt["first_tokens"], cfg)
        rec["loader"] = {"frames": len(loader), "sequences": loader.max_seq_id + 1}
        if loader.all_sample_token != sub["tokens"]:
            raise RuntimeError("loader token order differs from the receipt")
        logs = list(a.logs) if a.logs else list(sub["logs"])
        selection, problems = [], []
        for lg in logs:
            idx = [i for i, t in enumerate(loader.all_sample_token) if t.startswith(lg + "_")]
            seqs = {loader.seq_ids[i] for i in idx}
            if not idx or len(seqs) != 1 or idx != list(range(idx[0], idx[0] + len(idx))) or loader.frame_ids[idx[0]] != 0:
                problems.append("log %s: not one contiguous sequence starting at frame 0" % lg)
                continue
            selection.append((lg, seqs.pop(), idx))
        selection.sort(key=lambda t: t[2][0])
        if problems or len(selection) != len(logs):
            raise RuntimeError("frame selection problems: %s" % problems[:5])
        rec["selection"] = [{"scene": s, "seq_id": q, "first_index": idx[0], "frames": len(idx)} for s, q, idx in selection]
        expected = [loader.all_sample_token[i] for _, _, idx in selection for i in idx]
        eval_config = config_factory("tracking_nips_2019")  # class names only (filter_classes); no evaluation
        tracker = Tracker(config=cfg)
        classes = cfg.get("limit_classes")
        meas_dim = 9 if has_velo else 7
        rec["meas_dim"] = meas_dim
        ck_base = {"harness": HARNESS_VERSION, "subset_sha256": sub["sha256"], "experiment": a.experiment, "detector": a.detector,
                   "has_velo": has_velo, "fast_convex": bool(a.fast_convex), "worker": a.worker}
        states = []
        for scene, seq, indices in selection:
            key = json.loads(json.dumps(dict(ck_base, scene=scene, seq_id=int(seq), indices=[int(i) for i in indices])))
            part = os.path.join(parts_dir, scene + ".jsonl.gz")
            spath = os.path.join(parts_dir, scene + ".state.json")
            if os.path.exists(spath) and os.path.exists(part):
                stt = json.load(open(spath))
                if stt.get("key") == key and list(gz_sha256(part)) == [stt["lines_sha256"], stt["lines_bytes"]]:
                    states.append(stt)
                    reused.append(scene)
                    continue
            tl0 = time.time()
            L = {"per_frame": [], "visited": [], "kviol": [], "tokens": [], "bad_assoc": 0, "counts": {k: 0 for k in COUNT_KEYS},
                 "min_eig_native": None, "min_eig_P": None, "class_counts": {}}
            seen_l = set()
            h, nbytes, nlines = hashlib.sha256(), 0, 0
            cnt = L["counts"]
            with gzip.open(part, "wt", encoding="utf-8", compresslevel=6) as gz:
                prev_tracks, prev_ts = 0, None
                for i in indices:
                    frame_data = loader[i]
                    L["visited"].append((i, frame_data["timestamp"], frame_data["seq_id"], frame_data["frame_id"]))
                    frame_data = X.filter_classes(frame_data, classes, eval_config)
                    n_dets = int(frame_data["det_num"])
                    tracker.tracking(frame_data)
                    token = frame_data["sample_token"]
                    ts_ns = int(token.rsplit("_", 1)[1])
                    raw = X.export_frame(frame_data)
                    dumps = {}
                    if "no_val_track_result" not in frame_data:
                        for pb in frame_data["box_track_res"]:
                            d = X.state_export(tracker, pb)
                            dumps[d["tracking_id"]] = d
                    if token in seen_l:
                        L["per_frame"].append({"scene": scene, "token": token, "error": "duplicate frame record"})
                        continue
                    seen_l.add(token)
                    L["tokens"].append(token)
                    kept = X.postprocess_token(raw)
                    for r in kept:
                        cnt["tracks"] += 1
                        if r["sample_token"] != token:
                            L["bad_assoc"] += 1
                        L["class_counts"][r["tracking_name"]] = L["class_counts"].get(r["tracking_name"], 0) + 1
                        c = X.mat_check(r.get("covariance", []), meas_dim)
                        d = dumps.get(r["tracking_id"])
                        pc = X.mat_check(d["P"], len(d["state"])) if d and "P" in d else {"shape_ok": False, "finite": False, "symmetric": False, "pd": False, "min_eig": None}
                        cnt["shape_ok"] += int(c["shape_ok"] and pc["shape_ok"] and r.get("state_dim") == meas_dim)
                        cnt["finite_ok"] += int(c["finite"] and pc["finite"])
                        cxy = X.mat_check(np.asarray(r.get("covariance", []), dtype=float)[:2, :2], 2) if c["shape_ok"] else c
                        cnt["sym_ok"] += int(cxy["symmetric"] and pc["symmetric"])
                        cnt["pd_ok"] += int(cxy["pd"] and pc["pd"])
                        if c["min_eig"] is not None:
                            L["min_eig_native"] = c["min_eig"] if L["min_eig_native"] is None else min(L["min_eig_native"], c["min_eig"])
                        if pc["min_eig"] is not None:
                            L["min_eig_P"] = pc["min_eig"] if L["min_eig_P"] is None else min(L["min_eig_P"], pc["min_eig"])
                        if d and "HPH_T" in d and c["shape_ok"] and c["finite"]:
                            native = np.asarray(r["covariance"], dtype=float)
                            rel = float(np.max(np.abs(d["HPH_T"] - native))) / max(float(np.max(np.abs(native))), 1e-300)
                            cnt["hph_ok"] += int(rel <= X.REL_TOL)
                        line = {"scene": scene, "seq_id": int(seq), "frame_id": int(frame_data["frame_id"]),
                                "sample_token": token, "tracking_id": r["tracking_id"], "tracking_name": r["tracking_name"],
                                "tracking_score": float(r["tracking_score"]), "translation": r["translation"],
                                "size": r["size"], "rotation": r["rotation"], "velocity": r["velocity"],
                                "cov9": np.asarray(r["covariance"], dtype=float).tolist(),
                                "state10": d["state"].tolist() if d and "state" in d else None,
                                "P10": d["P"].tolist() if d and "P" in d else None,
                                "pool": d.get("pool") if d else None}
                        s_line = json.dumps(line) + "\n"
                        gz.write(s_line)
                        # the text-mode gzip writer (as v01's) translates "\n" to os.linesep; hash the bytes it writes
                        b = s_line.replace("\n", os.linesep).encode("utf-8")
                        h.update(b)
                        nbytes += len(b)
                        nlines += 1
                    pf = {"scene": scene, "seq_id": int(seq), "index": i, "timestamp": frame_data["timestamp"],
                          "frame_id": int(frame_data["frame_id"]), "token": token, "timestamp_ns": ts_ns,
                          "dt_s": None if prev_ts is None else 1e-9 * (ts_ns - prev_ts), "dets_post_filter": n_dets,
                          "tracks": len(kept), "prev_tracks": prev_tracks, "is_first_frame": bool(frame_data["is_first_frame"])}
                    L["per_frame"].append(pf)
                    if not (0 <= len(kept) <= n_dets + prev_tracks):
                        L["kviol"].append(pf)
                    prev_tracks, prev_ts = len(kept), ts_ns
            L.update(key=key, lines=nlines, lines_bytes=nbytes, lines_sha256=h.hexdigest(), seconds=round(time.time() - tl0, 1))
            write_json_atomic(spath, L)
            states.append(json.load(open(spath)))     # the same JSON round trip as a reused state
            ran.append(scene)
            print("log %s done (%d frames) at %.0f s" % (scene, len(indices), time.time() - t0), flush=True)
            if a.test_stop_after and len(ran) >= a.test_stop_after:
                print("TEST STOP after %d newly tracked logs (simulated crash; no assembly)" % len(ran), flush=True)
                sys.stdout.flush()
                os._exit(3)
        rec["wall_seconds_tracking"] = round(time.time() - t0, 1)
        # aggregate the per-log states in selection order (v01's accumulators)
        for stt in states:
            per_frame += stt["per_frame"]
            visited += [tuple(v) for v in stt["visited"]]
            kviol += stt["kviol"]
            bad_assoc += stt["bad_assoc"]
            for k in COUNT_KEYS:
                counts[k] += stt["counts"][k]
            if stt["min_eig_native"] is not None:
                min_eig_native = stt["min_eig_native"] if min_eig_native is None else min(min_eig_native, stt["min_eig_native"])
            if stt["min_eig_P"] is not None:
                min_eig_P = stt["min_eig_P"] if min_eig_P is None else min(min_eig_P, stt["min_eig_P"])
            for k, v in stt["class_counts"].items():
                class_counts[k] = class_counts.get(k, 0) + v
            dup_across = set(stt["tokens"]) & seen_tokens
            if dup_across:
                per_frame.append({"scene": stt["key"]["scene"], "token": sorted(dup_across)[0], "error": "duplicate frame record"})
            seen_tokens |= set(stt["tokens"])
            log_seconds[stt["key"]["scene"]] = stt["seconds"]
        tracks_path = os.path.join(a.out, "x1_tracks.jsonl.gz")
        h_all = hashlib.sha256()
        with gzip.open(tracks_path, "wb", compresslevel=6) as gz:
            for scene, _, _ in selection:
                with gzip.open(os.path.join(parts_dir, scene + ".jsonl.gz"), "rb") as f:
                    for b in iter(lambda: f.read(1 << 20), b""):
                        gz.write(b)
                        h_all.update(b)
        exp_set = set(expected)
        missing = sorted(exp_set - seen_tokens)
        unexpected = sorted(seen_tokens - exp_set)
        dup = [p for p in per_frame if p.get("error")]
        rec["criteria"]["F1"] = len(exp_set) == len(expected) and not missing
        rec["criteria"]["F2"] = not dup and len(visited) == len(set(v[0] for v in visited))
        rec["criteria"]["F3"] = not unexpected
        rec["criteria"]["F4"] = bad_assoc == 0
        if missing:
            rec["reasons"].append("missing tokens: %d" % len(missing))
        if unexpected:
            rec["reasons"].append("unexpected tokens: %d" % len(unexpected))
        order_ok = all(v[0] == v[1] for v in visited)
        frame_ok = all([p["frame_id"] for p in per_frame if p.get("scene") == s and not p.get("error")] == list(range(len(idx)))
                       for s, q, idx in selection)
        first_ok = all([p["is_first_frame"] for p in per_frame if p.get("scene") == s and not p.get("error")][:1] == [True]
                       for s, q, idx in selection)
        rec["criteria"]["T1"] = order_ok and frame_ok
        rec["criteria"]["T2"] = first_ok
        n = counts["tracks"]
        for k, key_ in (("C1", "shape_ok"), ("C2", "finite_ok"), ("C3", "sym_ok"), ("C4", "pd_ok"), ("C5", "hph_ok")):
            rec["criteria"][k] = n > 0 and counts[key_] == n
            if not rec["criteria"][k]:
                rec["reasons"].append("%s failed on %d of %d tracks" % (k, n - counts[key_], n))
        rec["criteria"]["K1"] = not kviol
        ratios = [p["tracks"] / p["dets_post_filter"] for p in per_frame if not p.get("error") and p["dets_post_filter"] > 0]
        med = float(np.median(ratios)) if ratios else None
        rec["criteria"]["K2"] = med is not None and 0.2 <= med <= 1.5
        dts = [p["dt_s"] for p in per_frame if p.get("dt_s") is not None]
        rec["stats"] = dict(counts, expected_tokens=len(expected), frames_exported=len(seen_tokens),
                            min_eig_native=min_eig_native, min_eig_P=min_eig_P, median_tracks_per_det=med,
                            class_counts=class_counts, peak_working_set_mb=X.peak_working_set_mb(),
                            dt_s={"min": min(dts), "median": float(np.median(dts)), "max": max(dts)} if dts else None)
        with open(os.path.join(a.out, "x1_per_frame.json"), "w") as f:
            json.dump(per_frame, f)
        rec["output_sha256"] = {"x1_tracks.jsonl.gz": C.sha256_path(tracks_path),
                                "x1_tracks.jsonl (decompressed)": h_all.hexdigest(),
                                "x1_per_frame.json": C.sha256_path(os.path.join(a.out, "x1_per_frame.json"))}
        rec["checkpoint"] = {"logs_reused_from_checkpoints": reused, "logs_tracked_in_this_process": ran,
                             "tracking_seconds_per_log": log_seconds,
                             "tracking_seconds_sum": round(sum(log_seconds.values()), 1)}
        rec["criteria"]["X1"] = True
    except Exception as e:
        import traceback
        rec["reasons"].append("exception: %r" % (e,))
        rec["traceback"] = traceback.format_exc()
        rec["criteria"]["X1"] = False
    finally:
        for k in CRITERIA:
            rec["criteria"].setdefault(k, False)
        rec["failed_criteria"] = [k for k, v in rec["criteria"].items() if not v]
        rec["status"] = "PASS" if not rec["failed_criteria"] and not rec["reasons"] else "FAIL"
        gating = [k for k in rec["failed_criteria"] if k != "K2"]
        rec["status_X1_gates"] = "PASS" if not gating and not [r for r in rec["reasons"] if "K2" not in r] else "FAIL"
        rec["wall_seconds_total"] = round(time.time() - t0, 1)
        if rec["status_X1_gates"] == "PASS":
            with open(os.path.join(a.out, "x1_export_record.json"), "w") as f:
                json.dump(rec, f, indent=2, default=str)
            shutil.rmtree(parts_dir, ignore_errors=True)
        else:
            # a run that fails its gates keeps its checkpoints for a resume and writes its record under another name
            with open(os.path.join(a.out, "x1_export_record_FAILED.json"), "w") as f:
                json.dump(rec, f, indent=2, default=str)
        print("AV2 export:", rec["status"], "| failed:", rec["failed_criteria"], "| reasons:", rec["reasons"][:5], flush=True)
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
