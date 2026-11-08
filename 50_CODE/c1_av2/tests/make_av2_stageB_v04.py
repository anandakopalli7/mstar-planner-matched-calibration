#!/usr/bin/env python3
"""Generator of 50_CODE/av2/av2_cache_stageB_v04.py from av2_cache_stageB_v03.py (not modified), asserted replacements (R17c M1, m5;
D16 v18 Choice 39c): v04 is v03 on c1_guard_v03 (the latest line of the C1 hash log only, FROZEN_ENV versions asserted, the log hash
recorded in the stage-B manifest's code record); and D16 v19 Choice 40: before any ground truth is read, an AV2 cache needs the deposit
record 40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt naming the frozen plan (c1_guard_v03.check_deposit; hard-coded path, no override); its
sha256 is recorded in the stage-B manifest (stage_b.deposit_record_sha256), which c1_guard_v03.chain_cache requires. nuScenes is exempt.
Usage (from 50_CODE/c1_av2): python -B tests/make_av2_stageB_v04.py
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AV2 = os.path.join(os.path.dirname(C1), "av2")


def rep(s, old, new):
    assert s.count(old) == 1, "expected one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""av2_cache_stageB_v03 = av2_cache_stageB_v02 (kept)',
            '"""av2_cache_stageB_v04 = av2_cache_stageB_v03 (kept) on c1_guard_v03 (R17c M1, m5), written by c1_av2/tests/make_av2_stageB_v04.py:\n'
            'the latest line of 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only; FROZEN_ENV versions asserted; the log hash recorded; and D16 v19 Choice 40:\n'
            'an AV2 cache needs the deposit record 40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt naming the frozen plan (no override), checked\n'
            'before any ground truth is read; its sha256 goes into stage_b.deposit_record_sha256. nuScenes is exempt.\n'
            'av2_cache_stageB_v03 = av2_cache_stageB_v02 (kept)')
    s = rep(s, "import c1_guard_v02 as G  # noqa: E402\n", "import c1_guard_v03 as G  # noqa: E402\n")
    s = rep(s, 'filled from the GT table by av2_cache_stageB_v03"\n', 'filled from the GT table by av2_cache_stageB_v04"\n')
    s = rep(s, "    plan_sha, rt = None, None\n", "    plan_sha, rt, deposit = None, None, None\n")
    s = rep(s, "            G.check_inputs(frozen, [a.gt])\n", "            G.check_inputs(frozen, [a.gt])\n            deposit = G.check_deposit(plan_sha, dataset)\n")
    s = rep(s, '    out_man["dataset"] = dataset\n',
            '    out_man["dataset"] = dataset\n'
            '    out_man["stage_b"]["deposit_record_sha256"] = deposit["sha256"] if deposit else "exempt (%s)" % dataset\n'
            '    out_man["stage_b"]["deposit"] = deposit\n')
    return s


def main():
    with open(os.path.join(AV2, "av2_cache_stageB_v03.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(AV2, "av2_cache_stageB_v04.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "av2_cache_stageB_v04.py")


if __name__ == "__main__":
    main()
