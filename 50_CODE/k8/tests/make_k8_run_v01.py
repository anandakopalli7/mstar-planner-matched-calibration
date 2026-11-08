#!/usr/bin/env python3
"""Writes 50_CODE/k8/k8_run_v01.py from 50_CODE/k7/k7_run_v01.py (Claude line, 1 Nov 2026). Changes: it runs k8_sim_v01; the
fit-free arms are S.FITFREE (Z0, B0 and the K8 alpha and delta' arms); the per-decision records that k8_sim_v01 returns under
out["decisions"] are written to decisions_<tag>.npz (one row per decision, with the episode index), the per-episode calibration
tables under out["cal"] to cal_<tag>.npz (episode, key, values), both hashed into the run record; the messages name K8. The design lock under --prereg and the development-scene selection (--dev: the 10 nuScenes-mini
scenes of DEV_SCENES present in the cache manifests) are unchanged."""
import os

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(os.path.dirname(K8), "k7", "k7_run_v01.py"), encoding="utf-8").read()
rep = [
    ('"""K7 episode runner (Claude line, k7_run_v01, 1 Nov 2026) = k6_run_v02 running k7_sim_v01 (tests/make_k7_run_v01.py).\n',
     '"""K8 episode runner (Claude line, k8_run_v01, 1 Nov 2026) = k7_run_v01 running k8_sim_v01 (tests/make_k8_run_v01.py), with the\n'
     'fit-free arms S.FITFREE (Z0, B0, B0a<alpha>, B0d<delta\'>), the per-decision records written to decisions_<tag>.npz and the\n'
     'per-episode calibration tables to cal_<tag>.npz.\n'
     'K7 episode runner (Claude line, k7_run_v01, 1 Nov 2026) = k6_run_v02 running k7_sim_v01 (tests/make_k7_run_v01.py).\n'),
    ('sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport k7_sim_v01 as S  # noqa: E402\n',
     'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\nimport k8_sim_v01 as S  # noqa: E402\n'),
    ('        raise SystemExit("K7 plan hash mismatch")', '        raise SystemExit("K8 plan hash mismatch")'),
    ('            o, c = S.run_decisions(sc, arm, fits if arm not in ("Z0", "B0") else None)\n',
     '            o, c = S.run_decisions(sc, arm, fits if arm not in S.FITFREE else None)\n'),
    ('            o, c = S.run_episode(sc, arm, fits if arm not in ("LOG", "Z0", "B0") else None, d)\n',
     '            o, c = S.run_episode(sc, arm, fits if arm not in S.FITFREE else None, d)\n'),
    ('        pre = "DEV MODE (nuScenes-mini scenes only; excluded from K7)"', '        pre = "DEV MODE (nuScenes-mini scenes only; excluded from K8)"'),
    ('    eps, ce, cc, cn, cx = [], [], [], [], []\n',
     '    eps, ce, cc, cn, cx = [], [], [], [], []\n'
     '    dec = {f: [] for f in S.DEC_FIELDS + ("stats", "episode")}\n'
     '    cal_e, cal_k, cal_v = [], [], []\n'),
    ('            idx = len(eps)\n            o["episode"] = idx\n            eps.append(o)\n',
     '            idx = len(eps)\n            o["episode"] = idx\n'
     '            decs = o.pop("decisions", None)\n'
     '            if decs is not None:\n'
     '                for f_ in S.DEC_FIELDS + ("stats",):\n'
     '                    dec[f_].extend(decs[f_])\n'
     '                dec["episode"].extend([idx] * len(decs["k"]))\n'
     '            cal = o.pop("cal", None) or {}\n'
     '            for key in sorted(cal):\n'
     '                cal_e.append(idx)\n'
     '                cal_k.append(key)\n'
     '                cal_v.append(cal[key])\n'
     '            eps.append(o)\n'),
    ('    np.savez_compressed(ct_path, episode=np.array(ce, np.int32), cell=np.array(cc, np.int32),\n'
     '                        n=np.array(cn, np.int32), exceed=np.array(cx, np.int32))\n',
     '    np.savez_compressed(ct_path, episode=np.array(ce, np.int32), cell=np.array(cc, np.int32),\n'
     '                        n=np.array(cn, np.int32), exceed=np.array(cx, np.int32))\n'
     '    dc_path = os.path.join(a.out, "decisions_%s.npz" % a.tag)\n'
     '    np.savez_compressed(dc_path, episode=np.array(dec["episode"], np.int32), k=np.array(dec["k"], np.int32), ob=np.array(dec["ob"], np.int8),\n'
     '                        infeasible=np.array(dec["infeasible"], np.int8), lam=np.array(dec["lam"], float), v_now=np.array(dec["v_now"], float),\n'
     '                        v_chosen=np.array(dec["v_chosen"], float), v_log=np.array(dec["v_log"], float), ds_plan=np.array(dec["ds_plan"], float),\n'
     '                        ds_log=np.array(dec["ds_log"], float), min_gap=np.array(dec["min_gap"], float), ttc=np.array(dec["ttc"], float),\n'
     '                        n_enf_tracks=np.array(dec["n_enf_tracks"], np.int32), stats=np.array(dec["stats"], float).reshape(-1, S.N_ST))\n'
     '    cl_path = os.path.join(a.out, "cal_%s.npz" % a.tag)\n'
     '    np.savez_compressed(cl_path, episode=np.array(cal_e, np.int32), key=np.array(cal_k, np.int32),\n'
     '                        values=np.array(cal_v, float).reshape(-1, S.N_CAL), fields=np.array(S.CAL_FIELDS))\n'),
    ('"caches": [os.path.abspath(c) for c in a.caches], "episodes_sha256": sha256_path(ep_path), "counts_sha256": sha256_path(ct_path),\n',
     '"caches": [os.path.abspath(c) for c in a.caches], "episodes_sha256": sha256_path(ep_path), "counts_sha256": sha256_path(ct_path),\n'
     '           "decisions_sha256": sha256_path(dc_path), "decisions": len(dec["k"]), "cal_sha256": sha256_path(cl_path),\n'),
    ('    print("K7 RUN DONE")', '    print("K8 RUN DONE")'),
]
for a, b in rep:
    assert s.count(a) == 1, "anchor not found exactly once: " + a[:80]
    s = s.replace(a, b, 1)
open(os.path.join(K8, "k8_run_v01.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k8_run_v01.py written")
