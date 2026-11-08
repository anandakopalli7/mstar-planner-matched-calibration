#!/usr/bin/env python3
"""r21_runlog_check_v01 (7 Nov 2026): R21's check of the tables of record against the uploaded run log (plan sections 8.6, 9).

Reads (never writes) the run log, the decision of record (and the analysis JSON), the frozen config, optionally the frozen plan
and the stage-B log, and hashes the files they name. Checks:
  1. the chain: every line one JSON object; prev_sha256 = SHA-256 of the previous line's bytes (no newline); 64 zeros first;
     the file ends with a newline (a cut last line shows);
  2. the decision's binding.run_log_at_start: the first `lines` lines hash to run_log_sha256 (bytes with newlines), line
     `lines` hashes to last_line_sha256; the analysis's own start line (binding.run_id) is in that prefix;
  3. the analysis run: its "done" line lists the decision (and analysis JSON) with the SHA-256 they have now;
  4. every table the decision consumed (binding.tables_in_run_log) and every table the config names (method stage, H8, H9,
     descriptive H9, every route's run record and the run tables it records, every fits file): a "done" line with that output
     and SHA-256, before the analysis's start line, under the decision's deposit record; the file on disk still hashes to it;
     the table of record = the first such done line (plan 8.6); every other done line for the same output role is listed;
  5. stops: start lines without a done line; analysis runs whose decision holds one of section 9's seven strings or that left
     one of their two outputs (environment stops); the analysis table of record = the first analysis run with a done line,
     under the current deposit record, that is not an environment stop; it must be the decision given;
  6. plan and deposit-record hashes on every line (exempt lines listed).
Output: JSON with every check and a markdown summary. Usage:
  python -B r21_runlog_check_v01.py --run-log <C1_RUN_LOG.txt> --decision <c1_decision_rN.json> [--analysis <c1_analysis_rN.json>]
      --config <cfg.json> --root <workspace root> [--plan <frozen plan>] [--stage-b-log <C1_STAGE_B_LOG.txt>] --out <json> --md <md>
"""
import argparse
import hashlib
import json
import os
import sys

SEVEN = ("MemoryError", "[Errno 28]", "[WinError 112]", "[WinError 39]", "[WinError 8]", "[WinError 14]", "[WinError 1455]")
ZERO = "0" * 64


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(root, p):
    """Workspace-relative path with forward slashes (the run log's convention)."""
    try:
        r = os.path.relpath(os.path.abspath(p), os.path.abspath(root))
    except ValueError:
        return p.replace("\\", "/")
    return r.replace("\\", "/")


def absp(root, r):
    return os.path.normpath(os.path.join(root, r))


def read_log(path):
    raw = open(path, "rb").read()
    out = {"path": path, "bytes": len(raw), "sha256": sha_bytes(raw), "ends_with_newline": raw.endswith(b"\n"),
           "crlf": b"\r\n" in raw}
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    recs, errors = [], []
    prev = ZERO
    for i, ln in enumerate(lines):
        b = ln[:-1] if ln.endswith(b"\r") else ln
        try:
            o = json.loads(b)
        except Exception as e:  # noqa: BLE001
            errors.append({"line": i + 1, "error": "not JSON: %s" % e})
            recs.append(None)
            prev = sha_bytes(b)
            continue
        if o.get("prev_sha256") != prev:
            errors.append({"line": i + 1, "error": "chain broken", "expected_prev": prev, "found_prev": o.get("prev_sha256")})
        recs.append(o)
        prev = sha_bytes(b)
    out["n_lines"] = len(lines)
    out["chain_errors"] = errors
    out["chain_ok"] = not errors and out["ends_with_newline"]
    out["line_bytes"] = lines
    out["records"] = recs
    return out


