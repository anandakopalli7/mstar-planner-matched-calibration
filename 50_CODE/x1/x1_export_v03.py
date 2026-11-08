#!/usr/bin/env python3
"""X1 real-data input (Claude line, v01, 30 Oct 2026): CANMOT covariance export on all nuScenes val scenes.

Adapted from the archived F-A4 harness v2 (2026-10-10; 00_CONTEXT/archive_fa4_20261010/.../fa4_export_smoke_v2.py).
Kept from the archive: provenance criteria P1-P6; verbatim copies of run.py's loop body (class filter, export record)
and per-token post-processing (score sort, cap 500); the read-only state/P capture with the HPH^T association check;
the F/C/K integrity criteria. Changed: every val scene instead of four smoke scenes; output streamed per scene as
gzip JSON lines; peak memory read through the Windows API instead of `resource`; evaluate() is not called.

Run from the CANMOT repository root inside the CANMOT environment:
    python -B <this file> --environment my_machine --trainval-meta <dir with scene.json, sample.json> --out <dir>
"""
import argparse
import datetime as dt
import gzip
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time

import numpy as np

HARNESS_VERSION = "x1_export_v03 (2026-10-30): v02 + --split {val,train} (tracker parameters unchanged)"
APPROVED_CANMOT_COMMIT = "515d0792a4a2dddf4f3f26c2fa26c54bb1c14167"
APPROVED_DEVKIT_COMMIT = "e4818ff92714d28aefa3ffe0e07dacbd7f64e840"
APPROVED_DETECTION_SHA256 = {"val": "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e",
                             "train": "547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145"}
APPROVED_EXPERIMENT = "paper/local/canmot/sc"
EXECUTED_TREE = ["run.py", "src/canmot", "config", "data/utils", "requirements-lock.txt", "reproducibility", ".gitmodules", "pyproject.toml"]
NATIVE_CAP = 500
MEAS_DIM = 9
STATE_DIM = 10
REL_TOL = 1e-9

CRITERIA = {
    "P1": "CANMOT repository HEAD equals the approved commit",
    "P2": "nuScenes devkit submodule HEAD equals the approved commit",
    "P3": "executed tree is clean",
    "P4": "imported canmot and nuscenes packages originate from the checkout and its submodule; run.py unmodified",
    "P5": "detection file SHA-256 equals the approved value",
    "P6": "run.py validate_config passed and the composed experiment is the approved one on split val",
    "T1": "frames visited in original global order with native timestamps (index) and frame ids 0..n-1 per scene",
    "T2": "each scene is one contiguous sequence; one Tracker with native per-sequence reset",
    "F1": "expected token set = union of all val scene chains (devkit split list); all present",
    "F2": "no duplicate or overwritten frame record",
    "F3": "no unexpected token in the export",
    "F4": "every exported record's sample_token equals its frame's token",
    "C1": "every emitted track has a native covariance of shape 9x9 and a recorded P of shape 10x10",
    "C2": "all covariance entries finite",
    "C3": "native covariance and P symmetric (max|C-C^T| <= 1e-9 max|C|)",
    "C4": "native covariance and P positive-definite (Cholesky succeeds, min eigenvalue > 0)",
    "C5": "H(state) P H(state)^T recomputed from the owning trajectory equals the native covariance (1e-9 relative)",
    "K1": "per frame: 0 <= tracks_t <= dets_t + tracks_{t-1} (tracks_{-1} = 0 at each sequence start)",
    "K2": "aggregate: median(tracks/dets) over frames with dets > 0 within [0.2, 1.5]",
    "X1": "no exception; record written",
}


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def peak_working_set_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return None
        return round(pmc.PeakWorkingSetSize / 2 ** 20, 1)
    except Exception:
        return None


def _git(path, *args):
    try:
        r = subprocess.run(["git", "-C", path] + list(args), capture_output=True, text=True, check=True)
        return r.stdout.strip(), None
    except (OSError, subprocess.CalledProcessError) as e:
        return None, "git %s: %s" % (" ".join(args), (getattr(e, "stderr", "") or repr(e)).strip())


