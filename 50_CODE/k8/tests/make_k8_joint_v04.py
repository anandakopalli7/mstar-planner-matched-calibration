#!/usr/bin/env python3
"""Generator of the minimal v04 copies for the joint arm M*J (Claude line, 2 Nov 2026): k8_sim_v04.py, k8_run_v04.py and
k8_analyse_v04.py are written from k8_sim_v02.py, k8_run_v02.py and k8_analyse_v03.py (never modified) by asserted text
replacements, and the diff note K8_V04_DIFF_NOTE_v01.md is written with the unified diffs. Re-running reproduces the files byte
for byte (test_k8_joint_fit_v01.py checks it).
Why v04 copies are needed (k8_run_v02 / k8_analyse_v03 cannot evaluate the new arm unchanged):
  1. k8_sim_v02.margins knows its arms by name: an arm 'MstarJ' raises ValueError, whatever the fits file holds;
  2. k8_run_v02 --exploratory fixes the design to all 29 v02 arms (no subset, no new arm); --dev runs the 10 development scenes
     only; --prereg needs a frozen plan;
  3. k8_analyse_v03 analyses only the arms in k8_sim_v02.ARMS (an unknown arm's episodes are dropped silently), and its
     --exploratory binding accepts only the v02 runs.
The only way to use the v02 files unchanged would be to write M*J's thresholds under the key 'Mstar_ip' of a separate fits file
and rerun the whole v02 design under the arm name 'Mstar': M*J would then be labelled M*, could not sit beside M* in one run,
and every one of the 29 arms would be re-simulated. Rejected.
Usage: python -B tests/make_k8_joint_v04.py   (from 50_CODE/k8)
"""
import difflib
import hashlib
import os
import sys

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rep(s, old, new, count=1):
    assert s.count(old) == count, "expected %d occurrence(s) of: %r (found %d)" % (count, old[:100], s.count(old))
    return s.replace(old, new)


def make_sim(src):
    s = src
    s = rep(s, '"""K8 harness (Claude line, k8_sim_v02, 1 Nov 2026)',
            '"""K8 harness (Claude line, k8_sim_v04, 2 Nov 2026) = k8_sim_v02 plus the joint arms of D16 Choice 2 (b), written by\n'
            'tests/make_k8_joint_v04.py (asserted text replacements; K8_V04_DIFF_NOTE_v01.md). Two changes, no other:\n'
            '  * JOINT_ARMS = ("MstarJ", "MstarJx") are appended to ARMS: each takes its thresholds from its own key \'<arm>_ip\' of the\n'
            '    fits (192 per step, index L0 + 96 x in-path, written by k8_joint_fit_v01.py), else from \'<arm>\' (96, the steps after\n'
            '    2 s), exactly as M* does with \'Mstar_ip\' / \'Mstar\'; their covariance for A6 is the generic D S\' D of _arm_cov;\n'
            '  * JOINT_RUN_STAMP, the stamp of the k8_run_v04 --exploratory --joint runs.\n'
            'Every v02 arm decides exactly as in k8_sim_v02 (test_k8_joint_fit_v01.py).\n'
            'K8 harness (Claude line, k8_sim_v02, 1 Nov 2026)')
    s = rep(s, "ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS\n",
            "ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS\n"
            "# v04 (D16 Choice 2 (b)): the joint arms M*J (primary) and M*Jx (exact split), M*'s per-stratum thresholds times one scalar\n"
            "JOINT_ARMS = (\"MstarJ\", \"MstarJx\")\n"
            "JOINT_RUN_STAMP = \"EXPLORATORY (K8 joint arm M*J, k8_run_v04 --joint): nuScenes development evidence, not a confirmation\"\n"
            "ARMS = ARMS + JOINT_ARMS\n")
    s = rep(s, '        elif arm in ("B6", "Mstar") and (arm + "_ip") in f:\n',
            '        elif arm in ("B6", "Mstar") + JOINT_ARMS and (arm + "_ip") in f:\n')
    s = rep(s, '        elif arm == "Mstar":\n            out[:, h, :] = np.asarray(f["Mstar"])[L0] * s\n',
            '        elif arm == "Mstar" or arm in JOINT_ARMS:\n            out[:, h, :] = np.asarray(f[arm])[L0] * s\n')
    return s


