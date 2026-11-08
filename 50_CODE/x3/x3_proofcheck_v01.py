#!/usr/bin/env python3
"""x3_proofcheck_v01 (Claude line, 7 Nov 2026): numeric checks for Appendix A (full proofs) of manuscript v06,
20_DESIGN/ms_v06_parts/A_proofs_v01.md. Every number quoted in Appendix A is recomputed here, exactly (closed form,
rational arithmetic) or by one-dimensional quadrature where possible, else by seeded Monte Carlo with a stated tolerance.

Sources checked against: 10_PROOFS/P01_THEORY_PROOFS_v02.md, P01_ADDENDUM_v03.md, P01_ADDENDUM_v04.md,
P02_METHOD_PROPOSITIONS_v03.md, 70_TESTS/R04_THIRD_PROOF_REVIEW_v01.md, 20_DESIGN/MANUSCRIPT_DRAFT_v05.md.
Code tied to the statements (imported or copied, never run as a program):
  - 50_CODE/m/m_lib_v04.py (fit_hier, deploy_covariance): IMPORTED as a library;
  - 50_CODE/c1_av2/c1_crc_exact_v01.py (crc_threshold_exact): its decision rule is COPIED below verbatim in logic
    (crc_exact), not imported, so nothing in 50_CODE/c1_av2 is executed.
Writes 20_DESIGN/ms_v06_parts/A_proofs_checks_v01.json. Run: <canmot310 python> -B x3_proofcheck_v01.py
"""
import hashlib
import json
import math
import os
import platform
import sys
import time
from fractions import Fraction

import numpy as np
import scipy
from scipy import integrate, stats
from scipy.special import ndtr  # standard normal cdf

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(W, "20_DESIGN", "ms_v06_parts", "A_proofs_checks_v01.json")
sys.path.insert(0, os.path.join(W, "50_CODE", "m"))
import m_lib_v04 as M  # noqa: E402  (library import; defines functions and constants only)

SEED = 20261107
rng = np.random.default_rng(SEED)
nd = stats.norm
Phi, Phibar = ndtr, (lambda x: ndtr(-np.asarray(x, float)))
z = lambda d: float(nd.isf(d))  # z_{1-d}

CHECKS = []


def add(cid, claim, computed, expected=None, tol=None, method="exact", ok=None, note=None):
    if ok is None:
        if expected is None:
            ok = True
        elif isinstance(expected, (list, tuple)):
            ok = all(abs(c - e) <= tol for c, e in zip(computed, expected))
        else:
            ok = abs(computed - expected) <= tol
    rec = {"id": cid, "claim": claim, "computed": computed, "expected_in_draft": expected, "tolerance": tol,
           "method": method, "pass": bool(ok)}
    if note:
        rec["note"] = note
    CHECKS.append(rec)
    print("%-28s %-5s %s" % (cid, "PASS" if ok else "FAIL", json.dumps(computed, default=float)[:110]), flush=True)


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


t0 = time.time()

# =====================================================================================================================
# Remark 1 (Gaussian half-space reduction)
m_, V_, a_, b_ = np.array([1.0, -2.0]), np.array([[2.0, 0.6], [0.6, 1.0]]), np.array([0.6, 0.8]), 1.0
Y = rng.multivariate_normal(m_, V_, 4_000_000)
mc = float(np.mean(Y @ a_ > b_))
an = float(Phibar((b_ - a_ @ m_) / math.sqrt(a_ @ V_ @ a_)))
add("R1_halfspace", "P(a'Y > b) = Phibar((b - a'm)/sqrt(a'Va)); MC vs formula (relative tol 1%)", {"mc": mc, "formula": an},
    method="MC 4e6", ok=abs(mc - an) / an < 0.01)

# =====================================================================================================================
# Proposition 1
# (i) event identity {a'X > b} = {U > tau} for I_k-measurable a, b, m, v (non-Gaussian truth)
v, mh, bb, c = 1.7, 0.4, 3.0, 2.326
X = mh + math.sqrt(v) * (rng.standard_t(5, 1_000_000) * 1.2)
tau = (bb - mh) / math.sqrt(v)
same = bool(np.array_equal(X > bb, (X - mh) / math.sqrt(v) > tau))
add("P1i_event_identity", "{a'X > b} and {U > tau} are the same event (indicator arrays identical)", same, method="exact (1e6 draws)", ok=same)

# (ii) fair-label counterexample, exact
z99 = z(0.01)
marg = float(Phibar(z99))  # U ~ N(0,1) marginally: P(U > z) = Phibar(z)
cond1 = float(2 * Phibar(z99))  # U | L=1 ~ |N(0,1)|: P(|Z| > z) = 2 Phibar(z)
cond2 = 0.0  # U | L=2 ~ -|N(0,1)| <= 0 < z
L = rng.integers(1, 3, 4_000_000)
A0 = np.abs(rng.standard_normal(L.size))
U = np.where(L == 1, A0, -A0)
mc_m, mc_1 = float(np.mean(U > z99)), float(np.mean(U[L == 1] > z99))
ks_p = float(stats.kstest(U[:200_000], "norm").pvalue)
add("P1ii_fair_label", "fair label: marginal 0.0100, label 1 0.0200, label 2 0 (exact); MC and KS(U ~ N(0,1))",
    {"marginal_exact": marg, "label1_exact": cond1, "label2_exact": cond2, "marginal_mc": mc_m, "label1_mc": mc_1, "ks_p_normal": ks_p},
    expected=None, method="exact + MC 4e6",
    ok=abs(marg - 0.01) < 1e-12 and abs(cond1 - 0.02) < 1e-12 and abs(mc_m - 0.01) < 4e-4 and abs(mc_1 - 0.02) < 8e-4 and ks_p > 1e-3)

