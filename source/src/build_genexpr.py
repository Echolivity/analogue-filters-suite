#!/usr/bin/env python3
"""Generates dubfilter.genexpr — the complete gen~ DSP engine.

The engine is written as pure GenExpr functions (state in -> state out) plus a
generated main body. All filter state lives in top-level History objects that
are read once at the top of each sample and written once at the end, so the
code behaves identically whatever History read/write ordering semantics apply.

Model registry (MODELS) is the single extension point: adding a model means
adding a GenExpr function + one registry entry; the main body, crossfading,
slope logic, oversampling and reset code are generated from the registry.
"""
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from hiir_design import coefs as hiir_coefs
import bpf  # v1.2 band-pass engine (separate module)

HIIR = hiir_coefs(10, 0.0227)

# ---------------------------------------------------------------------------
# Library of pure DSP functions (GenExpr)
# ---------------------------------------------------------------------------
LIB = r"""
// ---------- helpers ----------
// TPT one-pole lowpass. returns lp, new_state
f_op(x, s, G) {
	v = (x - s) * G;
	lp = v + s;
	return lp, lp + v;
}

// secant gain of tanh: tanh(v)/v  (1 at v=0)
f_tg(v) {
	a = abs(v);
	r = 1 - a * a * 0.333333333;
	if (a > 0.001) {
		r = tanh(v) / v;
	}
	return r;
}

// secant gain of an asymmetric diode-like curve with unit slope at 0
// curve: (tanh(v + b) - tanh(b)) / (1 - tanh(b)^2), b = 0.35
f_dg(v) {
	a = abs(v);
	r = 1 - 0.3363755443363322 * v;
	if (a > 0.001) {
		r = (tanh(v + 0.35) - 0.3363755443363322) / (v * 0.8868514931724362);
	}
	return max(r, 0);
}

// secant gain of algebraic hard-knee sigmoid v/sqrt(1+v^2)
f_ag(v) {
	return 1 / sqrt(1 + v * v);
}

// asymmetric soft clip with unit slope at 0
f_asym(x) {
	return (tanh(x + 0.35) - 0.3363755443363322) / 0.8868514931724362;
}

// ---------- TPT state-variable filter (Zavalishin) ----------
// returns hp, bp, lp, new_s1, new_s2
f_svf(x, s1, s2, g, R) {
	h = (x - (2 * R + g) * s1 - s2) / (1 + 2 * R * g + g * g);
	b = g * h + s1;
	l = g * b + s2;
	return h, b, l, g * h + b, g * b + l;
}

// ---------- 4x4 tridiagonal solve (Thomas algorithm) ----------
// rows: [B1 C1 . .], [A2 B2 C2 .], [. A3 B3 C3], [. . A4 B4]
f_tri4(d1, d2, d3, d4, B1, C1, A2, B2, C2, A3, B3, C3, A4, B4) {
	c1 = C1 / B1;
	e1 = d1 / B1;
	m2 = B2 - A2 * c1;
	c2 = C2 / m2;
	e2 = (d2 - A2 * e1) / m2;
	m3 = B3 - A3 * c2;
	c3 = C3 / m3;
	e3 = (d3 - A3 * e2) / m3;
	y4 = (d4 - A4 * e3) / (B4 - A4 * c3);
	y3 = e3 - c3 * y4;
	y2 = e2 - c2 * y3;
	y1 = e1 - c1 * y2;
	return y1, y2, y3, y4;
}

// ================= MODEL 01: Sherman Filterbank-inspired =================
// No schematic is public. Structure follows the published description: input
// overdrive stage -> filter 1 -> filter 2 in series (24 dB when tuned equal),
// filter 2 more resonant than filter 1. Plus a saturated feedback path
// (output -> input, unit delay) for the Filterbank's howl.
// R1: filter-1 damping (mild); Rt: filter-2 damping (to self-oscillation).
// ti: 0 = filter 2 alone (12 dB), 1 = filter 1 -> filter 2 (24 dB)
// returns y, y, s1a, s2a, ba, s1b, s2b, bb, yprev
f_sherman(x, s1a, s2a, ba, s1b, s2b, bb, yp, g, R1, Rt, fb, ti, hp) {
	u = f_asym(1.6 * (x + fb * yp)) * 0.625;
	Ra = 1 - (1 - R1) * f_tg(ba);
	h1, b1, l1, n1a, n2a = f_svf(u, s1a, s2a, g, Ra);
	o1 = hp > 0.5 ? h1 : l1;
	Rb = 1 - (1 - Rt) * f_ag(bb * 2);
	i2 = u + ti * (o1 - u);
	h2, b2, l2, n1b, n2b = f_svf(i2, s1b, s2b, g, Rb);
	o2 = hp > 0.5 ? h2 : l2;
	ynext = tanh(o2);
	return o2, o2, fixdenorm(n1a), fixdenorm(n2a), b1, fixdenorm(n1b), fixdenorm(n2b), b2, ynext;
}

// ================= MODEL 02: Korg 35 (MS-20 Mk1)-inspired =================
// Sallen-Key style: LP1 -> sum -> LP2 -> y ; y*K -> HP1 -> sum   (lowpass)
//                   HP1 -> sum -> HP2 -> y ; y*K -> LP1 -> sum   (highpass)
// Zero-delay-feedback solve, tanh in the loop, and diode-style limiting of
// the feedback gain K (secant of tanh at level L, from previous output).
// returns y, s1, s2, s3, yprev
f_k35lp(x, s1, s2, s3, yp, g, K0, L) {
	G = g / (1 + g);
	ig = 1 / (1 + g);
	K = K0 * f_tg(K0 * yp / L);
	y1, n1 = f_op(x, s1, G);
	u = (y1 + ig * (K * ig * s2 - s3)) / (1 - K * G * ig);
	u = 0.85 * tanh(u * 1.17647058824);
	y, n2 = f_op(u, s2, G);
	l3, n3 = f_op(K * y, s3, G);
	return y, fixdenorm(n1), fixdenorm(n2), fixdenorm(n3), y;
}

f_k35hp(x, s1, s2, s3, yp, g, K0, L) {
	G = g / (1 + g);
	ig = 1 / (1 + g);
	K = K0 * f_tg(K0 * yp / L);
	l1, n1 = f_op(x, s1, G);
	y1 = x - l1;
	u = (y1 + ig * (s3 - G * K * s2)) / (1 - K * G * ig);
	u = 0.85 * tanh(u * 1.17647058824);
	l2, n2 = f_op(u, s2, G);
	y = u - l2;
	l3, n3 = f_op(K * y, s3, G);
	return y, fixdenorm(n1), fixdenorm(n2), fixdenorm(n3), y;
}

// ================= MODEL 03: Moog transistor ladder-inspired =================
// Circuit: each ladder stage is a transistor differential pair loaded by a
// capacitor, so each stage obeys  dy_i/dt = w (tanh(y_{i-1}) - tanh(y_i)),
// driven by the input pair tanh(x - k y4)  (Huovilainen, DAFx-04).
// Solved here with zero-delay feedback: every tanh is replaced by its secant
// gain at the previous sample (T = tanh(v)/v), which makes each stage
// linear for the current sample, so the global feedback is solved exactly.
// hs scales the stage pairs' saturation (CHARACTER: STAGE SAT).
// returns y12, y24, s1..s4, p0..p4
f_ladder(x, s1, s2, s3, s4, p0, p1, p2, p3, p4, g, k, bc, hs, hp) {
	T0 = f_tg(1.4 * p0);
	T1 = f_tg(1.4 * hs * p1);
	T2 = f_tg(1.4 * hs * p2);
	T3 = f_tg(1.4 * hs * p3);
	T4 = f_tg(1.4 * hs * p4);
	i1 = 1 / (1 + g * T1);
	i2 = 1 / (1 + g * T2);
	i3 = 1 / (1 + g * T3);
	i4 = 1 / (1 + g * T4);
	G1 = g * T0 * i1;
	G2 = g * T1 * i2;
	G3 = g * T2 * i3;
	G4 = g * T3 * i4;
	S = G2 * G3 * G4 * s1 * i1 + G3 * G4 * s2 * i2 + G4 * s3 * i3 + s4 * i4;
	u = (x * (1 + k * bc) - k * S) / (1 + k * G1 * G2 * G3 * G4);
	y1 = G1 * u + s1 * i1;
	y2 = G2 * y1 + s2 * i2;
	y3 = G3 * y2 + s3 * i3;
	y4 = G4 * y3 + s4 * i4;
	o12 = y2;
	o24 = y4;
	if (hp > 0.5) {
		o12 = u - 2 * y1 + y2;
		o24 = u - 4 * y1 + 6 * y2 - 4 * y3 + y4;
	}
	return o12, o24, fixdenorm(2 * y1 - s1), fixdenorm(2 * y2 - s2), fixdenorm(2 * y3 - s3), fixdenorm(2 * y4 - s4), u, y1, y2, y3, y4;
}

// ================= MODEL 04: Steiner-Parker Synthacon-inspired =================
// Circuit (Steiner, Electronic Design 25, 1974; CGS35 notes): a Sallen-Key
// network whose two resistors are biased diode strings (voltage-controlled
// resistors), with Q set by the gain K of a non-inverting amplifier
// (self-oscillation at K = 3, Q constant while sweeping). LP, BP and HP are
// obtained by injecting the signal at three different points of the SAME
// network:  xl -> R1 (LP),  xb -> feedback node of C1 (BP),  xh -> C2 (HP).
// Linear: H_LP = K/D, H_BP = K s/D, H_HP = K s(s+2)/D,  D = s^2 + (3-K)s + 1.
// Nonlinear: diode-string currents saturate (tanh secant of the voltage
// across each string), the amplifier clips (hard-knee sigmoid secant on K).
// Zero-delay 2x2 trapezoidal solve per sample.
// returns y, s1, s2, d1, d2, vb
f_steiner(xl, xb, xh, s1, s2, d1p, d2p, vbp, g, K) {
	t1 = f_tg(d1p * 0.7);
	t2 = f_tg(d2p * 0.7);
	Ke = K * f_ag(K * vbp * 0.7);
	a11 = 1 + g * (t1 + t2);
	a12 = -g * (t1 * Ke + t2 * (Ke - 1));
	a21 = g * t2;
	a22 = 1 - g * t2 * (Ke - 1);
	c2 = g * t2 * ((Ke - 1) * xh + xb);
	b1 = g * t1 * (Ke * xh + xb - xl) + c2 + s1;
	b2 = c2 + s2;
	idet = 1 / (a11 * a22 - a12 * a21);
	q1 = (b1 * a22 - a12 * b2) * idet;
	q2 = (a11 * b2 - a21 * b1) * idet;
	vB = q2 + xh;
	vA = Ke * vB + xb - q1;
	return Ke * vB, fixdenorm(2 * q1 - s1), fixdenorm(2 * q2 - s2), xl - vA, vA - vB, vB;
}

// ================= MODEL 05: Oberheim SEM-inspired =================
// Circuit: 2-pole state-variable filter whose integrators are CA3080 OTAs
// driving capacitors; an OTA's output current is gm*tanh(vin/2Vt), so each
// integrator's input saturates. Damping (resonance pot) never reaches zero:
// no self-oscillation. Mode knob mixes LP and HP (notch at the centre).
// Secant-linearised OTA gains (g1, g2) inside a zero-delay SVF solve.
// m: LP->notch (LPF stage) or HP->notch (HPF stage)
// returns y, s1, s2, hprev, bprev
f_sem(x, s1, s2, hpp, bpp, g, R, m, hp) {
	u = 2 * tanh(0.5 * x);
	g1 = g * f_tg(hpp * 0.6);
	g2 = g * f_tg(bpp * 0.6);
	h = (u - (2 * R + g2) * s1 - s2) / (1 + 2 * R * g1 + g1 * g2);
	b = g1 * h + s1;
	l = g2 * b + s2;
	y = hp > 0.5 ? h + m * l : l + m * h;
	return y, fixdenorm(2 * b - s1), fixdenorm(2 * l - s2), h, b;
}

// ================= MODEL 06: Roland TB-303-inspired (diode ladder) =================
// Circuit (Stinchcombe 2008, "TB-303 configuration": one diode at the top of
// the ladder, bottom capacitor C/2): current-driven 4-node RC ladder whose
// rungs are diode pairs. Linear core:
//   0.5 v1' = u - (v1-v2);  v2' = (v1-v2)-(v2-v3);  v3' = (v2-v3)-(v3-v4);
//   v4' = (v3-v4) - v4
// -> denominator s^4 + 6.727 s^3 + 14.142 s^2 + 9.514 s + 1 (after scaling),
// self-oscillation at k = 17, w = sqrt(2). Feedback drives the input pair
// through a one-pole highpass (as in the 303). Nonlinear: input pair tanh,
// each diode rung's conductance follows the tanh secant of its voltage.
// returns y, s1..s4, v1..v4, sf, sc
f_diode(x, s1, s2, s3, s4, v1p, v2p, v3p, v4p, sf, sc, g, k, Gf, bc) {
	t1 = f_tg(0.5 * (v1p - v2p));
	t2 = f_tg(0.5 * (v2p - v3p));
	t3 = f_tg(0.5 * (v3p - v4p));
	t4 = f_tg(0.5 * v4p);
	B1 = 1 + 2 * g * t1;
	C1 = -2 * g * t1;
	A2 = -g * t1;
	B2 = 1 + g * (t1 + t2);
	C2 = -g * t2;
	A3 = -g * t2;
	B3 = 1 + g * (t2 + t3);
	C3 = -g * t3;
	A4 = -g * t3;
	B4 = 1 + g * (t3 + t4);
	a1, a2, a3, a4 = f_tri4(2 * g, 0, 0, 0, B1, C1, A2, B2, C2, A3, B3, C3, A4, B4);
	b1, b2, b3, b4 = f_tri4(s1, s2, s3, s4, B1, C1, A2, B2, C2, A3, B3, C3, A4, B4);
	xi = tanh(x);
	lc, nsc = f_op(xi, sc, Gf);
	xc = xi + k * bc * (xi - lc);
	igf = 1 - Gf;
	u = (xc - k * igf * (b4 - sf)) / (1 + k * igf * a4);
	u = 2 * tanh(0.5 * u);
	y1 = b1 + u * a1;
	y2 = b2 + u * a2;
	y3 = b3 + u * a3;
	y4 = b4 + u * a4;
	lf, nsf = f_op(y4, sf, Gf);
	return y4, fixdenorm(2 * y1 - s1), fixdenorm(2 * y2 - s2), fixdenorm(2 * y3 - s3), fixdenorm(2 * y4 - s4), y1, y2, y3, y4, fixdenorm(nsf), fixdenorm(nsc);
}

// ---------- 2x polyphase IIR half-band (5+5 first-order allpasses) ----------
// one allpass chain step: returns y, z0..z5 (z0 = x[n-1] of section 1, zi = y[n-1] of section i)
f_ap5(x, z0, z1, z2, z3, z4, z5, c1, c2, c3, c4, c5) {
	y1 = c1 * (x - z1) + z0;
	y2 = c2 * (y1 - z2) + z1;
	y3 = c3 * (y2 - z3) + z2;
	y4 = c4 * (y3 - z4) + z3;
	y5 = c5 * (y4 - z5) + z4;
	return y5, x, y1, y2, y3, y4, y5;
}
"""

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
# taps: "12" (native 12 dB only), "12/24" (native 12 & 24 taps), "24" (native 24 only)
# states: names of per-channel state variables
# lp/hp: whether the model supports the stage natively ("native"), as an
#        explicitly labelled alternative ("alt") or not at all (None)
MODELS = [
    dict(id=0, key="sh", name="Sherman Filterbank-inspired", taps="12/24",
         states=["s1a", "s2a", "ba", "s1b", "s2b", "bb", "yp"], lp="native", hp="native",
         char="FEEDBACK",
         coef=["{p}_g = {s}_gw;",
               "{p}_R1 = 0.3 + 0.7 * (1 - {r}) * (1 - {r});",
               "{p}_R = 0.8 * (1 - {r}) * (1 - {r}) - 0.08 * pow({r}, 30);",
               "{p}_fb = 0.92 * {c};"],
         call=["o12, o24, {sv} = f_sherman({x}, {sv}, {p}_g, {p}_R1, {p}_R, {p}_fb, {s}_ti, {hp});",
               "{acc} = {acc} + {mix} * (o12 + {s}_ti * (o24 - o12));"]),
    dict(id=1, key="k3", name="Korg 35 (MS-20 Mk1)-inspired", taps="12",
         states=["s1", "s2", "s3", "yp"], lp="native", hp="native", char="FB CLIP",
         coef=["{p}_g = {s}_gw;",
               "{p}_K = 0.05 + 2.03 * pow({r}, 1.1);",
               "{p}_L = 4 * exp2(-4 * {c});"],
         call=["o1, {sv} = {k35fn}({x}, {sv}, {p}_g, {p}_K, {p}_L);",
               "{acc} = {acc} + {mix} * o1;"]),
    dict(id=2, key="ld", name="Moog transistor ladder-inspired", taps="12/24",
         states=["s1", "s2", "s3", "s4", "p0", "p1", "p2", "p3", "p4"], lp="native", hp="alt", char="STAGE SAT",
         coef=["{p}_g = {s}_gw;",
               "{p}_k = 4.3 * pow({r}, 1.3);",
               "{p}_bc = {s}_cmp * {lpflag};",
               "{p}_hs = 1 + 2 * {c};"],
         call=["o12, o24, {sv} = f_ladder({x}, {sv}, {p}_g, {p}_k, {p}_bc, {p}_hs, {hp});",
               "{acc} = {acc} + {mix} * (o12 + {s}_ti * (o24 - o12));"]),
    dict(id=3, key="st", name="Steiner-Parker Synthacon-inspired", taps="12",
         states=["s1", "s2", "d1", "d2", "vb"], lp="native", hp="native", char="BP BLEND",
         coef=["{p}_g = {s}_gw;",
               "{p}_K = 1 + 2.1 * pow({r}, 1.3);",
               "{p}_kd = 1 / pow({p}_K, {s}_cmp);"],
         call=["o1, {sv} = f_steiner({x} * (1 - {c}) * {lpflag}, {x} * {c}, {x} * (1 - {c}) * {hp}, {sv}, {p}_g, {p}_K);",
               "{acc} = {acc} + {mix} * o1 * {p}_kd;"]),
    dict(id=4, key="se", name="Oberheim SEM-inspired", taps="12",
         states=["s1", "s2", "hq", "bq"], lp="native", hp="native", char="NOTCH MORPH",
         coef=["{p}_g = {s}_gw;",
               "{p}_R = pow(20, -{r});"],
         call=["o1, {sv} = f_sem({x}, {sv}, {p}_g, {p}_R, {c}, {hp});",
               "{acc} = {acc} + {mix} * o1;"]),
    dict(id=5, key="di", name="Roland TB-303-inspired (diode ladder)", taps="24",
         states=["s1", "s2", "s3", "s4", "v1", "v2", "v3", "v4", "sf", "sc"], lp="native", hp=None, char="SQUELCH",
         coef=["{p}_k = {kmax} * pow({r}, 1.8);",
               "{p}_g = {s}_gw / (0.1494 + 1.2648 * sqrt(min({p}_k / {kosc}, 1.06)));",
               "{p}_gf = tan(pi * min(8 * exp2(5.2 * {c}), 0.45 * fso) / fso);",
               "{p}_Gf = {p}_gf / (1 + {p}_gf);"],
         call=["o1, {sv} = f_diode({x}, {sv}, {p}_g, {p}_k, {p}_Gf, {s}_cmp);",
               "{acc} = {acc} + {mix} * o1;"]),
]

