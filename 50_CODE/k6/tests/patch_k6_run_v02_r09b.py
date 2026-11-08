"""R09b fixes to k6_run_v02.py (m6 b/c, m11). Run once (Claude line, 1 Nov 2026)."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(K, "k6_run_v02.py")
s = open(p, encoding="utf-8").read()
assert "episodes_sha256" not in s, "already applied"
rep = [
    ("Usage: python -B k6_run_v01.py --caches", "Usage: python -B k6_run_v02.py --caches"),
    (r'''    with open(os.path.join(a.out, "episodes_%s.jsonl" % a.tag), "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    np.savez_compressed(os.path.join(a.out, "counts_%s.npz" % a.tag), episode=np.array(ce, np.int32), cell=np.array(cc, np.int32),
                        n=np.array(cn, np.int32), exceed=np.array(cx, np.int32))''',
     r'''    ep_path, ct_path = os.path.join(a.out, "episodes_%s.jsonl" % a.tag), os.path.join(a.out, "counts_%s.npz" % a.tag)
    with open(ep_path, "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    np.savez_compressed(ct_path, episode=np.array(ce, np.int32), cell=np.array(cc, np.int32),
                        n=np.array(cn, np.int32), exceed=np.array(cx, np.int32))'''),
    ('''           "runner_sha256": sha256_path(__file__), "manifest_sha256": [sha256_path(os.path.join(c, "MANIFEST.json")) for c in a.caches],''',
     '''           "runner_sha256": sha256_path(__file__), "manifest_sha256": [sha256_path(os.path.join(c, "MANIFEST.json")) for c in a.caches],
           "caches": [os.path.abspath(c) for c in a.caches], "episodes_sha256": sha256_path(ep_path), "counts_sha256": sha256_path(ct_path),'''),
]
for a_, b_ in rep:
    assert s.count(a_) == 1, a_[:70]
    s = s.replace(a_, b_, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("runner patched (R09b)")
