# C1 criteria: development check of rule set R*2 (v03, 5 Nov 2026)

## Short answer

Under R\*2 the development verdict is the same as v02's on both trackers.

| | T1 | T3 |
|---|---|---|
| Valid(M\*) | yes | yes |
| V_t | {B3} | {B0, B3} |
| Form A, Form B, Form C | met | met |
| H10 | holds | holds |
| H3 | passes at every Holm level (0.005 to 0.025) | passes at every Holm level |
| H3's doubled p | 0 | 0 |

- **Stability.** In 100 independent seed sets per tracker (B = 20,000 each), V_t and V^J membership never differ from the primary result. Valid(M\*), Form B, H10 and H3 hold in every set.
- **Monte Carlo error.** The MC SE of every decisive bound is ≤ 0.0006.
- **Operating characteristics at 375 units** (B = 20,000, 300 sets): P(H1) = 0.870 with plug-in rates and 0.933 with M\* capped at δ. Failure is driven by T1's HK1c, as in v02.
- **B1 and B9** now stay in V_t in 9–16 % of sets. When they do, M\* beats them in every such set.
- **The L check.** With B = 20,000, M\*'s pooled-UB coverage at L = 0.995 is unchanged within MC error.

## What was run

**R\*2** is R\* (check v02) changed by D16 v33 Choice 52(c) and (d):
- removal from V_t: each of the 9 conditions at 1 − 0.0125/9;
- Form B at UB^{1 − 0.0125/|V_t|};
- H3: V^J removal at 1 − 0.0025/3, p_H3 = min(1, 2 |V^J| max_c p_c), judged at the Holm levels;
- B = 20,000 for every observed-data bootstrap. The power rule keeps 2000 datasets and the first 500 weights.

Unchanged: the flags against M\* (0.95), HK1c at L = 0.995 ≤ δ + 0.03, and Form C and H10's NI at 0.975.

**Data.** nuScenes development data only:
- the K8 Linux replicate, its v03 analysis and the K8 joint run;
- v01's development caches, and v02's power families for B0 and B3.

No Argoverse 2 file of any kind was read. v01 and v02 still hash-check: 306/306 and 52/52.

**Code.** The new code is `50_CODE/c1_criteria/c1crit_rstar2_v03.py`, with `c1crit_rstar2_summary_v03.py` for the combination. It reuses v02's R\* functions and the project's analysis code by import.

The log-level shortcuts used for E3 (`rates_log`, `paired_log`) were asserted equal to `k6_analyse_v02.rates` and `c1_analyse_v02.paired` on the primary weights before use.

**Compute.**
- At most 3 compute processes ran at once, every job was checkpointed, and C: stayed at ≥ 50 GB.
- D3 ran on the laptop: 300 sets per variant at B = 20,000, about 1 h wall over 3 processes. **No RunPod pod was used**; spend was $0.
- 2 of D3's 24 chunks were computed twice, by two of my processes, with identical seeds and identical results.

## C3. Development verdict under R*2

`C3_verdict_rstar2_v03.json`; weights [20261401, i, 0], B = 20,000.

**M\*'s families on the v03 weights' first 500**, size (share of records):

| | PD7 | SD1_7 | PD |
|---|---|---|---|
| T1 | 27 (0.997) | 18 (0.983) | 5 (0.655) |
| T3 | 26 (0.994) | 18 (0.984) | 5 (0.671) |

These are the same as v02's.

**M\* checks:**
- No flag of any kind. The largest t − q is −1.3 to −2.8.
- Pooled UBs at L, PD7 / SD1_7 / PD: **0.046 / 0.039 / 0.063 (T1)** and **0.044 / 0.037 / 0.052 (T3)**, all ≤ 0.08.
- The floors are met.

**V_t and removal reasons** (at 1 − 0.0125/9):

| Comparator | T1 | T3 |
|---|---|---|
| B0 | removed: PD7 cell and family, SD1_7 cell and family, PD cell | **kept** (no condition) |
| B1 | removed: PD7 cell, PD cell | removed: PD7 cell |
| B3 | **kept** (no condition) | **kept** (no condition) |
| B4 | removed: cells in all 3 populations, PD pooled LB | removed: cells in all 3 populations, PD pooled LB |
| B6 | removed: PD7 cell, SD1_7 cell | removed: PD7 cell |
| B9 | removed: one PD7 cell | removed: one PD7 cell |
| RETUNED | removed: PD7, SD1_7, PD cells | removed: PD7 cell |

