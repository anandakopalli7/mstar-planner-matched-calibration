#!/usr/bin/env python3
"""Generator of c1_run_v02.py from c1_run_v01.py (Claude line, 2 Nov 2026), asserted replacements; c1_run_v01 is not modified.
R17 C1 / M2, D16 v09 Choice 24: (1) --standin refuses any cache whose manifest is AV2-tagged or not recognisably nuScenes;
(2) --c1-plan accepts only a FROZEN plan logged in C1_PLAN_HASH_LOG.txt (c1_guard_v01.frozen_plan; paths in the block are relative to
W, so the runner resolves them like the analysis); it requires the folds, the sim and this runner to be bound, checks the fits by
provenance (their plan hash = the sidecar, their folds hash = the folds file, every code hash bound), and requires an AV2 cache to
be stage B with the plan's sidecar hash in its manifest; fits and stage-B manifests are never listed in the plan (no circularity).
Usage (from 50_CODE/c1_av2): python -B tests/make_c1_run_v02.py
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_BLOCK = '''        mans = [json.load(open(os.path.join(c, "MANIFEST.json"))) for c in a.caches]
        dsets = [G.dataset_of_manifest(m_) for m_ in mans]
        if a.standin:   # v02 (R17 M2): a stand-in never touches AV2-derived caches
            assert a.c1_plan is None, "--standin runs without a plan"
            assert all(d_ == "nuscenes" for d_ in dsets), "--standin refuses caches that are not nuScenes: %s" % dsets
            pre = STANDIN_STAMP
        else:           # v02 (D16 v09 Choice 24): frozen plan from the hash log; provenance for everything made after the freeze
            assert a.c1_plan, "a C1 confirmatory run needs --c1-plan (the frozen C1 plan)"
            c1_plan_sha, frozen = G.frozen_plan(a.c1_plan, a.hash_log)
            for p in (a.c1_folds, os.path.abspath(S.__file__), os.path.abspath(__file__)):
                G.require_bound(frozen, p)
            fj_ = json.load(open(a.fits))
            assert fj_.get("folds_sha256") == c1_folds_sha, "the fits were not made for these folds"
            if fj_.get("route") == "transfer":   # made before the freeze: its source fit is bound by the plan
                assert fj_.get("transfer_fit_source_sha256") in frozen.values(), "the transfer fit's source is not bound by the plan"
            else:                                 # made after the freeze: checked by provenance
                prov = fj_.get("provenance") or {}
                assert prov.get("plan_sha256") == c1_plan_sha, "the fits were not made under this frozen plan"
                for k_, h_ in (fj_.get("code_sha256") or {}).items():
                    assert h_ in frozen.values(), "fit code %s is not bound by the plan" % k_
            for m_, d_ in zip(mans, dsets):
                if d_ != "nuscenes":
                    assert m_.get("stage") == "B" and (m_.get("stage_b") or {}).get("frozen_plan_sha256") == c1_plan_sha, \\
                        "an AV2 cache must be stage B, built under this frozen plan"
            pre = C1_STAMP
'''


def rep(s, old, new):
    assert s.count(old) == 1, "expected one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""C1 episode runner (Claude line, c1_run_v01, 2 Nov 2026)',
            '"""C1 episode runner v02 (Claude line, c1_run_v02, 2 Nov 2026) = c1_run_v01 with the binding of D16 v09 Choice 24 and the\n'
            'dataset guard of R17 M2 (written by c1_av2/tests/make_c1_run_v02.py; see that file).\n'
            'C1 episode runner (Claude line, c1_run_v01, 2 Nov 2026)')
    s = rep(s, "import k8_sim_v04 as S  # noqa: E402\n",
            "import k8_sim_v04 as S  # noqa: E402\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport c1_guard_v01 as G  # noqa: E402\n")
    s = rep(s, '    ap.add_argument("--standin", action="store_true", help="C1 stand-in on nuScenes development scenes (no plan)")\n',
            '    ap.add_argument("--standin", action="store_true", help="C1 stand-in on nuScenes development scenes (no plan)")\n'
            '    ap.add_argument("--hash-log", default=G.HASH_LOG, help="the C1 plan hash log (a rehearsal passes its own)")\n')
    old = s[s.index("        if a.standin:\n            assert a.c1_plan is None"):s.index("            pre = C1_STAMP\n") + len("            pre = C1_STAMP\n")]
    s = rep(s, old, NEW_BLOCK)
    s = rep(s, '    print("C1 RUN V01 DONE")\n', '    print("C1 RUN V02 DONE")\n')
    return s


def main():
    with open(os.path.join(C1, "c1_run_v01.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(C1, "c1_run_v02.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "c1_run_v02.py")


if __name__ == "__main__":
    main()