# (ii) ratio-of-expectations bound with I_k-measurable weights, and the log-weighted (scene-weighted) rate.
# Two instances per log; instance 1 always selected; instance 2 selected iff U1 <= 0 (measurable at I_2, which contains U1);
# both exactly calibrated given their information (U_i | I_{k(i)} ~ N(0,1)).
d05, z95 = 0.05, z(0.05)
rec_exact = (d05 + 0.5 * d05) / 1.5
log_exact = d05 + 0.5 * d05 / 2  # P(U1 > z) [single-item logs] + P(U1 <= 0) * delta / 2
nn = 4_000_000
U1, U2 = rng.standard_normal(nn), rng.standard_normal(nn)
sel2 = U1 <= 0
rec_mc = float((np.sum(U1 > z95) + np.sum(sel2 & (U2 > z95))) / (nn + sel2.sum()))
log_mc = float(np.mean(np.where(sel2, ((U1 > z95).astype(float) + (U2 > z95)) / 2.0, (U1 > z95).astype(float))))
# reverse selection (instance 2 iff U1 > 0)
log_rev = 0.5 * (2 * d05 + d05) / 2
add("P1ii_logweighted_toy", "record-weighted = delta exactly; log-weighted = 1.25 delta = 0.0625 (selection U1<=0) and 0.75 delta (U1>0)",
    {"record_weighted_exact": rec_exact, "log_weighted_exact": log_exact, "log_weighted_reverse_exact": log_rev,
     "record_weighted_mc": rec_mc, "log_weighted_mc": log_mc},
    method="exact + MC 4e6",
    ok=abs(rec_exact - 0.05) < 1e-15 and abs(log_exact - 0.0625) < 1e-15 and abs(rec_mc - 0.05) < 4e-4 and abs(log_mc - 0.0625) < 4e-4,
    note="The draft's 0.0591 toy (R04 m1) is not specified in any source file and could not be recomputed; this exact toy replaces it.")

# =====================================================================================================================
# Proposition 2 (dilution)
pr, okp = {}, True
for kap, rh in ((2.0, 0.5), (4.0, 3.0), (0.5, 2.0)):
    q = 1.0
    ph = rh * q
    p = kap * ph
    cc = z(0.01)
    Uq = rng.normal(0, math.sqrt(p + q), 3_000_000) / math.sqrt(ph + q)
    f = float(Phibar(cc * math.sqrt((rh + 1) / (kap * rh + 1))))
    pr["k%g_r%g" % (kap, rh)] = {"mc": float(np.mean(Uq > cc)), "formula": f}
    okp &= abs(pr["k%g_r%g" % (kap, rh)]["mc"] - f) / f < 0.03
# derivative sign and limits
rr = lambda r, k: (r + 1) / (k * r + 1)
deriv_ok = all(np.all(np.diff(rr(np.linspace(0, 50, 2001), k)) * np.sign(1 - k) >= -1e-15) for k in (0.5, 2.0, 4.0))
lim_ok = abs(rr(0, 3.0) - 1) < 1e-15 and abs(rr(1e12, 3.0) - 1 / 3) < 1e-9
# "constant over tuples only when q = 0" is false: equal finite rho-hat gives a constant factor
s_ = 4.0
fac = [math.sqrt((s_ * r + 1) / (r + 1)) for r in (1.0, 1.0)]
add("P2_dilution", "P(U>c)=Phibar(c sqrt r), r=(rho+1)/(kappa rho+1); monotone in rho with sign(1-kappa); limits 1 and 1/kappa",
    {"mc_vs_formula": pr, "monotone_sign_ok": bool(deriv_ok), "limits_ok": bool(lim_ok)}, method="exact + MC 3e6",
    ok=bool(okp and deriv_ok and lim_ok))
add("P2_global_dose_constancy", "dose s=4 with q>0 but equal rho-hat=1 on two tuples gives the same factor sqrt((s rho+1)/(rho+1)) "
    "= 1.5811 on both: constancy holds iff rho-hat is constant, not only when q = 0", {"factors": fac}, method="exact",
    ok=abs(fac[0] - fac[1]) < 1e-15 and abs(fac[0] - math.sqrt(2.5)) < 1e-15,
    note="Correction to the draft's 'constant over tuples only when q_j = 0'.")

# =====================================================================================================================
# Proposition 3 (A2): Gaussian posterior + estimate-only separating filter and toward-ego orientation -> exactly delta.
def sep_axis_toy(n, posterior=True, sa=0.10):
    mhat = np.stack([rng.uniform(-25, 25, n), rng.uniform(-12, 12, n)], 1)
    psi = rng.uniform(0, 2 * math.pi, n)
    s1, s2, th = rng.uniform(0.2, 2.0, n), rng.uniform(0.2, 2.0, n), rng.uniform(0, math.pi, n)
    R = np.stack([np.stack([np.cos(th), -np.sin(th)], -1), np.stack([np.sin(th), np.cos(th)], -1)], -2)
    Lc = R * np.stack([s1, s2], -1)[:, None, :]  # R diag(s): Sigma = R diag(s^2) R'
    Sig = Lc @ np.transpose(Lc, (0, 2, 1))
    eps = np.einsum("nij,nj->ni", Lc, rng.standard_normal((n, 2)))
    if posterior:
        X = mhat + eps                       # X | I ~ N(mhat, Sigma)
    else:
        X = mhat.copy()                      # fixed truth: the estimate is the truth plus error
        mhat = X + eps
    Xgt = X + sa * rng.standard_normal((n, 2))
    ce, ue, ve = np.zeros(2), np.array([1.0, 0.0]), np.array([0.0, 1.0])
    lo, wi = 4.5, 1.9
    exc, cnt = 0, 0
    for a, half in ((np.stack([np.cos(psi), np.sin(psi)], 1), lo / 2), (np.stack([-np.sin(psi), np.cos(psi)], 1), wi / 2)):
        off = np.einsum("ni,ni->n", a, ce - mhat)
        hego = (4.1 / 2 + 0.5) * np.abs(a @ ue) + (1.8 / 2 + 0.5) * np.abs(a @ ve)
        keep = np.abs(off) > half + hego
        ast = a * np.sign(off)[:, None]
        vv = np.einsum("ni,nij,nj->n", ast, Sig, ast) + sa ** 2
        Uu = np.einsum("ni,ni->n", ast, Xgt - mhat) / np.sqrt(vv)
        exc += int(np.sum(keep & (Uu > z95)))
        cnt += int(np.sum(keep))
    return exc / cnt, cnt


e_post, n_post = sep_axis_toy(2_000_000, True)
e_ft, n_ft = sep_axis_toy(2_000_000, False)
se_post = math.sqrt(0.05 * 0.95 / n_post)
add("P3_A2_posterior_exact", "record-weighted exceedance over an estimate-only selection = Phibar(z) = 0.05 under a Gaussian posterior "
    "with known sigma_a (draft: Monte Carlo 0.0503); fixed-truth contrast reported",
    {"posterior_mc": e_post, "items": n_post, "mc_se": se_post, "fixed_truth_mc": e_ft}, expected=0.05, tol=4 * se_post,
    method="MC 2e6 records", ok=abs(e_post - 0.05) <= 4 * se_post)