def make_run(src):
    s = src
    s = rep(s, '"""K8 episode runner (Claude line, k8_run_v02, 1 Nov 2026)',
            '"""K8 episode runner (Claude line, k8_run_v04, 2 Nov 2026) = k8_run_v02 running k8_sim_v04 (the joint arms MstarJ, MstarJx),\n'
            'written by tests/make_k8_joint_v04.py (K8_V04_DIFF_NOTE_v01.md). One addition: --joint with --exploratory runs a subset of\n'
            'arms (Mstar and at least one joint arm among them) in decision mode on every non-development scene, stamped\n'
            'S.JOINT_RUN_STAMP; launch and run records carry "joint": true and the v04 code hashes (CODE_FILES names k8_analyse_v04\n'
            'and k8_joint_fit_v01). Everything else is k8_run_v02.\n'
            'Joint usage: python -B k8_run_v04.py --caches <train> <val> --fits <k8_joint_fits_<t>_v01.json> --tag <t>_decide\n'
            '       --mode decide --out <dir> --exploratory --joint --arms B0 B1 B3 B4 B6 B9 Mstar MstarJ MstarJx [--workers n] [--resume]\n'
            'K8 episode runner (Claude line, k8_run_v02, 1 Nov 2026)')
    s = rep(s, "import k8_sim_v02 as S  # noqa: E402\n", "import k8_sim_v04 as S  # noqa: E402\n")
    s = rep(s, '              "analysis": os.path.join(W_ROOT, "50_CODE", "k8", "k8_analyse_v02.py"),\n',
            '              "analysis": os.path.join(W_ROOT, "50_CODE", "k8", "k8_analyse_v04.py"),\n'
            '              "joint_fit": os.path.join(W_ROOT, "50_CODE", "k8", "k8_joint_fit_v01.py"),\n')
    s = rep(s, '    ap.add_argument("--prereg", default=None)\n',
            '    ap.add_argument("--prereg", default=None)\n'
            '    ap.add_argument("--joint", action="store_true", help="v04, with --exploratory: decision mode, a subset of arms with Mstar and a "\n'
            '                                                         "joint arm, every non-development scene")\n')
    s = rep(s, '    assert not (a.dry_run and a.prereg), "--dry-run is for --dev and --exploratory"\n',
            '    assert not (a.dry_run and a.prereg), "--dry-run is for --dev and --exploratory"\n'
            '    assert a.exploratory or not a.joint, "--joint goes with --exploratory"\n')
    s = rep(s, '    elif a.exploratory:\n        assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes, \\\n'
               '            "under --exploratory the design is fixed: all arms, delays 0 2 4, every non-development scene (no --scenes)"\n',
            '    elif a.exploratory:\n'
            '        if a.joint:   # v04: the joint arms beside M* (and chosen comparators), decision mode, every non-development scene\n'
            '            assert (a.mode == "decide" and "Mstar" in a.arms and any(x in S.JOINT_ARMS for x in a.arms) and set(a.arms) <= set(S.ARMS)\n'
            '                    and len(set(a.arms)) == len(a.arms) and "LOG" not in a.arms and list(a.delays_kf) == [0, 2, 4] and not a.scenes), \\\n'
            '                "--exploratory --joint: decision mode, Mstar and a joint arm among known arms, delays 0 2 4, every non-development scene"\n'
            '        else:\n'
            '            assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes, \\\n'
            '                "under --exploratory the design is fixed: all arms, delays 0 2 4, every non-development scene (no --scenes)"\n')
    s = rep(s, "        pre = EXPLORATORY_STAMP\n        exploratory = True\n",
            "        pre = S.JOINT_RUN_STAMP if a.joint else EXPLORATORY_STAMP\n        exploratory = True\n")
    s = rep(s, '    launch = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "dry_run": bool(a.dry_run), "stamp": pre,\n',
            '    launch = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": bool(a.dry_run),\n'
            '              "stamp": pre,\n')
    s = rep(s, '    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "dry_run": False, "stamp": pre, "arms": a.arms,\n',
            '    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": False, "stamp": pre,\n'
            '           "arms": a.arms,\n')
    s = rep(s, '    print("K8 RUN DONE")\n', '    print("K8 RUN V04 DONE")\n')
    return s


