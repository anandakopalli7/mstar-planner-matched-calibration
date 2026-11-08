#!/usr/bin/env python3
"""TPP arm counts (Claude line, v01, 2 Nov 2026): COUNTS AND INTEGRITY CHECKS ONLY on the real run outputs (outcome-blind
until D17 is frozen). Reads the keys file and the run files of one or more trackers; never reads a ground-truth position.
Reports per tracker and source: records and items (all steps and the primary step 2.0 s), relied (PD7) items, SD1_7 and
PD items, per cache class, per history-length stratum {<2, 2, 3-4, >=5}, development scenes, join coverage (K8 records
with a run row, items whose record has a row, rows with status ok), status counts, shapes, finiteness and positive
definiteness of V1 / V2, mixture rows, runtimes. No exceedance, coverage, NEES, quantile, residual or multiplier.
Usage: python -I tpp_counts_v01.py --set t1 <keys> <run_trk> <run_gt> [--set t3 ...] --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_common_v01 as C  # noqa: E402


def counts_for(keys, run_paths):
    kz = np.load(keys, allow_pickle=False)
    nrec = len(kz["rec_k"])
    dev = kz["scene_is_dev"][kz["rec_s"]]
    it_rec = kz["item_rec"]
    h3_rec = kz["rec_h"] == 3
    rel_h3 = kz["item_ref_relied"] & (kz["item_h"] == 3)
    gap_rel = np.where(kz["item_a"] == 0, kz["rec_gap_long"][it_rec], kz["rec_gap_lat"][it_rec])
    out = {"keys": os.path.abspath(keys), "keys_sha256": C.sha256_path(keys), "scenes": int(len(kz["scene_names"])),
           "logs": int(len(np.unique(kz["scene_logs"]))), "dev_scenes": [str(s) for s, d in zip(kz["scene_names"], kz["scene_is_dev"]) if d],
           "records_all_steps": int(nrec), "records_h3": int(h3_rec.sum()), "items_all_steps": int(len(it_rec)),
           "items_h3": int((kz["item_h"] == 3).sum()), "PD7_items_h3": int(rel_h3.sum()),
           "SD1_7_items_h3": int((rel_h3 & (gap_rel <= 5.0)).sum()), "PD_items_h3": int((rel_h3 & kz["item_inpath"]).sum()),
           "records_h3_in_dev_scenes": int((h3_rec & dev).sum()),
           "records_by_step": {str(C.STEP_OF_H[h]): int(np.sum(kz["rec_h"] == h)) for h in range(4)},
           "records_h3_by_class": {C.CLASSES[c]: int(np.sum(h3_rec & (kz["rec_cls"] == c))) for c in range(7)},
           "PD7_items_h3_by_class": {C.CLASSES[c]: int(np.sum(rel_h3 & (kz["rec_cls"][it_rec] == c))) for c in range(7)},
           "records_h3_scenes_with_any": int(len(np.unique(kz["rec_s"][h3_rec]))), "sources": {}}
    for src, rp in run_paths.items():
        z = np.load(rp, allow_pickle=False)
        meta = json.loads(str(z["meta_json"]))
        st = z["status"]
        assert np.array_equal(z["rec_index"], np.arange(nrec)), "run rows are not the keys records 1:1"
        hs = kz["rec_hist_stratum_trk"] if src == "trk" else kz["rec_hist_stratum_gt"]
        hname = {-1: "<2", 0: "2", 1: "3-4", 2: ">=5"}
        ok = st == C.ST_OK
        ok_h3 = ok & h3_rec
        item_ok = ok[it_rec]
        sc = z["scene_seconds"]
        steps = z["steps_k_nodes_edges_dec_sec"]
        o = {"run": os.path.abspath(rp), "run_sha256": C.sha256_path(rp), "checkpoint_sha256": meta["checkpoint_sha256"],
             "seed": meta["seed"], "workers": meta["workers"],
             "join": {"records_with_row": int(len(z["rec_index"])), "records_total": int(nrec),
                      "items_whose_record_has_row": int(len(it_rec)), "records_ok": int(ok.sum()), "records_h3_ok": int(ok_h3.sum()),
                      "PD7_items_h3_ok": int((rel_h3 & item_ok).sum()), "share_records_h3_ok": float(ok_h3.sum() / max(h3_rec.sum(), 1))},
             "status_h3": {C.STATUS_NAMES[c]: int(np.sum(h3_rec & (st == c))) for c in C.STATUS_NAMES},
             "status_all_steps": {C.STATUS_NAMES[c]: int(np.sum(st == c)) for c in C.STATUS_NAMES},
             "records_h3_by_history_stratum": {hname[v]: int(np.sum(h3_rec & (hs == v))) for v in (-1, 0, 1, 2)},
             "records_h3_ok_by_history_stratum": {hname[v]: int(np.sum(ok_h3 & (hs == v))) for v in (-1, 0, 1, 2)},
             "PD7_items_h3_ok_by_history_stratum": {hname[v]: int(np.sum(rel_h3 & item_ok & (hs[it_rec] == v))) for v in (-1, 0, 1, 2)},
             "records_h3_ok_by_class": {C.CLASSES[c]: int(np.sum(ok_h3 & (kz["rec_cls"] == c))) for c in range(7)},
             "PD7_items_h3_ok_by_class": {C.CLASSES[c]: int(np.sum(rel_h3 & item_ok & (kz["rec_cls"][it_rec] == c))) for c in range(7)},
             "PD7_items_h3_ok_dev_scenes": int(np.sum(rel_h3 & item_ok & dev[it_rec])),
             "integrity": {"shapes": {k: list(z[k].shape) for k in ("v1_mu", "v1_cov", "v2_mu", "v2_cov", "mix_w", "mix_mu", "mix_cov")},
                           "ok_rows_all_finite": bool(np.all(np.isfinite(z["v2_mu"][ok])) and np.all(np.isfinite(z["v2_cov"][ok]))
                                                      and np.all(np.isfinite(z["v1_mu"][ok])) and np.all(np.isfinite(z["v1_cov"][ok]))),
                           "ok_rows_v2_pd": int(np.sum(C.min_eig_2x2(z["v2_cov"][ok]) > 0)), "ok_rows": int(ok.sum()),
                           "ok_rows_v1_not_pd": int(np.sum(C.min_eig_2x2(z["v1_cov"][ok]) <= 0)),
                           "ok_rows_v1_not_pd_h3": int(np.sum(C.min_eig_2x2(z["v1_cov"][ok_h3]) <= 0)),
                           "non_ok_rows_all_nan": bool(np.all(np.isnan(z["v2_mu"][~ok]))),
                           "mixture_rows": int(len(z["mix_rec"])),
                           "mixture_rows_equal_predicted_h3": bool(len(z["mix_rec"]) == int(np.sum(h3_rec & np.isin(st, (C.ST_OK, C.ST_NOT_PD, C.ST_NONFINITE))))),
                           "mixture_weights_sum_to_1": bool(np.allclose(z["mix_w"].sum(-1), 1.0, atol=1e-5)) if len(z["mix_w"]) else None,
                           "weights_constant_over_steps": meta.get("weights_constant_over_steps")},
             "runtime": {"wall_seconds": meta["seconds"], "scene_seconds_sum": float(sc.sum()), "scene_seconds_median": float(np.median(sc)),
                         "scene_seconds_max": float(sc.max()), "steps": int(len(steps)), "nodes_per_step_median": float(np.median(steps[:, 1])),
                         "nodes_per_step_max": int(steps[:, 1].max()), "decodes_total": int(steps[:, 3].sum())}}
        out["sources"][src] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", nargs=4, action="append", metavar=("TAG", "KEYS", "RUN_TRK", "RUN_GT"), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {"note": "counts and integrity checks only; no outcome computed (D17 not frozen)",
           "trackers": {t: counts_for(k, {"trk": r1, "gt": r2}) for t, k, r1, r2 in a.set},
           "script_sha256": C.sha256_path(os.path.abspath(__file__))}
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1)[:6000])
    print("TPP COUNTS V01 DONE")


if __name__ == "__main__":
    main()