def verify_provenance(repo, detection_path, modules):
    repo = os.path.realpath(repo)
    out = {"repo": repo}
    head, e1 = _git(repo, "rev-parse", "HEAD")
    out["canmot_commit"], out["canmot_commit_error"] = head, e1
    out["P1"] = head == APPROVED_CANMOT_COMMIT
    sub = os.path.join(repo, "dependencies_repos", "nuscenes-devkit")
    sh, e2 = _git(sub, "rev-parse", "HEAD")
    out["devkit_commit"], out["devkit_commit_error"] = sh, e2
    out["P2"] = sh == APPROVED_DEVKIT_COMMIT
    st, e3 = _git(repo, "status", "--porcelain", "--untracked-files=all", "--", *EXECUTED_TREE)
    out["executed_tree_status"], out["status_error"] = st, e3
    out["P3"] = (st == "")

    def origin(m):
        f = getattr(m, "__file__", None) if m is not None else None
        return os.path.realpath(f) if f else None
    cf, nf = origin(modules.get("canmot")), origin(modules.get("nuscenes"))
    out["canmot_module_file"], out["nuscenes_module_file"] = cf, nf
    out["canmot_from_checkout"] = bool(cf) and cf.startswith(os.path.join(repo, "src", "canmot") + os.sep)
    out["nuscenes_from_submodule"] = bool(nf) and nf.startswith(os.path.join(sub, "python-sdk", "nuscenes") + os.sep)
    blob, _ = _git(repo, "hash-object", "--", "run.py")
    head_blob, _ = _git(repo, "rev-parse", "HEAD:run.py")
    out["run_py_unmodified"] = blob is not None and blob == head_blob
    out["P4"] = out["canmot_from_checkout"] and out["nuscenes_from_submodule"] and out["run_py_unmodified"]
    out["detection_path"] = detection_path
    out["detection_sha256"] = sha256_path(detection_path) if os.path.isfile(detection_path) else None
    out["P5"] = out["detection_sha256"] in APPROVED_DETECTION_SHA256.values()
    out["ok"] = all(out[k] for k in ("P1", "P2", "P3", "P4", "P5"))
    return out


def scene_chains(trainval_meta, scene_names):
    with open(os.path.join(trainval_meta, "scene.json")) as f:
        scenes = {s["name"]: s for s in json.load(f)}
    with open(os.path.join(trainval_meta, "sample.json")) as f:
        samples = {s["token"]: s for s in json.load(f)}
    chains = {}
    for name in scene_names:
        sc = scenes[name]
        chain, tok = [], sc["first_sample_token"]
        while tok:
            chain.append(tok)
            tok = samples[tok]["next"]
        if len(chain) != sc["nbr_samples"] or chain[-1] != sc["last_sample_token"]:
            raise RuntimeError("scene %s: chain mismatch" % name)
        chains[name] = chain
    return chains


def select_frames(loader, chains):
    tok_index = {t: i for i, t in enumerate(loader.all_sample_token)}
    out, problems = [], []
    for name, chain in chains.items():
        idx0 = tok_index.get(chain[0])
        if idx0 is None:
            problems.append("scene %s: first token not in the detection file" % name)
            continue
        seq = loader.seq_ids[idx0]
        indices = [i for i in range(len(loader.all_sample_token)) if loader.seq_ids[i] == seq]
        if indices != list(range(indices[0], indices[0] + len(indices))):
            problems.append("scene %s: sequence %d is not contiguous in the file" % (name, seq))
        if [loader.all_sample_token[i] for i in indices] != chain:
            problems.append("scene %s: sequence %d tokens differ from the scene chain" % (name, seq))
        if loader.frame_ids[indices[0]] != 0:
            problems.append("scene %s: first frame id is %r" % (name, loader.frame_ids[indices[0]]))
        out.append((name, seq, indices))
    out.sort(key=lambda t: t[2][0])
    return out, problems


# --- verbatim copies of run.py's loop body and post-processing (run.py:116-152 at the approved commit) ----------
def filter_classes(frame_data, classes_to_evaluate, eval_config):
    if classes_to_evaluate is not None:
        selected = [
            index for index, box in enumerate(frame_data["box_dets"])
            if eval_config.class_names.index(box.name) in classes_to_evaluate
        ]
        frame_data["box_dets"] = [frame_data["box_dets"][index] for index in selected]
        frame_data["np_dets"] = np.asarray([frame_data["np_dets"][index] for index in selected])
        frame_data["np_dets_bottom_corners"] = np.asarray(
            [frame_data["np_dets_bottom_corners"][index] for index in selected]
        )
        frame_data["det_num"] = len(selected)
        frame_data["no_dets"] = not selected
    return frame_data


