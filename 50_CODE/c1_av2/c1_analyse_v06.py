#!/usr/bin/env python3
"""C1 analysis v06 (Claude line, c1_analyse_v06, 4 Nov 2026) = c1_analyse_v05 (kept, imported: holm_v05, transfer_equals_source; Choice 33's
rule unchanged) on c1_guard_v03, with R17c's fixes and D16 v17 Choice 38 / v18 Choice 39:
  M2  (Choice 39d) every secondary input, route and claim block runs under `except Exception`: a failure of any type makes that claim
      "not tested" with the exception text; any failure on an H1 input (the within_lt3d route of T1 or T3, or H1's own block) makes the
      decision NO-GO with the reason. e0_check and every table load are wrapped the same way. The decision is always written.
  M4  tables are checked by c1_guard_v03.check_table with their unit lists: method stage and predictor arm = the bound folds' units, H8
      = a non-empty subset of them (the ground truth's scenes, checked against the exports by c1_h8_v04), dataset = the folds'
      dataset, the current hash log. H9's primary table must come from seed 20261102 (its recorded and verified run seed).
  m1  an H9 table without a TPP arm (no "H9" key) gives H9 "not tested".  m2  E0's seed must be 20261114 (mode c1).
  m3  every run cache's dataset must equal the folds' dataset.  m5  versions are asserted by the guard (FROZEN_ENV) under --c1.
  38b H9_seed_robustness (descriptive, outside family S, never read by claims["H9"]): "seed-robust" if H9 holds under 20261102, 20261104
      and 20261105 on both trackers; "not seed-robust" otherwise; "not tested" if any seed's result is missing or invalid.
  38c DESCRIPTIVE_TRACKERS = ("tab",) (AB3DMOT): its routes run with tracker index 2 and are stored in results_descriptive; decide()
      receives only T1 and T3 results (asserted) and never reads the descriptive block; its tables use the separate config keys
      method_stage_descriptive and h9_descriptive; the block is labelled "descriptive (Choice 38c; outside H1 and family S)".
  38d expected folds role per route: within_lt3d and transfer_lt3d "folds"; voxelnext_val, public_lt3d_val and source_transfer
      "folds_val150" (a restriction of the bound parent, verified); source_transfer's fit is a "source" fit by the plan's entry:c1_fit,
      trained on exactly the folds_train225 units and applied to the folds_val150 units. H5 and H1-P are "not tested" when missing.
Usage: as c1_analyse_v05.
"""
import argparse
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v03 as G  # noqa: E402
import c1_analyse_v05 as A5  # noqa: E402
import c1_e0_v03 as E0  # noqa: E402

B3, B, K = A5.B3, A5.B, A5.K
DELTA, TRACKERS, FAMILY_S, REQUIRED_ARMS = A5.DELTA, A5.TRACKERS, A5.FAMILY_S, A5.REQUIRED_ARMS
DESCRIPTIVE_TRACKERS = ("tab",)
ROLE = "entry:c1_analyse"
TABLE_ROLES = {"method_stage": "entry:c1_mstage", "h8": "entry:c1_h8", "h9": "entry:c1_predarm"}
DESC_TABLES = {"method_stage_descriptive": "entry:c1_mstage", "h9_descriptive": "entry:c1_predarm"}
ROUTE_FOLDS_ROLE = {"within_lt3d": "folds", "transfer_lt3d": "folds", "voxelnext_val": "folds_val150", "public_lt3d_val": "folds_val150",
                    "source_transfer": "folds_val150"}
PRIMARY_SEED, ROBUST_SEEDS = 20261102, (20261104, 20261105)
DESC_LABEL = "descriptive (Choice 38c; outside H1 and family S)"
RULE = A5.RULE + "; any exception on a secondary input makes it 'not tested', on an H1 input NO-GO (R17c M2)"
_claim = A5._claim


def _exc(ex):
    return "%s: %s" % (type(ex).__name__, str(ex)[:300])


