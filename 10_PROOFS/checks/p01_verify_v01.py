"""Numerical verification of every quantitative statement in P01_THEORY_PROOFS_v01.md.
Synthetic only; numpy + stdlib; seeded. Each check records value(s) and a pass flag."""
import json, math, os
from statistics import NormalDist
import numpy as np

N = NormalDist()
rng = np.random.default_rng(20261030)


def sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def z(d):
    return N.inv_cdf(1 - d)


R, ok = {}, {}

# Lemma 1
m, V, a, b = np.array([1.0, -2.0]), np.array([[2.0, 0.6], [0.6, 1.0]]), np.array([0.6, 0.8]), 3.0
Y = rng.multivariate_normal(m, V, 2_000_000)
mc = float(np.mean(Y @ a > b)); an = sf((b - a @ m) / math.sqrt(a @ V @ a))
R["L1"] = {"mc": mc, "analytic": an}; ok["L1"] = abs(mc - an) < 3e-4

# Theorem 1 (i): inclusion, and equality on active constraints
viol = eq = 0
for _ in range(20000):
    mh = rng.normal(size=2); A = rng.normal(size=(2, 2)); Vh = A @ A.T + 0.1 * np.eye(2)
    aa = rng.normal(size=2); aa /= np.linalg.norm(aa); c = abs(rng.normal()) + 0.5
    slack = abs(rng.normal()) * (rng.random() < 0.5)
    bb = aa @ mh + c * math.sqrt(aa @ Vh @ aa) + slack
    X = mh + rng.normal(size=2) * 2
    U = aa @ (X - mh) / math.sqrt(aa @ Vh @ aa)
    if (aa @ X > bb) and not (U > c):
        viol += 1
    if slack == 0 and ((aa @ X > bb) != (U > c)):
        eq += 1
R["T1i"] = {"inclusion_violations": viol, "active_equality_violations": eq}; ok["T1i"] = viol == 0 and eq == 0
R["T1ii_counterexample"] = {"marginal": sf(z(0.01)), "conditional": 2 * sf(z(0.01))}
ok["T1ii"] = abs(2 * sf(z(0.01)) - 0.02) < 1e-12

# Proposition 1
pr = {}
for kap, rh in ((2.0, 0.5), (4.0, 3.0)):
    q = 1.0; ph = rh * q; p = kap * ph; c = z(0.01)
    U = rng.normal(0, math.sqrt(p + q), 2_000_000) / math.sqrt(ph + q)
    r = (rh + 1) / (kap * rh + 1)
    pr[f"k{kap}_r{rh}"] = {"mc": float(np.mean(U > c)), "formula": sf(c * math.sqrt(r))}
R["P1"] = pr; ok["P1"] = all(abs(v["mc"] - v["formula"]) < 5e-4 for v in pr.values())
rs = [(r_ + 1) / (2 * r_ + 1) for r_ in (0.01, 0.1, 1, 10, 100, 1e6)]
ok["P1_monotone_limits"] = all(x > y for x, y in zip(rs, rs[1:])) and abs(rs[0] - 1) < 0.02 and abs(rs[-1] - 0.5) < 1e-5

# Lemma 3 and Corollary 2
worst = cor2 = 0.0
for _ in range(5000):
    A = rng.normal(size=(4, 4)); Vh = A @ A.T + 0.05 * np.eye(4); e = rng.normal(size=4)
    full = e @ np.linalg.solve(Vh, e)
    for _ in range(4):
        aa = rng.normal(size=4); worst = max(worst, (aa @ e) ** 2 / (aa @ Vh @ aa) / full)
    cor2 = max(cor2, (e[:2] @ np.linalg.solve(Vh[:2, :2], e[:2])) / full)
R["L3_max_ratio"] = worst; R["C2_max_ratio"] = cor2
ok["L3"] = worst <= 1 + 1e-12; ok["C2"] = cor2 <= 1 + 1e-12
R["C1_ratio_0.01"] = math.sqrt(-2 * math.log(0.01)) / z(0.01)

# Theorem 2
R["T2a"] = {str(d): sf(z(d) * math.sqrt(2 / 3)) for d in (0.05, 0.01, 0.001)}
R["T2b1"] = 0.5 * math.exp(-z(0.01) ** 2 / 2)
b2 = {}
th0 = np.linspace(-math.pi / 2, math.pi / 2, 200001); c = z(0.01)
for s in (0.3, 0.6, 1.0):
    norm = s * math.sqrt(2 * math.pi)
    dens = 0.5 * sum(np.exp(-(th0 - 2 * math.pi * k) ** 2 / (2 * s * s)) for k in range(-3, 4)) / norm
    dens += 0.5 * sum(np.exp(-(th0 - math.pi - 2 * math.pi * k) ** 2 / (2 * s * s)) for k in range(-3, 4)) / norm
    integrand = np.exp(-c * c / (2 * np.maximum(np.cos(th0), 1e-12) ** 2)) * dens
    quad = float(np.sum((integrand[1:] + integrand[:-1]) / 2 * np.diff(th0)))
    n = 3_000_000; Rr = np.sqrt(rng.chisquare(2, n)); th = rng.normal(0, s, n) + math.pi * rng.integers(0, 2, n)
    b2[f"s{s}"] = {"quadrature": quad, "mc": float(np.mean(Rr * np.cos(th) > c)),
                   "nees_pv95_mc": float(np.mean(Rr ** 2 > 5.991464547107979))}
