#!/usr/bin/env python3
"""X3 runner v03 (x3-core agent, x3_run_v03, 7 Nov 2026) = x3_run_v02 (kept unchanged) with three additions for amendment A4,
nothing else changed:
  * --mode loop --delays 0 2 4: k8_sim_v04.run_episode per variant and delay (c1_run_v02._scene_job's loop path; base arm LOG allowed
    in loop mode, as the record's loop design runs it for the artefact-collision reference);
  * variant "drop_unmatched": true (A4 (5)): the variant runs on a freshly loaded Scene whose track arrays keep only the rows with
    tr_inst >= 0 (tracks with an annotation match), tr_by_k and the paired-instance index recomputed by the Scene's own code;
  * variant "ego": [L, W] (A4 (3)): k8_sim_v04.EGO_L / EGO_W are set in-process for that variant only (restored after; the buffer
    is unchanged); every geometric use reads the module constants at call time.
X3 decision-mode runner v02 (x3-core agent, x3_run_v02, 7 Nov 2026) = x3_run_v01 (kept unchanged; the round-1 runs used it) with
two additions for round 2 (analyses d, e1, e2, g), nothing else changed:
  * covariance substitution: a variant's "cov_dir" may be a directory of per-scene npz files (pred_cov, tr_k; the runner asserts
    np.array_equal(sc.tr["k"], z["tr_k"]) and then sets sc.tr["pred"] = copy with [:, :, 2:5] = pred_cov, x3-ref's interface), or
    the word "self": the cache's own covariance copied into the same slot (the neutrality check of the substitution step);
  * margin rule "B7" (m_lib_v04's learned scale, analysis e1): k8_sim_v04.strata and k8_sim_v04.margins are wrapped in-process
    (files untouched). The strata wrapper calls the frozen strata unchanged and keeps the track rows; for a B7 variant the margins
    wrapper returns c[h, ip] * exp(phi . beta[h, ip]) * sd per track, step and axis, phi = m_lib_v04.phi's 17 columns built from the
    same quantities (axis, motion state l0 % 4, group, range of the step, log sd, min(tr_spd, 20), the course-over-ground rate
    tr_omc clipped at 0.5 rad/s where finite and moving); every other variant gets the frozen margins unchanged. The base arm of a
    B7 variant is "Mstar" (its covariance for the calibration table is the generic D S' D of margin / sd, as for B6 and M*).
X3 decision-mode runner for arm variants (x3-core agent, x3_run_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).
Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md sections 0, 1, 2(a), 2(b).

A variant = (label, base_arm, fits JSON or None, optional covariance-substitution dir). The base arm decides through k8_sim_v04
unchanged (S.run_decisions, imported read-only; never edited, never run as a program). For each scene the base arm's fits are the
variant's fits for the scene's fold (fits["fits"][fold][step], the layout of the fits of record) and the output arm is relabelled
to the variant's label. The outputs reuse c1_run_v02's scene-job record layout (episodes_<tag>.jsonl, counts_<tag>.npz,
decisions_<tag>.npz, cal_<tag>.npz; per-scene shards merged in (scene, variant) order), so the frozen analysis functions read them.

Covariance substitution: a directory of per-scene npz files holding pred_cov (n_tracks, 8, 3), which replaces the cache's
tr_pred[:, :, 2:5] after loading, for that variant only.

Partition-tagged counts (plan 2(b)): k8_sim_v04._record is wrapped in-process (the module attribute is replaced in this process
only; the file is untouched). The wrapper calls the frozen _record unchanged, then recomputes its locals for the relied records
(PD7 type: relied-on axis with G > 0, enforced, satisfied: the records behind st / cal) and asserts that its per-cell counts equal
_record's own st counts (n and exceedances per near x in-path cell) at every call. Each relied record adds (n, exceed) to
(c4, partition, bin, relied axis), c4 = near * 2 + in-path (k8_sim_v04's 4-cell split). Partitions and bins (fixed by the plan):
  P0 distance to the ego: the range stratum r of the record's L0 (< 20, 20-40, >= 40 m; a partition M*'s strata use; reported);
  P1 track speed tr_spd: [0, 0.5), [0.5, 3), [3, 8), >= 8 m/s;
  P2 track length tr_l: < 2, [2, 5.5), [5.5, 8), >= 8 m;
  P3 track age: keyframes since the track id (tr_tid) first appeared in the log, counting the current keyframe
     (k - first k + 1): 1-2, 3-5, 6-10, > 10;
  P4 detection score tr_score: [0.4, 0.5), [0.5, 0.7), [0.7, 0.85), >= 0.85 (a score below 0.4, if any, goes to bin 4, reported);
  P5 ego speed at the decision v_now = max(v_log(t_k), 0) (run_decisions' own value): < 1, [1, 5), [5, 10), >= 10 m/s;
  P6 annotation lidar points gt_pts at k + h: 1-10, 11-50, 51-200, > 200;
  P7 city of the log (AV2 map manifests): ATX, DTW, MIA, PAO, PIT, WDC.
A non-finite value goes to bin 7 ("missing"), reported. Partition array per episode: (4 * 8 * 8 * 2, 2) int counts, key =
((c4 * 8 + partition) * 8 + bin) * 2 + axis.

Usage: python -B x3_run_v01.py --tracker t1 --variants <spec.json> --tag <tag> --out <dir> [--workers 3] [--resume] [--parts]
spec.json: {"variants": [{"label": "Mstar", "base": "Mstar", "fits": <path or null>, "cov_dir": null}, ...]}
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(X3))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
import k8_sim_v04 as S  # noqa: E402
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
PARTS = ("P0_distance_range", "P1_track_speed", "P2_track_length", "P3_track_age", "P4_detection_score", "P5_ego_speed",
         "P6_gt_lidar_points", "P7_city")
NP_, NB_ = len(PARTS), 8
N_PKEY = 4 * NP_ * NB_ * 2
CITIES = ("ATX", "DTW", "MIA", "PAO", "PIT", "WDC")
BIN_LABELS = {
    "P0_distance_range": ["<20 m", "20-40 m", ">=40 m"],
    "P1_track_speed": ["[0,0.5)", "[0.5,3)", "[3,8)", ">=8"],
    "P2_track_length": ["<2", "[2,5.5)", "[5.5,8)", ">=8"],
    "P3_track_age": ["1-2", "3-5", "6-10", ">10"],
    "P4_detection_score": ["[0.4,0.5)", "[0.5,0.7)", "[0.7,0.85)", ">=0.85", "<0.4"],
    "P5_ego_speed": ["<1", "[1,5)", "[5,10)", ">=10"],
    "P6_gt_lidar_points": ["1-10", "11-50", "51-200", ">200"],
    "P7_city": list(CITIES),
}
MISSING_BIN = 7
_G = {}
_CTX = {"acc": None, "age": None, "city": -1, "checks": 0}
_ORIG_RECORD = S._record
_ORIG_STRATA = S.strata
_ORIG_MARGINS = S.margins


def _strata_x3(sc, rows, k, ego_rear, ego_v, ego_w):
    out = _ORIG_STRATA(sc, rows, k, ego_rear, ego_v, ego_w)
    _CTX["rows"], _CTX["sc"] = rows, sc
    return out


def b7_phi(lat, m, g, r, sd, spd, omc):
    """m_lib_v04.phi's columns for one axis (lat 0/1), per track: motion state m, group g, range r, sd, track speed, omc."""
    n = len(m)
    lat = np.full(n, float(lat))
    st, tu, nw = (m == 0).astype(float), (m == 2).astype(float), (m == 3).astype(float)
    om = np.where(np.isfinite(omc) & (m != 0), np.minimum(np.abs(np.nan_to_num(omc)), 0.5), 0.0)
    cols = [np.ones(n), lat, st, tu, nw, lat * st, lat * tu, lat * nw, (g == 1) * 1.0, (g == 2) * 1.0, (g == 3) * 1.0,
            (r == 1) * 1.0, (r == 2) * 1.0, np.log(sd), np.minimum(spd, 20.0), om * (1 - lat), om * lat]
    return np.column_stack(cols)


