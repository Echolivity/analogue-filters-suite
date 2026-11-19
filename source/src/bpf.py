"""Band-pass filter engine (v1.2) — GenExpr library + code emitters.

Kept in its own module so the LPF/HPF generator is only touched at a few
insertion hooks. With BPF off (the default) none of this code changes a single
sample of the LPF/HPF signal path (verified bit-exact by tests/golden.py).

ARCHITECTURES (topology)                   MODELS (analogue character)
  0 SVF       2-pole state-variable BP      0 Oberheim SEM     OTA integrators
  1 CASCADE   2-pole HP -> 2-pole LP        1 Steiner-Parker   diode-string resistors + clipping amp
  2 MULTIMODE 4-pole ladder core, pole-mix  2 Korg 35 / MS-20  transconductor stages, diode-limited feedback
                                            3 ARP 2600         transistor-pair stages, 4072 HF roll-off
                                            4 EMS VCS3         diode-rung stages (Civolani-Fontana)

Architecture decides the transfer function; the model decides which nonlinear
element sits in each integrator/stage, how resonance regenerates and limits,
and model-specific documented traits (ARP 4072 roll-off). A model's "native"
architecture is the one its hardware actually uses (see docs/BPF.md).
"""

BPF_MODELS = [
    # name, element type (0 = difference-type: OTA/diode/transconductor, 1 = separate-type: transistor pairs),
    # element scale, regeneration saturator (0 tanh, 1 hard-knee amplifier clip), max regeneration r,
    # max ladder k, ARP 4072 roll-off, native architecture
    dict(name="Oberheim SEM", typ=0, sc=0.6, rg=0, rmax=0.9, kmax=3.6, roll=0, native=0),
    dict(name="Steiner-Parker", typ=0, sc=0.7, rg=1, rmax=1.06, kmax=4.3, roll=0, native=0),
    dict(name="Korg 35 / MS-20", typ=0, sc=1.0, rg=0, rmax=1.06, kmax=4.3, roll=0, native=1),
    dict(name="ARP 2600", typ=1, sc=1.4, rg=0, rmax=1.06, kmax=4.3, roll=1, native=None),
    dict(name="EMS VCS3", typ=0, sc=0.5, rg=0, rmax=1.06, kmax=4.3, roll=0, native=None),
]
ARCHS = ["SVF", "CASCADE", "MULTIMODE"]
CH = ["L", "R"]
SLOTS = ["A", "B"]
SLOT_STATES = (["yp", "ro"] +                                 # regeneration memory, ARP roll-off state
               ["v_s1", "v_s2", "v_hq", "v_bq"] +            # SVF section
               ["c_s1", "c_s2", "c_hq", "c_bq", "c_t1", "c_t2", "c_tq", "c_tb"] +  # cascade HP + LP sections
               ["m_s1", "m_s2", "m_s3", "m_s4", "m_p0", "m_p1", "m_p2", "m_p3", "m_p4"])  # multimode core

PARAMS = [
    ("b_on", 0, 0, 1), ("b_model", 0, 0, 4), ("b_arch", 0, 0, 2), ("b_freq", 1000, 30, 12000),
    ("b_bw", 2, 0.2, 6), ("b_q", 0.707, 0.5, 10), ("b_res", 0, 0, 100), ("b_drive", 0, 0, 100),
    ("b_comp", 100, 0, 100), ("b_mix", 100, 0, 100), ("b_pos", 0, 0, 1),
]