R["T2b2"] = b2; ok["T2b2"] = all(abs(v["quadrature"] - v["mc"]) < 4e-4 for v in b2.values())
R["T2c"] = {"ANEES": 5.0, "margin_x": math.sqrt(2.5), "risk": sf(z(0.01) * math.sqrt(2.5))}


def t3sf(t):
    return 1 - (0.5 + (t / (math.sqrt(3) * (1 + t * t / 3)) + math.atan(t / math.sqrt(3))) / math.pi)


R["T2d"] = {str(d): t3sf(z(d) * math.sqrt(3)) for d in (0.05, 0.01, 0.001)}

# Theorem 3 (ii)/(iii): horizon dependence of the dose ratio under CV prediction
s = 4.0; ts = [0.5, 1, 2, 3, 4]; sp2, sv2 = 0.04, 0.25
Rj = [math.sqrt((s * (sp2 + t * t * sv2) + 0.5 * t * t) / ((sp2 + t * t * sv2) + 0.5 * t * t)) for t in ts]
R["T3iii_R_over_horizon"] = Rj; ok["T3iii"] = (max(Rj) - min(Rj)) > 1e-3


# Corollary 3: toy deterministic closed loop (1-D following), margin-sufficient planner
def sim(sig_p2, sig_v2, qcoef, cmult, steps=80, dt=0.1):
    ex, ev, ox, ov = 0.0, 12.0, 40.0, 8.0
    hs = [0.5, 1.0, 1.5, 2.0, 3.0]; acc_grid = np.round(np.arange(-6.0, 2.01, 0.25), 2)
    errs = np.random.default_rng(7).normal(0, 0.3, (steps, 2)); traj = []
    for k in range(steps):
        mx, mv = ox + errs[k, 0], ov + 0.2 * errs[k, 1]
        best = acc_grid[0]
        for acc in acc_grid[::-1]:
            feas = True
            for j, t in enumerate(hs):
                vh = sig_p2 + t * t * sig_v2 + qcoef * t * t
                cm = cmult[j] if isinstance(cmult, (list, tuple)) else cmult
                if ex + ev * t + 0.5 * acc * t * t + 4.5 > mx + mv * t - cm * math.sqrt(vh):
                    feas = False; break
            if feas:
                best = float(acc); break
        traj.append(best); ev = max(0.0, ev + best * dt); ex += ev * dt; ox += ov * dt
    return traj


c0 = z(0.01); sd = 3.0
base_Q0 = sim(0.04, 0.25, 0.0, c0); dosed_Q0 = sim(sd * 0.04, sd * 0.25, 0.0, c0)
retuned_Q0 = sim(0.04, 0.25, 0.0, c0 * math.sqrt(sd))
dosedQ = sim(sd * 0.04, sd * 0.25, 0.5, c0)
best_mismatch = min(sum(abs(x - y) for x, y in zip(dosedQ, sim(0.04, 0.25, 0.5, cc))) for cc in np.linspace(c0, 3 * c0, 801))
hs = [0.5, 1.0, 1.5, 2.0, 3.0]
per_c = [c0 * math.sqrt((sd * (0.04 + t * t * 0.25) + 0.5 * t * t) / ((0.04 + t * t * 0.25) + 0.5 * t * t)) for t in hs]
repr_K3 = sim(0.04, 0.25, 0.5, per_c)
R["C3"] = {"Q0_dosed_vs_retuned_identical": dosed_Q0 == retuned_Q0, "Q0_dose_changes_commands": dosed_Q0 != base_Q0,
           "Qpos_best_global_retune_total_abs_command_diff": best_mismatch,
           "Qpos_K3_representation_identical": repr_K3 == dosedQ}
ok["C3"] = dosed_Q0 == retuned_Q0 and dosed_Q0 != base_Q0 and best_mismatch > 0 and repr_K3 == dosedQ


# Theorem 4
def mreq(k, r, d=0.01):
    return z(d) * math.sqrt((k * r + 1) / (r + 1))


