# C1 deviation log (v01; opened 6 Nov 2026 by the lead)

Plan: `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md` (SHA-256 0817e600…, frozen 2026-11-06 20:08:13 UTC). Registration: https://osf.io/v8qfk/ (Date Registered Nov 6, 2026, 3:31 PM EST; approved by the researcher as administrator). Deposit record: `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt` (1911afcf…). Plan section 9: after the deposit record, deviations are recorded here with their reason, and the frozen analysis is reported beside any deviating one. Decisions: `90_DECISIONS/D16_DELEGATED_CHOICES_v48.md`, Choice 67. Times are UTC.

## Entry 1: the first launch of the post-freeze commands failed in the launcher, before any entry point read an input (a record, not an analysis deviation)

**What happened.**
- From 20:42 to 20:45, the lead's orchestrator v01 (`80_LOGS/c1_postfreeze_v01/run_c1_postfreeze_v01.py`, 5b7c2b02…) started 14 lines of `40_PROTOCOL/C1_RUN_COMMANDS_v01.txt` by passing each line's text to `bash -c`. Bash treats an unquoted backslash as an escape character, so every absolute Windows path in the arguments reached the entry point with its backslashes removed (for example `C:UsersanandDownloads…`).
- Each process ended within 20 s, with `FileNotFoundError` on the first path it opened. Lines 46 and 47 failed for the cause of entry 2. The lines were:
  - 2 to 8: stage B, at the stage-A manifest, before its guard;
  - 24 and 25: the transfer fit, read by the unguarded `c1_transfer_apply_v01`;
  - 41 and 42: the method stage, at its export dataset check, before its guard;
  - 44: H8, at the same check, before its guard;
  - 46 and 47: the environment check.
- Line logs: `80_LOGS/c1_postfreeze_v01/logs/line02.log` to `line47.log`. Run notes: `80_LOGS/c1_postfreeze_v01/C1_RUN_NOTES_v01.jsonl`.
- The orchestrator was stopped on purpose at 20:45:40 (STOP file).

**What was written:**
- no output of any line;
- no run-log line (`40_PROTOCOL/C1_RUN_LOG.txt` did not exist afterwards);
- no stage-B log or folder;
- no ground-truth temporary file;
- no results folder.

Two empty `c1_tppenv_*` temporary folders, left by lines 46 and 47 outside the workspace, were removed. No ground truth was read, and no AV2 outcome was computed.

**Classification.** These were not runs of the frozen commands. The shell changed their arguments before the entry point started, and no guard was reached, so no run of a guarded entry point is on record (plan section 8.6). They are therefore neither environment stops nor exceptions of section 9, which concern the frozen command's own run. The same frozen lines run again, unchanged, as the first runs of record. The independent results review (R21) can check this against the line logs, which show the altered paths, and against the run log, which begins only with the reruns.

**The fix.** Orchestrator v02 (`80_LOGS/c1_postfreeze_v01/run_c1_postfreeze_v02.py`) starts each line without a shell: the line's exact whitespace-separated words are the argument vector. Only the interpreter's path is given in absolute form, because Windows cannot start a program from a relative path written with forward slashes (the cause of entry 2). The interpreter file is the same.

## Entry 2 (deviation D-1): lines 46 and 47, the Trajectron++ environment checks, run with the `--python` path in backslash form

**The frozen lines:**
- `… c1_tpp_envcheck_v01.py --python 50_CODE/env/canmot310/Scripts/python.exe --kind tpp_keys --plan …` (line 46);
- the same with `50_CODE/env/tpp38/Scripts/python.exe --kind tpp_run` (line 47).

**Why they cannot run as printed.** `c1_tpp_envcheck_v01` passes `--python` to Windows' process start (`subprocess.run([a.python, …])`, l. 70). Windows cannot resolve a relative path written with forward slashes. The lead tested this from the workspace root: `50_CODE/env/canmot310/Scripts/python.exe` fails with `[WinError 2]`, while `50_CODE\env\canmot310\Scripts\python.exe` and the absolute path both start Python 3.10.22.

**The deviation.** Lines 46 and 47 run with exactly one token changed, the `--python` value, written with backslashes:
- `50_CODE\env\canmot310\Scripts\python.exe`;
- `50_CODE\env\tpp38\Scripts\python.exe`.

They name the same files; nothing else changes.

**Effect.** None on any outcome. The check is outcome-free: it compares the interpreters' versions with FROZEN_ENV and FROZEN_ENV_TPP, and its result only gates the Trajectron++ runs of H9, which are descriptive. The frozen analysis is unaffected; there is no deviating analysis to report beside it. Run notes: `80_LOGS/c1_postfreeze_v01/C1_RUN_NOTES_v02.jsonl`.

## Entry 3: lines 24 and 25 (the transfer fits applied) failed because their output folder did not exist (a record, not an analysis deviation)

**What happened.**
- At 20:48 to 20:49, under orchestrator v02, `c1_transfer_apply_v01` (lines 24 and 25) ended with `FileNotFoundError` when it opened its output for writing: `60_RESULTS/c1_av2_v01/fits/transfer_applied_t1.json` and `…_t3.json` (logs `80_LOGS/c1_postfreeze_v01/logs/line24_v02.log` and `line25_v02.log`).
- The plan requires `<R>` = `60_RESULTS/c1_av2_v01` to be absent at the freeze, so `<R>/fits/` did not exist.
- This tool, unlike every other post-freeze tool, does not create its output folder. The lead checked each tool's source for `os.makedirs`: `c1_fit_v06` creates it through `c1_fit_v02`, and `k8_items_v08`, `c1_run_v02`, `c1_mstage_v06`, `c1_h8_v06`, `tpp_keys_v01`, `tpp_run_v01`, `c1_predarm_v07` and `c1_analyse_v10` create theirs.

**What was written or read.** Nothing was written. The tool is unguarded and outcome-free (plan section 3.2): it reads only the bound nuScenes transfer fit and the folds file, copies the fit unchanged, and computes no statistic. It writes no run-log line, and no AV2 data were involved.

**Classification.** The exception came from a missing output folder, a condition of the workspace, not from any input of a claim. No output exists, so the same frozen command is not blocked (plan section 8.6). Its output is a copy that the analysis checks against the bound source, so a rerun cannot differ.

**The fix.** The lead created the empty folder `60_RESULTS/c1_av2_v01/fits/`, and lines 24 and 25 run again unchanged (exact words, interpreter path absolute), recorded in `C1_RUN_NOTES_v02.jsonl`. The independent results review can check this.
