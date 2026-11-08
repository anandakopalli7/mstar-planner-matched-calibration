"""Make m_freeze_v04.py from m_freeze_v03.py and summarise_tests_v04.py from summarise_tests_v03.py (Claude line,
31 Oct 2026): plan v05, the derived eps, the OC merges at that eps, R07c. Kept as the record of the edits."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(HERE, "m_freeze_v03.py"), encoding="utf-8").read()
reps = [
    ('"""Freeze the method-stage pre-registration v04 (Claude line, v03, 31 Oct 2026).', '"""Freeze the method-stage pre-registration v05 (Claude line, v04, 31 Oct 2026).'),
    ('- the plans v01-v03, their hash log, P02 v03, and reviews R07 and R07b;', '- the plans v01-v04 and their makers, their hash log, P02 v03, and reviews R07, R07b and R07c;'),
    ('Every test JSON must report all_ok (R07b N-m9), and the OC merges must report acceptance.all (plan v04 section 9).',
     'Every test JSON must report all_ok (R07b N-m9), and the OC merges must report acceptance.all at the derived eps, which must\nequal m_lib_v03.EPS_POOLED (plan v05 section 9).'),
    ('The freeze hash goes into M_FREEZE_RECORD_v04.txt', 'The freeze hash goes into M_FREEZE_RECORD_v05.txt'),
    ('Usage: python m_freeze_v03.py', 'Usage: python m_freeze_v04.py'),
    ('''    files += [j("40_PROTOCOL", f) for f in ("M_PREREGISTRATION_v01.md", "M_PREREGISTRATION_v02.md", "M_PREREGISTRATION_v03.md", "M_PLAN_HASH_LOG.txt",
                                            "X2_PREREGISTRATION_v02.md", "make_plan_v04.py")]''',
     '''    files += [j("40_PROTOCOL", f) for f in ("M_PREREGISTRATION_v01.md", "M_PREREGISTRATION_v02.md", "M_PREREGISTRATION_v03.md", "M_PREREGISTRATION_v04.md",
                                            "M_PLAN_HASH_LOG.txt", "X2_PREREGISTRATION_v02.md", "make_plan_v04.py", "make_plan_v05.py")]
    files += sorted(glob.glob(j("40_PROTOCOL", "make_plan_v05_r07c_edits.json")))'''),
    ('''              j("70_TESTS", "R07B_M_PREFREEZE_REREVIEW_v01.md"), j("80_LOGS", "pip_freeze_canmot310.txt")]''',
     '''              j("70_TESTS", "R07B_M_PREFREEZE_REREVIEW_v01.md"), j("70_TESTS", "R07C_M_PREFREEZE_CHECK_v01.md"), j("80_LOGS", "pip_freeze_canmot310.txt")]'''),
    ('''    ocs = [os.path.join(S, "oc_v02_T1.json"), os.path.join(S, "oc_v02_T3.json")]''',
     '''    ocs = [os.path.join(S, "oc_v03_T1.json"), os.path.join(S, "oc_v03_T3.json")]'''),
    ('''    pre += sorted(glob.glob(os.path.join(S, "oc_v02", "*.json"))) + [j("70_TESTS", "M_SYNTHETIC_TESTS_v03.md")]''',
     '''    pre += sorted(glob.glob(os.path.join(S, "oc_v02", "*.json"))) + [os.path.join(S, "eps_v01.json"), j("70_TESTS", "M_SYNTHETIC_TESTS_v04.md")]'''),
    ('''    for p in ocs:
        assert json.load(open(p))["acceptance"]["all"] is True, "OC acceptance criteria not met: " + p''',
     '''    eps = json.load(open(os.path.join(S, "eps_v01.json")))["eps"]
    import sys
    sys.path.insert(0, os.path.join(B, "50_CODE", "m"))
    import m_lib_v03
    assert abs(m_lib_v03.EPS_POOLED - eps) < 1e-12, "m_lib_v03.EPS_POOLED differs from the derived eps"
    for p in ocs:
        oc = json.load(open(p))
        assert oc["acceptance"]["all"] is True and oc["eps_used"] == eps, "OC acceptance criteria not met at the derived eps: " + p'''),
    ('''    plan = j("40_PROTOCOL", "M_PREREGISTRATION_v04.md")''', '''    plan = j("40_PROTOCOL", "M_PREREGISTRATION_v05.md")'''),
    ('''M_FREEZE_RECORD_v04.txt"), "a").write("%s  %s  M_PREREGISTRATION_v04.md frozen''', '''M_FREEZE_RECORD_v05.txt"), "a").write("%s  %s  M_PREREGISTRATION_v05.md frozen'''),
]
for a, b in reps:
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)
open(os.path.join(HERE, "m_freeze_v04.py"), "w", encoding="utf-8", newline="\n").write(t)

s = open(os.path.join(HERE, "tests", "summarise_tests_v03.py"), encoding="utf-8").read()
reps = [
    ("70_TESTS/M_SYNTHETIC_TESTS_v03.md\n(Claude line, v03, 31 Oct 2026).",
     "70_TESTS/M_SYNTHETIC_TESTS_v04.md\n(Claude line, v04, 31 Oct 2026): v03 plus the OC merges at the derived eps (oc_v03_*.json, eps_v01.json)."),
    ('L = ["# M synthetic tests v03 (31 Oct 2026)", "",', 'L = ["# M synthetic tests v04 (31 Oct 2026)", "",'),
    ('"## 7. Operating characteristics at the real counts (OC v02; plan v04 §9)", ""]',
     '"## 7. Operating characteristics at the real counts (OC v02 shards, merged at the derived eps; plan v05 §9)", "",\n          "Derived tolerance: %s" % json.dumps(J("eps_v01.json")), ""]'),
    ('p = os.path.join(S, "oc_v02_%s.json" % t)', 'p = os.path.join(S, "oc_v03_%s.json" % t)'),
    ('open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v03.md"), "w"', 'open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v04.md"), "w"'),
]
for a, b in reps:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(os.path.join(HERE, "tests", "summarise_tests_v04.py"), "w", encoding="utf-8", newline="\n").write(s)
print("m_freeze_v04.py and summarise_tests_v04.py written")
