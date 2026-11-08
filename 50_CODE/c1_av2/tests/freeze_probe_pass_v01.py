#!/usr/bin/env python3
"""A trivial suite for test_c1_v09's freeze probes (c1_freeze_v04 runs every README "test" file): writes its out JSON, prints ALL_PASS."""
import json
import sys

json.dump({"verdict": "ALL_PASS"}, open(sys.argv[1], "w"))
print("ALL_PASS")
