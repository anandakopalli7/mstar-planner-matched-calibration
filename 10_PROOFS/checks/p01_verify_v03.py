"""P01 v02 verification (supersedes p01_verify_v01 / v02_c3 as the reference checks; those files are kept).
Constructive checks only; every quoted number has a pass flag. Synthetic; numpy + stdlib; seeded."""
import json, math, os
from statistics import NormalDist
import numpy as np

N = NormalDist(); rng = np.random.default_rng(20261031)
sf = lambda x: 0.5 * math.erfc(x / math.sqrt(2)); z = lambda d: N.inv_cdf(1 - d)
R, ok = {}, {}

# Lemma 1 with a non-trivial probability and relative tolerance
m, V, a, b = np.array([1.0, -2.0]), np.array([[2.0, 0.6], [0.6, 1.0]]), np.array([0.6, 0.8]), 1.0
Y = rng.multivariate_normal(m, V, 4_000_000); mc = float(np.mean(Y @ a > b)); an = sf((b - a @ m) / math.sqrt(a @ V @ a))
R["L1"] = {"mc": mc, "analytic": an}; ok["L1"] = abs(mc - an) / an < 0.01

# Theorem 1 (i), slack-aware identity: P(a'X > b) = P(U > tau), tau = (b - a'm)/sqrt(v) >= c
taus = []
for _ in range(3):
    c = 2.326; slack = abs(rng.normal()); v = 1.7; tau = c + slack / math.sqrt(v)
    U = rng.normal(0, 1.3, 2_000_000)  # true sd 1.3 vs exported 1
    lhs = float(np.mean(U * math.sqrt(v) > c * math.sqrt(v) + slack)); rhs = float(np.mean(U > tau))
    taus.append((lhs, rhs))
R["T1i_slack_identity"] = taus; ok["T1i"] = all(abs(x - y) < 1e-12 for x, y in taus)

# Theorem 1 (ii) counterexample, constructed (half-normal mixture)
L = rng.integers(1, 3, 4_000_000); A0 = np.abs(rng.normal(size=L.size)); U = np.where(L == 1, A0, -A0)
R["T1ii"] = {"marginal": float(np.mean(U > z(0.01))), "cond_L1": float(np.mean(U[L == 1] > z(0.01))), "var": float(U.var())}
ok["T1ii"] = abs(R["T1ii"]["marginal"] - 0.01) < 5e-4 and abs(R["T1ii"]["cond_L1"] - 0.02) < 8e-4 and abs(R["T1ii"]["var"] - 1) < 5e-3

# Prop 1: formula vs MC incl. kappa < 1
pr = {}
for kap, rh in ((2.0, 0.5), (4.0, 3.0), (0.5, 2.0)):
    q = 1.0; ph = rh * q; p = kap * ph; c = z(0.01)
    U = rng.normal(0, math.sqrt(p + q), 3_000_000) / math.sqrt(ph + q)
    pr[f"k{kap}_r{rh}"] = {"mc": float(np.mean(U > c)), "formula": sf(c * math.sqrt((rh + 1) / (kap * rh + 1)))}
R["P1"] = pr; ok["P1"] = all(abs(v["mc"] - v["formula"]) / v["formula"] < 0.03 for v in pr.values())

# Lemma 3 / Cor 2 / chi2_9 radius
worst = cor2 = 0.0
for _ in range(5000):
    A = rng.normal(size=(4, 4)); Vh = A @ A.T + 0.05 * np.eye(4); e = rng.normal(size=4); full = e @ np.linalg.solve(Vh, e)
    for _ in range(4):
        aa = rng.normal(size=4); worst = max(worst, (aa @ e) ** 2 / (aa @ Vh @ aa) / full)
    cor2 = max(cor2, (e[:2] @ np.linalg.solve(Vh[:2, :2], e[:2])) / full)
chi9 = np.quantile(rng.chisquare(9, 4_000_000), 0.95)
R["L3"] = worst; R["C2"] = cor2; R["sqrt_chi2_9_95"] = float(math.sqrt(chi9)); R["C1_ratio_0.01"] = math.sqrt(-2 * math.log(0.01)) / z(0.01)
ok["L3"] = worst <= 1 + 1e-12; ok["C2"] = cor2 <= 1 + 1e-12; ok["chi9"] = abs(math.sqrt(chi9) - 4.113) < 0.005; ok["C1"] = abs(R["C1_ratio_0.01"] - 1.3046) < 1e-3