# (A3) annotation noise: |e + eta|^2/(1+s^2) ~ chi2_2 for any angle law (here theta0 ~ N(0, 0.3^2) + pi B)
n = 1_000_000
Rr = np.sqrt(rng.chisquare(2, n))
th = rng.normal(0, 0.3, n) + math.pi * rng.integers(0, 2, n)
e = np.stack([Rr * np.cos(th), Rr * np.sin(th)], 1)
sig = 0.5
Nq = np.sum((e + sig * rng.standard_normal((n, 2))) ** 2, 1) / (1 + sig ** 2)
ksA3 = float(stats.kstest(Nq[:200_000], stats.chi2(2).cdf).pvalue)
add("P3_A3_annotation_noise", "|e+eta|^2/(1+sigma^2) ~ chi2_2 for a non-uniform angle law (KS p-value)", {"ks_p": ksA3,
    "p_exceed_chi2_2_95": float(np.mean(Nq > stats.chi2.ppf(0.95, 2)))}, method="MC 1e6", ok=ksA3 > 1e-3)

# =====================================================================================================================
# Proposition 4 (Cauchy-Schwarz) and the 1.30 margin ratio
worst = 0.0
for _ in range(5000):
    A = rng.normal(size=(4, 4))
    Vh = A @ A.T + 0.05 * np.eye(4)
    ee = rng.normal(size=4)
    full = ee @ np.linalg.solve(Vh, ee)
    for _ in range(4):
        aa = rng.normal(size=4)
        worst = max(worst, (aa @ ee) ** 2 / (aa @ Vh @ aa) / full)
    aeq = np.linalg.solve(Vh, ee)
    eq_gap = abs((aeq @ ee) ** 2 / (aeq @ Vh @ aeq) - full) / full
cN = math.sqrt(stats.chi2.ppf(0.99, 2))
ratio = cN / z(0.01)
add("P4_cauchy_schwarz", "(a'e)^2/(a'Va) <= e'V^-1 e (max ratio over 20000 random cases), equality at a = V^-1 e",
    {"max_ratio": worst, "equality_rel_gap": float(eq_gap)}, method="exact algebra, random spot checks", ok=worst <= 1 + 1e-12 and eq_gap < 1e-10)
add("P4_margin_ratio", "sqrt(chi2_{2,0.99}) / z_{0.99} = sqrt(-2 ln 0.01)/z_{0.99} (draft 1.30)",
    {"c_N": cN, "c_N_closed_form": math.sqrt(-2 * math.log(0.01)), "z_0.99": z(0.01), "ratio": ratio,
     "ratio_delta_0.05": math.sqrt(stats.chi2.ppf(0.95, 2)) / z(0.05)}, expected=1.30, tol=0.005, method="exact",
    ok=abs(ratio - 1.30) < 0.005 and abs(cN - math.sqrt(-2 * math.log(0.01))) < 1e-12)

# Remark 3 (Schur) and the 9-D radius
cor2 = 0.0
for _ in range(5000):
    A = rng.normal(size=(6, 6))
    Vh = A @ A.T + 0.05 * np.eye(6)
    ee = rng.normal(size=6)
    cor2 = max(cor2, (ee[:2] @ np.linalg.solve(Vh[:2, :2], ee[:2])) / (ee @ np.linalg.solve(Vh, ee)))
rad = math.sqrt(stats.chi2.ppf(0.95, 9))
add("R3_schur_radius", "e1'V11^-1 e1 <= e'V^-1 e (max ratio); sqrt(chi2_{9,0.95}) (draft 4.113)", {"max_ratio": cor2, "radius": rad},
    expected=4.113, tol=5e-4, method="exact", ok=cor2 <= 1 + 1e-12 and abs(rad - 4.113) < 5e-4)

# =====================================================================================================================
# Theorem 1
# (a)
EN_a = 1 / 2 + 1 / (2 / 3)
risk_a = float(Phibar(z(0.01) * math.sqrt(2 / 3)))
# ANEES acceptance probability in the large-sample limit: N = e1^2/2 + 3 e2^2/2 has mean 2, variance 2*(1/4+9/4) = 5 (chi2_2: 4)
acc_lim = float(2 * Phi(1.959963984540054 * 2 / math.sqrt(5)) - 1)
add("T1a", "E[N] = 2 exactly; risk along axis 2 = Phibar(z_0.99 sqrt(2/3)) (draft 0.0288); ANEES 95% test acceptance -> 0.920",
    {"E_N": EN_a, "risk_axis2": risk_a, "var_N": 2 * (0.25 + 2.25), "anees_accept_limit": acc_lim},
    expected=0.0288, tol=5e-5, method="exact", ok=abs(EN_a - 2) < 1e-15 and abs(risk_a - 0.0288) < 5e-5)

# (b): risk(phi) = E[h(theta - phi)], h(psi) = exp(-z^2/(2 cos^2 psi)) 1{cos psi > 0}; theta = theta0 + pi B
zz = z(0.01)


def risk_b(s, phi=0.0):
    # 0.5 E[exp(-z^2/(2 cos^2(theta0 - phi)))], theta0 ~ N(0, s^2); integrate over theta0 on +-12 s around 0 (mass outside < 1e-30)
    f = lambda t: 0.5 * math.exp(-zz * zz / (2 * max(math.cos(t - phi) ** 2, 1e-300))) * nd.pdf(t, 0, s)
    pts = sorted({phi + k * math.pi / 2 for k in range(-40, 41) if abs(phi + k * math.pi / 2) < 12 * s})
    val, err = integrate.quad(f, -12 * s, 12 * s, points=pts or None, limit=800, epsabs=1e-14, epsrel=1e-12)
    return val


rb = {s: risk_b(s) for s in (0.3, 0.6, 1.0)}
lim0 = 0.5 * math.exp(-zz * zz / 2)
# direction-averaged risk equals delta for any angle law (here s = 0.3): (1/2pi) int risk(phi) dphi
avg = integrate.quad(lambda ph: risk_b(0.3, ph), 0, 2 * math.pi, limit=400, epsabs=1e-12)[0] / (2 * math.pi)
# MC: N = R^2 ~ chi2_2 exactly, p_v95 = 0.05; risk along a0
mcb = {}
for s in (0.3, 0.6, 1.0):
    n = 3_000_000
    Rr = np.sqrt(rng.chisquare(2, n))
    th = rng.normal(0, s, n) + math.pi * rng.integers(0, 2, n)
    ee = np.stack([Rr * np.cos(th), Rr * np.sin(th)], 1)
    NN = (ee ** 2).sum(1)
    mcb["s%g" % s] = {"risk_a0_mc": float(np.mean(ee[:, 0] > zz)), "p_v95_mc": float(np.mean(NN > stats.chi2.ppf(0.95, 2))),
                      "var_e1_mc": float(ee[:, 0].var()), "var_e1_exact": 1 + math.exp(-2 * s * s),
                      "ks_p_chi2_2": float(stats.kstest(NN[:200_000], stats.chi2(2).cdf).pvalue)}
