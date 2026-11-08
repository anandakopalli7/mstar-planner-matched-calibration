#!/usr/bin/env python3
"""C1 analysis v07 (Claude line, c1_analyse_v07, 4 Nov 2026) = c1_analyse_v06 (kept, imported: decide, decide_all, descriptive_block and
every rule unchanged) on c1_guard_v04, with D16 v21 Choice 42 (R17d):
  B1  under --c1 on AV2 the guard requires the validated deposit record (entry:c1_analyse); every table must carry the current
      deposit_record_sha256 (c1_guard_v04.check_table), and every run record's provenance_v05 too.
  M2  H8's table must hold exactly the units of the folds role named by the config's "h8_units" (default "folds", the 375 logs); no subset.
  M3  Q1 (QCNet, descriptive, Choice 41c): read only from the config key "q1" ({tracker: table}); each table must be a c1_predarm_v05
      --q1-only table whose units equal the folds_val150 role's units; reported in its own block "Q1" (descriptive, outside H1 and
      family S); a Q1 failure makes only Q1 "not tested" (m5). Q1 arms inside H9 tables are ignored.
  B2  E0's recompute reads the ground truth from the quarantine when the plain file is gone (decompressed to a temporary file outside the
      workspace, SHA-256 = the config's recorded hash), and removes it afterwards.
  (g) on AV2 an existing --out or --decision is refused, and one line is appended to 40_PROTOCOL/C1_RUN_LOG.txt.
Routes and claims are c1_analyse_v06's; check_route_c1 reads c1_run_v05's provenance_v05 (with the deposit) instead of v04's.
Usage: as c1_analyse_v06.
"""
import argparse
import copy
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v04 as G  # noqa: E402
import c1_analyse_v06 as A6  # noqa: E402

A5, B, K = A6.A5, A6.B, A6.K
TRACKERS, DESCRIPTIVE_TRACKERS, FAMILY_S = A6.TRACKERS, A6.DESCRIPTIVE_TRACKERS, A6.FAMILY_S
ROLE = "entry:c1_analyse"
TABLE_ROLES, DESC_TABLES, ROUTE_FOLDS_ROLE = A6.TABLE_ROLES, A6.DESC_TABLES, A6.ROUTE_FOLDS_ROLE
PRIMARY_SEED = A6.PRIMARY_SEED
Q1_LABEL = "descriptive (Choice 20, 41c; folds_val150; outside H1 and family S)"
_exc = A6._exc


def e0_check(cfg, mode, frozen=None):
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


def load_table(key, role, cfg, mode, side, frozen, folds_sha, trackers, units, ds, deposit, exact_units=True, q1=False, allow_subset_trackers=False):
    try:
        ent = cfg.get(key)
        if not ent:
            return None
        multi = isinstance(ent, dict) and "path" not in ent
        if multi:
            paths = {t: (e if isinstance(e, str) else e["path"]) for t, e in ent.items()}
            ok_keys = set(paths) <= set(trackers) and paths if allow_subset_trackers else set(paths) == set(trackers)
            if not ok_keys:
                return {"ok": False, "why": "%s: tables for %s, not for %s" % (key, sorted(paths), list(trackers))}
        else:
            paths = {"_": ent if isinstance(ent, str) else ent["path"]}
        data, checks = {}, {}
        for t, p in paths.items():
            if not os.path.exists(p):
                return {"ok": False, "why": "%s %s: no file %s" % (key, t, p)}
            d = json.load(open(p))
            if mode == "c1":
                checks[t] = G.check_table(d, side, frozen, folds_sha, role, units=units if exact_units else None, dataset=ds,
                                          units_subset_of=None if exact_units else units, deposit=deposit)
                if role == "entry:c1_predarm" and not q1:
                    sd = (d.get("provenance") or {}).get("seeds") or {}
                    assert (sd.get("trk") or {}).get("seed") == PRIMARY_SEED and (sd.get("trk") or {}).get("verified") is True, \
                        "H9's primary table is not from the verified seed %d (R17c M4)" % PRIMARY_SEED
                    assert not d.get("q1_only"), "a --q1-only table given as an H9 table"
                if q1:
                    assert d.get("q1_only") is True and "H9" not in d, "a Q1 table must be a c1_predarm_v05 --q1-only table (Choice 42e)"
            else:
                dsx = (d.get("provenance") or {}).get("dataset")
                assert dsx in ("nuscenes", "synthetic"), "--%s accepts nuScenes or synthetic tables only, not %s" % (mode, dsx)
                checks[t] = {"entry_point": list((d.get("provenance") or {}).get("entry_point", {"(none)": None}))[0]}
            data[t] = d
        if not multi:
            return {"ok": True, "data": data["_"], "checks": checks["_"]}
        return {"ok": True, "data": data, "checks": checks}
    except Exception as ex:
        return {"ok": False, "why": "%s: not provenance-valid: %s" % (key, _exc(ex))}


