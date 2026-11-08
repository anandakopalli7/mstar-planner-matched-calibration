#!/usr/bin/env python3
"""Rehearsal stand-in for Q1 (Claude line, c1_q1_standin_v01, 4 Nov 2026; used by c1_rehearsal_v05 only; nuScenes data only). QCNet ran
on AV2 only, and the nuScenes Trajectron++ keys carry no (sample, instance) tokens, so the rehearsal makes:
  * keys restricted to the units of a folds file (the rehearsal's folds_val150 child): every rec_* array restricted to those scenes'
    records, every item_* array to their items, every scene_* array to the scenes, with rec_s, item_s and item_rec re-indexed; the cache
    pointer and the code hashes (hashes_json) are kept, so c1_predarm_v05's key chain still checks the bound nuScenes cache;
  * fixture tokens rec_sample_token / rec_instance_token ("tok%07d", "inst%07d");
  * a QCNet-format stand-in file (sample_token, instance_token, v2_mu, v2_cov 2x2, finite, pd_v2) from the TRACKER's own propagated
    prediction of every record (read from the cache by tpp_analyse_v01.load_inputs), rows shuffled (seed 3), so not_predicted = 0.
It is a data-preparation step for the rehearsal, not a C1 entry point; its outputs are chained by content (keys) and by
c1_qcnet_summary_v01 (the stand-in QCNet file). Usage: python -B tests/c1_q1_standin_v01.py --keys <npz> --folds <json> --out-keys <npz>
--out-qcnet <npz>
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(C1), "tpp"))
import tpp_analyse_v01 as TA  # noqa: E402


def restrict(kz, keep_names):
    names = [str(x) for x in kz["scene_names"]]
    s_keep = np.array([n in keep_names for n in names])
    s_new = np.cumsum(s_keep) - 1
    r_keep = s_keep[kz["rec_s"]]
    r_new = np.cumsum(r_keep) - 1
    i_keep = r_keep[kz["item_rec"]]
    n_rec, n_item, n_sc = len(kz["rec_s"]), len(kz["item_rec"]), len(names)
    out = {}
    for k, v in kz.items():
        if k.startswith("rec_"):
            assert len(v) == n_rec, k
            out[k] = v[r_keep]
        elif k.startswith("item_"):
            assert len(v) == n_item, k
            out[k] = v[i_keep]
        elif k.startswith("scene_"):
            assert len(v) == n_sc, k
            out[k] = v[s_keep]
        else:
            out[k] = v
    out["rec_s"] = s_new[kz["rec_s"][r_keep]].astype(kz["rec_s"].dtype)
    out["item_s"] = s_new[kz["item_s"][i_keep]].astype(kz["item_s"].dtype)
    out["item_rec"] = r_new[kz["item_rec"][i_keep]].astype(kz["item_rec"].dtype)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--out-keys", required=True)
    ap.add_argument("--out-qcnet", required=True)
    a = ap.parse_args(argv)
    kz = dict(np.load(a.keys, allow_pickle=False))
    keep = set(json.load(open(a.folds))["fold_of_log"])
    k2 = restrict(kz, keep)
    assert sorted(str(x) for x in k2["scene_names"]) == sorted(keep), "the keys do not cover the folds' units"
    n = len(k2["rec_k"])
    k2["rec_sample_token"] = np.array(["tok%07d" % i for i in range(n)])
    k2["rec_instance_token"] = np.array(["inst%07d" % i for i in range(n)])
    os.makedirs(os.path.dirname(os.path.abspath(a.out_keys)), exist_ok=True)
    np.savez_compressed(a.out_keys, **k2)
    kz3, _, gt_xy, mu, cov = TA.load_inputs(a.out_keys, {}, False, None)
    c22 = np.stack([np.stack([cov[:, 0], cov[:, 1]], -1), np.stack([cov[:, 1], cov[:, 2]], -1)], 1)
    fin = np.isfinite(mu).all(1) & np.isfinite(c22).all((1, 2))
    pd = fin & (cov[:, 0] > 0) & (cov[:, 0] * cov[:, 2] - cov[:, 1] ** 2 > 0)
    perm = np.random.default_rng(3).permutation(n)
    np.savez_compressed(a.out_qcnet, sample_token=k2["rec_sample_token"][perm], instance_token=k2["rec_instance_token"][perm],
                        v2_mu=np.nan_to_num(mu)[perm], v2_cov=np.nan_to_num(c22)[perm], finite=fin[perm], pd_v2=pd[perm])
    print(json.dumps({"units": len(keep), "records": n, "items": int(len(k2["item_rec"])), "pd_share": float(pd.mean())}))
    print("C1 Q1 STAND-IN DONE")


if __name__ == "__main__":
    main()
