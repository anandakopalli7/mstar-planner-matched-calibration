#!/usr/bin/env python3
"""X3 round-2 refits (x3-core agent, x3_fits_r2_v01, 7 Nov 2026): analyses (e1) and (g).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan sections 2(e1), 2(g).

Common: the items of record (fits_within_<t>.json's item files, hash-checked), J.load_items, c1_fit_v02.load_records, M.levels,
U = D / sd, the frozen folds; per calibrated step h (0.5 to 2 s; the 2.5 to 4 s step dicts are copies, as of record) and, as M*, per
in-path part (192 thresholds = L0 + 96 x in-path, the layout of 'Mstar_ip', which k8_sim_v04.margins reads as threshold x sd).
Every CRC accept/reject is exact (c1_crc_exact_v01, as every CRC of record, E15). delta = 0.05, n_min = 19.

(e1), m_lib_v04.fit_methods' rules ported unchanged except the exact CRC and the in-path split:
  * B5 (per-axis scalars): fit_hier(U, s, lv, start = 3) = one CRC threshold per object axis, per step and in-path part
    (split_fit_exact(..., start = 3));
  * B8 (stratified variance matching): fit_hier(U, s, lv, start = 0, stat = z_0.95 sqrt(mean U^2)) per L0 stratum with its
    fallback (L1, L2, L3 when fewer than 19 calibration logs), per step and in-path part;
  * B7 (learned scale): the calibration logs are permuted by default_rng(seed).permutation (m_lib_v04 re-creates its generator
    with one seed for every fit; here seed = [20261201, i, 5], plan section 0, j = 5 for (e)) and the first half fits the scale
    model: least squares of log(max(|U|, 0.05)) on m_lib_v04.phi's 17 columns; the second half gives the CRC threshold of
    U / exp(phi beta); per step and in-path part. phi needs the track speed and the course-over-ground rate, which the items of
    record do not carry ('spd', 'omc' / '_om_used'); they are read from the stage-B cache at each item's track row (items -> records
    by (log, pair) -> rec_row -> tr_spd, tr_omc), and the items' motion state is re-derived from them as a check.
(g), the learning curve: for n in {25, 50, 100, 200, 300} and repeat r (3 for n < 300), per held-out fold f, the training logs are
the first n of default_rng([20261207, n, r, f]).permutation(the 300 sorted training logs) (n = 300: all of them, no draw); M*'s
fit rule (split_fit_exact, start 0) on them. Check: n = 300 reproduces Mstar_ip and Mstar_ip_src of record exactly. The fallback
share is the share of the 192 x 4 thresholds whose source level is coarser than the own L0 stratum (src > 0). A subsample whose
fit leaves a threshold undefined (no level with 19 logs) is reported as not fittable and not run.
Usage: python -B x3_fits_r2_v01.py --tracker t1 [--parts e1 g]
"""
import argparse
import json
import math
import os
import sys
import time
from functools import partial

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(X3))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "c1_av2"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
sys.path.insert(0, X3)
import c1_crc_exact_v01 as X  # noqa: E402
import c1_fit_v02 as F  # noqa: E402
import k8_joint_fit_v02 as J  # noqa: E402
import x3_common_v01 as C  # noqa: E402
import x3_run_v02 as RUN  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

M = X.M
STEPS = J.STEPS
CC = J.CC_STEPS
N_L0 = M.N_L0
N_MIN = 19
Z95 = 1.6448536269514722
G_N = (25, 50, 100, 200, 300)
E1_DIR = os.path.join(C.OUT, "e_alternatives", "fits")
G_DIR = os.path.join(C.OUT, "g_learning", "fits")


def b8_stat(u, _unit):
    return Z95 * math.sqrt(float(np.mean(u * u)))


def split_hier(U, s, lv, ip, start, stat):
    out, src = np.full(2 * N_L0, np.nan), np.full(2 * N_L0, -1)
    for part in (0, 1):
        sel = ip == part
        thr, so = M.fit_hier(U[sel], s[sel], [x[sel] for x in lv], start, N_MIN, stat=stat)
        out[part * N_L0:(part + 1) * N_L0], src[part * N_L0:(part + 1) * N_L0] = thr, so
    return out, src


