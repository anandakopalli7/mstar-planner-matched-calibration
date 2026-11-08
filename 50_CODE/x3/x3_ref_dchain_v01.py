#!/usr/bin/env python3
"""x3_ref_dchain_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Runs the remaining (d) steps under ONE heavy lock instead of one lock per step (the shared lock was handed over
about every 5 minutes, and each of x3-ref's eleven short steps waited for it separately): the item builds not yet on disk
(x3_ref_items_v01.main), the fit-rule validation (x3_ref_fit_v01.main --validate), the per-reference fits (x3_ref_fit_v01.main --ref)
and the d1 Z0 check (x3_ref_z0check_v01). The scripts are imported unchanged; their own heavy_lock calls are replaced in this process
by a no-op (x3_heavylock_v01.heavy_lock is patched before they import it), because this driver already holds the lock. A step whose
output exists is skipped (resume, never restart).
Usage: python -B x3_ref_dchain_v01.py
"""
import contextlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
import x3_heavylock_v01 as HL  # noqa: E402

REAL_LOCK = HL.heavy_lock


@contextlib.contextmanager
def _held_by_driver(owner, *a, **k):
    print("  (inner lock request '%s' served by the driver's lock)" % owner, flush=True)
    yield


def main():
    C.run_log_ok()
    import x3_ref_items_v01 as IT
    import x3_ref_fit_v01 as FT
    import x3_ref_z0check_v01 as ZC
    steps = []
    for r in ("d1", "d2"):
        for t in ("t1", "t3"):
            steps.append(("items %s %s" % (r, t), os.path.join(C.D_REF, "items_x3ref_%s_%s_summary.json" % (r, t)),
                          lambda r=r, t=t: IT.main(["--trk", t, "--ref", r, "--workers", "2"])))
    for t in ("t1", "t3"):
        steps.append(("fit validate %s" % t, os.path.join(C.D_REF, "VALIDATION_fit_record_%s.json" % t),
                      lambda t=t: FT.main(["--validate", "--trk", t])))
    for r in ("d0", "d1", "d2"):
        for t in ("t1", "t3"):
            steps.append(("fit %s %s" % (r, t), os.path.join(C.D_REF, "fit_report_x3ref_%s_%s.json" % (r, t)),
                          lambda r=r, t=t: FT.main(["--ref", r, "--trk", t])))
    steps.append(("z0check t3", os.path.join(C.D_REF, "VALIDATION_d1_z0_t3.json"), lambda: ZC.main(["--trk", "t3"])))
    with REAL_LOCK("x3-ref: (d) items d1/d2, fit validation, fits (one lock)"):
        HL.heavy_lock = _held_by_driver
        for i, (name, done_file, fn) in enumerate(steps):
            if os.path.exists(done_file):
                print("skip (done): " + name, flush=True)
                continue
            t0 = time.time()
            print("== " + name, flush=True)
            C.live("dchain: " + name, i, len(steps))
            fn()
            print("== done %s  %.0f s" % (name, time.time() - t0), flush=True)
        HL.heavy_lock = REAL_LOCK
    C.live("dchain done", len(steps), len(steps))
    C.run_log_ok()
    print("X3 REF DCHAIN DONE")


if __name__ == "__main__":
    main()
