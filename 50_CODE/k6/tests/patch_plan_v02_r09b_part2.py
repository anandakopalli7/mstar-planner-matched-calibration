"""R09b text fixes to K6 plan v02, part 2: sections 4.3, 5, 8 (tables regenerated from the final OC v02), 9 and the new
13b. Run once (Claude line, 1 Nov 2026)."""
import json
import os

import numpy as np
from scipy.stats import norm

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
p = os.path.join(W, "40_PROTOCOL", "K6_PREREGISTRATION_v02.md")
s = open(p, encoding="utf-8").read()
assert "## 13b." not in s, "already applied"
oc = json.load(open(os.path.join(W, "70_TESTS", "k6_scratch", "k6_oc_v02.json")))

# ---- 4.3
rep = [
    ("| Infeasible frames, hard braking, blocked time, mean \\|a\\| | Per arm |",
     "| Infeasible frames, back-off use and emergency stops, hard braking, blocked time, mean \\|a\\| | Per arm |"),
    ("| At-fault collisions with tracked agents | Per 1000 episodes, exact Poisson 95 % interval |",
     "| At-fault collisions with tracked agents, split into fallback-related (within 2 s of an infeasible decision) and not | Per 1000 episodes, exact Poisson 95 % interval. Contrasts between arms are descriptive and are not interpreted as calibration effects (C14) |"),
]
# ---- 5
rep += [
    ("| **HK1a** | M\\* valid in every power-qualified cell | The family is the cells with M\\* records in ≥ 39 scenes from ≥ 8 logs whose simulated power to be flagged at a true rate of 0.15 is ≥ 0.80. The power is computed from M\\*'s record counts only: beta-binomial with intra-scene correlation 0.3, 200 datasets, seed 20261104. HK1a holds when the family has at least F_MIN = 4 cells and none is flagged (simultaneous one-sided 95 % lower bound > δ, or zero SE with estimate > δ). |",
     "| **HK1a** | M\\* valid in every evaluable cell, with at least F_MIN power-qualified cells | Two conditions (C15, R09b MJ3). (i) **No flag:** no cell is flagged in M\\*'s sup-t over *all* its evaluable cells (records in ≥ 39 scenes from ≥ 8 logs), where a flag means a simultaneous one-sided 95 % lower bound > δ, or zero SE with estimate > δ. (ii) **Enough qualified cells:** at least F_MIN = 6 power-qualified cells, also not flagged in their own sup-t. A power-qualified cell is an evaluable cell whose simulated power to be flagged at a true rate of 0.15 is ≥ 0.80. That power is computed from M\\*'s record counts only, under a beta-binomial with intra-scene correlation 0.5 (200 datasets, seed 20261104). The claim of non-exceedance is made for those cells only. The power is ≥ 0.80 under this model, and R09b showed it falls under stronger clustering (R09b m2). |"),
    ("| **HK2** | A practitioner arm fails where M\\* holds | For some b ∈ {B0, B1, B4}, a cell is flagged at level 1 − 0.05/3 (sup-t over b's evaluable cells), M\\* is not flagged there, and the paired difference b − M\\* is positive at level 1 − 0.05/3. |",
     "| **HK2** | A practitioner arm fails where M\\* holds | For some b ∈ {B0, B1, B4}, three conditions hold in the same cell: it is flagged at level 1 − 0.05/3 (sup-t over b's evaluable cells); M\\* is not flagged there in M\\*'s own sup-t over all its evaluable cells at level 0.95 (R09b m9); and the paired difference b − M\\* is positive at level 1 − 0.05/3 (sup-t over the cells evaluable for both). |"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b, 1)

# ---- 8: rebuild from "**Layout.**" to the line before "## 9."
i = s.index("**Layout.**\n- For each confirmatory scene")
j = s.index("## 9. Development scenes")
rows = ["| Layout | Evaluable cells | HK1a family | A1: P(HK1 fails \\| M\\* valid) | P(flag \\| M\\* at 0.15 in the thinnest family cell) | Practitioner power in car\\|lat\\|turning at 0.10 / 0.15 / 0.20 |",
        "|---|---|---|---|---|---|"]
for k, v in oc["layouts"].items():
    t, sc_, rho = k.split("|")
    pp = v["practitioner_power"]
    ps = "not evaluable" if pp is None else "%.2f / %.2f / %.2f" % (pp["0.1"], pp["0.15"], pp["0.2"])
    rows.append("| %s, scale %s, ρ %s | %d | %d | %.3f | %.2f (%s) | %s |" % (t.upper(), sc_.replace("scale", ""), rho.replace("rho", ""), v["evaluable_cells"],
                v["family_size"], v["A1_P_HK1_fails_valid_Mstar"], v["P_HK1a_flags_Mstar_at_0.15_in_thinnest_family_cell"],
                v["thinnest_family_cell"], ps))
a1_s1 = [v["A1_P_HK1_fails_valid_Mstar"] for k, v in oc["layouts"].items() if "|scale1.0|" in k]
fam_s1 = [v["family_size"] for k, v in oc["layouts"].items() if "|scale1.0|" in k]
z = norm.ppf(1 - 0.05 / 4)
hk3 = ["| Tracker | Arm | Development mean (SD) of M\\* − arm, per scene | Power at the development effect, design effect 1 / 2 / 3.5 | Power at half the effect, design effect 1 / 2 / 3.5 |",
       "|---|---|---|---|---|"]
joint = {}
for t in ("t1", "t3"):
    for b, d in oc["HK3_power_" + t].items():
        hk3.append("| %s | %s | %.3f (%.3f) | %.2f / %.2f / %.2f | %.2f / %.2f / %.2f |" % (t.upper(), b, d["dev_mean"], d["dev_sd"], d["power_deff1.0_effect1.0"],
                   d["power_deff2.0_effect1.0"], d["power_deff3.5_effect1.0"], d["power_deff1.0_effect0.5"], d["power_deff2.0_effect0.5"],
                   d["power_deff3.5_effect0.5"]))
        for key in ("power_deff2.0_effect1.0", "power_deff3.5_effect1.0", "power_deff2.0_effect0.5", "power_deff3.5_effect0.5"):
            joint.setdefault(key, 1.0)
            joint[key] *= d[key]
low = sorted(((d["power_deff3.5_effect0.5"], t.upper(), b) for t in ("t1", "t3") for b, d in oc["HK3_power_" + t].items()))[:2]
SEC8 = ("**Layout.**\n"
        "- For each confirmatory scene, the open-loop items per cell are multiplied by that cell's development ratio of M\\*'s PD records to open-loop items. A missing ratio takes the mean of the motion class, or failing that the pooled ratio.\n"
        "- **Zero development ratios are floored at 0.02**, not treated as structural zeros (R09b m4).\n"
        "- The layout is scaled by 0.5, 1 and 2, with ρ ∈ {0.1, 0.3}, 300 datasets and B = 500.\n"
        "- The planted practitioner arm uses M\\*'s layout. Arms are simulated independently, which is conservative for the paired test, since in reality they share residuals (R09 m12).\n"
        "- A1 counts HK1 as failing when *any* evaluable cell is flagged (C15).\n\n"
        "**Acceptance (checked by the freeze script, which reads only the frozen OC file).** At scale 1, in every layout:\n"
        "- A1 = P(HK1 fails | M\\* valid) ≤ 0.10;\n"
        "- the HK1a family has at least F_MIN = 6 cells;\n"
        "- on T1, the family contains car|lat|straight and car|lat|turning, the cells of the method-stage failures. This is the informative criterion (R09b m3).\n\n"
        + "\n".join(rows) + "\n\n"
        "**Reading the table.**\n"
        "- **Acceptance.** It holds in every layout. At scale 1, A1 is %.3f–%.3f and the family has %d–%d cells.\n"
        "- **What acceptance shows.** A1 ≤ 0.10 is a sanity check: a conservative sup-t passes it easily. The informative criterion is that T1's family includes the moving-car lateral cells.\n"
        "- **Practitioner arms.** On T1, a practitioner arm at 0.15 in car|lat|turning is detected with power 0.65–0.99. At 0.10 the power is only 0.06–0.46, so HK2 cannot see small failures.\n"
        "- **T3.** car|lat|turning is barely populated on T3, because the development ratio was 0, floored at 0.02, and HK2 there has little power. HK2 is decided on T1 only.\n"
        "- **False NO-GO.** The probability that a valid M\\* fails HK1 on at least one tracker is about 1 − (1 − %.3f)² ≈ %.2f.\n\n"
        % (min(a1_s1), max(a1_s1), min(fam_s1), max(fam_s1), max(a1_s1), 1 - (1 - max(a1_s1)) ** 2)
        + "**HK3 power.** A normal approximation from the development per-scene paired differences, with a log-cluster design effect of 1, 2 or 3.5 on the standard error, at the development effect and at half of it.\n\n"
        + "\n".join(hk3) + "\n\n"
        "**Joint power.** HK3 needs all 8 one-sided tests (4 arms × 2 trackers). As a product (treating the tests as independent), the joint power is:\n"
        "- at the development effect: %.2f with design effect 2, and %.2f with design effect 3.5;\n"
        "- at half the effect: %.2f with design effect 2, and %.2f with design effect 3.5.\n\n"
        "The weakest single contrasts are %s against %s (%.2f) and %s against %s (%.2f), both at half the effect with design effect 3.5 (R09b m7). The development effects come from 10 scenes.\n\n"
        % (joint["power_deff2.0_effect1.0"], joint["power_deff3.5_effect1.0"], joint["power_deff2.0_effect0.5"], joint["power_deff3.5_effect0.5"],
           low[0][1], low[0][2], low[0][0], low[1][1], low[1][2], low[1][0]))
s = s[:i] + SEC8 + s[j:]

# ---- 9
a = ("The development results are in D09 v04 §1, with data in `70_TESTS/k6_scratch/k6_dev_check_v02.json`. They fixed the planner rules only: nothing in §4–§7 was tuned to their values beyond the design changes listed in D09 v04 §0, and every change there has a stated reason other than the result.")
b = ("**Where the results are.** D09 v04 §1 and D09 v05 §1, with data in `70_TESTS/k6_scratch/k6_dev_check_v02.json` (final rules, dev v08).\n\n"
     "**How they were used (R09b MJ2).**\n"
     "- **To fix the planner rules.** Each change listed in D09 v03–v05 states its reason.\n"
     "- **To choose HK3's endpoint and comparator set.** This was done after dev v07; see \"What had been seen\" item 6.\n"
     "- **The HK1 and HK2 populations** (PD) were set in response to R09, before their development values were inspected for any choice.\n\n"
     "**Not evidence.** Ten scenes from 8 logs support no statement about the arms.")
assert s.count(a) == 1
s = s.replace(a, b, 1)

# ---- 13b
R13B = """
## 13b. Response to R09b

| R09b | Resolution |
|---|---|
| MJ1 | C14 (D09 v05): the margin back-off before the emergency stop, with the infeasibility indicator unchanged. On R09b's widened grid (576 cases × 9 doses), no case free of collisions at dose 0 collides at a larger dose, against 16 such cases before. T11 is now that grid, and 170 of its cases collide at some dose. Fallback-related collisions are flagged, and closed-loop safety contrasts are declared descriptive, not calibration effects (§1, §4.3). |
| MJ2 | "What had been seen" item 6 gives the history of HK3's endpoint and arms, with the development values. B6 is excluded from HK3 with the reason and the foreknowledge stated; "operability against B6" is not claimed. §9 and the iteration count are corrected. |
| MJ3 | C15: HK1a fails on a flag in any evaluable cell. Bounds for all evaluable cells are reported (`HK1a_Mstar_all_evaluable`). The OC's A1 counts the union. |
| m1 | §1: HK3 against B0 on T3 is near-implied. |
| m2 | The power rule uses ρ = 0.5; §5 says "under this model". |
| m3 | The informative acceptance criterion (T1 family contains the moving-car lateral cells); §8 calls A1 a sanity check. |
| m4 | F_MIN = 6; zero ratios are floored at 0.02 in the OC. |
| m5 | T12 produces and asserts every value of the in-path, enforced and satisfied bits. A mutant with the bits hard-coded to 1 now fails it. |
| m6 | Done: the manifests given to the analysis must be frozen; run records hash their outputs, and the analysis checks them; the tracker pairing is checked; the tag order is checked; the freeze reads only the frozen OC. |
| m7 | §8: the weakest contrasts are corrected, and the joint power of HK3 is reported. |
| m8 | "What had been seen" item 2 describes the new 8-step build. |
| m9 | §5 (HK2) states which M\\* family is meant. |
| m10 | §2 discloses the decision-mode replay devices. |
| m11 | Usage lines and the T10 name are fixed. E_rec (S6) is reported beside E_scene. |
"""
k = s.index("FROZEN_HASHES_BEGIN")
s = s[:k] + R13B.lstrip("\n") + "\n" + s[k:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("plan part 2 patched; joint power", {kk: round(vv, 3) for kk, vv in joint.items()})
