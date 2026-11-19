"""v1.6 envelope filter: Musitronics Mu-Tron III (schematic "above S/N 02050", 1975; copy at pisotones.com,
scanned by CJLectronics) and envelope routing to the LPF / HPF / BPF cutoffs. Topology also in Beigel's
US patent 3,911,776; values cross-checked with R. G. Keen's Neutron (GEO design 117).

From the schematic:
  A1 preamp: R4 120k / (R2 3.3k + GAIN 1M CCW log): x36.4 .. x0.12 (+31.2 .. -18.4 dB).
  A2 summer: input to (+) via R5 4.7k; band-pass back to (+) via R9 12k + PEAK 150k CW log; (-) = (HP + LP)/2
      (R7 / R8 22k). Solving: HP = 2a s^2/(s^2 + 2b s + 1) x, BP = -HP/s, LP = HP/s^2, with
      Rf = 12k + Rpeak, a = Rf/(4.7k + Rf), b = 4.7k/(4.7k + Rf): Q = 1/(2b) = 1.78 .. 17.7, passband gain 2a,
      band-pass peak 2aQ (+8 .. +31 dB).
  A3 / A4 integrators: R10 / R12 220k in parallel with the two LDRs of the 0805 opto, C5 / C7 1800 pF,
      + C4 / C6 2200 pF on RANGE Low. No series resistor.
  A5 precision half-wave rectifier (D1 / D2 1N914): 1M / 22k = 45.5 (UP), 1M / (22k || 12k) = 129 (DOWN).
  C9 4.7 uF charges through R17 330 R (1.55 ms) and drains through R18 47k toward -9 V (221 ms): a near-linear
      fall, held at the rectifier output (rest ~0 V). Between the peaks of a held note the ripple modulates the
      LED (part of the Mu-tron growl).
  A6 V-to-I LED driver: I = Vc9 / R23 (UP); I = (7.2 V - Vc9) / R23 (DOWN, 7.2 V = 2 x the R19/R20 divider).
Photocell (Hamamatsu P873-13, the 0805's catalogue number; technical data supplied by the user):
  equilibrium ON resistance vs LED current from fig. 5 (280 k @ 0.1 mA ... 2.0 k @ 20 mA; quadratic log-log fit,
  within 9 %); dynamics from the CdS recombination law dG/dt = k (Geq^2 - G^2), k set by the table's 4 / 6 ms
  rise / fall at 20 mA (tau 4.4 ms at 2 k). This makes it fast when bright and slow when dim, with the hyperbolic
  recovery tail of fig. 6 (measured there on the sister part P873-G35-911).
ASSUMED: R23 = 3.9 k (the schematic: "value depends on characteristics of 0805"; chosen so the sweep tops out at
about 7 kHz on HI), A6 limited to ~5.6 V across R23; +/-7.5 V op-amp rails (4558 on +/-9 V) at the preamp,
rectifier, envelope, summer (A2) and both integrators (A3, A4; states follow the clipped outputs); 1 model unit = 1 V. Polarity inversions of the original (inverted
dry, inverted BP) are not modelled. Attack / release are the circuit's 1.55 ms / 221 ms by default and adjustable.
"""

PARAMS = [
    ("ef_on", 0, 0, 1),        # OFF / ON
    ("ef_mode", 1, 0, 2),      # LP / BP / HP
    ("ef_peak", 50, 0, 100),   # PEAK 150k CW log: Q 1.78 .. 17.7
    ("ef_gain", 0, -18.4, 31.2),  # A1 preamp gain, dB (x0.12 .. x36.4)
    ("ef_range", 1, 0, 1),     # LO / HI
    ("ef_sweep", 0, 0, 1),     # UP / DOWN
    ("ef_att", 1.55, 0.5, 50),   # C9 charge time constant, ms (circuit: R17 330 x 4.7 uF)
    ("ef_rel", 221, 10, 1000),   # C9 drain time constant toward -9 V, ms (circuit: R18 47k x 4.7 uF)
    ("ef_mix", 100, 0, 100),   # dry / wet, %
    ("ef_out", 0, -24, 12),    # output level, dB
    ("ef_to_l", 0, -5, 5),     # envelope -> LPF cutoff, octaves at full sweep
    ("ef_to_h", 0, -5, 5),     # envelope -> HPF cutoff
    ("ef_to_b", 0, -5, 5),     # envelope -> BPF centre
]

RP = 220e3            # R10 / R12 across each LDR
R23 = 3900.0          # LED current-sense resistor: "value depends on characteristics of 0805" (calibration, assumed)
VLMAX = 5.6           # most A6 can put across R23: ~7.5 V swing minus the LED's ~1.9 V
KREC = 1 / (0.0044 * (1 / 2000.0))   # CdS recombination constant: tau 4.4 ms at 20 mA / 2.0 k (P873-13 table)
RAIL = 7.5


