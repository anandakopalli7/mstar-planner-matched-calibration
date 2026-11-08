"""R09b fixes to k6_oc_v02.py (MJ3 union in A1; m3 informative acceptance; m4 zero-ratio floor) and to
k6_analyse_v02.outcome_summary (MJ1: fallback-related collisions reported apart). Run once (Claude line, 1 Nov 2026)."""
import os

H = os.path.dirname(os.path.abspath(__file__))
K = os.path.dirname(H)

# ---- OC
p = os.path.join(H, "k6_oc_v02.py")
s = open(p, encoding="utf-8").read()
assert "ZERO_FLOOR" not in s, "already applied"
rep = [
    ('TARGET = "car|lat|turning"',
     'TARGET = "car|lat|turning"\n'
     'ZERO_FLOOR = 0.02       # a development ratio of 0 (10 scenes) is floored, not treated as a structural zero (R09b m4)\n'
     'REQUIRED_T1 = ("car|lat|straight", "car|lat|turning")   # informative acceptance (R09b m3): the method-stage failure cells'),
    ('    r = np.array([ratio[c[0]]["ratio"] if ratio[c[0]]["ratio"] is not None else np.nan for c in cells], float)',
     '    r = np.array([max(ratio[c[0]]["ratio"], ZERO_FLOOR) if ratio[c[0]]["ratio"] is not None else np.nan for c in cells], float)'),
    ('                    hk1a = len(fam_idx) >= A.F_MIN and not il["Mstar"]["sig_above_cells"]',
     '                    il_all, _, _, _ = A.inloop_population({"Mstar": N}, {"Mstar": X0}, cells, scene_of_ep, log_of_ep, W)\n'
     '                    hk1a = len(fam_idx) >= A.F_MIN and not il["Mstar"]["sig_above_cells"] and not il_all["Mstar"]["sig_above_cells"]'),
    ('            res["acceptance"][k] = {"A1_le_0.10": v["A1_P_HK1_fails_valid_Mstar"] <= 0.10, "family_ge_floor": v["family_size"] >= A.F_MIN}',
     '            res["acceptance"][k] = {"A1_le_0.10": v["A1_P_HK1_fails_valid_Mstar"] <= 0.10, "family_ge_floor": v["family_size"] >= A.F_MIN}\n'
     '            if k.startswith("t1|"):\n'
     '                res["acceptance"][k]["T1_family_has_moving_car_lateral_cells"] = all(c in v["family"] for c in REQUIRED_T1)'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
s = s.replace("Acceptance (plan v02 section 8): A1 <= 0.10 and family size >= F_MIN in every layout at scale 1; reported otherwise.",
              "Acceptance (plan v02 section 8), at scale 1 in every layout: A1 <= 0.10 (HK1 failing for a valid M*, a flag in ANY evaluable\n"
              "cell counting, R09b MJ3), family size >= F_MIN, and on T1 the family contains car|lat|straight and car|lat|turning\n"
              "(R09b m3). Zero development ratios are floored at 0.02 (R09b m4).", 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)

# ---- analysis: fallback-related collisions apart
p = os.path.join(K, "k6_analyse_v02.py")
s = open(p, encoding="utf-8").read()
assert "fallback_related" not in s, "analysis already patched"
rep = [
    ('''        aft = sum(c["at_fault"] and c["tracked"] for c in real)''',
     '''        aft = sum(c["at_fault"] and c["tracked"] for c in real)
        aft_fb = sum(c["at_fault"] and c["tracked"] and c.get("fallback_related", False) for c in real)'''),
    ('''                    "at_fault_tracked": aft, "at_fault_tracked_per_1000": 1000.0 * aft / n, "at_fault_tracked_ci": poisson_ci(aft, n),''',
     '''                    "at_fault_tracked": aft, "at_fault_tracked_per_1000": 1000.0 * aft / n, "at_fault_tracked_ci": poisson_ci(aft, n),
                    "at_fault_tracked_fallback_related": aft_fb, "at_fault_tracked_not_fallback": aft - aft_fb,'''),
    ('''Closed loop (estimates). Progress, infeasible frames, hard braking, blocked time, collisions (at fault with tracked and
  with untracked agents, not at fault, artefacts: agents the LOG reference at the same delay overlaps), front buffer''',
     '''Closed loop (estimates). Progress, infeasible frames, emergency stops, hard braking, blocked time, collisions (at fault
  with tracked agents, split into fallback-related -- within 2 s of an infeasible decision, when the planner ran at a
  backed-off margin -- and not; with untracked agents; not at fault; artefacts: agents the LOG reference at the same delay
  overlaps). Closed-loop safety contrasts between arms are descriptive and are not interpreted as calibration effects:
  an arm that is infeasible more often runs more often at a backed-off margin (R09b MJ1). Front buffer'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("OC and analysis patched (R09b)")
