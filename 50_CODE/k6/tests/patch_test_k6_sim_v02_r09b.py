"""R09b fixes to test_k6_sim_v02.py (MJ1: widened T11; m5: T12 produces and asserts every bit value; m11: T10 name).
Run once (Claude line, 1 Nov 2026)."""
import os

H = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(H, "test_k6_sim_v02.py")
s = open(p, encoding="utf-8").read()
assert "T11_margin_never_creates_collision" not in s, "already applied"

i = s.index("def t11_dose_monotone(tmp):")
j = s.index("def t13_decision_mode(tmp):")
NEW = '''def t11_dose_monotone(tmp):
    """R09b's widened late-crossing grid: ego 8, 12 or 15 m/s; crossing at 30 or 60 m; track lead 0.5-2.5 s; crossing
    speed 3, 6 or 10 m/s (cars; pedestrians at 3 m/s); delay 1 or 2 s; crossing-time offset -0.75, 0 or +0.75 s; margin
    multiplier 0 to 16 (M* with every threshold = c, sd about 1 m). Property (strict): a case free of at-fault collisions
    at dose 0 has none at any larger dose (the margin never turns a safe encounter into a collision). Informative: some
    cases collide. Cases that already collide at dose 0 but not at every dose are reported (very late detections)."""
    import itertools
    doses = [0.0, 1.0, 1.645, 2.5, 4.0, 6.0, 8.0, 12.0, 16.0]
    grid = list(itertools.product((8.0, 12.0, 15.0), (30.0, 60.0), (0.5, 1.0, 1.5, 2.5), (3.0, 6.0, 10.0), (2, 4), (-0.75, 0.0, 0.75), ("car", "ped")))
    bad, late, n_cases, n_coll = [], [], 0, 0
    for ve, x0, lead_s, vc, dkf, off, kind in grid:
        if kind == "ped" and vc > 3.0:
            continue
        L_, W_ = (4.5, 1.8) if kind == "car" else (0.7, 0.7)
        cls = 0 if kind == "car" else 4
        ego = ego_log(lambda t: ve)
        t_c = x0 / ve + 0.5 * dkf + off
        k_app = max(0, int(math.ceil((t_c - lead_s) / 0.5)))
        tracks, gts = [], []
        for k in range(41):
            y = vc * (0.5 * k - t_c)
            gts.append({"k": k, "inst": 0, "cls": cls, "x": x0, "y": y, "yaw": math.pi / 2, "w": W_, "l": L_, "pts": 10})
            if k >= k_app:
                tracks.append({"k": k, "tid": 0, "cls": cls, "x": x0, "y": y, "yaw": math.pi / 2, "w": W_, "l": L_, "vx": 0.0, "vy": vc,
                               "spd": vc, "omc": 0.0, "inst": 0, "pred": [[x0, y + vc * 0.5 * h, 1.0, 0.0, 1.0] for h in range(1, 9)]})
        sc = make_scene(os.path.join(tmp, "t11.npz"), ego, tracks, gts)
        af = []
        for c in doses:
            fits = [{"Mstar": [c] * 96, "B6": [c] * 96, "B4": c, "B3": c, "B9": c, "B1": [1.0] * 12} for _ in range(8)]
            o, _ = S.run_episode(sc, "Mstar", fits, dkf, record=False)
            if not o["entered"]:
                af = None
                break
            af.append(o["n_at_fault"])
        if af is None:
            continue
        n_cases += 1
        n_coll += int(any(af))
        case = [ve, x0, lead_s, vc, dkf, off, kind]
        if af[0] == 0 and any(af[1:]):
            bad.append({"case": case, "at_fault": af})
        elif af[0] > 0 and not all(af):
            late.append({"case": case, "at_fault": af})
    check("T11_margin_never_creates_collision", not bad and n_coll > 0,
          {"cases": n_cases, "cases_with_any_at_fault": n_coll, "violations": bad[:5], "late_detection_non_monotone": late[:5],
           "n_late_detection_non_monotone": len(late)})


def t12_record_bits(tmp):
    """Every value of every record bit is produced and asserted: in-path 1 (car A) and 0 (car B, not in a rack);
    enforced 0 (an in-lane head-on car whose mean footprint reaches the held ego) and 1; satisfied 0 (decisions with no
    feasible plan at the margin) and 1; offset bin 0 at delay 0 and 2 at a 2 s delay; the bicycle inside a rack is never
    recorded."""
    ego = ego_log(lambda t: 8.0)
    tracks, gts = [], []
    for k in range(41):
        t = 0.5 * k
        a = static_track(k, 0, 120.0, 4.0, 0, cov=(0.01, 0.0, 0.01))
        a["inpath"] = True
        b = static_track(k, 1, 125.0, -4.0, 1, cov=(0.01, 0.0, 0.01))
        b["inpath"] = False
        bk = static_track(k, 2, 70.0, -5.0, 2, cov=(0.01, 0.0, 0.01), cls=6, w=0.6, l=1.7)
        bk["inpath"] = False
        xc = 150.0 - 6.0 * t
        c = {"k": k, "tid": 3, "cls": 0, "x": xc, "y": 0.0, "yaw": math.pi, "w": 1.8, "l": 4.5, "vx": -6.0, "vy": 0.0, "spd": 6.0,
             "omc": 0.0, "inst": 3, "inpath": True, "pred": [[xc - 6.0 * 0.5 * h, 0.0, 0.5, 0.0, 0.5] for h in range(1, 9)]}
        tracks += [a, b, bk, c]
        gts.append({"k": k, "inst": 0, "cls": 0, "x": 120.0, "y": 4.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
        gts.append({"k": k, "inst": 1, "cls": 0, "x": 125.0, "y": -4.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
        gts.append({"k": k, "inst": 2, "cls": 6, "x": 70.0, "y": -5.0, "yaw": 0.0, "w": 0.6, "l": 1.7, "pts": 10, "inrack": True})
        gts.append({"k": k, "inst": 3, "cls": 0, "x": xc, "y": 0.0, "yaw": math.pi, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
    path = os.path.join(tmp, "t12.npz")
    make_scene(path, ego, tracks, gts)
    z = dict(np.load(path))
    z["tr_inpath"] = np.array([t_["inpath"] for t_ in tracks], bool)
    z["gt_inrack"] = np.array([g["inrack"] for g in gts], bool)
    np.savez(path, **z)
    sc = S.Scene(path)
    res, ok = {}, True
    for d, want_ob in ((0, 0), (4, 2)):
        _, cnt = S.run_episode(sc, "B0", None, d)
        bits = [S.decode_cell(cell) for cell in cnt]
        got = {"offset": sorted({x[0] for x in bits}), "inpath": sorted({x[1] for x in bits}), "enforced": sorted({x[2] for x in bits}),
               "satisfied": sorted({x[3] for x in bits}), "groups": sorted({x[7] // 24 for x in bits})}
        res["delay_kf%d" % d] = got
        ok &= 2 not in got["groups"] and want_ob in got["offset"]
        if d == 0:
            ok &= got["offset"] == [0] and got["inpath"] == [0, 1] and got["enforced"] == [0, 1] and got["satisfied"] == [0, 1]
    check("T12_record_bits", ok, res)


'''
s = s[:i] + NEW + s[j:]
s = s.replace('check("T10_uncontrollable_and_brought_not_enforced"', 'check("T10_oncoming_within_margin_yields"', 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("tests patched (R09b)")
