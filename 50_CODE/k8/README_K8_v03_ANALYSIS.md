# K8 analysis v03 (1 Nov 2026): the analysis of record for the v02 exploratory runs

`k8_analyse_v03.py` analyses the 840-scene exploratory runs that `run_k8_expl_v02.sh` produces with the **v02** code. It applies `70_TESTS/R15B_K8V02_CHECK_v01.md` (N1–N3, n2–n8) and `90_DECISIONS/D14_K8_DESIGN_v05.md`. `k8_analyse_v02.py` is **unchanged**: the v02 runner hash-binds it into every run record, so editing it would have failed the running simulation (R15b N2). v03 is a new file whose binding accepts the v02 records and logs its own hash with the relation **"v03 analysis of v02 runs; v02 analysis aborts by R15b N1"**.

Nothing in this folder has read a non-development scene. v03 has been run only on the 10 development scenes and on synthetic records (`70_TESTS/k8_scratch/v03/`).

Python: `50_CODE/env/canmot310/Scripts/python.exe -B`.

## Files

| File | What it is |
|---|---|
| `k8_analyse_v03.py` | The analysis: a copy of `k8_analyse_v02.py` with the R15b fixes (below). It never imports `k8_run_v02` or `k8_items_v02` |
| `tests/test_k8_analyse_v03.py` | Tests (a)–(f) → `70_TESTS/k8_scratch/v03/k8_tests_v03.json` |
| `90_DECISIONS/D14_K8_DESIGN_v05.md` | The design the analysis implements (v04 kept) |

## When and how to run it on the exploratory outputs

Run it **after `run_k8_expl_v02.sh` has exited**, whether or not the script printed `K8_EXPL_DONE`. v03 only reads the run directory `70_TESTS/k8_expl_v02/`. It writes to a new folder, `70_TESTS/k8_expl_v02_analysis_v03/`, and to the record archive `70_TESTS/k8_expl_v02_records_archive/`.

The exact command, from `50_CODE/k8` (Git Bash, like the script):

```bash
cd /c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911/50_CODE/k8
PY=../env/canmot310/Scripts/python.exe
OUT=../../70_TESTS/k8_expl_v02
FIT=../../60_RESULTS/k7_fits_v01
A3=../../70_TESTS/k8_expl_v02_analysis_v03
mkdir -p $A3
$PY -B k8_analyse_v03.py --runs $OUT --tags t1 t3 \
    --manifests ../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json \
    --out $A3/k8_exploratory_analysis_v03.json --csv-dir $A3/csv --exploratory \
    --fits $FIT/k7_fits_t1_v01.json $FIT/k7_fits_t3_v01.json \
    --items $OUT/items_k8_v02_expl_t1.npz $OUT/items_k8_v02_expl_t3.npz 2>&1 | tee $A3/run_v03.log
```

The defaults that matter:
- `--archive-dir` defaults to `70_TESTS/k8_expl_v02_records_archive` because `--runs` is `70_TESTS/k8_expl_v02`. For any other run directory, `--archive-dir` is required.
- `--run-cwd` defaults to `50_CODE/k8`, the directory the script `cd`s to. The run records store the fits path as the script passed it (`../../60_RESULTS/...`), and v03 resolves it against this directory (n6).

If the analysis stops part-way, rerun **the same command with `--resume` added**. Every tracker × mode that finished is then taken from its checkpoint.

**What a successful run prints:**
1. The relation line, e.g. `v03 analysis of v02 runs; v02 analysis aborts by R15b N1: the runs name k8_analyse_v02 333210a28364 (equal to the current file); this analysis is k8_analyse_v03 <hash>; 12 records archived in ...`: 4 run records, 4 launch records, and the 2 items summaries and 2 items launch records. Any `launch_record_*_DRYRUN.json` in the run directory is archived too, which raises the count.
2. `t1_decide: done, checkpoint written`, then the same line for `t1_loop`, `t3_decide` and `t3_loop`.
3. The K7-form line (reported only), the EXPLORATORY stamp, and `K8 ANALYSIS V03 DONE`.

**Outputs** (all in `70_TESTS/k8_expl_v02_analysis_v03/`):
- `k8_exploratory_analysis_v03.json`;
- `k8_exploratory_analysis_v03_checkpoints/<tag>_<mode>.json`;
- `csv/k8_<tag>_<mode>_*.csv`: v02's 17 tables per tracker, plus `*_safety.csv` and `*_paired_safety.csv` for each mode (21 per tracker).

**Expected time and memory.** At full scale this was not measured (R15b: "not measured at scale"). The development analysis takes 5–7 min under the present CPU load. The synthetic 840-scene run of test (b) took 29 min (1,736 s) for both trackers and both modes: about 12 min per tracker in decision mode and 3 min in loop mode. It has the same per-arm and per-key work (power families, 465 arm pairs, bootstrap B = 2000), but only about 1/10 of the records and 1/60 of the items. Plan for **1–3 h** on the real outputs. The v02 README's memory estimate (a loop-mode peak of 5–6 GB, one tracker × mode at a time) still applies; v03 frees each result after its checkpoint. Close other heavy programs first: on 1 Nov the machine had about 1 GB of free RAM while the simulation ran.