okb = (abs(rb[0.3] - 0.0268) < 5e-5 and abs(rb[0.6] - 0.0181) < 5e-5 and abs(rb[1.0] - 0.0121) < 5e-5 and abs(avg - 0.01) < 1e-8
       and all(abs(v["risk_a0_mc"] - rb[float(k[1:])]) < 5e-4 and abs(v["p_v95_mc"] - 0.05) < 8e-4 for k, v in mcb.items()))
add("T1b", "N = R^2 ~ chi2_2 for any angle law (p_v95 = 0.05 exactly); risk along a0 = 0.5 E[exp(-z^2/(2cos^2 theta0))] "
    "(draft 0.0268, 0.0181, 0.0121); direction-averaged risk = delta exactly; s->0 limit 0.5 exp(-z^2/2)",
    {"risk_quadrature": {str(k): v for k, v in rb.items()}, "limit_s0": lim0, "direction_average_s0.3": avg,
     "p_v95_exact": math.exp(-stats.chi2.ppf(0.95, 2) / 2), "mc": mcb}, expected=[0.0268, 0.0181, 0.0121], tol=5e-5,
    method="1-D quadrature + MC 3e6", ok=bool(okb))

# (c)
EN_c = 1 + 4
risk_c = float(Phibar(z(0.01) * math.sqrt(2.5)))
add("T1c", "E[N] = 5; binding direction exactly calibrated (risk 0.01); after x2.5 the risk is Phibar(z sqrt 2.5) (draft 0.00012)",
    {"E_N": EN_c, "risk_binding_before": float(Phibar(z(0.01))), "risk_after_x2.5": risk_c, "risk_axis2_before": float(Phibar(z(0.01) / 2))},
    expected=0.00012, tol=5e-6, method="exact", ok=abs(risk_c - 0.00012) < 5e-6)

# (d) closed form for t3: P(T > sqrt3 z) = 1/2 - (arctan z + z/(1+z^2))/pi
td = {}
for d in (0.05, 0.01, 0.001):
    zd = z(d)
    cf = 0.5 - (math.atan(zd) + zd / (1 + zd * zd)) / math.pi
    td[str(d)] = {"closed_form": cf, "scipy_t_sf": float(stats.t.sf(math.sqrt(3) * zd, 3))}
okd = (abs(td["0.01"]["closed_form"] - 0.0137) < 5e-5 and abs(td["0.001"]["closed_form"] - 0.0064) < 5e-5
       and abs(td["0.05"]["closed_form"] - 0.0326) < 5e-5 and all(abs(v["closed_form"] - v["scipy_t_sf"]) < 1e-12 for v in td.values()))
add("T1d", "e = (T1,T2)/sqrt3, T ~ t3: unit variance (Var t3 = 3), E[N] = 2; risk along e1 (draft 0.0137 at 0.01, 0.0064 at 0.001, 0.0326 at 0.05)",
    {"var_t3": float(stats.t(3).var()), "risk": td}, expected=[0.0326, 0.0137, 0.0064], tol=5e-5, method="exact closed form", ok=bool(okd))

# =====================================================================================================================
# Proposition 5 and Theorem 2
mreq = lambda k, r, d=0.01: z(d) * math.sqrt((k * r + 1) / (r + 1))
c1v = [mreq(2, 0.2), mreq(2, 5)]
c3v = [mreq(2, 1), mreq(3, 1 / 3)]
infl_excess = z(0.01) * (math.sqrt(4 / 2) - math.sqrt(3 / 2))  # s = 3, tuple (2, 1): p = q, v = 2q
add("T2_knobs", "case 1: inflation exact (s=2), multiplier costs m2-m1 (draft 0.637); case 2: multiplier exact at 2.849, inflation (s=3) "
    "costs z(sqrt2 - sqrt1.5) (draft 0.441)", {"case1_m": c1v, "case1_excess": c1v[1] - c1v[0], "case2_m": c3v,
                                                "case2_infl_excess": infl_excess},
    expected=[0.637, 2.849, 0.441], tol=5e-4, method="exact",
    ok=abs(c1v[1] - c1v[0] - 0.637) < 5e-4 and abs(c3v[0] - c3v[1]) < 1e-12 and abs(c3v[0] - 2.849) < 5e-4 and abs(infl_excess - 0.441) < 5e-4)
# Prop 5(c): aggregate knob illustration, equal weights on case 1's tuples
from scipy.optimize import brentq  # noqa: E402

rk = lambda c, k, r: float(Phibar(c * math.sqrt((r + 1) / (k * r + 1))))
Fagg = lambda c: 0.5 * rk(c, 2, 0.2) + 0.5 * rk(c, 2, 5) - 0.01
cagg = brentq(Fagg, 0.1, 10)
add("P5c_aggregate", "weighted-average risk = delta at c_agg gives max risk > delta when m_j differ (equal weights, case-1 tuples)",
    {"c_agg": cagg, "risks": [rk(cagg, 2, 0.2), rk(cagg, 2, 5)]}, method="exact (root finding)",
    ok=max(rk(cagg, 2, 0.2), rk(cagg, 2, 5)) > 0.01 and abs(0.5 * rk(cagg, 2, 0.2) + 0.5 * rk(cagg, 2, 5) - 0.01) < 1e-12)

# =====================================================================================================================
# Remark 5 (sample floor), exact
fl = {}
for d in (Fraction(1, 20), Fraction(1, 100)):
    nmin = math.ceil(1 / d - 1)
    nprac = int(2 / d - 1)
    alw = ((nprac + 1) * d - 1) / nprac
    fl[str(float(d))] = {"n_min": nmin, "n_practical": nprac, "allowance": float(alw), "delta_over_2_minus_delta": float(d / (2 - d)),
                         "allowance_at_floor": float(((nmin + 1) * d - 1) / nmin)}
add("R5_floor", "n_min = 19 / 99; practical n = 39 / 199 with allowance delta/(2-delta) = 0.025641 / 0.0050251; allowance 0 at the floor",
    fl, expected=[19, 39, 99, 199], tol=0, method="exact rational",
    ok=fl["0.05"]["n_min"] == 19 and fl["0.05"]["n_practical"] == 39 and fl["0.01"]["n_min"] == 99 and fl["0.01"]["n_practical"] == 199
    and abs(fl["0.05"]["allowance"] - 0.05 / 1.95) < 1e-15 and fl["0.05"]["allowance_at_floor"] == 0.0)