case1 = [mreq(2, 0.2), mreq(2, 5)]; case3 = [mreq(2, 1), mreq(3, 1 / 3)]
infl3 = z(0.01) * (math.sqrt((3 * 1 + 1) / (1 + 1)) - math.sqrt((2 * 1 + 1) / (1 + 1)))
R["T4c"] = {"case1_mult": case1, "case1_excess": case1[1] - case1[0], "case3_mult": case3, "case3_inflation_excess": infl3}
ok["T4c"] = (abs(case1[0] - 2.513) < 1e-3 and abs(case1[1] - 3.150) < 1e-3
             and abs(case3[0] - case3[1]) < 1e-12 and abs(infl3 - 0.441) < 1e-3)
ks = [(1.2, 0.5, 0.5), (2.5, 2.0, 0.3), (4.0, 0.7, 0.2)]


def agg(cc):
    return sum(w * sf(cc * math.sqrt((r + 1) / (k * r + 1))) for k, r, w in ks)


lo, hi = 0.0, 20.0
for _ in range(200):
    mid = (lo + hi) / 2; lo, hi = (mid, hi) if agg(mid) > 0.01 else (lo, mid)
R["T4d_max_risk_at_c_agg"] = max(sf(hi * math.sqrt((r + 1) / (k * r + 1))) for k, r, w in ks)
ok["T4d"] = R["T4d_max_risk_at_c_agg"] > 0.01

# Proposition 5
pdok = True
for _ in range(2000):
    A = rng.normal(size=(4, 4)); S = A @ A.T + 0.01 * np.eye(4); D = rng.normal(size=(4, 4))
    if abs(np.linalg.det(D)) < 1e-6:
        continue
    pdok &= bool(np.all(np.linalg.eigvalsh(D @ S @ D.T) > 0))
R["P5iii_det"] = 0.5 * 1 - 0.9 * 0.9; ok["P5"] = pdok and R["P5iii_det"] < 0


# Theorem 5 and Proposition 6: scene-level CRC, Mondrian stratum, clustered heavy-ish scores
def crc_c(scores_by_scene, d):
    n = len(scores_by_scene)
    if 1 / (n + 1) > d:
        return float("inf")
    lo, hi = -10.0, float(max(u.max() for u in scores_by_scene)) + 1e-9
    for _ in range(60):
        mid = (lo + hi) / 2; Rn = np.mean([np.mean(u > mid) for u in scores_by_scene])
        if n / (n + 1) * Rn + 1 / (n + 1) <= d:
            hi = mid
        else:
            lo = mid
    return hi


def scene(g):
    b = g.normal(0, math.sqrt(0.3))
    if g.integers(0, 3) == 0:
        return None  # stratum absent from this scene
    mm = int(g.integers(5, 60))
    return b + g.normal(0, math.sqrt(0.7), mm) + 0.3 * g.standard_t(4, mm)


res = {}
for d, n in ((0.05, 40), (0.05, 80), (0.10, 25)):
    L = []
    for rep in range(1500):
        cal = []
        while len(cal) < n:
            sc = scene(rng)
            if sc is not None:
                cal.append(sc)
        ch = crc_c(cal, d)
        te = None
        while te is None:
            te = scene(rng)
        L.append(float(np.mean(te > ch)))
    L = np.array(L); res[f"d{d}_n{n}"] = {"delta": d, "E_L_test": float(L.mean()), "se": float(L.std() / math.sqrt(len(L)))}
R["T5_mc"] = res; ok["T5"] = all(v["E_L_test"] <= v["delta"] + 2.5 * v["se"] for v in res.values())
R["P6_allowance"] = {"n39_d0.05": (40 * 0.05 - 1) / 39, "delta_over_2_minus_delta_0.05": 0.05 / 1.95,
                     "n199_d0.01": (200 * 0.01 - 1) / 199, "delta_over_2_minus_delta_0.01": 0.01 / 1.99}
ok["P6"] = (abs(R["P6_allowance"]["n39_d0.05"] - R["P6_allowance"]["delta_over_2_minus_delta_0.05"]) < 1e-12
            and abs(R["P6_allowance"]["n199_d0.01"] - R["P6_allowance"]["delta_over_2_minus_delta_0.01"]) < 1e-12)

ok = {k: bool(v) for k, v in ok.items()}
R["ALL_PASS"] = all(ok.values()); R["pass_flags"] = ok
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p01_verify_v01_results.json")
json.dump(R, open(out, "w"), indent=1, default=float)
print(json.dumps({"pass_flags": ok, "ALL_PASS": R["ALL_PASS"]}, indent=1))
print(json.dumps({k: R[k] for k in ("T2b2", "C3", "T4c", "T5_mc", "T3iii_R_over_horizon", "T4d_max_risk_at_c_agg")}, indent=1, default=float))
