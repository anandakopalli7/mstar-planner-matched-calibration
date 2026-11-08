#!/usr/bin/env python3
"""CANMOT tracker worker for the P3 closed-loop probe (Claude line, v02, 31 Oct 2026). v02: optional --fast-convex
(compiled GIoU hull area, record-identical to native on 604,043 export records).

Runs in the CANMOT environment from the CANMOT repository root. Reads one JSON object per line on stdin:
  {"cmd": "reset"}
  {"cmd": "frame", "frame_id": k, "dets": [{"translation", "size", "velocity", "rotation", "detection_score",
                                             "detection_name"}, ...]}
  {"cmd": "quit"}
and answers one JSON line per frame: {"tracks": [{"tracking_id", "tracking_name", "tracking_score", "translation",
"size", "rotation", "velocity", "cov9"}], "t_s": seconds}.
Pre-processing (score filter, blend NMS) and tracking are CANMOT's own code, configured by the approved experiment
paper/local/canmot/sc; frame data are built exactly as NuScenesloader.__getitem__ builds them.
"""
import json
import os
import sys
import time

import numpy as np


def main():
    repo = os.path.realpath(os.getcwd())
    sys.path.insert(0, os.path.join(repo, "src"))
    from canmot.cli import _compose
    from omegaconf import OmegaConf
    from canmot.pre_processing import dictdet2array, arraydet2box, blend_nms  # noqa: F401
    import canmot.pre_processing as pp
    from canmot.tracking.nusc_tracker import Tracker
    cfg = OmegaConf.to_container(_compose(sys.argv[1] if len(sys.argv) > 1 else "my_machine", "paper/local/canmot/sc"), resolve=True)
    if "--fast-convex" in sys.argv:
        sys.path.insert(0, os.environ.get("FAST_CONVEX_DIR", os.path.dirname(os.path.abspath(__file__))))
        import fast_convex_v01
        fast_convex_v01.install()
    sf = cfg["preprocessing"]["SF_thre"]
    nms_type, nms_metric, nms_thre = cfg["preprocessing"]["NMS_type"], cfg["preprocessing"]["NMS_metric"], cfg["preprocessing"]["NMS_thre"]
    tracker = Tracker(config=cfg)
    out = sys.stdout
    first = True
    for line in sys.stdin:
        msg = json.loads(line)
        if msg["cmd"] == "quit":
            break
        if msg["cmd"] == "reset":
            tracker = Tracker(config=cfg)
            first = True
            out.write(json.dumps({"ok": True}) + "\n")
            out.flush()
            continue
        t0 = time.perf_counter()
        ori = msg["dets"]
        if ori:
            list_dets, np_dets = dictdet2array(ori, "translation", "size", "velocity", "rotation", "detection_score", "detection_name")
            np_dets = np.array([d for d in list_dets if d[-2] > sf[d[-1]]])
        else:
            np_dets = np.zeros(0)
        if len(np_dets) != 0:
            box_dets, corners = arraydet2box(np_dets)
            keep = getattr(pp, nms_type)(box_infos={"np_dets": np_dets, "np_dets_bottom_corners": corners}, metrics=nms_metric, thre=nms_thre)
            keep_num = len(keep)
        else:
            keep = keep_num = 0
        frame = {"is_first_frame": first, "timestamp": int(msg["frame_id"]), "sample_token": "sim_%d" % msg["frame_id"],
                 "seq_id": 0, "frame_id": int(msg["frame_id"]), "has_velo": cfg["basic"]["has_velo"],
                 "np_dets": np_dets[keep] if keep_num else np.zeros(0),
                 "np_dets_bottom_corners": corners[keep] if keep_num else np.zeros(0),
                 "box_dets": box_dets[keep] if keep_num else np.zeros(0), "no_dets": keep_num == 0, "det_num": keep_num}
        first = False
        tracker.tracking(frame)
        tracks = []
        if "no_val_track_result" not in frame:
            for pb in frame["box_track_res"]:
                tracks.append({"tracking_id": str(pb.tracking_id), "tracking_name": pb.name, "tracking_score": float(pb.score),
                               "translation": [float(v) for v in pb.center], "size": [float(v) for v in pb.wlh],
                               "rotation": [float(v) for v in pb.orientation],
                               "velocity": [float(pb.velocity[0]), float(pb.velocity[1])],
                               "cov9": np.asarray(pb.covariance, dtype=float).tolist()})
        out.write(json.dumps({"tracks": tracks, "t_s": time.perf_counter() - t0}) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
