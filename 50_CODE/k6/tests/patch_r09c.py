"""R09c fixes (Claude line, 1 Nov 2026): N2 (back-off and emergency-stop shares in outcome_summary), N5 (tracker pairing
checked by content: the fits file's tags and the cache manifests' experiment), N6 (test header). Run once."""
import os

H = os.path.dirname(os.path.abspath(__file__))
K = os.path.dirname(H)
p = os.path.join(K, "k6_analyse_v02.py")
s = open(p, encoding="utf-8").read()
assert "emergency_stop_frame_share" not in s, "already applied"
rep = [
    ('''                    "infeasible_frame_share": float(sum(o["infeasible_frames"] for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),''',
     '''                    "infeasible_frame_share": float(sum(o["infeasible_frames"] for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),
                    "emergency_stop_frame_share": float(sum(o.get("emergency_stop_frames", 0) for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),
                    "backoff_frame_share": float(sum(o["infeasible_frames"] - o.get("emergency_stop_frames", 0) for o in Lst)
                                                 / max(sum(o["frames"] for o in Lst), 1)),'''),
    ('''            same_tracker = ("_%s_" % tag) in os.path.basename(rr["fits"]) and all(("cache_v02_%s_" % tag) in c for c in rr["caches"])
            assert same_tracker, "run %s_%s uses another tracker's fits or caches" % (tag, mode)''',
     '''            same_tracker = ("_%s_" % tag) in os.path.basename(rr["fits"]) and all(("cache_v02_%s_" % tag) in c for c in rr["caches"])
            fits_tags = json.load(open(rr["fits"]))["tags"]
            exps = {json.load(open(os.path.join(c, "MANIFEST.json")))["experiment"] for c in rr["caches"]}
            same_tracker &= fits_tags == ["%s_train" % tag, "%s_val" % tag] and exps == {EXPERIMENT[tag]}   # by content (R09c N5)
            assert same_tracker, "run %s_%s uses another tracker's fits or caches" % (tag, mode)'''),
    ('''N_SCENES_CONF, DELAYS = 840, [0, 2, 4]''',
     '''N_SCENES_CONF, DELAYS = 840, [0, 2, 4]
EXPERIMENT = {"t1": "paper/local/canmot/sc", "t3": "paper/baseline/poly_mot"}'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = os.path.join(H, "test_k6_sim_v02.py")
s = open(p, encoding="utf-8").read()
a = '''T11 margin monotonicity: a car crossing the path after the logged ego, its track appearing 1.5 to 3.5 s before it reaches
    the path, crossing at 3, 6 or 9 m/s, met by the 2 s-delayed ego; margin multiplier 0 to 16: no collision at any dose
    above a collision-free one (strict); progress inversions between neighbouring doses of at most 0.05, and the largest
    dose no faster than dose 0.'''
b = '''T11 margin never creates a collision (R09b's widened grid, 576 late-crossing cases x 9 margin doses): a case free of
    at-fault collisions at dose 0 has none at any larger dose; some cases collide (the test is informative); very late
    detections that already collide at dose 0 are reported.'''
assert s.count(a) == 1
s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("R09c code fixes applied")
