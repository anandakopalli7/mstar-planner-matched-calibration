#!/usr/bin/env python3
"""C1 rehearsal v08 (Claude line, c1_rehearsal_v08, 5 Nov 2026) = c1_rehearsal_v07 (kept, unchanged) with the lead's criteria decision of
5 Nov 2026 in README v09 (c1_rules_v01, c1_analyse_v09 with the criteria, c1_predarm_v07): the mock plan MOCK_C1_PLAN_v08.md, the
predictor arm c1_predarm_v07, the outputs *_v08. Everything else is v07's.

C1 rehearsal v07 (Claude line, c1_rehearsal_v07, 5 Nov 2026) = c1_rehearsal_v06 (kept, unchanged) on README v09's code (D16 v26
Choice 47, v27 Choice 48, v28 Choice 49): c1_freeze_v07, c1_analyse_v09 and test_c1_v12; the mock plan MOCK_C1_PLAN_v07.md; the
Choice 41(a) block check on a copy of the NEWEST plan draft (40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07e_DRAFT.md if it exists, else
v07d, v07c, v07b, v06). Everything else is v06's: the whole confirmatory path once, end to end, with nuScenes stand-in data. Never AV2;
never 40_PROTOCOL/C1_PLAN_HASH_LOG.txt (its own log in --out, accepted only because every unit is a nuScenes scene); no deposit record,
stage-B log, run log or quarantine is made (nuScenes is exempt; the AV2 data roles of Choice 47(j) are required only on AV2 folds).
Resumable (steps.jsonl; finished steps are skipped).
Steps: (1) folds and the two children; a mock split; (2) E0 before the freeze (c1_e0_v05); (3) the config with "h8_units": "folds",
"h9_label": "secondary" (Choice 47c: explicit; v08: "descriptive", D16 v33 Choice 52b) and no "q1"; (4) the mock plan; (5) c1_freeze_v07 (README v09's files with roles; it
runs test_c1_v12 and writes the five blocks); (5b) Choice 41(a): the newest draft's own blocks filled by c1_freeze_v07 into a separate
log, each exactly once; (6)-(10) fits, transfer, runs, method stage, H8, predictor arm, tab as v06; (11) c1_analyse_v09 --c1; (12)
test_c1_v12 --rehearsal (its REHEARSAL group compares this decision with rehearsal150_v08's).
Usage (from 50_CODE/c1_av2): <canmot310 python> -B c1_rehearsal_v08.py --out <dir> [--workers 2] [--readme README_C1_CODE_v09.md]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(C1))
PY = sys.executable
MOCK_PLAN = """# MOCK C1 plan for the rehearsal v08 (not the C1 plan; nuScenes stand-in data only)

This file exists only to rehearse the confirmatory path on README v09's code (D16 v13 Choices 33-35, v16 Choice 37, v17 Choice 38,
v18 Choice 39, v20 Choice 41, v21 Choice 42, v23 Choice 44, v24 Choice 45, v26 Choice 47, v27 Choice 48, v28 Choice 49, and the lead's
criteria decision of 5 Nov 2026). It is frozen
into a rehearsal hash log in its own directory, never into 40_PROTOCOL/C1_PLAN_HASH_LOG.txt.

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END

