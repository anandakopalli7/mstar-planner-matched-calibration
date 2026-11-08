import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_k6_sim_v02.py")
s = open(p, encoding="utf-8").read()
rep = [
('''    ok = (0.5 < o["progress"] < 1.0 and o["infeasible_frames"] > 0 and o["n_collisions"] == 0''',
 '''    ok = (o["infeasible_frames"] > 0 and o.get("emergency_stop_frames", 0) == 0 and o["n_collisions"] == 0'''),
('''    """An oncoming car in the adjacent lane passes with lateral clearance (1.0 m beyond the buffered footprints) below its
    lateral margin (about 1.65 m). Its buffered mean footprint never meets the ego, so under the reference-margin rule
    (v02) the pair is enforced at the arm's margin: passing is not allowed, the ego yields (emergency stops while the
    encounter lasts) and resumes, with no collision. A static car on the path ahead, with the same covariance, stops it."""''',
 '''    """An oncoming car in the adjacent lane passes with lateral clearance (1.0 m beyond the buffered footprints) below its
    lateral margin (about 1.65 m). Its buffered mean footprint never meets the ego, so under the reference-margin rule
    (v02) the pair is enforced at the arm's margin: the decisions of the encounter are infeasible at the margin (counted),
    and the margin back-off (R09b MJ1) lets the ego pass at a reduced margin instead of an emergency stop, with no
    collision. A static car on the path ahead, with the same covariance, stops the ego."""'''),
('''        if d == 0:
            ok &= got["offset"] == [0] and got["inpath"] == [0, 1] and got["enforced"] == [0, 1] and got["satisfied"] == [0, 1]''',
 '''        if d == 0:
            ok &= 0 in got["offset"] and got["inpath"] == [0, 1] and got["enforced"] == [0, 1] and got["satisfied"] == [0, 1]'''),
('''T10 enforcement rules: the ego yields to an oncoming car passing within its margin, then resumes; a static car ahead
    stops it.''','''T10 enforcement rules: an oncoming car passing within its margin is infeasible at the margin, and the ego passes it by the
    margin back-off without an emergency stop or a collision; a static car ahead stops it.'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
