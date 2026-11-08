#!/usr/bin/env python3
"""A probe suite for test_c1_v10's amendment test (Choice 42c): it asserts that the C1 hash log of its own tree is absent, UNLESS the
freeze runs it and passes that log's SHA-256 in C1_FREEZE_LOG_SHA256, which is how the bound suite v10 decides whether to skip its
"real log absent" assertions. Writes its out JSON and prints ALL_PASS or FAIL."""
import hashlib
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG = os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt")
ok = (not os.path.exists(LOG)) or os.environ.get("C1_FREEZE_LOG_SHA256") == hashlib.sha256(open(LOG, "rb").read()).hexdigest()
json.dump({"verdict": "ALL_PASS" if ok else "FAIL", "log_exists": os.path.exists(LOG)}, open(sys.argv[1], "w"))
print("ALL_PASS" if ok else "FAIL")