def export_frame(frame_data):
    sample_results = []
    if "no_val_track_result" not in frame_data:
        for predicted_box in frame_data["box_track_res"]:
            box_result = {
                "sample_token": frame_data["sample_token"],
                "translation": [float(value) for value in predicted_box.center],
                "size": [float(value) for value in predicted_box.wlh],
                "rotation": [float(value) for value in predicted_box.orientation],
                "velocity": [float(predicted_box.velocity[0]), float(predicted_box.velocity[1])],
                "tracking_id": str(predicted_box.tracking_id),
                "tracking_name": predicted_box.name,
                "tracking_score": predicted_box.score,
            }
            if getattr(predicted_box, "covariance", None) is not None:
                box_result["covariance"] = predicted_box.covariance
                box_result["state_dim"] = len(predicted_box.covariance)
            sample_results.append(box_result)
    return sample_results


def postprocess_token(boxes):
    ranked = sorted(((-box["tracking_score"], index) for index, box in enumerate(boxes)))
    return [boxes[index] for _, index in ranked[:NATIVE_CAP]]


# ------------------------------------------------------------------------------------------------------------
def find_trajectory(tracker, tracking_id):
    for pool in ("active_tras", "tentative_tras", "dead_tras"):
        d = getattr(tracker, pool, None)
        if isinstance(d, dict):
            for key in (tracking_id, str(tracking_id)):
                if key in d:
                    return pool, d[key]
            try:
                k = int(tracking_id)
                if k in d:
                    return pool, d[k]
            except (TypeError, ValueError):
                pass
    return None, None


def state_export(tracker, predicted_box):
    pool, tra = find_trajectory(tracker, predicted_box.tracking_id)
    if tra is None:
        return {"tracking_id": str(predicted_box.tracking_id), "pool": None}
    mm = tra.motion_management
    P = np.asarray(mm.P, dtype=float)
    st = np.asarray(mm.state, dtype=float).reshape(-1, 1)
    H = np.asarray(mm.model.getMeaStateH(st), dtype=float)
    return {"tracking_id": str(predicted_box.tracking_id), "pool": pool, "state": st.ravel(), "P": P, "HPH_T": H @ P @ H.T}