LIB = r"""
// ======================= BAND-PASS ENGINE (v1.2) =======================
// Secant gain of the model's nonlinear element (rg selects the curve):
//   0: tanh (OTA, transistor pair, diode pair)   1: hard-knee amplifier clip
f_bsat(v, rg) {
	return rg > 0.5 ? f_ag(v) : f_tg(v);
}

// SVF section with saturating integrators (element secants from the previous
// sample's integrator inputs). Affine form: every output = a * x + b for the
// current sample, used to solve the regeneration loop with zero delay.
// returns ah, bh, ab, bb, al, bl
f_bsva(s1, s2, hq, bq, g, R, sc) {
	g1 = g * f_tg(sc * hq);
	g2 = g * f_tg(sc * bq);
	iD = 1 / (1 + 2 * R * g1 + g1 * g2);
	bh = -((2 * R + g2) * s1 + s2) * iD;
	ab = g1 * iD;
	bb = g1 * bh + s1;
	return iD, bh, ab, bb, g2 * ab, g2 * bb + s2;
}

// same section, state update for a known input. returns h, b, l, s1, s2
f_bsvs(x, s1, s2, hq, bq, g, R, sc) {
	g1 = g * f_tg(sc * hq);
	g2 = g * f_tg(sc * bq);
	h = (x - (2 * R + g2) * s1 - s2) / (1 + 2 * R * g1 + g1 * g2);
	b = g1 * h + s1;
	l = g2 * b + s2;
	return h, b, l, fixdenorm(2 * b - s1), fixdenorm(2 * l - s2);
}

// 4-pole ladder core (MULTIMODE). Element type typ: 0 = difference-type
// (dy/dt = w f(in - y): OTA / diode rung / transconductor), 1 = separate-type
// (dy/dt = w (f(in) - f(y)): transistor differential pairs). Global feedback
// u = x - k*y4 solved with zero delay; band-pass by pole mixing:
//   BP4 = 4 (y2 - 2 y3 + y4) = 4 s^2 / ((1+s)^4 + k)      (narrow, 12 dB/oct skirts)
//   BP2 = 2 (y1 - y2)        = 2 s (1+s)^2 / ((1+s)^4 + k) (wide, 6 dB/oct skirts)
// wb crossfades BP4 -> BP2. returns y, s1..s4, p0..p4
f_bmm(x, s1, s2, s3, s4, p0, p1, p2, p3, p4, g, k, typ, sc, wb) {
	d1 = f_tg(sc * (p0 - p1));
	d2 = f_tg(sc * (p1 - p2));
	d3 = f_tg(sc * (p2 - p3));
	d4 = f_tg(sc * (p3 - p4));
	ti1 = typ > 0.5 ? f_tg(sc * p0) : d1;
	ti2 = typ > 0.5 ? f_tg(sc * p1) : d2;
	ti3 = typ > 0.5 ? f_tg(sc * p2) : d3;
	ti4 = typ > 0.5 ? f_tg(sc * p3) : d4;
	to1 = typ > 0.5 ? f_tg(sc * p1) : d1;
	to2 = typ > 0.5 ? f_tg(sc * p2) : d2;
	to3 = typ > 0.5 ? f_tg(sc * p3) : d3;
	to4 = typ > 0.5 ? f_tg(sc * p4) : d4;
	i1 = 1 / (1 + g * to1);
	i2 = 1 / (1 + g * to2);
	i3 = 1 / (1 + g * to3);
	i4 = 1 / (1 + g * to4);
	G1 = g * ti1 * i1;
	G2 = g * ti2 * i2;
	G3 = g * ti3 * i3;
	G4 = g * ti4 * i4;
	S = G2 * G3 * G4 * s1 * i1 + G3 * G4 * s2 * i2 + G4 * s3 * i3 + s4 * i4;
	u = (x - k * S) / (1 + k * G1 * G2 * G3 * G4);
	u = 0.35 * tanh(u * 2.857142857);
	y1 = G1 * u + s1 * i1;
	y2 = G2 * y1 + s2 * i2;
	y3 = G3 * y2 + s3 * i3;
	y4 = G4 * y3 + s4 * i4;
	bp4 = 4 * (y2 - 2 * y3 + y4);
	bp2 = 2 * (y1 - y2);
	y = bp4 + wb * (bp2 - bp4);
	return y, fixdenorm(2 * y1 - s1), fixdenorm(2 * y2 - s2), fixdenorm(2 * y3 - s3), fixdenorm(2 * y4 - s4), u, y1, y2, y3, y4;
}

// analogue magnitude of a 2-pole HP (hp=1) or LP (hp=0) at normalised frequency rho
f_bmag(rho, Q, hp) {
	m = 1 / sqrt((1 - rho * rho) * (1 - rho * rho) + rho * rho / (Q * Q));
	return hp > 0.5 ? m * rho * rho : m;
}
"""


def params():
    return PARAMS


def register_state(SV, CV):
    for sl in SLOTS:
        for ch in CH:
            for v in SLOT_STATES:
                SV(f"b{sl}_{ch}_{v}")
    CV("b_lc", 9.965784284662087)
    for n, i in (("bwz", 2.0), ("lq", -0.5), ("rz", 0.0), ("drv", 0.0), ("cmp", 1.0), ("mx", 1.0), ("en", 0.0)):
        CV(f"b_{n}", i)
    for n, i in (("ca", 0), ("cb", 0), ("act", 0), ("fade", 1), ("cur_pos", 0)):
        CV(f"b_{n}", i)
    CV("bA_dz", 0)   # v1.6 slot-has-state flags
    CV("bB_dz", 0)