- **The weakest removal** is B9's single PD7 cell, `car|long|new`, at t − q = 3.3 (T1) and 3.8 (T3). Every other removed comparator clears its threshold by at least 3.2 (B1 T1) in some population.
- **The kept comparators** are far from removal: t − q from −6 to −16.

**Bounds:**
- **Form B**, T1 at 0.9875: −0.722 (B3). T3 at 0.99375: −0.566 (B0) and −0.677 (B3). In v02 they were −0.725, and −0.571 / −0.680.
- **Form A** (descriptive, 1 − 0.05/4): T1 −0.197 / −0.244 / −0.064 / −0.295; T3 −0.570 / −0.184 / −0.032 / −0.234 (B0 / B1 / B4 / B9).
- **Form C** UB^{0.975}: −0.066 (T1) and −0.034 (T3).
- **H10**: the ablation part holds on both trackers. The NI bound is −0.043 (T1) and **+0.005 (T3)**, against 0.03.

**H3:**
- ValidJ(M\*Jx) holds. Its UB at 0.995 is PD7 0.056 / 0.060, SD1_7 0.011 / 0.013, PD 0.005 / 0.008 (T1 / T3).
- V^J at 1 − 0.0025/3 is {B3} on T1 and {B0, B3} on T3. RETUNED is absent from the joint run.
- p_c = 0 for every kept comparator, so p_H3 = 0 and H3 **passes at 0.005, 0.00625, 0.00833, 0.0125 and 0.025**.
- The bounds at the Holm-assigned levels, UB^{1 − α/(2|V^J|)}:
  - T1 B3: −0.367 to −0.377;
  - T3 B0: −0.151 to −0.158;
  - T3 B3: −0.254 to −0.260.

  The bound reading and the p reading agree at every level.

**Differences from v02:** none in any verdict. The bounds move by ≤ 0.005.

## E3. Monte Carlo stability at B = 20,000

100 independent seed sets per tracker, [20261402, i, s], s = 1 to 100.

**Membership:**
- **V_t membership differs from the primary in 0 of 100 sets on both trackers.** B3 (T1), and B0 and B3 (T3), are kept every time; every other comparator is removed every time.
- **V^J membership differs in 0 of 100.**
- Valid(M\*), Form B and H10 hold in 100 of 100; p_H3 = 0 in 100 of 100.

**MC SE (SD over the 100 sets) of each decisive bound:**

| Bound | MC SE | Notes |
|---|---|---|
| Form B | 0.0003–0.0005 | |
| HK1c UBs | 0.00005–0.00017 | the largest over all sets is 0.0632 (T1 PD), against 0.08 |
| Form C | 0.0001–0.0002 | |
| H10 NI | 0.0001–0.0002 | T3 maximum +0.0053, against 0.03 |
| H3's bounds at 0.0125 | 0.0004–0.0006 | |

**Removal margins.** The closest removal conditions to their thresholds hold in every set:

| Comparator, condition | Primary t − q | Minimum over sets |
|---|---|---|
| B0 T1, SD1_7 | 0.51 | 0.27 |
| B1 T1, PD | 0.95 | 0.59 |
| B6 T1, SD1_7 | 1.33 | 1.11 |

Each of these comparators is also removed with a margin above 3 elsewhere. B1's SD1_7 condition on T3 (t − q −0.10) fires in 4 % of sets, but B1 T3 is removed by PD7 at 7.0 anyway.

## D3. Operating characteristics at 375 units under R*2

`c1_power_counts_v02.run_oc` with the R\* validity and forms set to R\*2's levels. B = 20,000 bootstrap weights per set, 300 sets per variant, in 12 chunks of 25 (seeds [20261403, variant, chunk]). The power family is the analytic one, which equals the simulated R\* family for M\* on development (check v02, D).

