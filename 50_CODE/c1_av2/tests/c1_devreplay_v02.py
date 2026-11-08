#!/usr/bin/env python3
"""Development replay v02 (Claude line, c1_devreplay_v02, 5 Nov 2026) = c1_devreplay_v01 (kept) on c1_rules_v02, for D16 v34 Choice 53(g):
B = 40000 (c1_rules_v02.B_BOOT), every p-value (k + 1)/(B + 1) (c1_rules_v02.paired_mc; recorded: H1's Form B p, Form C's p and H10's
NI p), H1's own V_t at 1 - 0.0125/9 (the within route; H4's level 1 - 0.0025/9 applies on the transfer route, which development does
not have). A test module of README v10 (test_c1_v13, group DEVREPLAY). Compared, every difference listed and none adjusted (tolerance
0.002 on bounds, 1 cell on families):
  * with the lead's development check v03 (60_RESULTS/c1_criteria_sensitivity_v03/C3_verdict_rstar2_v03.json; Choice 52's levels,
    B = 20000): Valid(M*), V_t, M*'s pooled bounds at HK1C_LEVEL and power families, Form B's level and bounds, Form C, H10's NI bound;
  * Form A at 1 - 0.025/4 (D16 v34 Choice 53a: the v03 reference's Form A is at 1 - 0.05/4): with the lead's reference v02
    (60_RESULTS/c1_criteria_sensitivity_v02/C_verdict_rstar_v02.json, formA_descriptive ub_at_1-0.025/4, B = 2000), and with a
    recomputation at 1 - 0.025/4 on the v03 reference's weights (default_rng([20261401, i, 0]), B = 20000; the same per-scene rates).
Only those two reference files are read in 60_RESULTS.

c1_devreplay_v01's docstring (kept):
Development replay of the audit's rules on the K8 v03 inputs (Claude line, c1_devreplay_v01, 5 Nov 2026; D16 v30 Choice 50,
the lead's item 8). nuScenes DEVELOPMENT DATA ONLY: the K8 Linux replicate (70_TESTS/k8_expl_v02_linux, 840 scenes,
decision mode) and its v03 analysis (RETUNED's cross-fitted arm per scene). No Argoverse 2 file is read. Outcome-free for C1.
A test module of README v09: test_c1_v12's group DEVREPLAY checks that the recorded result was made by the bound c1_rules_v01 and this
file, and that its verdict is the expected one.
Per tracker (T1 = 0, T3 = 1):
  * the scene x cell record and exceedance tables of M*, B0, B1, B3, B4, B6, B9 and RETUNED on PD7, SD1_7 and PD
    (c1_power_counts_v02.load_tracker, unchanged), the per-scene infeasible rates (episodes' infeasible_frames / frames), the K8 v03
    log bootstrap (default_rng([20261106, i, 0]), B = 2000) and power keys ([20261107, i] for M*, [20261107, i, 100 + ARM_INDEX] for a
    comparator, then + [population index]);
  * every arm's validity by c1_rules_v01.hk1_rule_criteria (M* at LEVEL_AGAINST, comparators' removal conditions at
    LEVEL_REMOVAL_V, HK1c at HK1C_LEVEL, target-only power with N_DATASETS datasets), evaluable >= MIN_UNITS scenes from >= MIN_LOGS
    logs, sup-t quantiles recorded rather than raised (c1_analyse_v09's m13);
  * Valid(M*) (c1_analyse_v02.arm_status), V_t (the comparators with no removal condition: c1_analyse_v09's rule), Form B at
    1 - ALPHA_FOR / |V_t|, Form A at LEVEL_FORM_A, Form C at LEVEL_FOR with c = C_FORM_C (c1_analyse_v02.paired, the per-scene
    weights).
The lead's expectation at Choice 50's levels (recorded, informational since D16 v33 Choice 52): Valid(M*) on T1 and T3; V_t = {B3}
on T1 and {B0, B3} on T3; Forms A, B and C met. At Choice 52's levels (removal 1 - 0.0125/9, Form B 1 - 0.0125/|V_t|, B = 20000) the
replay reports its values; the lead compares them with development check v03.
Comparison (the lead, 5 Nov 2026): the lead's independent reference 60_RESULTS/c1_criteria_sensitivity_v02/C_verdict_rstar_v02.json (the
only file read there) gives M*'s pooled UB at HK1C_LEVEL, M*'s power-family sizes, V_t, the Form A, B and C bounds and H10's NI bound;
each is compared (tolerance 0.002 on bootstrap bounds, 1 cell on family sizes) and every larger difference is listed, never adjusted.
H3 is not replayed: the K8 replicate's episodes hold no M*J or M*Jx arm (the reference takes H3's joint statuses from k8_analyse_v03's
stored analysis); H3's rules are tested on constructed cases (test_c1_v12 AN9 and CRIT) and in the rehearsal.
Resumable: each (tracker, arm) validity is checkpointed in <out dir>/ckpt/ with the code hashes; a re-run reuses valid checkpoints.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/c1_devreplay_v01.py [--out 70_TESTS/c1_v01/status_v09/c1_devreplay_v01.json]
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
import c1_rules_v02 as R  # noqa: E402
import c1_power_counts_v02 as PC2  # noqa: E402
import c1_analyse_v02 as B  # noqa: E402

A, K = R.A, R.K
OUT = os.path.join(W_ROOT, "70_TESTS", "c1_v01", "status_v10", "c1_devreplay_v02.json")
EXPECTED = {"t1": {"valid_Mstar": True, "V_t": ["B3"], "A": True, "B": True, "C": True},
            "t3": {"valid_Mstar": True, "V_t": ["B0", "B3"], "A": True, "B": True, "C": True}}
TIDX = {"t1": 0, "t3": 1}
SEED_BOOT, SEED_POWER = 20261106, 20261107
REFERENCE = os.path.join(W_ROOT, "60_RESULTS", "c1_criteria_sensitivity_v03", "C3_verdict_rstar2_v03.json")
REFERENCE_FORM_A = os.path.join(W_ROOT, "60_RESULTS", "c1_criteria_sensitivity_v02", "C_verdict_rstar_v02.json")
SEED_REF_V03, B_REF_V03 = 20261401, 20000
LAB = {"PD7_primary": "PD7", "SD1_7_gap_le_5m": "SD1_7", "PD_inpath": "PD"}
TOL_BOUND, TOL_FAMILY = 0.002, 1


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def code_key():
    return {"c1_rules_v02": sha(R.__file__), "c1_devreplay_v02": sha(os.path.abspath(__file__))}


def jdump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    os.replace(path + ".tmp", path)


def removal(status):
    """c1_analyse_v09.comparator_reasons' removal part: a flagged cell, family cell or pooled cell in any population."""
    out = []
    for p, r in status["pops"].items():
        if not r["NoFlag"]:
            out.append("%s cell" % p)
        if r["FamFlag"]:
            out.append("%s family" % p)
        if r["pooled_evaluable"] and not r["NoFlag_pool"]:
            out.append("%s pooled" % p)
    return out