def ctrl_names():
    return ["bA_dz", "bB_dz", "b_lc", "b_bwz", "b_lq", "b_rz", "b_drv", "b_cmp", "b_mx", "b_en", "b_ca", "b_cb", "b_act", "b_fade"]


def model_table(field, idx):
    """Nested ternary selecting a per-model constant by model index expression."""
    vals = [m[field] for m in BPF_MODELS]
    expr = repr(float(vals[-1]))
    for i in range(len(vals) - 2, -1, -1):
        expr = f"({idx} < {i + 0.5} ? {float(vals[i])!r} : {expr})"
    return expr


def emit_controls(w, G):
    w("// ================= BPF controls (v1.2) =================")
    w("b_lc = H_b_lc + a_cut * (log2(clamp(b_freq, 30, 12000)) - H_b_lc);")
    w("b_bwz = H_b_bwz + a_par * (clamp(b_bw, 0.2, 6) - H_b_bwz);")
    w("b_lq = H_b_lq + a_par * (log2(clamp(b_q, 0.5, 10)) - H_b_lq);")
    w("b_rz = H_b_rz + a_par * (clamp(b_res, 0, 100) * 0.01 - H_b_rz);")
    w("b_drv = H_b_drv + a_par * (clamp(b_drive, 0, 100) * 0.01 - H_b_drv);")
    w("b_cmp = H_b_cmp + a_par * (clamp(b_comp, 0, 100) * 0.01 - H_b_cmp);")
    w("b_mxt = clamp(b_mix, 0, 100) * 0.01;")
    w("b_mx = H_b_mx + a_mix * (b_mxt - H_b_mx);")
    w("if (abs(b_mx - b_mxt) < 0.0001 && (b_mxt < 0.0001 || b_mxt > 0.9999)) {")
    w("\tb_mx = b_mxt;")
    w("}")
    w("b_ent = b_on > 0.5 ? 1 : 0;")
    w("b_en = H_b_en + a_mix * (b_ent - H_b_en);")
    w("if (b_ent < 0.5 && b_en < 0.0001) {")
    w("\tb_en = 0;")
    w("}")
    w("if (b_ent > 0.5 && b_en > 0.9999) {")
    w("\tb_en = 1;")
    w("}")
    w("b_wet = b_en * b_mx;")
    w("b_run = b_en > 0 ? 1 : 0;")
    w("b_fc = min(ef_rb != 0 ? clamp(exp2(b_lc + ef_rb), 30, 12000) : exp2(b_lc), 0.45 * fso);")  # v1.6 envelope routing
    w("b_qq = exp2(b_lq);")
    w("b_d = 0.25 * exp2(5 * b_drv);")
    w("b_osc = (1 / b_d) * exp2(5 * b_drv * (1 - 0.5 * b_cmp));")
    # configuration slots
    w("b_cfg = clamp(floor(b_model + 0.5), 0, 4) * 3 + clamp(floor(b_arch + 0.5), 0, 2);")
    w("b_ca = H_b_ca;")
    w("b_cb = H_b_cb;")
    w("b_act = H_b_act;")
    w("b_fade = H_b_fade;")
    w("b_ccur = b_act < 0.5 ? b_ca : b_cb;")
    w("b_newA = 0;")
    w("b_newB = 0;")
    w("if (b_cfg != b_ccur) {")
    w("\tif (b_act < 0.5) {")
    w("\t\tb_cb = b_cfg;")
    w("\t\tb_act = 1;")
    w("\t\tb_newB = 1;")
    w("\t} else {")
    w("\t\tb_ca = b_cfg;")
    w("\t\tb_act = 0;")
    w("\t\tb_newA = 1;")
    w("\t}")
    w("\tb_fade = 0;")
    w("}")
    w("b_fade = min(1, b_fade + fstep);")
    w("b_wA = b_act < 0.5 ? b_fade : 1 - b_fade;")
    w("b_wB = 1 - b_wA;")
    for sl in SLOTS:
        cfg = f"b_c{sl.lower()}"
        p = f"b{sl}"
        w(f"// slot {sl}: per-slot coefficients")
        w(f"{p}_run = (b_run > 0.5 && b_w{sl} > 0) ? 1 : 0;")
        w(f"{p}_m = floor({cfg} / 3 + 0.001);")
        w(f"{p}_a = {cfg} - 3 * {p}_m;")
        w(f"{p}_typ = {model_table('typ', p + '_m')};")
        w(f"{p}_sc = {model_table('sc', p + '_m')};")
        w(f"{p}_rg = {model_table('rg', p + '_m')};")
        w(f"{p}_r = {model_table('rmax', p + '_m')} * pow(b_rz, 1.3);")
        w(f"{p}_k = {model_table('kmax', p + '_m')} * pow(b_rz, 1.3);")
        w(f"{p}_roll = {model_table('roll', p + '_m')};")
        w(f"{p}_gc = tan(pi * b_fc / fso);")
        w(f"{p}_R = 0.5 / b_qq;")
        w(f"{p}_fh = clamp(b_fc * exp2(-0.5 * b_bwz), 10, 0.45 * fso);")
        w(f"{p}_fl = clamp(b_fc * exp2(0.5 * b_bwz), 10, 0.45 * fso);")
        w(f"{p}_gh = tan(pi * {p}_fh / fso);")
        w(f"{p}_gl = tan(pi * {p}_fl / fso);")
        w(f"{p}_cn = 1 / (f_bmag({p}_gc / {p}_gh, b_qq, 1) * f_bmag({p}_gc / {p}_gl, b_qq, 0));")
        w(f"{p}_wb = clamp((b_bwz - 1) * 0.5, 0, 1);")
        # multimode: the ladder feedback shifts the -3 dB band centre (0.90 w at k~1.4,
        # 1.01 w at k=4.3); 5th-order fit of the analytic band centre (max error 0.2 %)
        w(f"{p}_kk = min({p}_k, 4.3);")
        w(f"{p}_cmm = ((((0.000804 * {p}_kk - 0.009901) * {p}_kk + 0.039923) * {p}_kk - 0.03441) * {p}_kk - 0.07288) * {p}_kk + 0.998285;")
        w(f"{p}_gm = {p}_gc / {p}_cmm;")
        # raw (uncompensated) circuit gain at the centre: SVF Q, cascade 1/cn, multimode taps unity
        w(f"{p}_raw = {p}_a < 0.5 ? b_qq : ({p}_a < 1.5 ? 1 / {p}_cn : 1);")
        w(f"{p}_ocmp = pow({p}_raw, 1 - b_cmp);")
        w(f"{p}_gro = tan(pi * min(14000, 0.45 * fso) / fso);")
        w(f"{p}_Gro = {p}_gro / (1 + {p}_gro);")
        # v1.6: clear the slot only when it holds state (bit-exact with clearing every sample)
        w(f"{p}_dz = H_{p}_dz;")
        w(f"if (({p}_run < 0.5 && {p}_dz > 0.5) || b_new{sl} > 0.5) {{")
        G.ind += 1
        for ch in CH:
            for v in SLOT_STATES:
                w(f"{p}_{ch}_{v} = 0;")
        w(f"{p}_dz = 0;")
        G.ind -= 1
        w("}")
        w(f"if ({p}_run > 0.5) {{")
        w(f"\t{p}_dz = 1;")
        w("}")
    w()


