"""v1.6 envelope filter (Mu-Tron III topology) and envelope routing to the LPF / HPF / BPF cutoffs.

Topology from M. L. Beigel, US patent 3,911,776 (1975), "Sound effects generator" (Musitronics):
  preamp (gain, op-amp rails) -> precision half-wave rectifier -> RC smoothing (fast attack through a small
  resistor, slow decay through a large one) -> voltage-to-current converter driving ONE LED that lights the
  two photoresistors of a two-integrator second-order filter (LP / BP / HP taken from the three nodes; Q set
  by a variable resistor, gain proportional to Q). DOWN subtracts the envelope from a reference (and doubles
  the rectifier gain). RANGE adds a capacitor across each integrator.

Values: integrator capacitors 1.8 nF, +2.2 nF in LO, Peak pot 150 k audio (R. G. Keen, Neutron, a Mu-tron III
work-alike). EVERY OTHER CONSTANT IS AN ASSUMPTION (no production schematic was available):
  - 1 model unit = 1 V at the Mu-tron input; op-amp rails +/-7.5 V (RC4558 on +/-9 V);
  - LDR: conductance proportional to light^0.8, 10 k at an envelope of 1 V, on/off lags 2.5 / 35 ms
    (VTL5C3-like; the original used a Hamamatsu dual-LDR whose data is not available);
  - 1 M in parallel with each LDR (lowest frequency), 3.3 k in series (highest);
  - Peak: Q from 0.6 to 16 (log), the patent gives no range;
  - DOWN: LED drive = 1 - 2 x envelope.
Runs at the base rate before the filter section. Off (and all routing amounts 0) is bit-transparent.
"""

PARAMS = [
    ("ef_on", 0, 0, 1),        # OFF / ON
    ("ef_mode", 1, 0, 2),      # LP / BP / HP
    ("ef_peak", 50, 0, 100),   # Q 0.6 .. 16 (log)
    ("ef_gain", 0, -20, 32),   # preamp gain, dB (Mu-tron: 0.1 .. 40)
    ("ef_range", 1, 0, 1),     # LO / HI
    ("ef_sweep", 0, 0, 1),     # UP / DOWN
    ("ef_att", 2, 0.5, 50),    # envelope attack, ms
    ("ef_rel", 150, 10, 1000), # envelope release, ms
    ("ef_mix", 100, 0, 100),   # dry / wet, %
    ("ef_out", 0, -24, 12),    # output level, dB
    ("ef_to_l", 0, -5, 5),     # envelope -> LPF cutoff, octaves at full sweep
    ("ef_to_h", 0, -5, 5),     # envelope -> HPF cutoff
    ("ef_to_b", 0, -5, 5),     # envelope -> BPF centre
]

RP, RS, RL = 1e6, 3300.0, 10000.0          # parallel resistor, series resistor, LDR at light 1 (assumed)
QMIN, QMAX = 0.6, 16.0
RAIL = 7.5


def params():
    return list(PARAMS)


def register_state(CV):
    for n, i in (("ef_en", 0), ("ef_mx", 1), ("ef_e", 0), ("ef_ld", 0),
                 ("ef_L1", 0), ("ef_L2", 0), ("ef_R1", 0), ("ef_R2", 0)):
        CV(n, i)


def ctrl_names():
    return ["ef_en", "ef_mx", "ef_e", "ef_ld", "ef_L1", "ef_L2", "ef_R1", "ef_R2"]


