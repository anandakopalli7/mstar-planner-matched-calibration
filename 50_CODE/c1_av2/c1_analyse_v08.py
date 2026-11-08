#!/usr/bin/env python3
"""C1 analysis v08 (Claude line, c1_analyse_v08, 5 Nov 2026) = c1_analyse_v07 (kept, imported: e0_check, load_table, check_route_c1; and
through it c1_analyse_v06's decide_all, routes, claims and rules, all unchanged) on c1_guard_v05, with D16 v23 Choice 44 and v24 Choice 45c:
  * 44(d), 45(c) M-D: Q1 (QCNet) is not tested in C1. A config with a "q1" entry is refused. The decision reports Q1 as "not tested" with
    Choice 44(d)'s two reasons, in its own block, outside H1, H9 and family S. C1_verdict, gate_H1, H9 and family S are those of
    c1_analyse_v06.decide_all (Q1 is never read). Q1 is not listed among the missing inputs, because it was decided before any outcome.
  * 44(f) m1: on AV2 (--c1) the guard writes the run-log "start" line, and the analysis records the run log's hash. Every table it
    consumes must have a "done" line in the verified, chained run log whose output hash equals the file's SHA-256: the method-stage, H8,
    H9 and descriptive H9 tables, and every route's run record. A table without one is not provenance-valid (the claim it carries is
    then "not tested", Choice 33). A route's run record without one is a route problem. A broken chain refuses the analysis.
  * the rest as v07: the deposit record on AV2, tables with the current deposit_record_sha256, H8 on the folds units (h8_units), E0's
    recompute from the quarantine (on c1_guard_v05), an existing --out or --decision refused on AV2, the "done" line after the outputs.
Usage: as c1_analyse_v07 (the config holds no "q1" entry).
"""
import argparse
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v05 as G  # noqa: E402
import c1_analyse_v07 as A7  # noqa: E402

A6 = A7.A6
A5, B, K = A6.A5, A6.B, A6.K
TRACKERS, DESCRIPTIVE_TRACKERS, FAMILY_S = A6.TRACKERS, A6.DESCRIPTIVE_TRACKERS, A6.FAMILY_S
ROLE = "entry:c1_analyse"
TABLE_ROLES, DESC_TABLES = A6.TABLE_ROLES, A6.DESC_TABLES
_exc = A6._exc
Q1_LABEL = "Q1 (QCNet on the 150 validation logs, descriptive): not tested in C1 (D16 v23 Choice 44d, v24 Choice 45c)"
Q1_REASONS = ["no C1 tracker index shares QCNet's history source: QCNet's deployed histories are the 10 Hz matched AB3DMOT tracks with "
              "the SF threshold (30_DATA/qcnet_av2_v03), while C1's AB3DMOT index is the 2 Hz run of Choice 11 (Choice 43a, 44d)",
              "QCNet predicted 95.7 % of T1's 2 Hz records (88,182 of 92,166), so the frozen condition not_predicted == 0 cannot hold (Choice 44d)"]


def add_q1_not_tested(dec):
    """44(d): Q1 in its own block, "not tested" with the decided reasons; nothing else in the decision is read or changed."""
    dec["hypotheses"].pop("Q1", None)
    dec["hypotheses"]["Q1"] = {"label": Q1_LABEL, "status": "not tested", "reasons": list(Q1_REASONS), "decided": "before any outcome (Choice 44d)"}
    dec["claims_status"]["Q1"] = "not tested"
    dec["not_tested"] = sorted(set(dec["not_tested"]) | {"Q1"})
    return dec


def decide_all(results_all, cfg, mode, aux):
    assert "q1" not in cfg, "the config holds a q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d)"
    return add_q1_not_tested(A6.decide_all(results_all, cfg, mode, aux))


def e0_check(cfg, mode, frozen=None):
    """c1_analyse_v07.e0_check on c1_guard_v05 (its c1_gt_<pid>_* temporary folder is never swept while this run lives)."""
    import copy
    tmp = None
    try:
        e = cfg.get("e0")
        if e and int(e.get("seed", -1)) != A6.E0.SEED:
            return {"present": True, "ok": False, "reason": "E0's seed must be %d (R17c m2), not %s" % (A6.E0.SEED, e.get("seed"))}
        if e and frozen is not None and not os.path.exists(e["inputs"]["gt"]):
            k = G.rel(e["inputs"]["gt"])
            want = (e.get("inputs_sha256") or {}).get(k)
            member = G.member_for(want) if want else None
            assert member, "the E0 ground truth is neither on disk nor in the quarantine"
            tmp = G.materialise_quarantined(member, want)
            cfg = copy.deepcopy(cfg)
            cfg["e0"]["inputs"]["gt"] = tmp
            cfg["e0"]["inputs_sha256"] = {(G.rel(tmp) if kk == k else kk): v for kk, v in cfg["e0"]["inputs_sha256"].items()}
        return A5.e0_check(cfg, mode, frozen)
    except Exception as ex:
        return {"present": bool(cfg.get("e0")), "ok": False, "reason": "exception: " + _exc(ex)}
    finally:
        G.cleanup(tmp)


