# X3 reference and Q-refit inputs: report of the x3-ref agent (v01, 7 Nov 2026)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

This report covers the inputs for analyses (d) and (e2) of the locked plan `20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md` (sha256 `38e2526d…`, checked at the start). x3-ref built inputs only. It ran no decision-mode planner run and no screen. Those are x3-core's.

## 1. Outcome in brief

| Part | Validation | Outcome |
|---|---|---|
| (d) items, d0 | Every item, record and scene array is bitwise equal to the items of record, for T1 and T3. The decision and pair totals are equal too. | **Pass.** d1 and d2 were built. |
| (d) d1's Z0 plan | Arm Z0's decisions from `k8_sim_v04.plan_step` equal the Z0 decisions of the run of record on all 11 288 decisions per tracker: infeasible, lam, v_now, v_chosen, v_log and ds_plan. | **Pass** (T1, T3) |
| (d) fit rule | On the items of record, the refit gives the same `Mstar_ip`, `Mstar_ip_src`, `Mstar` and `_copied_from` as `fits_within` of record, for every fold and all 8 steps. `fold_of_scene` is equal too. | **Pass** (T1, T3) |
| (e2) Q = 1 propagation | The imported frozen `propagate` matches the horizon of record with max abs difference **0**. This holds on every deployed line of all 375 logs (329 789 rows per tracker) and on every line of the 3 check logs. | **Pass** (T1, T3) |
| (e2) cache alignment | For all 375 logs, the cache's `tr_pred` is bitwise equal to the horizon of record and to the Q = 1 re-propagation. `tr_k`, `tr_tid` and `tr_score` also match. | **Pass** (T1, T3) |
| (e2) linearity in Q | S(q) − [A + q(S − A)] at q = 0.5 and q = 2 on the check logs: max abs 1.7e-13 (T1) and 1.2e-10 (T3). The tolerance is 1e-9. | **Pass** |
| (e2) q-fit and substitution | Projection check: sd(1) = item sd of record exactly (max abs 0) on 537 924 (T1) and 537 754 (T3) relied items. The record's S equals the cache's `tr_pred` (max abs 0). | **Done.** The grid's lower end binds (section 4). |
| Runner interface | One-log smoke test, T1 and T3, log `02a00399…` (fold 2): (i) the d0 fits file drives arm Mstar to the decisions of record; (ii) replacing `tr_pred[:, :, 2:5]` by the cache's own covariance leaves arm B0's decisions of record unchanged; (iii) the substitution file loads, aligns and runs B0. Fields checked in (i) and (ii): infeasible, lam, ds_plan, v_chosen, k, stats. | **Pass** |
| Integrity | `C1_RUN_LOG.txt` keeps sha `8bc6235d…`, checked before and after every step. The `60_RESULTS/c1_av2_v01/` re-hash against `BASELINE_MANIFEST_v01.txt` gives 3 091 of 3 091 equal, nothing missing, nothing extra. | **Pass** |

## 2. (d) The items at three references

### 2.1 What changes

`x3_ref_items_v01.scene_items_x3` is a textual copy of `k8_items_v08.scene_items`. Its unified diff against the file of record is stored in every summary and has exactly three changed lines:

- the function name;
- the job tuple, which also carries `ref` and `aux`;
- the line `lead = sc.s_log(tk + S.EVAL_T)`, which becomes `lead = REF_FN[ref](sc, k, tk, s, v, vmax, aux)`.

`lead` is the 16-vector of reference arc lengths at t_k + 0.25 … 4 s. In the code of record this one variable has two roles, and both change together:

1. **The leash of the candidate plans** in the enforced-pair rule at margin 0. Here `splan = min(plan_positions, lead)`, which sets `ctrl` and hence the enforced set.
2. **The reference ego pose.** At this pose the code takes the gap G, the signed separation (side of separation, the sign of D) and the relied-on axis (argmax G).

Unchanged: the strata, sd = √(a′S_h a + 0.10²), the hold-at-current-position test, the ground-truth censoring, D = sign(sep)·a·(g − m) and the output layout.

The three references:

- **d0, the logged arc length** (as of record): `s_log(t_k + t)`.
- **d1, the planner's own reference plan.** It is arm Z0's chosen candidate from `k8_sim_v04.plan_step`, called exactly as `run_decisions` calls it: s = s_log(t_k), v = max(v_log(t_k), 0), vmax = v_log_max + 2, leash = s_log, sensor offset 0. The positions are `min(plan_positions(s, v, vmax)[choice], s_log(t_k + t))`. These are exactly the plan's leashed positions; the code asserts that position − s at 0.5 s equals plan_step's `ds_plan`.
- **d2, constant current speed:** `min(s_k + v_k t, s_end)`, where s_k and v_k are the decision state's values in the items code.

