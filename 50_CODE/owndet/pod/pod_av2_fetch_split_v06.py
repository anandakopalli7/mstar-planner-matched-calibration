"""pod_av2_fetch_split_v06 (own-detector job, 2 Nov 2026) = 50_CODE/av2/av2_fetch_v04.py with the split as a parameter
(--split train|val, default val) and an optional --logs-file (one log id per line) to restrict the logs; manifest name
MANIFEST_av2_<split>_lidar_v06[_maps].csv. Same files kept per log (annotations, poses, calibration, lidar, and map/* with --maps).
av2_fetch_v04 (v03 + retries on every listing call, listing concurrency 16; v01-v03 kept): lidar-only download of the Argoverse 2 Sensor *validation* split from the public S3 bucket.

Standard library only (urllib, xml, concurrent.futures). Unsigned ListObjectsV2 calls on
https://argoverse.s3.amazonaws.com, then plain HTTPS GETs of the keys we need:
  <log>/annotations.feather, <log>/city_SE3_egovehicle.feather, <log>/calibration/*, <log>/sensors/lidar/*.feather
Cameras are skipped (D15 §3 step 1); maps are skipped unless --maps is given (the official detection evaluation
filters ground truth by the region of interest, which needs <log>/map/*). v01 is kept unchanged. Resumable: a file whose size matches the listing is not re-fetched.
Writes a manifest CSV (key, size, etag, local path, status) next to the data.

Usage: python -B av2_fetch_v01.py --out <folder> [--logs N] [--threads 8]
The output folder is treated as untrusted data (D15): nothing in it is executed or imported.
"""
import argparse
import csv
import hashlib
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

BUCKET = "https://argoverse.s3.amazonaws.com"
PREFIX = "datasets/av2/sensor/val/"  # v06: replaced from --split in main()
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
KEEP_SUFFIX = ("annotations.feather", "city_SE3_egovehicle.feather")
KEEP_DIRS = ("/calibration/", "/sensors/lidar/")


def list_keys(prefix):
    """All (key, size, etag) under prefix, following continuation tokens."""
    out, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        url = BUCKET + "/?" + urllib.parse.urlencode(q)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    root = ET.fromstring(r.read())
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 4:
                    raise
                time.sleep(2 * (attempt + 1))
        for c in root.findall(NS + "Contents"):
            out.append((c.find(NS + "Key").text, int(c.find(NS + "Size").text), c.find(NS + "ETag").text.strip('"')))
        nt = root.find(NS + "NextContinuationToken")
        if nt is None:
            break
        token = nt.text
    return out


def get_xml(url, tries=8):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return ET.fromstring(r.read())
        except Exception:  # noqa: BLE001  (transient DNS / connection errors under load)
            if attempt == tries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def list_top(prefix):
    """Objects directly under prefix (not in sub-folders), e.g. annotations.feather and city_SE3_egovehicle.feather."""
    q = {"list-type": "2", "prefix": prefix, "delimiter": "/"}
    root = get_xml(BUCKET + "/?" + urllib.parse.urlencode(q))
    return [(c.find(NS + "Key").text, int(c.find(NS + "Size").text), c.find(NS + "ETag").text.strip('"')) for c in root.findall(NS + "Contents")]


def list_logs():
    q = {"list-type": "2", "prefix": PREFIX, "delimiter": "/"}
    root = get_xml(BUCKET + "/?" + urllib.parse.urlencode(q))
    return sorted(p.find(NS + "Prefix").text for p in root.findall(NS + "CommonPrefixes"))


def wanted(key, maps=False):
    return key.endswith(KEEP_SUFFIX) or any(d in key for d in KEEP_DIRS) or (maps and "/map/" in key)


def fetch(key, size, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) == size:
        return "kept"
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
            os.replace(tmp, dest)
            return "fetched"
        except Exception as e:  # noqa: BLE001
            if attempt == 4:
                return "FAILED: %s" % e
            time.sleep(3 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--logs", type=int, default=0, help="limit to the first N logs (0 = all)")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--maps", action="store_true", help="also fetch <log>/map/* (needed for the ROI-filtered evaluation)")
    ap.add_argument("--split", default="val", choices=["train", "val"])
    ap.add_argument("--logs-file", default="")
    a = ap.parse_args()
    global PREFIX
    PREFIX = "datasets/av2/sensor/%s/" % a.split
    os.makedirs(a.out, exist_ok=True)
    logs = list_logs()
    print("val logs listed:", len(logs), flush=True)
    if a.logs_file:
        want = set(l.strip() for l in open(a.logs_file) if l.strip())
        logs = [l for l in logs if l[len(PREFIX):].strip("/") in want]
        print("restricted to logs-file:", len(logs), flush=True)
    if a.logs:
        logs = logs[: a.logs]
    # v03: list only the sub-prefixes we need (not the ~2,700 camera keys per log), all logs in parallel
    subs = ["sensors/lidar/", "calibration/"] + (["map/"] if a.maps else [])
    def list_log(lg):
        ks = []
        for sub in subs:
            ks += list_keys(lg + sub)
        top = [k for k in list_top(lg)]
        return [k for k in ks + top if wanted(k[0], a.maps)]
    keys = []
    with ThreadPoolExecutor(max_workers=min(16, a.threads)) as ex:
        for ks in ex.map(list_log, logs):
            keys += ks
    total = sum(k[1] for k in keys)
    print("files to hold: %d, %.2f GB" % (len(keys), total / 1e9), flush=True)
    rows, done, t0 = [], 0, time.time()
    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        futs = {ex.submit(fetch, k, s, os.path.join(a.out, k[len(PREFIX):].replace("/", os.sep))): (k, s, e) for k, s, e in keys}
        for fu in as_completed(futs):
            k, s, e = futs[fu]
            st = fu.result()
            rows.append((k, s, e, st))
            done += 1
            if done % 500 == 0 or st.startswith("FAILED"):
                print("%d/%d %s %.0fs" % (done, len(keys), st if st.startswith("FAILED") else "", time.time() - t0), flush=True)
    rows.sort()
    man = os.path.join(a.out, "MANIFEST_av2_%s_lidar_v06%s.csv" % (a.split, "_maps" if a.maps else ""))
    with open(man, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "size", "etag", "status"])
        w.writerows(rows)
    fails = [r for r in rows if r[3].startswith("FAILED")]
    h = hashlib.sha256(open(man, "rb").read()).hexdigest()
    print("manifest", man, "sha256", h, flush=True)
    print("fetched %d kept %d failed %d" % (sum(r[3] == "fetched" for r in rows), sum(r[3] == "kept" for r in rows), len(fails)), flush=True)
    print("AV2 FETCH DONE" if not fails else "AV2 FETCH INCOMPLETE", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