def item_spd_omc(it, names, items_paths, tracker):
    """Per item: tr_spd and tr_omc of its track row (items -> records by (scene, pair) -> rec_row -> the stage-B cache)."""
    rs, rp, rrow = [], [], []
    gidx = {n: i for i, n in enumerate(names)}
    for p in items_paths:
        z = np.load(p)
        remap = np.array([gidx[str(x)] for x in z["scene_names"]], np.int64)
        rs.append(remap[z["rec_s"]])
        rp.append(z["rec_pair"])
        rrow.append(z["rec_row"])
    rs, rp, rrow = np.concatenate(rs), np.concatenate(rp), np.concatenate(rrow)
    key_rec = rs.astype(np.int64) * 10_000_000 + rp.astype(np.int64)
    assert len(np.unique(key_rec)) == len(key_rec), "(scene, pair) does not identify a record"
    order = np.argsort(key_rec)
    key_it = it["s"].astype(np.int64) * 10_000_000 + it["pair"].astype(np.int64)
    pos = np.searchsorted(key_rec[order], key_it)
    assert np.all(key_rec[order][np.minimum(pos, len(order) - 1)] == key_it), "an item without its record"
    row_it = rrow[order][pos]
    spd = np.full(len(key_it), np.nan)
    omc = np.full(len(key_it), np.nan)
    cache = C.CACHES[tracker]
    for si, n in enumerate(names):
        sel = np.flatnonzero(it["s"] == si)
        if not len(sel):
            continue
        z = np.load(os.path.join(cache, n + ".npz"))
        spd[sel] = z["tr_spd"][row_it[sel]]
        omc[sel] = z["tr_omc"][row_it[sel]]
    m = np.where(spd < 1.0, 0, np.where(~np.isfinite(omc), 3, np.where(np.abs(np.nan_to_num(omc)) >= 0.10, 2, 1)))
    return spd, omc, bool(np.array_equal(m, it["m"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True, choices=["t1", "t3"])
    ap.add_argument("--parts", nargs="+", default=["e1", "g"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.assert_run_log("x3_fits_r2 start %s" % a.tracker)
    rec = json.load(open(C.FITS_REC[a.tracker]))
    items = [x["file"] for x in rec["items"]]
    for x in rec["items"]:
        assert C.sha256(x["file"]) == x["sha256"], "items of record changed"
    fj = json.load(open(C.FOLDS))
    fold_of = {u: int(f) for u, f in fj["fold_of_log"].items()}
    i_tr = C.TRACKER_I[a.tracker]
    with heavy_lock("x3-core: round-2 refits (e1, g) %s" % a.tracker):
        it, names, info = J.load_items(items)
        assert set(names) == set(fold_of)
        names = list(names)
        rc = F.load_records(items, names)
        fold_unit = np.array([fold_of[n] for n in names], int)
        lv = M.levels(it, it["m"])
        assert np.array_equal(lv[0], it["l0"])
        U = it["D"] / it["sd"]
        ip = it["inpath"].astype(int)
        crc = partial(X.crc_threshold_exact, delta=0.05)
        base = {"stamp": C.STAMP, "tracker": a.tracker, "folds": C.FOLDS, "folds_sha256": C.sha256(C.FOLDS), "items": info,
                "fold_of_scene": fold_of, "rule": __doc__.split("Usage:")[0].strip()}
        summary = {"stamp": C.STAMP, "tracker": a.tracker}
        if "e1" in a.parts:
            spd, omc, m_ok = item_spd_omc(it, names, items, a.tracker)
            assert m_ok, "the items' motion state differs from the one re-derived from tr_spd / tr_omc"
            assert np.all(np.isfinite(spd)), "an item without a track speed"
            seed = [C.SEED_BOOT_X3, i_tr, C.ANALYSIS_J["e"]]
            outs = {k: dict(base, arm=k, fits={}) for k in ("B5", "B8", "B7")}
            b7_info = {}
            for f in range(5):
                cal_log = fold_unit != f
                cal_logs = np.flatnonzero(cal_log)
                perm = np.random.default_rng(seed).permutation(cal_logs)
                fit_half = np.zeros(len(names), bool)
                fit_half[perm[: len(perm) // 2]] = True
                fd = {k: {} for k in outs}
                b7_info[str(f)] = {"fit_half_logs": int(fit_half.sum()), "crc_half_logs": int((cal_log & ~fit_half).sum())}
                for h in range(CC):
                    sel = (it["h"] == h) & cal_log[it["s"]]
                    Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
                    b5, b5s = split_hier(Us, ss, lvs, ips, 3, crc)
                    b8, b8s = split_hier(Us, ss, lvs, ips, 0, b8_stat)
                    beta = np.full((2, 17), np.nan)
                    cth = np.full(2, np.nan)
                    for part in (0, 1):
                        fsel = sel & (ip == part) & fit_half[it["s"]]
                        csel = sel & (ip == part) & ~fit_half[it["s"]]
                        Xf = _lat_cols(RUN.b7_phi(0, it["m"][fsel], it["g"][fsel], it["r"][fsel], it["sd"][fsel], spd[fsel], omc[fsel]),
                                       it["a"][fsel].astype(float), it["m"][fsel], omc[fsel])
                        y = np.log(np.maximum(np.abs(U[fsel]), 0.05))
                        beta[part] = np.linalg.lstsq(Xf, y, rcond=None)[0]
                        Xc = _lat_cols(RUN.b7_phi(0, it["m"][csel], it["g"][csel], it["r"][csel], it["sd"][csel], spd[csel], omc[csel]),
                                       it["a"][csel].astype(float), it["m"][csel], omc[csel])
                        Uc = U[csel] / np.exp(Xc @ beta[part])
                        c_ = X.crc_threshold_exact(Uc, it["s"][csel])
                        cth[part] = np.nan if c_ is None else float(c_)
                        b7_info[str(f)]["h%d_ip%d" % (h, part)] = {"fit_items": int(fsel.sum()), "crc_items": int(csel.sum()),
                                                                     "crc_logs": int(len(np.unique(it["s"][csel])))}
                    for k, thr, src in (("B5", b5, b5s), ("B8", b8, b8s)):
                        assert np.all(np.isfinite(thr)) and np.all(thr > 0), "%s threshold undefined or <= 0" % k
                        fd[k][STEPS[h]] = {"Mstar_ip": thr.tolist(), "Mstar_ip_src": src.astype(int).tolist(), "x3_arm": k}
                    assert np.all(np.isfinite(beta)) and np.all(np.isfinite(cth)) and np.all(cth > 0), "B7 undefined"
                    fd["B7"][STEPS[h]] = {"B7_beta_ip": beta.tolist(), "B7_c_ip": cth.tolist(), "x3_arm": "B7"}
                for k in fd:
                    for h in range(CC, len(STEPS)):
                        fd[k][STEPS[h]] = dict(fd[k][STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
                    outs[k]["fits"][str(f)] = fd[k]
            outs["B7"]["b7_split"] = {"seed": seed, "by_fold": b7_info, "phi_inputs_from_cache": ["tr_spd", "tr_omc"],
                                      "motion_state_rederived_equal": m_ok}
            summary["e1"] = {}
            for k, o in outs.items():
                p = os.path.join(E1_DIR, "fits_x3e1_%s_%s.json" % (k, a.tracker))
                C.jdump(p, o)
                srcs = np.array([o["fits"][f_][s_]["Mstar_ip_src"] for f_ in o["fits"] for s_ in STEPS[:CC]]) if k != "B7" else None
                summary["e1"][k] = {"file": p, "sha256": C.sha256(p),
                                    "source_level_shares": ({str(l_): float(np.mean(srcs == l_)) for l_ in (0, 1, 2, 3)} if srcs is not None else None)}
            print("e1 fits %s done %.0f s" % (a.tracker, time.time() - t0), flush=True)
            C.live("round 2 refits e1 %s" % a.tracker, 1, 2)
        if "g" in a.parts:
            summary["g"] = {}
            for n in G_N:
                for r in range(3 if n < 300 else 1):
                    out = dict(base, n_train_logs=n, repeat=r, fits={}, subsample={})
                    ok = True
                    fb = []
                    for f in range(5):
                        train = sorted(np.flatnonzero(fold_unit != f).tolist())
                        if n < 300:
                            sub = np.random.default_rng([20261207, n, r, f]).permutation(np.array(train))[:n]
                        else:
                            sub = np.array(train)
                        mask = np.zeros(len(names), bool)
                        mask[sub] = True
                        out["subsample"][str(f)] = sorted(names[i] for i in sub)
                        fd = {}
                        for h in range(CC):
                            sel = (it["h"] == h) & mask[it["s"]]
                            thr, src = X.split_fit_exact(U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel], 0)
                            if not np.all(np.isfinite(thr)):
                                ok = False
                            fd[STEPS[h]] = {"Mstar_ip": [None if not np.isfinite(v) else float(v) for v in thr],
                                            "Mstar_ip_src": src.astype(int).tolist()}
                            fb.append(src)
                        for h in range(CC, len(STEPS)):
                            fd[STEPS[h]] = dict(fd[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
                        out["fits"][str(f)] = fd
                    fb = np.array(fb)
                    out["fittable"] = ok
                    out["fallback"] = {"share_coarser_than_L0": float(np.mean(fb > 0)), "share_undefined": float(np.mean(fb < 0)),
                                       "by_level": {str(l_): float(np.mean(fb == l_)) for l_ in (-1, 0, 1, 2, 3)}}
                    if n == 300:
                        eq = all(out["fits"][str(f)][s_]["Mstar_ip"] == rec["fits"][str(f)][s_]["Mstar_ip"]
                                 and out["fits"][str(f)][s_]["Mstar_ip_src"] == rec["fits"][str(f)][s_]["Mstar_ip_src"]
                                 for f in range(5) for s_ in STEPS)
                        out["check_vs_record"] = bool(eq)
                    p = os.path.join(G_DIR, "fits_x3g_%s_n%d_r%d.json" % (a.tracker, n, r))
                    C.jdump(p, out)
                    summary["g"]["n%d_r%d" % (n, r)] = {"file": p, "sha256": C.sha256(p), "fittable": ok, "fallback": out["fallback"],
                                                        "check_vs_record": out.get("check_vs_record")}
                    print("g fits %s n %d r %d fittable %s fallback %.3f%s" % (a.tracker, n, r, ok, out["fallback"]["share_coarser_than_L0"],
                                                                         ("  check %s" % out.get("check_vs_record")) if n == 300 else ""), flush=True)
            C.live("round 2 refits g %s" % a.tracker, 2, 2)
    summary["seconds"] = round(time.time() - t0, 1)
    summary["code_sha256"] = C.code_hashes([os.path.abspath(__file__), X.__file__, M.__file__, F.__file__, J.__file__, RUN.__file__])
    C.assert_run_log("x3_fits_r2 end %s" % a.tracker)
    for part, d in (("e1", "e_alternatives"), ("g", "g_learning")):
        if part in summary:
            C.jdump(os.path.join(C.OUT, d, "fits_r2_%s_%s_summary.json" % (part, a.tracker)),
                    {"stamp": C.STAMP, "tracker": a.tracker, part: summary[part], "seconds_all_parts": summary["seconds"],
                     "code_sha256": summary["code_sha256"]})
    print("X3 FITS R2 DONE %.0f s" % summary["seconds"])


def _lat_cols(Xm, lat, m, omc):
    """phi's axis-dependent columns for items of mixed axes (b7_phi builds them for one axis): lat, lat x motion, omega x axis."""
    st, tu, nw = (m == 0).astype(float), (m == 2).astype(float), (m == 3).astype(float)
    om = np.where(np.isfinite(omc) & (m != 0), np.minimum(np.abs(np.nan_to_num(omc)), 0.5), 0.0)
    Xm = Xm.copy()
    Xm[:, 1], Xm[:, 5], Xm[:, 6], Xm[:, 7] = lat, lat * st, lat * tu, lat * nw
    Xm[:, 15], Xm[:, 16] = om * (1 - lat), om * lat
    return Xm


if __name__ == "__main__":
    main()