def replay(tag, J, ckdir):
    i = TIDX[tag]
    aos = J["decide"][tag]["retune"]["arm_of_scene"]
    scenes, tab, _F = PC2.load_tracker(tag, aos)
    del _F
    log_idx, logs = PC2.log_map(scenes)
    inf = {}
    with open(os.path.join(PC2.RUNS, "episodes_%s_decide.jsonl" % tag)) as f:
        for line in f:
            o = json.loads(line)
            if o.get("entered") and o["scene"] not in PC2.DEV_SCENES and o["arm"] != "LOG":
                inf[(o["scene"], o["arm"])] = (o["infeasible_frames"], o["frames"])
    rate = {a: np.array([inf[(s, aos[s] if a == "RETUNED" else a)][0] / max(inf[(s, aos[s] if a == "RETUNED" else a)][1], 1) for s in scenes])
            for a in PC2.ARMS}
    n_logs = len(logs)
    Wl = np.random.default_rng([SEED_BOOT, i, 0]).multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=R.B_BOOT).astype(float)
    W = Wl[:, np.asarray(log_idx)]
    sc = np.array(scenes)
    lg = np.asarray(log_idx)
    cells = A.cell_family()
    vba, ck = {}, code_key()
    for k, a in enumerate(PC2.ARMS):
        cp = os.path.join(ckdir, "ckpt_%s_%s.json" % (tag, a))
        if os.path.exists(cp):
            d = json.load(open(cp))
            if d.get("key") == ck:
                vba[a] = d["v"]
                continue
        T = {p: (tab[p][0][k], tab[p][1][k]) for p in K.CONF_POPS}
        pk = [SEED_POWER, i] if a == "Mstar" else [SEED_POWER, i, 100 + K.ARM_INDEX[a]]
        t0 = time.time()
        v = R.hk1_rule_criteria(T, cells, sc, lg, W, pk, arm=a)
        v = json.loads(json.dumps(v, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
        jdump(cp, {"key": ck, "v": v, "seconds": round(time.time() - t0, 1)})
        vba[a] = v
        print(tag, a, "%.0f s" % (time.time() - t0), flush=True)
    status = {a: B.arm_status(v) for a, v in vba.items()}
    comps = [a for a in PC2.ARMS if a != "Mstar"]
    reasons = {c: removal(status[c]) for c in comps}
    V = [c for c in comps if not reasons[c]]
    lvl_b = 1 - R.ALPHA_FORM_B / max(len(V), 1)
    fb = {c: R.paired_mc(rate, W, "Mstar", c, lvl_b) for c in V}
    form_b = {"V_t": V, "level": lvl_b, "ub": {c: r["ub"] for c, r in fb.items()},
              "vacuous": not V, "met": bool(status["Mstar"]["valid"] and all(r["ub"] < 0 for r in fb.values())),
              "p_H1": None if not V else min(1.0, len(V) * max(r["p_lt0"] for r in fb.values())), "p_threshold": R.ALPHA_FORM_B,
              "p_k": {c: r["p_k"] for c, r in fb.items()}}
    fa = {c: R.paired_mc(rate, W, "Mstar", c, R.LEVEL_FORM_A)["ub"] for c in B.FORM_A_SET}
    form_a = {"level": R.LEVEL_FORM_A, "ub": fa, "met": bool(status["Mstar"]["valid"] and all(u < 0 for u in fa.values()))}
    rc = R.paired_mc(rate, W, "Mstar", "B4", R.LEVEL_FOR)
    kc = int(np.sum(rc["_bm"] > R.C_FORM_C))
    form_c = {"level": R.LEVEL_FOR, "c": R.C_FORM_C, "ub": rc["ub"], "mean_diff": rc["mean_diff"], "met": bool(rc["ub"] <= R.C_FORM_C),
              "p": R.mc_p(kc, len(rc["_bm"])), "p_k": kc}
    rn = R.paired_mc(rate, W, "Mstar", "B6", R.LEVEL_FOR)
    kn = int(np.sum(rn["_bm"] > R.NI_MARGIN))
    h10_ni = {"level": R.LEVEL_FOR, "margin": R.NI_MARGIN, "ub": rn["ub"], "met": bool(rn["ub"] <= R.NI_MARGIN), "p": R.mc_p(kn, len(rn["_bm"])), "p_k": kn}
    Wr = np.random.default_rng([SEED_REF_V03, i, 0]).multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=B_REF_V03).astype(float)[:, np.asarray(log_idx)]
    form_a["recomputed_on_v03_reference_weights"] = {"seed": [SEED_REF_V03, i, 0], "B": B_REF_V03, "level": R.LEVEL_FORM_A,
                                                     "ub": {c: R.paired_mc(rate, Wr, "Mstar", c, R.LEVEL_FORM_A)["ub"] for c in B.FORM_A_SET}}
    del Wr
    out = {"scenes": len(scenes), "logs": n_logs, "valid_Mstar": status["Mstar"]["valid"],
           "Mstar_pops": {p: {k_: status["Mstar"]["pops"][p][k_] for k_ in ("NoFlag", "FamFlag", "NoFlag_pool", "Floor", "HK1c", "family_size", "evaluable")}
                          for p in K.CONF_POPS},
           "Mstar_family_record_share": {p: vba["Mstar"]["pops"][p].get("family_record_share") for p in K.CONF_POPS},
           "Mstar_pooled_ub_hk1c_level": {p: (vba["Mstar"]["pops"][p].get("pooled") or {}).get("ub") for p in K.CONF_POPS},
           "removal_reasons": reasons, "form_b": form_b, "form_a": form_a, "form_c": form_c, "H10_noninferiority": h10_ni,
           "family_sizes": {a: {p: vba[a]["pops"][p]["family_size"] for p in K.CONF_POPS} for a in vba},
           "zero_se_quantiles": {a: vba[a]["zero_se_quantiles"] for a in vba if vba[a]["zero_se_quantiles"]},
           "levels": vba["Mstar"]["levels"], "power_rule": vba["Mstar"]["power_rule"]}
    got = {"valid_Mstar": out["valid_Mstar"], "V_t": V, "A": form_a["met"], "B": form_b["met"], "C": form_c["met"]}
    out["verdict"] = got
    out["matches_expectation_at_choice_50_levels"] = got == EXPECTED[tag]
    return out


def compare(tag, out, ref, ref_a):
    """Every quantity the lead's references report, against this replay's: (name, ours, reference, difference, within tolerance).
    ref: development check v03 (Choice 52's levels, B = 20000); ref_a: reference v02, for Form A at 1 - 0.025/4 (D16 v34 Choice 53a)."""
    r = ref["trackers"][tag]
    vm = r["arms"]["Mstar"].get("valid", all(v.get("ok") for v in r["arms"]["Mstar"]["pops"].values()))
    rows = [("valid_Mstar", out["valid_Mstar"], vm, None, out["valid_Mstar"] == vm),
            ("V_t", out["form_b"]["V_t"], r["V_t"], None, out["form_b"]["V_t"] == r["V_t"])]
    for p, lab in LAB.items():
        a, b = out["Mstar_pooled_ub_hk1c_level"][p], r["arms"]["Mstar"]["pops"][lab]["pooled_ub_at_L"]
        rows.append(("Mstar pooled UB at %s, %s" % (R.HK1C_LEVEL, lab), a, b, a - b, abs(a - b) <= TOL_BOUND))
        a, b = out["family_sizes"]["Mstar"][p], r["arms"]["Mstar"]["pops"][lab]["family_size"]
        rows.append(("Mstar power family, %s" % lab, a, b, a - b, abs(a - b) <= TOL_FAMILY))
    if abs(r["formB"]["level"] - out["form_b"]["level"]) < 1e-12:
        for c, b in r["formB"]["ub"].items():
            a = out["form_b"]["ub"].get(c)
            rows.append(("Form B UB M*-%s at %.4f" % (c, out["form_b"]["level"]), a, b, None if a is None else a - b, a is not None and abs(a - b) <= TOL_BOUND))
    else:
        rows.append(("Form B level", out["form_b"]["level"], r["formB"]["level"], None, False))
    ra = ((ref_a or {}).get("trackers", {}).get(tag) or {}).get("formA_descriptive") or {}
    for c, b in ra.get("ub_at_1-0.025/4", {}).items():
        a = out["form_a"]["ub"][c]
        rows.append(("Form A UB M*-%s at 1-0.025/4 vs reference v02 (B = 2000)" % c, a, b, a - b, abs(a - b) <= TOL_BOUND))
    for c, b in out["form_a"]["recomputed_on_v03_reference_weights"]["ub"].items():
        a = out["form_a"]["ub"][c]
        rows.append(("Form A UB M*-%s at 1-0.025/4 vs recomputed on v03's weights (B = 20000)" % c, a, b, a - b, abs(a - b) <= TOL_BOUND))
    a, b = out["form_c"]["ub"], r["formC"]["ub_0.975"]
    rows.append(("Form C UB M*-B4 at 0.975", a, b, a - b, abs(a - b) <= TOL_BOUND))
    a, b = out["H10_noninferiority"]["ub"], r["H10"]["ni_ub_0.975"]
    rows.append(("H10 NI UB M*-B6 at 0.975", a, b, a - b, abs(a - b) <= TOL_BOUND))
    rows = [{"name": n, "replay": x, "reference": y, "difference": d, "within_tolerance": bool(ok)} for n, x, y, d, ok in rows]
    return {"rows": rows, "larger_differences": [r_ for r_ in rows if not r_["within_tolerance"]],
            "not_compared": "H3 (no M*J or M*Jx arm in the K8 replicate's episodes)"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    B.configure("c1")
    K.STRICT_Q = False
    t0 = time.time()
    J = json.load(open(PC2.ANALYSIS))
    ckdir = os.path.join(os.path.dirname(os.path.abspath(a.out)), "devreplay_ckpt")
    res = {"tool": "c1_devreplay_v02", "code_sha256": code_key(), "inputs": {"k8_runs": os.path.relpath(PC2.RUNS, W_ROOT).replace(os.sep, "/"),
                                                                          "k8_v03_analysis_sha256": sha(PC2.ANALYSIS)},
           "constants": R.CONSTANTS, "levels": R.levels(), "expected": EXPECTED, "trackers": {}}
    ref = json.load(open(REFERENCE)) if os.path.exists(REFERENCE) else None
    ref_a = json.load(open(REFERENCE_FORM_A)) if os.path.exists(REFERENCE_FORM_A) else None
    res["reference"] = {"note": "development check v03 (Choice 52's levels, B = 20000) for everything but Form A; Form A at 1 - 0.025/4 "
                                "against reference v02 (B = 2000) and against a recomputation on v03's weights (D16 v34 Choice 53a, g)",
                        "file": os.path.relpath(REFERENCE, W_ROOT).replace(os.sep, "/"), "sha256": sha(REFERENCE) if ref else None,
                        "file_form_a": os.path.relpath(REFERENCE_FORM_A, W_ROOT).replace(os.sep, "/"),
                        "sha256_form_a": sha(REFERENCE_FORM_A) if ref_a else None,
                        "B": (ref or {}).get("B"), "tolerance": {"bounds": TOL_BOUND, "family_cells": TOL_FAMILY}}
    for tag in ("t1", "t3"):
        res["trackers"][tag] = replay(tag, J, ckdir)
        if ref:
            res["trackers"][tag]["vs_reference"] = compare(tag, res["trackers"][tag], ref, ref_a)
    res["all_match_expectation_at_choice_50_levels"] = all(v["matches_expectation_at_choice_50_levels"] for v in res["trackers"].values())
    res["seconds"] = round(time.time() - t0, 1)
    jdump(a.out, res)
    print(json.dumps({t: {"verdict": v["verdict"], "matches_expectation_at_choice_50_levels": v["matches_expectation_at_choice_50_levels"],
                          "larger_differences_vs_reference": [x["name"] for x in (v.get("vs_reference") or {}).get("larger_differences", [])]}
                      for t, v in res["trackers"].items()}))
    print("C1 DEVREPLAY V02 DONE", sha(a.out))


if __name__ == "__main__":
    main()