def ldr_r(i_ma):
    """P873-13 ON resistance (ohm) vs LED current (mA): Hamamatsu technical data, fig. 5, quadratic fit in log-log
    (within 9 %, 0.1..20 mA); below 0.1 mA continued at the end slope; 10 M dark floor."""
    import math
    L = math.log10(max(i_ma, 1e-6))
    lk = 1.30166519 - 0.99354299 * L + 0.16560469 * L * L if L >= -1 else 2.46081287 - 1.32475236 * (L + 1)
    return 1 / (1 / (1000 * 10 ** lk) + 1e-7)


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
    rtop = 1 / (1 / RP + 1 / ldr_r(VLMAX / R23 * 1000))
    gr = math.log2(RP / rtop)                     # log2(R at rest / R at the rail): sweep span
    w("// ================= v1.6 envelope filter (Mu-Tron III, 1975 schematic) =================")
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
    w("ef_g = exp2(clamp(ef_gain, -18.4, 31.2) * 0.166096405);")
    w("ef_pL = 0;")
    w("ef_pR = 0;")
    w("ef_fr = 1000;")
    w("if (ef_en > 0 || ef_to_l != 0 || ef_to_h != 0 || ef_to_b != 0) {")
    w(f"\tef_pL = {RAIL} * tanh(x_L * ef_g * {1 / RAIL!r});      // A1 preamp, op-amp rails")
    w(f"\tef_pR = {RAIL} * tanh(x_R * ef_g * {1 / RAIL!r});")
    w("\tef_up = ef_sweep < 0.5 ? 1 : 0;")
    w("\tef_tg = min(max(max(ef_pL, ef_pR), 0) * (ef_up > 0.5 ? 45.4545455 : 128.787879), 7.5);   // A5 half-wave, 1M/22k or 1M/(22k||12k)")
    w("\tef_tc = clamp(ef_att, 0.5, 50) * 0.001;")
    w("\tef_td = clamp(ef_rel, 10, 1000) * 0.001;")
    w("\tif (ef_tg > ef_e) {")
    w("\t\tef_e = ef_e + (1 - exp(-1 / (ef_tc * fs))) * (ef_tg - ef_e);       // C9 charges through R17")
    w("\t} else {")
    w("\t\tef_e = max(ef_tg, (ef_e + 9) * exp(-1 / (ef_td * fs)) - 9);        // drains through R18 toward -9 V")
    w("\t}")
    w("\tef_lt = ef_up > 0.5 ? ef_e : max(7.2 - ef_e, 0);                  // A6: LED current x R23")
    w(f"\tef_lq = log10(max(min(ef_lt, {VLMAX}) * {1000 / R23!r}, 0.000001));   // log10(LED mA)")
    w("\tef_lk = ef_lq >= -1 ? 1.30166519 - 0.99354299 * ef_lq + 0.16560469 * ef_lq * ef_lq : 2.46081287 - 1.32475236 * (ef_lq + 1);")
    w("\tef_lg = 1 / (1000 * exp(2.30258509 * ef_lk)) + 0.0000001;                        // P873-13 equilibrium conductance (fig. 5)")
    w(f"\tef_ld = max(ef_ld + {KREC!r} * (ef_lg * ef_lg - ef_ld * ef_ld) / fs, 0.0000001);   // CdS recombination: dG/dt = k (Geq^2 - G^2)")
    w(f"\tef_rx = 1 / ({1 / RP!r} + ef_ld);                                   // R10 / R12 220k || LDR")
    w("\tef_fr = 1 / (6.28318531 * ef_rx * (ef_range > 0.5 ? 1.8e-9 : 4.0e-9));")
    w(f"\tef_ps = clamp(log2({RP!r} / ef_rx) * {1 / gr!r}, 0, 1);              // 0 at rest, 1 at the rail")
    w("\tef_ps = ef_up > 0.5 ? ef_ps : -(1 - ef_ps);")
    w("\tef_rl = ef_to_l * ef_ps;")
    w("\tef_rh = ef_to_h * ef_ps;")
    w("\tef_rb = ef_to_b * ef_ps;")
    w("}")
    w("if (ef_en > 0) {")
    w("\tef_gq = tan(pi * min(ef_fr, 0.45 * fs) / fs);")
    w("\tef_rp = 150000 * (exp(clamp(ef_peak, 0, 100) * 0.04394) - 1) * 0.0125057;   // PEAK 150k CW log (10 % at mid)")
    w("\tef_rf = 12000 + ef_rp;                       // R9 + PEAK")
    w("\tef_R = 4700 / (4700 + ef_rf);                 // b = 1/(2Q)")
    w("\tef_a2 = 2 * ef_rf / (4700 + ef_rf);           // 2a: summer gain")
    w("\tef_og = exp2(clamp(ef_out, -24, 12) * 0.166096405);")
    w("\tef_sn = 1 / (1 + 2 * ef_R * ef_gq + ef_gq * ef_gq);")
    for c in ("L", "R"):
        # TPT state-variable filter with the op-amp rails INSIDE the loop: A2 (HP), A3 (BP) and A4 (LP) each
        # saturate at +/-7.5 V, and the integrator states follow the clipped outputs (an integrator cannot
        # hold more than its rail). Linear below the rails; at high Peak the hot band-pass clips as on the pedal.
        w(f"\tefh_{c} = (ef_p{c} * ef_a2 - (2 * ef_R + ef_gq) * H_ef_{c}1 - H_ef_{c}2) * ef_sn;")
        w(f"\tefh_{c} = {RAIL} * tanh(efh_{c} * {1 / RAIL!r});")
        w(f"\tefb_{c} = {RAIL} * tanh((ef_gq * efh_{c} + H_ef_{c}1) * {1 / RAIL!r});")
        w(f"\tefl_{c} = {RAIL} * tanh((ef_gq * efb_{c} + H_ef_{c}2) * {1 / RAIL!r});")
        w(f"\tef_{c}1 = 2 * efb_{c} - H_ef_{c}1;")
        w(f"\tef_{c}2 = 2 * efl_{c} - H_ef_{c}2;")
        w(f"\tefo_{c} = (ef_mode < 0.5 ? efl_{c} : (ef_mode < 1.5 ? efb_{c} : efh_{c})) * ef_og;")
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
