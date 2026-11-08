#!/usr/bin/env python3
"""Provenance of the AV2 stage-A inputs (Claude line, c1_av2_provenance_v01, 5 Nov 2026; D16 v25 Choice 46d, v26 47a, v27 48b m-2).
A bound, outcome-free builder, run by the lead after stage A (and after the scene map) and before the GT inventory and the quarantine.
For every AV2 stage-A manifest given, every recorded input hash is followed to the tool that produced the file, and that tool's file
must be a BUILDER of the README given (its SHA-256 equal to the README's row with role "builder"). Refused otherwise; then nothing is
written (m-2), the exit code is non-zero, and the freeze (c1_freeze_v07) cannot bind a record.
  * the manifest itself: inputs.builder_sha256 must be a bound builder's hash (m-6);
  * tracker exports (inputs.workers, export_sha256): each worker's receipt x1_export_record.json must record the same output hash
    (output_sha256["x1_tracks.jsonl.gz"]) and name its tool (harness_version, and argv[0] where recorded), which must be a bound
    builder; for CANMOT/Poly-MOT exports the detection input's receipt (receipt.json beside provenance.detection_path) must name a
    bound adapter (receipt "adapter");
  * the horizon (horizon, horizon_sha256):
      - T1/T3 (CANMOT experiments): it is RE-MADE by the bound builder av2_horizon_prep_v02 --propagate-only on the manifest's workers
        (tracker output only), in a temporary folder outside the workspace, and the decompressed SHA-256 must be equal;
      - AB3DMOT (experiment lt3d/ab3dmot): it must be the concatenation, in worker order, of the workers' horizon8 files written by the
        bound AB3DMOT builder named in the receipts (where the receipt records their decompressed hash, it must match);
  * the ego file (ego, ego_sha256): RE-MADE by the bound builder av2_ego_prep_v02 --gt <the manifest's ground truth>; decompressed
    SHA-256 equal;
  * the prepared ground truth (gt, gt_sha256): RE-MADE by the bound builder av2_gt_prep_v02 (with --logs-file when the manifest's logs
    are not the 150 validation logs) into a temporary file outside the workspace, hashed and DELETED at once (never opened); equal;
  * scene.json, when the manifest records it: its hash must equal the recorded one.
A re-made file proves that a bound builder, on the bound inputs, writes exactly the recorded bytes; this is the "receipt" of the three
tools that write none. Run before the quarantine (the ego and ground-truth builders read the plain prepared files).
Output (only if every check passes): {"tool", "status": "PASS", "ok": true, "readme", "readme_sha256", "manifests": {path: {"sha256",
"inputs": {...}}}, "seconds"}; the freeze binds it as data:provenance and checks it (c1_guard_v06.provenance_record_check).
Usage: <canmot310 python> -B c1_av2_provenance_v01.py --readme README_C1_CODE_v09.md --stageA-manifests <MANIFEST.json ...>
         [--logs-file <C1_LOGS_375_v01.json>] --out <json>
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
HORIZON = "50_CODE/av2/av2_horizon_prep_v02.py"
EGO = "50_CODE/av2/av2_ego_prep_v02.py"
GT = "50_CODE/av2/av2_gt_prep_v02.py"
TOOL_DIRS = ("50_CODE/av2", "50_CODE/x1")
AB3DMOT_EXPERIMENT = "lt3d/ab3dmot"


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace(os.sep, "/")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def gz_sha(paths):
    """SHA-256 of the concatenated decompressed bytes of one or several gzip files."""
    h = hashlib.sha256()
    for p in paths:
        with gzip.open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def bound_builders(readme):
    rows = re.findall(r"^([0-9a-f]{64})  (50_CODE/\S+)  (\S+)$", open(readme, encoding="utf-8").read(), re.M)
    return {p: h for h, p, r in rows if r == "builder"}


def require_builder(path_rel, bound, what):
    p = os.path.join(W, path_rel)
    assert path_rel in bound, "%s: %s is not a bound builder of the README (Choice 46d)" % (what, path_rel)
    assert os.path.isfile(p) and sha(p) == bound[path_rel], "%s: %s differs from the README's hash" % (what, path_rel)
    return {"tool": path_rel, "sha256": bound[path_rel]}


def tool_file(name):
    name = re.split(r"[\s(:]", (name or "").strip())[0]
    for d in TOOL_DIRS:
        if os.path.isfile(os.path.join(W, d, name + ".py")):
            return "%s/%s.py" % (d, name)
    return "%s/%s.py" % (TOOL_DIRS[0], name or "(unnamed)")


def export_check(worker, recorded_sha, bound):
    rp = os.path.join(worker, "x1_export_record.json")
    assert os.path.isfile(rp), "tracker export %s has no receipt x1_export_record.json" % rel(worker)
    rec = json.load(open(rp))
    out = (rec.get("output_sha256") or {}).get("x1_tracks.jsonl.gz")
    assert out == recorded_sha == sha(os.path.join(worker, "x1_tracks.jsonl.gz")), \
        "tracker export %s: the receipt, the manifest and the file disagree on x1_tracks.jsonl.gz's hash" % rel(worker)
    tool = tool_file(rec.get("harness_version") or rec.get("harness"))
    argv0 = (rec.get("argv") or [None])[0]
    if argv0:
        assert os.path.basename(argv0) == os.path.basename(tool), "tracker export %s: argv names %s, the harness %s" % (rel(worker), argv0, tool)
    r = {"worker": rel(worker), "x1_tracks_sha256": out, "producer": require_builder(tool, bound, "tracker export " + rel(worker)),
         "experiment": (rec.get("resolved_config") or {}).get("experiment_id"), "record_worker": rec.get("worker")}
    det = (rec.get("provenance") or {}).get("detection_path")
    if det:
        rc = os.path.join(os.path.dirname(det), "receipt.json")
        assert os.path.isfile(rc), "tracker export %s: its detection input has no receipt %s" % (rel(worker), rc)
        r["detection_adapter"] = require_builder(tool_file(json.load(open(rc)).get("adapter")), bound, "detection input of " + rel(worker))
    if rec.get("v05"):
        r["horizon8_file"], r["horizon8_decompressed_sha256"] = rec["v05"].get("horizon8_file"), rec["v05"].get("horizon8_decompressed_sha256")
    return r


def run_tool(tool_rel, args, tmpd, bound, what):
    rec = require_builder(tool_rel, bound, what)
    t0 = time.time()
    r = subprocess.run([PY, "-I", "-B", os.path.join(W, tool_rel)] + args, capture_output=True, text=True, cwd=tmpd)
    assert r.returncode == 0, "%s: the bound builder %s failed: %s" % (what, tool_rel, (r.stdout + r.stderr)[-600:])
    return dict(rec, seconds=round(time.time() - t0, 1))


def default_runner(kind, m, bound, tmpd, logs_file):
    """Re-makes one input with its bound builder in tmpd (outside the workspace); returns (path, producer record)."""
    i = m["inputs"]
    if kind == "horizon":
        out = os.path.join(tmpd, "horizon.jsonl.gz")
        args = ["--experiment", m["experiment"], "--workers"] + list(i["workers"]) + ["--out", out, "--propagate-only", "--allow-av2-propagation"]
        return out, run_tool(HORIZON, args, tmpd, bound, "horizon")
    if kind == "ego":
        out = os.path.join(tmpd, "ego.json.gz")
        return out, run_tool(EGO, ["--gt", i["gt"], "--out", out], tmpd, bound, "ego")
    if kind == "gt":
        out = os.path.join(tmpd, "gt.json")
        logs = sorted({str((v or {}).get("log", u)) if isinstance(v, dict) else str(u) for u, v in (m.get("scenes") or {}).items()})
        args = ["--out", out]
        if len(logs) != 150:
            assert logs_file, "the manifest's logs are not the 150 validation logs: --logs-file is required to re-make its ground truth"
            args += ["--logs-file", logs_file]
        return out, run_tool(GT, args, tmpd, bound, "ground truth")
    raise ValueError(kind)


def check_manifest(mp, bound, logs_file=None, runner=default_runner, kinds=("exports", "horizon", "ego", "gt", "scene_json")):
    m = json.load(open(mp))
    assert m.get("stage", "A") == "A" and str(m.get("dataset", "")).startswith("av2"), "%s is not an AV2 stage-A manifest" % rel(mp)
    i = m.get("inputs") or {}
    bh = i.get("builder_sha256")
    assert bh, "stage-A manifest %s records no builder_sha256 (Choice 48b m-6)" % rel(mp)
    names = [p for p, h in bound.items() if h == bh]
    assert names, "stage-A manifest %s was built by %s..., not a bound builder" % (rel(mp), bh[:12])
    res = {"sha256": sha(mp), "builder": names[0], "inputs": {}}
    exps = []
    if "exports" in kinds:
        assert len(i["workers"]) == len(i["export_sha256"]) and i["workers"], "%s: workers and export hashes disagree" % rel(mp)
        exps = [export_check(w, h, bound) for w, h in zip(i["workers"], i["export_sha256"])]
        res["inputs"]["exports"] = exps
    tmp_root = tempfile.mkdtemp(prefix="c1_prov_")
    assert not os.path.abspath(tmp_root).startswith(os.path.abspath(W)), "the temporary folder must lie outside the workspace"
    try:
        if "horizon" in kinds:
            assert sha(i["horizon"]) == i["horizon_sha256"], "%s: the horizon file differs from the manifest's hash" % rel(mp)
            want = gz_sha([i["horizon"]])
            if m.get("experiment") == AB3DMOT_EXPERIMENT:
                assert exps, "AB3DMOT horizon: the exports must be checked first"
                parts = []
                for e in sorted(exps, key=lambda x: int(x["record_worker"])):
                    w = os.path.join(W, e["worker"])
                    hz = os.path.join(os.path.dirname(os.path.dirname(w)), "horizon8_ab3dmot_kf_worker%d.jsonl.gz" % int(e["record_worker"]))
                    assert os.path.isfile(hz), "AB3DMOT horizon: the worker file %s is missing" % rel(hz)
                    if e.get("horizon8_decompressed_sha256"):
                        assert gz_sha([hz]) == e["horizon8_decompressed_sha256"], "AB3DMOT horizon: %s differs from its receipt" % rel(hz)
                    parts.append(hz)
                got = gz_sha(parts)
                assert got == want, "%s: the horizon is not the worker-order concatenation of the bound AB3DMOT builder's files" % rel(mp)
                res["inputs"]["horizon"] = {"sha256": i["horizon_sha256"], "decompressed_sha256": want, "method": "concatenation of the "
                                            "AB3DMOT workers' horizon8 files", "producer": exps[0]["producer"], "parts": [rel(p) for p in parts]}
            else:
                d = tempfile.mkdtemp(dir=tmp_root)
                out, prod = runner("horizon", m, bound, d, logs_file)
                got = gz_sha([out])
                assert got == want, "%s: the horizon is not what the bound builder %s makes from the bound exports" % (rel(mp), prod["tool"])
                res["inputs"]["horizon"] = {"sha256": i["horizon_sha256"], "decompressed_sha256": want, "method": "re-made", "producer": prod}
        if "ego" in kinds:
            assert sha(i["ego"]) == i["ego_sha256"], "%s: the ego file differs from the manifest's hash" % rel(mp)
            d = tempfile.mkdtemp(dir=tmp_root)
            out, prod = runner("ego", m, bound, d, logs_file)
            assert gz_sha([out]) == gz_sha([i["ego"]]), "%s: the ego file is not what the bound builder %s makes" % (rel(mp), prod["tool"])
            res["inputs"]["ego"] = {"sha256": i["ego_sha256"], "method": "re-made", "producer": prod}
        if "gt" in kinds:
            assert sha(i["gt"]) == i["gt_sha256"], "%s: the ground-truth file differs from the manifest's hash" % rel(mp)
            d = tempfile.mkdtemp(dir=tmp_root)
            out, prod = runner("gt", m, bound, d, logs_file)
            got = sha(out)
            os.remove(out)
            assert got == i["gt_sha256"], "%s: the ground truth is not what the bound builder %s makes" % (rel(mp), prod["tool"])
            res["inputs"]["gt"] = {"sha256": i["gt_sha256"], "method": "re-made, hashed, deleted unopened", "producer": prod}
        if "scene_json" in kinds and i.get("scene_json"):
            assert sha(i["scene_json"]) == i["scene_json_sha256"], "%s: scene.json differs from the manifest's hash" % rel(mp)
            res["inputs"]["scene_json"] = {"sha256": i["scene_json_sha256"], "method": "hash"}
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    return res


def run(manifests, readme, logs_file=None, runner=default_runner, kinds=("exports", "horizon", "ego", "gt", "scene_json")):
    t0 = time.time()
    bound = bound_builders(readme)
    assert bound, "the README binds no builder"
    out = {}
    for mp in manifests:
        out[rel(mp)] = check_manifest(mp, bound, logs_file, runner, kinds)
    return {"tool": "c1_av2_provenance_v01", "tool_sha256": sha(os.path.abspath(__file__)), "status": "PASS", "ok": True,
            "readme": rel(readme), "readme_sha256": sha(readme), "logs_file": rel(logs_file) if logs_file else None,
            "logs_file_sha256": sha(logs_file) if logs_file else None, "manifests": out, "kinds": list(kinds),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": round(time.time() - t0, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--readme", required=True)
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--logs-file", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    assert not os.path.exists(a.out), "%s exists: never overwritten" % a.out
    rec = run([os.path.abspath(p) for p in a.stageA_manifests], os.path.abspath(a.readme), a.logs_file)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".partial"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, sort_keys=True)
    os.replace(tmp, a.out)
    print(json.dumps({"status": "PASS", "manifests": len(rec["manifests"]), "seconds": rec["seconds"]}), sha(a.out))
    print("C1 AV2 PROVENANCE V01 PASS")


if __name__ == "__main__":
    main()