# =====================================================================================================================
# Proposition 6: exact CRC rule (copied in logic from 50_CODE/c1_av2/c1_crc_exact_v01.crc_threshold_exact, not imported)
def crc_exact(U, s, delta=0.05):
    U = np.asarray(U, float)
    units, si = np.unique(np.asarray(s), return_inverse=True)
    n = len(units)
    d_exact = Fraction(repr(float(delta)))
    if n == 0 or Fraction(1, n + 1) > d_exact:
        return None
    tot = np.bincount(si, minlength=n).astype(np.int64)
    order = np.sort(np.unique(U))

    def ok(c):
        x = np.bincount(si, weights=(U > c).astype(float), minlength=n).astype(np.int64)
        ssum = sum((Fraction(int(x[tot == t].sum()), int(t)) for t in np.unique(tot)), Fraction(0))
        return ssum <= d_exact * (n + 1) - 1
    if not ok(order[-1]):
        return float(order[-1]) + 1e-9
    lo, hi = 0, len(order) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(order[mid]):
            hi = mid
        else:
            lo = mid + 1
    return float(order[lo])


def bound_exact(U, s, c, delta=0.05):
    units, si = np.unique(np.asarray(s), return_inverse=True)
    n = len(units)
    tot = np.bincount(si, minlength=n).astype(np.int64)
    x = np.bincount(si, weights=(np.asarray(U) > c).astype(float), minlength=n).astype(np.int64)
    return (sum(Fraction(int(xi), int(ti)) for xi, ti in zip(x, tot)) + 1) / (n + 1)


def crc_fast(U, unit, n_units, delta=0.05):
    """The same rule in floating point for continuous scores (no ties): smallest observed U with (S(U)+1)/(n+1) <= delta."""
    thr = delta * (n_units + 1) - 1
    if thr < -1e-12:
        return np.inf
    cnt = np.bincount(unit, minlength=n_units)
    w = 1.0 / cnt[unit]
    o = np.argsort(U, kind="stable")
    Us, cs = U[o], np.cumsum(w[o])
    S = cs[-1] - cs
    S[-1] = 0.0
    return float(Us[int(np.argmax(S <= thr + 1e-12))])


# (P6a) the implementation returns the infimum of the defining set, an observed score; the set is [c_hat, inf)
bad, n_tested, floor_ok = 0, 0, True
d_ex = Fraction(1, 20)
for rep in range(300):
    nlog = int(rng.integers(19, 70))
    cnts = rng.integers(1, 12, nlog)
    s_ = np.repeat(np.arange(nlog), cnts)
    U_ = np.round(rng.normal(0, 1, s_.size) + np.repeat(rng.normal(0, 0.5, nlog), cnts), 2)  # rounded: ties occur
    ch = crc_exact(U_, s_)
    uniq = np.sort(np.unique(U_))
    k = int(np.searchsorted(uniq, ch))
    below = uniq[k - 1] + (uniq[k] - uniq[k - 1]) / 2 if k > 0 else uniq[0] - 1.0
    ok1 = bound_exact(U_, s_, ch) <= d_ex and bound_exact(U_, s_, below) > d_ex and bound_exact(U_, s_, uniq[0] - 1.0) == 1
    ok2 = all(bound_exact(U_, s_, c) <= d_ex for c in uniq[k:][:5]) and all(bound_exact(U_, s_, c) > d_ex for c in uniq[max(0, k - 5):k])
    bad += int(not (ok1 and ok2))
    n_tested += 1
    if nlog == 19:
        floor_ok &= ch == uniq[-1]
# explicit floor test: n = 19 -> c_hat is the largest calibration score
s19 = np.repeat(np.arange(19), 7)
U19 = rng.normal(size=s19.size)
floor_ok &= crc_exact(U19, s19) == U19.max()
# fast float rule == exact rule on continuous data
fast_mis = 0
for rep in range(200):
    nlog = int(rng.integers(19, 120))
    cnts = rng.integers(1, 30, nlog)
    s_ = np.repeat(np.arange(nlog), cnts)
    U_ = rng.normal(size=s_.size) + np.repeat(rng.normal(0, 0.5, nlog), cnts)
    fast_mis += int(crc_exact(U_, s_) != crc_fast(U_, s_, nlog))
add("P6a_threshold_is_infimum", "the code's rule (smallest observed U passing the exact predicate, bisection) equals "
    "inf{c : (sum_i L_i(c) + 1)/(n+1) <= delta}; bound = 1 below all scores; at n = 19 c_hat = max score; float rule = exact rule",
    {"datasets": n_tested, "violations": bad, "floor_max_ok": bool(floor_ok), "fast_vs_exact_mismatches": fast_mis},
    method="exact rational arithmetic", ok=bad == 0 and floor_ok and fast_mis == 0)

# (P6f) fit_hier (m_lib_v04, imported) assigns own thresholds iff >= 19 units and fits coarse cells on all their items
nlog = 120
logs_items = []
l0_pool = [0, 1, 2, 3, 4, 5, 6, 7]  # L0 strata of L1 cells 0 and 1 (car, <20 m, long / lat); probabilities make some rare
probs = np.array([0.5, 0.3, 0.05, 0.04, 0.4, 0.06, 0.03, 0.02])
Uall, sall, l0all = [], [], []
for lg in range(nlog):
    for l0, p in zip(l0_pool, probs):
        if rng.random() < p:
            k = int(rng.integers(1, 6))
            Uall.append(rng.normal(0.3 * (l0 % 4), 1, k))
            sall += [lg] * k
            l0all += [l0] * k
Uall, sall, l0all = np.concatenate(Uall), np.array(sall), np.array(l0all)
par = np.array([M.parents(int(x)) for x in l0all])
lv = [l0all, par[:, 0], par[:, 1], par[:, 2]]
thr, src = M.fit_hier(Uall, sall, lv, 0, 19, stat=crc_exact)
fh_ok = True
fh_rows = []
for l0 in l0_pool:
    keys = (l0,) + M.parents(l0)
    nunits = [len(np.unique(sall[lv[lev] == keys[lev]])) for lev in range(4)]
    exp_lev = next(lev for lev in range(4) if nunits[lev] >= 19)
    exp_thr = crc_exact(Uall[lv[exp_lev] == keys[exp_lev]], sall[lv[exp_lev] == keys[exp_lev]])
    fh_ok &= int(src[l0]) == exp_lev and thr[l0] == exp_thr
    fh_rows.append({"l0": l0, "units_by_level": nunits, "src": int(src[l0]), "expected_level": exp_lev})
add("P7_code_fit_hier", "m_lib_v04.fit_hier: a stratum keeps its own threshold iff its calibration-unit count >= 19; otherwise it takes "
    "the CRC threshold of the first coarser cell with >= 19 units, fitted on ALL of that cell's items", {"rows": fh_rows},
    method="exact, synthetic data through the imported library", ok=bool(fh_ok))


