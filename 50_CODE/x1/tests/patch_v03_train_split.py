"""One-off patch (30 Oct 2026): make export, splitter and ground-truth prep work on the nuScenes train split (X2 replication).
The tracker parameters are unchanged (experiment paper/local/canmot/sc); only the evaluated split changes. CANMOT's own
validate_config checks the train detection hash against its PAPER_INPUT_HASHES['train'].
"""
import sys

exp, spl, gtp = sys.argv[1], sys.argv[2], sys.argv[3]

s = open(exp, encoding="utf-8").read()
reps = [
    ('HARNESS_VERSION = "x1_export_val_v02 (2026-10-30): v01 + per-worker scene subsets of the approved detection file"',
     'HARNESS_VERSION = "x1_export_v03 (2026-10-30): v02 + --split {val,train} (tracker parameters unchanged)"'),
    ('APPROVED_DETECTION_SHA256 = "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e"',
     'APPROVED_DETECTION_SHA256 = {"val": "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e",\n                             "train": "547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145"}'),
    ('    out["P5"] = out["detection_sha256"] == APPROVED_DETECTION_SHA256',
     '    out["P5"] = out["detection_sha256"] in APPROVED_DETECTION_SHA256.values()'),
    ('    ap.add_argument("--worker", type=int, default=None)',
     '    ap.add_argument("--worker", type=int, default=None)\n    ap.add_argument("--split", default="val", choices=["val", "train"])'),
    ('''        cfg = OmegaConf.to_container(_compose(a.environment, a.experiment), resolve=True)
        split = cfg["dataset_cfg"]["split"]''',
     '''        cfg = OmegaConf.to_container(_compose(a.environment, a.experiment), resolve=True)
        cfg["dataset_cfg"]["split"] = a.split
        split = cfg["dataset_cfg"]["split"]'''),
    ('        rec["criteria"]["P6"] = (cfg.get("experiment_id") == APPROVED_EXPERIMENT and split == "val")',
     '        rec["criteria"]["P6"] = (cfg.get("experiment_id") == APPROVED_EXPERIMENT and split == a.split)'),
    ('''        from nuscenes.utils.splits import val as VAL_SCENES
        scene_names = list(a.scenes) if a.scenes else list(VAL_SCENES)''',
     '''        from nuscenes.utils import splits as SPLITS
        scene_names = list(a.scenes) if a.scenes else list(getattr(SPLITS, a.split))'''),
    ('            assert receipt["source_sha256"] == APPROVED_DETECTION_SHA256 and receipt["partition_exact"]',
     '            assert receipt["source_sha256"] == APPROVED_DETECTION_SHA256[a.split] and receipt["partition_exact"]'),
]
for a_, b_ in reps:
    assert s.count(a_) == 1, a_[:70]
    s = s.replace(a_, b_)
open(exp, "w", encoding="utf-8").write(s)

t = open(spl, encoding="utf-8").read()
reps = [
    ('APPROVED = "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e"',
     'APPROVED = {"val": "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e",\n            "train": "547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145"}'),
    ('    ap.add_argument("--scenes", nargs="*", default=None)', '    ap.add_argument("--scenes", nargs="*", default=None)\n    ap.add_argument("--split", default="val", choices=["val", "train"])'),
    ('    assert src_sha == APPROVED, "source detection file is not the approved one"', '    assert src_sha == APPROVED[a.split], "source detection file is not the approved one"'),
    ('''    from nuscenes.utils.splits import val as VAL
    names = list(a.scenes) if a.scenes else list(VAL)''',
     '''    from nuscenes.utils import splits as SPLITS
    names = list(a.scenes) if a.scenes else list(getattr(SPLITS, a.split))'''),
]
for a_, b_ in reps:
    assert t.count(a_) == 1, a_[:70]
    t = t.replace(a_, b_)
open(spl, "w", encoding="utf-8").write(t)

g = open(gtp, encoding="utf-8").read()
reps = [
    ('    ap.add_argument("--out", required=True)', '    ap.add_argument("--out", required=True)\n    ap.add_argument("--split", default="val", choices=["val", "train"])'),
    ('''    from nuscenes.utils.splits import val as VAL_SCENES''', '''    from nuscenes.utils import splits as SPLITS'''),
    ('    val_names = set(VAL_SCENES)', '    val_names = set(getattr(SPLITS, a.split))'),
    ('''    assert len(sample_rows) == 6019, "expected 6019 val samples"
    assert len(scenes) == 150, "expected 150 val scenes"''',
     '''    assert len(scenes) == {"val": 150, "train": 700}[a.split], "unexpected scene count"
    assert len(sample_rows) == {"val": 6019, "train": 28130}[a.split], "unexpected sample count"'''),
    ('    path = os.path.join(a.out, "x1_val_gt_v02.json")', '    path = os.path.join(a.out, "x2_%s_gt_v03.json" % a.split)'),
]
for a_, b_ in reps:
    assert g.count(a_) == 1, a_[:70]
    g = g.replace(a_, b_)
open(gtp, "w", encoding="utf-8").write(g)
print("patched export, splitter, gt prep")
