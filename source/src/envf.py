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
ASSUMED (the schematic leaves them to the 0805 part, which has no data): R23 and the LDR law, here
conductance = (V/1 V)^0.8 / 67k (sweep top 7.0 kHz HI / 3.2 kHz LO at the rail), LDR lags 2.5 / 35 ms (VTL5C3
class); +/-7.5 V op-amp rails (4558 on +/-9 V); 1 model unit = 1 V; rails applied at the preamp, rectifier,
envelope and selected output only. Polarity inversions of the original (inverted dry, inverted BP) are not
modelled. Attack / release are the circuit's 1.55 ms / 221 ms by default and adjustable.
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
GL = 1 / 67000.0      # LDR conductance at 1 V of LED drive (assumed; R23 / 0805 dependent)
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
    rtop = 1 / (1 / RP + GL * RAIL ** 0.8)
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
    w(f"\tef_lg = pow(min(ef_lt, 8), 0.8) * {GL!r};                           // LDR conductance (assumed law)")
    w("\tef_ld = ef_ld + (ef_lg > ef_ld ? 1 - exp(-400 / fs) : 1 - exp(-28.5714286 / fs)) * (ef_lg - ef_ld);   // 2.5 / 35 ms")
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
    for c in ("L", "R"):
        w(f"\tefh_{c}, efb_{c}, efl_{c}, ef_{c}1, ef_{c}2 = f_svf(ef_p{c} * ef_a2, H_ef_{c}1, H_ef_{c}2, ef_gq, ef_R);")
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
