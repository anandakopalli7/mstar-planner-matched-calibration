#!/usr/bin/env python3
"""C1 analysis v05 (Claude line, c1_analyse_v05, 4 Nov 2026) = c1_analyse_v03 (kept, imported: form_b, joint_b, joint_status,
per_scene_rates, holm and v02's per-route statistics unchanged) with D16 v13 Choices 33-35 and R17b's findings. c1_analyse_v04 is
superseded and not imported: its E0 check is re-implemented here under Choice 33.
  decide (Choice 33; R17b M-c)  GO <=> H1 holds with every input H1 needs present and provenance-valid (both trackers' within-AV2
        runs, their fits, folds, caches and chains, every comparator and arm); otherwise NO-GO, the reasons in "nogo_reasons" (also
        "failed_conditions", which now holds H1's conditions only). Every secondary claim (H2-H10) and Q1 gets a status: "holds",
        "does not hold" or "not tested" (an input missing or not provenance-valid, with the reason in "missing_inputs"). A claim not
        tested enters Holm's family S (fixed m = 5) with p = 1 and is never confirmed; it never changes GO. gate_H1 equals
        (verdict == GO) by construction and is asserted; no claim is "confirmed" unless the gate holds and the claim holds.
  H8 and E0 (Choice 31 under Choice 33; R17b M-c, m-6)  the config's e0 entry must record its inputs' hashes; the inputs are re-hashed
        (a change is reported as such), E0 is recomputed (c1_e0_v02, mode c1, the plan's seed) and compared bit for bit with the plan's
        values; the H8 table must carry E0_plan equal to the plan's values. Any failure makes H8 "not tested" with the reason; it no
        longer changes the verdict (Choice 31's NO-GO is replaced by Choice 33's rule, which governs every secondary input).
  H6-H9 tables (Choice 34.4; R17b B)  the config names their paths only; each is checked by provenance (c1_guard_v02.check_table): this
        plan, these folds, the plan's entry point for its role (entry:c1_mstage, entry:c1_h8, entry:c1_predarm) and bound code.
  H9 and H9-noHL (D16 v16 Choice 37)  H9 is the predictor-arm table's "H9" (c1_predarm_v03: history-length strata and HL cells in
        the family); its "H9_noHL" (D17-style strata) is reported as the descriptive claim "H9-noHL", never in family S.
  binding (Choice 34; R17b A, M-a, M-b, m-4)  --c1: the plan is read with c1_guard_v02 (40_PROTOCOL/C1_PLAN_HASH_LOG.txt; --hash-log
        only if the folds' units are nuScenes, and then every cache must be nuScenes), this file must be the plan's entry:c1_analyse,
        every loaded module bound (checked again before writing), the config bound as "config", the folds as "folds". Run records must
        carry c1_run_v03's provenance (entry:c1_run, cache chains, fits check); within fits c1_fit_v03's (entry:c1_fit, item chains);
        transfer fits must equal their bound source (role transfer_fits) in every fit entry. A failure of these makes that route
        "not provenance-valid" (H1: NO-GO; H4 and others: not tested). Other modes refuse confirmatory run records, run records
        without caches (R17b A3) and any cache or table that is not nuScenes. The decision records the entry point's hash.
Usage: python -B c1_analyse_v05.py --config <json> --out <json> --decision <json> (--c1 --plan <plan> | --standin | --reproduce | --smoke)
       [--csv-dir <dir>] [--hash-log <file>: nuScenes rehearsal only]
"""
import argparse
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v02 as G  # noqa: E402
import c1_analyse_v03 as B3  # noqa: E402
import c1_e0_v02 as E0  # noqa: E402

B, K = B3.B, B3.K
DELTA, TRACKERS, K_SET = B3.DELTA, B3.TRACKERS, B3.K_SET
FAMILY_S, REQUIRED_ARMS = B3.FAMILY_S, B3.REQUIRED_ARMS
ROLE = "entry:c1_analyse"
TABLE_ROLES = {"method_stage": "entry:c1_mstage", "h8": "entry:c1_h8", "h9": "entry:c1_predarm"}
RULE = ("D16 v13 Choice 33: GO iff H1 holds with every input H1 needs present and provenance-valid; a missing or unverifiable "
        "secondary input makes that claim 'not tested' (p = 1 in Holm's fixed m = 5, never confirmed) and does not change GO")


