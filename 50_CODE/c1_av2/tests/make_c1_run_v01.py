#!/usr/bin/env python3
"""Generator of c1_run_v01.py from k8_run_v04.py (Claude line, 2 Nov 2026) by asserted text replacements; k8_run_v04 is not modified.
Why a new runner: k8_run_v04's modes are --dev (10 nuScenes development scenes), --exploratory (the 840 nuScenes scenes) and
--prereg (non-development nuScenes scenes); none runs the C1 unit set (the 375 AV2 logs of the folds), binds the C1 plan, or runs
the nuScenes stand-in. c1_run_v01 adds one mode, --c1-folds, with --c1-plan (confirmatory) or --standin; nothing else changes.
Usage (from 50_CODE/c1_av2): python -B tests/make_c1_run_v01.py   (writes c1_run_v01.py; prints its SHA-256)
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K8 = os.path.join(os.path.dirname(C1), "k8")


def rep(s, old, new):
    assert s.count(old) == 1, "expected exactly one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""K8 episode runner (Claude line, k8_run_v04, 2 Nov 2026)',
            '"""C1 episode runner (Claude line, c1_run_v01, 2 Nov 2026) = k8_run_v04 plus one mode for the AV2 confirmation (C1 v04\n'
            'sections 3, 5.1, 7, 11), written by c1_av2/tests/make_c1_run_v01.py. --c1-folds <c1_folds_v01 JSON> runs exactly the units of\n'
            'the folds (the 375 AV2 logs; one log = one scene of the stage-B caches) with the fixed design (every arm of k8_sim_v04.ARMS,\n'
            'joint arms included; delays 0 2 4; decide or loop) and fits made for those folds (fits["folds_sha256"]). With --c1-plan <frozen\n'
            'plan .md> it binds the plan like --prereg (sidecar hash, FROZEN_HASHES block holding the fits, folds, sim, runner and manifests)\n'
            'and stamps C1_STAMP; with --standin it runs nuScenes development scenes treated as logs, stamped STANDIN_STAMP (never evidence).\n'
            'The end-of-run hash guard, shards and --resume are k8_run_v04\'s.\n'
            'C1 usage: python -B c1_run_v01.py --caches <stage-B dirs> --fits <c1 fits> --c1-folds <folds> --c1-plan <plan.md>\n'
            '       --tag <t>_<route>_<mode> --mode decide|loop --out <dir> [--workers n] [--resume]\n'
            'K8 episode runner (Claude line, k8_run_v04, 2 Nov 2026)')
    s = rep(s, "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport k8_sim_v04 as S  # noqa: E402\n",
            "sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \"k8\"))\n"
            "import k8_sim_v04 as S  # noqa: E402\n")
    s = rep(s, 'EXPLORATORY_STAMP = "EXPLORATORY: nuScenes development evidence, not a confirmation"\n',
            'EXPLORATORY_STAMP = "EXPLORATORY: nuScenes development evidence, not a confirmation"\n'
            'C1_STAMP = "C1 CONFIRMATORY: AV2 (run under the frozen C1 plan)"\n'
            'STANDIN_STAMP = "C1 STAND-IN: nuScenes development scenes treated as logs; a pipeline test, not evidence"\n')
    s = rep(s, '              "analysis": os.path.join(W_ROOT, "50_CODE", "k8", "k8_analyse_v04.py"),\n'
               '              "joint_fit": os.path.join(W_ROOT, "50_CODE", "k8", "k8_joint_fit_v01.py"),\n',
            '              "analysis": os.path.join(W_ROOT, "50_CODE", "c1_av2", "c1_analyse_v01.py"),\n'
            '              "k8_analyse_v04": os.path.join(W_ROOT, "50_CODE", "k8", "k8_analyse_v04.py"),\n'
            '              "fit": os.path.join(W_ROOT, "50_CODE", "c1_av2", "c1_fit_v01.py"),\n'
            '              "crc_exact": os.path.join(W_ROOT, "50_CODE", "c1_av2", "c1_crc_exact_v01.py"),\n'
            '              "joint_fit": os.path.join(W_ROOT, "50_CODE", "k8", "k8_joint_fit_v02.py"),\n')
    s = rep(s, '    ap.add_argument("--joint", action="store_true",',
            '    ap.add_argument("--c1-folds", default=None, help="C1: the c1_folds_v01 JSON; runs exactly its units")\n'
            '    ap.add_argument("--c1-plan", default=None, help="C1: the frozen C1 plan (.md with its .sha256 sidecar)")\n'
            '    ap.add_argument("--standin", action="store_true", help="C1 stand-in on nuScenes development scenes (no plan)")\n'
            '    ap.add_argument("--joint", action="store_true",')
    s = rep(s, '    assert int(a.dev) + int(a.exploratory) + int(a.prereg is not None) == 1, "exactly one of --dev, --exploratory, --prereg"\n',
            '    assert int(a.dev) + int(a.exploratory) + int(a.prereg is not None) + int(a.c1_folds is not None) == 1, \\\n'
            '        "exactly one of --dev, --exploratory, --prereg, --c1-folds"\n')
    s = rep(s, "    exploratory = False\n    if a.dev:\n",
            "    exploratory = False\n"
            "    c1_mode, c1_plan_sha, c1_folds_sha = a.c1_folds is not None, None, None\n"
            "    if c1_mode:   # C1: the fixed design on exactly the units of the folds, with fits made for those folds\n"
            "        assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes, \\\n"
            "            \"C1: every arm of k8_sim_v04.ARMS, delays 0 2 4, every unit of the folds (no --scenes)\"\n"
            "        assert a.fits, \"C1 needs the fits\"\n"
            "        c1_folds_sha = sha256_path(a.c1_folds)\n"
            "        units = set(json.load(open(a.c1_folds))[\"fold_of_log\"])\n"
            "        assert json.load(open(a.fits)).get(\"folds_sha256\") == c1_folds_sha, \"the fits were not made for these folds\"\n"
            "        jobs = [j for j in jobs if j[1] in units]\n"
            "        assert {j[1] for j in jobs} == units, \"the caches do not hold every unit of the folds\"\n"
            "        if a.standin:\n"
            "            assert a.c1_plan is None, \"--standin runs without a plan\"\n"
            "            pre = STANDIN_STAMP\n"
            "        else:\n"
            "            assert a.c1_plan, \"a C1 confirmatory run needs --c1-plan (the frozen C1 plan)\"\n"
            "            c1_plan_sha, frozen = frozen_hashes(a.c1_plan)\n"
            "            need = [a.fits, a.c1_folds, os.path.abspath(S.__file__), os.path.abspath(__file__)] + \\\n"
            "                [os.path.join(c, \"MANIFEST.json\") for c in a.caches]\n"
            "            for p in need:\n"
            "                assert sha256_path(p) in frozen, \"run input not frozen: \" + p\n"
            "            pre = C1_STAMP\n"
            "    elif a.dev:\n")
    s = rep(s, '    launch = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": bool(a.dry_run),\n',
            '    launch = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": bool(a.dry_run),\n'
            '              "c1": c1_mode, "standin": bool(a.standin), "c1_plan_sha256": c1_plan_sha, "c1_folds_sha256": c1_folds_sha,\n')
    s = rep(s, '    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": False, "stamp": pre,\n',
            '    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "joint": bool(a.joint), "dry_run": False, "stamp": pre,\n'
            '           "c1": c1_mode, "standin": bool(a.standin), "c1_plan_sha256": c1_plan_sha, "c1_folds_sha256": c1_folds_sha,\n')
    s = rep(s, '    print("K8 RUN V04 DONE")\n', '    print("C1 RUN V01 DONE")\n')
    return s


def main():
    with open(os.path.join(K8, "k8_run_v04.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(C1, "c1_run_v01.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "c1_run_v01.py")


if __name__ == "__main__":
    main()