## If the script's own final step (the v02 analysis) failed

This is the expected case (R15b N1/N2).

**What you see:**
- The script's log ends with `loop t3 done ...` and then a traceback from `k8_analyse_v02.py` ending in `AssertionError: non-finite sup-t quantile in <set> <population>`. Here `<set>` is empty for the cell family, or `pooled` or `family`. The quantile belongs to a comparator arm with zero exceedances.
- `set -e` then stops the script. **`K8 exploratory run v02 end` and `K8_EXPL_DONE` are not printed.**

**The runs are intact.** Each runner writes its run record last, after re-hashing the code, so the outputs are complete if `70_TESTS/k8_expl_v02/` holds:
- the four run records `run_record_{t1,t3}_{decide,loop}.json`;
- their four `launch_record_*.json`;
- `items_k8_v02_expl_{t1,t3}.npz` with `_summary.json` and `_launch.json`.

v03's binding re-checks every hash of these.

**v02 may have left partial CSVs.** v02 writes its CSVs after each tracker × mode and its JSON only at the end. If it died in T3, `70_TESTS/k8_expl_v02/csv/` may hold v02 CSVs for T1, and there is no v02 JSON. These are not the analysis of record. Leave them; v03 writes elsewhere.

**Then run the command above.** No re-run and no `--resume` of the runner is needed.

**If a run record is missing**, a *run* failed, not the analysis. v03 then refuses with `run record ... missing: run <tag>_<mode> did not finish`.
1. **Archive the records first.** Re-running the runner rewrites that run's launch record (R15b N2). Use the command above with `--archive-only` added: it copies the records that exist, read-only, and checks nothing.
2. Rerun that one line of the script (the runner with `--resume` reuses the finished per-scene shards).
3. Then run the v03 command.

## If v03 itself stops