def _claim(store, name, label, status, reasons=(), **kw):
    assert status in ("holds", "does not hold", "not tested", "descriptive")
    store[name] = dict(kw, label=label, status=status, reasons=list(reasons))
    return store[name]


def holm_v05(claims, statuses, gate):
    full = B3.holm({c: v for c, v in claims.items() if statuses.get(c) != "not tested"}, 0.05, gate=gate)
    for c in FAMILY_S:
        st = statuses.get(c, "not tested")
        if st == "not tested":
            full[c] = dict(full[c], p=1.0, holds=False, rejected=False if gate else None, confirmed=False, status=st,
                           label="not tested (%s)" % "; ".join(statuses.get("_why_" + c, ["input missing"])))
        else:
            full[c]["status"] = st
            full[c].setdefault("confirmed", False)
        assert not full[c].get("confirmed") or (gate and st == "holds"), "a claim confirmed without the gate or without holding"
    return full


def decide(results, cfg, mode, aux=None):
    aux = aux or {}
    rp, tabs, e0 = aux.get("route_problems", {}), aux.get("tables", {}), aux.get("e0", {})
    nogo, missing, claims, pvals = [], [], {}, {}
    dec = {"stamp": B.STAMPS[mode], "delta": DELTA, "wording": B.WORDING, "rule": RULE, "hypotheses": {}}
    get = lambda route, t: results.get(route, {}).get(t)  # noqa: E731
    w = {t: get("within_lt3d", t) for t in TRACKERS}
    wording = {}
    for t in TRACKERS:
        if w[t] is None:
            why = rp.get("within_lt3d", {}).get(t, "the within-AV2 decision-mode run is missing")
            nogo.append("%s: %s" % (t, why))
            missing.append("H1 %s: %s" % (t, why))
            wording[t] = "missing"
            continue
        fb, st = w[t]["form_b"], w[t]["status"]
        miss_arms = [x for x in REQUIRED_ARMS if x not in st]
        if miss_arms:
            nogo.append("%s: arms missing from the run: %s" % (t, miss_arms))
            missing.append("H1 %s: arms %s" % (t, miss_arms))
        if fb["missing"]:
            nogo.append("%s: comparators missing (Form B fails, D16 Choice 25): %s" % (t, fb["missing"]))
            missing.append("H1 %s: comparators %s" % (t, fb["missing"]))
        sm = st.get("Mstar")
        if sm and not sm["valid"]:
            for p, r in sm["pops"].items():
                if not r["pooled_evaluable"]:
                    nogo.append("%s %s: M*'s pooled cell is not evaluable" % (t, p))
                for k_ in ("NoFlag", "Floor"):
                    if not r[k_]:
                        nogo.append("%s %s: M* %s fails" % (t, p, k_))
                if r["pooled_evaluable"] and not r["NoFlag_pool"]:
                    nogo.append("%s %s: M*'s pooled cell is shown above delta" % (t, p))
                if r["pooled_evaluable"] and not r["HK1c"]:
                    nogo.append("%s %s: M* HK1c fails" % (t, p))
                if r["FamFlag"]:
                    nogo.append("%s %s: M* family cell flagged" % (t, p))
        for c, v in fb["vs"].items():
            if not v["lower"]:
                nogo.append("%s: M* not less infeasible than %s%s" % (t, c, " (in V_t by Choice 9)" if c in fb["in_V_by_choice9"] else ""))
        if not fb["met"]:
            nogo.append("%s: Form B not met" % t)
        wording[t] = ("GO part met" if fb["met"] else "not shown above delta, operability not shown" if (sm and sm["valid"])
                      else "floor not met" if (sm and not sm["shown_above"]) else "M* shown above delta" if sm else "M* missing")
    h1 = all(w[t] is not None and w[t]["form_b"]["met"] and not [x for x in REQUIRED_ARMS if x not in w[t]["status"]] for t in TRACKERS)
    h1_untested = any(m.startswith("H1 ") for m in missing)
    dec["hypotheses"]["H1"] = {"label": "primary", "holds": bool(h1),
                               "status": "holds" if h1 else "not tested (input missing or not provenance-valid)" if h1_untested else "does not hold",
                               "by_tracker": {t: (w[t] or {}).get("form_b") for t in TRACKERS}, "wording_by_tracker": wording}
    gate = bool(h1)

    def not_tested(name, label, why):
        missing.append("%s: %s" % (name, why))
        _claim(claims, name, label, "not tested", [why])

    if all(w.values()):
        fc = {t: w[t]["form_c"] for t in TRACKERS}
        if all(fc.values()):
            h2 = all(fc[t]["met"] for t in TRACKERS)
            _claim(claims, "H2", "secondary", "holds" if h2 else "does not hold", by_tracker=fc)
            pvals["H2"] = {"p": max(fc[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h2}
        else:
            not_tested("H2", "secondary", "B4 is missing: Form C cannot be computed")
        if all("H3" in w[t] for t in TRACKERS):
            h3 = {t: w[t]["H3"] for t in TRACKERS}
            lq = {t: B3.lambda_qualified(r["fits"][t]) for r in cfg["routes"] if r["name"] == "within_lt3d" for t in TRACKERS if r.get("fits")}
            jmiss = {t: h3[t]["missing"] for t in TRACKERS if h3[t]["missing"]}
            if jmiss:
                not_tested("H3", "secondary", "joint comparators missing: %s" % jmiss)
            else:
                reasons = ["%s: M*Jx's lambda did not qualify in folds %s (D16 Choice 25)" % (t, bad) for t, (ok_, bad) in lq.items() if not ok_]
                gate3 = all(h3[t]["validJ_method"] for t in TRACKERS) and all(v[0] for v in lq.values()) and len(lq) == 2
                holds3 = gate3 and all(h3[t]["met"] for t in TRACKERS)
                pv = [h3[t]["p_rejection_bonferroni"] for t in TRACKERS]
                _claim(claims, "H3", "secondary", "holds" if holds3 else "does not hold", reasons, validity_gate=gate3, lambda_qualified=lq, by_tracker=h3)
                pvals["H3"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate3, "holds": holds3}
        else:
            not_tested("H3", "secondary", "M*Jx missing from the within-AV2 runs")
        h10 = {t: w[t].get("H10") for t in TRACKERS}
        if all(h10.values()):
            h10h = all(h10[t]["met"] for t in TRACKERS)
            _claim(claims, "H10", "secondary", "holds" if h10h else "does not hold", by_tracker=h10)
            pvals["H10"] = {"p": max(h10[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h10h}
        else:
            not_tested("H10", "secondary", "B6 or M* missing")
        dec["hypotheses"]["FormA"] = {"label": "descriptive", "by_tracker": {t: w[t]["form_a"] for t in TRACKERS}}
    else:
        for n in ("H2", "H3", "H10"):
            not_tested(n, "secondary", "a within-AV2 run is missing or not provenance-valid")
    tr = {t: get("transfer_lt3d", t) for t in TRACKERS}
    if all(tr.values()):
        miss4 = {t: tr[t]["form_b"]["missing"] for t in TRACKERS if tr[t]["form_b"]["missing"]}
        if miss4:
            not_tested("H4", "secondary", "comparators missing (RETUNED's transfer point is required): %s" % miss4)
        else:
            gate4 = all(tr[t]["form_b"]["valid_method"] for t in TRACKERS)
            h4 = all(tr[t]["form_b"]["met"] for t in TRACKERS)
            pv = [tr[t]["form_b"]["p_rejection_bonferroni"] for t in TRACKERS]
            _claim(claims, "H4", "secondary", "holds" if h4 else "does not hold", validity_gate=gate4, by_tracker={t: tr[t]["form_b"] for t in TRACKERS})
            pvals["H4"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate4, "holds": h4}
    else:
        why = "; ".join("%s: %s" % (t, rp.get("transfer_lt3d", {}).get(t, "missing")) for t in TRACKERS if tr[t] is None)
        not_tested("H4", "secondary", "the transfer route is missing or not provenance-valid (%s)" % why)
    for route, hn in (("voxelnext_val", "H5"), ("public_lt3d_val", "H1-P"), ("source_transfer", "source_transfer")):
        rr_ = {t: get(route, t) for t in TRACKERS}
        if all(rr_.values()):
            _claim(claims, hn, "descriptive", "descriptive", holds_as_formula=all(rr_[t]["form_b"]["met"] for t in TRACKERS),
                   by_tracker={t: rr_[t]["form_b"] for t in TRACKERS})
    ms = tabs.get("method_stage")
    if ms and ms.get("ok"):
        h6 = {t: B.h6_rules(ms["data"][t]) for t in TRACKERS}
        h7 = {t: B.h7_rule(ms["data"][t]) for t in TRACKERS}
        h6b = all(h6[t]["H6b"] for t in TRACKERS)
        _claim(claims, "H6a", "secondary (no-flag)", "holds" if all(h6[t]["H6a"] for t in TRACKERS) else "does not hold", by_tracker=h6)
        _claim(claims, "H6b", "secondary", "holds" if h6b else "does not hold")
        pv = [h6[t]["H6b_p"] for t in TRACKERS]
        pvals["H6b"] = {"p": max(pv) if all(p is not None for p in pv) else None, "gate_ok": True, "holds": h6b}
        _claim(claims, "H7", "secondary (no-flag)", "holds" if all(h7[t]["H7"] for t in TRACKERS) else "does not hold", by_tracker=h7)
        dec["hypotheses"]["method_stage_provenance"] = ms["checks"]
    else:
        why = (ms or {}).get("why", "the method-stage tables are missing")
        for n, lab in (("H6a", "secondary (no-flag)"), ("H6b", "secondary"), ("H7", "secondary (no-flag)")):
            not_tested(n, lab, why)
    h8 = tabs.get("h8")
    if h8 and h8.get("ok") and e0.get("ok"):
        t8 = h8["data"]
        plan_e0 = e0["plan"]
        if t8.get("E0_plan") is None or any(t8["E0_plan"].get(c) != plan_e0[c] for c in E0.DECISION_CELLS):
            not_tested("H8", "secondary, family P at 0.05", "the H8 table used E0 values other than the plan's (D16 Choice 31)")
        else:
            _claim(claims, "H8", "secondary, family P at 0.05 (%s)" % h8["checks"]["entry_point"], "holds" if t8["H8"] else "does not hold",
                   bins=t8.get("bins"), cells=t8.get("cells"), thresholds=t8.get("thresholds"), E0_plan=t8.get("E0_plan"))
    else:
        why = (h8 or {}).get("why", "the H8 table is missing") if not (h8 and h8.get("ok")) else "E0: " + str(e0.get("reason"))
        not_tested("H8", "secondary, family P at 0.05", why)
    h9 = tabs.get("h9")
    h9_label = cfg.get("h9_label", "secondary")
    if h9 and h9.get("ok"):
        d9 = h9["data"]
        st9 = "holds" if all(v.get("H9") for v in d9.values()) else "does not hold"
        _claim(claims, "H9", "%s (no-flag, floor 6)" % h9_label, st9 if h9_label == "secondary" else "descriptive",
               holds_as_formula=st9 == "holds", population=next(iter(d9.values())).get("population"),
               by_tracker={t: v["arms"].get("TPP") for t, v in d9.items()})
        if all("H9_noHL" in v for v in d9.values()):
            _claim(claims, "H9-noHL", "descriptive (D17-style strata without history length; D16 v16 Choice 37)", "descriptive",
                   holds_as_formula=all(v["H9_noHL"] for v in d9.values()))
        q1 = {t: {k: v["arms"][k] for k in ("Q1_deployed", "Q1_gt") if k in v["arms"]} for t, v in d9.items()}
        if any(q1.values()):
            _claim(claims, "Q1", "descriptive (Choice 20; never in family S)", "descriptive", by_tracker=q1)
    else:
        why = (h9 or {}).get("why", "the predictor-arm tables are missing")
        if h9_label == "secondary":
            not_tested("H9", "secondary (no-flag, floor 6)", why)
        else:
            missing.append("H9 (descriptive): %s" % why)
    statuses = {c: claims.get(c, {}).get("status", "not tested") for c in FAMILY_S}
    statuses.update({"_why_" + c: claims[c]["reasons"] for c in FAMILY_S if c in claims})
    dec["family_S"] = holm_v05(pvals, statuses, gate)
    dec["hypotheses"].update(claims)
    dec["claims_status"] = {c: v["status"] for c, v in claims.items()}
    dec["C1_verdict"] = "GO" if h1 else "NO-GO"
    dec["gate_H1"] = gate
    dec["nogo_reasons"] = [] if h1 else nogo
    dec["failed_conditions"] = dec["nogo_reasons"]
    dec["missing_inputs"] = missing
    dec["not_tested"] = sorted(c for c, v in claims.items() if v["status"] == "not tested")
    dec["E0_check"] = e0
    assert dec["gate_H1"] == (dec["C1_verdict"] == "GO") and (h1 or dec["nogo_reasons"]), "inconsistent decision record"
    return dec


def e0_check(cfg, mode, frozen=None):
    e = cfg.get("e0")
    if not e:
        return {"present": False, "ok": False, "reason": "no e0 entry in the config (D16 Choice 31)"}
    i = e["inputs"]
    if float(e.get("sigma_a", E0.PRIMARY_SIGMA)) != E0.PRIMARY_SIGMA:
        return {"present": True, "ok": False, "reason": "sigma_a is not 0.10 m"}
    rec = e.get("inputs_sha256")
    if not rec:
        return {"present": True, "ok": False, "reason": "the config records no E0 input hashes (R17b m-6)"}
    now = E0.input_hashes(i["workers"], i["gt"], i["meta"], i["horizon"])
    if now != rec:
        return {"present": True, "ok": False, "inputs_equal": False, "reason": "E0 inputs changed: %s" % sorted(k for k in set(now) | set(rec) if now.get(k) != rec.get(k))}
    if frozen is not None:
        try:
            G.check_inputs(frozen, E0.input_files(i["workers"], i["gt"], i["horizon"]))
        except AssertionError as ex:
            return {"present": True, "ok": False, "inputs_equal": True, "reason": "E0 inputs not bound: %s" % ex}
    val = E0.compute(i["workers"], i["gt"], i["meta"], i["horizon"], "c1", int(e["seed"]))["H8_E0_primary"]
    plan = {c: e["plan_values"].get(c) for c in E0.DECISION_CELLS}
    match = all(plan[c] is not None and val[c] == plan[c] for c in E0.DECISION_CELLS)
    return {"present": True, "inputs_equal": True, "match": bool(match), "ok": bool(match), "recomputed": val, "plan": plan,
            "seed": int(e["seed"]), "reason": None if match else "the recomputed E0 %s differs from the plan's %s" % (val, plan)}


def load_table(key, cfg, mode, side, frozen, folds_sha):
    ent = cfg.get(key)
    if not ent:
        return None
    multi = isinstance(ent, dict) and "path" not in ent
    paths = ent if multi else {"_": ent if isinstance(ent, str) else ent["path"]}
    if multi:
        paths = {t: (e if isinstance(e, str) else e["path"]) for t, e in ent.items()}
        if set(paths) != set(TRACKERS):
            return {"ok": False, "why": "%s: tables for %s, not for both trackers" % (key, sorted(paths))}
    data, checks = {}, {}
    for t, p in paths.items():
        if not os.path.exists(p):
            return {"ok": False, "why": "%s %s: no file %s" % (key, t, p)}
        d = json.load(open(p))
        try:
            if mode == "c1":
                checks[t] = G.check_table(d, side, frozen, folds_sha, TABLE_ROLES[key])
            else:
                ds = (d.get("provenance") or {}).get("dataset")
                assert ds in ("nuscenes", "synthetic"), "--%s accepts nuScenes or synthetic tables only, not %s" % (mode, ds)
                checks[t] = {"entry_point": list((d.get("provenance") or {}).get("entry_point", {"(none)": None}))[0]}
        except AssertionError as ex:
            return {"ok": False, "why": "%s %s: not provenance-valid: %s" % (key, t, ex)}
        data[t] = d
    if not multi:
        return {"ok": True, "data": data["_"], "checks": checks["_"]}
    return {"ok": True, "data": data, "checks": checks}


def transfer_equals_source(fj, frozen):
    h = fj.get("transfer_fit_source_sha256")
    srcs = [p for p in (frozen.roles or {}).get("transfer_fits", []) if frozen.get(p) == h]
    assert srcs, "the transfer fit's source is not bound as transfer_fits"
    src = json.load(open(os.path.join(G.W, srcs[0])))
    for k in ("fits", "joint", "retuned_transfer_arm", "transfer_source_units", "transfer_source_folds_sha256"):
        assert fj.get(k) == src.get(k), "applied transfer fit differs from its bound source in " + k
    return srcs[0]


def check_route_c1(rr, r, t, side, frozen, folds_sha):
    tag = r["tags"][t]
    assert rr.get("c1") is True and not rr.get("standin"), "run %s is not a C1 confirmatory run" % tag
    assert rr.get("c1_plan_sha256") == side and rr.get("c1_folds_sha256") == folds_sha, "run %s: plan or folds hash differs" % tag
    caches = rr.get("caches") or []
    assert caches, "run %s records no caches (R17b A3)" % tag
    pv = rr.get("provenance_v03") or {}
    ep = pv.get("entry_point") or {}
    assert pv.get("plan_sha256") == side and len(ep) == 1, "run %s carries no c1_run_v03 provenance under this plan" % tag
    p, h = list(ep.items())[0]
    assert (frozen.roles or {}).get("entry:c1_run") == [p] and frozen.get(p) == h, "run %s was not made by the plan's entry:c1_run" % tag
    bad = [q for q, x in (pv.get("code_sha256") or {}).items() if frozen.get(q) != x]
    assert pv.get("code_sha256") and not bad, "run %s: code not bound %s" % (tag, bad)
    assert len(pv.get("cache_chains") or []) == len(caches), "run %s: caches without a chain" % tag
    fits = r["fits"][t]
    assert rr["fits_sha256"] == G.sha(fits), "the fits are not the run's fits: " + tag
    fj = json.load(open(fits))
    assert fj.get("folds_sha256") == folds_sha, "fits %s: folds differ" % fits
    if r["name"] in ("transfer_lt3d", "source_transfer"):
        assert fj.get("route") == "transfer", "fits %s: not a transfer fit" % fits
        src = transfer_equals_source(fj, frozen)
        return {"run_entry": p, "fits": "transfer from " + src, "caches": [c["dataset"] for c in pv["cache_chains"]]}
    prov = fj.get("provenance") or {}
    fe = prov.get("entry_point") or {}
    assert prov.get("plan_sha256") == side and len(fe) == 1, "fits %s: provenance differs" % fits
    q, hq = list(fe.items())[0]
    assert (frozen.roles or {}).get("entry:c1_fit") == [q] and frozen.get(q) == hq, "fits %s were not made by the plan's entry:c1_fit" % fits
    badf = [x for x, y in (prov.get("code_sha256") or {}).items() if frozen.get(x) != y]
    assert prov.get("code_sha256") and not badf, "fit code not bound: %s" % badf
    assert prov.get("inputs_checked") is True and prov.get("item_chains"), "fits %s: items not chained to the plan" % fits
    return {"run_entry": p, "fits_entry": q, "caches": [c["dataset"] for c in pv["cache_chains"]]}


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
    ds_units = G.dataset_checked(fj.get("dataset"), list(fj["fold_of_log"])) if fj else "unknown"
    side = frozen = rt = None
    if mode == "c1":
        assert a.plan, "--c1 needs --plan"
        side, frozen, rt = G.guard(ds_units, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        G.require_bound(frozen, a.config, "config")
        folds_sha = G.require_bound(frozen, cfg["folds"], "folds")
        assert "c" in cfg, "--c1: c must be stated in the frozen config (R16 m1, R17 m9)"
    else:
        assert a.plan is None and a.hash_log is None, "--%s runs without a plan or a hash log" % mode
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha = G.sha(cfg["folds"]) if cfg.get("folds") else None
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "plan_sha256": side, "entry_point": rt["entry_point"],
               "code_sha256": rt["code_sha256"], "folds_sha256": folds_sha, "hash_log": G.rel(a.hash_log) if a.hash_log else "canonical"}
    aux = {"route_problems": {}, "tables": {k: load_table(k, cfg, mode, side, frozen, folds_sha) for k in TABLE_ROLES}}
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
        for i, t in enumerate(TRACKERS):
            if t not in r["tags"]:
                continue
            runs, tag = r["runs"], r["tags"][t]
            rp = os.path.join(runs, "run_record_%s_decide.json" % tag)
            if not os.path.exists(rp):
                aux["route_problems"].setdefault(r["name"], {})[t] = "no run record " + rp
                continue
            rr = json.load(open(rp))
            caches = rr.get("caches") or []
            dsets = [G.manifest_dataset(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in caches]
            if mode == "c1":
                if a.hash_log:
                    assert caches and all(d_ == "nuscenes" for d_ in dsets), "a rehearsal hash log with caches that are not nuScenes: refused"
                try:
                    route_checks.setdefault(r["name"], {})[t] = check_route_c1(rr, r, t, side, frozen, folds_sha)
                except AssertionError as ex:
                    aux["route_problems"].setdefault(r["name"], {})[t] = "not provenance-valid: %s" % ex
                    continue
            else:
                assert not (rr.get("c1") and not rr.get("standin")), "--%s refuses C1 confirmatory run records (R17 M2)" % mode
                assert caches, "--%s refuses a run record without caches (R17b A3)" % mode
                assert all(d_ == "nuscenes" for d_ in dsets), "--%s refuses runs on caches that are not nuScenes: %s" % (mode, dsets)
                if mode == "standin":
                    assert rr.get("c1") is True and rr.get("standin") is True, "run %s is not a stand-in run" % tag
            l_of = log_of_scene
            if cfg.get("units_are_logs"):
                l_of = {o["scene"]: o["scene"] for o in (json.loads(l) for l in open(os.path.join(runs, "episodes_%s_decide.jsonl" % tag)))}
            c_t = float(cfg["c"][t]) if mode == "c1" else float(cfg.get("c", B.C_DEFAULT)[t])
            out, res_small, res = B.analyse_route_tracker(r["name"], i, tag, runs, (r.get("fits") or {}).get(t), l_of, source_of_log, c_t,
                                                          a.boot, r.get("retuned_arm"))
            K.csv_tables_decide(res, "%s_%s" % (r["name"], t), csv_dir)
            results.setdefault(r["name"], {})[t] = out
            k8res.setdefault(r["name"], {})[t] = K.strip_csv_payload(res_small)
            del res
            print("%s %s: done %.0f s" % (r["name"], t, time.time() - t0), flush=True)
    dec = decide(results, cfg, mode, aux)
    if mode == "c1":
        rt = G.verify_runtime_again(frozen, rt)
        binding["code_sha256"] = rt["code_sha256"]
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
    print(json.dumps({"C1_verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"][:8],
                      "not_tested": dec["not_tested"], "claims": dec["claims_status"]}, default=str))
    print(B.STAMPS[mode])
    print("C1 ANALYSIS V05 DONE")


if __name__ == "__main__":
    main()