JOINT_FUNCS = r'''
# ---------------------------------------------------------------- v04: the joint arm M*J (D16 Choice 2 (b); k8_joint_fit_v01)

JOINT_METHODS = S.JOINT_ARMS
JOINT_FORM_B_COMPARATORS = ("Mstar",) + FORM_B_COMPARATORS
JOINT_RULE = ("Form B validity (D14 v05 section 6 (i)) applied to the joint loss: for each of PD7, SD1_7 and PD the scene-level V2 "
              "(per scene, the share of its decisions with a relied record in the population that have >= 1 exceedance; then the mean "
              "over scenes) must be evaluable (>= 39 scenes from >= 8 logs), not flagged (A.flag: one-sided 0.95 log-cluster bootstrap "
              "lower bound > delta, or est > delta when the bootstrap SE is zero) and its one-sided 0.95 upper bound must be <= "
              "delta + 0.03 (HK1c). The same rule for M*J, M* and every comparator. HK1a's per-stratum cell family has no analogue "
              "(a decision's union spans strata), so the test is HK1b and HK1c on the pooled joint loss.")


def joint_validity(rows, kix, n_keys, W, scene_of_ep, log_of_ep):
    """JOINT_RULE for one arm: per confirmatory population the pooled scene-level V2 with its flag and bounds."""
    one = np.ones((1, n_keys))
    out = {"pops": {}}
    ok_all = True
    for p in CONF_POPS:
        c4, obs = V2_DECIDE[p]
        N, X, _, _ = v2_tables(rows, kix, n_keys, c4, obs)
        r = {"evaluable": bool(A.evaluable(N, scene_of_ep, log_of_ep)[0]), "valid": False}
        if N.sum() > 0:
            est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
            lb, ub, se, sig, q = A.flag(est, boot, np.array([0]), 0.95)
            r.update({"E": float(est[0]), "lb_one_sided_0.95": float(lb[0]), "ub_one_sided_0.95": float(ub[0]), "flagged": bool(sig[0]),
                      "q": float(q) if np.isfinite(q) else None, "ub_le_delta_plus_0.03": bool(ub[0] <= DELTA + 0.03),
                      "point_le_delta": bool(est[0] <= DELTA), "decisions_with_records": int(N.sum()),
                      "decisions_any_exceed": int(X.sum()), "scenes": int((N[:, 0] > 0).sum()),
                      "ci95": [float(np.nanquantile(boot[:, 0], 0.025)), float(np.nanquantile(boot[:, 0], 0.975))]})
            r["valid"] = bool(r["evaluable"] and not r["flagged"] and r["ub_le_delta_plus_0.03"])
        ok_all = ok_all and r["valid"]
        out["pops"][p] = r
    out["valid"] = bool(ok_all)
    return out


def joint_form_b(rate, Ws, jv, arms, method):
    """D14 v05 section 6 Form B with validity = JOINT_RULE, for one joint method: (i) the method and every comparator tested
    alike; (ii) the method less infeasible than every comparator that is also valid on the joint loss (paired one-sided log
    bootstrap bound at 1 - 0.05 / |valid comparators|); (iii) the invalid comparators in the trade-off table."""
    def diff(b, level):
        d = rate[method] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        return float(d.mean()), float(np.quantile(bm, level)), [float(x) for x in np.quantile(bm, [0.025, 0.975])]
    comps = [b for b in JOINT_FORM_B_COMPARATORS if b in arms and b != method]
    passing = [b for b in comps if jv[b]["valid"]]
    level = 1 - 0.05 / max(len(passing), 1)
    lower = {}
    for b in passing:
        md, u, _ = diff(b, level)
        lower[b] = {"mean_diff": md, "ub_one_sided": u, "lower": bool(u < 0)}
    out = {"method": method, "comparators": comps, "comparators_valid_on_joint_loss": passing,
           "comparators_invalid_on_joint_loss": [b for b in comps if b not in passing], "level": level,
           "validity_method": bool(jv[method]["valid"]), "lower_than_every_valid_comparator": lower, "vacuous": not passing,
           "missing_comparators": [b for b in JOINT_FORM_B_COMPARATORS if b not in arms and b != method], "rule": JOINT_RULE}
    out["met"] = bool(out["validity_method"] and all(v["lower"] for v in lower.values()))
    tab = []
    for b in [method] + comps:
        r = {"arm": b, "valid_joint": jv[b]["valid"], "infeasible_rate": float(rate[b].mean())}
        for p in CONF_POPS:
            r["V2_%s_E" % POP_LAB[p]] = jv[b]["pops"][p].get("E")
            r["V2_%s_ub" % POP_LAB[p]] = jv[b]["pops"][p].get("ub_one_sided_0.95")
        if b != method:
            md, _, ci = diff(b, 0.95)
            r["method_minus_arm_infeasible"], r["method_minus_arm_infeasible_ci95"] = md, ci
        tab.append(r)
    out["trade_off_table"] = tab
    return out


def joint_section(rows_by_arm, arms, n_keys, W, scene_of_ep, log_of_ep, rate, Ws, fits):
    """v04: the joint loss of every arm (JOINT_RULE), Form B on the joint loss for each joint method, the price of each joint
    method over M* (paired infeasible-rate difference at identical decision states) and the fitted lambdas."""
    jv = {a: joint_validity(rows_by_arm[a][0], rows_by_arm[a][1], n_keys, W, scene_of_ep, log_of_ep) for a in arms}
    out = {"rule": JOINT_RULE, "crc_target_delta": DELTA, "validity_by_arm": jv, "form_B_joint": {}, "price_vs_Mstar": {},
           "lambda_by_fold": None, "fit": None}
    for m in JOINT_METHODS:
        if m not in arms:
            continue
        out["form_B_joint"][m] = joint_form_b(rate, Ws, jv, arms, m)
        if "Mstar" in arms:
            d = rate[m] - rate["Mstar"]
            bm = (Ws @ d) / Ws.sum(1)
            out["price_vs_Mstar"][m] = {"infeasible_rate_" + m: float(rate[m].mean()), "infeasible_rate_Mstar": float(rate["Mstar"].mean()),
                                        "diff_mean": float(d.mean()), "diff_ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
                                        "note": "paired at identical decision states; scene-level means; log-cluster bootstrap"}
    jm = (fits or {}).get("joint")
    if jm:
        out["lambda_by_fold"] = {f: {m: jm["fit"]["folds"][f][m]["lambda"] for m in JOINT_METHODS} for f in jm["fit"]["folds"]}
        out["fit"] = {"stamp": jm.get("stamp"), "delta": jm.get("delta"), "stratification": jm.get("stratification"),
                      "code_sha256": jm.get("code_sha256"), "base_fits_sha256": jm.get("base_fits_sha256")}
    return out
'''