def _margins_x3(arm, fits, g, r, sd, l0, inp=None):
    if not _CTX.get("b7"):
        return _ORIG_MARGINS(arm, fits, g, r, sd, l0, inp)
    tr, rows = _CTX["sc"].tr, _CTX["rows"]
    assert len(rows) == sd.shape[0]
    spd, omc = np.asarray(tr["spd"][rows], float), np.asarray(tr["omc"][rows], float)
    m = (np.asarray(l0)[:, 0, 0] % 4).astype(int)
    ipi = np.asarray(inp, int)
    out = np.empty_like(sd)
    for h in range(S.N_STEP):
        beta, c = np.asarray(fits[h]["B7_beta_ip"], float), np.asarray(fits[h]["B7_c_ip"], float)
        for a_ in (0, 1):
            X = b7_phi(a_, m, g, r[:, h], sd[:, h, a_], spd, omc)
            out[:, h, a_] = c[ipi] * np.exp(np.sum(X * beta[ipi], axis=1)) * sd[:, h, a_]
    return out


def pkey(c4, part, b, ax):
    return ((np.asarray(c4) * NP_ + part) * NB_ + np.asarray(b)) * 2 + np.asarray(ax)


def decode_pkey(key):
    rest, ax = divmod(int(key), 2)
    rest, b = divmod(rest, NB_)
    c4, part = divmod(rest, NP_)
    return c4, part, b, ax


