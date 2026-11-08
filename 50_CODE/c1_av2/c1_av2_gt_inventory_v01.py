#!/usr/bin/env python3
"""The C1 ground-truth inventory (Claude line, c1_av2_gt_inventory_v01, 5 Nov 2026; D16 v26 Choice 47b, v28 Choice 49b; R20 B2, N3).
A bound, outcome-free builder. The lead expands its "files" into c1_quarantine_v03 --gt-inventory (or --extra), and c1_freeze_v07
binds it as data:gt_inventory and refuses any plain file carrying one of its hashes. Built from code, file names, sizes, dates and
SHA-256 only: no listed file is opened except to hash it, and archives are listed by MEMBER NAMES only (tar headers), never extracted.
THE RULE (Choice 49b, a content rule; producers only find candidates). A file is a ground-truth file if it holds any per-object AV2
annotation position, box, size, yaw or velocity, at any frame, of ANY AV2 log (training logs included), including quantities derived
per object from them (e.g. per-item p0) and archive members. Not ground truth: identity-only data (track ids, existence and point
counts, as in the stage-A caches and the K8 count items), ego poses, and purely aggregate files (AP, metric and count tables).
How the candidates were found: by tracing, in the code, every tool under 50_CODE (av2, qcnet, owndet, x1, k8, c1_av2) that reads
annotations.feather, a prepared ground-truth table, an infos pickle or a detection-evaluation table, and every file it writes; then a
name sweep. Each rule records the content class and the producing code line that decides it ("deciding_code").
Classes: "ground truth" (listed in "files", quarantined); "identity only", "ego poses", "aggregate" (listed under
"checked_not_listed" with the reason).
Pending: the port's 375-log prepared ground truth (30_DATA/av2_trk_v02/) is listed by its expected path unless --include-port is given
(the lead gives it once the port has finished; the folder is otherwise not opened). With --include-port, every path of the port's
GT_FILES_FOR_QUARANTINE_v01.txt must be in "files", the port folder's own files (its list, its ego poses) are classified by PORT_RULES,
and the name sweep covers the port folder too.
Excluded areas (stated in the output): the public annotation folders 30_DATA/av2_val and 30_DATA/av2_train225 (conceded by the
claim), nuScenes data and nuScenes-derived folders (by name), 70_TESTS (fixtures from nuScenes or synthetic data), 50_CODE/env/,
folders whose names hold a banned word, and anything outside the workspace. A name sweep under 30_DATA and 60_RESULTS lists every other
file whose name contains "gt" or "infos", or that is an archive (.tar, .tgz, .zip, .7z) or a pickle (.pkl), and that no rule covers
("unclassified_name_matches"); the tool refuses if one exists.
Usage: <canmot310 python> -B c1_av2_gt_inventory_v01.py --out <json> [--extra-list <txt>] [--include-port]
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import tarfile

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANNED = ("restricted", "sealed", "do_not_open", "participant", "codex")
PORT = "30_DATA/av2_trk_v02"
QREC1 = "30_DATA/qcnet_av2_v01/env/code_qcnet_sha256_at_finish.txt"
QREC2 = "30_DATA/qcnet_av2_v02/env/code_qcnet_sha256_rerun.txt"
OREC = "30_DATA/av2_det_owncp_v01/env/code_owndet_sha256.txt"
SPLIT = "50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json"
GT = "ground truth"

RULES = [
    # ---- ground truth (listed, quarantined)
    {"glob": "30_DATA/av2_trk_v01/gt/*", "class": GT, "producer": "50_CODE/av2/av2_gt_prep_v01.py",
     "deciding_code": "av2_gt_prep_v01.py l. 153 (json.dump of the table built from annotations.feather)",
     "writes": "the prepared ground-truth table: every annotated box per 2 Hz sample, with its city position, size and yaw"},
    {"glob": "30_DATA/av2_det_v01/lt3d_centerpoint/*_gt_v01.feather", "class": GT, "producer": "50_CODE/av2/pod/pod_lt3d_export_v01.py",
     "deciding_code": "pod_lt3d_export_v01.py l. 56 (gts.to_feather: LT3D format_results' ground-truth boxes)",
     "writes": "the ground-truth boxes of the 150 validation logs for the detection AP check"},
    {"glob": "30_DATA/av2_det_owncp_v01/*/*_gt_v01.feather", "class": GT, "producer": "50_CODE/owndet/pod/pod_owndet_export_v01.py",
     "runtime_record": OREC, "deciding_code": "pod_owndet_export_v01.py l. 85 (gts.to_feather)",
     "writes": "the ground-truth boxes of the 150 validation or 225 held-out logs for the detection AP check"},
    {"glob": "30_DATA/qcnet_av2_v01/qcnet_av2_gt_v01.npz", "class": GT, "producer": "50_CODE/qcnet/pod/qcnet_av2_infer_v01.py",
     "runtime_record": QREC1, "deciding_code": "qcnet_av2_infer_v01.py l. 311 (res['p0'] = the input position at the origin; --source gt)",
     "writes": "per item p0 = the annotation centre at every 2 Hz origin: a per-object position, after k for the decision at k (R20 B2)"},
    {"glob": "30_DATA/qcnet_av2_v02/qcnet_av2_gt_recentred_v02.npz", "class": GT, "producer": "50_CODE/qcnet/pod/qcnet_av2_infer_v03.py",
     "runtime_record": QREC2, "deciding_code": "qcnet_av2_infer_v03.py l. 236-250 (res['p0'] = res['p0_local'] + o; --source gt, "
                                               "pod_qcnet2_master_v02.sh l. 84-89)",
     "writes": "per item p0 = the annotation centre at every origin (R20 B2)"},
    {"glob": "30_DATA/av2_det_owncp_v01/train_progress/infos_archive_v01b.tar", "class": GT, "archive": True,
     "producer": "50_CODE/owndet/pod/pod_owndet_full_v02.sh (tar -cf, l. 66-67) of pod_owndet_prep_v02.py's outputs",
     "deciding_code": "pod_owndet_prep_v02.py l. 6-9 (infos: LT3D generate_info per log, with the annotation boxes; gtdb: "
                      "GTDatabaseCreater on av2_infos_train475.pkl: per-object points and boxes)",
     "writes": "an uncompressed tar of LT3D infos (annotation boxes) and the ground-truth database (per-object points, boxes in "
               "av2_dbinfos_train.pkl); see archive_members: by its member names it holds the 475 TRAINING logs only"},
    # ---- read ground truth, output not ground truth by the content rule (not listed)
    {"glob": "30_DATA/qcnet_av2_v01/bscheck_gt.json", "class": "aggregate", "producer": "50_CODE/qcnet/pod/qcnet_av2_infer_v01.py",
     "runtime_record": QREC1, "deciding_code": "qcnet_av2_infer_v01.py l. 375-384 (max |batch 1 - batch B| of loc, scale, pi, v2_cov)",
     "writes": "output-against-output differences on one log, its id, item count and batch size"},
    {"glob": "30_DATA/qcnet_av2_v0[12]/qcnet_av2_gt*_summary.json", "class": "aggregate", "producer": "50_CODE/qcnet/pod/qcnet_av2_infer_v0[13].py",
     "deciding_code": "qcnet_av2_infer_v01.py l. 343 / v02 l. 250 (json.dump of the merge totals)", "writes": "item and log totals"},
    {"glob": "30_DATA/qcnet_av2_v01/join2hz_t[13]_v01*", "class": "identity only", "producer": "50_CODE/qcnet/pod/pod_join2hz_v01.py",
     "runtime_record": QREC1, "deciding_code": "pod_join2hz_v01.py l. 80-83 (json of coverage counts; npz of sample token, instance token, "
                                               "group, in-path flag, k, horizon status)",
     "writes": "keys, identity and existence flags, coverage counts; no position"},
    {"glob": "30_DATA/qcnet_av2_v0[123]/qcnet_av2_counts_v0*.json", "class": "aggregate", "producer": "50_CODE/qcnet/pod/pod_qcnet_pack_v0[123].py",
     "deciding_code": "pod_qcnet_pack_v01.py l. 110 (json.dump of counts)", "writes": "counts, distributions, join coverage, finiteness"},
    {"glob": "30_DATA/av2_cache_stageA_v01/cache_*/**/*", "class": "identity only", "producer": "50_CODE/av2/av2_cache_stageA_v01.py",
     "deciding_code": "av2_cache_stageA_v01.py l. 9 and 63-65 (gt_x, gt_y, gt_yaw, gt_w, gt_l NaN-filled; existence, visibility, points)",
     "writes": "stage-A caches: tracker records, existence and visibility flags, point counts; no annotation position"},
    {"glob": "30_DATA/av2_cache_stageA_v01/items/*", "class": "identity only", "producer": "50_CODE/k8/k8_items_v04.py --counts-only",
     "deciding_code": "counts-only items: error fields NaN (AV2_TRACKER_COUNTS_v02.json outcome_statement)", "writes": "K8 count items"},
    {"glob": "30_DATA/av2_cache_stageA_v01/horizon8_*", "class": "identity only", "producer": "50_CODE/av2/av2_horizon_prep_v01.py --propagate-only",
     "deciding_code": "av2_horizon_prep_v01.py propagate(): tracker output only", "writes": "the trackers' own 2 s propagation"},
    {"glob": "30_DATA/av2_cache_stageA_v01/av2_ego10hz_v01.json.gz", "class": "ego poses", "producer": "50_CODE/av2/av2_ego_prep_v01.py",
     "deciding_code": "av2_ego_prep_v01.py docstring and output: {log: t, x, y, yaw} of city_SE3_egovehicle", "writes": "logged ego poses"},
    {"glob": "30_DATA/av2_cache_stageA_v01/logs/*", "class": "aggregate", "producer": "stage-A run logs", "deciding_code": "run logs",
     "writes": "progress lines"},
    {"glob": "60_RESULTS/av2_trk/metrics/*", "class": "aggregate", "producer": "50_CODE/av2/av2_track_metrics_v03.py",
     "deciding_code": "av2_track_metrics_v03.py l. 446 (json.dump of per-class metrics)", "writes": "aggregate tracking metrics (Rule 0)"},
    {"glob": "60_RESULTS/av2_trk/hota/**/*", "class": "aggregate", "producer": "50_CODE/av2/av2_hota_v03.py (TrackEval)",
     "deciding_code": "av2_hota_v03.py l. 140 (json.dump); TrackEval's per-sequence summaries and plots", "writes": "HOTA per class"},
    {"glob": "60_RESULTS/av2_trk/c1_375/**/*", "class": "aggregate", "producer": "50_CODE/av2/av2_track_metrics_v04.py, av2_hota_v04.py, av2_c1_frame_check_v01.py",
     "deciding_code": "metric and check summaries; equivalence records (hashes only)", "writes": "aggregates and hashes"},
    {"glob": "60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v0[12].json", "class": "aggregate", "producer": "50_CODE/av2/av2_counts_v0[12].py",
     "deciding_code": "av2_counts_v02.py l. 131 (json.dump of counts)", "writes": "counts"},
    {"glob": "30_DATA/av2_det*/**/*_ap_*", "class": "aggregate", "producer": "the AP steps of pod_lt3d_export_v01 / pod_owndet_export_v01",
     "deciding_code": "AP tables", "writes": "average precision per category"},
    {"glob": "30_DATA/av2_det_owncp_v01/**/*infos*_summary.json", "class": "aggregate", "producer": "50_CODE/owndet/pod/pod_owndet_prep_v0[12].py",
     "deciding_code": "infos summaries: counts", "writes": "counts of frames and boxes"},
]
PENDING = [
    {"expected_path": PORT + "/gt/av2_c1_gt375_v01.json", "class": GT, "producer": "50_CODE/av2/av2_gt_prep_v02.py",
     "deciding_code": "av2_gt_prep_v02.py (v01's table for the 375 logs; port design v04 section 8)",
     "writes": "the one 375-unit prepared ground-truth table"},
]
PORT_RULES = [   # only with --include-port
    {"glob": PORT + "/GT_FILES_FOR_QUARANTINE_v01.txt", "class": "aggregate", "producer": "50_CODE/av2/av2_c1_gt_list_v01.py",
     "deciding_code": "av2_c1_gt_list_v01.py (writes '<sha256>  <path>' lines)", "writes": "the port's list of ground-truth file paths and hashes"},
    {"glob": PORT + "/ego/*", "class": "ego poses", "producer": "50_CODE/av2/av2_ego_prep_v02.py",
     "deciding_code": "av2_ego_prep_v02.py docstring and output: {log: t, x, y, yaw} of city_SE3_egovehicle", "writes": "logged ego poses of the 375 logs"},
]
EXCLUDED = ["30_DATA/av2_val (public AV2 annotations of the 150 validation logs; conceded by the claim)",
            "30_DATA/av2_train225 (public AV2 annotations of the 225 held-out logs; conceded by the claim)",
            "30_DATA/nuscenes, nuscenes_mini_meta, scenarionet_mini, x1_gt, x2_gt, tpp_v01, k6, k7, detectors (nuScenes CenterPoint "
            "infos, named infos_*_10sweeps_withvelo), det_subsets_*, det_stream_equiv_val, canmot_* (nuScenes; not AV2)",
            "70_TESTS (fixtures built from nuScenes or synthetic data)",
            "50_CODE/env/ and folders whose names hold a banned word (not opened)",
            "anything outside the workspace: pods (no network volume was used; pod volumes are deleted with the pod) and other folders"]
SWEEP_ROOTS = ("30_DATA", "60_RESULTS")
SWEEP_EXCLUDE = ("30_DATA/av2_val", "30_DATA/av2_train225", "30_DATA/nuscenes", "30_DATA/nuscenes_mini_meta", "30_DATA/scenarionet_mini",
                 "30_DATA/x1_gt", "30_DATA/x2_gt", "30_DATA/tpp_v01", "30_DATA/k6", "30_DATA/k7", "30_DATA/detectors", "30_DATA/det_subsets",
                 "30_DATA/det_stream_equiv_val", "30_DATA/canmot", "60_RESULTS/tpp_v01", PORT)
SWEEP_SUFFIX = (".tar", ".tgz", ".zip", ".7z", ".pkl")


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace(os.sep, "/")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def utc(p):
    return datetime.datetime.utcfromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%dT%H:%M:%SZ")


def expand(pattern):
    out = []
    for p in glob.glob(os.path.join(W, pattern), recursive=True):
        if any(w in rel(p).lower() for w in BANNED) or not os.path.isfile(p):
            continue
        out.append(p)
    return sorted(out)


def runtime_hash(record, script):
    if not record or not os.path.exists(os.path.join(W, record)):
        return None
    for ln in open(os.path.join(W, record)).read().splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[-1].replace("*", "").endswith(os.path.basename(script)):
            return parts[0]
    return None


def producer_record(rule):
    pr = rule["producer"]
    rec = {"producer": pr}
    if pr.endswith(".py") and "," not in pr and "[" not in pr and os.path.exists(os.path.join(W, pr)):
        rec["producer_sha256_now"] = sha(os.path.join(W, pr))
        rh = runtime_hash(rule.get("runtime_record"), pr)
        if rh:
            rec["producer_sha256_recorded_at_run"] = rh
            rec["runtime_record"] = rule["runtime_record"]
            rec["recorded_equals_now"] = rh == rec["producer_sha256_now"]
    return rec


def confirmation_logs():
    logs = set()
    sp = os.path.join(W, SPLIT)
    if os.path.exists(sp):
        logs |= set(json.load(open(sp)).get("held_out_225") or [])
    val = os.path.join(W, "30_DATA", "av2_val")
    if os.path.isdir(val):
        logs |= {d for d in os.listdir(val) if os.path.isdir(os.path.join(val, d))}
    return logs


def archive_members(p):
    """Member NAMES of an archive (tar headers only; nothing is extracted)."""
    names = []
    with tarfile.open(p, "r:") as t:
        for m in t:
            names.append((m.name, int(m.size), bool(m.isdir())))
    conf = confirmation_logs()
    db = [n for n, _, d in names if "/av2_gt_database/" in n and not d]
    prefixes = sorted({os.path.basename(n).split("_")[0] for n in db})
    other = [n for n, _, _ in names if "/av2_gt_database/" not in n]
    return {"members": len(names), "names_outside_gt_database": other, "gt_database_files": len(db),
            "gt_database_log_prefixes": len(prefixes), "confirmation_logs_known": len(conf),
            "gt_database_logs_among_the_375": sorted(set(prefixes) & conf),
            "infos_of_the_375_present": [n for n in other if "held225" in n or "val150" in n],
            "listing": "member names from the tar headers only; never extracted"}


def name_sweep(covered, include_port=False):
    out = []
    excl = tuple(x for x in SWEEP_EXCLUDE if not (include_port and x == PORT))
    for root in SWEEP_ROOTS:
        for dp, dn, fn in os.walk(os.path.join(W, root)):
            r = rel(dp)
            dn[:] = [d for d in dn if not any(w in d.lower() for w in BANNED) and not any((r + "/" + d).startswith(x) for x in excl)]
            for f in fn:
                low = f.lower()
                if "gt" in low or "infos" in low or low.endswith(SWEEP_SUFFIX):
                    q = rel(os.path.join(dp, f))
                    if q not in covered and not q.endswith(".log"):
                        out.append(q)
    return sorted(out)


def build(include_port):
    files, nl, covered = [], [], set()
    for rule in RULES + (PORT_RULES if include_port else []):
        paths = expand(rule["glob"])
        covered |= {rel(p) for p in paths}
        base = {k: rule[k] for k in ("writes", "deciding_code")}
        if rule["class"] == GT:
            for p in paths:
                f = dict({"path": rel(p), "bytes": os.path.getsize(p), "sha256": sha(p), "date_utc": utc(p), "content_class": GT,
                          "rule": rule["glob"]}, **producer_record(rule), **base)
                if rule.get("archive"):
                    f["archive_members"] = archive_members(p)
                files.append(f)
        else:
            nl.append(dict({"rule": rule["glob"], "content_class": rule["class"], "files": len(paths), "names": [rel(p) for p in paths][:40]},
                           **producer_record(rule), **base))
    pending = []
    if include_port:
        for pd in PENDING:
            p = os.path.join(W, pd["expected_path"])
            assert os.path.isfile(p), "--include-port: %s does not exist" % pd["expected_path"]
            files.append(dict({"path": pd["expected_path"], "bytes": os.path.getsize(p), "sha256": sha(p), "date_utc": utc(p),
                               "content_class": GT, "rule": "port"}, **producer_record(pd), writes=pd["writes"], deciding_code=pd["deciding_code"]))
            covered.add(pd["expected_path"])
        lst = os.path.join(W, PORT, "GT_FILES_FOR_QUARANTINE_v01.txt")
        if os.path.exists(lst):
            listed = {f["path"] for f in files}
            for ln in open(lst).read().splitlines():
                # entry lines are "<sha256>  <path>"; a comment line counts only if it names a file as "already handled: <sha256>  <path>"
                body = ln.split("already handled:", 1)[1] if ln.lstrip().startswith("#") and "already handled:" in ln else \
                    ("" if ln.lstrip().startswith("#") else ln)
                cand = [x for x in body.split() if "/" in x or "\\" in x]
                if cand:
                    pth = cand[0].replace("\\", "/")
                    pth = rel(pth) if os.path.isabs(pth) else pth
                    assert pth in listed, "the port's GT_FILES_FOR_QUARANTINE_v01.txt names %s, which the inventory does not list" % pth
    else:
        pending = [dict(pd, status="pending: the port is running; listed with --include-port once it has finished") for pd in PENDING]
    unclassified = name_sweep(covered, include_port)
    return {"tool": "c1_av2_gt_inventory_v01", "tool_sha256": sha(os.path.abspath(__file__)),
            "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rule": "D16 v28 Choice 49b: a file is ground truth if it holds any per-object AV2 annotation position, box, size, yaw or "
                    "velocity at any frame of any AV2 log, derived per-object quantities and archive members included; identity-only "
                    "data, ego poses and aggregate files are not. Built from code, names and hashes only.",
            "files": sorted(files, key=lambda f: f["path"]), "pending": pending, "checked_not_listed": nl, "excluded_areas": EXCLUDED,
            "unclassified_name_matches": unclassified, "include_port": bool(include_port),
            "counts": {"files": len(files), "bytes": int(sum(f["bytes"] for f in files)), "pending": len(pending),
                       "checked_not_listed_rules": len(nl), "unclassified": len(unclassified)}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra-list", default=None)
    ap.add_argument("--include-port", action="store_true")
    a = ap.parse_args(argv)
    for p in (a.out, a.extra_list):
        assert not p or not os.path.exists(p), "%s exists: never overwritten" % p
    inv = build(a.include_port)
    assert not inv["unclassified_name_matches"], "files that no rule covers: %s" % inv["unclassified_name_matches"][:10]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".partial", "w", encoding="utf-8", newline="\n") as f:
        json.dump(inv, f, indent=1, sort_keys=True)
    os.replace(a.out + ".partial", a.out)
    if a.extra_list:
        with open(a.extra_list, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(x["path"] + "\n" for x in inv["files"]))
    print(json.dumps(inv["counts"]), sha(a.out))
    print("C1 GT INVENTORY V01 DONE")


if __name__ == "__main__":
    main()
