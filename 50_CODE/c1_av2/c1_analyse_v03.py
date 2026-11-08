#!/usr/bin/env python3
"""C1 analysis v03 (Claude line, c1_analyse_v03, 2 Nov 2026) = c1_analyse_v02 (kept, imported) with R17's defects fixed and D16 v09
Choices 24-26. v02's per-route statistics (analyse_route_tracker: k8_analyse_v04.analyse_decide, H10, RETUNED-HK1, E14, source
heterogeneity) are used unchanged; these functions are REPLACED in v02's namespace, so v02's route analysis calls the v03 versions:
  form_b, joint_b   C2 / Choice 25: a missing comparator makes the part fail ("missing" non-empty -> met False); an empty V_t (V^J) is
                    "vacuous": part (ii) holds vacuously, no rejection (p None), never p = 0 (R17 m3).
  joint_status      R17 m5: ValidJ also requires the pooled joint population to be evaluable (>= 39 logs), as k8_analyse_v04.
  per_scene_rates   Choice 25: a NaN rate or an arm missing in some log is an error, never a silent drop.
  holm              Choice 26 / M1: family S has exactly m = 5 members (H2, H3, H4, H6b, H10); a member that cannot be tested (gate
                    failed, no p-value, route absent) enters with p = 1; a member is confirmed only if its bound-based verdict holds
                    AND Holm rejects at its level (R17 m6).
  decide            the decision: H1 needs both trackers, every comparator and every arm present (else NO-GO with the reason); Form C
                    without B4 is a failed condition (m9); H3 fails a tracker whose M*Jx lambda did not qualify in some fold (m2,
                    Choice 25); H4 needs RETUNED's transfer point (Choice 25); H9 is required when its label is secondary (M3);
                    absent H6-H9 inputs are failed conditions; per-tracker wording for mixed failure types; a non-evaluable pooled
                    cell is named as such (m10).
  main              Choice 24 / M2 / M3: --c1 accepts only a FROZEN plan in C1_PLAN_HASH_LOG.txt (c1_guard_v01); the config, the
                    analysis code, the folds and the transfer fits must be bound; every within-AV2 fit is checked by provenance
                    (plan hash = sidecar, folds hash, code hashes bound); every run record's c1_plan_sha256 and c1_folds_sha256 must
                    equal the sidecar and the bound folds; the H6-H9 inputs are given as {"path", "sha256"} and hash-checked in every
                    mode. --standin / --reproduce / --smoke refuse confirmatory run records and any cache that is not nuScenes.
                    c is required in the config under --c1 (m9).
Usage: as c1_analyse_v02, plus --hash-log (a rehearsal passes its own log).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_analyse_v02 as B  # noqa: E402
import c1_guard_v01 as G  # noqa: E402

K, A, M, S = B.K, B.A, B.M, B.S
DELTA, POPS, TRACKERS, K_SET, KJ_SET = B.DELTA, B.POPS, B.TRACKERS, B.K_SET, B.KJ_SET
FAMILY_S = ("H2", "H3", "H4", "H6b", "H10")
REQUIRED_ARMS = ("Mstar",) + K_SET
_paired = B.paired


def form_b(status, rate, Ws, method="Mstar", comps=K_SET, alpha=0.05):
    present = [c for c in comps if c in status and c in rate]
    missing = [c for c in comps if c not in present]
    V = [c for c in present if not status[c]["shown_above"]]
    level = 1 - alpha / max(len(V), 1)
    per = {}
    for c in V:
        r = _paired(rate, Ws, method, c, level)
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    vac = not V
    met = bool(method in status and status[method]["valid"] and not missing and all(v["lower"] for v in per.values()))
    p = None if vac else min(1.0, len(V) * max(v["p_lt0"] for v in per.values()))
    return {"method": method, "valid_method": bool(method in status and status[method]["valid"]), "V": V,
            "in_V_by_choice9": [c for c in V if status[c]["floor_only"]], "removed_shown_above": [c for c in present if c not in V],
            "missing": missing, "n_V": len(V), "level": level, "vs": per, "met": met, "vacuous": vac, "p_rejection_bonferroni": p,
            "rule": "C1 v04 5.4 FormB with Choice 9 (E13); a missing comparator fails it (D16 Choice 25); empty V_t is vacuous"}


def joint_status(jv):
    per, ok = {}, True
    for p in POPS:
        r = jv["pops"][p]
        has = r.get("E") is not None
        v = bool(has and r.get("evaluable") and not r.get("flagged") and r.get("ub_le_delta_plus_0.03"))
        per[p] = {"E": r.get("E"), "lb": r.get("lb_one_sided_0.95"), "ub": r.get("ub_one_sided_0.95"), "flagged": r.get("flagged"),
                  "evaluable": r.get("evaluable"), "validJ": v}
        ok = ok and v
    return {"validJ": bool(ok), "shown_aboveJ": bool(not ok), "pops": per}


def joint_b(jstat, rate, Ws, method="MstarJx", comps=KJ_SET, alpha=0.05):
    present = [c for c in comps if c in jstat and c in rate]
    missing = [c for c in comps if c not in present]
    V = [c for c in present if jstat[c]["validJ"]]
    level = 1 - alpha / max(len(V), 1)
    per = {}
    for c in V:
        r = _paired(rate, Ws, method, c, level)
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    vac = not V
    valid_m = bool(method in jstat and jstat[method]["validJ"])
    met = bool(valid_m and not missing and all(v["lower"] for v in per.values()))
    p = None if vac else min(1.0, len(V) * max(v["p_lt0"] for v in per.values()))
    return {"method": method, "validJ_method": valid_m, "VJ": V, "missing": missing, "level": level, "vs": per, "met": met, "vacuous": vac,
            "p_rejection_bonferroni": p}


def per_scene_rates(eps, arm_of_scene, scenes):
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps if o.get("entered") and o["arm"] != "LOG"}
    arms = sorted({a for _, a in inf})
    gaps = {a: [sc for sc in scenes if (sc, a) not in inf] for a in arms}
    bad = {a: g[:3] for a, g in gaps.items() if g}
    assert not bad, "an arm is missing in some logs (never dropped silently, D16 Choice 25): %s" % bad
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms}
    if arm_of_scene:
        rate["RETUNED"] = np.array([inf[(sc, arm_of_scene[sc])][0] / max(inf[(sc, arm_of_scene[sc])][1], 1) for sc in scenes])
    for a, v in rate.items():
        assert np.all(np.isfinite(v)), "NaN infeasible rate for " + a
    return rate


def holm(claims, alpha=0.05, gate=True):
    out = {}
    full = {}
    for c in FAMILY_S:
        v = claims.get(c)
        if v is None:
            full[c] = {"p": 1.0, "holds": False, "why": "absent (route or input missing)"}
        elif v.get("gate_ok") is False:
            full[c] = {"p": 1.0, "holds": False, "why": "validity gate failed"}
        elif v.get("p") is None:
            full[c] = {"p": 1.0, "holds": bool(v.get("holds")), "why": "no p-value (untestable or vacuous)"}
        else:
            full[c] = {"p": float(v["p"]), "holds": bool(v.get("holds")), "why": None}
    if not gate:
        return {c: dict(v, rejected=None, label=B.GATE_NOTE, m=len(FAMILY_S)) for c, v in full.items()}
    order = sorted(FAMILY_S, key=lambda c: (full[c]["p"], FAMILY_S.index(c)))
    stop = False
    for i, c in enumerate(order):
        lvl = alpha / (len(FAMILY_S) - i)
        rej = (not stop) and full[c]["p"] <= lvl
        stop = stop or not rej
        conf = bool(rej and full[c]["holds"])
        out[c] = dict(full[c], holm_level=lvl, rejected=bool(rej), confirmed=conf, m=len(FAMILY_S),
                      label="confirmed (Holm, family S, m = 5)" if conf else "not confirmed" + (" (%s)" % full[c]["why"] if full[c]["why"] else ""))
    return out


def lambda_qualified(fits_path):
    f = json.load(open(fits_path))
    folds = (f.get("joint") or {}).get("fit", {}).get("folds", {})
    bad = [k for k, v in folds.items() if v.get("MstarJx", {}).get("none_qualifies_grid_max_used")]
    return not bad and bool(folds), bad


def decide(results, cfg, mode):
    fc_ = []
    dec = {"stamp": B.STAMPS[mode], "delta": DELTA, "wording": B.WORDING, "hypotheses": {}, "failed_conditions": fc_}
    get = lambda route, t: results.get(route, {}).get(t)  # noqa: E731
    w = {t: get("within_lt3d", t) for t in TRACKERS}
    wording = {}
    for t in TRACKERS:
        if w[t] is None:
            fc_.append("%s: the within-AV2 decision-mode run is missing" % t)
            wording[t] = "missing"
            continue
        fb, st = w[t]["form_b"], w[t]["status"]
        miss_arms = [x for x in REQUIRED_ARMS if x not in st]
        if miss_arms:
            fc_.append("%s: arms missing from the run: %s" % (t, miss_arms))
        if fb["missing"]:
            fc_.append("%s: comparators missing (Form B fails, D16 Choice 25): %s" % (t, fb["missing"]))
        sm = st.get("Mstar")
        if sm and not sm["valid"]:
            for p, r in sm["pops"].items():
                if not r["pooled_evaluable"]:
                    fc_.append("%s %s: M*'s pooled cell is not evaluable" % (t, p))
                for k_ in ("NoFlag", "Floor"):
                    if not r[k_]:
                        fc_.append("%s %s: M* %s fails" % (t, p, k_))
                if r["pooled_evaluable"] and not r["NoFlag_pool"]:
                    fc_.append("%s %s: M*'s pooled cell is shown above delta" % (t, p))
                if r["pooled_evaluable"] and not r["HK1c"]:
                    fc_.append("%s %s: M* HK1c fails" % (t, p))
                if r["FamFlag"]:
                    fc_.append("%s %s: M* family cell flagged" % (t, p))
        for c, v in fb["vs"].items():
            if not v["lower"]:
                fc_.append("%s: M* not less infeasible than %s%s" % (t, c, " (in V_t by Choice 9)" if c in fb["in_V_by_choice9"] else ""))
        wording[t] = ("GO part met" if fb["met"] else "not shown above delta, operability not shown" if (sm and sm["valid"])
                      else "floor not met" if (sm and not sm["shown_above"]) else "M* shown above delta" if sm else "M* missing")
    h1 = all(w[t] is not None and w[t]["form_b"]["met"] and not [x for x in REQUIRED_ARMS if x not in w[t]["status"]] for t in TRACKERS)
    dec["hypotheses"]["H1"] = {"label": "primary", "holds": bool(h1), "by_tracker": {t: (w[t] or {}).get("form_b") for t in TRACKERS},
                               "wording_by_tracker": wording}
    dec["C1_verdict"] = "GO" if h1 else "NO-GO"
    claims = {}
    if all(w.values()):
        fc = {t: w[t]["form_c"] for t in TRACKERS}
        if all(fc.values()):
            h2 = all(fc[t]["met"] for t in TRACKERS)
            dec["hypotheses"]["H2"] = {"label": "secondary", "holds": h2, "by_tracker": fc}
            claims["H2"] = {"p": max(fc[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h2}
        else:
            fc_.append("H2: B4 is missing, Form C cannot be computed")
        if all("H3" in w[t] for t in TRACKERS):
            h3 = {t: w[t]["H3"] for t in TRACKERS}
            lq = {t: lambda_qualified(r["fits"][t]) for r in cfg["routes"] if r["name"] == "within_lt3d" for t in TRACKERS if r.get("fits")}
            for t, (ok_, bad) in lq.items():
                if not ok_:
                    fc_.append("H3 %s: M*Jx's lambda did not qualify in folds %s (D16 Choice 25)" % (t, bad))
            for t in TRACKERS:
                if h3[t]["missing"]:
                    fc_.append("H3 %s: joint comparators missing: %s" % (t, h3[t]["missing"]))
            gate3 = all(h3[t]["validJ_method"] for t in TRACKERS) and all(v[0] for v in lq.values()) and len(lq) == 2
            holds3 = gate3 and all(h3[t]["met"] for t in TRACKERS)
            pv = [h3[t]["p_rejection_bonferroni"] for t in TRACKERS]
            dec["hypotheses"]["H3"] = {"label": "secondary", "holds": holds3, "validity_gate": gate3, "lambda_qualified": lq, "by_tracker": h3}
            claims["H3"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate3, "holds": holds3}
        else:
            fc_.append("H3: M*Jx missing from the within-AV2 runs")
        h10 = {t: w[t].get("H10") for t in TRACKERS}
        if all(h10.values()):
            h10h = all(h10[t]["met"] for t in TRACKERS)
            dec["hypotheses"]["H10"] = {"label": "secondary", "holds": h10h, "by_tracker": h10}
            claims["H10"] = {"p": max(h10[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h10h}
        else:
            fc_.append("H10: B6 or M* missing")
        dec["hypotheses"]["FormA"] = {"label": "descriptive", "by_tracker": {t: w[t]["form_a"] for t in TRACKERS}}
    tr = {t: get("transfer_lt3d", t) for t in TRACKERS}
    if all(tr.values()):
        gate4 = all(tr[t]["form_b"]["valid_method"] for t in TRACKERS)
        miss4 = {t: tr[t]["form_b"]["missing"] for t in TRACKERS if tr[t]["form_b"]["missing"]}
        if miss4:
            fc_.append("H4: comparators missing (RETUNED's transfer point is required): %s" % miss4)
        h4 = all(tr[t]["form_b"]["met"] for t in TRACKERS)
        pv = [tr[t]["form_b"]["p_rejection_bonferroni"] for t in TRACKERS]
        dec["hypotheses"]["H4"] = {"label": "secondary", "holds": h4, "validity_gate": gate4, "by_tracker": {t: tr[t]["form_b"] for t in TRACKERS}}
        claims["H4"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate4, "holds": h4}
    else:
        fc_.append("H4: the transfer route is missing")
    for route, hn in (("voxelnext_val", "H5"), ("public_lt3d_val", "H1-P"), ("source_transfer", "source_transfer")):
        rr_ = {t: get(route, t) for t in TRACKERS}
        if all(rr_.values()):
            dec["hypotheses"][hn] = {"label": "descriptive", "holds_as_formula": all(rr_[t]["form_b"]["met"] for t in TRACKERS),
                                     "by_tracker": {t: rr_[t]["form_b"] for t in TRACKERS}}
    ms = cfg.get("_method_stage")
    if ms:
        h6 = {t: B.h6_rules(ms[t]) for t in TRACKERS}
        h7 = {t: B.h7_rule(ms[t]) for t in TRACKERS}
        h6b = all(h6[t]["H6b"] for t in TRACKERS)
        dec["hypotheses"]["H6a"] = {"label": "secondary (no-flag)", "holds": all(h6[t]["H6a"] for t in TRACKERS), "by_tracker": h6}
        dec["hypotheses"]["H6b"] = {"label": "secondary", "holds": h6b}
        pv = [h6[t]["H6b_p"] for t in TRACKERS]
        claims["H6b"] = {"p": max(pv) if all(p is not None for p in pv) else None, "gate_ok": True, "holds": h6b}
        dec["hypotheses"]["H7"] = {"label": "secondary (no-flag)", "holds": all(h7[t]["H7"] for t in TRACKERS), "by_tracker": h7}
    else:
        fc_.append("H6a, H6b, H7: the method-stage results are missing")
    if cfg.get("_h8"):
        dec["hypotheses"]["H8"] = dict(cfg["_h8"], label="secondary, family P at 0.05 (c1_h8_v01)")
    else:
        fc_.append("H8: the diagnosis table is missing")
    if cfg.get("_h9"):
        dec["hypotheses"]["H9"] = {"label": "secondary (no-flag, floor 6)", "holds": all(v.get("H9") for v in cfg["_h9"].values()),
                                   "by_tracker": {t: v["arms"].get("TPP") for t, v in cfg["_h9"].items()}}
        q1 = {t: {k: v["arms"][k] for k in ("Q1_deployed", "Q1_gt") if k in v["arms"]} for t, v in cfg["_h9"].items()}
        if any(q1.values()):
            dec["hypotheses"]["Q1"] = {"label": "descriptive (Choice 20; never in family S)", "by_tracker": q1}
    elif cfg.get("h9_label", "secondary") == "secondary":
        fc_.append("H9: the predictor-arm results are missing")
    dec["family_S"] = holm(claims, 0.05, gate=h1)
    dec["gate_H1"] = bool(h1)
    return dec


for _n, _f in (("form_b", form_b), ("joint_b", joint_b), ("joint_status", joint_status), ("per_scene_rates", per_scene_rates),
               ("holm", holm), ("decide", decide)):
    setattr(B, _n, _f)


def load_checked(entry):
    """{"path", "sha256"} -> the JSON, hash-checked (R17 M3)."""
    assert isinstance(entry, dict) and "path" in entry and "sha256" in entry, "an H6-H9 input must be given as {path, sha256}"
    assert G.sha(entry["path"]) == entry["sha256"], "input differs from its recorded hash: " + entry["path"]
    return json.load(open(entry["path"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--csv-dir", default=None)
    g = ap.add_mutually_exclusive_group(required=True)
    for m_ in ("c1", "standin", "reproduce", "smoke"):
        g.add_argument("--" + m_, action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=G.HASH_LOG)
    ap.add_argument("--boot", type=int, default=K.B_BOOT)
    a = ap.parse_args(argv)
    mode = "c1" if a.c1 else "standin" if a.standin else "reproduce" if a.reproduce else "smoke"
    assert mode == "smoke" or a.boot == K.B_BOOT, "B = 2000 is fixed outside --smoke"
    B.configure(mode)
    B.K8_SEEDS = mode == "reproduce"
    t0 = time.time()
    cfg = json.load(open(a.config))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_analyse_v03", "c1_analyse_v06", LEGACY.ds_config(cfg))
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "analysis_sha256": G.sha(os.path.abspath(__file__)), "v02_sha256": G.sha(B.__file__)}
    side = frozen = None
    if mode == "c1":
        assert a.plan, "--c1 needs --plan"
        side, frozen = G.frozen_plan(a.plan, a.hash_log)
        for p in (os.path.abspath(__file__), B.__file__, B.__file__.replace("v02", "v01"), K.__file__, a.config, cfg["folds"]):
            G.require_bound(frozen, p)
        assert "c" in cfg, "--c1: c must be stated in the frozen config (R16 m1, R17 m9)"
        binding["plan_sha256"] = side
    for key in ("method_stage", "h9"):
        if cfg.get(key):
            cfg["_" + key] = {t: load_checked(e) for t, e in cfg[key].items()}
    if cfg.get("h8"):
        cfg["_h8"] = load_checked(cfg["h8"])
    log_of_scene = {}
    for p in cfg.get("manifests", []):
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    source_of_log = json.load(open(cfg["folds"]))["source_of_log"] if cfg.get("folds") else {}
    folds_sha = G.sha(cfg["folds"]) if cfg.get("folds") else None
    results, k8res = {}, {}
    csv_dir = a.csv_dir or os.path.dirname(os.path.abspath(a.out))
    os.makedirs(csv_dir, exist_ok=True)
    for r in cfg["routes"]:
        for i, t in enumerate(TRACKERS):
            if t not in r["tags"]:
                continue
            runs, tag = r["runs"], r["tags"][t]
            rr = json.load(open(os.path.join(runs, "run_record_%s_decide.json" % tag)))
            dsets = [G.dataset_of_manifest(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in rr.get("caches", [])]
            if mode == "c1":
                assert rr.get("c1") is True and not rr.get("standin"), "run %s is not a C1 confirmatory run" % tag
                assert rr.get("c1_plan_sha256") == side and rr.get("c1_folds_sha256") == folds_sha, "run %s: plan or folds hash differs" % tag
                fj = json.load(open(r["fits"][t]))
                if r["name"] in ("transfer_lt3d", "source_transfer"):
                    assert fj.get("route") == "transfer" and fj.get("transfer_fit_source_sha256") in frozen.values() and                         fj.get("folds_sha256") == folds_sha, "transfer fits %s: source not bound or folds differ" % r["fits"][t]
                else:
                    prov = fj.get("provenance") or {}
                    assert prov.get("plan_sha256") == side and fj.get("folds_sha256") == folds_sha, "fits %s: provenance differs" % r["fits"][t]
                    for k_, h_ in (fj.get("code_sha256") or {}).items():
                        assert h_ in frozen.values(), "fit code %s is not bound" % k_
                assert rr["fits_sha256"] == G.sha(r["fits"][t]), "the fits are not the run's fits: " + tag
            else:
                assert not (rr.get("c1") and not rr.get("standin")), "--%s refuses C1 confirmatory run records (R17 M2)" % mode
                assert all(d_ == "nuscenes" for d_ in dsets), "--%s refuses runs on caches that are not nuScenes: %s" % (mode, dsets)
                if mode == "standin":
                    assert rr.get("c1") is True and rr.get("standin") is True, "run %s is not a stand-in run" % tag
            l_of = log_of_scene
            if cfg.get("units_are_logs"):
                l_of = {o["scene"]: o["scene"] for o in (json.loads(l) for l in open(os.path.join(runs, "episodes_%s_decide.jsonl" % tag)))}
            if mode == "c1":
                c_t = float(cfg["c"][t])
            else:
                c_t = float(cfg.get("c", B.C_DEFAULT)[t])
            out, res_small, res = B.analyse_route_tracker(r["name"], i, tag, runs, (r.get("fits") or {}).get(t), l_of, source_of_log, c_t,
                                                          a.boot, r.get("retuned_arm"))
            K.csv_tables_decide(res, "%s_%s" % (r["name"], t), csv_dir)
            results.setdefault(r["name"], {})[t] = out
            k8res.setdefault(r["name"], {})[t] = K.strip_csv_payload(res_small)
            del res
            print("%s %s: done %.0f s" % (r["name"], t, time.time() - t0), flush=True)
    dec = decide(results, cfg, mode)
    dec["binding"] = binding
    for path, obj in ((a.out, {"stamp": B.STAMPS[mode], "binding": binding, "c1": results, "k8": k8res}), (a.decision, dec)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f, indent=1, default=float)
    print(json.dumps({"C1_verdict": dec["C1_verdict"], "failed_conditions": dec["failed_conditions"][:12]}))
    print(B.STAMPS[mode])
    print("C1 ANALYSIS V03 DONE")


if __name__ == "__main__":
    main()
