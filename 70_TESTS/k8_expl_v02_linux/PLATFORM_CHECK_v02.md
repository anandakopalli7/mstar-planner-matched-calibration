# K8 platform check v02: the two complete analyses compared (2 Nov 2026, 12:35 EST)

**What was compared.**
- The v03 analysis of the **Windows run of record** (`70_TESTS/k8_expl_v02_analysis_v03/`). The run finished at 12:23 EST on 2 Nov, after the power-loss resume via `50_CODE/k8/run_k8_expl_v02_resume_v01.sh`: records archived first, and 312 of 840 loop-t3 shards reused under the runner's hash check.
- The v03 analysis of the **Linux replicate** (`70_TESTS/k8_expl_v02_linux_analysis_v03/`).
- Same code and inputs. See `PLATFORM_CHECK_v01.md` for the per-decision comparison.

## Decision mode (24 headline items)

**Identical on both platforms, for both trackers:**
- HK1, HK2 and HK3;
- Forms A, B and C;
- the set of comparators passing validity (T1: B3; T3: B0, B3);
- the infeasible rates of M*, B4, B6, B0 and B3, to 6 decimals.

**0 differences.**

## Loop mode

- **Collision counts are identical** for all 9 arms on both trackers: episodes, at-fault tracked and at-fault untracked.
- The full per-arm tables (`k8_t*_loop_arms.csv`, 3,844 cells each) differ in 545 cells (T1) and 470 cells (T3). All differences are numeric, and the largest is 4.4e-12 relative, in progress ratios and TTC-proxy means and their interval ends. That is last-bit rounding. No integer or text cell differs.

## Conclusion

- Every K8 conclusion is platform-independent: decision-mode verdicts, rates, comparator sets and loop-mode collision counts.
- The Windows run is the run of record. Numbers quoted in the paper come from it, and are the same as the Linux replicate's to the precision reported.
- R16's review, done on the Linux replicate, therefore applies unchanged to the run of record.