def logged_check(paths, logged):
    """m1: every consumed file's SHA-256 must be an output of a "done" line of the run log."""
    out, missing = {}, []
    for p in paths:
        h = G.sha(p)
        hits = logged.get(h) or []
        if not hits:
            missing.append(G.rel(p))
        else:
            out[G.rel(p)] = {"sha256": h, "done_lines": [{"output": q, "entry": e, "run_id": r} for q, e, r in hits]}
    return out, missing


def table_paths(cfg, key):
    ent = cfg.get(key)
    if not ent:
        return []
    if isinstance(ent, dict) and "path" not in ent:
        return [e if isinstance(e, str) else e["path"] for e in ent.values()]
    return [ent if isinstance(ent, str) else ent["path"]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--csv-dir", default=None)
    g_ = ap.add_mutually_exclusive_group(required=True)
    for m_ in ("c1", "standin", "reproduce", "smoke"):
        g_.add_argument("--" + m_, action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None, help="a rehearsal's own log: nuScenes units only")
    ap.add_argument("--boot", type=int, default=K.B_BOOT)
    a = ap.parse_args(argv)
    mode = "c1" if a.c1 else "standin" if a.standin else "reproduce" if a.reproduce else "smoke"
    assert mode == "smoke" or a.boot == K.B_BOOT, "B = 2000 is fixed outside --smoke"
    B.configure(mode)
    B.K8_SEEDS = mode == "reproduce"
    t0 = time.time()
    cfg = json.load(open(a.config))
    assert "q1" not in cfg, "the config holds a q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d)"
    fj = json.load(open(cfg["folds"])) if cfg.get("folds") else None
    ds_units = G.folds_dataset(fj) if fj else "unknown"
    side = frozen = rt = None
    deposit = None
    if mode == "c1":
        assert a.plan, "--c1 needs --plan"
        G.refuse_existing([a.out, a.decision], ds_units)
        side, frozen, rt = G.guard(ds_units, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        deposit = rt["deposit_record_sha256"]
        G.require_bound(frozen, a.config, "config")
        folds_sha = G.require_bound(frozen, cfg["folds"], "folds")
        assert "c" in cfg, "--c1: c must be stated in the frozen config (R16 m1, R17 m9)"
    else:
        assert a.plan is None and a.hash_log is None, "--%s runs without a plan or a hash log" % mode
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha = G.sha(cfg["folds"]) if cfg.get("folds") else None
    av2_logged = mode == "c1" and ds_units not in G.EXEMPT_DS
    logged, run_log_rec = ({}, {"run_log": "not used (%s)" % ds_units})
    if av2_logged:
        logged, run_log_rec = G.logged_outputs()
    units = sorted(fj["fold_of_log"]) if fj else None
    h8_role = cfg.get("h8_units", "folds")
    h8_units = units
    if mode == "c1" and h8_role != "folds":
        hp, _ = G.role_hash(frozen, h8_role)
        h8_units = sorted(json.load(open(os.path.join(G.W, hp)))["fold_of_log"])
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "plan_sha256": side, "entry_point": rt["entry_point"],
               "code_sha256": rt["code_sha256"], "folds_sha256": folds_sha, "versions": rt.get("versions"),
               "hash_log": G.rel(a.hash_log) if a.hash_log else "canonical", "hash_log_sha256": rt.get("hash_log_sha256"),
               "deposit_record_sha256": deposit, "h8_units_role": h8_role, "run_log_at_start": run_log_rec, "run_id": rt.get("run_id")}
    logged_tables = {}

    def gate_logged(key, tab):
        if not av2_logged or not tab or not tab.get("ok"):
            return tab
        ok_paths, missing = logged_check(table_paths(cfg, key), logged)
        logged_tables[key] = ok_paths
        if missing:
            return {"ok": False, "why": "%s: no 'done' line in the run log for %s (Choice 44f m1)" % (key, missing)}
        return tab
    tabs = {}
    for k, r in TABLE_ROLES.items():
        u = h8_units if k == "h8" else units
        tabs[k] = gate_logged(k, A7.load_table(k, r, cfg, mode, side, frozen, folds_sha, TRACKERS, u, ds_units, deposit))
    aux = {"route_problems": {}, "tables": tabs,
           "tables_descriptive": {k: gate_logged(k, A7.load_table(k, r, cfg, mode, side, frozen, folds_sha, DESCRIPTIVE_TRACKERS, units, ds_units, deposit))
                                  for k, r in DESC_TABLES.items() if cfg.get(k)}}
    aux["e0"] = e0_check(cfg, mode, frozen)
    print("E0 check:", json.dumps({k: v for k, v in aux["e0"].items() if k != "recomputed"}, default=float), flush=True)
    log_of_scene = {}
    for p in cfg.get("manifests", []):
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    source_of_log = fj["source_of_log"] if fj else {}
    results, k8res, route_checks = {}, {}, {}
    csv_dir = a.csv_dir or os.path.dirname(os.path.abspath(a.out))
    os.makedirs(csv_dir, exist_ok=True)
    for r in cfg["routes"]:
        for i, t in enumerate(TRACKERS + DESCRIPTIVE_TRACKERS):
            if t not in r["tags"]:
                continue
            try:
                runs, tag = r["runs"], r["tags"][t]
                rp = os.path.join(runs, "run_record_%s_decide.json" % tag)
                assert os.path.exists(rp), "no run record " + rp
                rr = json.load(open(rp))
                caches = rr.get("caches") or []
                dsets = [G.manifest_dataset(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in caches]
                if mode == "c1":
                    if a.hash_log:
                        assert caches and all(d_ == "nuscenes" for d_ in dsets), "GUARD: a rehearsal hash log with caches that are not nuScenes"
                    route_checks.setdefault(r["name"], {})[t] = A7.check_route_c1(rr, r, t, side, frozen, ds_units, deposit)
                    if av2_logged:
                        okp, missing = logged_check([rp], logged)
                        assert not missing, "run record %s has no 'done' line in the run log (Choice 44f m1)" % missing
                        route_checks[r["name"]][t]["run_log"] = okp
                else:
                    assert not (rr.get("c1") and not rr.get("standin")), "GUARD: --%s refuses C1 confirmatory run records (R17 M2)" % mode
                    assert caches, "GUARD: --%s refuses a run record without caches (R17b A3)" % mode
                    assert all(d_ == "nuscenes" for d_ in dsets), "GUARD: --%s refuses runs on caches that are not nuScenes: %s" % (mode, dsets)
                    if mode == "standin":
                        assert rr.get("c1") is True and rr.get("standin") is True, "run %s is not a stand-in run" % tag
                l_of = log_of_scene
                if cfg.get("units_are_logs"):
                    l_of = {o["scene"]: o["scene"] for o in (json.loads(l) for l in open(os.path.join(runs, "episodes_%s_decide.jsonl" % tag)))}
                cc = cfg["c"] if mode == "c1" else cfg.get("c", B.C_DEFAULT)
                c_t = float(cc.get(t, cc[TRACKERS[0]]))
                out, res_small, res = B.analyse_route_tracker(r["name"], i, tag, runs, (r.get("fits") or {}).get(t), l_of, source_of_log, c_t,
                                                              a.boot, r.get("retuned_arm"))
                K.csv_tables_decide(res, "%s_%s" % (r["name"], t), csv_dir)
                results.setdefault(r["name"], {})[t] = out
                k8res.setdefault(r["name"], {})[t] = K.strip_csv_payload(res_small)
                del res
                print("%s %s: done %.0f s" % (r["name"], t, time.time() - t0), flush=True)
            except Exception as ex:
                if str(ex).startswith("GUARD:"):
                    raise
                aux["route_problems"].setdefault(r["name"], {})[t] = "not provenance-valid or failed: " + _exc(ex)
                print("%s %s: %s" % (r["name"], t, aux["route_problems"][r["name"]][t][:200]), flush=True)
    dec = decide_all(results, cfg, mode, aux)
    if mode == "c1":
        rt = G.verify_runtime_again(frozen, rt)
        binding["code_sha256"] = rt["code_sha256"]
    binding["tables_in_run_log"] = logged_tables if av2_logged else "not used (%s)" % ds_units
    dec["binding"] = binding
    dec["route_checks"] = route_checks
    dec["route_problems"] = aux["route_problems"]
    dec["tables"] = {k: ({"ok": v["ok"], "why": v.get("why"), "checks": v.get("checks")} if v else None) for k, v in aux["tables"].items()}
    for path, obj in ((a.out, {"stamp": B.STAMPS[mode], "binding": binding, "c1": results, "k8": k8res}), (a.decision, dec)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=1, default=float)
        os.replace(tmp, path)
    if mode == "c1":
        G.run_log_append(ds_units, os.path.abspath(__file__), side, deposit, {"config": binding["config_sha256"]}, [a.out, a.decision])
    print(json.dumps({"C1_verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"][:8],
                      "not_tested": dec["not_tested"], "claims": dec["claims_status"]}, default=str))
    print(B.STAMPS[mode])
    print("C1 ANALYSIS V08 DONE")


if __name__ == "__main__":
    main()
