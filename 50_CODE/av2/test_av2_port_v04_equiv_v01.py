#!/usr/bin/env python3
"""test_av2_port_v04_equiv_v01 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md section 10): equivalence checks of the
v02 tools against the v01 (v04, v03) outputs on the 150 val logs with the public LT3D detections. Compares bytes / hashes /
parsed JSON of tracker outputs, adapter files, records and metric summaries; never opens a ground-truth file (GT outputs are
compared by SHA-256 in the driver, outside this script). Writes one JSON result per check.
Usage: python -I -B test_av2_port_v04_equiv_v01.py <check> [args] --out <json>
  common
  adapter  --test <dir> --ref <dir>
  export   --test <worker dir> --ref <worker dir>
  ab3dmot  --test <out dir> --ref <out dir> --worker i
  horizon_prefix --test <gz> --ref <gz> --n <lines>
  metrics  --test <json> --ref <json>      (per-class values)
  hota     --test <json> --ref <json>      (per-class values)
  gz       --test <gz> --ref <gz>          (decompressed SHA-256)
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v01 as C1  # noqa: E402
import av2_common_v02 as C2  # noqa: E402


def sha(p):
    return C2.sha256_path(p)


def gz_sha(p):
    h, n, lines = hashlib.sha256(), 0, 0
    with gzip.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
            lines += b.count(b"\n")
    return {"sha256": h.hexdigest(), "bytes": n, "lines": lines}


def drop(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def check_common():
    logs = sorted(d for d in os.listdir(C1.AV2_VAL) if os.path.isdir(os.path.join(C1.AV2_VAL, d)))
    bad = []
    for lg in logs:
        if os.path.normcase(C2.log_dir(lg)) != os.path.normcase(os.path.join(C1.AV2_VAL, lg)):
            bad.append((lg, "log_dir"))
        if C2.sweep_timestamps(lg) != C1.sweep_timestamps(lg):
            bad.append((lg, "sweep_timestamps"))
        if C2.frame_timestamps(lg) != C1.frame_timestamps(lg):
            bad.append((lg, "frame_timestamps"))
        if C2.sweep_timestamps_v01(lg) != C1.sweep_timestamps(lg):
            bad.append((lg, "sweep_timestamps_v01"))
    same_consts = all(getattr(C1, k) == getattr(C2, k) for k in ("W_ROOT", "AV2_VAL", "FRAME_STEP", "RANGE_SQUARE_M", "TRACKER_MAP",
                                                                 "ANALYSIS_GROUP", "ANALYSIS_GROUPS_D15", "RIDDEN", "RB_IOU", "CLASS_RANGE"))
    same_det = all(C1.DET_PATHS[k] == C2.DET_PATHS[k] and C1.DET_HAS_VELO[k] == C2.DET_HAS_VELO[k] for k in C1.DET_PATHS)
    return {"logs": len(logs), "mismatches": bad, "constants_equal": same_consts, "v01_detectors_equal": same_det,
            "identical": len(logs) == 150 and not bad and same_consts and same_det}


def check_adapter(test, ref):
    r = {"files": {}}
    ok = True
    a = sha(os.path.join(test, "first_tokens.json")) == sha(os.path.join(ref, "first_tokens.json"))
    r["files"]["first_tokens.json"] = {"bytes_identical": a}
    ok &= a
    rt, rr = json.load(open(os.path.join(test, "receipt.json"))), json.load(open(os.path.join(ref, "receipt.json")))
    for s_t, s_r in zip(rt["subsets"], rr["subsets"]):
        name = os.path.basename(s_t["path"])
        bt = open(os.path.join(test, name), "rb").read()
        old, new = b'"adapter": "av2_tracker_input_v02"', b'"adapter": "av2_tracker_input_v01"'
        n_sub = bt.count(old)
        bt2 = bt.replace(old, new)
        same = hashlib.sha256(bt2).hexdigest() == sha(os.path.join(ref, name))
        r["files"][name] = {"substitutions": n_sub, "bytes_identical_after_adapter_name_substitution": same,
                            "bytes_identical_raw": hashlib.sha256(bt).hexdigest() == sha(os.path.join(ref, name))}
        ok &= same and n_sub == 1
    vol = {"adapter", "source", "first_tokens", "subsets", "wall_seconds", "stats_per_source", "logs_file", "logs_file_sha256",
           "logs_per_part", "first_tokens_sha256"}
    eq_rest = json.loads(json.dumps(drop(rt, vol))) == json.loads(json.dumps(drop(rr, vol)))
    eq_sub = [drop(a_, {"path", "sha256"}) == drop(b_, {"path", "sha256"}) for a_, b_ in zip(rt["subsets"], rr["subsets"])]
    r["receipt_equal_except_paths_hashes_time_and_v02_keys"] = eq_rest and all(eq_sub) and len(rt["subsets"]) == len(rr["subsets"])
    r["receipt_first_tokens_sha256_equal"] = rt["first_tokens_sha256"] == rr["first_tokens_sha256"]
    ok &= r["receipt_equal_except_paths_hashes_time_and_v02_keys"] and r["receipt_first_tokens_sha256_equal"]
    r["identical"] = bool(ok)
    return r


def check_export(test, ref, expect_reused=-1):
    gt_, gr = gz_sha(os.path.join(test, "x1_tracks.jsonl.gz")), gz_sha(os.path.join(ref, "x1_tracks.jsonl.gz"))
    pf = sha(os.path.join(test, "x1_per_frame.json")) == sha(os.path.join(ref, "x1_per_frame.json"))
    rt, rr = json.load(open(os.path.join(test, "x1_export_record.json"))), json.load(open(os.path.join(ref, "x1_export_record.json")))
    st_keys = [k for k in rr["stats"] if k != "peak_working_set_mb"]
    stats_eq = all(rt["stats"].get(k) == rr["stats"][k] for k in st_keys)
    crit_eq = rt["criteria"] == rr["criteria"]
    other = {k: rt.get(k) == rr.get(k) for k in ("status", "status_X1_gates", "failed_criteria", "reasons", "dataset", "detector",
                                                  "meas_dim", "loader", "selection", "resolved_config")}
    r = {"tracks_decompressed": {"test": gt_, "ref": gr, "identical": gt_ == gr}, "per_frame_bytes_identical": pf,
         "record_stats_equal": stats_eq, "record_criteria_equal": crit_eq, "record_fields_equal": other,
         "test_checkpoint": rt.get("checkpoint", {}).get("logs_reused_from_checkpoints")}
    r["identical"] = gt_ == gr and pf and stats_eq and crit_eq and all(other.values())
    if expect_reused >= 0:   # the resume path: exactly this many logs were reused from checkpoints
        r["reused_as_expected"] = len(r["test_checkpoint"] or []) == expect_reused
        r["identical"] = r.pop("identical") and r["reused_as_expected"]   # kept as the last key
    return r


def check_ab3dmot(test, ref, worker, expect_reused=-1):
    r, ok = {}, True
    for v in ("det", "kf"):
        dt_, dr = os.path.join(test, "ab3dmot_" + v, "worker%d" % worker), os.path.join(ref, "ab3dmot_" + v, "worker%d" % worker)
        a, b = gz_sha(os.path.join(dt_, "x1_tracks.jsonl.gz")), gz_sha(os.path.join(dr, "x1_tracks.jsonl.gz"))
        pf = sha(os.path.join(dt_, "x1_per_frame.json")) == sha(os.path.join(dr, "x1_per_frame.json"))
        rt, rr = json.load(open(os.path.join(dt_, "x1_export_record.json"))), json.load(open(os.path.join(dr, "x1_export_record.json")))
        eq = {k: rt.get(k) == rr.get(k) for k in ("fast_association_shim_L2", "logs", "worker", "n_workers", "dataset", "detector",
                                                  "tracker", "resolved_config", "settings", "stats", "criteria", "status_X1_gates",
                                                  "shims", "lt3d_files_sha256")}
        r[v] = {"tracks_decompressed": {"test": a, "ref": b, "identical": a == b}, "per_frame_bytes_identical": pf, "record_fields_equal": eq,
                "test_checkpoint": rt.get("v05", {}).get("logs_reused_from_checkpoints")}
        ok &= a == b and pf and all(eq.values())
        if expect_reused >= 0:
            r[v]["reused_as_expected"] = len(r[v]["test_checkpoint"] or []) == expect_reused
            ok &= r[v]["reused_as_expected"]
    a = gz_sha(os.path.join(test, "horizon8_ab3dmot_kf_worker%d.jsonl.gz" % worker))
    b = gz_sha(os.path.join(ref, "horizon8_ab3dmot_kf_worker%d.jsonl.gz" % worker))
    r["horizon"] = {"test": a, "ref": b, "identical": a == b}
    ok &= a == b
    r["identical"] = bool(ok)
    return r


def check_horizon_prefix(test, ref, n):
    h_t, h_r = hashlib.sha256(), hashlib.sha256()
    nt = 0
    with gzip.open(test, "rb") as f:
        for line in f:
            h_t.update(line)
            nt += 1
    nr = 0
    with gzip.open(ref, "rb") as f:
        for line in f:
            if nr == n:
                break
            h_r.update(line)
            nr += 1
    return {"test_lines": nt, "ref_prefix_lines": nr, "n_expected": n, "test_sha256": h_t.hexdigest(), "ref_prefix_sha256": h_r.hexdigest(),
            "identical": nt == n and nr == n and h_t.hexdigest() == h_r.hexdigest()}


def _close(x, y, rtol):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        return x == y or abs(x - y) <= rtol * max(abs(x), abs(y))
    return json.dumps(x, sort_keys=True) == json.dumps(y, sort_keys=True)


def check_per_class(test, ref, rtol=0.0, control=None):
    """Exact comparison of every per-class value; with rtol > 0 also a relative-tolerance verdict, and with a control file
    (a rerun of the reference tool itself on the same inputs) the reference tool's own run-to-run differences."""
    t, r = json.load(open(test)), json.load(open(ref))
    if rtol > 0:
        out = {"exact": check_per_class(test, ref)}
        diffs = {c: {k: (t["per_class"][c].get(k), v) for k, v in (r["per_class"][c] or {}).items()
                     if not _close(t["per_class"][c].get(k), v, rtol)} for c in r["per_class"] if r["per_class"][c] is not None}
        out["rtol"] = rtol
        out["differences_beyond_rtol"] = {c: d for c, d in diffs.items() if d}
        if control:
            out["control_reference_rerun_vs_reference"] = check_per_class(control, ref)
            out["control_reference_rerun_vs_test"] = check_per_class(control, test)
        out["identical"] = not out["differences_beyond_rtol"] and all(
            (t["per_class"][c] is None) == (r["per_class"][c] is None) for c in r["per_class"])
        return out
    out = {"classes": {}, "identical": True}
    for c, vr in r["per_class"].items():
        vt = t["per_class"].get(c)
        if vr is None or vt is None:
            eq = vr is None and vt is None
            out["classes"][c] = {"equal": eq}
        else:
            diff = {k: (vt.get(k), vr[k]) for k in vr if json.dumps(vt.get(k), sort_keys=True) != json.dumps(vr[k], sort_keys=True)}
            eq = not diff
            out["classes"][c] = {"equal": eq, "keys": len(vr), "differences": diff}
        out["identical"] &= eq
    if "counts" in r:
        out["counts_equal"] = t.get("counts") == r["counts"]
        out["identical"] &= out["counts_equal"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("check")
    ap.add_argument("--test")
    ap.add_argument("--ref")
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--expect-reused", type=int, default=-1)
    ap.add_argument("--rtol", type=float, default=0.0, help="metrics/hota: relative tolerance verdict (exact result kept)")
    ap.add_argument("--control", default=None, help="metrics/hota: a rerun of the reference tool on the same inputs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.check == "common":
        r = check_common()
    elif a.check == "adapter":
        r = check_adapter(a.test, a.ref)
    elif a.check == "export":
        r = check_export(a.test, a.ref, a.expect_reused)
    elif a.check == "ab3dmot":
        r = check_ab3dmot(a.test, a.ref, a.worker, a.expect_reused)
    elif a.check == "horizon_prefix":
        r = check_horizon_prefix(a.test, a.ref, a.n)
    elif a.check in ("metrics", "hota"):
        r = check_per_class(a.test, a.ref, a.rtol, a.control)
    elif a.check == "gz":
        x, y = gz_sha(a.test), gz_sha(a.ref)
        r = {"test": x, "ref": y, "identical": x == y}
    else:
        raise SystemExit("unknown check")
    r = dict({"check": a.check, "test": os.path.abspath(a.test) if a.test else None, "ref": os.path.abspath(a.ref) if a.ref else None}, **r)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(r, open(a.out, "w"), indent=1, default=str)
    print(a.check, "identical:", r["identical"])


if __name__ == "__main__":
    sys.exit(main())
