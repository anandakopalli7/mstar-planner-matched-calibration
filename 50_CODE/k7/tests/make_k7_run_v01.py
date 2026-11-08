#!/usr/bin/env python3
"""Writes 50_CODE/k7/k7_run_v01.py from the frozen 50_CODE/k6/k6_run_v02.py (Claude line, 1 Nov 2026). Changes: it runs
k7_sim_v01 instead of k6_sim_v02, and its messages name K7. The design lock under --prereg (every arm, delays 0 2 4,
every non-development scene; plan sidecar, frozen block and the fits, simulator, runner and manifest hashes) is unchanged."""
import os

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(os.path.dirname(K7), "k6", "k6_run_v02.py"), encoding="utf-8").read()
rep = [
    ('"""K6 episode runner (Claude line, v02, 1 Nov 2026).',
     '"""K7 episode runner (Claude line, k7_run_v01, 1 Nov 2026) = k6_run_v02 running k7_sim_v01 (tests/make_k7_run_v01.py).\n'
     'K6 episode runner (Claude line, v02, 1 Nov 2026).'),
    ('sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport k6_sim_v02 as S  # noqa: E402\n',
     'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport k7_sim_v01 as S  # noqa: E402\n'),
    ('        raise SystemExit("K6 plan hash mismatch")', '        raise SystemExit("K7 plan hash mismatch")'),
    ('        pre = "DEV MODE (nuScenes-mini scenes only; excluded from K6)"', '        pre = "DEV MODE (nuScenes-mini scenes only; excluded from K7)"'),
    ('    print("K6 RUN DONE")', '    print("K7 RUN DONE")'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
open(os.path.join(K7, "k7_run_v01.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k7_run_v01.py written")
