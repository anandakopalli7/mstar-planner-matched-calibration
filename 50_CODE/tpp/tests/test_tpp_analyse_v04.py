#!/usr/bin/env python3
"""Tests for tpp_analyse_v04 and tpp_freeze_v02 (4 Nov 2026) on SYNTHETIC data only. Run in canmot310 with `python -I`.
= the v03 suite (E1-E9) run on v04 / freeze v02, with R18b's additions:
  E1  ties labelled: trivial (n = 19, no exceedance, bound 1/20) and non-trivial (n7);
  E2  plus: a relabelled copy of the primary run (same predictions, meta says seed 20261104) is refused (n4);
  E8  binding with c1_guard_v02 through the function's rehearsal log (no module patch); plus: a plan under 90_DECISIONS is
      frozen only into the canonical log (n2), and a log override for non-nuScenes units is refused (n3);
  E10 the tracker arm's sd equals K8's item sd (a synthetic K8 provider); a 1e-6 difference or a missing item is refused (n6);
  E11 the superseded entry points (tpp_analyse_v01, v02, v03 main) refuse real inputs and name tpp_analyse_v04; the live
      tpp_freeze_v01 refuses any plan under 90_DECISIONS and names tpp_freeze_v02 (D16 v15 Choice 36).
Usage: python -I test_tpp_analyse_v04.py --out <json>
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(1, HERE)
import tpp_analyse_v04 as T  # noqa: E402
import tpp_analyse_v03 as A3  # noqa: E402
import tpp_analyse_v01 as A1o  # noqa: E402
import tpp_freeze_v01 as F1  # noqa: E402
import tpp_analyse_v02 as A2  # noqa: E402
import tpp_freeze_v02 as F  # noqa: E402
import tpp_common_v01 as C  # noqa: E402
import test_tpp_analyse_v01 as T1  # noqa: E402

RES = {}


def check(name, cond, info=None):
    RES[name] = {"pass": bool(cond), "info": info}
    print(("PASS " if cond else "FAIL ") + name + ("  " + json.dumps(info, default=float)[:600] if info is not None else ""), flush=True)


def raises(fn):
    try:
        fn()
        return False
    except AssertionError:
        return True


def build(d, seed):
    """One synthetic tracker: keys, primary trk / gt runs, two S1 seed runs, SHA256SUMS lists."""
    os.makedirs(d, exist_ok=True)
    kp, runs, _ = T1.make_synthetic(d, seed=seed)
    kz = dict(np.load(kp))
    names = list(kz["scene_names"])
    dev = np.zeros(len(names), bool)
    for i, nm in zip((10, 50, 90, 130), T.CFG["dev_scenes"]):
        names[i] = nm
        dev[i] = True
    assert len(set(names)) == len(names)
    kz["scene_names"], kz["scene_is_dev"] = np.array(names), dev
    np.savez(kp, **kz)
    ksha = C.sha256_path(kp)
    h3 = np.nonzero(kz["rec_h"] == 3)[0]
    rng = np.random.default_rng(seed + 100)

    def write(p, z, src, sd):
        ok3 = h3[z["status"][h3] == C.ST_OK]
        z["mix_rec"] = ok3
        z["mix_w"] = np.full((len(ok3), 25), 1.0 / 25, np.float32)
        z["mix_mu"] = np.repeat(z["v2_mu"][ok3][:, None, :], 25, 1)
        z["mix_cov"] = np.repeat(z["v2_cov"][ok3][:, None, :], 25, 1)
        z["meta_json"] = np.array(json.dumps({"source": src, "seed": sd, "model": "int_ee", "keys_sha256": ksha}))
        np.savez(p, **z)

    out = {"keys": kp}
    zt = dict(np.load(runs["trk"]))
    zg = dict(np.load(runs["gt"]))
    out["trk"], out["gt"] = os.path.join(d, "tpp_trk.npz"), os.path.join(d, "tpp_gt.npz")
    write(out["trk"], dict(zt), "trk", T.PRIMARY)
    write(out["gt"], dict(zg), "gt", T.PRIMARY)
    sdir = os.path.join(d, "seed_sensitivity")
    os.makedirs(sdir, exist_ok=True)
    for role, sd in (("s1a", T.S1_SEEDS[0]), ("s1b", T.S1_SEEDS[1])):
        z = dict(zt)
        f = np.exp(rng.normal(0, 0.3, len(z["v2_cov"])))[:, None]
        z["v2_cov"], z["v1_cov"] = z["v2_cov"] * f, z["v1_cov"] * f
        out[role] = os.path.join(sdir, "tpp_trk_seed%d.npz" % sd)
        write(out[role], z, "trk", sd)
    with open(os.path.join(d, "SHA256SUMS_v01.txt"), "w") as fh:
        for r in ("trk", "gt"):
            fh.write("%s *%s\n" % (C.sha256_path(out[r]), os.path.basename(out[r])))
    with open(os.path.join(sdir, "SHA256SUMS_seed_v01.txt"), "w") as fh:
        for r in ("s1a", "s1b"):
            fh.write("%s *%s\n" % (C.sha256_path(out[r]), os.path.basename(out[r])))
    cache = os.path.join(d, "cache")
    os.makedirs(cache, exist_ok=True)
    json.dump({"scenes": {}}, open(os.path.join(cache, "MANIFEST.json"), "w"))
    out["cache"] = cache
    return out


def load(t):
    kz, runs, gt_xy, trk_mu, trk_cov = T.A1.load_inputs(t["keys"], {"trk": t["trk"], "gt": t["gt"]}, True)
    return kz, runs, gt_xy, trk_mu, trk_cov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    root = tempfile.mkdtemp(prefix="tpp_syn3_")
    tr = {"t1": build(os.path.join(root, "t1"), 5), "t3": build(os.path.join(root, "t3"), 6)}
    B_FAST = 500
    kz, runs, gt_xy, trk_mu, trk_cov = load(tr["t1"])
    # E1 exact against float
    P3 = T.analyse_v04(kz, runs, gt_xy, trk_mu, trk_cov, "v2", B_FAST)
    P2 = A2.analyse_v02(kz, runs, gt_xy, trk_mu, trk_cov, "v2", B_FAST)
    diffs = {m: abs(P3["populations"]["PD7"]["validity"][m]["pooled_E"] - P2["populations"]["PD7"]["validity"][m]["pooled_E"])
             for m in ("TPP_Mstar", "TPP_B4", "TPP_B3", "TRK_Mstar")}
    ex = P3["exact_crc"]
    check("E1_exact_crc_ties_labelled", max(diffs.values()) < 1e-12 and ex["decisions"] > 0
          and ex["exact_ties_bound_equals_delta"] == ex["ties_trivial_n19_no_exceedance"] + ex["ties_nontrivial"],
          {"diffs": diffs, "exact_crc": ex})
    # E2 fail safe
    z = dict(np.load(tr["t1"]["trk"]))
    okrows = np.nonzero((z["status"] == C.ST_OK) & (kz["rec_h"] == 3))[0][:40]
    z["v2_mu"] = z["v2_mu"].copy()
    z["v2_mu"][okrows] = np.nan
    nanp = os.path.join(root, "nan_trk.npz")
    np.savez(nanp, **z)
    _, rn, _, _, _ = T.A1.load_inputs(tr["t1"]["keys"], {"trk": nanp, "gt": tr["t1"]["gt"]}, True)
    e_nan = raises(lambda: T.analyse_v04(kz, rn, gt_xy, trk_mu, trk_cov, "v2", 200))
    paths = {k: tr["t1"][k] for k in ("trk", "gt", "s1a", "s1b")}
    e_gt = raises(lambda: T.check_runs(tr["t1"]["keys"], {k: v for k, v in paths.items() if k != "gt"}, True))
    e_dup = raises(lambda: T.check_runs(tr["t1"]["keys"], dict(paths, s1a=paths["trk"]), True)) and \
        raises(lambda: T.check_runs(tr["t1"]["keys"], dict(paths, s1b=paths["s1a"]), True))
    e_lab = raises(lambda: T.check_runs(tr["t1"]["keys"], dict(paths, s1a=paths["s1b"], s1b=paths["s1a"]), True))
    e_keys = raises(lambda: T.check_runs(tr["t3"]["keys"], paths, True))
    relab = os.path.join(os.path.dirname(tr["t1"]["s1a"]), "relabelled_primary.npz")
    zr = dict(np.load(tr["t1"]["trk"]))
    zr["meta_json"] = np.array(json.dumps(dict(json.loads(str(zr["meta_json"])), seed=T.S1_SEEDS[0])))
    np.savez(relab, **zr)
    e_relab = raises(lambda: T.check_runs(tr["t1"]["keys"], dict(paths, s1a=relab), True))
    e_ok = not raises(lambda: T.check_runs(tr["t1"]["keys"], paths, True))
    cr = T.check_runs(tr["t1"]["keys"], paths, True)
    e_gtarm = raises(lambda: T.analyse_v04(kz, {"trk": runs["trk"]}, gt_xy, trk_mu, trk_cov, "v2", 200))
    check("E2_fail_safe", all([e_nan, e_gt, e_dup, e_lab, e_keys, e_ok, e_gtarm, e_relab]),
          {"relabelled_primary_refused": e_relab, "share_2s_rows_differ": cr["share_2s_rows_v2cov_differs_from_primary"], "nan": e_nan, "missing_gt": e_gt, "duplicate_seed": e_dup, "mislabelled_seed": e_lab, "other_keys": e_keys, "valid_set_accepted": e_ok,
           "analysis_without_gt": e_gtarm})
    # E3 M1 gating
    hk = {"HK1_i_no_flagged_cell": True, "HK1_ii_pooled_evaluable": True, "HK1_ii_pooled_not_flagged": True}
    g1 = T.h2_population(hk, {"family_flagged": ["car|all ranges|lat|straight"], "family_size": 7, "floor_met": False})
    g2 = T.h2_population(hk, {"family_flagged": [], "family_size": 2, "floor_met": False})
    w_ok = P3["hypotheses"]["H2_no_cell_shown_above_delta_all_pops"] and ("floor of 6 not met" in P3["H2_wording"] or "met on every population" in P3["H2_wording"]) \
        and "valid" not in P3["H2_wording"]
    check("E3_family_flag_gates_H2", g1[0] is False and g2[0] is True and w_ok, {"flagged": g1, "few_cells": g2, "wording": P3["H2_wording"]})
    # E4 empty population and non-evaluable pooled cell
    kz_e = dict(kz)
    kz_e["item_inpath"] = np.zeros_like(kz["item_inpath"])
    PE = T.analyse_v04(kz_e, runs, gt_xy, trk_mu, trk_cov, "v2", 200)
    kz_n = dict(kz)
    few = set(range(0, 150, 6))              # in-path items only in 25 scenes: pooled PD cell not evaluable (< 39 scenes)
    kz_n["item_inpath"] = kz["item_inpath"] & np.isin(kz["item_s"], list(few))
    PN = T.analyse_v04(kz_n, runs, gt_xy, trk_mu, trk_cov, "v2", 200)
    pdn = PN["populations"]["PD"]
    check("E4_empty_and_unevaluable_are_NO", PE["populations"]["PD"].get("empty") is True and PE["hypotheses"]["H2_no_cell_shown_above_delta_all_pops"] is False
          and pdn["validity"]["TPP_Mstar"]["HK1_ii_pooled_evaluable"] is False and pdn["H2_population"] is False,
          {"empty": PE["populations"]["PD"]["H2_reason"], "unevaluable": pdn["H2_reason"]})
    # E5 decision coding
    Hs = ("H1_raw_TPP_overconfident", "H2_no_cell_shown_above_delta_all_pops", "H3_history_input_effect_positive")
    allt = {h: True for h in Hs}

    def mk(vals):
        return {t: {sd: dict(allt, **{Hs[0]: v}) for sd, v in zip([T.PRIMARY] + T.S1_SEEDS, vals[t])} for t in ("t1", "t3")}
    d1 = T.decide(mk({"t1": [True, True, True], "t3": [True, True, True]}))[Hs[0]]
    d2 = T.decide(mk({"t1": [True, True, False], "t3": [True, True, True]}))[Hs[0]]
    d3 = T.decide(mk({"t1": [True, False, False], "t3": [True, True, False]}))[Hs[0]]
    d4 = T.decide(mk({"t1": [False, True, True], "t3": [True, True, True]}))[Hs[0]]
    bad1 = raises(lambda: T.decide({"t1": {T.PRIMARY: allt, T.S1_SEEDS[0]: allt}}))
    bad2 = raises(lambda: T.decide(mk({"t1": [True, None, True], "t3": [True, True, True]})))
    check("E5_coded_decision", d1["code"] == "SUPPORTED" and d2["code"] == "SEED_DEPENDENT_NOT_SUPPORTED" and d2["note"] == "primary plus one S1 seed"
          and d3["note"] == "primary seed only" and d4["code"] == "NOT_SUPPORTED" and bad1 and bad2,
          {"all": d1["code"], "primary_plus_one": [d2["code"], d2["note"]], "primary_only": d3["note"], "fails_primary": d4["code"]})
    # E6 S1 refits M* on the seed run; a calibrated seed breaks H1 robustness
    _, rs, _, _, _ = T.A1.load_inputs(tr["t1"]["keys"], {"trk": tr["t1"]["s1a"]}, True)
    PS = T.analyse_v04(kz, {"trk": rs["trk"], "gt": runs["gt"]}, gt_xy, trk_mu, trk_cov, "v2", B_FAST)
    mt = (P3["key_numbers"]["TPP_Mstar_mean_margin_m_PD7"], PS["key_numbers"]["TPP_Mstar_mean_margin_m_PD7"])
    mr = (P3["key_numbers"]["TRK_Mstar_mean_margin_m_PD7"], PS["key_numbers"]["TRK_Mstar_mean_margin_m_PD7"])
    zc = dict(np.load(tr["t1"]["s1b"]))
    zc["v2_cov"] = zc["v2_cov"] * 9.0
    calp = os.path.join(root, "cal_seed.npz")
    np.savez(calp, **zc)
    _, rc, _, _, _ = T.A1.load_inputs(tr["t1"]["keys"], {"trk": calp}, True)
    PC = T.analyse_v04(kz, {"trk": rc["trk"], "gt": runs["gt"]}, gt_xy, trk_mu, trk_cov, "v2", B_FAST)
    dec = T.decide({"t1": {T.PRIMARY: P3["hypotheses"], T.S1_SEEDS[0]: PS["hypotheses"], T.S1_SEEDS[1]: PC["hypotheses"]}})
    check("E6_S1_refits_and_detects", abs(mt[0] - mt[1]) > 1e-6 and mr[0] == mr[1] and dec[Hs[0]]["code"] == "SEED_DEPENDENT_NOT_SUPPORTED"
          and PS["hypotheses"][Hs[0]] is True and PC["hypotheses"][Hs[0]] is False,
          {"TPP_Mstar_margin_primary_vs_seed": mt, "TRK_Mstar_margin": mr, "H1_decision": dec[Hs[0]]})
    # E7 H4 breakdowns
    bd = P3["H4_breakdowns_PD7"]
    n7 = P3["populations"]["PD7"]["items"]
    check("E7_H4_breakdowns", sum(v["items"] for v in bd["history_stratum"].values()) == n7 and sum(v["items"] for v in bd["group"].values()) == n7,
          {"history": {k: v["items"] for k, v in bd["history_stratum"].items()}, "group": {k: v["items"] for k, v in bd["group"].items()}})
    # E8 binding guard in a sandbox
    sb = os.path.join(root, "sandbox")
    os.makedirs(sb)
    log = os.path.join(sb, "D17_PLAN_HASH_LOG.txt")
    plan = os.path.join(sb, "plan_v03.md")
    body = ("# sandbox plan\n\nPre-registration text for the synthetic guard test; it cites 20_DESIGN/MANUSCRIPT_DRAFT_v02.md, "
            "which is a file name, not a banner.\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n")
    extra = [f for f in T.G.project_modules(T.__file__) if os.path.abspath(f) not in {os.path.abspath(x) for x in T.code_files()}]
    banner_cases = {"DRAFT plan": True, "v02 NOT FROZEN": True, "MANUSCRIPT_DRAFT_v02.md": False, "drafted": False, "DRAFTS": False}
    banner_ok = all(T.unfrozen_banner(k) == v for k, v in banner_cases.items())
    open(plan, "w", encoding="utf-8", newline="\n").write(body)
    trk_args = []
    for tag, t in tr.items():
        trk_args += ["--tracker", tag, t["keys"], t["trk"], t["gt"], t["s1a"], t["s1b"], t["cache"]]
    try:
        draft = os.path.join(sb, "plan_draft.md")
        open(draft, "w", encoding="utf-8").write(body.replace("Pre-registration", "DRAFT pre-registration"))
        r_draft = raises(lambda: F.main(["--plan", draft, "--sandbox-hash-log", log, "--results-dir", os.path.join(sb, "res")] + trk_args))
        plan_nx = os.path.join(sb, "plan_noextra.md")
        open(plan_nx, "w", encoding="utf-8", newline="\n").write(body)
        F.main(["--plan", plan_nx, "--sandbox-hash-log", log, "--results-dir", os.path.join(sb, "res")] + trk_args)
        r_runtime = raises(lambda: T.check_binding_real(plan_nx, {tag: dict(t) for tag, t in tr.items()}, log=log))
        h = F.main(["--plan", plan, "--sandbox-hash-log", log, "--results-dir", os.path.join(sb, "res")] + trk_args + ["--sandbox-extra-module"] + extra)
        r_extra_real = raises(lambda: F.check(os.path.join(T.W_ROOT, "90_DECISIONS", "x.md"), {}, os.path.join(sb, "res"), [], F.CANONICAL, extra))
        real_plan = os.path.join(T.W_ROOT, "90_DECISIONS", "D17_TPP_ARM_PREREG_v04.md")
        r_canon = raises(lambda: F.check_log_policy(real_plan, log)) and not raises(lambda: F.check_log_policy(real_plan, F.CANONICAL))
        r_av2 = raises(lambda: T.G.frozen_plan(plan, "av2", log=log, which="D17"))
        trackers = {tag: dict(t) for tag, t in tr.items()}
        ok_bind = not raises(lambda: T.check_binding_real(plan, trackers, log=log))
        side, frozen = T.G.frozen_plan(plan, "nuscenes", log=log, which="D17")
        roles_ok = frozen.roles.get(T.ROLE_ENTRY) == [T.G.rel(T.__file__)] and all(T.G.rel(f) in frozen.roles.get("module", []) for f in T.code_files()[1:-1])
        all_verify = all(T.G.sha(os.path.join(T.W_ROOT, p)) == hh for p, hh in frozen.items())
        n_bound = len(frozen)
        # tamper an input
        bak = tr["t1"]["gt"] + ".bak"
        shutil.copy(tr["t1"]["gt"], bak)
        zz = dict(np.load(tr["t1"]["gt"]))
        zz["extra"] = np.array(1)
        np.savez(tr["t1"]["gt"], **zz)
        r_tamper = raises(lambda: T.check_binding_real(plan, trackers, log=log))
        shutil.copy(bak, tr["t1"]["gt"])
        # run missing from its SHA256SUMS list (the list is restored afterwards)
        sums = os.path.join(os.path.dirname(tr["t1"]["trk"]), "SHA256SUMS_v01.txt")
        s_txt = open(sums).read()
        open(sums, "w").write("\n".join(ln for ln in s_txt.splitlines() if "tpp_gt" not in ln) + "\n")
        r_sums = raises(lambda: T.check_binding_real(plan, trackers, log=log))
        open(sums, "w").write(s_txt)
        # hash log without the plan
        open(log, "w").write("0" * 64 + "  other\n")
        r_log = raises(lambda: T.check_binding_real(plan, trackers, log=log))
        open(log, "w").write("%s  %s  restored\n" % (h, "plan"))
        ok_again = not raises(lambda: T.check_binding_real(plan, trackers, log=log))
        # plan edited after the freeze
        ptxt = open(plan, encoding="utf-8").read()
        open(plan, "w", encoding="utf-8", newline="\n").write(ptxt + "\nedited\n")
        r_edit = raises(lambda: T.check_binding_real(plan, trackers, log=log))
        open(plan, "w", encoding="utf-8", newline="\n").write(ptxt)
        # B on the command line in real mode
        r_boot = raises(lambda: T.main(["--plan", plan, "--out", os.path.join(sb, "o.json"), "--boot", "300"] + trk_args))
    finally:
        pass
    check("E8_binding_guard", banner_ok and r_draft and ok_bind and all_verify and r_tamper and r_sums and r_log and ok_again and r_edit and r_boot
          and r_canon and r_av2 and r_runtime and r_extra_real and roles_ok,
          {"bound_files": n_bound, "roles_block_entry_and_modules": roles_ok, "unbound_loaded_module_refused": r_runtime,
           "extra_modules_refused_for_real_plan": r_extra_real, "real_plan_only_canonical_log": r_canon, "override_refused_for_non_nuscenes_units": r_av2, "banner_regex": banner_ok, "draft_refused": r_draft, "accepted_after_freeze": ok_bind, "every_bound_hash_verifies": all_verify,
           "tampered_input_refused": r_tamper, "run_missing_from_sums_refused": r_sums, "log_without_plan_refused": r_log,
           "accepted_again": ok_again, "edited_plan_refused": r_edit, "boot_in_real_mode_refused": r_boot})
    # E10 the tracker arm's sd against K8's item sd (synthetic provider built like K8's strata: sqrt(a' S a + 0.1^2))
    def provider_from(kz_, bump=None, drop=False):
        def prov(path, si):
            sel = np.nonzero(np.asarray(kz_["item_s"]) == si)[0]
            rec = np.asarray(kz_["item_rec"])[sel]
            a_ = np.asarray(kz_["item_a"])[sel]
            yaw = np.asarray(kz_["rec_yaw"])[rec]
            ax = np.where(a_[:, None] == 0, np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1))
            S3 = np.asarray(kz_["syn_trk_cov"])[rec]
            sd = np.sqrt(np.maximum(ax[:, 0] ** 2 * S3[:, 0] + 2 * ax[:, 0] * ax[:, 1] * S3[:, 1] + ax[:, 1] ** 2 * S3[:, 2] + 0.01, 1e-6))
            out = {"h": np.asarray(kz_["item_h"])[sel], "ref_relied": np.asarray(kz_["item_ref_relied"])[sel],
                   "pair": np.asarray(kz_["rec_pair"])[rec], "a": a_, "sd": sd.copy()}
            if bump is not None and len(sd):
                out["sd"][0] += bump
                out["sd"] = out["sd"] + 0.0
                out["sd"][:] = np.where(np.arange(len(sd)) == 0, out["sd"], out["sd"])
            if drop and len(sd):
                for k in out:
                    out[k] = np.asarray(out[k])[1:]
            return out
        return prov
    sd_ok = T.trk_sd_vs_k8(kz, runs, gt_xy, trk_mu, trk_cov, "none", provider=provider_from(kz))
    sd_bump = raises(lambda: T.trk_sd_vs_k8(kz, runs, gt_xy, trk_mu, trk_cov, "none", provider=provider_from(kz, bump=1e-6)))
    sd_drop = raises(lambda: T.trk_sd_vs_k8(kz, runs, gt_xy, trk_mu, trk_cov, "none", provider=provider_from(kz, drop=True)))
    check("E10_trk_sd_equals_k8_item_sd", sd_ok["items_checked"] > 0 and sd_ok["max_abs_diff"] < 1e-12 and sd_bump and sd_drop,
          {"checked": sd_ok, "bumped_refused": sd_bump, "missing_item_refused": sd_drop})
    # E11 superseded entry points (D16 v15 Choice 36)
    def msg(fn):
        try:
            fn()
        except AssertionError as e:
            return str(e)
        return ""
    old_argv = sys.argv
    sys.argv = ["tpp_analyse_v01.py", "--keys", tr["t1"]["keys"], "--runs", "trk=" + tr["t1"]["trk"], "--out", os.path.join(root, "x1.json")]
    m1 = msg(A1o.main)
    sys.argv = ["tpp_analyse_v02.py", "--keys", tr["t1"]["keys"], "--runs", "trk=" + tr["t1"]["trk"], "--out", os.path.join(root, "x2.json")]
    m2 = msg(A2.main)
    sys.argv = old_argv
    m3 = msg(lambda: A3.main(["--plan", "p.md", "--out", os.path.join(root, "x3.json"), "--tracker", "t1", tr["t1"]["keys"], tr["t1"]["trk"],
                              tr["t1"]["gt"], tr["t1"]["s1a"], tr["t1"]["s1b"], tr["t1"]["cache"]]))
    mf = msg(lambda: F1.main(["--plan", os.path.join(T.W_ROOT, "90_DECISIONS", "D17_TPP_ARM_PREREG_v04.md"), "--production"]))
    check("E11_superseded_entry_points_refuse_real", all("superseded" in m and "tpp_analyse_v04" in m for m in (m1, m2, m3)) and "tpp_freeze_v02" in mf,
          {"v01": m1[:90], "v02": m2[:90], "v03": m3[:90], "freeze_v01": mf[:90]})
    # E9 end to end at the configuration's B
    outp = os.path.join(root, "syn_out_v03.json")
    argv = ["--synthetic", "--out", outp]
    for tag, t in tr.items():
        argv += ["--tracker", tag, t["keys"], t["trk"], t["gt"], t["s1a"], t["s1b"]]
    o = T.main(argv)
    again = raises(lambda: T.main(argv))
    codes = {hh: v["code"] for hh, v in o["decision"].items()}
    check("E9_end_to_end_B2000", o["B"] == 2000 and codes[Hs[0]] == "SUPPORTED" and codes[Hs[2]] == "SUPPORTED"
          and codes[Hs[1]] in ("SUPPORTED", "SEED_DEPENDENT_NOT_SUPPORTED", "NOT_SUPPORTED") and again
          and set(o["trackers"]["t1"]) == {"inputs_sha256", "trk_sd_vs_k8", "primary_v2", "secondary_v1", "sensitivity_tail_excluded_v2", "S1", "S2_seed_pooled_v2_descriptive"},
          {"codes": codes, "H2_wording_t1": o["trackers"]["t1"]["primary_v2"]["H2_wording"][:300], "never_overwritten": again})
    summ = {"tests": RES, "all_pass": all(x["pass"] for x in RES.values()), "data": "SYNTHETIC ONLY", "seconds": round(time.time() - t0, 1),
            "scripts": {"tpp_analyse_v04": C.sha256_path(T.__file__), "tpp_freeze_v02": C.sha256_path(F.__file__),
                        "test_tpp_analyse_v04": C.sha256_path(os.path.abspath(__file__)), "config": C.sha256_path(T.CONFIG_PATH),
                        "code_files": {T.G.rel(f): C.sha256_path(f) for f in T.code_files()}}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(summ, open(a.out, "w"), indent=1, default=float)
    print("ALL_PASS" if summ["all_pass"] else "SOME_FAIL")


if __name__ == "__main__":
    main()
