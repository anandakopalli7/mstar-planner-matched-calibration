"""R09b fixes to k6_analyse_v02.py (MJ3, m2, m4, m6, m9). Run once (Claude line, 1 Nov 2026)."""
import os
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(K, "k6_analyse_v02.py")
s = open(p, encoding="utf-8").read()
assert "R09b" not in s, "already applied"
rep = [
("""  HK1a family: cells with M* records in >= 39 scenes from >= 8 logs whose power to be flagged at a true rate of 0.15 is
  >= 0.80, simulated from M*'s record counts only (beta-binomial, intra-scene correlation 0.3, 200 datasets, seed
  POWER_SEED). HK1a: at least F_MIN family cells and none flagged. HK1b: the pooled cell not flagged. HK1 = HK1a and HK1b.
  HK2: a practitioner arm (B0, B1, B4) flagged in a cell at the Bonferroni level 1 - 0.05/3, where M* is not flagged and
  the paired difference arm - M* is positive at the same level.""",
"""  HK1a (R09b MJ3): no cell flagged in M*'s sup-t over ALL its evaluable cells (>= 39 scenes, >= 8 logs), AND at least
  F_MIN power-qualified cells: evaluable cells whose power to be flagged at a true rate of 0.15 is >= 0.80, simulated from
  M*'s record counts only (beta-binomial, intra-scene correlation 0.5 (R09b m2), 200 datasets, seed POWER_SEED). The
  power-qualified cells are those whose non-rejection is claimed; a flag in any evaluable cell fails HK1a.
  HK1b: the pooled cell not flagged. HK1 = HK1a and HK1b.
  HK2: a practitioner arm (B0, B1, B4) flagged in a cell at the Bonferroni level 1 - 0.05/3 (sup-t over its evaluable
  cells), where M* is not flagged in its own all-evaluable sup-t at level 0.95, and the paired difference arm - M* is
  positive at level 1 - 0.05/3 (sup-t over the cells evaluable for both)."""),
("POWER_P, POWER_MIN, POWER_RHO, POWER_REPS = 0.15, 0.80, 0.3, 200\nF_MIN = 4",
 "POWER_P, POWER_MIN, POWER_RHO, POWER_REPS = 0.15, 0.80, 0.5, 200\nF_MIN = 6"),
("""    res["HK1a_Mstar"] = il_m["Mstar"]""","""    res["HK1a_Mstar_power_qualified"] = il_m["Mstar"]
    res["HK1a_Mstar_all_evaluable"] = pops["PD_primary"]["cells_by_arm"]["Mstar"]"""),
("""    hk1a = len(res["HK1a_family"]) >= F_MIN and not il_m["Mstar"]["sig_above_cells"]""",
"""    hk1a = (len(res["HK1a_family"]) >= F_MIN and not il_m["Mstar"]["sig_above_cells"]
            and not pops["PD_primary"]["cells_by_arm"]["Mstar"]["sig_above_cells"])"""),
("""def check_binding(prereg, runs, tags):
    import k6_run_v02 as R
    side, hashes = R.frozen_hashes(prereg)""","""def check_binding(prereg, runs, tags, manifests):
    import k6_run_v02 as R
    assert list(tags) == ["t1", "t3"], "the tags must be t1 t3, in this order (HK2 is read on T1)"
    side, hashes = R.frozen_hashes(prereg)
    for p in manifests:
        assert sha(p) in hashes, "a manifest passed to the analysis is not frozen: " + p"""),
("""            assert rr["episodes"] == n_ep, "incomplete run %s_%s" % (tag, mode)""","""            assert rr["episodes"] == n_ep, "incomplete run %s_%s" % (tag, mode)
            assert rr["tag"] == "%s_%s" % (tag, mode), "run record %s_%s carries another tag" % (tag, mode)
            assert ("_%s_" % tag) in os.path.basename(rr["fits"]) and all(("cache_v02_%s_" % tag) in c for c in rr["caches"]), \
                "run %s_%s uses another tracker's fits or caches" % (tag, mode)
            for f in ("episodes", "counts"):
                ext = "jsonl" if f == "episodes" else "npz"
                assert sha(os.path.join(runs, "%s_%s_%s.%s" % (f, tag, mode, ext))) == rr["%s_sha256" % f], "%s of run %s_%s changed" % (f, tag, mode)"""),
("""        side = check_binding(a.prereg, a.runs, a.tags)""","""        side = check_binding(a.prereg, a.runs, a.tags, a.manifests)"""),
]
for a_, b_ in rep:
    assert s.count(a_) == 1, a_[:70]
    s = s.replace(a_, b_, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("analysis patched (R09b)")
