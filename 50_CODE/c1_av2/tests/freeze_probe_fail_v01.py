#!/usr/bin/env python3
"""A trivial failing suite for test_c1_v09's freeze probes: c1_freeze_v04 must refuse a README whose test does not print ALL_PASS."""
import json
import sys

json.dump({"verdict": "FAIL"}, open(sys.argv[1], "w"))
print("FAIL")
