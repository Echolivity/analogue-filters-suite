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
import dyn  # v1.3 dynamics chain (separate module)
import routing  # v1.4 filter routing (series / parallel / hybrid)

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
// v1.6: Steiner diode-string conductance secant (Electronic Design, 6 Dec 1974). The string is fed in mirror
// from both ends, so signal current runs against the bias in one half and with it in the other:
// i = 2I sinh(v/V'), and conductance RISES with level (even orders cancel). The 2k feed resistors in series
// bound it: secant = (1 + rho) / (1 / (sinh(a)/a) + rho), rho = 2 pi fc 4.7nF 2k (1 at small signal).
f_sg(v, rho) {
	a = min(abs(v), 20);
	t = a > 0.0001 ? (exp(a) - exp(-a)) * 0.5 / a : 1 + a * a * 0.166666667;
	return (1 + rho) / (1 / t + rho);      // normalised: exactly 1 at small signal
}

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
	// v1.6: re-evaluate the amplitude-dependent damping at the CURRENT band value
	// (one fixed-point step). The lagged value alone lets the limiter sample an
	// oscillation near fs/4 at its zero crossings and pump it (period-2 parametric
	// instability, docs/independent-review/INDEPENDENT_AUDIT_REVIEW.md section 3.1).
	Rb = 1 - (1 - Rt) * f_ag(b2 * 2);
	h2, b2, l2, n1b, n2b = f_svf(i2, s1b, s2b, g, Rb);
	o2 = hp > 0.5 ? h2 : l2;
	ynext = tanh(o2);
	return o2, o2, fixdenorm(n1a), fixdenorm(n2a), b1, fixdenorm(n1b), fixdenorm(n2b), b2, ynext;
}

// ================= MODEL 02: Korg 35 / MS-20, OTA (LM13600, "Mk2") circuit =================
// v1.6: relabelled. Stinchcombe 2006 shows this structure (two buffered one-poles, 1/(s^2+(2-K)s+1),
// clipping in the feedback path) is the later OTA circuit, not the original Korg35 (see f_k35m1).
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

// v1.6: the MS-20 high-pass as built (Stinchcombe 2006, section 7): the low-pass input is grounded and the
// signal drives the lifted end of stage 2's capacitor, so  y = x + LP2(u - x),  u = HP1(K * y).
// Transfer function s(s + 1) / (s^2 + (2 - K)s + 1): a 12 dB high-pass plus a band-pass term, so the
// slope below cutoff is 6 dB/oct (v1.5 used s^2/(...), 12 dB/oct). s1 is unused.
f_k35hp(x, s1, s2, s3, yp, g, K0, L) {
	G = g / (1 + g);
	ig = 1 / (1 + g);
	K = K0 * f_tg(K0 * yp / L);
	// The input reaches the output through stage 2's capacitor, so the passband is clean in the circuit.
	// The OTA saturation is kept on the feedback signal, as in v1.5. (Saturating stage 2's differential
	// input instead was tried and rejected: it detuned self-oscillation by up to +39 cents and let it
	// reach +4 dBFS, for no passband benefit.)
	y = ig * (x - G * s3 + s2) / (1 - K * G * ig);
	u = ig * (K * y - s3);
	u = 0.85 * tanh(u * 1.17647058824);
	l2, n2 = f_op(u - x, s2, G);
	y = x + l2;
	l3, n3 = f_op(K * y, s3, G);
	return y, fixdenorm(s1), fixdenorm(n2), fixdenorm(n3), y;
}

