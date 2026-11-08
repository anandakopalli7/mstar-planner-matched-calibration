#!/usr/bin/env python3
"""TPP arm cross-platform spot check (Claude line, v01, 2 Nov 2026). Compares two runs of tpp_run_v01 on the same scenes
made on two platforms (laptop Windows reference, Linux pod): predictor self-consistency only, no ground truth is read.
Rows are aligned by (scene name, k, h, pair). Reported: rows matched, status agreement, and the largest absolute
differences of V1 / V2 means (m) and covariances (m^2, also relative to the largest entry of the reference matrix) at
step 4 (2.0 s) and over all steps, the weight summary, and the step-4 mixture (weights, means, covariances). Keys are
compared too: integer fields exactly, the stored geometry within 1e-9.
Gate (for the pod script): statuses identical, every reference row matched, step-4 V2 mean difference <= 0.01 m and
step-4 V2 covariance relative difference <= 0.01; exit code 0 = PASS, 2 = FAIL (the pod script stops on FAIL).
Usage: python -I tpp_xplat_compare_v01.py --ref-keys <k> --ref-run <r> --new-keys <k> --new-run <r> [...more pairs] --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_common_v01 as C  # noqa: E402

TOL_MEAN_M, TOL_COV_REL = 0.01, 0.01


def keyed(kz, z):
    names = kz["scene_names"]
    sel = z["rec_index"]
    keys = [(str(names[s]), int(k), int(h), int(p)) for s, k, h, p in zip(kz["rec_s"][sel], kz["rec_k"][sel], kz["rec_h"][sel], kz["rec_pair"][sel])]
    return {key: i for i, key in enumerate(keys)}


def compare(ref_keys, ref_run, new_keys, new_run):
    ka, kb = np.load(ref_keys, allow_pickle=False), np.load(new_keys, allow_pickle=False)
    za, zb = np.load(ref_run, allow_pickle=False), np.load(new_run, allow_pickle=False)
    ia, ib = keyed(ka, za), keyed(kb, zb)
    common = sorted(set(ia) & set(ib))
    a = np.array([ia[c] for c in common], int)
    b = np.array([ib[c] for c in common], int)
    out = {"ref_run": os.path.abspath(ref_run), "new_run": os.path.abspath(new_run), "ref_rows": len(ia), "new_rows": len(ib),
           "matched": len(common), "status_equal": int(np.sum(za["status"][a] == zb["status"][b]))}
    # keys: integer fields exactly, geometry within 1e-9 (on the matched records)
    ra, rb = za["rec_index"][a], zb["rec_index"][b]
    kint = all(np.array_equal(ka["rec_" + f][ra], kb["rec_" + f][rb]) for f in ("row", "inst", "tid", "cls", "rel", "l0_long", "l0_lat",
                                                                               "hist_trk", "hist_gt", "gt_row", "m", "g", "r"))
    kflt = max(float(np.max(np.abs(ka["rec_" + f][ra] - kb["rec_" + f][rb]))) if len(ra) else 0.0
               for f in ("sign_long", "sign_lat", "cref_x", "cref_y", "cctrv_x", "cctrv_y", "gap_long", "gap_lat", "yaw"))
    out["keys_integer_fields_equal"] = bool(kint)
    out["keys_geometry_max_abs_diff"] = kflt
    ok = (za["status"][a] == C.ST_OK) & (zb["status"][b] == C.ST_OK)
    st4 = ok & (za["step"][a] == 4)

    def mx(x):
        return float(np.max(x)) if x.size else 0.0

    def block(mask):
        r = {}
        for v in ("v1", "v2"):
            dm = np.abs(za[v + "_mu"][a][mask] - zb[v + "_mu"][b][mask])
            dc = np.abs(za[v + "_cov"][a][mask] - zb[v + "_cov"][b][mask])
            scale = np.max(np.abs(za[v + "_cov"][a][mask]), axis=-1, keepdims=True) if mask.any() else np.ones((0, 1))
            r[v] = {"mean_max_abs_m": mx(dm), "cov_max_abs_m2": mx(dc), "cov_max_rel": mx(dc / np.maximum(scale, 1e-12))}
        r["w_max_max_abs"] = mx(np.abs(za["w_max"][a][mask] - zb["w_max"][b][mask]))
        r["w_argmax_equal_share"] = float(np.mean(za["w_argmax"][a][mask] == zb["w_argmax"][b][mask])) if mask.any() else None
        r["rows"] = int(mask.sum())
        return r

    out["step4"] = block(st4)
    out["all_steps"] = block(ok)
    # mixtures at step 4
    ma = {int(j): i for i, j in enumerate(za["mix_rec"])}
    mb = {int(j): i for i, j in enumerate(zb["mix_rec"])}
    pairs = [(ma[x], mb[y]) for x, y in zip(a, b) if x in ma and y in mb]
    if pairs:
        pa, pb = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
        out["mixture_step4"] = {"rows": len(pairs), "w_max_abs": mx(np.abs(za["mix_w"][pa] - zb["mix_w"][pb])),
                                "mu_max_abs_m": mx(np.abs(za["mix_mu"][pa] - zb["mix_mu"][pb])),
                                "cov_max_abs_m2": mx(np.abs(za["mix_cov"][pa] - zb["mix_cov"][pb]))}
    out["gate_pass"] = bool(out["matched"] == out["ref_rows"] and out["status_equal"] == out["matched"] and kint and kflt < 1e-9
                            and out["step4"]["v2"]["mean_max_abs_m"] <= TOL_MEAN_M and out["step4"]["v2"]["cov_max_rel"] <= TOL_COV_REL)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-keys", action="append", required=True)
    ap.add_argument("--ref-run", action="append", required=True)
    ap.add_argument("--new-keys", action="append", required=True)
    ap.add_argument("--new-run", action="append", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert len(a.ref_keys) == len(a.ref_run) == len(a.new_keys) == len(a.new_run)
    res = [compare(*x) for x in zip(a.ref_keys, a.ref_run, a.new_keys, a.new_run)]
    worst = {"step4_v2_mean_max_abs_m": max(r["step4"]["v2"]["mean_max_abs_m"] for r in res),
             "step4_v2_cov_max_abs_m2": max(r["step4"]["v2"]["cov_max_abs_m2"] for r in res),
             "step4_v2_cov_max_rel": max(r["step4"]["v2"]["cov_max_rel"] for r in res),
             "step4_v1_mean_max_abs_m": max(r["step4"]["v1"]["mean_max_abs_m"] for r in res),
             "step4_v1_cov_max_rel": max(r["step4"]["v1"]["cov_max_rel"] for r in res),
             "rows_matched": sum(r["matched"] for r in res), "status_mismatches": sum(r["matched"] - r["status_equal"] for r in res)}
    out = {"pairs": res, "worst": worst, "gate_pass": all(r["gate_pass"] for r in res), "tolerances": {"mean_m": TOL_MEAN_M, "cov_rel": TOL_COV_REL},
           "script_sha256": C.sha256_path(os.path.abspath(__file__)), "note": "predictor self-consistency only; no ground truth read"}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(worst))
    print("XPLAT " + ("PASS" if out["gate_pass"] else "FAIL"))
    sys.exit(0 if out["gate_pass"] else 2)


if __name__ == "__main__":
    main()