# (P6b-d) Monte Carlo validity with the log as the unit and within-log dependence
def draw_logs(m, p, sb2=0.3, se2=0.7, nmax=40, tlaw=False):
    has = rng.random(m) < p
    k = np.where(has, rng.integers(1, nmax + 1, m), 0)
    if tlaw:
        b = rng.standard_t(4, m) * math.sqrt(sb2 / 2.0)  # Var t4 = 2
    else:
        b = rng.normal(0, math.sqrt(sb2), m)
    unit = np.repeat(np.arange(m), k)
    U_ = b[unit] + rng.normal(0, math.sqrt(se2), unit.size)
    return has, unit, U_


cgrid = np.linspace(-1, 8, 9001)
Rt = np.array([integrate.quad(lambda bb_: float(Phibar((c - bb_) / math.sqrt(0.7))) * stats.t.pdf(bb_ / math.sqrt(0.15), 4) / math.sqrt(0.15),
                              -np.inf, np.inf, epsabs=1e-13)[0] for c in cgrid[::30]])
R_t = lambda c: float(np.interp(c, cgrid[::30], Rt))
R_g = lambda c: float(Phibar(c))  # Gaussian law: b + e ~ N(0, 1), and E[share | b, k] = Phibar((c-b)/sqrt(.7)) => R(c) = Phibar(c)


def p6_mc(reps, m, p, tlaw=False, cond_floor=False):
    out, ns = [], []
    for _ in range(reps):
        has, unit, U_ = draw_logs(m, p, tlaw=tlaw)
        n = int(has.sum())
        if n < 19:
            ns.append(n)
            out.append(np.nan)
            continue
        uu = np.unique(unit, return_inverse=True)[1]
        ch = crc_fast(U_, uu, n)
        out.append(R_t(ch) if tlaw else R_g(ch))
        ns.append(n)
    return np.array(out), np.array(ns)


r1, n1 = p6_mc(4000, 300, 0.6)
r1t, n1t = p6_mc(2000, 300, 0.6, tlaw=True)
r2, n2 = p6_mc(20000, 300, 0.065)
v2 = ~np.isnan(r2)
bins = {}
for lo_, hi_ in ((19, 19), (20, 20), (21, 22), (23, 26), (27, 60)):
    sel = v2 & (n2 >= lo_) & (n2 <= hi_)
    if sel.any():
        bins["%d-%d" % (lo_, hi_)] = {"reps": int(sel.sum()), "E_risk": float(r2[sel].mean())}
se1 = float(r1.std() / math.sqrt(len(r1)))
se1t = float(r1t.std() / math.sqrt(len(r1t)))
add("P6b_validity_log_unit", "i.i.d. logs with a log random effect (within-log dependence), 300 calibration logs, membership 0.6: "
    "E[L_g(test; c_hat) | N] <= delta; share of calibration draws whose conditional risk exceeds delta (tightness)",
    {"gaussian": {"E_risk": float(r1.mean()), "se": se1, "P_cond_risk_gt_delta": float(np.mean(r1 > 0.05)), "N_range": [int(n1.min()), int(n1.max())]},
     "t4_log_effect": {"E_risk": float(r1t.mean()), "se": se1t, "P_cond_risk_gt_delta": float(np.mean(r1t > 0.05))}},
    method="MC (4000 and 2000 calibration draws; exact conditional risk given c_hat)",
    ok=r1.mean() <= 0.05 + 3 * se1 and r1t.mean() <= 0.05 + 3 * se1t)
add("P6c_validity_near_floor", "membership 0.065 (N ~ Bin(300, 0.065)): E[risk | N >= 19] <= delta, also per N bin",
    {"P_N_ge_19": float(v2.mean()), "E_risk_given_N_ge_19": float(r2[v2].mean()), "by_N": bins},
    method="MC 20000 draws", ok=float(r2[v2].mean()) <= 0.05 and all(b_["E_risk"] <= 0.05 for b_ in bins.values()))

# (P6d) cross-fitting: 375 i.i.d. logs, 5 fixed folds of 75; fold f calibrated on the other 300; log-weighted cross-fitted estimate
fold = np.repeat(np.arange(5), 75)
cf = []
for _ in range(2000):
    has, unit, U_ = draw_logs(375, 0.6)
    tot_ = 0.0
    nt = 0
    okf = True
    for f in range(5):
        cal = has & (fold != f)
        n = int(cal.sum())
        if n < 19:
            okf = False
            break
        m_ = np.isin(unit, np.where(cal)[0])
        uu = np.unique(unit[m_], return_inverse=True)[1]
        ch = crc_fast(U_[m_], uu, n)
        k_t = int((has & (fold == f)).sum())
        tot_ += k_t * R_g(ch)
        nt += k_t
    if okf and nt > 0:
        cf.append(tot_ / nt)
cf = np.array(cf)
secf = float(cf.std() / math.sqrt(len(cf)))
add("P6d_crossfit", "cross-fitted log-weighted estimate over 5 fixed folds of 75 (calibration 300 logs per fold): E[E_hat_g | A] <= delta",
    {"E": float(cf.mean()), "se": secf, "reps": len(cf)}, method="MC 2000 draws (exact conditional risk)", ok=cf.mean() <= 0.05 + 3 * secf)

# (P6e) scene unit under within-log dependence: exact anti-conservative example and log-unit contrast
def scene_unit_exact(nlogs, K, delta=Fraction(1, 20)):
    jmax = math.floor((delta * (nlogs * K + 1) - 1) / K)
    jlog = math.floor(delta * (nlogs + 1) - 1)
    return Fraction(jmax + 1, nlogs + 1), Fraction(jlog + 1, nlogs + 1)


sc30, lg30 = scene_unit_exact(30, 5)
sc_tab = {str(n_): [float(x) for x in scene_unit_exact(n_, 5)] for n_ in (20, 30, 39, 50, 59, 100)}
mcs = []
for _ in range(20000):
    V = rng.normal(size=30)
    Us = np.repeat(V, 5)
    ch = crc_exact(Us, np.arange(150))  # 150 scene units of one item each; 5 exact copies per log (exact ties)
    mcs.append(float(Phibar(ch)))
add("P6e_scene_unit_counterexample", "30 logs x 5 identical scenes, scene-unit CRC, test scene from a new log: risk (j+1)/(n'+1) = 2/31 = 0.0645 > delta; "
    "log-unit CRC on the same data 1/31", {"scene_unit_exact": float(sc30), "log_unit_exact": float(lg30), "scene_unit_mc": float(np.mean(mcs)),
                                           "table_scene_vs_log_by_nlogs_K5": sc_tab},
    method="exact rank argument + MC 20000", ok=sc30 == Fraction(2, 31) and lg30 == Fraction(1, 31) and abs(np.mean(mcs) - 2 / 31) < 0.003)