### 2.2 Caveats on I_k-measurability

- **d1 inherits the decision mode's leash.** The Z0 plan is capped by the logged progression, so d1 equals d0 wherever Z0 would drive at or beyond the log. At 2 s that is 95.7 % of decisions on T1 and 96.4 % on T3 (section 2.3).
- **d2 has no hindsight except two small items:**
  - v_k is `v_log(t_k)`, the logged speed over a centred 0.5 s window (t_k ± 0.25 s), as in the items code and the planner's decision state;
  - the route.

Z0 is infeasible, and takes the emergency stop, in 0.43 % (T1) and 0.24 % (T3) of decisions. There d1 is the emergency-stop profile.

### 2.3 Item counts and how much the population moves

| Reference | Tracker | Items | Records | Relied items | Relied share | In-path share (all / relied) | Enforced pairs | P_near / P_ip relied |
|---|---|---|---|---|---|---|---|---|
| d0 = record | T1 | 947 306 | 538 417 | 537 924 | 0.5678 | 0.0315 / 0.0399 | 560 406 | 62 148 / 21 442 |
| d1 | T1 | 947 842 | 538 329 | 538 329 | 0.5680 | 0.0317 / 0.0402 | 560 318 | 62 176 / 21 652 |
| d2 | T1 | 947 169 | 538 416 | 537 791 | 0.5678 | 0.0312 / 0.0396 | 560 405 | 62 266 / 21 297 |
| d0 = record | T3 | 947 746 | 538 152 | 537 754 | 0.5674 | 0.0297 / 0.0384 | 560 197 | 61 890 / 20 645 |
| d1 | T3 | 948 232 | 538 108 | 538 108 | 0.5675 | 0.0299 / 0.0387 | 560 153 | 61 996 / 20 802 |
| d2 | T3 | 947 636 | 538 160 | 537 635 | 0.5673 | 0.0295 / 0.0381 | 560 205 | 62 049 / 20 493 |

**Reading the table.**
- All three references have 11 288 decisions per tracker.
- Under d1 every record has exactly one relied item. At Z0's feasible plan every enforced pair has a positive gap on some axis.

**The reference itself** (`overlap_x3ref_v01.json`, all 11 288 decisions; reference minus logged arc length at 2 s):
- **d1:** equal in 95.7 % (T1) and 96.4 % (T3) of decisions; 1st percentile −7.5 m (T1) and −4.9 m (T3).
- **d2:** equal in 17.8 %; 10th–90th percentiles −1.7 to +1.9 m; 1st–99th percentiles −3.2 to +5.1 m. d2 does not depend on the tracker.

**The record's relied items at each reference.** An item is keyed by log, keyframe, step and track row.

| | Also relied | Same axis | Same axis and side |
|---|---|---|---|
| d1, T1 | 99.98 % | 99.65 % | 99.65 % |
| d1, T3 | 99.99 % | 99.80 % | 99.80 % |
| d2, T1 | 99.95 % | 98.74 % | 98.74 % |
| d2, T3 | 99.96 % | 98.75 % | 98.75 % |

A flipped side of separation on the same axis is at most 4e-6.

### 2.4 M\* refitted on each reference's items

`x3_ref_fit_v01` applies the M\* part of `c1_fit_v02.fit_arms`:
- `split_fit_exact` and `fit_hier_exact` from `c1_crc_exact_v01`, on U = D/sd of the other folds' items, per calibrated step;
- the frozen folds (`C1_FOLDS_375_v01.json`, sha `148458b0…`);
- the 2.5–4 s step dicts copied from 2 s, with `_copied_from`.

**One deviation from `fit_arms`.** Its assert that every M\* threshold is > 0 is required only by the joint arms. Here it is a recorded flag instead of a stop. No threshold ≤ 0 occurred.

**Validation.** On the items of record (and on d0) the refit reproduces `fits_within` of record exactly.

**Threshold change against the record** (`fit_report_x3ref_<ref>_<t>.json`):
- **Median ratio** (reference / record): 1.000 at every step (0.5, 1, 1.5, 2 s), in both in-path parts, under both d1 and d2, for both trackers.
- **Weighted by the record's relied items**, for P_rel, P_near and P_ip, the median ratio is also 1.000 everywhere, except 0.999 for T1, d1, 2 s, P_near.
- **Spread** (10th–90th percentile of the ratio):
  - within 0.93–1.07 over the 96-threshold parts;
  - within 0.96–1.09 item-weighted (the largest: T3, d2, 2 s, P_ip, 90th percentile 1.094).
