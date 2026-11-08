#!/usr/bin/env python3
"""Writes 50_CODE/k7/k7_sim_v01.py from the frozen 50_CODE/k6/k6_sim_v02.py (Claude line, 1 Nov 2026).
The only functional change: an arm whose fit dictionary carries '<arm>_ip' (192 thresholds: L0 + 96 x in-path) takes its
threshold from the track's (L0 stratum, in-path flag) instead of the L0 stratum alone. The in-path flag is the method's
(the cache's tr_inpath), read for the considered tracks in plan_step and passed to margins(). With fits that have no
'_ip' key (every K6 fit file), the behaviour is that of k6_sim_v02 exactly (test T-K7-1)."""
import os

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(K7), "k6", "k6_sim_v02.py")
s = open(SRC, encoding="utf-8").read()
rep = [
    ('"""K6 log-replay closed-loop harness (Claude line, v02, 1 Nov 2026). Design: 90_DECISIONS/D09_K6_HARNESS_DESIGN_v04.md.\n',
     '"""K7 harness (Claude line, k7_sim_v01, 1 Nov 2026) = k6_sim_v02 with one change, written by tests/make_k7_sim_v01.py:\n'
     '  an arm whose fit dictionary has the key \'<arm>_ip\' (192 thresholds, index L0 + 96 x in-path) takes its threshold\n'
     '  from the track\'s L0 stratum and the method\'s in-path flag (planner-matched calibration, K7); otherwise unchanged.\n'
     'K6 log-replay closed-loop harness (Claude line, v02, 1 Nov 2026). Design: 90_DECISIONS/D09_K6_HARNESS_DESIGN_v04.md.\n'),
    ('def margins(arm, fits, g, r, sd, l0):\n',
     'def margins(arm, fits, g, r, sd, l0, inp=None):\n'),
    ('        elif arm == "B6":\n            out[:, h, :] = np.asarray(f["B6"])[L0] * s\n'
     '        elif arm == "Mstar":\n            out[:, h, :] = np.asarray(f["Mstar"])[L0] * s\n',
     '        elif arm in ("B6", "Mstar") and (arm + "_ip") in f:\n'
     '            out[:, h, :] = np.asarray(f[arm + "_ip"])[L0 + N_L0 * np.asarray(inp, int)[:, None]] * s\n'
     '        elif arm == "B6":\n            out[:, h, :] = np.asarray(f["B6"])[L0] * s\n'
     '        elif arm == "Mstar":\n            out[:, h, :] = np.asarray(f["Mstar"])[L0] * s\n'),
    ('    mg = margins(arm, fits, g, r, sd, l0)                         # (J, 8, 2)\n',
     '    assert "inpath" in sc.tr, "cache without the method\'s in-path flag"   # R12 m5: no silent default\n'
     '    inp_sel = sc.tr["inpath"][sel]\n'
     '    mg = margins(arm, fits, g, r, sd, l0, inp_sel)                # (J, 8, 2)\n'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
open(os.path.join(K7, "k7_sim_v01.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k7_sim_v01.py written")