STAGES = [
    dict(key="l", hp=0, cut_min=20, cut_max=20000, cut_def=20000, nmodels=6),
    dict(key="h", hp=1, cut_min=20, cut_max=2000, cut_def=20, nmodels=5),
]
CH = ["L", "R"]
DIODE_KOSC = 17.0


def fill(t, **kw):
    kw.setdefault("kmax", repr(DIODE_KOSC * 1.15))
    kw.setdefault("kosc", repr(DIODE_KOSC))
    return t.format(**kw)


def stage_models(st):
    return [m for m in MODELS if (m["hp"] if st["hp"] else m["lp"])]


class Gen:
    def __init__(self):
        self.lines = []
        self.hist = []      # (name, init)
        self.ind = 0

    def w(self, s=""):
        self.lines.append("\t" * self.ind + s if s else "")

    def H(self, name, init=0.0):
        self.hist.append((name, init))
        return name


def build():
    G = Gen()
    params = []

    def P(name, default, lo, hi):
        params.append((name, default, lo, hi))

    # ----- parameters (values arrive in Live units) -----
    for st in STAGES:
        s = st["key"]
        P(f"{s}_on", 1, 0, 1)
        P(f"{s}_model", 2 if s == "l" else 1, 0, st["nmodels"] - 1)
        P(f"{s}_cut", st["cut_def"], st["cut_min"], st["cut_max"])
        P(f"{s}_res", 0, 0, 100)
        P(f"{s}_slope", 1 if s == "l" else 0, 0, 3)
        P(f"{s}_drive", 0, 0, 100)
        P(f"{s}_comp", 100, 0, 100)
        P(f"{s}_char", 0, 0, 100)
    P("order_sel", 0, 0, 1)
    P("ovs_sel", 0, 0, 1)
    P("out_db", 0, -24, 12)
    P("softclip", 1, 0, 1)
    # v1.2: band-pass engine parameters (appended; existing parameters unchanged)
    for (n, d, lo, hi) in bpf.params():
        P(n, d, lo, hi)

    # ----- state declarations -----
    statevars = []   # local names mirrored from histories
    def SV(name):
        G.H("H_" + name, 0.0)
        statevars.append(name)
        return name

    for st in STAGES:
        s = st["key"]
        for m in stage_models(st):
            for c in CH:
                for v in m["states"]:
                    SV(f"{s}_{c}_{m['key']}_{v}")
        for c in CH:
            for e in range(3):
                SV(f"{s}_{c}_x{e}_s1"); SV(f"{s}_{c}_x{e}_s2")
    for c in CH:
        for d in ("up", "dn"):
            for p in ("a", "b"):
                for z in range(6):
                    SV(f"os_{c}_{d}{p}{z}")
        SV(f"dc_{c}_x"); SV(f"dc_{c}_y")
    bpf_sv = []
    def SVB(name):  # v1.2 BPF state (registered after all existing state)
        bpf_sv.append(name)

    # smoothed control histories (not reset with filter state)
    ctrl = []
    def CV(name, init):
        G.H("H_" + name, init)
        ctrl.append(name)
    for st in STAGES:
        s = st["key"]
        CV(f"{s}_lc", math.log2(st["cut_def"]))
        for n, i in (("rz", 0), ("drv", 0), ("cmp", 1.0), ("chr", 0), ("en", 1), ("ti", 1 if s == "l" else 0),
                     ("w0", 1), ("w1", 0), ("w2", 0), ("w3", 0)):
            CV(f"{s}_{n}", i)
        CV(f"{s}_cur", 2 if s == "l" else 1)
        CV(f"{s}_prev", 2 if s == "l" else 1)
        CV(f"{s}_fade", 1)
    for n, i in (("cur_order", 0), ("cur_os", 0), ("duck", 1), ("og", 1), ("init", 0)):
        CV(n, i)
    bpf.register_state(SVB, CV)
    for v in bpf_sv:
        SV(v)

    # ======================= main body ==========================
    w = G.w
    w("// ======================= MAIN =======================")
    w("fs = samplerate;")
    w("cur_order = H_cur_order;")
    w("cur_os = H_cur_os;")
    w("ovs = cur_os > 0.5 ? 2 : 1;")
    w("fso = fs * ovs;")
    w("a_cut = 1 - exp(-1 / (0.006 * fs));")
    w("a_par = 1 - exp(-1 / (0.015 * fs));")
    w("a_mix = 1 - exp(-1 / (0.010 * fs));")
    w("fstep = 1 / (0.025 * fs);")
    w("dstep = 1 / (0.004 * fs);")
    w("x_L = in1;")
    w("x_R = in2;")
    w()
    w("// ---- load state ----")
    for v in statevars:
        w(f"{v} = H_{v};")
    w()

    for st in STAGES:
        s = st["key"]
        mods = stage_models(st)
        w(f"// ================= stage {s.upper()}PF controls =================")
        w(f"{s}_lc = H_{s}_lc + a_cut * (log2(clamp({s}_cut, {st['cut_min']}, {st['cut_max']})) - H_{s}_lc);")
        w(f"{s}_rz = H_{s}_rz + a_par * (clamp({s}_res, 0, 100) * 0.01 - H_{s}_rz);")
        w(f"{s}_drv = H_{s}_drv + a_par * (clamp({s}_drive, 0, 100) * 0.01 - H_{s}_drv);")
        w(f"{s}_cmp = H_{s}_cmp + a_par * (clamp({s}_comp, 0, 100) * 0.01 - H_{s}_cmp);")
        w(f"{s}_chr = H_{s}_chr + a_par * (clamp({s}_char, 0, 100) * 0.01 - H_{s}_chr);")
        w(f"{s}_fc = exp2({s}_lc);")
        w(f"{s}_fcc = min({s}_fc, 0.45 * fso);")
        w(f"{s}_gw = tan(pi * {s}_fcc / fso);")
        # enable & open-zone detent
        w(f"{s}_ent = {s}_on > 0.5 ? 1 : 0;")
        w(f"{s}_en = H_{s}_en + a_mix * ({s}_ent - H_{s}_en);")
        w(f"if ({s}_ent < 0.5 && {s}_en < 0.0001) {{")
        w(f"\t{s}_en = 0;")
        w("}")
        w(f"if ({s}_ent > 0.5 && {s}_en > 0.9999) {{")
        w(f"\t{s}_en = 1;")
        w("}")
        if s == "l":
            w(f"{s}_det = clamp((20000 - {s}_fc) * 0.00025, 0, 1);")
        else:
            w(f"{s}_det = clamp(({s}_fc - 20) * 0.2, 0, 1);")
        w(f"{s}_wet = {s}_en * {s}_det;")
        w(f"{s}_run = {s}_wet > 0 ? 1 : 0;")
        # drive & compensation
        w(f"{s}_d = 0.25 * exp2(5 * {s}_drv);")
        w(f"{s}_id = 1 / {s}_d;")
        w(f"{s}_osc = {s}_id * exp2(5 * {s}_drv * (1 - 0.5 * {s}_cmp));")
        # model selection & crossfade
        w(f"{s}_msel = clamp(floor({s}_model + 0.5), 0, {len(mods) - 1});")
        w(f"{s}_cur = H_{s}_cur;")
        w(f"{s}_prev = H_{s}_prev;")
        w(f"{s}_fade = H_{s}_fade;")
        w(f"if ({s}_msel != {s}_cur) {{")
        w(f"\t{s}_prev = {s}_cur;")
        w(f"\t{s}_cur = {s}_msel;")
        w(f"\t{s}_fade = 0;")
        w("}")
        w(f"{s}_fade = min(1, {s}_fade + fstep);")
        # slope logic
        w(f"{s}_ssel = clamp(floor({s}_slope + 0.5), 0, 3);")
        w(f"{s}_tit = {s}_ssel > 0.5 ? 1 : 0;")
        # number of linear extension sections for the CURRENT model
        conds = []
        for m in mods:
            if m["taps"] == "12":
                continue
        twelve = [m["id"] for m in mods if m["taps"] == "12"]
        cond = " || ".join(f"{s}_cur == {i}" for i in twelve) if twelve else "0"
        w(f"{s}_n12 = ({cond}) ? 1 : 0;")
        w(f"{s}_next = {s}_n12 > 0.5 ? {s}_ssel : max(0, {s}_ssel - 1);")
        w(f"{s}_ti = H_{s}_ti + a_mix * ({s}_tit - H_{s}_ti);")
        for j in range(4):
            w(f"{s}_w{j} = H_{s}_w{j} + a_mix * (({s}_next == {j} ? 1 : 0) - H_{s}_w{j});")
        w(f"{s}_xa = ({s}_w1 + {s}_w2 + {s}_w3) > 0.00001 ? 1 : 0;")
        w(f"{s}_xb = ({s}_w2 + {s}_w3) > 0.00001 ? 1 : 0;")
        w(f"{s}_xc = {s}_w3 > 0.00001 ? 1 : 0;")
        w(f"{s}_gx = {s}_gw;")
        # per-model activity, mix weights, coefficients
        for m in mods:
            i, k = m["id"], m["key"]
            w(f"{s}_a{k} = ({s}_run > 0.5 && ({s}_cur == {i} || ({s}_prev == {i} && {s}_fade < 1))) ? 1 : 0;")
            w(f"{s}_m{k} = ({s}_cur == {i} ? {s}_fade : 0) + (({s}_prev == {i} && {s}_cur != {i}) ? 1 - {s}_fade : 0);")
        # coefficients (computed only when active)
        r = f"{s}_rz"
        c = f"{s}_chr"
        for m in mods:
            w(f"// coefficients: {m['name']}")
            for line in m["coef"]:
                w(fill(line, s=s, p=f"{s}_{m['key']}", r=r, c=c, lpflag=1 - st["hp"]))
        # reset inactive model state
        for m in mods:
            k = m["key"]
            w(f"if ({s}_a{k} < 0.5) {{")
            G.ind += 1
            for ch in CH:
                for v in m["states"]:
                    w(f"{s}_{ch}_{k}_{v} = 0;")
            G.ind -= 1
            w("}")
        for e, flag in enumerate(("xa", "xb", "xc")):
            w(f"if ({s}_{flag} < 0.5 || {s}_run < 0.5) {{")
            G.ind += 1
            for ch in CH:
                w(f"{s}_{ch}_x{e}_s1 = 0;")
                w(f"{s}_{ch}_x{e}_s2 = 0;")
            G.ind -= 1
            w("}")
        w()

    bpf.emit_controls(w, G)

    # ---- duck / config switching ----
    w("// ================= order / oversampling switching (duck) =================")
    w("cfg_o = order_sel > 0.5 ? 1 : 0;")
    w("cfg_s = ovs_sel > 0.5 ? 1 : 0;")
    w("cfg_p = b_pos > 0.5 ? 1 : 0;")
    w("b_cur_pos = H_b_cur_pos;")
    w("pend = (cfg_o != cur_order || cfg_s != cur_os || cfg_p != b_cur_pos) ? 1 : 0;")
    w("duck = H_duck;")
    w("duck = pend > 0.5 ? max(0, duck - dstep) : min(1, duck + dstep);")
    w("new_order = cur_order;")
    w("new_os = cur_os;")
    w("new_pos = b_cur_pos;")
    w("rst = 0;")
    w("if (pend > 0.5 && duck <= 0) {")
    w("\tnew_order = cfg_o;")
    w("\tnew_os = cfg_s;")
    w("\tnew_pos = cfg_p;")
    w("\trst = cfg_s != cur_os ? 1 : 0;")
    w("}")
    w()

    # ---- oversampling: upsample ----
    ca = HIIR[0::2]; cb = HIIR[1::2]
    ca_s = ", ".join(repr(round(v, 15)) for v in ca)
    cb_s = ", ".join(repr(round(v, 15)) for v in cb)
    w("// ================= input (2x upsampler when oversampling) =================")
    for ch in CH:
        w(f"xa_{ch} = x_{ch};")
        w(f"xb_{ch} = 0;")
    w("if (ovs > 1.5) {")
    G.ind += 1
    for ch in CH:
        for p, cs in (("a", ca_s), ("b", cb_s)):
            zs = [f"os_{ch}_up{p}{z}" for z in range(6)]
            w(f"x{p}_{ch}, {', '.join(zs)} = f_ap5(x_{ch}, {', '.join(zs)}, {cs});")
    G.ind -= 1
    w("}")
    w()

    # ---- stage processing code generator ----
    def emit_stage(st, sub, src):
        """Emits processing of stage st for subsample 'sub' (a/b), input vars src[ch]."""
        s = st["key"]
        hp = st["hp"]
        mods = stage_models(st)
        w(f"// ---- {s.upper()}PF stage, subsample {sub} ----")
        for ch in CH:
            w(f"{s}y{sub}_{ch} = {src[ch]};")
        w(f"if ({s}_run > 0.5) {{")
        G.ind += 1
        for ch in CH:
            xin = src[ch]
            w(f"{s}i_{ch} = {xin} * {s}_d;")
            w(f"{s}b_{ch} = 0;")
            for m in mods:
                k = m["key"]
                sv = [f"{s}_{ch}_{k}_{v}" for v in m["states"]]
                svs = ", ".join(sv)
                w(f"if ({s}_a{k} > 0.5) {{")
                G.ind += 1
                for line in m["call"]:
                    w(fill(line, s=s, p=f"{s}_{k}", sv=svs, x=f"{s}i_{ch}", hp=hp, c=f"{s}_chr",
                           acc=f"{s}b_{ch}", mix=f"{s}_m{k}", lpflag=1 - hp,
                           k35fn="f_k35hp" if hp else "f_k35lp"))
                G.ind -= 1
                w("}")
            # linear slope-extension sections (Butterworth-Q SVFs, nested taps)
            w(f"e0 = {s}b_{ch};")
            w("e1 = 0;")
            w("e2 = 0;")
            w("e3 = 0;")
            prev = "e0"
            for e, flag in enumerate(("xa", "xb", "xc")):
                w(f"if ({s}_{flag} > 0.5) {{")
                G.ind += 1
                a, b = f"{s}_{ch}_x{e}_s1", f"{s}_{ch}_x{e}_s2"
                outsel = "eh" if hp else "el"
                w(f"eh, eb, el, {a}, {b} = f_svf({prev}, {a}, {b}, {s}_gx, 0.7071067811865476);")
                w(f"{a} = fixdenorm({a});")
                w(f"{b} = fixdenorm({b});")
                w(f"e{e + 1} = {outsel};")
                G.ind -= 1
                w("}")
                prev = f"e{e + 1}"
            w(f"wet_{ch} = ({s}_w0 * e0 + {s}_w1 * e1 + {s}_w2 * e2 + {s}_w3 * e3) * {s}_osc;")
            w(f"{s}y{sub}_{ch} = {xin} + {s}_wet * (wet_{ch} - {xin});")
        G.ind -= 1
        w("}")

    lst, hst = STAGES
    for ch in CH:
        w(f"zb_{ch} = 0;")
    for sub in ("a", "b"):
        if sub == "b":
            w("if (ovs > 1.5) {")
            G.ind += 1
        w(f"// ================= processing chain, subsample {sub} =================")
        w("if (b_cur_pos > 0.5) {")  # v1.2: BPF before the LPF/HPF chain
        G.ind += 1
        bpf.emit_process(w, G, {ch: f"x{sub}_{ch}" for ch in CH}, {ch: f"x{sub}_{ch}" for ch in CH})
        G.ind -= 1
        w("}")
        for ch in CH:
            w(f"hy{sub}_{ch} = 0;")
        w("if (cur_order > 0.5) {")
        G.ind += 1
        emit_stage(hst, sub, {ch: f"x{sub}_{ch}" for ch in CH})
        G.ind -= 1
        w("}")
        for ch in CH:
            w(f"lsrc_{ch} = cur_order > 0.5 ? hy{sub}_{ch} : x{sub}_{ch};")
        emit_stage(lst, sub, {ch: f"lsrc_{ch}" for ch in CH})
        for ch in CH:
            w(f"z{sub}_{ch} = ly{sub}_{ch};")
        w("if (cur_order < 0.5) {")
        G.ind += 1
        emit_stage(hst, sub, {ch: f"ly{sub}_{ch}" for ch in CH})
        for ch in CH:
            w(f"z{sub}_{ch} = hy{sub}_{ch};")
        G.ind -= 1
        w("}")
        w("if (b_cur_pos < 0.5) {")  # v1.2: BPF after the LPF/HPF chain (default)
        G.ind += 1
        bpf.emit_process(w, G, {ch: f"z{sub}_{ch}" for ch in CH}, {ch: f"z{sub}_{ch}" for ch in CH})
        G.ind -= 1
        w("}")
        if sub == "b":
            G.ind -= 1
            w("}")
        w()

    # ---- downsample ----
    w("// ================= output (2x downsampler when oversampling) =================")
    for ch in CH:
        w(f"y_{ch} = za_{ch};")
    w("if (ovs > 1.5) {")
    G.ind += 1
    for ch in CH:
        za = [f"os_{ch}_dna{z}" for z in range(6)]
        zb = [f"os_{ch}_dnb{z}" for z in range(6)]
        w(f"pa, {', '.join(za)} = f_ap5(zb_{ch}, {', '.join(za)}, {ca_s});")
        w(f"pb, {', '.join(zb)} = f_ap5(za_{ch}, {', '.join(zb)}, {cb_s});")
        w(f"y_{ch} = 0.5 * (pa + pb);")
    G.ind -= 1
    w("}")
    w()
    w("// ---- DC blocker (1st order, 2 Hz), output gain, soft clip, duck ----")
    w("dcr = 1 - 2 * pi * 2 / fs;")
    w("og = H_og + a_par * (exp(0.11512925465 * clamp(out_db, -24, 12)) - H_og);")
    for ch in CH:
        w(f"dy_{ch} = y_{ch} - dc_{ch}_x + dcr * dc_{ch}_y;")
        w(f"dc_{ch}_x = y_{ch};")
        w(f"dc_{ch}_y = fixdenorm(dy_{ch});")
        w(f"q_{ch} = dy_{ch} * og;")
        w(f"if (softclip > 0.5) {{")
        G.ind += 1
        w(f"aq = abs(q_{ch});")
        w(f"if (aq > 0.7) {{")
        G.ind += 1
        w(f"q_{ch} = (q_{ch} > 0 ? 1 : -1) * (0.7 + 0.3 * tanh((aq - 0.7) / 0.3));")
        G.ind -= 1
        w("}")
        G.ind -= 1
        w("}")
        w(f"q_{ch} = q_{ch} * duck;")
        w(f"q_{ch} = q_{ch} == q_{ch} ? q_{ch} : 0;")
    w("out1 = q_L;")
    w("out2 = q_R;")
    w()
    w("// ---- reset all filter state on oversampling change ----")
    w("if (rst > 0.5) {")
    G.ind += 1
    for v in statevars:
        w(f"{v} = 0;")
    G.ind -= 1
    w("}")
    w()
    w("// ---- store state ----")
    for v in statevars:
        w(f"H_{v} = {v};")
    for st in STAGES:
        s = st["key"]
        for n in ("lc", "rz", "drv", "cmp", "chr", "en", "ti", "w0", "w1", "w2", "w3", "cur", "prev", "fade"):
            w(f"H_{s}_{n} = {s}_{n};")
    w("H_cur_order = new_order;")
    w("H_cur_os = new_os;")
    w("H_duck = duck;")
    w("H_og = og;")
    w("H_init = 1;")
    for n in bpf.ctrl_names():
        w(f"H_{n} = {n};")
    w("H_b_cur_pos = new_pos;")

    # ---- assemble ----
    out = []
    out.append("// Dub Filter — multi-model analogue-inspired dual filter engine")
    out.append("// GENERATED by src/build_genexpr.py — edit the generator, not this file.")
    out.append("// gen~ codebox: in1/in2 = stereo in, out1/out2 = stereo out.")
    out.append("")
    for (n, d, lo, hi) in params:
        out.append(f"Param {n}({d}, min={lo}, max={hi});")
    out.append("")
    for (n, init) in G.hist:
        out.append(f"History {n}({init!r});")
    out.append(LIB)
    out.append(bpf.LIB)
    out.extend(G.lines)
    return "\n".join(out) + "\n", params


if __name__ == "__main__":
    code, params = build()
    dst = os.path.join(HERE, "..", "build", "dubfilter.genexpr")
    with open(dst, "w") as f:
        f.write(code)
    print("wrote", dst, len(code.splitlines()), "lines")