def decision_texts(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-log", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--analysis")
    ap.add_argument("--config", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--stage-b-log")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args(argv)
    for _p in (a.out, a.md):
        os.makedirs(os.path.dirname(os.path.abspath(_p)), exist_ok=True)
    root = a.root
    log = read_log(a.run_log)
    recs = log["records"]
    res = {"label": "R21 run-log check (plan sections 8.6, 9); descriptive review", "inputs": {}, "checks": [], "problems": []}

    def check(name, ok, detail=None):
        res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            res["problems"].append(name)

    for k in ("run_log", "decision", "analysis", "config", "plan", "stage_b_log"):
        p = getattr(a, k.replace("-", "_"), None)
        if p:
            res["inputs"][k] = {"path": p, "sha256": sha_file(p) if os.path.exists(p) else None}
    check("chain intact (prev_sha256 of every line; file ends with a newline)", log["chain_ok"],
          {"errors": log["chain_errors"][:20], "ends_with_newline": log["ends_with_newline"], "lines": log["n_lines"]})
    # ---- runs by run_id
    runs = {}
    for i, o in enumerate(recs):
        if o is None:
            continue
        r = runs.setdefault(o.get("run_id"), {"run_id": o.get("run_id"), "entry": o.get("entry"), "role": o.get("role"), "lines": []})
        r["lines"].append(i + 1)
        if o.get("event") == "start":
            r["start_line"], r["start_utc"] = i + 1, o.get("utc")
            r["deposit_record_sha256"] = o.get("deposit_record_sha256")
            r["plan_sha256"] = o.get("plan_sha256")
        elif o.get("event") == "done":
            r["done_line"], r["done_utc"] = i + 1, o.get("utc")
            r["outputs_sha256"] = o.get("outputs_sha256") or {}
            r["inputs_sha256"] = o.get("inputs_sha256") or {}
            r["done_deposit_record_sha256"] = o.get("deposit_record_sha256")
    res["runs"] = [{k: v for k, v in r.items()} for r in runs.values()]
    res["start_without_done"] = [{"run_id": r["run_id"], "entry": r["entry"], "start_line": r.get("start_line"), "utc": r.get("start_utc")}
                                 for r in runs.values() if "start_line" in r and "done_line" not in r]
    res["done_without_start"] = [r["run_id"] for r in runs.values() if "done_line" in r and "start_line" not in r]
    check("every done line has its start line", not res["done_without_start"], res["done_without_start"])
    # ---- the decision
    with open(a.decision, encoding="utf-8") as f:
        dec = json.load(f)
    b = dec.get("binding") or {}
    rls = b.get("run_log_at_start") or {}
    n = rls.get("lines")
    if isinstance(n, int) and 0 < n <= log["n_lines"]:
        prefix = b"".join(lb + b"\n" for lb in log["line_bytes"][:n])
        check("decision's run_log_sha256 = SHA-256 of the log's first `lines` lines", sha_bytes(prefix) == rls.get("run_log_sha256"),
              {"lines": n, "recorded": rls.get("run_log_sha256"), "recomputed": sha_bytes(prefix)})
        last = log["line_bytes"][n - 1]
        last = last[:-1] if last.endswith(b"\r") else last
        check("decision's last_line_sha256 = SHA-256 of line `lines`", sha_bytes(last) == rls.get("last_line_sha256"),
              {"recorded": rls.get("last_line_sha256"), "recomputed": sha_bytes(last)})
    else:
        check("decision records the run log at start (lines, run_log_sha256, last_line_sha256)", False, rls)
    run_id = b.get("run_id")
    me = runs.get(run_id)
    check("the analysis's run_id has a start and a done line", bool(me and "start_line" in me and "done_line" in me),
          {"run_id": run_id, "run": me and {k: me.get(k) for k in ("start_line", "done_line", "entry")}})
    dep = b.get("deposit_record_sha256")
    if me and isinstance(n, int):
        check("the analysis's start line lies in the recorded prefix (it is line `lines` or earlier)", me.get("start_line", 10 ** 9) <= n,
              {"start_line": me.get("start_line"), "lines": n})
    if me and "done_line" in me:
        outs = me.get("outputs_sha256", {})
        for k, p in (("decision", a.decision), ("analysis", a.analysis)):
            if not p:
                continue
            r_ = rel(root, p)
            rec = outs.get(r_)
            now = sha_file(p)
            check("analysis done line lists the %s with its current SHA-256" % k, rec == now, {"path": r_, "recorded": rec, "now": now})
        check("analysis done line under the decision's deposit record", me.get("done_deposit_record_sha256") == dep,
              {"done": me.get("done_deposit_record_sha256"), "decision": dep})
    # ---- done lines by output path
    by_out = {}
    for r in runs.values():
        for pth, h in (r.get("outputs_sha256") or {}).items():
            by_out.setdefault(pth, []).append({"run_id": r["run_id"], "entry": r["entry"], "done_line": r["done_line"], "sha256": h,
                                               "deposit_record_sha256": r.get("done_deposit_record_sha256")})
    start_limit = me.get("start_line") if me else None

    def table_check(label, path):
        if not path:
            return
        r_ = rel(root, path)
        exists = os.path.exists(path)
        now = sha_file(path) if exists else None
        dl = sorted(by_out.get(r_, []), key=lambda x: x["done_line"])
        valid = [d for d in dl if d["sha256"] == now and d["deposit_record_sha256"] == dep
                 and (start_limit is None or d["done_line"] < start_limit)]
        first_any = dl[0] if dl else None
        ok = bool(exists and valid and first_any is not None and first_any["done_line"] == valid[0]["done_line"])
        note = None
        if not dl and os.path.basename(path).startswith("transfer_applied_"):
            ok = exists
            note = "unguarded producer by design (c1_transfer_apply_v01, plan section 3.2): no run-log line; checked downstream by hash"
        check("table of record: %s" % label, ok, {"path": r_, "exists": exists, "sha256_now": now, "done_lines": dl, "note": note,
                                                   "first_done_is_this_file": bool(valid and first_any and first_any is valid[0])})
        res.setdefault("tables", {})[label] = {"path": r_, "sha256_now": now, "done_lines": dl, "table_of_record_ok": ok}
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    for k in ("method_stage", "h9", "h9_descriptive"):
        for t, p in (cfg.get(k) or {}).items():
            table_check("%s %s" % (k, t), p)
    table_check("h8", cfg.get("h8"))
    for r in cfg.get("routes", []):
        for t, tag in (r.get("tags") or {}).items():
            full = tag if tag.endswith("_decide") else tag + "_decide"
            rr = os.path.join(r["runs"], "run_record_%s.json" % full)
            table_check("%s %s run record" % (r["name"], t), rr)
            table_check("%s %s fits" % (r["name"], t), (r.get("fits") or {}).get(t))
            if os.path.exists(rr):
                with open(rr, encoding="utf-8") as f:
                    rec = json.load(f)
                for kind, ext in (("episodes", ".jsonl"), ("counts", ".npz"), ("decisions", ".npz"), ("cal", ".npz")):
                    p = os.path.join(r["runs"], "%s_%s%s" % (kind, full, ext))
                    if os.path.exists(p):
                        h = sha_file(p)
                        check("%s %s: %s hash = run record" % (r["name"], t, kind), h == rec.get(kind + "_sha256"),
                              {"now": h, "run_record": rec.get(kind + "_sha256")})
    # the decision's own listing
    tir = b.get("tables_in_run_log")
    if isinstance(tir, dict):
        for role, files in tir.items():
            for pth, v in (files or {}).items():
                dl = by_out.get(pth, [])
                ok = any(d["sha256"] == v.get("sha256") for d in dl)
                check("decision's tables_in_run_log %s %s has that done line" % (role, pth), ok,
                      {"recorded": v, "log_done_lines": dl})
                p = absp(root, pth)
                if os.path.exists(p):
                    check("decision's table %s still hashes as recorded" % pth, sha_file(p) == v.get("sha256"),
                          {"now": sha_file(p), "recorded": v.get("sha256")})
    else:
        check("decision lists tables_in_run_log", False, tir)
    # ---- analysis runs: environment stops and the table of record
    an_runs = sorted([r for r in runs.values() if (r.get("entry") or "").endswith("c1_analyse_v10.py")], key=lambda r: r.get("start_line", 0))
    classified = []
    for r in an_runs:
        c = {"run_id": r["run_id"], "start_line": r.get("start_line"), "done_line": r.get("done_line"), "class": None}
        if "done_line" not in r:
            c["class"] = "stop without done line (environment stop or raised exception; never a table of record)"
        else:
            outs = r.get("outputs_sha256") or {}
            present = {p: os.path.exists(absp(root, p)) for p in outs}
            c["outputs_present"] = present
            jsons = [p for p in outs if p.endswith(".json")]
            hits = []
            for p in jsons:
                txt = decision_texts(absp(root, p))
                if txt:
                    hits += [s for s in SEVEN if s in txt]
            c["seven_string_hits"] = sorted(set(hits))
            if len(outs) < 2 or not all(present.values()):
                c["class"] = "environment stop (one of its two outputs missing)"
            elif hits:
                c["class"] = "environment stop (resource error recorded: %s)" % ", ".join(sorted(set(hits)))
            elif r.get("done_deposit_record_sha256") != dep:
                c["class"] = "other deposit record"
            else:
                c["class"] = "completed run"
        classified.append(c)
    res["analysis_runs"] = classified
    first_ok = next((c for c in classified if c["class"] == "completed run"), None)
    check("the decision given is the first completed analysis run (table of record, plan 8.6 and 9)",
          bool(first_ok and first_ok["run_id"] == run_id), {"first_completed": first_ok, "decision_run_id": run_id})
    # ---- plan and deposit hashes on every line
    if a.plan:
        ph = sha_file(a.plan)
        bad = [i + 1 for i, o in enumerate(recs) if o and o.get("plan_sha256") not in (ph, None)]
        check("every line carries the frozen plan's SHA-256", not bad, {"plan_sha256": ph, "other_lines": bad[:50]})
    exempt = [i + 1 for i, o in enumerate(recs) if o and str(o.get("deposit_record_sha256", "")).startswith("exempt")]
    others = sorted({o.get("deposit_record_sha256") for o in recs if o and not str(o.get("deposit_record_sha256", "")).startswith("exempt")})
    res["deposit_record_hashes"] = {"exempt_lines": exempt, "non_exempt_values": others}
    check("one deposit record on every non-exempt line, equal to the decision's", others in ([dep], []), res["deposit_record_hashes"])
    # ---- stage-B log (descriptive)
    if a.stage_b_log and os.path.exists(a.stage_b_log):
        lines = [ln for ln in open(a.stage_b_log, "rb").read().split(b"\n") if ln.strip()]
        parsed = []
        for ln in lines:
            try:
                parsed.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                parsed.append({"raw": ln.decode("utf-8", "replace")[:300]})
        res["stage_b_log"] = {"lines": len(lines), "entries": parsed[:50]}
    res["ok"] = not res["problems"]
    res["n_checks"], res["n_problems"] = len(res["checks"]), len(res["problems"])
    for r in res["runs"]:
        r.pop("lines", None)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)
    os.replace(tmp, a.out)
    md = ["# R21 run-log check", "", "- run log: %s (%d lines, SHA-256 %s); chain ok: %s" % (a.run_log, log["n_lines"], log["sha256"], log["chain_ok"]),
          "- checks: %d, problems: %d" % (res["n_checks"], res["n_problems"]), ""]
    for c in res["checks"]:
        md.append("- [%s] %s" % ("ok" if c["ok"] else "PROBLEM", c["check"]))
    md += ["", "## Analysis runs", ""] + ["- %s: lines %s-%s: %s" % (c["run_id"], c.get("start_line"), c.get("done_line"), c["class"]) for c in classified]
    md += ["", "## Start lines without a done line", ""] + ["- %s %s line %s %s" % (x["entry"], x["run_id"], x["start_line"], x["utc"]) for x in res["start_without_done"]]
    with open(a.md, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("R21 run-log check: %d checks, %d problems -> %s" % (res["n_checks"], res["n_problems"], a.out))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