def decide(results, cfg, mode, aux=None):
    aux = aux or {}
    assert all(set(v) <= set(TRACKERS) for v in results.values()), "decide() reads T1 and T3 only (Choice 38c)"
    rp, tabs, e0 = aux.get("route_problems", {}), aux.get("tables", {}), aux.get("e0", {})
    nogo, missing, claims, pvals = [], [], {}, {}
    dec = {"stamp": B.STAMPS[mode], "delta": DELTA, "wording": B.WORDING, "rule": RULE, "hypotheses": {}}
    get = lambda route, t: results.get(route, {}).get(t)  # noqa: E731
    w = {t: get("within_lt3d", t) for t in TRACKERS}

    def not_tested(name, label, why):
        missing.append("%s: %s" % (name, why))
        _claim(claims, name, label, "not tested", [why])

    def block(names, label, fn):
        try:
            fn()
        except Exception as ex:
            for n in names:
                claims.pop(n, None)
                pvals.pop(n, None)
                not_tested(n, label, "exception: " + _exc(ex))

    h1 = False
    try:
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
    except Exception as ex:
        h1 = False
        nogo.append("H1: exception on an H1 input: " + _exc(ex))
        dec["hypotheses"]["H1"] = {"label": "primary", "holds": False, "status": "not tested (exception)", "exception": _exc(ex)}
    gate = bool(h1)

    if all(w.values()):
        def b_h2():
            fc = {t: w[t]["form_c"] for t in TRACKERS}
            if all(fc.values()):
                h2 = all(fc[t]["met"] for t in TRACKERS)
                _claim(claims, "H2", "secondary", "holds" if h2 else "does not hold", by_tracker=fc)
                pvals["H2"] = {"p": max(fc[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h2}
            else:
                not_tested("H2", "secondary", "B4 is missing: Form C cannot be computed")

        def b_h3():
            if all("H3" in w[t] for t in TRACKERS):
                h3 = {t: w[t]["H3"] for t in TRACKERS}
                lq = {t: B3.lambda_qualified(r["fits"][t]) for r in cfg["routes"] if r["name"] == "within_lt3d" for t in TRACKERS if r.get("fits")}
                jmiss = {t: h3[t]["missing"] for t in TRACKERS if h3[t]["missing"]}
                if jmiss:
                    not_tested("H3", "secondary", "joint comparators missing: %s" % jmiss)
                    return
                reasons = ["%s: M*Jx's lambda did not qualify in folds %s (D16 Choice 25)" % (t, bad) for t, (ok_, bad) in lq.items() if not ok_]
                gate3 = all(h3[t]["validJ_method"] for t in TRACKERS) and all(v[0] for v in lq.values()) and len(lq) == 2
                holds3 = gate3 and all(h3[t]["met"] for t in TRACKERS)
                pv = [h3[t]["p_rejection_bonferroni"] for t in TRACKERS]
                _claim(claims, "H3", "secondary", "holds" if holds3 else "does not hold", reasons, validity_gate=gate3, lambda_qualified=lq, by_tracker=h3)
                pvals["H3"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate3, "holds": holds3}
            else:
                not_tested("H3", "secondary", "M*Jx missing from the within-AV2 runs")

        def b_h10():
            h10 = {t: w[t].get("H10") for t in TRACKERS}
            if all(h10.values()):
                h10h = all(h10[t]["met"] for t in TRACKERS)
                _claim(claims, "H10", "secondary", "holds" if h10h else "does not hold", by_tracker=h10)
                pvals["H10"] = {"p": max(h10[t]["p"] for t in TRACKERS), "gate_ok": True, "holds": h10h}
            else:
                not_tested("H10", "secondary", "B6 or M* missing")
        block(["H2"], "secondary", b_h2)
        block(["H3"], "secondary", b_h3)
        block(["H10"], "secondary", b_h10)
        try:
            dec["hypotheses"]["FormA"] = {"label": "descriptive", "by_tracker": {t: w[t]["form_a"] for t in TRACKERS}}
        except Exception as ex:
            missing.append("FormA: exception: " + _exc(ex))
    else:
        for n in ("H2", "H3", "H10"):
            not_tested(n, "secondary", "a within-AV2 run is missing or not provenance-valid")

    def b_h4():
        tr = {t: get("transfer_lt3d", t) for t in TRACKERS}
        if all(tr.values()):
            miss4 = {t: tr[t]["form_b"]["missing"] for t in TRACKERS if tr[t]["form_b"]["missing"]}
            if miss4:
                not_tested("H4", "secondary", "comparators missing (RETUNED's transfer point is required): %s" % miss4)
                return
            gate4 = all(tr[t]["form_b"]["valid_method"] for t in TRACKERS)
            h4 = all(tr[t]["form_b"]["met"] for t in TRACKERS)
            pv = [tr[t]["form_b"]["p_rejection_bonferroni"] for t in TRACKERS]
            _claim(claims, "H4", "secondary", "holds" if h4 else "does not hold", validity_gate=gate4, by_tracker={t: tr[t]["form_b"] for t in TRACKERS})
            pvals["H4"] = {"p": None if any(p is None for p in pv) else max(pv), "gate_ok": gate4, "holds": h4}
        else:
            why = "; ".join("%s: %s" % (t, rp.get("transfer_lt3d", {}).get(t, "missing")) for t in TRACKERS if tr[t] is None)
            not_tested("H4", "secondary", "the transfer route is missing or not provenance-valid (%s)" % why)
    block(["H4"], "secondary", b_h4)
    for route, hn in (("voxelnext_val", "H5"), ("public_lt3d_val", "H1-P"), ("source_transfer", "source_transfer")):
        def b_desc(route=route, hn=hn):
            rr_ = {t: get(route, t) for t in TRACKERS}
            if all(rr_.values()):
                _claim(claims, hn, "descriptive", "descriptive", holds_as_formula=all(rr_[t]["form_b"]["met"] for t in TRACKERS),
                       by_tracker={t: rr_[t]["form_b"] for t in TRACKERS})
            else:
                why = "; ".join("%s: %s" % (t, rp.get(route, {}).get(t, "not run")) for t in TRACKERS if rr_[t] is None)
                not_tested(hn, "descriptive", "route %s missing or not provenance-valid (%s; Choice 38d)" % (route, why))
        block([hn], "descriptive", b_desc)

    def b_ms():
        ms = tabs.get("method_stage")
        if ms and ms.get("ok"):
            h6 = {t: B.h6_rules(ms["data"][t]) for t in TRACKERS}
            h7 = {t: B.h7_rule(ms["data"][t]) for t in TRACKERS}
            h6b = all(h6[t]["H6b"] for t in TRACKERS)
            pv = [h6[t]["H6b_p"] for t in TRACKERS]
            _claim(claims, "H6a", "secondary (no-flag)", "holds" if all(h6[t]["H6a"] for t in TRACKERS) else "does not hold", by_tracker=h6)
            _claim(claims, "H6b", "secondary", "holds" if h6b else "does not hold")
            pvals["H6b"] = {"p": max(pv) if all(p is not None for p in pv) else None, "gate_ok": True, "holds": h6b}
            _claim(claims, "H7", "secondary (no-flag)", "holds" if all(h7[t]["H7"] for t in TRACKERS) else "does not hold", by_tracker=h7)
            dec["hypotheses"]["method_stage_provenance"] = ms["checks"]
        else:
            why = (ms or {}).get("why", "the method-stage tables are missing")
            for n, lab in (("H6a", "secondary (no-flag)"), ("H6b", "secondary"), ("H7", "secondary (no-flag)")):
                not_tested(n, lab, why)
    try:
        b_ms()
    except Exception as ex:
        pvals.pop("H6b", None)
        for n, lab in (("H6a", "secondary (no-flag)"), ("H6b", "secondary"), ("H7", "secondary (no-flag)")):
            claims.pop(n, None)
            not_tested(n, lab, "exception: " + _exc(ex))

    def b_h8():
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
    block(["H8"], "secondary, family P at 0.05", b_h8)
    h9_label = cfg.get("h9_label", "secondary")

    def b_h9():
        h9 = tabs.get("h9")
        if h9 and h9.get("ok"):
            d9 = h9["data"]
            if not all("H9" in v for v in d9.values()):
                if h9_label == "secondary":
                    not_tested("H9", "secondary (no-flag, floor 6 E2 cells)", "a predictor-arm table has no TPP arm (no run given; R17c m1)")
                else:
                    missing.append("H9 (descriptive): a table has no TPP arm")
                return
            st9 = "holds" if all(v["H9"] for v in d9.values()) else "does not hold"
            _claim(claims, "H9", "%s (no-flag, floor 6 E2 cells + HL cells; Choices 37, 39b)" % h9_label, st9 if h9_label == "secondary" else "descriptive",
                   holds_as_formula=st9 == "holds", population=next(iter(d9.values())).get("population"),
                   by_tracker={t: (v["arms"].get("TPP") or {}).get("PD", {}).get("HL") for t, v in d9.items()})
            q1 = {t: {k: v["arms"][k] for k in ("Q1_deployed", "Q1_gt") if k in v["arms"]} for t, v in d9.items()}
            if any(q1.values()):
                _claim(claims, "Q1", "descriptive (Choice 20; never in family S)", "descriptive", by_tracker=q1)
        else:
            why = (h9 or {}).get("why", "the predictor-arm tables are missing")
            if h9_label == "secondary":
                not_tested("H9", "secondary (no-flag, floor 6 E2 cells)", why)
            else:
                missing.append("H9 (descriptive): %s" % why)
    block(["H9", "Q1"], "secondary (no-flag, floor 6 E2 cells)", b_h9)

    def b_h9nohl():
        h9 = tabs.get("h9")
        d9 = (h9 or {}).get("data") if (h9 or {}).get("ok") else None
        if d9 and all("H9_noHL" in v for v in d9.values()):
            _claim(claims, "H9-noHL", "descriptive (D17-style strata without history length; D16 v16 Choice 37)", "descriptive",
                   holds_as_formula=all(v["H9_noHL"] for v in d9.values()))
        else:
            not_tested("H9-noHL", "descriptive (Choice 37)", "no valid predictor-arm table with H9_noHL")
    block(["H9-noHL"], "descriptive (Choice 37)", b_h9nohl)

    def b_seed():
        h9 = tabs.get("h9")
        d9 = (h9 or {}).get("data") if (h9 or {}).get("ok") else None
        want = [str(PRIMARY_SEED)] + [str(s) for s in ROBUST_SEEDS]
        if d9 and all(all(s in (v.get("H9_seed") or {}) for s in want) for v in d9.values()):
            robust = all(all(v["H9_seed"][s] for s in want) for v in d9.values())
            _claim(claims, "H9_seed_robustness", "descriptive (Choice 38b; outside family S; never changes H9)", "descriptive",
                   label_value="seed-robust" if robust else "not seed-robust", by_tracker={t: v["H9_seed"] for t, v in d9.items()})
        else:
            not_tested("H9_seed_robustness", "descriptive (Choice 38b)", "a seed's H9 result is missing or its table is not valid")
    block(["H9_seed_robustness"], "descriptive (Choice 38b)", b_seed)
    statuses = {c: claims.get(c, {}).get("status", "not tested") for c in FAMILY_S}
    statuses.update({"_why_" + c: claims[c]["reasons"] for c in FAMILY_S if c in claims})
    dec["family_S"] = A5.holm_v05(pvals, statuses, gate)
    assert sorted(dec["family_S"]) == sorted(FAMILY_S), "family S must be exactly H2, H3, H4, H6b, H10"
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


def descriptive_block(results_descriptive, tabs_desc):
    """Choice 38c: AB3DMOT (and any descriptive tracker): Form B, validity and trade-off rows, never read by decide()."""
    out = {"label": DESC_LABEL, "trackers": list(DESCRIPTIVE_TRACKERS), "routes": {}, "tables": {}}
    for route, by_t in results_descriptive.items():
        for t, r in by_t.items():
            try:
                out["routes"].setdefault(route, {})[t] = {"form_b": r.get("form_b"), "Mstar_valid": (r.get("status") or {}).get("Mstar", {}).get("valid"),
                                                          "form_a": r.get("form_a"), "form_c": r.get("form_c")}
            except Exception as ex:
                out["routes"].setdefault(route, {})[t] = {"exception": _exc(ex)}
    for k, v in (tabs_desc or {}).items():
        out["tables"][k] = {"ok": (v or {}).get("ok"), "why": (v or {}).get("why"),
                            "H9": {t: d.get("H9") for t, d in ((v or {}).get("data") or {}).items()} if k == "h9_descriptive" and (v or {}).get("ok") else None}
    return out


def decide_all(results_all, cfg, mode, aux):
    """main()'s split: decide() gets T1 and T3 only; the descriptive trackers go to their own block."""
    prim = {r: {t: v for t, v in by.items() if t in TRACKERS} for r, by in results_all.items()}
    desc = {r: {t: v for t, v in by.items() if t in DESCRIPTIVE_TRACKERS} for r, by in results_all.items()}
    dec = decide(prim, cfg, mode, aux)
    dec["descriptive_trackers"] = descriptive_block({r: v for r, v in desc.items() if v}, aux.get("tables_descriptive"))
    return dec


def e0_check(cfg, mode, frozen=None):
    try:
        e = cfg.get("e0")
        if e and int(e.get("seed", -1)) != E0.SEED:
            return {"present": True, "ok": False, "reason": "E0's seed must be %d (R17c m2), not %s" % (E0.SEED, e.get("seed"))}
        return A5.e0_check(cfg, mode, frozen)
    except Exception as ex:
        return {"present": bool(cfg.get("e0")), "ok": False, "reason": "exception: " + _exc(ex)}


def load_table(key, role, cfg, mode, side, frozen, folds_sha, trackers, units, ds):
    try:
        ent = cfg.get(key)
        if not ent:
            return None
        multi = isinstance(ent, dict) and "path" not in ent
        if multi:
            paths = {t: (e if isinstance(e, str) else e["path"]) for t, e in ent.items()}
            if set(paths) != set(trackers):
                return {"ok": False, "why": "%s: tables for %s, not for %s" % (key, sorted(paths), list(trackers))}
        else:
            paths = {"_": ent if isinstance(ent, str) else ent["path"]}
        data, checks = {}, {}
        for t, p in paths.items():
            if not os.path.exists(p):
                return {"ok": False, "why": "%s %s: no file %s" % (key, t, p)}
            d = json.load(open(p))
            if mode == "c1":
                if role == "entry:c1_h8":
                    checks[t] = G.check_table(d, side, frozen, folds_sha, role, units_subset_of=units, dataset=ds)
                else:
                    checks[t] = G.check_table(d, side, frozen, folds_sha, role, units=units, dataset=ds)
                if role == "entry:c1_predarm":
                    sd = (d.get("provenance") or {}).get("seeds") or {}
                    assert (sd.get("trk") or {}).get("seed") == PRIMARY_SEED and (sd.get("trk") or {}).get("verified") is True, \
                        "H9's primary table is not from the verified seed %d (R17c M4)" % PRIMARY_SEED
                    rc = ((d.get("provenance") or {}).get("chains") or {}).get("runs", {}).get("trk", {})
                    assert rc.get("seed") == PRIMARY_SEED, "the primary run's chained summary seed is not %d" % PRIMARY_SEED
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


def check_route_c1(rr, r, t, side, frozen, fds):
    tag = r["tags"][t]
    role = ROUTE_FOLDS_ROLE.get(r["name"])
    assert role, "route %s has no expected folds role" % r["name"]
    fpath, fsha = G.role_hash(frozen, role)
    if role != "folds":
        G.check_child_folds(os.path.join(G.W, fpath), frozen)
    assert rr.get("c1") is True and not rr.get("standin"), "run %s is not a C1 confirmatory run" % tag
    assert rr.get("c1_plan_sha256") == side and rr.get("c1_folds_sha256") == fsha, "run %s: plan or folds hash differs (expected role %s)" % (tag, role)
    caches = rr.get("caches") or []
    assert caches, "run %s records no caches (R17b A3)" % tag
    pv = rr.get("provenance_v04") or {}
    ep = pv.get("entry_point") or {}
    assert pv.get("plan_sha256") == side and len(ep) == 1, "run %s carries no c1_run_v04 provenance under this plan" % tag
    p, h = list(ep.items())[0]
    assert (frozen.roles or {}).get("entry:c1_run") == [p] and frozen.get(p) == h, "run %s was not made by the plan's entry:c1_run" % tag
    bad = [q for q, x in (pv.get("code_sha256") or {}).items() if frozen.get(q) != x]
    assert pv.get("code_sha256") and not bad, "run %s: code not bound %s" % (tag, bad)
    ch = pv.get("cache_chains") or []
    assert len(ch) == len(caches), "run %s: caches without a chain" % tag
    assert all(c["dataset"] == fds for c in ch), "run %s: a cache's dataset differs from the folds' (R17c m3)" % tag
    assert pv.get("hash_log_sha256") == frozen.log_sha256, "run %s made under another state of the hash log" % tag
    fits = r["fits"][t]
    assert rr["fits_sha256"] == G.sha(fits), "the fits are not the run's fits: " + tag
    fj = json.load(open(fits))
    assert fj.get("folds_sha256") == fsha, "fits %s: folds differ" % fits
    if r["name"] == "transfer_lt3d":
        assert fj.get("route") == "transfer", "fits %s: not a transfer fit" % fits
        return {"run_entry": p, "fits": "transfer from " + A5.transfer_equals_source(fj, frozen), "folds_role": role}
    prov = fj.get("provenance") or {}
    fe = prov.get("entry_point") or {}
    assert prov.get("plan_sha256") == side and len(fe) == 1, "fits %s: provenance differs" % fits
    q, hq = list(fe.items())[0]
    assert (frozen.roles or {}).get("entry:c1_fit") == [q] and frozen.get(q) == hq, "fits %s were not made by the plan's entry:c1_fit" % fits
    badf = [x for x, y in (prov.get("code_sha256") or {}).items() if frozen.get(x) != y]
    assert prov.get("code_sha256") and not badf, "fit code not bound: %s" % badf
    assert prov.get("inputs_checked") is True and prov.get("item_chains"), "fits %s: items not chained to the plan" % fits
    if r["name"] == "source_transfer":
        assert fj.get("route") == "source", "source_transfer needs a 'source' fit (Choice 38d)"
        tp, _ = G.role_hash(frozen, "folds_train225")
        train = sorted(json.load(open(os.path.join(G.W, tp)))["fold_of_log"])
        assert fj.get("source_units") == train, "the source fit was not trained on exactly the folds_train225 units"
        assert fj.get("applied_units") == sorted(json.load(open(os.path.join(G.W, fpath)))["fold_of_log"]), "the source fit is not applied to folds_val150"
        assert not set(train) & set(fj["applied_units"]), "a source fit with validation units in training"
    else:
        assert fj.get("route") == "within", "fits %s: route %s, expected within" % (fits, fj.get("route"))
    return {"run_entry": p, "fits_entry": q, "folds_role": role, "caches": [c["dataset"] for c in ch]}


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
    units = sorted(fj["fold_of_log"]) if fj else None
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "plan_sha256": side, "entry_point": rt["entry_point"],
               "code_sha256": rt["code_sha256"], "folds_sha256": folds_sha, "versions": rt.get("versions"),
               "hash_log": G.rel(a.hash_log) if a.hash_log else "canonical", "hash_log_sha256": rt.get("hash_log_sha256")}
    aux = {"route_problems": {},
           "tables": {k: load_table(k, r, cfg, mode, side, frozen, folds_sha, TRACKERS, units, ds_units) for k, r in TABLE_ROLES.items()},
           "tables_descriptive": {k: load_table(k, r, cfg, mode, side, frozen, folds_sha, DESCRIPTIVE_TRACKERS, units, ds_units)
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
                    route_checks.setdefault(r["name"], {})[t] = check_route_c1(rr, r, t, side, frozen, ds_units)
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
    print("C1 ANALYSIS V06 DONE")


if __name__ == "__main__":
    main()