def emit_slot(w, G, sl, ch, xin, yout):
    p = f"b{sl}"
    s = lambda v: f"{p}_{ch}_{v}"
    w(f"if ({p}_run > 0.5) {{")
    G.ind += 1
    w(f"bx = {xin} * b_d;")
    w(f"by = 0;")
    w(f"bt = f_bsat({s('yp')} * 3.3333333333, {p}_rg);")
    # --- SVF ---
    w(f"if ({p}_a < 0.5) {{")
    G.ind += 1
    sv = [s("v_s1"), s("v_s2"), s("v_hq"), s("v_bq")]
    w(f"ah, bh, ab, bb, al, bl = f_bsva({', '.join(sv)}, {p}_gc, {p}_R, {p}_sc);")
    w(f"nA = 2 * {p}_R * ab;")
    w(f"nB = 2 * {p}_R * bb;")
    w(f"bu = (bx + {p}_r * bt * nB) / (1 - {p}_r * bt * nA);")
    # v1.6: re-evaluate the regeneration limiter at the current band estimate (one fixed-point
    # step; the lagged value overshoots to about +33 dBFS at fc near fs/4, tests/v16_tests.py)
    w(f"bt = f_bsat((nA * bu + nB) * 3.3333333333, {p}_rg);")
    w(f"bu = (bx + {p}_r * bt * nB) / (1 - {p}_r * bt * nA);")
    w(f"hh, b1, l1, {sv[0]}, {sv[1]} = f_bsvs(bu, {', '.join(sv)}, {p}_gc, {p}_R, {p}_sc);")
    w(f"{sv[2]} = hh;")
    w(f"{sv[3]} = b1;")
    w(f"by = 2 * {p}_R * b1;")
    G.ind -= 1
    w("}")
    # --- CASCADE ---
    w(f"if ({p}_a > 0.5 && {p}_a < 1.5) {{")
    G.ind += 1
    c1 = [s("c_s1"), s("c_s2"), s("c_hq"), s("c_bq")]
    c2 = [s("c_t1"), s("c_t2"), s("c_tq"), s("c_tb")]
    w(f"ah, bh, ab, bb, al, bl = f_bsva({', '.join(c1)}, {p}_gh, {p}_R, {p}_sc);")
    w(f"ah2, bh2, ab2, bb2, al2, bl2 = f_bsva({', '.join(c2)}, {p}_gl, {p}_R, {p}_sc);")
    w(f"nA = {p}_cn * al2 * ah;")
    w(f"nB = {p}_cn * (al2 * bh + bl2);")
    w(f"bu = (bx + {p}_r * bt * nB) / (1 - {p}_r * bt * nA);")
    w(f"hh, b1, l1, {c1[0]}, {c1[1]} = f_bsvs(bu, {', '.join(c1)}, {p}_gh, {p}_R, {p}_sc);")
    w(f"{c1[2]} = hh;")
    w(f"{c1[3]} = b1;")
    w(f"hh2, b2, l2, {c2[0]}, {c2[1]} = f_bsvs(hh, {', '.join(c2)}, {p}_gl, {p}_R, {p}_sc);")
    w(f"{c2[2]} = hh2;")
    w(f"{c2[3]} = b2;")
    w(f"by = {p}_cn * l2;")
    G.ind -= 1
    w("}")
    # --- MULTIMODE ---
    w(f"if ({p}_a > 1.5) {{")
    G.ind += 1
    mm = [s(v) for v in ("m_s1", "m_s2", "m_s3", "m_s4", "m_p0", "m_p1", "m_p2", "m_p3", "m_p4")]
    w(f"by, {', '.join(mm)} = f_bmm(bx, {', '.join(mm)}, {p}_gm, {p}_k, {p}_typ, {p}_sc, {p}_wb);")
    G.ind -= 1
    w("}")
    w(f"{s('yp')} = by;")
    # ARP 4072 HF roll-off
    w(f"if ({p}_roll > 0.5) {{")
    G.ind += 1
    w(f"by, {s('ro')} = f_op(by, {s('ro')}, {p}_Gro);")
    w(f"{s('ro')} = fixdenorm({s('ro')});")
    G.ind -= 1
    w("}")
    w(f"{yout} = {yout} + b_w{sl} * by * {p}_ocmp * b_osc;")
    G.ind -= 1
    w("}")


def emit_process(w, G, src, dst):
    """BPF on src[ch] -> dst[ch]. Leaves dst untouched (bit-exact) when the BPF is not running."""
    w("if (b_run > 0.5) {")
    G.ind += 1
    for ch in CH:
        w(f"bo_{ch} = 0;")
        for sl in SLOTS:
            emit_slot(w, G, sl, ch, src[ch], f"bo_{ch}")
        w(f"bbad = abs(bo_{ch}) < 1000000 ? 0 : 1;")   # v1.6 fault containment
        w("if (bbad > 0.5) {")
        G.ind += 1
        for sl in SLOTS:
            for v in SLOT_STATES:
                w(f"b{sl}_{ch}_{v} = 0;")
        w(f"bo_{ch} = {src[ch]};")
        w("fault = 1;")
        G.ind -= 1
        w("}")
        w(f"{dst[ch]} = {src[ch]} + b_wet * (bo_{ch} - {src[ch]});")
    G.ind -= 1
    w("}")