CHECK_JOINT = r'''
def check_joint_runs(runs, tags, fits_paths, manifests):
    """--joint-exploratory (v04): binds this analysis to the k8_run_v04 --exploratory --joint decision-mode runs: each run record
    is exploratory, joint, not a dry run, stamped S.JOINT_RUN_STAMP, made by the current k8_sim_v04 and k8_run_v04, with the
    --fits given here, Mstar and a joint arm among its arms, the 840 non-development scenes, unchanged outputs and launch
    record, and the caches' current manifests."""
    cur = {"sim_sha256": sha(S.__file__), "runner_sha256": sha(os.path.join(K8, "k8_run_v04.py"))}
    man_now = sorted(sha(p) for p in manifests)
    out = {"runs": {}, "relation": "k8_analyse_v04 analysis of k8_run_v04 --exploratory --joint decision-mode runs", "code": cur}
    for i, tag in enumerate(tags):
        tm = "%s_decide" % tag
        rp = os.path.join(runs, "run_record_%s.json" % tm)
        assert os.path.exists(rp), "run record %s missing: run %s did not finish" % (rp, tm)
        rr = json.load(open(rp))
        assert rr.get("exploratory") is True and rr.get("joint") is True and not rr.get("dry_run"), "not a joint exploratory run: " + tm
        assert rr["stamp"] == S.JOINT_RUN_STAMP and rr["mode"] == "decide", "run %s: stamp or mode" % tm
        assert rr["sim_sha256"] == cur["sim_sha256"] and rr["runner_sha256"] == cur["runner_sha256"], "code changed since run " + tm
        assert rr["fits_sha256"] == sha(fits_paths[i]), "the --fits are not the fits of run " + tm
        assert "Mstar" in rr["arms"] and any(x in rr["arms"] for x in S.JOINT_ARMS), "run %s lacks Mstar or a joint arm" % tm
        names = rr["scene_names"]
        assert len(names) == 840 and not (set(names) & set(DEV_SCENES_K6)), "run %s: not the 840 non-development scenes" % tm
        outs = {}
        for f, ext in RUN_OUTPUTS:
            p = os.path.join(runs, "%s_%s.%s" % (f, tm, ext))
            outs[f] = sha(p)
            assert outs[f] == rr["%s_sha256" % f], "output %s changed since the run" % p
        assert sha(rr["launch_record"]) == rr["launch_record_sha256"], "launch record of %s changed" % tm
        man = [sha(os.path.join(c, "MANIFEST.json")) for c in rr["caches"]]
        assert man == rr["manifest_sha256"], "cache manifests of %s changed" % tm
        if i == 0:
            assert sorted(man) == man_now, "--manifests are not the manifests of run " + tm
        out["runs"][tm] = {"run_record": os.path.abspath(rp), "run_record_sha256": sha(rp), "outputs_sha256": outs, "arms": rr["arms"],
                           "fits_sha256": rr["fits_sha256"], "scenes": len(names)}
    return out

'''

