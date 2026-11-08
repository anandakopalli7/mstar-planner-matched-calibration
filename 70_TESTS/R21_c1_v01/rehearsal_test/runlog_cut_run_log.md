# R21 run-log check

- run log: rehearsal_test/cut_run_log.txt (13 lines, SHA-256 7f9995510b2f5220b2a40209652148151e38bb5d3ad4266537b13e290e1b363c); chain ok: False
- checks: 14, problems: 4

- [PROBLEM] chain intact (prev_sha256 of every line; file ends with a newline)
- [ok] every done line has its start line
- [ok] decision's run_log_sha256 = SHA-256 of the log's first `lines` lines
- [ok] decision's last_line_sha256 = SHA-256 of line `lines`
- [ok] the analysis's run_id has a start and a done line
- [ok] the analysis's start line lies in the recorded prefix (it is line `lines` or earlier)
- [ok] analysis done line lists the decision with its current SHA-256
- [ok] analysis done line lists the analysis with its current SHA-256
- [ok] analysis done line under the decision's deposit record
- [PROBLEM] table of record: h8
- [ok] decision's tables_in_run_log h8 70_TESTS/h8_post.json has that done line
- [PROBLEM] decision's table 70_TESTS/h8_post.json still hashes as recorded
- [ok] the decision given is the first completed analysis run (table of record, plan 8.6 and 9)
- [PROBLEM] one deposit record on every non-exempt line, equal to the decision's

## Analysis runs

- b55b7397b54d4a5da2fca17e05d8d114: lines 5-6: completed run
- adbf4ffb89a44818b92650e8b458be4d: lines 7-8: completed run

## Start lines without a done line

- 50_CODE/c1_av2/c1_e0_v05.py 5832c751cafc40ad990594072b6288dc line 1 2026-11-06T19:54:17Z
- 50_CODE/c1_av2/c1_h8_v06.py 131048d930d44f1693f004ccda90ea9a line 4 2026-11-06T19:58:06Z
- 50_CODE/av2/av2_cache_stageB_v06.py 60b9efb27bf34b3bad18783cc07f3958 line 11 2026-11-06T19:59:27Z
- 50_CODE/av2/av2_cache_stageB_v06.py e61bd57ced1f4342b43b36fc35a9edae line 12 2026-11-06T19:59:42Z
