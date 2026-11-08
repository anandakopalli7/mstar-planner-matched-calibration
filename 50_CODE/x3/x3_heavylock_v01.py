#!/usr/bin/env python3
"""X3 heavy-job lock (the lead, 7 Nov 2026). The laptop has about 2 GB of free memory beside other processes, so X3's heavy steps
(decision-mode runs, the horizon re-propagation, B >= 2000 screens on 375 logs) run one at a time. A step takes the lock by creating
LOCK atomically (O_CREAT | O_EXCL) with its owner, PID and start time, and removes it when done. A lock whose PID no longer exists
is stale and is taken over (recorded in the history file). Waiting is logged; nothing is killed.
Usage (Python):  with heavy_lock("x3-core: (a) B4 runs T1"): ...
Usage (shell):   python -B x3_heavylock_v01.py status
"""
import contextlib
import json
import os
import sys
import time

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "60_RESULTS", "x3_explore_v01")
LOCK = os.path.join(D, "HEAVY_LOCK.json")
HIST = os.path.join(D, "HEAVY_LOCK_HISTORY.jsonl")


def _pid_alive(pid):
    """Windows: OpenProcess + GetExitCodeProcess (STILL_ACTIVE = 259). Never os.kill (signal 0 is CTRL_C_EVENT on Windows)."""
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259
    except Exception:
        return True


def _hist(ev):
    with open(HIST, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(ev, t=time.strftime("%Y-%m-%d %H:%M:%S"))) + "\n")


def status():
    if not os.path.exists(LOCK):
        return None
    try:
        return json.load(open(LOCK, encoding="utf-8"))
    except Exception:
        return {"unreadable": True}


@contextlib.contextmanager
def heavy_lock(owner, poll_s=30, max_wait_s=6 * 3600):
    os.makedirs(D, exist_ok=True)
    t0 = time.time()
    announced = False
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"owner": owner, "pid": os.getpid(), "start": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
            _hist({"event": "take", "owner": owner, "pid": os.getpid(), "waited_s": round(time.time() - t0)})
            break
        except FileExistsError:
            st = status() or {}
            if st.get("pid") and not _pid_alive(st["pid"]):
                _hist({"event": "stale_takeover", "owner": owner, "stale": st})
                try:
                    os.remove(LOCK)
                except FileNotFoundError:
                    pass
                continue
            if not announced:
                print("x3 heavy lock held by %s; waiting" % st.get("owner"), flush=True)
                announced = True
            if time.time() - t0 > max_wait_s:
                raise TimeoutError("x3 heavy lock: waited %d s for %s" % (max_wait_s, st))
            time.sleep(poll_s)
    try:
        yield
    finally:
        try:
            os.remove(LOCK)
        except FileNotFoundError:
            pass
        _hist({"event": "release", "owner": owner, "pid": os.getpid(), "held_s": round(time.time() - t0)})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(status()))