JOINT_CSV = r'''    if res.get("joint_loss"):            # v04: the joint loss of every arm and Form B on it
        jl = res["joint_loss"]
        rows = []
        for a, v in jl["validity_by_arm"].items():
            r = {"arm": a, "valid_joint_form_B_rule": v["valid"], "infeasible_rate": res["infeasible_rate"][a]["mean"]}
            for p in CONF_POPS:
                pv = v["pops"][p]
                for k in ("E", "ci95", "lb_one_sided_0.95", "ub_one_sided_0.95", "flagged", "evaluable", "valid", "scenes", "decisions_with_records"):
                    val = pv.get(k)
                    if k == "ci95":
                        r["V2_%s_ci95_lo" % POP_LAB[p]], r["V2_%s_ci95_hi" % POP_LAB[p]] = (val or [None, None])
                    else:
                        r["V2_%s_%s" % (POP_LAB[p], k)] = val
            for m, fb in jl["form_B_joint"].items():
                if a == m:
                    r["form_B_joint_met"] = fb["met"]
                    r["form_B_joint_valid_comparators"] = " ".join(fb["comparators_valid_on_joint_loss"])
            for m, pr in jl["price_vs_Mstar"].items():
                if a == m:
                    r["price_vs_Mstar_infeasible_diff"] = pr["diff_mean"]
                    r["price_vs_Mstar_ci95_lo"], r["price_vs_Mstar_ci95_hi"] = pr["diff_ci95"]
            rows.append(r)
        write_csv(os.path.join(csv_dir, "k8_%s_decide_joint.csv" % tag), rows)
'''

JOINT_MAIN = r'''    elif a.joint_exploratory:             # v04: the joint arm's decision-mode runs (k8_run_v04 --exploratory --joint)
        DEV_SCENES = DEV_SCENES_K6
        A.MIN_SCENES, A.MIN_LOGS = 39, 8
        STRICT_Q = True
        assert a.boot == B_BOOT and a.modes == ["decide"], "--joint-exploratory: B = %d, decision mode only" % B_BOOT
        assert a.fits, "--fits (the joint fits of the runs) are required"
        STAMP = STAMPS["joint"]
        run_mode = "joint_exploratory"
        binding = check_joint_runs(a.runs, a.tags, a.fits, a.manifests)
        print("%s: %s" % (binding["relation"], ", ".join("%s %s" % (k, v["run_record_sha256"][:12]) for k, v in binding["runs"].items())),
              flush=True)
'''


