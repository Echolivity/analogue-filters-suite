"""Standalone float64 replicas of selected production equations, written for the
independent review (root-cause analysis). They transcribe the generator source
line by line; they are NOT used by the device and change nothing in production.

  f_sherman : source/src/build_genexpr.py:102-113 (+ coefficients :300-305)
  f_steiner : source/src/build_genexpr.py:197-214 (+ coefficients :324-327)
"""
import math


def f_tg(v):
    a = abs(v)
    return math.tanh(v) / v if a > 0.001 else 1 - a * a * 0.333333333


def f_ag(v):
    return 1 / math.sqrt(1 + v * v)


def f_asym(x):
    return (math.tanh(x + 0.35) - 0.3363755443363322) / 0.8868514931724362


def f_svf(x, s1, s2, g, R):
    h = (x - (2 * R + g) * s1 - s2) / (1 + 2 * R * g + g * g)
    b = g * h + s1
    l = g * b + s2
    return h, b, l, g * h + b, g * b + l


def sherman_coefs(r, c=0.0):
    R1 = 0.3 + 0.7 * (1 - r) * (1 - r)
    Rt = 0.8 * (1 - r) * (1 - r) - 0.08 * r ** 30
    return R1, Rt, 0.92 * c


class Sherman:
    """Exact transcription; `iters` > 0 replaces the one-sample-lagged secant of the
    filter-2 damping by a fixed-point iteration on the CURRENT band value (diagnostic only)."""
    def __init__(self, g, r, c=0.0, ti=1.0, iters=0, damp_law="ag"):
        self.g, self.ti, self.iters, self.law = g, ti, iters, damp_law
        self.R1, self.Rt, self.fb = sherman_coefs(r, c)
        self.s1a = self.s2a = self.ba = self.s1b = self.s2b = self.bb = self.yp = 0.0
        self.Rb_trace = []

    def step(self, x):
        g = self.g
        u = f_asym(1.6 * (x + self.fb * self.yp)) * 0.625
        Ra = 1 - (1 - self.R1) * f_tg(self.ba)
        h1, b1, l1, n1a, n2a = f_svf(u, self.s1a, self.s2a, g, Ra)
        i2 = u + self.ti * (l1 - u)
        sat = (lambda v: f_ag(2 * v)) if self.law == "ag" else (lambda v: f_tg(2 * v))
        Rb = 1 - (1 - self.Rt) * sat(self.bb)
        h2, b2, l2, n1b, n2b = f_svf(i2, self.s1b, self.s2b, g, Rb)
        for _ in range(self.iters):           # diagnostic: implicit (current-sample) damping
            Rb = 1 - (1 - self.Rt) * sat(b2)
            h2, b2, l2, n1b, n2b = f_svf(i2, self.s1b, self.s2b, g, Rb)
        self.Rb_trace.append(Rb)
        self.s1a, self.s2a, self.ba = n1a, n2a, b1
        self.s1b, self.s2b, self.bb = n1b, n2b, b2
        self.yp = math.tanh(l2)
        return l2


def steiner_K(r):
    return 1 + 2.1 * r ** 1.3


class Steiner:
    def __init__(self, g, r, iters=0):
        self.g, self.K, self.iters = g, steiner_K(r), iters
        self.s1 = self.s2 = self.d1 = self.d2 = self.vb = 0.0
        self.trace = []

    def solve(self, xl, xb, xh, d1p, d2p, vbp):
        g, K = self.g, self.K
        t1 = f_tg(d1p * 0.7); t2 = f_tg(d2p * 0.7)
        Ke = K * f_ag(K * vbp * 0.7)
        a11 = 1 + g * (t1 + t2); a12 = -g * (t1 * Ke + t2 * (Ke - 1))
        a21 = g * t2; a22 = 1 - g * t2 * (Ke - 1)
        c2 = g * t2 * ((Ke - 1) * xh + xb)
        b1 = g * t1 * (Ke * xh + xb - xl) + c2 + self.s1
        b2 = c2 + self.s2
        idet = 1 / (a11 * a22 - a12 * a21)
        q1 = (b1 * a22 - a12 * b2) * idet; q2 = (a11 * b2 - a21 * b1) * idet
        vB = q2 + xh; vA = Ke * vB + xb - q1
        return Ke * vB, q1, q2, xl - vA, vA - vB, vB, Ke, t1, t2, a11 * a22 - a12 * a21

    def step(self, x):
        y, q1, q2, d1, d2, vB, Ke, t1, t2, det = self.solve(x, 0.0, 0.0, self.d1, self.d2, self.vb)
        for _ in range(self.iters):
            y, q1, q2, d1, d2, vB, Ke, t1, t2, det = self.solve(x, 0.0, 0.0, d1, d2, vB)
        self.trace.append((Ke, t1, t2, det))
        self.s1, self.s2 = 2 * q1 - self.s1, 2 * q2 - self.s2
        self.d1, self.d2, self.vb = d1, d2, vB
        return y