- **`non-finite sup-t quantile in Mstar ...`** is by design: R15b N1 keeps the finite-quantile rule for M* (K7 m3). Every tracker × mode that finished is in its checkpoint. Bring the case to the researcher; do not relax the rule in place.
  - It happens only if every evaluable cell of a set (or M*'s whole pooled population) has zero bootstrap SE.
  - The risk is real but small. On the development data M*'s in-path (PD) exceedances are few: 2 of 615 records on T1 and 5 of 600 on T3, all in `car|long|straight`.
  - A first, badly thinned build of the synthetic test data reproduced this abort in M*'s PD cells (for v02 and v03 alike).
- **A binding assertion** (a hash, a manifest, the fits, the items, a scene or design count) means the inputs differ from what the runs recorded. Do not analyse until the cause is known.
- **Anything else:** after the fix, rerun with `--resume`.

## What v03 changes (R15b → v03)

| R15b | Change in `k8_analyse_v03.py` |
|---|---|
| **N1** | `hk1_rule(..., arm=)`: the three sup-t quantiles (cell family, pooled cell, power-qualified family) must be finite for M* outside `--allow-dev`. For a comparator, a non-finite quantile is recorded as `q = None` with the note **"no cell can be flagged: zero bootstrap SE"**, and `A.flag`'s est > δ rule decides those cells. The values are `validity_by_arm.<arm>.pops.<pop>.{q, pooled.q, family_q}` with their notes; `zero_se_quantiles` lists every None |
| **n8** (and N1) | Checkpoints. Each tracker × mode is written, as a temporary file then an atomic rename, to `<out stem>_checkpoints/<tag>_<mode>.json`. The checkpoint is keyed by this file's hash, the statistics, the seeds, the input hashes and (for loop mode) RETUNED's selection, and it holds its CSVs' hashes. `--resume` reuses a matching checkpoint. The final JSON is assembled from the checkpoint files read back from disk |
| **N2** | `check_exploratory` verifies the v02 run and launch records exactly as v02 does, against `V02_CODE_FILES` (sim, runner, k6_sim_v02, k8_analyse_v02, k6_analyse_v02, m_lib_v04), the fits, the manifests, the outputs, the design, the 840 scenes and the items. The analysis hash the records name must equal the **current** `k8_analyse_v02.py`. In addition, `V02_CODE_FILES` must equal the `code_files` the runner logged in each launch record. Before any check, every `run_record_*` and `launch_record_*` of the run directory and the items' summary and launch records are **copied, by reading only**, to the archive; a repeat copy is skipped, and changed content is kept beside the earlier copy. Each invocation appends a line to `ARCHIVE_LOG.jsonl` |
| **N3** | `safety_reading`, `k8_<tag>_decide_safety.csv` and `..._paired_safety.csv` lead with **V2_viol** (ground truth, D > G) per population, paired against M*. In loop mode the lead is the **collisions** (at fault, tracked and untracked, all real; LOG artefacts removed; per delay; per-episode rates with intervals; paired against M*) and the **front-buffer intrusions**, with the confound note. TTV < 4 s and `ttv_enf` are **secondary**. `ttv_share_lt_2s` is kept, labelled **"arm-invariant by construction (R15b N3)"** |
| n3 | RETUNED reports `boundary_merged_curve` (v02's flag) and `boundary_alpha_grid` per fold; `boundary_semantics` states both |
| n4 | `selection_curve_note`: the selection runs on the merged 21-point α/δ′ curve, not the δ′ grid; the α-only and δ′-only choices stay reported, not used |
| n5 | `V2_exec_estop` (emergency stops, scored at margin 0) and `V2_exec_non_estop` in every V2 table |
| n6 | The fits path of each run record is resolved against `--run-cwd` and must hash to the recorded `fits_sha256`; the `--fits` given to the analysis must carry the same hash |
| n7 | The items' manifest hashes (summary and its launch record) must equal the runs' and the current manifests' |
| n2 | Tests only: T4 as counts (test (f)) |

Every number v02 computes is unchanged (test (a)). The `--prereg` path is v02's, with the runner's `frozen_hashes` copied in so that the runner is never imported; no K8 plan is frozen, so it is not exercised.

## Tests (`tests/test_k8_analyse_v03.py`)

Command: `python -B tests/test_k8_analyse_v03.py ../../70_TESTS/k8_scratch/v03/k8_tests_v03.json`. Verdict: **ALL_PASS** (`70_TESTS/k8_scratch/v03/k8_tests_v03.json`, `k8_tests_v03.log`; the final run used `--reuse` for the outputs of (a) and (b), which carry the current v03 hash, and recomputed (e)). The protected v02 files, the fits and the manifests have the same hashes before and after, and the real archive folder was not created.

| Test | What it checks |
|---|---|
| (a) | v03 `--allow-dev` on the stored development runs (B = 2000). Against `k8_analyse_v02` rerun on the same runs in the same environment, **every number is equal exactly**: JSON (182,660 numbers) and all 34 CSVs. Against the stored v02 outputs, 27 numbers differ in the last digit (relative ≤ 8e-16), from multi-threaded vs single-threaded BLAS; v02's own rerun shows the same 27. The development check's 718 headline numbers are equal exactly. **By design only two strings change** (`analysis_sha256`, `design`); everything else is an addition |
| (b) | A synthetic exploratory run directory: the development outputs copied onto the 840 non-development scene names and thinned to about 1/10 (M*'s count rows are copied in full), with B1's exceedances set to zero, and records as the v02 runner writes them. `k8_analyse_v02.analyse_decide` with the exploratory statistics raises `non-finite sup-t quantile in PD_inpath` for B0, the third arm tested (after M* and Z0), so v02 writes nothing. v03 `--exploratory` completes in 29 min. It records q = None with the note for B1 in all three populations on both trackers, for B0's PD sets (where v02 died), and on T1 for 13 other arms' PD sets and B9's SD1_7 family. M*'s quantiles are finite. All 12 records were archived and the originals are unchanged |
| (c) | M* with a zero-SE cell family or power-qualified family still raises. A comparator records None. A constant-rate comparator (est 1 > δ, zero SE) is flagged in all 32 cells by est > δ. `--allow-dev` stays relaxed |
| (d) | The binding accepts matching v02 records, including the fits stored as the relative path the script passes, resolved from another process cwd. It refuses a mismatched sim hash, runs naming v03 as their analysis, launch code files other than v02's, items with other manifest hashes, a wrong run cwd, the other tracker's `--fits`, a development scene and a dry run. The records are archived before any check. `--archive-only` archives an incomplete run directory and checks nothing |
| (e) | An abort injected in `t3_loop` leaves `t1_decide`, `t1_loop` and `t3_decide` on disk. `--resume` reuses them (`t3_loop` takes RETUNED from the `t3_decide` checkpoint), and the final JSON and every CSV equal (a)'s. A checkpoint with another key or a changed CSV is not reused |
| (f) | On the development curve the PD7 exceedance count is non-increasing and the infeasible-decision count non-decreasing along the merged α/δ′ curve, with no tolerance, on both trackers. The 1e-6 / 2e-5 upward steps of the rate (R15b §3 (5)) are listed as denominator effects |

## Not done, or read differently

- **A ground-truth TTV** (R15b N3, D14 v05 A5) needs new per-decision fields: a later supplementary decision-mode pass, not part of v03.
- **Collisions are a headline, not a ranking.** They are read descriptively, with the log-replay confound (D10 §2); D14 v05 §4 states this.
- **The `--prereg` path** is not exercised (no K8 plan is frozen).
- **Test (b) is not a nuScenes result.** Its synthetic outputs carry the EXPLORATORY stamp only because the binding requires it; they are marked `synthetic` and documented in `README_SYNTHETIC.txt`.