def make_analysis(src):
    s = src
    s = rep(s, '"""K8 analysis (Claude line, v03, 1 Nov 2026).',
            '"""K8 analysis (Claude line, v04, 2 Nov 2026) = k8_analyse_v03 plus the joint arm M*J (D16 Choice 2 (b)), written by\n'
            'tests/make_k8_joint_v04.py (asserted text replacements; K8_V04_DIFF_NOTE_v01.md). Changes, and nothing else:\n'
            '  * k8_sim_v04 replaces k8_sim_v02 (ARMS + JOINT_ARMS: every arm of a run is analysed, the joint arms included); A6 on the\n'
            '    items and item_margins accept the joint arms (\'<arm>_ip\' of the fits, as M*);\n'
            '  * joint_section (decision mode): the joint loss of every arm under JOINT_RULE (Form B\'s validity test applied to the\n'
            '    scene-level V2 on PD7, SD1_7 and PD), Form B on the joint loss for each joint method, the price of each joint method\n'
            '    over M* (paired infeasible-rate difference), the fitted lambdas; CSV k8_<tag>_decide_joint.csv;\n'
            '  * --joint-exploratory: binds to the k8_run_v04 --exploratory --joint decision-mode runs (check_joint_runs), stamp\n'
            '    S.JOINT_RUN_STAMP, confirmatory statistics (evaluable >= 39 scenes / >= 8 logs, B = 2000, M*\'s strict quantiles).\n'
            'M* stays the only arm with strict sup-t quantiles (R15b N1); the joint arms are treated as comparators there.\n'
            'K8 analysis (Claude line, v03, 1 Nov 2026).')
    s = rep(s, "import k8_sim_v02 as S  # noqa: E402\n", "import k8_sim_v04 as S  # noqa: E402\n")
    s = rep(s, 'ANALYSIS_VERSION = "k8_analyse_v03"\n', 'ANALYSIS_VERSION = "k8_analyse_v04"\n')
    s = rep(s, '          "confirmatory": "CONFIRMATORY: run under a frozen K8 plan"}\n',
            '          "confirmatory": "CONFIRMATORY: run under a frozen K8 plan", "joint": S.JOINT_RUN_STAMP}\n')
    s = rep(s, 'A6_ARMS = ("B0", "B1", "B3", "B4", "B6", "B9", "Mstar") + S.ALPHA_ARMS + (RETUNED,)',
            'A6_ARMS = ("B0", "B1", "B3", "B4", "B6", "B9", "Mstar") + S.JOINT_ARMS + S.ALPHA_ARMS + (RETUNED,)')
    s = rep(s, '            elif arm in ("B6", "Mstar"):\n                thr = np.asarray(F[arm + "_ip"])\n',
            '            elif arm in ("B6", "Mstar") + S.JOINT_ARMS:\n                thr = np.asarray(F[arm + "_ip"])\n')
    s = rep(s, "\ndef analyse_decide(eps, counts, D, C, log_of_scene, B, rng, power_key, fits=None, items=None, items_k8=None):\n",
            JOINT_FUNCS + "\n\ndef analyse_decide(eps, counts, D, C, log_of_scene, B, rng, power_key, fits=None, items=None, items_k8=None):\n")
    s = rep(s, '    res["d14_forms"] = forms\n',
            '    res["d14_forms"] = forms\n'
            '    # ---- v04: the joint loss (JOINT_RULE) of every arm, Form B on it for the joint methods, their price over M*\n'
            '    res["joint_loss"] = joint_section(rows_by_arm, arms, n_keys, W, scene_of_ep, log_of_ep, rate, Ws, fits)\n')
    s = rep(s, "\n\n\ndef csv_tables_loop(res, tag, csv_dir):\n", "\n" + JOINT_CSV + "\n\ndef csv_tables_loop(res, tag, csv_dir):\n")
    s = rep(s, "\ndef checkpoint_key(a, i, tag, mode, run_mode, binding, arm_of_scene):\n",
            CHECK_JOINT + "\ndef checkpoint_key(a, i, tag, mode, run_mode, binding, arm_of_scene):\n")
    s = rep(s, '    ap.add_argument("--exploratory", action="store_true", help="D14 v05 section 5.1: the 840-scene exploratory run (the v02 runs)")\n',
            '    ap.add_argument("--exploratory", action="store_true", help="D14 v05 section 5.1: the 840-scene exploratory run (the v02 runs)")\n'
            '    ap.add_argument("--joint-exploratory", action="store_true", help="v04: the k8_run_v04 --exploratory --joint decision-mode runs")\n')
    s = rep(s, '    assert int(a.allow_dev) + int(a.exploratory) + int(a.prereg is not None) == 1, "exactly one of --allow-dev, --exploratory, --prereg"\n',
            '    assert int(a.allow_dev) + int(a.exploratory) + int(a.prereg is not None) + int(a.joint_exploratory) == 1, \\\n'
            '        "exactly one of --allow-dev, --exploratory, --prereg, --joint-exploratory"\n')
    s = rep(s, "        check_dev_runs(a.runs, a.tags, a.modes)\n    else:\n",
            "        check_dev_runs(a.runs, a.tags, a.modes)\n" + JOINT_MAIN + "    else:\n")
    s = rep(s, '           "exploratory": bool(a.exploratory), "binding": binding,',
            '           "exploratory": bool(a.exploratory), "joint_exploratory": bool(a.joint_exploratory), "binding": binding,')
    s = rep(s, '    print("K8 ANALYSIS V03 DONE")\n', '    print("K8 ANALYSIS V04 DONE")\n')
    return s