# Theorem 2 (a): E[N] and axis-2 risk; (b2): N computed from e; (d): 2-D embedding of t3
Sh = np.diag([2.0, 2 / 3]); e = rng.normal(size=(3_000_000, 2)); Nn = np.einsum('ij,jk,ik->i', e, np.linalg.inv(Sh), e)
R["T2a"] = {"E_N": float(Nn.mean()), "risk_axis2_0.01": float(np.mean(e[:, 1] / math.sqrt(2 / 3) > z(0.01))), "analytic": sf(z(0.01) * math.sqrt(2 / 3))}
ok["T2a"] = abs(R["T2a"]["E_N"] - 2) < 0.01 and abs(R["T2a"]["risk_axis2_0.01"] - 0.0288) < 6e-4
b2 = {}
for s in (0.3, 0.6, 1.0):
    n = 3_000_000; Rr = np.sqrt(rng.chisquare(2, n)); th = rng.normal(0, s, n) + math.pi * rng.integers(0, 2, n)
    ee = np.stack([Rr * np.cos(th), Rr * np.sin(th)], 1); NN = (ee ** 2).sum(1)  # export I2
    b2[f"s{s}"] = {"risk_a0": float(np.mean(ee[:, 0] > z(0.01))), "pv95_from_e": float(np.mean(NN > 5.991464547107979)),
                   "N_q95": float(np.quantile(NN, 0.95))}
R["T2b2"] = b2; ok["T2b2"] = (abs(b2["s0.3"]["risk_a0"] - 0.0268) < 5e-4 and abs(b2["s0.6"]["risk_a0"] - 0.0181) < 5e-4
                               and abs(b2["s1.0"]["risk_a0"] - 0.0121) < 5e-4 and all(abs(v["pv95_from_e"] - 0.05) < 1e-3 for v in b2.values()))
T = rng.standard_t(3, (3_000_000, 2)) / math.sqrt(3)
R["T2d"] = {"var": T.var(0).tolist(), "risk_0.01": float(np.mean(T[:, 0] > z(0.01))), "risk_0.001": float(np.mean(T[:, 0] > z(0.001)))}
ok["T2d"] = abs(R["T2d"]["risk_0.01"] - 0.0137) < 5e-4 and abs(R["T2d"]["risk_0.001"] - 0.0064) < 3e-4

# Theorem 3: (a) constant-multiplier family, global dose with heterogeneous rho -> non-representable;
# (b) CC-joint existence-weighted family c_j(theta)=z_{1-theta/p_j}: Q=0 global dose s=4 not representable by one theta
def best_theta_rel_err(ps, s, dref=0.01):
    target = [math.sqrt(s) * z(dref / p) for p in ps]
    best = 1e9
    for lt in np.linspace(-14, -1, 20001):
        th = 10 ** lt; c = [z(min(th / p, 0.4999)) for p in ps]
        best = min(best, max(abs(ci - ti) / ti for ci, ti in zip(c, target)))
    return best
R["T3_ccjoint_Q0_s4_best_maxrelerr"] = best_theta_rel_err([0.5, 0.8, 1.0], 4.0)
ok["T3_ccjoint"] = R["T3_ccjoint_Q0_s4_best_maxrelerr"] > 0.01
Sig = np.array([[0.09, 0.06], [0.06, 0.25]])  # 1-D pos/vel along a, correlated (rho_pv ~ 0.4)
hs = np.arange(0.2, 4.01, 0.2); ph = np.array([Sig[0, 0] + 2 * t * Sig[0, 1] + t * t * Sig[1, 1] for t in hs])
for name, q in (("q_t2", 0.5 * hs ** 2), ("q_t3", 0.3 * hs ** 3)):
    R[f"T3iii_rho_range_{name}"] = [float((ph / q).min()), float((ph / q).max())]
ok["T3iii"] = R["T3iii_rho_range_q_t3"][1] / R["T3iii_rho_range_q_t3"][0] > 2


# Corollary 3 adversarial suite (1-D following; c on exported sd; s = 4 exact power of 2)
def sim(sp2_fn, qcoef, cmult, cost_w=0.0, grid_step=0.05, brake=False, steps=120, dt=0.1):
    ex, ev, ox, ov = 0.0, 14.0, 45.0, 12.0; HS = [0.5, 1.0, 2.0, 4.0]
    grid = np.round(np.arange(-8.0, 2.0001, grid_step), 4); errs = np.random.default_rng(11).normal(0, 0.25, (steps, 2)); tr = []
    for k in range(steps):
        if brake and 40 <= k < 70: ov = max(0.0, ov - 0.6)
        mx, mv = ox + errs[k, 0], ov + 0.2 * errs[k, 1]; sp2 = sp2_fn(k); best, bscore = float(grid[0]), -1e18
        for acc in grid:
            feas = True
            for j, t in enumerate(HS):
                vh = sp2 * (1 + t * t) + qcoef * t * t; cm = cmult[j] if isinstance(cmult, (list, tuple)) else cmult
                if ex + ev * t + 0.5 * acc * t * t + 4.5 > mx + mv * t - cm * math.sqrt(vh): feas = False; break
            if feas:
                score = acc - cost_w * math.sqrt(sp2) * abs(acc)  # covariance enters the cost when cost_w > 0
                if score > bscore: best, bscore = float(acc), score
        tr.append(best); ev = max(0.0, ev + best * dt); ex += ev * dt; ox += ov * dt
    return tr