def _dig(x, edges):
    x = np.asarray(x, float)
    b = np.digitize(x, edges)
    b[~np.isfinite(x)] = MISSING_BIN
    return b


def track_age(sc):
    """Per track row: keyframes since its track id first appeared in the log, counting the current keyframe (k - first k + 1)."""
    tr = sc.tr
    if not len(tr.get("k", [])):
        return np.zeros(0, int)
    k, tid = tr["k"].astype(int), tr["tid"].astype(int)
    first = {}
    for kk, t in zip(k.tolist(), tid.tolist()):
        if t not in first or kk < first[t]:
            first[t] = kk
    return np.array([kk - first[t] + 1 for kk, t in zip(k.tolist(), tid.tolist())], int)


def _partition(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, enf, st_flat, acc):
    """Recomputes _record's locals for the relied records (k8_sim_v04 lines 825-877, read-only copy of the arithmetic), checks the
    per-cell counts against _record's own st, and adds every record to its partition bins."""
    st = np.asarray(st_flat, float).reshape(4, len(S.ST_FIELDS))
    inst = sc.tr["inst"][sel]
    inpath = sc.tr["inpath"][sel] if "inpath" in sc.tr else np.zeros(len(sel), bool)
    G = gap[choice]
    Sg = sep[choice]
    slack_ax = G - mg.transpose(1, 0, 2)
    relied = np.argmax(slack_ax, axis=-1)
    sat = np.take_along_axis(slack_ax, relied[..., None], -1)[..., 0] >= 0.0
    pair_gap = np.max(G, axis=-1)
    hh, jj, rr = [], [], []
    paired = np.nonzero(inst >= 0)[0]
    inrack = sc.gt["inrack"] if "inrack" in sc.gt else np.zeros(len(sc.gt["k"]), bool)
    for h in range(S.CC_STEPS):
        kk = k + h + 1
        if kk >= sc.K:
            break
        gat = sc.gt_at[kk]
        for j in paired:
            row = gat.get(int(inst[j]))
            if row is not None and not inrack[row]:
                hh.append(h)
                jj.append(j)
                rr.append(row)
    _CTX["checks"] += 1
    if not hh:
        assert st[:, 0].sum() == 0 and st[:, 1].sum() == 0, "partition check: records where _record has none"
        return
    hh, jj, rr = np.array(hh), np.array(jj), np.array(rr)
    e = np.stack([sc.gt["x"][rr] - pred_xy[jj, hh, 0], sc.gt["y"][rr] - pred_xy[jj, hh, 1]], -1)
    pg = pair_gap[hh, jj]
    rel_ = relied[hh, jj]
    ok = (G[hh, jj, rel_] > 0) & enf[hh, jj] & sat[hh, jj]
    if not ok.any():
        assert st[:, 0].sum() == 0 and st[:, 1].sum() == 0, "partition check: no relied record but _record has some"
        return
    h_, j_, e_, a_, r_ = hh[ok], jj[ok], e[ok], rel_[ok], rr[ok]
    D = np.sign(Sg[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)
    exc = (D > mg[j_, h_, a_]).astype(np.int64)
    c4 = (pg[ok] <= S.GAP_BINS[1]).astype(int) * 2 + inpath[j_].astype(int)
    n4 = np.bincount(c4, minlength=4).astype(float)
    x4 = np.bincount(c4, weights=exc.astype(float), minlength=4)
    assert np.array_equal(n4, st[:, 0]) and np.array_equal(x4, st[:, 1]), \
        "partition check: recomputed relied records differ from _record's st (%s %s vs %s %s)" % (n4, x4, st[:, 0], st[:, 1])
    rows = sel[j_]
    v_now = max(sc.v_log(float(sc.kf_t[k])), 0.0)
    score = np.asarray(sc.tr["score"][rows], float)
    b_score = _dig(score, [0.5, 0.7, 0.85])
    b_score[np.isfinite(score) & (score < 0.4)] = 4
    bins = [
        (l0[j_, h_, a_] // 8) % 3,
        _dig(sc.tr["spd"][rows], [0.5, 3.0, 8.0]),
        _dig(sc.tr["l"][rows], [2.0, 5.5, 8.0]),
        _dig(_CTX["age"][rows], [3, 6, 11]),
        b_score,
        _dig(np.full(len(rows), v_now), [1.0, 5.0, 10.0]),
        _dig(sc.gt["pts"][r_], [11, 51, 201]),
        np.full(len(rows), _CTX["city"] if _CTX["city"] >= 0 else MISSING_BIN),
    ]
    for p, b in enumerate(bins):
        key = pkey(c4, p, b, a_)
        np.add.at(acc[:, 0], key, 1)
        np.add.at(acc[:, 1], key, exc)


def _record_x3(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm=None, sd=None, pcov=None, cal=None, lam_exec=1.0):
    """The frozen k8_sim_v04._record, called unchanged; then the partition tagging of its relied records."""
    out = _ORIG_RECORD(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm, sd, pcov, cal, lam_exec)
    acc = _CTX["acc"]
    if acc is not None:
        _partition(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, enf, out[0], acc)
    return out


def install_wrapper():
    S._record = _record_x3
    S.strata = _strata_x3
    S.margins = _margins_x3


def _init(spec, city_idx, fold_of_scene):
    _G["variants"] = spec["variants"]
    _G["fits"] = {}
    for v in spec["variants"]:
        if v.get("fits") and v["fits"] not in _G["fits"]:
            _G["fits"][v["fits"]] = json.load(open(v["fits"]))
    _G["city_idx"] = city_idx
    _G["fold_of_scene"] = fold_of_scene
    install_wrapper()


def drop_unmatched_scene(path):
    """A fresh Scene with only the tracks that have an annotation match (tr_inst >= 0)."""
    sc = S.Scene(path)
    keep = np.asarray(sc.tr["inst"]) >= 0
    n = len(keep)
    for k_ in list(sc.tr):
        v = sc.tr[k_]
        if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == n:
            sc.tr[k_] = v[keep]
    sc.tr_by_k = [np.nonzero(sc.tr["k"] == k)[0] for k in range(sc.K)] if len(sc.tr.get("k", [])) else [np.zeros(0, int)] * sc.K
    sc._paired_by_k()
    return sc, int(n - keep.sum())


def _shard_path(shard_dir, scene):
    return os.path.join(shard_dir, scene + ".npz")


def _scene_job(job):
    """One scene: every variant, one decision-mode episode each, in c1_run_v02._scene_job's record layout, plus the partition
    arrays. Writes one shard (atomic) and returns its path."""
    path, scene, shard_dir, meta, with_parts = job
    mode, delays = meta.get("mode", "decide"), meta.get("delays", [0])
    sc = S.Scene(path)
    _CTX["checks"] = 0
    fold = int(_G["fold_of_scene"][scene])
    _CTX["age"] = track_age(sc)
    _CTX["city"] = int(_G["city_idx"].get(scene, -1))
    pred0 = sc.tr["pred"] if "pred" in sc.tr else None
    t0 = time.perf_counter()
    eps_l = []
    dec = {f: [] for f in S.DEC_FIELDS}
    dec_ep, stats, trk = [], [], []
    ce, cc, cn, cx = [], [], [], []
    ke, kk, kv = [], [], []
    pe, pa = [], []

    def add(o, c, acc):
        li = len(eps_l)
        decs = o.pop("decisions", None)
        cal = o.pop("cal", None) or {}
        o["_local"] = li
        eps_l.append(o)
        if decs is not None and len(decs["k"]):
            for f_ in S.DEC_FIELDS:
                dec[f_].append(np.asarray(decs[f_], np.int32 if f_ in S.DEC_INT else float))
            stats.append(np.asarray(decs["stats"], np.float32).reshape(-1, S.N_ST))
            trk.append(np.asarray(decs["trk"], np.float32).reshape(-1, S.N_TRK))
            dec_ep.append(np.full(len(decs["k"]), li, np.int32))
        for cell in sorted(c):
            ce.append(li)
            cc.append(cell)
            cn.append(c[cell][0])
            cx.append(c[cell][1])
        for key in sorted(cal):
            ke.append(li)
            kk.append(key)
            kv.append(cal[key])
        if acc is not None:
            pe.append(li)
            pa.append(acc.astype(np.int32))

    dropped = {}
    for v in _G["variants"]:
        base = v["base"]
        fits = None
        if base not in S.FITFREE:
            fa = _G["fits"][v["fits"]]
            assert int(fa["fold_of_scene"][scene]) == fold, "the variant's fits map %s to another fold" % scene
            fits = [fa["fits"][str(fold)][h] for h in STEPS]
        if v.get("cov_dir"):
            if v["cov_dir"] == "self":
                pc = pred0[:, :, 2:5].copy()
            else:
                z_ = np.load(os.path.join(v["cov_dir"], scene + ".npz"))
                assert np.array_equal(sc.tr["k"], z_["tr_k"]), "pred_cov rows do not align with the cache's tr_k: " + scene
                pc = z_["pred_cov"]
            assert pred0 is not None and pc.shape == (len(pred0), S.N_STEP, 3), "pred_cov shape %s" % (pc.shape,)
            p = pred0.copy()
            p[:, :, 2:5] = pc
            sc.tr["pred"] = p
        sc_v = sc
        if v.get("drop_unmatched"):
            assert not v.get("cov_dir") and not with_parts, "drop_unmatched runs without substitution or partitions"
            sc_v, dropped[v["label"]] = drop_unmatched_scene(path)
        ego0 = (S.EGO_L, S.EGO_W)
        if v.get("ego"):
            S.EGO_L, S.EGO_W = float(v["ego"][0]), float(v["ego"][1])
        try:
            for d in (delays if mode == "loop" else [0]):
                if mode == "decide" and base == "LOG":
                    continue
                acc = np.zeros((N_PKEY, 2), np.int64) if (with_parts and mode == "decide") else None
                _CTX["acc"] = acc
                _CTX["b7"] = v.get("margin_rule") == "B7"
                try:
                    if mode == "decide":
                        o, c = S.run_decisions(sc_v, base, fits)
                    else:
                        o, c = S.run_episode(sc_v, base, fits, d)
                finally:
                    _CTX["acc"] = None
                    _CTX["b7"] = False
                    if pred0 is not None:
                        sc.tr["pred"] = pred0
                o["arm"] = v["label"]
                o["base_arm"] = base
                for k_ in ("margin_rule", "cov_dir", "drop_unmatched", "ego"):
                    if v.get(k_):
                        o[k_] = v[k_]
                if v.get("drop_unmatched"):
                    o["dropped_unmatched_track_rows"] = dropped[v["label"]]
                o["scene"], o["fold"] = scene, fold
                if mode == "decide":
                    o["delay_kf"] = 0
                add(o, c, acc)
        finally:
            S.EGO_L, S.EGO_W = ego0
    cat = lambda L, dt, shape: np.concatenate(L) if L else np.zeros(shape, dt)  # noqa: E731
    arrs = {"dec_" + f_: cat(dec[f_], np.int32 if f_ in S.DEC_INT else float, (0,)) for f_ in S.DEC_FIELDS}
    arrs.update({"dec_episode": cat(dec_ep, np.int32, (0,)), "dec_stats": cat(stats, np.float32, (0, S.N_ST)),
                 "dec_trk": cat(trk, np.float32, (0, S.N_TRK)),
                 "cnt_episode": np.array(ce, np.int32), "cnt_cell": np.array(cc, np.int32), "cnt_n": np.array(cn, np.int32),
                 "cnt_exceed": np.array(cx, np.int32), "cal_episode": np.array(ke, np.int32), "cal_key": np.array(kk, np.int32),
                 "cal_values": np.array(kv, float).reshape(-1, S.N_CAL),
                 "par_episode": np.array(pe, np.int32), "par_acc": (np.stack(pa) if pa else np.zeros((0, N_PKEY, 2), np.int32))})
    dt = time.perf_counter() - t0
    meta = dict(meta, scene=scene, seconds=dt, partition_checks=_CTX["checks"])
    out = _shard_path(shard_dir, scene)
    tmp = out[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, meta=np.array(json.dumps(meta)), episodes=np.array(json.dumps(eps_l)), **arrs)
    os.replace(tmp, out)
    return scene, out, len(eps_l), dt


def _shard_ok(p, meta):
    try:
        z = np.load(p)
        m = json.loads(str(z["meta"]))
    except Exception:
        return False
    return all(m.get(k) == v for k, v in meta.items())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True, choices=["t1", "t3", "tab"])
    ap.add_argument("--variants", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--parts", action="store_true", help="partition-tagged counts (analysis b)")
    ap.add_argument("--scenes", nargs="*", default=None, help="test only: a subset of scenes (the merge is then partial)")
    ap.add_argument("--mode", choices=["decide", "loop"], default="decide")
    ap.add_argument("--delays", nargs="+", type=int, default=[0, 2, 4])
    a = ap.parse_args(argv)
    assert 1 <= a.workers <= 3, "at most 3 workers"
    out_abs = os.path.abspath(a.out)
    assert out_abs.startswith(os.path.abspath(C.OUT)), "X3 outputs go under 60_RESULTS/x3_explore_v01"
    t0 = time.time()
    C.assert_run_log("x3_run start " + a.tag)
    spec = json.load(open(a.variants))
    labels = [v["label"] for v in spec["variants"]]
    assert len(set(labels)) == len(labels), "variant labels must be unique"
    for v in spec["variants"]:
        assert v["base"] in S.ARMS and (v["base"] != "LOG" or a.mode == "loop"), "unknown base arm " + v["base"]
        assert v.get("margin_rule") in (None, "B7") and (v.get("margin_rule") != "B7" or v["base"] == "Mstar"), "B7 runs on base Mstar"
        assert (v.get("fits") is not None) == (v["base"] not in S.FITFREE), "fits iff the base arm takes fits: " + v["label"]
    cache = C.CACHES[a.tracker]
    man = json.load(open(os.path.join(cache, "MANIFEST.json")))
    folds = json.load(open(C.FOLDS))
    fold_of_scene = {s: int(f) for s, f in folds["fold_of_log"].items()}
    jobs = [(os.path.join(cache, s + ".npz"), s, info["sha256"]) for s, info in sorted(man["scenes"].items())]
    assert {j[1] for j in jobs} == set(fold_of_scene), "the cache's scenes differ from the folds' logs"
    for v in spec["variants"]:
        if v.get("fits"):
            fj = json.load(open(v["fits"]))
            assert {s: int(f) for s, f in fj["fold_of_scene"].items()} == fold_of_scene, "fits with other folds: " + v["fits"]
            del fj
    if a.scenes:
        jobs = [j for j in jobs if j[1] in set(a.scenes)]
    for p, scene, h in jobs:
        assert C.sha256(p) == h, "cache file differs from its manifest: " + p
    city, city_src = C.city_of_log()
    city_idx = {s: CITIES.index(city[s]) for s in fold_of_scene if s in city}
    code = C.code_hashes([os.path.abspath(S.__file__), os.path.abspath(__file__), os.path.abspath(C.__file__)])
    vspec = [{"label": v["label"], "base": v["base"], "fits_sha256": C.sha256(v["fits"]) if v.get("fits") else None,
              "cov_dir": v.get("cov_dir"), "cov_manifest_sha256": C.sha256(os.path.join(v["cov_dir"], "MANIFEST.json"))
              if v.get("cov_dir") not in (None, "self") and os.path.exists(os.path.join(v["cov_dir"], "MANIFEST.json")) else None,
              "margin_rule": v.get("margin_rule"), "drop_unmatched": bool(v.get("drop_unmatched")), "ego": v.get("ego")} for v in spec["variants"]]
    shard_dir = os.path.join(out_abs, "shards_%s" % a.tag)
    os.makedirs(shard_dir, exist_ok=True)
    meta0 = {"tag": a.tag, "tracker": a.tracker, "variants": vspec, "parts": bool(a.parts), "code": code, "stamp": C.STAMP,
             "mode": a.mode, "delays": list(a.delays) if a.mode == "loop" else [0]}
    todo, reused = [], []
    for p, scene, h in jobs:
        meta = dict(meta0, cache_sha256=h)
        sp = _shard_path(shard_dir, scene)
        if a.resume and os.path.exists(sp) and _shard_ok(sp, dict(meta, scene=scene)):
            reused.append(scene)
            continue
        todo.append((p, scene, shard_dir, meta, bool(a.parts)))
    print("x3_run %s: %d scenes, %d to run, %d reused, %d variants" % (a.tag, len(jobs), len(todo), len(reused), len(labels)), flush=True)
    times = []
    if todo:
        with heavy_lock("x3-core: decision-mode run %s" % a.tag):
            with Pool(a.workers, initializer=_init, initargs=(spec, city_idx, fold_of_scene)) as pool:
                for i, (scene, sp, n_ep, dt) in enumerate(pool.imap_unordered(_scene_job, todo, chunksize=1)):
                    times.append(dt)
                    if (i + 1) % 25 == 0 or i + 1 == len(todo):
                        print("scenes %d/%d  %.0f s" % (i + 1, len(todo), time.time() - t0), flush=True)
                        C.live("run " + a.tag, len(reused) + i + 1, len(jobs))
    # merge in (scene, variant) order: c1_run_v02's layout
    rank = {x: i for i, x in enumerate(labels)}
    scene_names = sorted(j[1] for j in jobs)
    eps, parts, shard_times, checks = [], {}, [], 0
    for scene in scene_names:
        z = np.load(_shard_path(shard_dir, scene))
        m = json.loads(str(z["meta"]))
        assert m["scene"] == scene and m["code"] == code and m["variants"] == vspec, "shard of %s made by other code or variants" % scene
        shard_times.append(float(m["seconds"]))
        checks += int(m.get("partition_checks", 0))
        eps_l = json.loads(str(z["episodes"]))
        order = sorted(range(len(eps_l)), key=lambda i: (rank[eps_l[i]["arm"]], eps_l[i]["delay_kf"]))
        remap = np.zeros(len(eps_l), np.int64)
        for i in order:
            o = eps_l[i]
            o.pop("_local", None)
            o["episode"] = len(eps)
            o["stamp"] = C.STAMP
            remap[i] = len(eps)
            eps.append(o)
        for pre_, fields in (("dec_", ["episode"] + list(S.DEC_FIELDS) + ["stats", "trk"]), ("cnt_", ["episode", "cell", "n", "exceed"]),
                             ("cal_", ["episode", "key", "values"]), ("par_", ["episode", "acc"])):
            ep_new = remap[z[pre_ + "episode"]] if len(z[pre_ + "episode"]) else np.zeros(0, np.int64)
            perm = np.argsort(ep_new, kind="stable")
            for f_ in fields:
                v = ep_new if f_ == "episode" else z[pre_ + f_]
                parts.setdefault(pre_ + f_, []).append(v[perm])
    cat = lambda k, dt: np.concatenate(parts[k]).astype(dt) if parts.get(k) else np.zeros(0, dt)  # noqa: E731
    ep_path, ct_path = os.path.join(out_abs, "episodes_%s.jsonl" % a.tag), os.path.join(out_abs, "counts_%s.npz" % a.tag)
    tmp = ep_path + ".tmp"
    with open(tmp, "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    os.replace(tmp, ep_path)

    def savez(path, **kw):
        tmp_ = path[:-4] + ".tmp.npz"
        np.savez_compressed(tmp_, **kw)
        os.replace(tmp_, path)
    savez(ct_path, episode=cat("cnt_episode", np.int32), cell=cat("cnt_cell", np.int32), n=cat("cnt_n", np.int32),
          exceed=cat("cnt_exceed", np.int32), stamp=np.array(C.STAMP))
    dc_path = os.path.join(out_abs, "decisions_%s.npz" % a.tag)
    darr = {"episode": cat("dec_episode", np.int32)}
    for f_ in S.DEC_FIELDS:
        darr[f_] = cat("dec_" + f_, np.int32 if f_ in S.DEC_INT else float)
    darr["ob"] = darr["ob"].astype(np.int8)
    darr["infeasible"] = darr["infeasible"].astype(np.int8)
    darr["stats"] = np.concatenate(parts["dec_stats"]).astype(np.float32).reshape(-1, S.N_ST) if parts.get("dec_stats") else np.zeros((0, S.N_ST), np.float32)
    darr["trk"] = np.concatenate(parts["dec_trk"]).astype(np.float32).reshape(-1, S.N_TRK) if parts.get("dec_trk") else np.zeros((0, S.N_TRK), np.float32)
    savez(dc_path, st_fields=np.array(S.ST_FIELDS), trk_fields=np.array(S.TRK_FIELDS), stamp=np.array(C.STAMP), **darr)
    cl_path = os.path.join(out_abs, "cal_%s.npz" % a.tag)
    savez(cl_path, episode=cat("cal_episode", np.int32), key=cat("cal_key", np.int32),
          values=(np.concatenate(parts["cal_values"]) if parts.get("cal_values") else np.zeros((0, S.N_CAL))).reshape(-1, S.N_CAL),
          fields=np.array(S.CAL_FIELDS), stamp=np.array(C.STAMP))
    rec_extra = {}
    if a.parts:
        pa_path = os.path.join(out_abs, "parts_%s.npz" % a.tag)
        acc = np.concatenate(parts["par_acc"]).astype(np.int32) if parts.get("par_acc") else np.zeros((0, N_PKEY, 2), np.int32)
        savez(pa_path, episode=cat("par_episode", np.int32), acc=acc, parts=np.array(PARTS), cities=np.array(CITIES),
              bin_labels=np.array(json.dumps(BIN_LABELS)), key_rule=np.array("key = ((c4 * 8 + partition) * 8 + bin) * 2 + axis; "
                                                                             "c4 = near * 2 + inpath; axis 0 long, 1 lat; bin 7 missing"),
              stamp=np.array(C.STAMP))
        rec_extra = {"parts_sha256": C.sha256(pa_path), "partition_checks": checks,
                     "city_sources": city_src, "city_logs": len(city_idx)}
    code_end = C.code_hashes([os.path.abspath(S.__file__), os.path.abspath(__file__), os.path.abspath(C.__file__)])
    assert code_end == code, "code changed during the run"
    rl = C.assert_run_log("x3_run end " + a.tag)
    rec = {"stamp": C.STAMP, "tag": a.tag, "tracker": a.tracker, "mode": a.mode, "delays": meta0["delays"], "variants": spec["variants"], "variants_hashed": vspec,
           "scenes": len(scene_names), "partial": bool(a.scenes), "episodes": len(eps), "decisions": int(len(darr["k"])),
           "cache": cache, "cache_manifest_sha256": C.sha256(os.path.join(cache, "MANIFEST.json")), "folds_sha256": C.sha256(C.FOLDS),
           "code_sha256": code, "numpy": np.__version__, "workers": a.workers, "shards_reused": len(reused),
           "episodes_sha256": C.sha256(ep_path), "counts_sha256": C.sha256(ct_path), "decisions_sha256": C.sha256(dc_path),
           "cal_sha256": C.sha256(cl_path), "seconds": round(time.time() - t0, 1),
           "scene_seconds_median": float(np.median(shard_times)) if shard_times else None,
           "scene_seconds_sum": float(np.sum(shard_times)) if shard_times else None, "run_log_sha256_end": rl}
    rec.update(rec_extra)
    C.jdump(os.path.join(out_abs, "run_record_%s.json" % a.tag), rec)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("variants", "variants_hashed", "city_sources")}))
    print("X3 RUN V03 DONE")


if __name__ == "__main__":
    main()