# =====================================================================================================================
# Proposition 7 (ii): conditioning on the fallback event can break the coarse-cell bound
mu, pg, m7 = 3.0, 0.06, 300
nh_vals, ng_vals = np.arange(1, 4), np.arange(5, 11)


def RC(c):
    """Exact conditional risk of a fresh log's C-share at threshold c (C = g u h; h items N(0,1), g items N(mu,1);
    n_h ~ U{1..3} on every log, n_g ~ U{5..10} on a g-log)."""
    nh, ng = np.meshgrid(nh_vals, ng_vals)
    share_g = np.mean((nh * Phibar(c) + ng * Phibar(c - mu)) / (nh + ng))
    return (1 - pg) * float(Phibar(c)) + pg * float(share_g)


rows7 = []
for _ in range(20000):
    hasg = rng.random(m7) < pg
    nh = rng.integers(1, 4, m7)
    ng = np.where(hasg, rng.integers(5, 11, m7), 0)
    unit = np.concatenate([np.repeat(np.arange(m7), nh), np.repeat(np.arange(m7), ng)])
    Uc = np.concatenate([rng.normal(size=nh.sum()), rng.normal(mu, 1, ng.sum())])
    isg = np.concatenate([np.zeros(nh.sum(), bool), np.ones(ng.sum(), bool)])
    cC = crc_fast(Uc, unit, m7)
    Ng = int(hasg.sum())
    if Ng >= 19:
        ug = np.unique(unit[isg], return_inverse=True)[1]
        cg = crc_fast(Uc[isg], ug, Ng)
        rg_own = float(Phibar(cg - mu))
    else:
        rg_own = np.nan
    rows7.append((Ng, RC(cC), float(Phibar(cC - mu)), rg_own))
rows7 = np.array(rows7)
fb = rows7[:, 0] < 19
res7 = {"P_fallback": float(fb.mean()),
        "E_LC_unconditional": float(rows7[:, 1].mean()), "se_unconditional": float(rows7[:, 1].std() / math.sqrt(len(rows7))),
        "E_LC_given_fallback": float(rows7[fb, 1].mean()), "se_given_fallback": float(rows7[fb, 1].std() / math.sqrt(fb.sum())),
        "E_LC_given_own": float(rows7[~fb, 1].mean()),
        "E_LC_given_N_g_le_14": float(rows7[rows7[:, 0] <= 14, 1].mean()),
        "E_Lg_at_cC_given_fallback_and_test_has_g": float(rows7[fb, 2].mean()),
        "E_Lg_at_own_cg_given_own": float(np.nanmean(rows7[~fb, 3]))}
add("P7_fallback_conditioning", "C = g u h, g rare (p = 0.06; 5-10 g items shifted by 3, 1-3 h items): E[L_C(c_C)] <= delta unconditionally, but "
    "E[L_C(c_C) | N_g < 19] > delta and the fallback stratum's own loss at c_C is far above delta; own threshold valid when N_g >= 19",
    res7, method="MC 20000 calibration draws (exact conditional risk)",
    ok=res7["E_LC_unconditional"] <= 0.05 + 3 * res7["se_unconditional"] and res7["E_LC_given_fallback"] > 0.05 + 3 * res7["se_given_fallback"]
    and res7["E_Lg_at_cC_given_fallback_and_test_has_g"] > 0.2 and res7["E_Lg_at_own_cg_given_own"] <= 0.05)

# =====================================================================================================================
# Proposition 8 (deployable covariance) through the imported m_lib_v04.deploy_covariance
# (a) exact rational arithmetic: unit axes from the rational parametrisation (1-t^2, 2t)/(1+t^2), rational alphas and Sigma
def fr(x):
    return Fraction(x).limit_denominator(10 ** 6)


