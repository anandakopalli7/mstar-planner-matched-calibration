#!/usr/bin/env python3
"""X3 integrity check (x3-core agent, x3_integrity_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of
record; not part of the registered test). Plan section 0: 40_PROTOCOL/C1_RUN_LOG.txt keeps sha256 8bc6235d...; the hash manifest of
60_RESULTS/c1_av2_v01 equals 70_TESTS/X3_INTEGRITY_v01/BASELINE_MANIFEST_v01.txt. Appends one line to
70_TESTS/X3_INTEGRITY_v01/x3_core_integrity_log_v01.jsonl and exits 1 on any difference.
Usage: python -B x3_integrity_v01.py <event label> [--quick]   (--quick: the run log only)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_common_v01 as C  # noqa: E402


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "check"
    quick = "--quick" in sys.argv
    t0 = time.time()
    rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "event": label, "run_log_sha256": C.sha256(C.RUN_LOG)}
    rec["run_log_ok"] = rec["run_log_sha256"] == C.RUN_LOG_SHA
    ok = rec["run_log_ok"]
    if not quick:
        mok, det = C.manifest_check()
        rec["manifest_ok"], rec["manifest"] = mok, det
        ok = ok and mok
    rec["ok"], rec["seconds"] = ok, round(time.time() - t0, 1)
    with open(os.path.join(C.INTEG, "x3_core_integrity_log_v01.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "manifest"}))
    if not ok:
        print("X3 STOP: integrity difference", json.dumps(rec.get("manifest")))
        sys.exit(1)


if __name__ == "__main__":
    main()