c0 = z(0.01); s = 4.0; const = lambda k: 0.1
d_marg = sim(lambda k: s * 0.1, 0.0, c0); r_marg = sim(const, 0.0, c0 * 2.0)
d_cost = sim(lambda k: s * 0.1, 0.0, c0, cost_w=3.0); r_cost = sim(const, 0.0, c0 * 2.0, cost_w=3.0)
mature = lambda k: 4 * math.exp(-k / 15) + 0.04
d_tv = sim(lambda k: s * mature(k), 0.5, c0)
mm_tv = min(sum(abs(x - y) for x, y in zip(d_tv, sim(mature, 0.5, cc))) for cc in np.linspace(c0, 3 * c0, 801))
d_grid = sim(lambda k: s * 0.1, 0.0, c0); coarse = [c0 * x for x in np.arange(1.0, 3.0, 0.15)]  # grid omits 2.0
mm_grid = min(sum(abs(x - y) for x, y in zip(d_grid, sim(const, 0.0, cc))) for cc in coarse)
R["C3_suite"] = {"margin_only_Q0_s4_identical": d_marg == r_marg, "cost_term_breaks_identity_sumabs": sum(abs(x - y) for x, y in zip(d_cost, r_cost)),
                 "time_varying_export_single_horizon_min_global_mismatch": mm_tv, "grid_without_representing_value_min_mismatch": mm_grid}
ok["C3_suite"] = d_marg == r_marg and R["C3_suite"]["cost_term_breaks_identity_sumabs"] > 0 and mm_tv > 0 and mm_grid > 0

# Theorem 4 numbers
mreq = lambda k, r: z(0.01) * math.sqrt((k * r + 1) / (r + 1))
R["T4c"] = {"case1": [mreq(2, 0.2), mreq(2, 5)], "case3": [mreq(2, 1), mreq(3, 1 / 3)],
            "case3_infl_excess": z(0.01) * (math.sqrt(4 / 2) - math.sqrt(3 / 2))}
ok["T4c"] = abs(R["T4c"]["case1"][1] - R["T4c"]["case1"][0] - 0.637) < 1e-3 and abs(R["T4c"]["case3_infl_excess"] - 0.441) < 1e-3


# Theorem 5 with RANDOM stratum membership; test scene conditioned to contain g; two-sided report
def scene(g):
    b = g.normal(0, math.sqrt(0.3)); has = g.random() < 0.6
    if not has: return None
    mm = int(g.integers(5, 60)); return b + g.normal(0, math.sqrt(0.7), mm) + 0.3 * g.standard_t(4, mm)


def crc(sc, d):
    n = len(sc)
    if n == 0 or 1 / (n + 1) > d: return float("inf")
    lo, hi = -10.0, float(max(u.max() for u in sc)) + 1e-9
    for _ in range(60):
        mid = (lo + hi) / 2; Rn = np.mean([np.mean(u > mid) for u in sc])
        lo, hi = (lo, mid) if n / (n + 1) * Rn + 1 / (n + 1) <= d else (mid, hi)
    return hi


Ls, ns = [], []
for rep in range(2000):
    cal = [x for x in (scene(rng) for _ in range(75)) if x is not None]; ns.append(len(cal)); ch = crc(cal, 0.05)
    te = None
    while te is None: te = scene(rng)
    Ls.append(float(np.mean(te > ch)))
Ls = np.array(Ls); R["T5_random_membership"] = {"E_L": float(Ls.mean()), "se": float(Ls.std() / math.sqrt(len(Ls))), "n_g_range": [int(min(ns)), int(max(ns))]}
ok["T5"] = Ls.mean() <= 0.05 + 2.5 * R["T5_random_membership"]["se"]

ok = {k: bool(v) for k, v in ok.items()}; R["pass_flags"] = ok; R["ALL_PASS"] = all(ok.values())
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "p01_verify_v03_results.json"), "w"), indent=1, default=float)
print(json.dumps({"pass_flags": ok, "ALL_PASS": R["ALL_PASS"], "T3_ccjoint": R["T3_ccjoint_Q0_s4_best_maxrelerr"],
                  "T3iii": [R["T3iii_rho_range_q_t2"], R["T3iii_rho_range_q_t3"]], "C3_suite": R["C3_suite"], "T5": R["T5_random_membership"]}, indent=1, default=float))