// ================= MODEL 02b: Korg35 (MS-10 / early MS-20, "Mk1") Sallen-Key =================
// v1.6, from Stinchcombe 2006 (Figures 1, 3, 17; sections 2.2, 5, 7). Sallen-Key low-pass with C1 = 3 C2 and
// R1 = R2/3 (the study's assumption; equal section frequencies): 1 / (s^2 + (7/3 - k)s + 1).
// Forward-path X1 stage: gain 1 + 270k/4.7k = 58.45 with back-to-back diodes across 270k, so it is
// v = Vf/57.45 + c sinh(Vf/nVt) with Vo = v + Vf (Fig. 17 fit: nVt = 52 mV, c = 1.617e-5 V).
// Units are volts: x * A is the voltage at the core input (A = 5 V peak per unit x R59/(R57+R59), times
// CHARACTER drive; output makeup follows Drive's level compensation). HP variant (section 7): signal into C2's lifted end, k1 s(s + 4/3) / (same).
// Each sample is one scalar monotone equation in Vf, solved by four step-limited Newton iterations from a
// closed-form start (offline worst relative residual 1.2e-5, about -98 dB; tests/review/ms20/solver.py). returns y, s1, s2, Vf, yprev
f_k35m1(x, s1, s2, s3, yp, g, K0, A, Am, hp) {
	k2 = K0 * 0.0203116;          // (7/6) K0 / 57.4385 (small-signal X1 gain incl. diode leakage, Fig. 17 fit)
	xin = x * A;
	xl = hp > 0.5 ? 0 : xin;
	xh = hp > 0.5 ? xin : 0;
	D = 1 + 1.33333333333 * g;
	E = (1 + g) - g * g / (3 * D);
	Aa = (s2 + xh + g * (s1 + g * xl) / D) / E;
	B = g * k2 / (D * E);
	vt = Aa / (1 - B);
	av = abs(vt);
	V = (vt < 0 ? -1 : 1) * min(av * 57.4468, 0.052 * log(av / 0.00001617 + sqrt(av * av / 0.000000000261469 + 1)));
	for (i = 0; i < 4; i += 1) {
		ex = exp(V * 19.2307692308);
		fv = (1 - B) * (V * 0.0174074 + 0.00001617 * 0.5 * (ex - 1 / ex)) - B * V - Aa;
		dv = (1 - B) * (0.0174074 + 0.000310962 * 0.5 * (ex + 1 / ex)) - B;
		V = V - clamp(fv / dv, -0.05, 0.05);
	}
	ex = exp(V * 19.2307692308);
	v3 = V * 0.0174074 + 0.00001617 * 0.5 * (ex - 1 / ex);
	vo = v3 + V;
	v2 = (s1 + g * xl + 0.333333333333 * g * v3 + k2 * vo) / D;
	n1 = 2 * (v2 - k2 * vo) - s1;
	n2 = 2 * (v3 - xh) - s2;
	y = vo / Am;
	return y, fixdenorm(n1), fixdenorm(n2), V, y;
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
// one linear solve of the Sallen-Key network for given element secants t1, t2 and amp gain Ke
f_stsolve(xl, xb, xh, s1, s2, t1, t2, Ke, g) {
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
	return q1, q2, vA, vB;
}

f_steiner(xl, xb, xh, s1, s2, d1p, d2p, vbp, g, K, rho) {
	// argument: one model unit = the article's 0 dBm input at the LP node (1.1 V pk / 48 = 22.9 mV);
	// V' = 2 n Vt = 98 mV per diode pair, so a = d * 0.233.
	t1 = f_sg(d1p * 0.233, rho);
	t2 = f_sg(d2p * 0.233, rho);
	Ke = K * f_ag(K * vbp * 0.7);
	q1, q2, vA, vB = f_stsolve(xl, xb, xh, s1, s2, t1, t2, Ke, g);
	// v1.6: re-evaluate the diode-string secants and amplifier limit at the current
	// solution (one fixed-point step) - removes the fs/4 overshoot (+30 dBFS) of v1.5.
	t1 = f_sg((xl - vA) * 0.233, rho);
	t2 = f_sg((vA - vB) * 0.233, rho);
	Ke = K * f_ag(K * vB * 0.7);
	q1, q2, vA, vB = f_stsolve(xl, xb, xh, s1, s2, t1, t2, Ke, g);
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
// SEM op-amp / buffer rails: +-13 V = 2.6 units at 5 V/unit, sharp knee (|x| = 0.5 -> error ~1e-7)
f_rail(x) {
	r = x * 0.384615385;
	r = r * r; r = r * r; r = r * r;
	return x / sqrt(sqrt(sqrt(1 + r)));
}

// SEM D11/D12 limiter: extra half-damping 0.5 * 0.926 * smoothmax(0, 0.175 |BP| - 0.45 V) / |BP|, BP in volts (5 V/unit)
f_semd(bp) {
	bv = abs(bp) * 5 + 0.000001;
	ex = 0.175 * bv - 0.45;
	sm = 0.5 * (ex + sqrt(ex * ex + 0.0004)) - 0.000222;      // smooth max(0, ex), exactly 0 at bv = 0
	return 0.463 * max(sm, 0) / bv;
}

f_sem(x, s1, s2, hpp, bpp, g, R, m, hp) {
	// v1.6 (Oberheim SEM-1A schematic): the input summer A12 is a linear op-amp stage (the old 2*tanh(x/2)
	// had no circuit origin). Damping 2R comes from the RES pot (linear) plus the D11/D12 limiter: buffered BP ->
	// 47k/10k (x0.175) -> antiparallel 1N4148 -> 100k into the summer, adding damping once |BP| > ~2.6 V
	// (level reference 5 V per unit). Evaluated at the lagged BP, then re-solved at the current BP.
	u = x;
	g1 = g * f_tg(hpp * 0.6);
	g2 = g * f_tg(bpp * 0.6);
	Rt = R + f_semd(bpp);
	h = (u - (2 * Rt + g2) * s1 - s2) / (1 + 2 * Rt * g1 + g1 * g2);
	b = g1 * h + s1;
	Rt = R + f_semd(b);
	h = f_rail((u - (2 * Rt + g2) * s1 - s2) / (1 + 2 * Rt * g1 + g1 * g2));
	b = f_rail(g1 * h + s1);
	l = f_rail(g2 * b + s2);
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
    dict(id=1, key="k3", name="Korg 35 / MS-20 (OTA Mk2, or KORG-35 Mk1 via K35 Circuit)", taps="12",
         states=["s1", "s2", "s3", "yp"], lp="native", hp="native", char="FB CLIP",
         coef=["{p}_g = {s}_gw;",
               "{p}_K = 0.05 + 2.03 * pow({r}, 1.1);",
               "{p}_L = 4 * exp2(-4 * {c});",
               "{p}_A = 0.0195084 * exp2(4 * {c});",                  # v1.6 Mk1: 5 V peak x 47/12047, +0..24 dB drive
               "{p}_Am = 1.12052 * exp2(2 * {c} * {s}_cmp);"],        # 57.4385 x 0.0195084, makeup = half the drive in dB at full level compensation (as Drive)
         call=["o1 = 0;",
               "if (cur_k35 > 0.5) {{",
               "    o1, {sv} = f_k35m1({x}, {sv}, {p}_g, {p}_K, {p}_A, {p}_Am, {hp});",
               "}} else {{",
               "    o1, {sv} = {k35fn}({x}, {sv}, {p}_g, {p}_K, {p}_L);",
               "}}",
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
               "{p}_kd = 1 / pow({p}_K, {s}_cmp);",
               "{p}_rho = 0.0000590619 * {s}_fcc;"],                 # 2 pi x 4.7 nF x 2k x fc
         call=["o1, {sv} = f_steiner({x} * (1 - {c}) * {lpflag}, {x} * {c}, {x} * (1 - {c}) * {hp}, {sv}, {p}_g, {p}_K, {p}_rho);",
               "{acc} = {acc} + {mix} * o1 * {p}_kd;"]),
    dict(id=4, key="se", name="Oberheim SEM-inspired", taps="12",
         states=["s1", "s2", "hq", "bq"], lp="native", hp="native", char="NOTCH MORPH",
         coef=["{p}_g = {s}_gw;",
               "{p}_R = 0.05 + 1.515 * (1 - {r});"],                 # v1.6: 2R = 0.1 + 3.03 (1 - res): SEM-1A RES pot -> 33k into the 100k summer (linear taper assumed), floor 0.1 = Q 10 (no self-oscillation)
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

# v1.6 minimum oversampling index per model in Reference mode (0 = 1x, 1 = 2x, 2 = 4x),
# from the independent review's factor study (verify.json OS_filters, test C1, target -80 dBc)
# and tests/v16_tests.py for HPF / BPF.
OS_MIN_LP = [1, 1, 2, 2, 0, 1]      # Sherman, K35, Ladder, Steiner, SEM, TB-303
OS_MIN_K35M1_LP = 3                  # v1.6 Korg35 (Mk1) LPF: 8x (4x -76.5, 8x -105.3 dBc at the bright test point)
OS_MIN_K35M1_HP = 2                  # v1.6 Korg35 (Mk1) HPF: 4x (-86.9 dBc)
OS_MIN_HP = [1, 1, 1, 1, 1]         # Sherman, K35, Ladder ALT, Steiner, SEM (HPF at fc 2 kHz: all pass at 2x)
OS_MIN_BPF = [2, 2, 2]              # SVF, CASCADE, MULTIMODE (all about -70 dBc at 2x, < -116 at 4x)
TUBE_OS_MIN_REF = 3                 # TUBE in Reference mode: 8x

def tbl(var, vals):
    """Nested ternary picking vals[i] by the index expression var."""
    e = repr(float(vals[-1]))
    for i in range(len(vals) - 2, -1, -1):
        e = f"({var} < {i + 0.5} ? {float(vals[i])!r} : {e})"
    return e


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
    # v1.3: dynamics chain parameters (appended)
    for (n, d, lo, hi) in dyn.params():
        P(n, d, lo, hi)
    # v1.4: filter routing parameters (appended)
    for (n, d, lo, hi) in routing.params():
        P(n, d, lo, hi)
    # v1.6: engine mode (0 = Reference, 1 = Creative) and high oversampling factors (appended)
    P("eng_mode", 0, 0, 1)
    P("ovs_hi", 0, 0, 3)
    P("k35_circ", 0, 0, 1)   # v1.6: K35 circuit, 0 = LM13600 OTA (Mk2, as v1.5), 1 = Korg35 (Mk1)

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
    dyn_sv = []
    dyn.register_state(lambda n: dyn_sv.append(n), CV)  # v1.3 (after all existing state)
    for v in dyn_sv:
        SV(v)
    routing.register_state(CV)  # v1.4
    for c in CH:  # v1.6: half-band stages 2..4 (4x, 8x, 16x); stage 1 keeps the v1.1 os_* states
        for stg in (2, 3, 4):
            for d in ("up", "dn"):
                for p in ("a", "b"):
                    for z in range(6):
                        SV(f"os_{c}_s{stg}{d}{p}{z}")
    CV("cur_tos", 1)  # v1.6: TUBE oversampling index (1 = 2x, as v1.3-v1.5)
    CV("cur_k35", 0)  # v1.6: K35 circuit in use (switches at the duck bottom)

    dirty = []   # v1.6 has-state flags (stored at the end)

    def lazy_cond(v):
        """v1.6: half-band states of stages 2..4 are loaded / stored only while that stage is in use."""
        import re as _re
        mm = _re.match(r"os_[LR]_s(\d)", v)
        if mm:
            return f"cur_os > {int(mm.group(1)) - 0.5}"
        mm = _re.match(r"d[PQ]_T_[LR]_s(\d)", v)
        if mm:
            return f"cur_tos > {int(mm.group(1)) - 0.5}"
        return None
    # ======================= main body ==========================
    w = G.w
    w("// ======================= MAIN =======================")
    w("fs = samplerate;")
    w("cur_order = H_cur_order;")
    w("cur_os = H_cur_os;")
    w("cur_tos = H_cur_tos;")
    w("cur_k35 = H_cur_k35;")
    w("ovs = cur_os < 0.5 ? 1 : (cur_os < 1.5 ? 2 : (cur_os < 2.5 ? 4 : (cur_os < 3.5 ? 8 : 16)));")
    w("fso = fs * ovs;")
    w("a_cut = 1 - exp(-1 / (0.006 * fs));")
    w("a_par = 1 - exp(-1 / (0.015 * fs));")
    w("a_mix = 1 - exp(-1 / (0.010 * fs));")
    w("fstep = 1 / (0.025 * fs);")
    w("dstep = 1 / (0.004 * fs);")
    w("x_L = in1;")
    w("x_R = in2;")
    w("fault = 0;")
    w()
    w("// ---- load state ----")
    groups = {}
    for v in statevars:
        c = lazy_cond(v)
        if c is None:
            w(f"{v} = H_{v};")
        else:
            w(f"{v} = 0;")
            groups.setdefault(c, []).append(v)
    for c, vs in groups.items():
        w(f"if ({c}) {{")
        for v in vs:
            w(f"\t{v} = H_{v};")
        w("}")
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
        # reset inactive model state (v1.6: once, when it holds state - bit-exact with v1.5)
        for m in mods:
            k = m["key"]
            dz = f"{s}_dz{k}"
            G.H("H_" + dz, 0.0); dirty.append(dz)
            w(f"{dz} = H_{dz};")
            w(f"if ({s}_a{k} < 0.5 && {dz} > 0.5) {{")
            G.ind += 1
            for ch in CH:
                for v in m["states"]:
                    w(f"{s}_{ch}_{k}_{v} = 0;")
            w(f"{dz} = 0;")
            G.ind -= 1
            w("}")
            w(f"if ({s}_a{k} > 0.5) {{")
            w(f"\t{dz} = 1;")
            w("}")
        for e, flag in enumerate(("xa", "xb", "xc")):
            dz = f"{s}_dzx{e}"
            G.H("H_" + dz, 0.0); dirty.append(dz)
            w(f"{dz} = H_{dz};")
            w(f"if (({s}_{flag} < 0.5 || {s}_run < 0.5) && {dz} > 0.5) {{")
            G.ind += 1
            for ch in CH:
                w(f"{s}_{ch}_x{e}_s1 = 0;")
                w(f"{s}_{ch}_x{e}_s2 = 0;")
            w(f"{dz} = 0;")
            G.ind -= 1
            w("}")
            w(f"if ({s}_{flag} > 0.5 && {s}_run > 0.5) {{")
            w(f"\t{dz} = 1;")
            w("}")
        w()

    bpf.emit_controls(w, G)
    routing.emit_controls(w)  # v1.4

    # ---- duck / config switching ----
    w("// ================= order / oversampling switching (duck) =================")
    w("cfg_o = order_sel > 0.5 ? 1 : 0;")
    # v1.6 oversampling policy (docs/independent-review/DSP_ARCHITECTURE_RECOMMENDATIONS.md 2.1):
    # index 0..4 = 1x, 2x, 4x, 8x, 16x. Creative: the user's setting. Reference: at least the
    # measured minimum of every active model (<= -80 dBc aliasing at the bright test point).
    w("os_user = ovs_hi > 0.5 ? clamp(floor(ovs_hi + 0.5), 1, 3) + 1 : (ovs_sel > 0.5 ? 1 : 0);")
    w("ref_mode = eng_mode < 0.5 ? 1 : 0;")
    w("cfg_k = k35_circ > 0.5 ? 1 : 0;")
    w(f"os_ml = l_on > 0.5 ? ((cfg_k > 0.5 && abs(l_model - 1) < 0.5) ? {OS_MIN_K35M1_LP} : {tbl('clamp(floor(l_model + 0.5), 0, 5)', OS_MIN_LP)}) : 0;")
    w(f"os_mh = h_on > 0.5 ? ((cfg_k > 0.5 && abs(h_model - 1) < 0.5) ? {OS_MIN_K35M1_HP} : {tbl('clamp(floor(h_model + 0.5), 0, 4)', OS_MIN_HP)}) : 0;")
    w(f"os_mb = b_on > 0.5 ? {tbl('clamp(floor(b_arch + 0.5), 0, 2)', OS_MIN_BPF)} : 0;")
    w("cfg_s = ref_mode > 0.5 ? max(os_user, max(os_ml, max(os_mh, os_mb))) : os_user;")
    w(f"cfg_t = ref_mode > 0.5 ? max(os_user, {TUBE_OS_MIN_REF}) : max(os_user, 1);")
    w("cfg_p = b_pos > 0.5 ? 1 : 0;")
    w("b_cur_pos = H_b_cur_pos;")
    w("pend = (cfg_o != cur_order || cfg_s != cur_os || cfg_p != b_cur_pos || cfg_r != cur_route || cfg_t != cur_tos || cfg_k != cur_k35) ? 1 : 0;")
    w("duck = H_duck;")
    w("duck = pend > 0.5 ? max(0, duck - dstep) : min(1, duck + dstep);")
    w("new_order = cur_order;")
    w("new_os = cur_os;")
    w("new_pos = b_cur_pos;")
    w("new_route = cur_route;")
    w("new_tos = cur_tos;")
    w("new_k35 = cur_k35;")
    w("rst = 0;")
    w("if (pend > 0.5 && duck <= 0) {")
    w("\tnew_order = cfg_o;")
    w("\tnew_os = cfg_s;")
    w("\tnew_pos = cfg_p;")
    w("\tnew_route = cfg_r;")
    w("\tnew_tos = cfg_t;")
    w("\tnew_k35 = cfg_k;")
    w("\trst = (cfg_s != cur_os || cfg_t != cur_tos || cfg_k != cur_k35) ? 1 : 0;")
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
            # v1.6 fault containment (defence in depth; never active in normal operation):
            # a non-finite or absurd stage output resets that stage's model state for this channel
            w(f"flt_bad = abs(wet_{ch}) < 1000000 ? 0 : 1;")
            w("if (flt_bad > 0.5) {")
            G.ind += 1
            for m in mods:
                for v in m["states"]:
                    w(f"{s}_{ch}_{m['key']}_{v} = 0;")
            for e in range(3):
                w(f"{s}_{ch}_x{e}_s1 = 0;")
                w(f"{s}_{ch}_x{e}_s2 = 0;")
            w(f"wet_{ch} = {xin};")
            w("fault = 1;")
            G.ind -= 1
            w("}")
            w(f"{s}y{sub}_{ch} = {xin} + {s}_wet * (wet_{ch} - {xin});")
        G.ind -= 1
        w("}")

    # ---- oversampling (v1.6): cascade of the v1.1 half-band to 2x / 4x / 8x / 16x ----
    ca = HIIR[0::2]; cb = HIIR[1::2]
    ca_s = ", ".join(repr(round(v, 15)) for v in ca)
    cb_s = ", ".join(repr(round(v, 15)) for v in cb)
    NMAX = 16

    def stz(ch, stg, d, p):
        if stg == 1:
            return [f"os_{ch}_{d}{p}{z}" for z in range(6)]
        return [f"os_{ch}_s{stg}{d}{p}{z}" for z in range(6)]

    w("// ================= input: up-sampling cascade (v1.6) =================")
    for ch in CH:
        for k in range(NMAX):
            w(f"u{k}_{ch} = 0;")
            w(f"wo{k}_{ch} = 0;")
        w(f"u0_{ch} = x_{ch};")
    for ch in CH:
        # level L holds 2^L values u0..; built in place from the previous level, stage by stage
        for stg in (1, 2, 3, 4):
            w(f"if (ovs > {2 ** (stg - 1) + 0.5}) {{")
            G.ind += 1
            n_in = 2 ** (stg - 1)
            za, zb = stz(ch, stg, "up", "a"), stz(ch, stg, "up", "b")
            # compute outputs from the current level first (temporaries), then write the new level
            for j in range(n_in):
                w(f"q{2 * j}, {', '.join(za)} = f_ap5(u{j}_{ch}, {', '.join(za)}, {ca_s});")
                w(f"q{2 * j + 1}, {', '.join(zb)} = f_ap5(u{j}_{ch}, {', '.join(zb)}, {cb_s});")
                w(f"u{2 * j}_t{stg}_{ch} = q{2 * j};")
                w(f"u{2 * j + 1}_t{stg}_{ch} = q{2 * j + 1};")
            for j in range(2 * n_in):
                w(f"u{j}_{ch} = u{j}_t{stg}_{ch};")
            G.ind -= 1
            w("}")
    w()

    lst, hst = STAGES
    w(f"// ================= filter section: one pass per sub-sample (ovs = 1..{NMAX}) =================")
    w("for (k = 0; k < ovs; k += 1) {")
    G.ind += 1
    sub = "a"
    for ch in CH:
        sel = f"u{NMAX - 1}_{ch}"
        for k in range(NMAX - 2, -1, -1):
            sel = f"(k < {k + 0.5} ? u{k}_{ch} : {sel})"
        w(f"x{sub}_{ch} = {sel};")
    w("if (b_cur_pos > 0.5 && cur_route < 0.5) {")  # v1.2: BPF before the LPF/HPF chain (v1.4: SERIES only)
    G.ind += 1
    bpf.emit_process(w, G, {ch: f"x{sub}_{ch}" for ch in CH}, {ch: f"x{sub}_{ch}" for ch in CH})
    G.ind -= 1
    w("}")
    for ch in CH:
        w(f"hy{sub}_{ch} = 0;")
    w("if (cur_order > 0.5 && r_par < 0.5) {")  # v1.4: PARALLEL feeds the HPF below from the input
    G.ind += 1
    emit_stage(hst, sub, {ch: f"x{sub}_{ch}" for ch in CH})
    G.ind -= 1
    w("}")
    for ch in CH:
        w(f"lsrc_{ch} = (cur_order > 0.5 && r_par < 0.5) ? hy{sub}_{ch} : x{sub}_{ch};")
    emit_stage(lst, sub, {ch: f"lsrc_{ch}" for ch in CH})
    for ch in CH:
        w(f"z{sub}_{ch} = ly{sub}_{ch};")
    for ch in CH:
        w(f"hsrc_{ch} = r_par > 0.5 ? x{sub}_{ch} : ly{sub}_{ch};")
    w("if (cur_order < 0.5 || r_par > 0.5) {")
    G.ind += 1
    emit_stage(hst, sub, {ch: f"hsrc_{ch}" for ch in CH})
    for ch in CH:
        w(f"z{sub}_{ch} = hy{sub}_{ch};")
    G.ind -= 1
    w("}")
    routing.emit_combine(w, G, sub, bpf.emit_process)  # v1.4: PARALLEL sum / HYBRID add
    w("if (b_cur_pos < 0.5 && cur_route < 0.5) {")  # v1.2: BPF after the LPF/HPF chain (default; v1.4: SERIES only)
    G.ind += 1
    bpf.emit_process(w, G, {ch: f"z{sub}_{ch}" for ch in CH}, {ch: f"z{sub}_{ch}" for ch in CH})
    G.ind -= 1
    w("}")
    # store this sub-sample's output
    for k in range(NMAX):
        w(("if" if k == 0 else "} else if") + f" (k < {k + 0.5}) {{")
        G.ind += 1
        for ch in CH:
            w(f"wo{k}_{ch} = z{sub}_{ch};")
        G.ind -= 1
    w("}")
    G.ind -= 1
    w("}")
    w()

    # ---- down-sampling cascade ----
    w("// ================= output: down-sampling cascade (v1.6) =================")
    for ch in CH:
        w(f"y_{ch} = wo0_{ch};")
    for n_os in (2, 4, 8, 16):
        w(f"if (ovs > {n_os / 2 + 0.5} && ovs < {n_os + 0.5}) {{")
        G.ind += 1
        for ch in CH:
            vals = [f"wo{k}_{ch}" for k in range(n_os)]
            stg = n_os.bit_length() - 1      # highest stage index used
            while len(vals) > 1:
                za, zb = stz(ch, stg, "dn", "a"), stz(ch, stg, "dn", "b")
                nxt = []
                for j in range(len(vals) // 2):
                    w(f"pa, {', '.join(za)} = f_ap5({vals[2 * j + 1]}, {', '.join(za)}, {ca_s});")
                    w(f"pb, {', '.join(zb)} = f_ap5({vals[2 * j]}, {', '.join(zb)}, {cb_s});")
                    nm = f"d{stg}_{j}_{ch}"
                    w(f"{nm} = 0.5 * (pa + pb);")
                    nxt.append(nm)
                vals = nxt
                stg -= 1
            w(f"y_{ch} = {vals[0]};")
        G.ind -= 1
        w("}")
    w()
    dyn.emit_chain(w, G, {"L": "y_L", "R": "y_R"}, {"L": "y_L", "R": "y_R"})  # v1.3
    w()
    w("// ---- DC blocker (1st order, 2 Hz), output gain, soft clip, duck ----")
    w("dcr = 1 - 2 * pi * 2 / fs;")
    w("og = H_og + a_par * (exp(0.11512925465 * clamp(out_db, -24, 12)) - H_og);")
    for ch in CH:
        # v1.6: never let a non-finite / absurd value into the output DC blocker's memory
        w(f"if (abs(y_{ch}) < 1000000 && abs(dc_{ch}_y) < 1000000) {{")
        w("} else {")
        w(f"\ty_{ch} = 0;")
        w(f"\tdc_{ch}_x = 0;")
        w(f"\tdc_{ch}_y = 0;")
        w("\tfault = 1;")
        w("}")
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
    dyn.emit_outputs(w)  # v1.3 meter outlets out3..out14
    w("out15 = ovs;")       # v1.6: effective filter oversampling factor
    w("out16 = t_nf;")      # v1.6: effective TUBE oversampling factor
    w("out17 = fault;")     # v1.6: 1 on a sample where fault containment acted
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
    groups = {}
    for v in statevars:
        c = lazy_cond(v)
        if c is None:
            w(f"H_{v} = {v};")
        else:
            groups.setdefault(c, []).append(v)
    for c, vs in groups.items():
        w(f"if ({c} || rst > 0.5) {{")
        for v in vs:
            w(f"\tH_{v} = {v};")
        w("}")
    for v in dirty:
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
    w("H_cur_route = new_route;")
    w("H_cur_tos = new_tos;")
    w("H_cur_k35 = new_k35;")
    for n in routing.ctrl_names():
        w(f"H_{n} = {n};")
    for n in dyn.ctrl_names():
        w(f"H_{n} = {n};")

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
    out.append(dyn.LIB)
    out.extend(G.lines)
    return "\n".join(out) + "\n", params


if __name__ == "__main__":
    code, params = build()
    dst = os.path.join(HERE, "..", "build", "dubfilter.genexpr")
    with open(dst, "w") as f:
        f.write(code)
    print("wrote", dst, len(code.splitlines()), "lines")