NOTE_HEAD = """# K8 v04 copies for the joint arm M*J: diff note (v01, 2 Nov 2026)

Written by `tests/make_k8_joint_v04.py` (asserted text replacements; rerunning it reproduces the three files byte for byte,
`tests/test_k8_joint_fit_v01.py` checks it). No v02 or v03 file is modified.

## Why the v02 runner and the v03 analysis cannot evaluate M*J unchanged

1. `k8_sim_v02.margins` resolves arms by name: `MstarJ` raises `ValueError` whatever the fits file holds (test S1).
2. `k8_run_v02 --exploratory` fixes the design to all 29 v02 arms; `--dev` runs only the 10 development scenes; `--prereg` needs a frozen plan.
3. `k8_analyse_v03` analyses only the arms of `k8_sim_v02.ARMS` (an unknown arm's episodes are silently dropped), and its `--exploratory` binding accepts only the v02 runs.

The one way to use them unchanged, writing M*J's thresholds under `Mstar_ip` of a separate fits file and rerunning the full v02 design, would label M*J as M*, keep it out of the run that holds M*, and re-simulate all 29 arms. It was rejected.

## What changes

| File | From | Changes |
|---|---|---|
| `k8_sim_v04.py` | `k8_sim_v02.py` | `JOINT_ARMS = ("MstarJ", "MstarJx")` appended to `ARMS`; `margins` reads `<arm>_ip` (192 per step) or `<arm>` (96, steps after 2 s) for them, as for M*; `JOINT_RUN_STAMP`. Every v02 arm decides exactly as before |
| `k8_run_v04.py` | `k8_run_v02.py` | imports `k8_sim_v04`; `--joint` (with `--exploratory`): decision mode, a subset of arms containing `Mstar` and a joint arm, all 840 non-development scenes, stamp `JOINT_RUN_STAMP`; `"joint"` in the launch and run records; `CODE_FILES` names `k8_analyse_v04` and `k8_joint_fit_v01` |
| `k8_analyse_v04.py` | `k8_analyse_v03.py` | imports `k8_sim_v04`; A6 and `item_margins` accept the joint arms; `joint_validity`, `joint_form_b`, `joint_section` (decision mode) and the CSV `k8_<tag>_decide_joint.csv`; `--joint-exploratory` with `check_joint_runs` |

## Unified diffs
"""


def main():
    pairs = (("k8_sim_v02.py", "k8_sim_v04.py", make_sim), ("k8_run_v02.py", "k8_run_v04.py", make_run),
             ("k8_analyse_v03.py", "k8_analyse_v04.py", make_analysis))
    note = [NOTE_HEAD]
    out_hashes = {}
    for src, dst, fn in pairs:
        with open(os.path.join(K8, src), encoding="utf-8", newline="") as f:
            a = f.read()
        b = fn(a)
        with open(os.path.join(K8, dst), "w", encoding="utf-8", newline="") as f:
            f.write(b)
        d = "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), src, dst, n=1))
        note.append("\n### %s -> %s (source sha256 %s, output sha256 %s)\n\n```diff\n%s```\n"
                    % (src, dst, hashlib.sha256(a.encode("utf-8")).hexdigest(), hashlib.sha256(b.encode("utf-8")).hexdigest(), d))
        out_hashes[dst] = hashlib.sha256(b.encode("utf-8")).hexdigest()
    with open(os.path.join(K8, "K8_V04_DIFF_NOTE_v01.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(note))
    for k, v in out_hashes.items():
        print(v, k)
    print("MAKE K8 JOINT V04 DONE")


if __name__ == "__main__":
    sys.exit(main())