- **Share of thresholds that changed at all:** 1–45 % (d1) and 8–44 % (d2), increasing with the step and largest in the in-path part.
- **Fallback-level shares** (L0, L1, L2, L3) move by at most 0.1 percentage point.

### 2.5 Files (d) (`60_RESULTS/x3_explore_v01/d_ref/`, sha256 prefix)

| File | T1 | T3 |
|---|---|---|
| `items_x3ref_d0_<t>.npz` | `d50fd8a80cd4` | `57dd08c3c737` |
| `items_x3ref_d1_<t>.npz` | `acbd5f5444bb` | `afb6879e9065` |
| `items_x3ref_d2_<t>.npz` | `397378a94c15` | `abed145e2722` |
| `fits_x3ref_d0_<t>.json` (equal to the record's M\* keys) | `393ca804e739` | `7ef95919f8e4` |
| **`fits_x3ref_d1_<t>.json`** | `8e89c47e26d5` | `ba178f0bf831` |
| **`fits_x3ref_d2_<t>.json`** | `dbfbdc9493e5` | `a6f050cae5bd` |

**Other files:**
- `VALIDATION_d0_items_<t>.json`
- `VALIDATION_d1_z0_<t>.json`
- `VALIDATION_fit_record_<t>.json`
- `fit_report_x3ref_<ref>_<t>.json`
- `overlap_x3ref_v01.json`
- the `*_summary.json` files
- `logs/`

**What the items files hold.**
- The same `item_*`, `rec_*` and `scene_*` arrays as the record.
- `x3_ref_scene`, `x3_ref_k` and `x3_ref_lead` (n_dec, 16): the reference of every decision.
- For d1 also `x3_z0_*`: Z0's choice, infeasible, lam, ds_plan, v_chosen, v_now and v_log.

### 2.6 Interface for the runner (d)

**The fits JSON** has the layout of `fits_within`, with only the M\* keys:
- `fits[str(fold)][step]` for the 8 steps `h0p5s` … `h4s`; each holds `Mstar_ip` (192 = L0 + 96 × in-path), `Mstar_ip_src` and `Mstar` (96);
- the steps after 2 s are copies with `_copied_from`;
- top level: `fold_of_scene`, `folds_sha256` (= `148458b0…`, the folds of record), `route` "within", `c1` false and the stamp.

**Use.** `c1_run_v02._scene_job`'s reading (`fits_all["fold_of_scene"][scene]`, then `fits_all["fits"][str(fold)][h]`) feeds `k8_sim_v04.run_decisions(sc, "Mstar", fits)`. `margins` then takes `Mstar_ip`, indexed by L0 + 96 × in-path.

**Run settings.** The decision mode is unchanged: leash = the log, the arm's own chosen plan. A comparator arm run with these files fails with a KeyError, which is intended.

**Smoke test** (`e2_qrefit/SMOKE_runner_interface_t1_t3.json`, sha `4ee8135b4c43`): on log `02a00399…`, the d0 file drives arm Mstar to the decisions of record, for T1 and T3. The d1 and d2 files have the same layout.

## 3. (e2) The Q = 0 re-propagation

### 3.1 Code and environment

`x3_ref_qzero_v01` imports `av2_horizon_prep_v02` (sha `76cc6a9a…`, bound) and calls its `build_models` and `propagate`; the tool's `main()` is never run.
- **Environment:** canmot310, `environment="my_machine"` (the tool's default).
- **`has_velo`:** from the exports' records (True for both trackers).

| Tracker | Experiment | Filters | Q_sha |
|---|---|---|---|
| T1 | `paper/local/canmot/sc` | ExtendedKalmanFilterRotate for every class | `59c0aea8…` |
| T3 | `paper/baseline/poly_mot` | LinearKalmanFilter for classes 0, 3, 5; ExtendKalmanFilter for 1, 2, 4, 6 | `0a3a48d5…` |

### 3.2 How Q = 0 is set

Q = 0 replaces each class's Q by a zero matrix of the same shape. F, the rotation and the state propagation are untouched.

P_{h+1} = F P_h F′ + R Q R′, with F and R functions of the state only. So S_h(q) = A_h + q(S_h − A_h) exactly; this was checked numerically (table in section 1).

### 3.3 Validation

The full list is in `qzero_<t>/MANIFEST.json` and `_worker<i>_done.json`.
- **Lockstep:** every export line (858 248 for T1, 858 204 for T3) matches its horizon line in (scene, frame, track).
- **Q = 1:** every deployed line (score ≥ 0.4; 329 789 per tracker) has max |Q = 1 − horizon| = 0. On the 3 check logs (`02a00399…`, `067b1c50…`, `0aa4e8f5…`) this also holds for every line, 5 748 and 5 751 lines.
- **Cache:** for all 375 logs, `tr_pred` is bitwise equal to the horizon of record and to the Q = 1 re-propagation. So the cache's covariance equals the Q = 1 projection on every log, not only on the check logs.
- **Means:** Q = 0 leaves the means bitwise unchanged.
- **Elapsed time:** 536 s (T1) and 502 s (T3), run in parallel.

### 3.4 Files

`e2_qrefit/qzero_<t>/<log>.npz` (375 per tracker, 61 MB each tracker):
- `pred_cov` (n, 8, 3) float64 = A_h's (Pxx, Pxy, Pyy), rows = the cache's tr rows;
- `tr_k`.

MANIFEST sha: T1 `a23aece6d11e`, T3 `4bcde3384959`.

## 4. (e2) The q-fit and the substitution files

### 4.1 The rule (`x3_ref_qfit_v01`)

The fit runs per tracker, held-out fold f and class group g. The groups follow `GROUP_OF_CLS`: 0 car, 1 pedestrian, 2 motorcycle/bicycle, 3 truck/bus/trailer.

- **Training items:** the relied items (`item_ref_relied`) of the items of record whose log lies in another fold and whose track is in group g. The steps 0.5–2 s are pooled.
- **Choice:** the smallest q in {0.25, 0.5, 1, 2, 4, 8, 16, 32} with share(D/sd(q) > 1.6448536269514722) ≤ 0.05.
- **sd(q):** `k6_sim_v02.strata`'s own projection and floor applied to A + q(S − A), so sd(1) is the item's sd of record.
- **No cell qualified:** q = 32, flagged. This did not occur.
- **Linking:** each item is linked to its record by (log, pair id). The record supplies the track row, yaw and S. A comes from `qzero_<t>`.

### 4.2 Result: the q table

| Tracker | Car | Pedestrian (folds 0–4) | Motorcycle/bicycle | Truck/bus/trailer |
|---|---|---|---|---|
| T1 | 0.25 | 2, 1, 2, 2, 4 | 0.25 | 0.25 |
| T3 | 0.25 | 0.25 | 0.25 | 0.25 |

### 4.3 Point for the lead: the grid's lower end binds

The lower end of the pre-specified grid binds in 17 of 20 cells on T1 and in 20 of 20 on T3. At q = 0.25 the training exceedance share is already below 0.05:

| Tracker | Car | Motorcycle/bicycle | Truck/bus/trailer | Pedestrian |
|---|---|---|---|---|
| T1 | 0.031–0.034 | 0.022–0.028 | 0.038–0.047 | 0.055–0.064 at q = 0.25; 0.049–0.057 at q = 1 |
| T3 | 0.005 | 0.000–0.001 | 0.006–0.0095 | 0.005–0.008 |

**Consequence.** For these cells the Q-refit arm is the grid floor, not a point at which the relied-item exceedance reaches δ. On T3 even q = 0.25 leaves the exceedance 5 to 10 times below δ, and more for motorcycles and bicycles. This suggests, as an inference not tested here, that much of B0's conservatism on T3 lies in the Q-free part A_h (the propagated initial covariance), which the plan's decomposition does not rescale.

**Not done.** A lower or finer grid (or q = 0) is outside the plan and was not computed. The full training curve (share at every grid point, item and log counts) is in `qfit_table_<t>.json`, under `training_curve`.

### 4.4 Substitution files and interface for the runner

**Files:** `e2_qrefit/subst_<t>/<log>.npz`, 375 per tracker, 62 MB (T1) and 61 MB (T3). Each holds:
- `pred_cov` (n, 8, 3), **float64**: A + q_{f(log), g(row)}(S − A) for every tr row and all 8 steps. Rows with q = 1 take S itself, bitwise. Float64 storage means no rounding question arises.
- `tr_k`, `q_row`, `g_row`, `fold` and the stamp.

**Row counts by q:**
- T1: 234 802 rows at q = 0.25, 57 682 at q = 2, 21 576 at q = 1 and 15 729 at q = 4.
- T3: all 329 789 rows at q = 0.25.

**Manifests:** `subst_<t>/MANIFEST.json` (T1 `0e68283afe87`, T3 `3da2be9afcaa`) hold the q table, `fold_of_scene`, `folds_sha256`, the cache manifest hash and a sha256 per file.

**q tables:** `qfit_table_t1.json` `160706ee4898`, `qfit_table_t3.json` `73c82fdff05d`.

**What the runner does:**
1. Load the cache with `k8_sim_v04.Scene(path)`.
2. Assert `np.array_equal(sc.tr["k"], z["tr_k"])`.
3. Set `sc.tr["pred"] = sc.tr["pred"].copy()` and `sc.tr["pred"][:, :, 2:5] = z["pred_cov"]`.
4. Run arm **B0** (`run_decisions(sc, "B0", None)`, margin z_0.95 · sd).

The means (`tr_pred[:, :, :2]`) are not touched. Everything that reads the covariance then sees the substituted one: sd, the margins and the arm's calibration table.

The smoke test shows that the substitution step itself is neutral: with S in place of S, B0 reproduces the decisions of record.

## 5. Process notes

- **No guard was imported or called.**
  - `k8_items_v08`, `c1_fit_v02`, `c1_fit_v06`, the cache builders and `av2_horizon_prep_v02.main` were not run.
  - `k8_items_v08` was not even imported, because it imports `c1_guard_v05`; its function was copied instead, with the diff recorded.
  - Every item summary records `no_guard_ran: true` and loaded no `c1_guard` module.
- **Imported frozen modules match the hashes bound in `README_C1_CODE_v10.md`:** `k6_sim_v02` `257bb10f`, `k8_sim_v04` `03881acd`, `k8_items_v08` (read for the diff) `dfc7b8cf`, `c1_crc_exact_v01` `4919ed20`, `k8_joint_fit_v02` `473e29ba`, `m_lib_v04` `6d191e5c`, `x1_lib_v03` `f78a7844`, `k7_fit_v01` `05b835a0`, `av2_horizon_prep_v02` `76cc6a9a`.
- **Heavy lock.** Every heavy step ran inside `heavy_lock`. The lock was handed between agents about every 5 minutes, and x3-ref's eleven short (d) steps each waited separately. So:
  - I stopped my own lock-waiting chain while it was still waiting. Nothing had been written, and a log `items_d1_t3.log` holds only the waiting line. This was a deliberate stop.
  - The remaining (d) steps then ran under one lock, through `x3_ref_dchain_v01`, which serves the scripts' inner lock requests from its own lock.
- **One helper edit during a run.** `x3_ref_common_v01.live()` was made robust (a per-PID temp name and no exception on a file clash) while d0 T3 was running. d0 T1 records the earlier hash `9dc1cffb…`. d0 T3 records `90c03213…` but ran the earlier version. The edit touches only the progress line; no computation.
- **Code** (`50_CODE/x3/`, sha prefix):

  | File | sha prefix |
  |---|---|
  | `x3_ref_common_v01` | `90c03213` |
  | `x3_ref_items_v01` | `95ae5017` |
  | `x3_ref_fit_v01` | `ea2202d6` |
  | `x3_ref_z0check_v01` | `0f5b282b` |
  | `x3_ref_dchain_v01` | `85020820` |
  | `x3_ref_overlap_v01` | `14b18863` |
  | `x3_ref_qzero_v01` | `1fb90320` |
  | `x3_ref_qfit_v01` | `770dce10` |
  | `x3_ref_smoke_v01` | `37962db0` |

## 6. Integrity

- **Run log and plan.**
  - `40_PROTOCOL/C1_RUN_LOG.txt` is sha `8bc6235d0c582f0b52952dcb86717a6ab42236a1e472582ebf8f4a10f95e2090` at the start and after every script; the scripts assert it.
  - It was checked again at the end, 12:48 EST.
  - The plan file is unchanged (`38e2526d…`).
- **Results of record.** `60_RESULTS/c1_av2_v01/` was re-hashed at the end against `70_TESTS/X3_INTEGRITY_v01/BASELINE_MANIFEST_v01.txt` (sha `9cc24411…`, 3 091 entries including the run log). All match; no file is missing or extra (3 090 files).
- **Where x3-ref wrote.**
  - Only under `60_RESULTS/x3_explore_v01/d_ref/` and `e2_qrefit/` (new files only; every save refuses an existing path).
  - `50_CODE/x3/x3_ref_*`, this report and `00_PROGRESS/live/x3_ref.txt`.
  - The shared lock tool wrote its own `HEAVY_LOCK*` files.
- **No stray files.** No `__pycache__` was written (all runs use `-B`), and nothing was written under CANMOT.
- **What was not touched.**
  - No other agent's folder or process was opened or touched.
  - No guarded entry point was run.
  - No network, pod or download was used.
