"""av2_fetch_v05 (Claude line, 5 Nov 2026; v01-v04 kept): metadata-only fetch of an explicit list of Argoverse 2 Sensor *train*
logs from the public S3 bucket, for the 375-log C1 confirmation set (AV2_TRACKER_PORT_DESIGN_v04.md section 4).

Per log (prefix datasets/av2/sensor/train/<log>/ of https://argoverse.s3.amazonaws.com):
  downloaded: annotations.feather, city_SE3_egovehicle.feather, calibration/* ;
  listed only (never downloaded): sensors/lidar/ -> <out>/<log>/lidar_keys_v01.csv (key, size, etag; sorted by key).
Cameras, maps and lidar contents are never fetched. Integrity: size equals the listing's; where the ETag is a plain MD5
(32 hex, no '-') the file's MD5 equals it (otherwise the partial file is removed and the key reported FAILED).
Resumable: a present file with the right size (and MD5) is kept. Writes <out>/MANIFEST_av2_train225_meta_v05.csv
(key, size, etag, md5_ok, status) and <out>/FETCH_SUMMARY_av2_train225_meta_v05.json.
Standard library only (urllib, xml, csv, hashlib, concurrent.futures); unsigned ListObjectsV2 calls and plain HTTPS GETs.
The output folder is untrusted data: nothing in it is executed or imported; run with python -I -B from outside it.

Usage: python -I -B av2_fetch_v05.py --out <30_DATA/av2_train225> --logs-file <C1_LOGS_375_v01.json> --logs-key held_out_225
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

BUCKET = "https://argoverse.s3.amazonaws.com"
SPLIT = "train"
PREFIX = "datasets/av2/sensor/%s/" % SPLIT
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
TOP_FILES = ("annotations.feather", "city_SE3_egovehicle.feather")
LISTING = "lidar_keys_v01.csv"
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MD5 = re.compile(r"^[0-9a-f]{32}$")


def get_xml(url, tries=8):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return ET.fromstring(r.read())
        except Exception:  # noqa: BLE001  (transient DNS / connection errors)
            if attempt == tries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def list_keys(prefix, delimiter=None):
    """All (key, size, etag) under prefix (with delimiter '/': only the objects directly under it)."""
    out, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if delimiter:
            q["delimiter"] = delimiter
        if token:
            q["continuation-token"] = token
        root = get_xml(BUCKET + "/?" + urllib.parse.urlencode(q))
        for c in root.findall(NS + "Contents"):
            out.append((c.find(NS + "Key").text, int(c.find(NS + "Size").text), c.find(NS + "ETag").text.strip('"')))
        nt = root.find(NS + "NextContinuationToken")
        if nt is None:
            break
        token = nt.text
    return out


def safe_rel(key, log):
    """Relative path of a key inside the log folder; refuses anything outside the expected prefix."""
    pre = PREFIX + log + "/"
    if not key.startswith(pre):
        raise ValueError("key outside the log prefix: %s" % key)
    rel = key[len(pre):]
    if not rel or ".." in rel or "\\" in rel or rel.startswith("/"):
        raise ValueError("unsafe key: %s" % key)
    return rel


def md5_path(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch(key, size, etag, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    check_md5 = bool(MD5.match(etag))
    if os.path.exists(dest) and os.path.getsize(dest) == size and (not check_md5 or md5_path(dest) == etag):
        return "kept", check_md5
    tmp = dest + ".part"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(BUCKET + "/" + urllib.parse.quote(key), timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            if os.path.getsize(tmp) != size:
                raise IOError("size mismatch %d != %d" % (os.path.getsize(tmp), size))
            if check_md5 and md5_path(tmp) != etag:
                raise IOError("md5 mismatch")
            os.replace(tmp, dest)
            return "fetched", check_md5
        except Exception as e:  # noqa: BLE001
            if os.path.exists(tmp):
                os.remove(tmp)
            if attempt == 4:
                return "FAILED: %s" % e, check_md5
            time.sleep(3 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--logs-file", required=True)
    ap.add_argument("--logs-key", default="logs")
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()
    d = json.load(open(a.logs_file))
    logs = sorted(str(x) for x in (d if isinstance(d, list) else d[a.logs_key]))
    assert len(set(logs)) == len(logs) and all(UUID.match(x) for x in logs), "bad log list"
    os.makedirs(a.out, exist_ok=True)
    print("logs requested:", len(logs), flush=True)

    def list_log(lg):
        top = list_keys(PREFIX + lg + "/", delimiter="/")
        top = [k for k in top if k[0].rsplit("/", 1)[-1] in TOP_FILES]
        cal = list_keys(PREFIX + lg + "/calibration/")
        lid = list_keys(PREFIX + lg + "/sensors/lidar/")
        return lg, top, cal, lid

    with ThreadPoolExecutor(max_workers=min(16, a.threads)) as ex:
        listed = list(ex.map(list_log, logs))
    rows, problems, lidar_n, lidar_bytes = [], [], 0, 0
    jobs = []
    for lg, top, cal, lid in listed:
        names = sorted(k[0].rsplit("/", 1)[-1] for k in top)
        if names != sorted(TOP_FILES):
            problems.append("%s: top-level files %s" % (lg, names))
        if not cal:
            problems.append("%s: no calibration files" % lg)
        if not lid or not all(k[0].endswith(".feather") for k in lid):
            problems.append("%s: lidar listing empty or not .feather" % lg)
        for k, s, e in top + cal:
            jobs.append((k, s, e, os.path.join(a.out, lg, *safe_rel(k, lg).split("/"))))
        lid = sorted(lid)
        for k, s, e in lid:
            safe_rel(k, lg)
        lp = os.path.join(a.out, lg, LISTING)
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        with open(lp + ".tmp", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["key", "size", "etag"])
            w.writerows(lid)
        os.replace(lp + ".tmp", lp)
        lidar_n += len(lid)
        lidar_bytes += sum(s for _, s, _ in lid)
    print("listed: %d files to fetch (%.1f MB), %d lidar keys recorded (%.1f GB, not fetched) %.0f s"
          % (len(jobs), sum(j[1] for j in jobs) / 1e6, lidar_n, lidar_bytes / 1e9, time.time() - t0), flush=True)
    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        res = list(ex.map(lambda j: fetch(*j), jobs))
    for (k, s, e, dest), (st, chk) in zip(jobs, res):
        rows.append((k, s, e, ("ok" if chk else "no_md5_etag") if not st.startswith("FAILED") else "", st))
    rows.sort()
    man = os.path.join(a.out, "MANIFEST_av2_train225_meta_v05.csv")
    with open(man, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["key", "size", "etag", "md5_ok", "status"])
        w.writerows(rows)
    fails = [r for r in rows if r[4].startswith("FAILED")]
    summ = {"tool": "av2_fetch_v05", "bucket": BUCKET, "prefix": PREFIX, "logs": len(logs), "files": len(rows),
            "bytes": sum(r[1] for r in rows), "fetched": sum(r[4] == "fetched" for r in rows),
            "kept": sum(r[4] == "kept" for r in rows), "failed": len(fails),
            "md5_checked": sum(r[3] == "ok" for r in rows), "lidar_keys_listed": lidar_n, "lidar_bytes_not_fetched": lidar_bytes,
            "problems": problems, "manifest": os.path.abspath(man), "manifest_sha256": hashlib.sha256(open(man, "rb").read()).hexdigest(),
            "wall_seconds": round(time.time() - t0, 1)}
    with open(os.path.join(a.out, "FETCH_SUMMARY_av2_train225_meta_v05.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps(summ), flush=True)
    ok = not fails and not problems
    print("AV2 TRAIN META FETCH DONE" if ok else "AV2 TRAIN META FETCH INCOMPLETE", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