def emit(w):
    """Per-sample code, placed right after x_L / x_R are read. Defines ef_rl, ef_rh, ef_rb (octaves) used by
    the stage and BPF cutoff code; they are exactly 0 when the routing amounts are 0."""
    import math
    gr = math.log2(RP / (RS + 1.0 / (1.0 / RP + 1.0 / RL)))     # log2(R at rest / R at light 1)
    w("// ================= v1.6 envelope filter (Mu-Tron III topology, US 3,911,776) =================")
    w("ef_ent = ef_on > 0.5 ? 1 : 0;")
    w("ef_en = H_ef_en + a_mix * (ef_ent - H_ef_en);")
    w("if (ef_ent < 0.5 && ef_en < 0.0001) {")
    w("\tef_en = 0;")
    w("}")
    w("if (ef_ent > 0.5 && ef_en > 0.9999) {")
    w("\tef_en = 1;")
    w("}")
    w("ef_mx = H_ef_mx + a_par * (clamp(ef_mix, 0, 100) * 0.01 - H_ef_mx);")
    w("ef_e = H_ef_e;")
    w("ef_ld = H_ef_ld;")
    w("ef_rl = 0;")
    w("ef_rh = 0;")
    w("ef_rb = 0;")
    w("ef_g = exp2(clamp(ef_gain, -20, 32) * 0.166096405);")
    w("ef_pL = 0;")
    w("ef_pR = 0;")
    w("ef_fr = 1000;")
    w("if (ef_en > 0 || ef_to_l != 0 || ef_to_h != 0 || ef_to_b != 0) {")
    w(f"\tef_pL = {RAIL} * tanh(x_L * ef_g * {1 / RAIL!r});      // preamp, op-amp rails")
    w(f"\tef_pR = {RAIL} * tanh(x_R * ef_g * {1 / RAIL!r});")
    w("\tef_rc = max(max(ef_pL, ef_pR), 0);                     // precision half-wave rectifier, both channels")
    w("\tef_aa = 1 - exp(-1000 / (clamp(ef_att, 0.5, 50) * fs));")
    w("\tef_ar = 1 - exp(-1000 / (clamp(ef_rel, 10, 1000) * fs));")
    w("\tef_e = ef_e + (ef_rc > ef_e ? ef_aa : ef_ar) * (ef_rc - ef_e);")
    w("\tef_up = ef_sweep < 0.5 ? 1 : 0;")
    w("\tef_lt = ef_up > 0.5 ? ef_e : max(1 - 2 * ef_e, 0);   // LED drive (DOWN: reference - 2 x envelope)")
    w("\tef_lg = pow(min(ef_lt, 8), 0.8);                       // LDR conductance (x 1/10k) vs light")
    w("\tef_ld = ef_ld + (ef_lg > ef_ld ? 1 - exp(-400 / fs) : 1 - exp(-28.5714286 / fs)) * (ef_lg - ef_ld);   // 2.5 / 35 ms")
    w(f"\tef_rx = {RS!r} + 1 / ({1 / RP!r} + ef_ld * {1 / RL!r});   // series R + (parallel R || LDR)")
    w("\tef_fr = 1 / (6.28318531 * ef_rx * (ef_range > 0.5 ? 1.8e-9 : 4.0e-9));")
    w(f"\tef_ps = log2({RP + RS!r} / ef_rx) * {1 / gr!r};          // sweep position: 0 at rest, 1 at light 1")
    w("\tef_ps = ef_up > 0.5 ? ef_ps : 1 - ef_ps;")
    w("\tef_ps = clamp(ef_ps, 0, 1.5) * (ef_up > 0.5 ? 1 : -1);")
    w("\tef_rl = ef_to_l * ef_ps;")
    w("\tef_rh = ef_to_h * ef_ps;")
    w("\tef_rb = ef_to_b * ef_ps;")
    w("}")
    w("if (ef_en > 0) {")
    w("\tef_gq = tan(pi * min(ef_fr, 0.45 * fs) / fs);")
    w(f"\tef_R = {0.5 / QMIN!r} * exp2(-clamp(ef_peak, 0, 100) * {math.log2(QMAX / QMIN) / 100!r});   // 1/(2Q)")
    w("\tef_og = exp2(clamp(ef_out, -24, 12) * 0.166096405);")
    for c in ("L", "R"):
        w(f"\tefh_{c}, efb_{c}, efl_{c}, ef_{c}1, ef_{c}2 = f_svf(ef_p{c}, H_ef_{c}1, H_ef_{c}2, ef_gq, ef_R);")
        w(f"\tefo_{c} = ef_mode < 0.5 ? efl_{c} : (ef_mode < 1.5 ? efb_{c} : efh_{c});")
        w(f"\tefo_{c} = {RAIL} * tanh(efo_{c} * {1 / RAIL!r}) * ef_og;")
        w(f"\tefo_{c} = efo_{c} == efo_{c} ? efo_{c} : 0;")
        w(f"\tx_{c} = x_{c} + ef_en * ef_mx * (efo_{c} - x_{c});")
        w(f"\tH_ef_{c}1 = fixdenorm(ef_{c}1);")
        w(f"\tH_ef_{c}2 = fixdenorm(ef_{c}2);")
    w("}")
    w("H_ef_en = ef_en;")
    w("H_ef_mx = ef_mx;")
    w("H_ef_e = fixdenorm(ef_e);")
    w("H_ef_ld = fixdenorm(ef_ld);")
    w()