FROZEN_ROLES_BEGIN
FROZEN_ROLES_END
"""
DRAFTS = [os.path.join(W, "40_PROTOCOL", "C1_AV2_CONFIRMATORY_PREREG_%s_DRAFT.md" % v) for v in ("v07e", "v07d", "v07c", "v07b", "v06")]
DRAFT = [p for p in DRAFTS if os.path.exists(p)][0]
BLOCKS = ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS")
STEPS = None
VAL_T1 = [os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker%d" % i) for i in range(3)]
VAL_T3 = [os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "val", "worker%d" % i) for i in range(3)]
GT = os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json")
META = os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval")
HOR = {"t1": os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"),
       "t3": os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "horizon_val_v03.jsonl.gz")}
EXPORTS = {"t1": VAL_T1, "t3": VAL_T3}
EXPERIMENT = {"t1": "paper/local/canmot/sc", "t3": "paper/baseline/poly_mot"}
TPP = os.path.join(W, "30_DATA", "tpp_v01")
TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
MS_TEST = ["--test", "--reps", "1", "--boot", "40", "--refit-boot", "3", "--e2-boot", "3"]
DATA_OF = {"t1": "t1", "t3": "t3", "tab": "t1"}


def _done():
    if not (STEPS and os.path.exists(STEPS)):
        return set()
    return {r["key"] for r in (json.loads(l) for l in open(STEPS) if l.strip()) if r.get("event") == "end" and r.get("exit") == 0}


def _log_step(rec):
    with open(STEPS, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


def run(cmd, log):
    key = " ".join(cmd)
    if key in _done():
        with open(log, "a") as f:
            f.write("$ %s\n[skipped: done in an earlier attempt]\n" % key)
        return ""
    _log_step({"key": key, "event": "start", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    t0 = time.time()
    r = subprocess.run([PY, "-B"] + cmd, capture_output=True, text=True, cwd=C1)
    with open(log, "a") as f:
        f.write("$ %s\n%s\n%s\n[exit %d, %.0f s]\n" % (key, r.stdout[-4000:], r.stderr[-4000:], r.returncode, time.time() - t0))
        f.flush()
    _log_step({"key": key, "event": "end", "exit": r.returncode, "seconds": round(time.time() - t0, 1),
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    assert r.returncode == 0, "step failed: %s\n%s" % (" ".join(cmd[:2]), (r.stdout + r.stderr)[-2500:])
    return r.stdout


def probe_readme(readme, out):
    """README v09's rows with the bound test replaced by freeze_probe_pass_v01 (for the Choice 41(a) block check only)."""
    txt = open(readme, encoding="utf-8").read()
    rows = re.findall(r"^([0-9a-f]{64})  (\S+)  (\S+)$", txt, re.M)
    probe = "50_CODE/c1_av2/tests/freeze_probe_pass_v01.py"
    lines = ["%s  %s  %s" % (h, p, ("test_module" if r == "test" else r)) for h, p, r in rows if p != probe]
    ph = [h for h, p, _ in rows if p == probe]
    assert ph, "freeze_probe_pass_v01 is not bound by %s" % readme
    lines.append("%s  %s  test" % (ph[0], probe))
    lines += ["superseded  %s" % s for s in re.findall(r"^superseded  (50_CODE/\S+)$", txt, re.M)]
    if not os.path.exists(out):
        open(out, "w", encoding="utf-8", newline="\n").write("# probe README for the rehearsal's Choice 41(a) block check (not a code README)\n\n```\n"
                                                           + "\n".join(lines) + "\n```\n")
    return out