def add_q1(dec, q1tab):
    """m5: Q1 in its own block; nothing else in the decision is read or changed."""
    dec["hypotheses"].pop("Q1", None)
    dec["claims_status"].pop("Q1", None)
    try:
        if q1tab and q1tab.get("ok"):
            by = {t: {k: v["arms"][k] for k in ("Q1_deployed", "Q1_gt") if k in v["arms"]} for t, v in q1tab["data"].items()}
            assert any(by.values()), "the Q1 tables hold no QCNet arm"
            dec["hypotheses"]["Q1"] = {"label": Q1_LABEL, "status": "descriptive", "reasons": [], "by_tracker": by, "checks": q1tab.get("checks")}
            dec["claims_status"]["Q1"] = "descriptive"
            return dec
        why = (q1tab or {}).get("why", "the Q1 tables are missing")
    except Exception as ex:
        why = "exception: " + _exc(ex)
    dec["hypotheses"]["Q1"] = {"label": Q1_LABEL, "status": "not tested", "reasons": [why]}
    dec["claims_status"]["Q1"] = "not tested"
    dec["missing_inputs"].append("Q1: %s" % why)
    dec["not_tested"] = sorted(set(dec["not_tested"]) | {"Q1"})
    return dec


def decide_all(results_all, cfg, mode, aux):
    dec = A6.decide_all(results_all, cfg, mode, aux)
    return add_q1(dec, aux.get("q1"))


def check_route_c1(rr, r, t, side, frozen, fds, deposit):
    tag = r["tags"][t]
    rr2 = dict(rr)
    pv = rr.get("provenance_v05") or {}
    assert pv, "run %s carries no c1_run_v05 provenance (provenance_v05)" % tag
    assert pv.get("deposit_record_sha256") == deposit, "run %s was made under another deposit record (Choice 42a)" % tag
    rr2["provenance_v04"] = pv
    return A6.check_route_c1(rr2, r, t, side, frozen, fds)


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
    units = sorted(fj["fold_of_log"]) if fj else None
    h8_role = cfg.get("h8_units", "folds")
    h8_units = units
    v150_units = None
    if mode == "c1":
        if h8_role != "folds":
            hp, _ = G.role_hash(frozen, h8_role)
            h8_units = sorted(json.load(open(os.path.join(G.W, hp)))["fold_of_log"])
        if (frozen.roles or {}).get("folds_val150"):
            vp, _ = G.role_hash(frozen, "folds_val150")
            v150_units = sorted(json.load(open(os.path.join(G.W, vp)))["fold_of_log"])
    elif cfg.get("folds_val150"):
        v150_units = sorted(json.load(open(cfg["folds_val150"]))["fold_of_log"])
    v150_sha = None
    if mode == "c1" and (frozen.roles or {}).get("folds_val150"):
        v150_sha = G.role_hash(frozen, "folds_val150")[1]
    elif cfg.get("folds_val150"):
        v150_sha = G.sha(cfg["folds_val150"])
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "plan_sha256": side, "entry_point": rt["entry_point"],
               "code_sha256": rt["code_sha256"], "folds_sha256": folds_sha, "versions": rt.get("versions"),
               "hash_log": G.rel(a.hash_log) if a.hash_log else "canonical", "hash_log_sha256": rt.get("hash_log_sha256"),
               "deposit_record_sha256": deposit, "h8_units_role": h8_role}
    tabs = {}
    for k, r in TABLE_ROLES.items():
        u = h8_units if k == "h8" else units
        tabs[k] = load_table(k, r, cfg, mode, side, frozen, folds_sha, TRACKERS, u, ds_units, deposit)
    aux = {"route_problems": {}, "tables": tabs,
           "tables_descriptive": {k: load_table(k, r, cfg, mode, side, frozen, folds_sha, DESCRIPTIVE_TRACKERS, units, ds_units, deposit)
                                  for k, r in DESC_TABLES.items() if cfg.get(k)},
           "q1": load_table("q1", "entry:c1_predarm", cfg, mode, side, frozen, v150_sha, TRACKERS, v150_units, ds_units, deposit, q1=True,
                            allow_subset_trackers=True) if cfg.get("q1") else None}
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
                    route_checks.setdefault(r["name"], {})[t] = check_route_c1(rr, r, t, side, frozen, ds_units, deposit)
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
    dec["binding"] = binding
    dec["route_checks"] = route_checks
    dec["route_problems"] = aux["route_problems"]
    dec["tables"] = {k: ({"ok": v["ok"], "why": v.get("why"), "checks": v.get("checks")} if v else None) for k, v in list(aux["tables"].items()) + [("q1", aux.get("q1"))]}
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
    print("C1 ANALYSIS V07 DONE")


if __name__ == "__main__":
    main()
