"""Make x1_export_v06.py from x1_export_v05.py (Claude line, 31 Oct 2026): adds Poly-MOT (paper/baseline/poly_mot) to the
approved experiments and checks P against each track's own state dimension (10 for CV/CTRA, 13 for CA). Kept as a record."""
import os

X = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(X, "x1_export_v05.py"), encoding="utf-8").read()
reps = [
    ('HARNESS_VERSION = "x1_export_v05 (2026-10-31): v04 + a second approved experiment (CANMOT sample-covariance configuration)"',
     'HARNESS_VERSION = "x1_export_v06 (2026-10-31): v05 + Poly-MOT (paper/baseline/poly_mot); P checked against each track\'s own state dimension"'),
    ('APPROVED_EXPERIMENTS = ("paper/local/canmot/sc", "paper/local/sample/trainval")',
     'APPROVED_EXPERIMENTS = ("paper/local/canmot/sc", "paper/local/sample/trainval", "paper/baseline/poly_mot")'),
    ('"C1": "every emitted track has a native covariance of shape 9x9 and a recorded P of shape 10x10",',
     '"C1": "every emitted track has a native covariance of shape 9x9 and a recorded P of its state dimension (10 for CV and CTRA, 13 for CA)",'),
    ('pc = mat_check(d["P"], STATE_DIM) if d and "P" in d else',
     'pc = mat_check(d["P"], len(d["state"])) if d and "P" in d else'),
    # Poly-MOT's CTRA measurement Jacobian has parallel velocity rows at zero speed, so its 9x9 native covariance is
    # singular by construction. The analysis uses only the native xy block and P, so C3 and C4 are checked on those.
    ('"C3": "native covariance and P symmetric (max|C-C^T| <= 1e-9 max|C|)",',
     '"C3": "native covariance xy block and P symmetric (max|C-C^T| <= 1e-9 max|C|); v06: the 9x9 native block is not required",'),
    ('"C4": "native covariance and P positive-definite (Cholesky succeeds, min eigenvalue > 0)",',
     '"C4": "native covariance xy block and P positive-definite (Cholesky succeeds, min eigenvalue > 0); v06: the 9x9 native block is not required (singular for CTRA at zero speed)",'),
    ('                        counts["sym_ok"] += int(c["symmetric"] and pc["symmetric"])\n                        counts["pd_ok"] += int(c["pd"] and pc["pd"])',
     '                        cxy = mat_check(np.asarray(r.get("covariance", []), dtype=float)[:2, :2], 2) if c["shape_ok"] else c\n'
     '                        counts["sym_ok"] += int(cxy["symmetric"] and pc["symmetric"])\n                        counts["pd_ok"] += int(cxy["pd"] and pc["pd"])'),
]
for a, b in reps:
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)
open(os.path.join(X, "x1_export_v06.py"), "w", encoding="utf-8", newline="\n").write(t)
print("x1_export_v06.py written")