| | Plug-in | Capped (M\* valid at cell level) |
|---|---|---|
| **P(H1)** | **0.870** | **0.933** |
| P(H1 fails) | 0.130 | 0.067 |
| T1 failure reasons | **HK1c 0.103**, pooled 0.010, family flag 0.010 | **HK1c 0.060**, pooled 0.013 |
| T3 failure reasons | family flag 0.023, cell flag 0.017, HK1c 0.003 | family flag 0.003, HK1c 0.003 |
| In V_t, T1 | **B1 0.160, B9 0.157**, B0 / RETUNED 0.010 | **B1 0.143, B9 0.147**, B0 / RETUNED 0.027 |
| In V_t, T3 | **B9 0.120** (B0, B3 always) | **B9 0.093** |
| Superiority over a kept comparator | holds in every set (1.000 for B1, B9, B0, RETUNED) | the same |
| P(H2), P(H10) | 1.00, 1.00 | 1.00, 1.00 |

**M\*'s families, median (p10):**
- PD7: 23 (22–23); record share 0.987–0.988.
- SD1_7: 11 (9–10); record share 0.90–0.91 (p10 0.87–0.88); P(≥ 6) = 1.00.
- PD: 2–4.

Every failure of Form B comes from M\*'s validity, never from superiority.

## A3. M*'s pooled-UB coverage at L = 0.995 with B = 20,000

375 units, 500 sets, seeds [20261404, i].

| | PD7 | SD1_7 | PD |
|---|---|---|---|
| T1, B = 20,000 | 0.992 | 0.978 | 0.966 |
| T3, B = 20,000 | 0.982 | 0.968 | 0.976 |
| v02 (B = 2000, 2000 sets), T1 | 0.988 | 0.983 | 0.974 |
| v02 (B = 2000, 2000 sets), T3 | 0.988 | 0.970 | 0.966 |

- Every difference is within the MC SE of about 0.007 at 500 sets.
- Every value is ≥ 0.9625.
- The larger B does not move L's calibration.

## Surprises, plainly

1. **B1 and B9 stay in V_t much more often at 375 units than in v02.**
   - On T1, B1 stays in 14–16 % of sets and B9 in 15–16 %; on T3, B9 in 9–12 %. In v02 it was 2–5 %.
   - Two things cause it: the stricter removal level (0.0125/9), and B = 20,000 against v02's 200-weight OC.
   - B9's development removal rests on one PD7 cell (t − q 3.3–3.8).
   - It costs nothing on development data: on development M\* is 0.22 to 0.33 less infeasible than B1 and B9 (scene-mean infeasible rate), so superiority held in every set where either was kept.
2. **HK1c on T1 remains the main route to failure at 375 units:** 0.103 plug-in and 0.060 capped. It comes from M\*'s pooled PD exceedance of 0.049, close to δ. Nothing in R\*2 changes this relative to v02.
3. **H10's NI bound on T3 is +0.005,** the closest bound of all to a sign change, but it is 0.025 from its 0.03 threshold, with MC SE 0.0001.

## Files and hashes (SHA-256)

**Code** (`50_CODE/c1_criteria/`):

| File | SHA-256 |
|---|---|
| `c1crit_rstar2_v03.py` | 589cef292400692ca19987c312ba9a59db7e4ab61d1ef82aa93d8d9d287072c4 |
| `c1crit_rstar2_summary_v03.py` | b026b989b33a7bc781f55aaf233b928e37275cc9efbf56bb91d377980e20b7b3 |
| `c1crit_rstar_v02.py` (imported, unchanged) | 687870d60bcc6d48b7905f2fc06caf3253063427c511d43216f96791ecdc4886 |

**Outputs** (`60_RESULTS/c1_criteria_sensitivity_v03/`):

| File | SHA-256 |
|---|---|
| `C3_verdict_rstar2_v03.json` | 3ac588109aa7b5cc2c5c062a3dac846fe095d7de0ac742274a9daa1abd6e8b5d |
| `rstar2_summary_v03.json` | 5806b8601555b23c7463371ed28e85704259a6e498fea1f181177ded1ed6a506 |

**Checkpoints:** `CP3_ckpt/` (6), `E3_ckpt/` (200), `A3_ckpt/` (2), `D3_ckpt/` (24). Logs are in `logs/`. Every file of this folder and the two v03 scripts is hashed in `SHA256SUMS_v03.txt`, this note included.

**Seeds:**

| Use | Seed |
|---|---|
| Primary weights | [20261401, i, 0], B = 20,000 |
| E3 | [20261402, i, s], s = 1 to 100 |
| D3 | [20261403, variant, chunk], chunks 0–11, cap [20261403, variant, 7] |
| A3 | [20261404, i] |
| CP3 (M\*'s families) | [20261405, i, k] |
