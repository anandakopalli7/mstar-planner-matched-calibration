#!/usr/bin/env python3
"""Generator of 50_CODE/av2/av2_cache_stageB_v06.py from av2_cache_stageB_v05.py (not modified), asserted replacements (D16 v23 Choice 44f
m1, m2, m7). v06 = v05 on c1_guard_v05: on AV2 the guard writes the chained run-log "start" line before the quarantined ground truth is
read, the deposit record must not name the OSF project and the plan's log line must carry a parsable time, and stale c1_gt_* folders are
swept; the "done" line is chained to the start line. Everything else (deposit first, quarantine only, 30_DATA/av2_cache_stageB_<tag>/
never overwritten, one line in 40_PROTOCOL/C1_STAGE_B_LOG.txt) is v05's.
Usage (from 50_CODE/c1_av2): python -B tests/make_av2_stageB_v06.py
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
    s = rep(s, '"""av2_cache_stageB_v05 = av2_cache_stageB_v04 (kept)',
            '"""av2_cache_stageB_v06 = av2_cache_stageB_v05 (kept) on c1_guard_v05 (D16 v23 Choice 44f), written by c1_av2/tests/make_av2_stageB_v06.py.\n'
            'On AV2: the chained run-log "start" line before any ground truth is read and the "done" line after (m1); the deposit record must not\n'
            'name the OSF project, and the plan\'s log line must carry a parsable time (m2); stale c1_gt_* folders swept (m7).\n'
            'av2_cache_stageB_v05 = av2_cache_stageB_v04 (kept)')
    s = rep(s, "import c1_guard_v04 as G  # noqa: E402\n", "import c1_guard_v05 as G  # noqa: E402\n")
    s = rep(s, 'filled from the GT table by av2_cache_stageB_v05"\n', 'filled from the GT table by av2_cache_stageB_v06"\n')
    return s


def main():
    with open(os.path.join(AV2, "av2_cache_stageB_v05.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    dst = os.path.join(AV2, "av2_cache_stageB_v06.py")
    if os.path.exists(dst):
        assert open(dst, encoding="utf-8", newline="").read() == out, "av2_cache_stageB_v06.py exists and differs from the generator's output"
    else:
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "av2_cache_stageB_v06.py")


if __name__ == "__main__":
    main()
