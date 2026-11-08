#!/usr/bin/env python3
"""Identity check (Claude line, v01, 31 Oct 2026): the 8-step horizon files must equal the method stage's files on the keys
they share (h1s, h2s, h4s), record for record and bit for bit, and must hold all 8 keys with finite, symmetric PSD xy
covariances. Usage: check_horizon8_v01.py new1 old1 [new2 old2 ...] --out <json>"""
import gzip
import json
import math
import sys

KEYS8 = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]


def main():
    args = sys.argv[1:]
    out = args[args.index("--out") + 1]
    files = args[:args.index("--out")]
    res = {"pairs": [], "all_ok": True}
    for new, old in zip(files[0::2], files[1::2]):
        n = mism = bad = 0
        with gzip.open(new, "rt") as fn, gzip.open(old, "rt") as fo:
            for ln, lo in zip(fn, fo):
                a, b = json.loads(ln), json.loads(lo)
                n += 1
                if (a["scene"], a["k"], a["tid"]) != (b["scene"], b["k"], b["tid"]) or any(a[k] != b[k] for k in ("h1s", "h2s", "h4s")):
                    mism += 1
                for k in KEYS8:
                    x, y, sxx, sxy, syy = a[k]
                    if not all(math.isfinite(v) for v in a[k]) or sxx < 0 or syy < 0 or sxx * syy - sxy * sxy < -1e-9 * max(1.0, sxx * syy):
                        bad += 1
            extra_new, extra_old = sum(1 for _ in fn), sum(1 for _ in fo)
        ok = mism == 0 and bad == 0 and extra_new == 0 and extra_old == 0 and n > 0
        res["pairs"].append({"new": new, "old": old, "records": n, "mismatch": mism, "bad_cov": bad, "extra_new": extra_new,
                             "extra_old": extra_old, "ok": ok})
        res["all_ok"] &= ok
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    print("IDENTITY", "PASS" if res["all_ok"] else "FAIL")


if __name__ == "__main__":
    main()