def mat_check(M, n_expected):
    M = np.asarray(M, dtype=float)
    r = {"shape_ok": M.ndim == 2 and M.shape == (n_expected, n_expected), "finite": bool(np.all(np.isfinite(M)))}
    if not (r["shape_ok"] and r["finite"]):
        r.update({"symmetric": False, "pd": False, "min_eig": None})
        return r
    scale = max(float(np.max(np.abs(M))), 1e-300)
    r["symmetric"] = float(np.max(np.abs(M - M.T))) / scale <= REL_TOL
    S = (M + M.T) / 2
    try:
        np.linalg.cholesky(S)
        chol = True
    except np.linalg.LinAlgError:
        chol = False
    eig = np.linalg.eigvalsh(S)
    r["min_eig"] = float(eig.min())
    r["pd"] = bool(chol and eig.min() > 0)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--environment", required=True)
    ap.add_argument("--experiment", default=APPROVED_EXPERIMENT)
    ap.add_argument("--trainval-meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenes", nargs="*", default=None, help="subset for a code-integrity run; default = all val scenes")
    ap.add_argument("--split-receipt", default=None, help="split_receipt.json from x1_split_detections_v01.py")
    ap.add_argument("--worker", type=int, default=None)
    ap.add_argument("--split", default="val", choices=["val", "train"])
    a = ap.parse_args(argv)
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    repo = os.path.realpath(os.getcwd())
    rec = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "harness_version": HARNESS_VERSION,
           "python": sys.version, "executable": sys.executable, "argv": sys.argv, "criteria": {},
           "criteria_text": CRITERIA, "reasons": [], "status": None}
    t0 = time.time()
    counts = {k: 0 for k in ("tracks", "shape_ok", "finite_ok", "sym_ok", "pd_ok", "hph_ok")}
    min_eig_native = min_eig_P = None
    per_frame, visited, kviol, seen_tokens, bad_assoc = [], [], [], set(), 0
    class_counts = {}
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
        cfg["dataset_cfg"]["split"] = a.split
        split = cfg["dataset_cfg"]["split"]
        det_path = cfg["detector_cfg"]["ordered_detections_path"][split]
        prov = verify_provenance(repo, det_path, {"canmot": canmot, "nuscenes": nuscenes})
        rec["provenance"] = prov
        for k in ("P1", "P2", "P3", "P4", "P5"):
            rec["criteria"][k] = bool(prov[k])
        if not prov["ok"]:
            raise RuntimeError("provenance failed: " + ", ".join(k for k in ("P1", "P2", "P3", "P4", "P5") if not prov[k]))
        run_mod.validate_config(cfg)
        rec["criteria"]["P6"] = (cfg.get("experiment_id") == APPROVED_EXPERIMENT and split == a.split)
        rec["resolved_config"] = cfg
        from nuscenes.utils import splits as SPLITS
        scene_names = list(a.scenes) if a.scenes else list(getattr(SPLITS, a.split))
        loader_path = det_path
        if a.split_receipt is not None:
            receipt = json.load(open(a.split_receipt))
            assert receipt["source_sha256"] == APPROVED_DETECTION_SHA256[a.split] and receipt["partition_exact"]
            sub = receipt["subsets"][a.worker]
            assert sha256_path(sub["path"]) == sub["sha256"], "subset file changed since the split"
            loader_path, scene_names = sub["path"], list(sub["scenes"])
            rec["subset"] = {"receipt": os.path.abspath(a.split_receipt), "worker": a.worker, "path": sub["path"], "sha256": sub["sha256"]}
        rec["scenes_requested"] = len(scene_names)
        from canmot.dataloader.nusc_loader import NuScenesloader
        from canmot.tracking.nusc_tracker import Tracker
        from nuscenes.eval.common.config import config_factory
        loader = NuScenesloader(loader_path, cfg["dataset_cfg"]["first_token_path"], cfg)
        rec["loader"] = {"frames": len(loader), "sequences": loader.max_seq_id + 1}
        chains = scene_chains(a.trainval_meta, scene_names)
        selection, problems = select_frames(loader, chains)
        if problems or len(selection) != len(scene_names):
            raise RuntimeError("frame selection problems: %s" % problems[:5])
        rec["selection"] = [{"scene": s, "seq_id": q, "first_index": idx[0], "frames": len(idx)} for s, q, idx in selection]
        expected = [t for chain in chains.values() for t in chain]
        eval_config = config_factory("tracking_nips_2019")
        tracker = Tracker(config=cfg)
        classes = cfg.get("limit_classes")
        tracks_path = os.path.join(a.out, "x1_tracks.jsonl.gz")
        with gzip.open(tracks_path, "wt", encoding="utf-8", compresslevel=6) as gz:
            for scene, seq, indices in selection:
                prev_tracks = 0
                for i in indices:
                    frame_data = loader[i]
                    visited.append((i, frame_data["timestamp"], frame_data["seq_id"], frame_data["frame_id"]))
                    frame_data = filter_classes(frame_data, classes, eval_config)
                    n_dets = int(frame_data["det_num"])
                    tracker.tracking(frame_data)
                    token = frame_data["sample_token"]
                    raw = export_frame(frame_data)
                    dumps = {}
                    if "no_val_track_result" not in frame_data:
                        for pb in frame_data["box_track_res"]:
                            d = state_export(tracker, pb)
                            dumps[d["tracking_id"]] = d
                    if token in seen_tokens:
                        per_frame.append({"scene": scene, "token": token, "error": "duplicate frame record"})
                        continue
                    seen_tokens.add(token)
                    kept = postprocess_token(raw)
                    for r in kept:
                        counts["tracks"] += 1
                        if r["sample_token"] != token:
                            bad_assoc += 1
                        class_counts[r["tracking_name"]] = class_counts.get(r["tracking_name"], 0) + 1
                        c = mat_check(r.get("covariance", []), MEAS_DIM)
                        d = dumps.get(r["tracking_id"])
                        pc = mat_check(d["P"], STATE_DIM) if d and "P" in d else {"shape_ok": False, "finite": False, "symmetric": False, "pd": False, "min_eig": None}
                        counts["shape_ok"] += int(c["shape_ok"] and pc["shape_ok"] and r.get("state_dim") == MEAS_DIM)
                        counts["finite_ok"] += int(c["finite"] and pc["finite"])
                        counts["sym_ok"] += int(c["symmetric"] and pc["symmetric"])
                        counts["pd_ok"] += int(c["pd"] and pc["pd"])
                        if c["min_eig"] is not None:
                            min_eig_native = c["min_eig"] if min_eig_native is None else min(min_eig_native, c["min_eig"])
                        if pc["min_eig"] is not None:
                            min_eig_P = pc["min_eig"] if min_eig_P is None else min(min_eig_P, pc["min_eig"])
                        if d and "HPH_T" in d and c["shape_ok"] and c["finite"]:
                            native = np.asarray(r["covariance"], dtype=float)
                            rel = float(np.max(np.abs(d["HPH_T"] - native))) / max(float(np.max(np.abs(native))), 1e-300)
                            counts["hph_ok"] += int(rel <= REL_TOL)
                        line = {"scene": scene, "seq_id": int(seq), "frame_id": int(frame_data["frame_id"]),
                                "sample_token": token, "tracking_id": r["tracking_id"], "tracking_name": r["tracking_name"],
                                "tracking_score": float(r["tracking_score"]), "translation": r["translation"],
                                "size": r["size"], "rotation": r["rotation"], "velocity": r["velocity"],
                                "cov9": np.asarray(r["covariance"], dtype=float).tolist(),
                                "state10": d["state"].tolist() if d and "state" in d else None,
                                "P10": d["P"].tolist() if d and "P" in d else None,
                                "pool": d.get("pool") if d else None}
                        gz.write(json.dumps(line) + "\n")
                    pf = {"scene": scene, "seq_id": int(seq), "index": i, "timestamp": frame_data["timestamp"],
                          "frame_id": int(frame_data["frame_id"]), "token": token, "dets_post_filter": n_dets,
                          "tracks": len(kept), "prev_tracks": prev_tracks, "is_first_frame": bool(frame_data["is_first_frame"])}
                    per_frame.append(pf)
                    if not (0 <= len(kept) <= n_dets + prev_tracks):
                        kviol.append(pf)
                    prev_tracks = len(kept)
                print("scene %s done (%d frames) at %.0f s" % (scene, len(indices), time.time() - t0), flush=True)
        rec["wall_seconds_tracking"] = round(time.time() - t0, 1)
        # integrity criteria
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
        for k, key in (("C1", "shape_ok"), ("C2", "finite_ok"), ("C3", "sym_ok"), ("C4", "pd_ok"), ("C5", "hph_ok")):
            rec["criteria"][k] = n > 0 and counts[key] == n
            if not rec["criteria"][k]:
                rec["reasons"].append("%s failed on %d of %d tracks" % (k, n - counts[key], n))
        rec["criteria"]["K1"] = not kviol
        ratios = [p["tracks"] / p["dets_post_filter"] for p in per_frame if not p.get("error") and p["dets_post_filter"] > 0]
        med = float(np.median(ratios)) if ratios else None
        rec["criteria"]["K2"] = med is not None and 0.2 <= med <= 1.5
        rec["stats"] = dict(counts, expected_tokens=len(expected), frames_exported=len(seen_tokens),
                            min_eig_native=min_eig_native, min_eig_P=min_eig_P, median_tracks_per_det=med,
                            class_counts=class_counts, peak_working_set_mb=peak_working_set_mb())
        with open(os.path.join(a.out, "x1_per_frame.json"), "w") as f:
            json.dump(per_frame, f)
        rec["output_sha256"] = {"x1_tracks.jsonl.gz": sha256_path(tracks_path),
                                "x1_per_frame.json": sha256_path(os.path.join(a.out, "x1_per_frame.json"))}
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
        with open(os.path.join(a.out, "x1_export_record.json"), "w") as f:
            json.dump(rec, f, indent=2, default=str)
        print("X1 export:", rec["status"], "| failed:", rec["failed_criteria"], "| reasons:", rec["reasons"][:5], flush=True)
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
