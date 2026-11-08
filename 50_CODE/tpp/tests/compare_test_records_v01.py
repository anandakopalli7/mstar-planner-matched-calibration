#!/usr/bin/env python3
"""D16 v15 Choice 36 check (4 Nov 2026): the synthetic test outputs of the superseded suites are identical before and after the
main()-only edits. Compares each pair of test JSONs: same test names, same pass flags, identical `info` payloads (every number
and string); only the recorded script hashes and run times may differ. Writes one JSON verdict.
Usage: python -I compare_test_records_v01.py --pair NAME BEFORE AFTER [--pair ...] --out <json>
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=3, action="append", required=True, metavar=("NAME", "BEFORE", "AFTER"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for name, b, c in a.pair:
        x, y = json.load(open(b)), json.load(open(c))
        tx, ty = x["tests"], y["tests"]
        same_names = sorted(tx) == sorted(ty)
        diffs = [k for k in tx if k in ty and (tx[k]["pass"] != ty[k]["pass"] or json.dumps(tx[k]["info"], sort_keys=True) != json.dumps(ty[k]["info"], sort_keys=True))]
        res[name] = {"before": b, "after": c, "tests": len(tx), "same_test_names": same_names, "tests_with_any_difference": diffs,
                     "all_pass_before": x["all_pass"], "all_pass_after": y["all_pass"], "scripts_before": x.get("scripts"), "scripts_after": y.get("scripts"),
                     "identical": bool(same_names and not diffs and x["all_pass"] and y["all_pass"])}
    out = {"pairs": res, "all_identical": all(r["identical"] for r in res.values())}
    json.dump(out, open(a.out, "w"), indent=1)
    for n, r in res.items():
        print(n, "identical" if r["identical"] else "DIFFERENT %s" % r["tests_with_any_difference"])
    print("IDENTICAL_ALL" if out["all_identical"] else "NOT_IDENTICAL")


if __name__ == "__main__":
    main()