exact8 = True
for _ in range(2000):
    t = fr(rng.uniform(-3, 3))
    cth, sth = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
    al_, at_ = (cth, sth), (-sth, cth)
    alpl, alpt = fr(rng.uniform(1e-3, 6)), fr(rng.uniform(1e-3, 6))
    g11, g12, g22 = fr(rng.normal()), fr(rng.normal()), fr(rng.normal())
    S_ = [[g11 * g11 + g12 * g12, g12 * g22], [g12 * g22, g22 * g22]]  # G G' with G = [[g11, g12], [0, g22]]
    sa2 = Fraction(1, 100)
    Mx = [[S_[0][0] + sa2, S_[0][1]], [S_[1][0], S_[1][1] + sa2]]
    A_ = [[alpl * al_[i] * al_[j] + alpt * at_[i] * at_[j] for j in range(2)] for i in range(2)]
    AM = [[sum(A_[i][k] * Mx[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    St_ = [[sum(AM[i][k] * A_[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    q = lambda Q, v_: sum(v_[i] * Q[i][j] * v_[j] for i in range(2) for j in range(2))
    exact8 &= St_[0][1] == St_[1][0]
    exact8 &= q(St_, al_) == alpl ** 2 * (q(S_, al_) + sa2) and q(St_, at_) == alpt ** 2 * (q(S_, at_) + sa2)
    det = St_[0][0] * St_[1][1] - St_[0][1] * St_[1][0]
    exact8 &= St_[0][0] > 0 and det > 0  # Sylvester: positive definite
# (b) the imported library function, floating point, error relative to the matrix scale (cancellation is O(eps * |S~|))
worst8, minev = 0.0, np.inf
for _ in range(20000):
    A = rng.normal(size=(2, 2))
    S = A @ A.T * rng.uniform(0.01, 5) + 1e-6 * np.eye(2)
    yaw = rng.uniform(-math.pi, math.pi)
    cl, ct = rng.uniform(-0.5, 8), rng.uniform(-0.5, 8)
    St = M.deploy_covariance(S, yaw, cl, ct)
    scale = float(np.abs(St).max())
    al, at = np.array([math.cos(yaw), math.sin(yaw)]), np.array([-math.sin(yaw), math.cos(yaw)])
    for a, c in ((al, cl), (at, ct)):
        target = (max(c, 1e-3) / M.Z) ** 2 * (a @ S @ a + M.SIGMA_A ** 2)
        worst8 = max(worst8, abs(a @ St @ a - target) / scale, abs((-a) @ St @ (-a) - a @ St @ a) / scale)
    minev = min(minev, float(np.linalg.eigvalsh((St + St.T) / 2).min()))
    worst8 = max(worst8, float(np.abs(St - St.T).max()) / scale)
add("P8_congruence", "S~ = A M A: symmetric, positive definite, a'S~a = alpha^2 (a'S a + sigma_a^2) on both axes (exact rational, 2000 cases); "
    "m_lib_v04.deploy_covariance reproduces z sqrt(a'S~a) = max(c, 1e-3) sd to floating-point accuracy",
    {"exact_rational_all_ok": bool(exact8), "library_max_err_rel_to_matrix_scale": worst8, "library_min_eigenvalue": minev,
     "Z": M.Z, "sigma_a": M.SIGMA_A}, method="exact rational + floating point (20000 cases)",
    ok=bool(exact8) and worst8 < 1e-13 and minev > 0,
    note="v01 first run used an error relative to a'S~a and failed at 1.1e-6 by cancellation when the two thresholds differ by 1e4; "
         "the identity itself is exact (part a).")

# Theorem 1(b) published analogue [Forsling2025]: Sigma = [[8,1],[1,2]], P = diag(8,2)
Sg, Pf = np.array([[8.0, 1.0], [1.0, 2.0]]), np.diag([8.0, 2.0])
Ph = np.diag(1 / np.sqrt(np.diag(Pf)))
ev = np.linalg.eigvalsh(Ph @ Sg @ Ph)
add("T1b_forsling", "whitened covariance P^-1/2 Sigma P^-1/2 has eigenvalues 0.75 and 1.25; E[N] = tr(P^-1 Sigma) = 2",
    {"eigenvalues": ev.tolist(), "E_N": float(np.trace(np.linalg.solve(Pf, Sg)))}, method="exact",
    ok=abs(ev[0] - 0.75) < 1e-12 and abs(ev[1] - 1.25) < 1e-12 and abs(np.trace(np.linalg.solve(Pf, Sg)) - 2) < 1e-12)

# Remark 4: a FIXED test log is not covered by the transductive bound; a uniformly drawn test log (or the test-part average) is
scores = np.concatenate([np.arange(1, 40, dtype=float), [1000.0]])  # 40 g-logs, one item each; log 39 is extreme
fix_l, avg_l = [], []
for _ in range(20000):
    perm = rng.permutation(40)
    cal, tst = perm[:20], perm[20:]
    ch = crc_exact(scores[cal], cal)
    if 39 in tst:
        fix_l.append(float(scores[39] > ch))
    avg_l.append(float(np.mean(scores[tst] > ch)))
add("R4_fixed_test_log", "random split of 40 g-logs into 20 + 20: the test-part average has E <= delta, but for the fixed extreme log, "
    "E[loss | it is in the test part] = 1", {"E_test_average": float(np.mean(avg_l)), "E_fixed_log_given_test": float(np.mean(fix_l))},
    method="MC 20000 random splits (exact CRC)", ok=np.mean(avg_l) <= 0.05 + 0.002 and np.mean(fix_l) == 1.0,
    note="Corrects P01-A4 Prop. B (B1) 'Fix a test scene t'.")

# Proposition 9: pointwise domination
dom_ok = True
for _ in range(2000):
    th_own = rng.normal(1.6, 0.5, 6)
    cbar = th_own.max() + abs(rng.normal())
    Ut = rng.normal(size=50)
    dom_ok &= all(np.mean(Ut > cbar) <= np.mean(Ut > t) for t in th_own)
add("P9_domination", "c_bar >= c_g implies L_g(Z; c_bar) <= L_g(Z; c_g) for every log (pointwise)", bool(dom_ok), method="exact", ok=bool(dom_ok))

# =====================================================================================================================
# Remark 2 (orientation null): exact 1-D quadrature, sigma_a = 0, units of the along-axis SD, half-width h = 6
z5 = z(0.05)
hh = 6.0


def eft(d):
    num = float(Phi(min(d - hh, -z5)) + Phibar(max(d + hh, z5)))
    den = float(Phi(d - hh) + Phibar(d + hh))
    return num / den


def e0_pre(d):
    num = integrate.quad(lambda ep: nd.pdf(ep) * float(Phi(d - hh - ep)), -np.inf, -z5, epsabs=1e-14)[0] + \
        integrate.quad(lambda ep: nd.pdf(ep) * float(Phibar(d + hh - ep)), z5, np.inf, epsabs=1e-14)[0]
    den = float(Phi((d - hh) / math.sqrt(2)) + Phibar((d + hh) / math.sqrt(2)))
    return num / den


def e0_kept(d):
    def inner(e_, which):
        dh = d - e_
        if which == "num":
            return float(Phi(min(dh - hh, -z5)) + Phibar(max(dh + hh, z5)))
        return float(Phi(dh - hh) + Phibar(dh + hh))
    num = den = 0.0
    for lo_, hi_ in ((-np.inf, d - hh), (d + hh, np.inf)):  # real filter: |d - e| > h
        num += integrate.quad(lambda e_: nd.pdf(e_) * inner(e_, "num"), lo_, hi_, epsabs=1e-15)[0]
        den += integrate.quad(lambda e_: nd.pdf(e_) * inner(e_, "den"), lo_, hi_, epsabs=1e-15)[0]
    return num / den


r2tab = {str(x): {"E_FT": eft(hh + x), "E0_pre": e0_pre(hh + x), "E0_kept": e0_kept(hh + x)} for x in (-2, -1, -0.5, 0, 0.5, 1, 4)}
add("R2_orientation_null", "truth 1 SD inside the separating boundary: E_FT = 0.05/Phi(-1) (draft 0.315) vs E0 (pre-filter candidates; draft 0.175)",
    {"x=-1": r2tab["-1"], "table": r2tab, "E_FT_closed_form": 0.05 / float(Phi(-1.0))}, expected=[0.315, 0.175], tol=5e-4,
    method="exact closed form + 1-D quadrature",
    ok=abs(r2tab["-1"]["E_FT"] - 0.315) < 5e-4 and abs(r2tab["-1"]["E0_pre"] - 0.175) < 5e-4)

# =====================================================================================================================
ALL = all(c["pass"] for c in CHECKS)
out = {"script": "50_CODE/x3/x3_proofcheck_v01.py", "script_sha256": sha256_path(os.path.abspath(__file__)),
       "library_sha256": {"50_CODE/m/m_lib_v04.py": sha256_path(M.__file__),
                          "50_CODE/c1_av2/c1_crc_exact_v01.py (logic copied, not executed)": sha256_path(os.path.join(W, "50_CODE", "c1_av2", "c1_crc_exact_v01.py"))},
       "python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__, "platform": platform.platform(), "seed": SEED,
       "runtime_s": round(time.time() - t0, 1), "n_checks": len(CHECKS), "ALL_PASS": ALL, "checks": CHECKS}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, default=float, ensure_ascii=False)
print("ALL_PASS", ALL, "checks", len(CHECKS), "runtime %.0f s" % (time.time() - t0))
print("wrote", OUT, sha256_path(OUT))
