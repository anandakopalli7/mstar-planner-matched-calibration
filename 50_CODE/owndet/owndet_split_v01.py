"""owndet_split_v01 (own-detector job, D18 v02 "Choices forced by option A" 1, 2 Nov 2026): the split of the 700 AV2 sensor
training logs.

Rule (D18 v02, fixed before any training-log data is examined): sort the 700 log ids, permute them with
numpy.random.default_rng(20261102).permutation; the first 225 are held out for the confirmation, the other 475 train the
detector. Log ids come from an unsigned listing of the public bucket (datasets/av2/sensor/train/, no account); no file content
is read for the split. City composition (reported, not used by the rule): the city code in each log's map archive file name
(<log>/map/log_map_archive_<log>____<CITY>_city_<n>.json), from a listing of <log>/map/ only.
Usage: python -I owndet_split_v01.py --out AV2_TRAIN_SPLIT_v01.json
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BUCKET = "https://argoverse.s3.amazonaws.com"
PREFIX = "datasets/av2/sensor/train/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
SEED = 20261102
N_HELD = 225


def get_xml(url, tries=8):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return ET.fromstring(r.read())
        except Exception:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def list_logs():
    out, token = [], None
    while True:
        q = {"list-type": "2", "prefix": PREFIX, "delimiter": "/"}
        if token:
            q["continuation-token"] = token
        root = get_xml(BUCKET + "/?" + urllib.parse.urlencode(q))
        out += [p.find(NS + "Prefix").text[len(PREFIX):].strip("/") for p in root.findall(NS + "CommonPrefixes")]
        nt = root.find(NS + "NextContinuationToken")
        if nt is None:
            return out
        token = nt.text


def city_of(log):
    q = {"list-type": "2", "prefix": PREFIX + log + "/map/"}
    root = get_xml(BUCKET + "/?" + urllib.parse.urlencode(q))
    names = [c.find(NS + "Key").text.split("/")[-1] for c in root.findall(NS + "Contents")]
    arch = [n for n in names if n.startswith("log_map_archive_")]
    return arch[0].split("____")[1].split("_city")[0] if arch else "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    logs = sorted(list_logs())
    assert len(logs) == 700, len(logs)
    perm = np.random.default_rng(SEED).permutation(len(logs))
    order = [logs[i] for i in perm]
    held, train = order[:N_HELD], order[N_HELD:]
    split = {"rule": "sorted(700 AV2 sensor train log ids) -> numpy.random.default_rng(20261102).permutation; first 225 held out, other 475 train",
             "numpy_version": np.__version__, "seed": SEED, "n_logs": len(logs),
             "sorted_log_ids_sha256": hashlib.sha256("\n".join(logs).encode()).hexdigest(),
             "held_out_225": held, "train_475": train}
    body = json.dumps(split, indent=1)
    with open(a.out, "w", newline="\n") as f:
        f.write(body)
    print("split written", a.out, "sha256", hashlib.sha256(body.encode()).hexdigest(), flush=True)
    with ThreadPoolExecutor(8) as ex:
        cities = dict(zip(logs, ex.map(city_of, logs)))
    comp = {}
    for part, ids in (("held_out_225", held), ("train_475", train), ("all_700", logs)):
        c = {}
        for lg in ids:
            c[cities[lg]] = c.get(cities[lg], 0) + 1
        comp[part] = dict(sorted(c.items()))
    with open(a.out.replace(".json", "_CITIES.json"), "w", newline="\n") as f:
        json.dump({"source": "city code in <log>/map/log_map_archive_*.json file names (listing only)", "composition": comp, "city_by_log": cities}, f, indent=1)
    print(json.dumps(comp), flush=True)


if __name__ == "__main__":
    sys.exit(main())