def draft_copy(out):
    """The newest plan draft with its slots replaced by rehearsal stand-in text (never a value of the plan)."""
    if os.path.exists(out):
        return out
    txt = open(DRAFT, encoding="utf-8").read()
    txt2, n = re.subn(r"\[\s*SLOT\s*:\s*([^\]]*)\]", lambda m: "(rehearsal stand-in text, not a value: %s)" % m.group(1), txt)
    assert n >= 5, n
    sys.path.insert(0, C1)
    import c1_guard_v03 as G3  # the slot pattern c1_freeze_v03's check uses
    assert not G3.SLOT.search(txt2), "a slot remains in the draft copy"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt2)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--readme", default=os.path.join(C1, "README_C1_CODE_v09.md"))
    a = ap.parse_args(argv)
    O = os.path.abspath(a.out)
    os.makedirs(O, exist_ok=True)
    log = os.path.join(O, "rehearsal.log")
    global STEPS
    STEPS = os.path.join(O, "steps.jsonl")
    hlog = os.path.join(O, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    plan = os.path.join(O, "MOCK_C1_PLAN_v08.md")
    folds, v150, t225 = (os.path.join(O, x) for x in ("folds.json", "folds_val150.json", "folds_train225.json"))
    units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
    import numpy as np
    for t in ("t1", "t3"):
        assert sorted(str(x) for x in np.load(os.path.join(TPP, "keys_%s_val_v01.npz" % t), allow_pickle=False)["scene_names"]) == units
    up = os.path.join(O, "units.txt")
    if not os.path.exists(up):
        open(up, "w").write("\n".join("%s %s" % (u, "held_out_train" if i < 60 else "val") for i, u in enumerate(units)) + "\n")
    run(["c1_folds_v03.py", "--logs", up, "--out", folds, "--dataset", "nuscenes", "--label", "C1 REHEARSAL v08 (nuScenes stand-in, 150 validation scenes)"], log)
    run(["c1_folds_v03.py", "--restrict-from", folds, "--source", "val", "--out", v150], log)
    run(["c1_folds_v03.py", "--restrict-from", folds, "--source", "held_out_train", "--out", t225], log)
    split = os.path.join(O, "mock_split.json")
    if not os.path.exists(split):
        json.dump({"rule": "mock split for the rehearsal", "units": units}, open(split, "w"), indent=1)
    e0_out = os.path.join(O, "e0_prefreeze_nuscenes_t1.json")
    run(["c1_e0_v05.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--out", e0_out, "--mode", "c1", "--seed", "20261114"], log)
    e0 = json.load(open(e0_out))
    e0_plan = os.path.join(O, "e0_plan_values.json")
    if not os.path.exists(e0_plan):
        json.dump(e0["H8_E0_primary"], open(e0_plan, "w"), indent=1)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, p), "MANIFEST.json") for t in ("t1", "t3") for p in ("train", "val")]
    runs = os.path.join(O, "runs")
    fit = lambda t, kind: os.path.join(O, "fits_%s_%s.json" % (kind, t))  # noqa: E731
    routes = [{"name": "within_lt3d", "runs": runs, "tags": {t: "%s_within_lt3d" % t for t in ("t1", "t3", "tab")},
               "fits": {t: fit(t, "within") for t in ("t1", "t3", "tab")}, "folds": folds, "modes": ["decide"]},
              {"name": "transfer_lt3d", "runs": runs, "tags": {t: "%s_transfer_lt3d" % t for t in ("t1", "t3")},
               "fits": {t: os.path.join(O, "transfer_applied_%s.json" % t) for t in ("t1", "t3")}, "folds": folds, "modes": ["decide"]},
              {"name": "public_lt3d_val", "runs": runs, "tags": {t: "%s_public_lt3d_val" % t for t in ("t1", "t3")},
               "fits": {t: fit(t, "val150") for t in ("t1", "t3")}, "folds": v150, "modes": ["decide"]},
              {"name": "source_transfer", "runs": runs, "tags": {t: "%s_source_transfer" % t for t in ("t1", "t3")},
               "fits": {t: fit(t, "source") for t in ("t1", "t3")}, "folds": v150, "modes": ["decide"]}]
    cfg_p = os.path.join(O, "config.json")
    if not os.path.exists(cfg_p):
        cfg = {"routes": routes, "units_are_logs": True, "manifests": man[:2], "c": {"t1": 0.03, "t3": 0.03}, "folds": folds,
               "folds_val150": v150, "folds_train225": t225,
               "e0": {"plan_values": e0["H8_E0_primary"], "seed": 20261114, "sigma_a": 0.10,
                      "inputs": {"workers": VAL_T1, "gt": GT, "meta": META, "horizon": HOR["t1"]}, "inputs_sha256": e0["inputs_sha256"]},
               "method_stage": {t: os.path.join(O, "mstage_%s.json" % t) for t in ("t1", "t3")}, "h8": os.path.join(O, "h8_t1.json"),
               "h8_units": "folds",
               "h9": {t: os.path.join(O, "h9_%s.json" % t) for t in ("t1", "t3")}, "h9_label": "descriptive",
               "h9_descriptive": {"tab": os.path.join(O, "h9_tab.json")},
               "note": "rehearsal v08 config: voxelnext_val is left out on purpose (H5 'not tested'); 'tab' is T1's data as an AB3DMOT stand-in; "
                       "no q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d)"}
        json.dump(cfg, open(cfg_p, "w"), indent=1)
    if not os.path.exists(plan):
        with open(plan, "w", encoding="utf-8", newline="\n") as f:
            f.write(MOCK_PLAN)
    data = ["e0_plan=" + e0_plan, "val_gt=" + GT, "scene_json=" + os.path.join(META, "scene.json"),
            "val_t1_horizon=" + HOR["t1"], "val_t3_horizon=" + HOR["t3"]]
    data += ["val_%s_export_w%d=%s" % (t, i, os.path.join(w, "x1_tracks.jsonl.gz")) for t in ("t1", "t3") for i, w in enumerate(EXPORTS[t])]
    common = ["--folds", folds, "--folds-val150", v150, "--folds-train225", t225, "--split", split, "--transfer-fits",
              os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"), "--stageA-manifests"] + man + \
             ["--config", cfg_p, "--data-root", os.path.join(O, "emptyroot"), "--data"] + data
    os.makedirs(os.path.join(O, "emptyroot"), exist_ok=True)
    run(["c1_freeze_v07.py", "--plan", plan, "--readme", a.readme, "--results-dir", os.path.join(O, "results")] + common +
        ["--hash-log", hlog, "--test-out-dir", os.path.join(O, "freeze_tests")], log)
    # (5b) Choice 41(a): the newest plan draft's own blocks, filled by c1_freeze_v07, each exactly once (separate log, probe README)
    dplan = draft_copy(os.path.join(O, "DRAFTCHECK_C1_PLAN_%s_COPY.md" % os.path.basename(DRAFT).split("_")[4]))
    preadme = probe_readme(a.readme, os.path.join(O, "README_draftcheck_probe.md"))
    run(["c1_freeze_v07.py", "--plan", dplan, "--readme", preadme, "--results-dir", os.path.join(O, "results_draftcheck")] + common +
        ["--hash-log", os.path.join(O, "C1_PLAN_HASH_LOG_DRAFTCHECK.txt"), "--test-out-dir", os.path.join(O, "freeze_tests_draftcheck")], log)
    dtxt = open(dplan, encoding="utf-8").read()
    draft_blocks = {b: dtxt.count(b + "_BEGIN\n") for b in BLOCKS}
    assert all(v == 1 for v in draft_blocks.values()), draft_blocks
    P = ["--plan", plan, "--hash-log", hlog]
    for i, t in enumerate(("t1", "t3", "tab")):
        dt = DATA_OF[t]
        items = [os.path.join(W, "70_TESTS", "k8_expl_v02", "items_k8_v02_expl_%s.npz" % dt),
                 os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_%s.npz" % dt)]
        caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (dt, p)) for p in ("train", "val")]
        run(["c1_fit_v06.py", "--items"] + items + ["--folds", folds, "--out", fit(t, "within"), "--units-subset"] + P, log)
        run(["c1_run_v06.py", "--caches"] + caches + ["--fits", fit(t, "within"), "--c1-folds", folds, "--c1-plan", plan, "--hash-log", hlog,
             "--tag", "%s_within_lt3d_decide" % t, "--mode", "decide", "--out", runs, "--workers", str(a.workers), "--resume"], log)
        keys = os.path.join(TPP, "keys_%s_val_v01.npz" % dt)
        seed_runs = ["trk=" + os.path.join(TPP, "tpp_int_ee_%s_trk_val_v01.npz" % dt)] + \
                    ["trk@%d=%s" % (s, os.path.join(TPP, "seed_sensitivity", "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (dt, s))) for s in (20261104, 20261105)]
        if t == "tab":
            run(["c1_predarm_v07.py", "--keys", keys, "--runs"] + seed_runs + ["--folds", folds, "--tracker-index", "2", "--out",
                 os.path.join(O, "h9_tab.json")] + P, log)
            continue
        run(["c1_transfer_apply_v01.py", "--transfer-fit", os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t), "--folds", folds,
             "--out", os.path.join(O, "transfer_applied_%s.json" % t)], log)
        run(["c1_fit_v06.py", "--items"] + items + ["--folds", v150, "--out", fit(t, "val150"), "--units-subset"] + P, log)
        rarm = json.load(open(os.path.join(TF, "c1_transfer_fits_%s_v01.json" % t))).get("retuned_transfer_arm")
        run(["c1_fit_v06.py", "--items"] + items + ["--folds", t225, "--apply-folds", v150, "--route", "source", "--out", fit(t, "source"),
             "--units-subset", "--retuned-arm", str(rarm)] + P, log)
        for r in routes[1:]:
            run(["c1_run_v06.py", "--caches"] + caches + ["--fits", r["fits"][t], "--c1-folds", r["folds"], "--c1-plan", plan, "--hash-log", hlog,
                 "--tag", r["tags"][t] + "_decide", "--mode", "decide", "--out", runs, "--workers", str(a.workers), "--resume"], log)
        ex = EXPORTS[t]
        run(["c1_mstage_v06.py", "--tracker", t.upper(), "--experiment", EXPERIMENT[t], "--av2-workers"] + ex +
            ["--av2-gt", GT, "--av2-meta", META, "--av2-horizon", HOR[t], "--train-workers"] + ex +
            ["--train-gt", GT, "--train-meta", META, "--train-horizon", HOR[t], "--out", os.path.join(O, "mstage_%s.json" % t), "--folds", folds] + P + MS_TEST, log)
        if t == "t1":
            run(["c1_h8_v06.py", "--workers"] + VAL_T1 + ["--gt", GT, "--meta", META, "--horizon", HOR["t1"], "--e0-plan", e0_plan,
                 "--out", os.path.join(O, "h8_t1.json"), "--folds", folds] + P, log)
        run(["c1_predarm_v07.py", "--keys", keys, "--runs"] + seed_runs + ["gt=" + os.path.join(TPP, "tpp_int_ee_%s_gt_val_v01.npz" % t),
             "--folds", folds, "--tracker-index", str(i), "--out", os.path.join(O, "h9_%s.json" % t)] + P, log)
    run(["c1_analyse_v09.py", "--config", cfg_p, "--out", os.path.join(O, "c1_analysis_rehearsal_v08.json"), "--decision",
         os.path.join(O, "c1_decision_rehearsal_v08.json"), "--csv-dir", os.path.join(O, "csv"), "--c1"] + P, log)
    run(["tests/test_c1_v12.py", os.path.join(O, "c1_tests_v12_rehearsal.json"), "--rehearsal", O], log)
    dec = json.load(open(os.path.join(O, "c1_decision_rehearsal_v08.json")))
    tv = json.load(open(os.path.join(O, "c1_tests_v12_rehearsal.json")))
    ptxt = open(plan, encoding="utf-8").read()
    summary = {"verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"], "claims_status": dec["claims_status"],
               "not_tested": dec["not_tested"], "missing_inputs": dec["missing_inputs"], "family_S": {k: v["label"] for k, v in dec["family_S"].items()},
               "tables": dec["tables"], "E0_check_ok": dec["E0_check"].get("ok"), "descriptive_trackers": dec.get("descriptive_trackers"),
               "Q1": {k: v for k, v in (dec["hypotheses"].get("Q1") or {}).items() if k in ("label", "status", "reasons")},
               "H9": {k: v for k, v in (dec["hypotheses"].get("H9") or {}).items() if k in ("label", "status", "reasons")},
               "plan_sha256": dec["binding"]["plan_sha256"], "entry_point": dec["binding"]["entry_point"], "route_problems": dec["route_problems"],
               "route_checks": {r: {t: v.get("folds_role") for t, v in by.items()} for r, by in dec["route_checks"].items()},
               "mock_plan_blocks": {b: ptxt.count(b + "_BEGIN\n") for b in BLOCKS}, "draft_copy": {"draft": os.path.basename(DRAFT), "draft_sha256": __import__("hashlib").sha256(open(DRAFT, "rb").read()).hexdigest(), "blocks": draft_blocks},
               "tests_v12_rehearsal": {k: (v.get("pass") if isinstance(v, dict) else v) for k, v in tv.items() if isinstance(v, dict) and "pass" in v},
               "tests_v12_rehearsal_verdict": tv.get("verdict"), "readme": os.path.basename(a.readme),
               "readme_sha256": __import__("hashlib").sha256(open(a.readme, "rb").read()).hexdigest(), "units": len(units),
               "H9_floor": dec.get("H9_floor", {}).get("by_tracker"),
               "V_t_hk1c_only": {r: {t: v.get("in_V_hk1c_only") for t, v in by.items()} for r, by in dec.get("V_t_reasons", {}).get("by_route", {}).items()},
               "Mstar_max_upper_bound": {r: {t: {p: (x or {}).get("max_ub") for p, x in pops.items()} for t, pops in by.items()}
                                         for r, by in dec.get("Mstar_simultaneous_upper_bounds", {}).get("by_route", {}).items()},
               "Mstar_zero_se_families": dec.get("Mstar_zero_se_families"),
               "criteria": dec.get("criteria"), "V_t": ((tv.get("REHEARSAL") or {}).get("result") or {}).get("V_t"),
               "vs_rehearsal150_v08_descriptive": ((tv.get("REHEARSAL") or {}).get("result") or {}).get("vs_rehearsal150_v08_descriptive")}
    json.dump(summary, open(os.path.join(O, "rehearsal_summary_v08.json"), "w"), indent=1, default=str)
    print(json.dumps(summary, default=str)[:3000])
    print("C1 REHEARSAL V08 DONE")


if __name__ == "__main__":
    main()
