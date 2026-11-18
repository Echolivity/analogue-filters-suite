"""Filter routing (v1.4): SERIES / PARALLEL / HYBRID for the LPF, HPF and BPF.

SERIES   (default, = v1.3)  the LPF/HPF chain in the selected stage order, BPF before or after it.
PARALLEL                    LPF, HPF and BPF each filter the same input; their outputs are summed.
HYBRID                      the LPF/HPF chain (stage order applies) with the BPF in parallel to it.

Parallel summing uses each stage's own wet weight w (ON fade x OPEN-zone, or BPF ON x Mix):
    y = sum_s level_s * (out_s - (1 - w_s) x)  +  x * prod_s (1 - w_s)
so a stage contributes exactly w_s * F_s(x): a stage that is off, or parked fully OPEN,
drops out of the sum instead of adding a second copy of the dry signal, and with every
stage off the output is the dry input. Mode changes use the existing 8 ms output duck.
"""
CH = ["L", "R"]
MODES = ["SERIES", "PARALLEL", "HYBRID"]
PARAMS = [("flt_route", 0, 0, 2), ("par_l", 0, -40, 6), ("par_h", 0, -40, 6), ("par_b", 0, -40, 6)]


def params():
    return PARAMS


def register_state(CV):
    CV("cur_route", 0)
    for n in ("rl", "rh", "rb"):
        CV(f"rt_{n}", 1.0)


def ctrl_names():
    return ["rt_rl", "rt_rh", "rt_rb"]


def emit_controls(w):
    w("// ================= filter routing (v1.4) =================")
    w("cur_route = H_cur_route;")
    w("r_par = (cur_route > 0.5 && cur_route < 1.5) ? 1 : 0;")
    w("r_hyb = cur_route > 1.5 ? 1 : 0;")
    for n, p in (("rl", "par_l"), ("rh", "par_h"), ("rb", "par_b")):
        w(f"rt_{n} = H_rt_{n} + a_par * (exp(0.11512925465 * clamp({p}, -40, 6)) - H_rt_{n});")
    w("cfg_r = clamp(floor(flt_route + 0.5), 0, 2);")


def emit_combine(w, G, sub, emit_bpf):
    """After the LPF/HPF blocks of one subsample: PARALLEL sum / HYBRID add."""
    x = {ch: f"x{sub}_{ch}" for ch in CH}
    w("if (cur_route > 0.5) {")
    G.ind += 1
    for ch in CH:
        w(f"bp{sub}_{ch} = {x[ch]};")
    emit_bpf(w, G, x, {ch: f"bp{sub}_{ch}" for ch in CH})
    for ch in CH:
        w(f"rdb_{ch} = bp{sub}_{ch} - (1 - b_wet) * {x[ch]};")
    w("if (r_par > 0.5) {")
    G.ind += 1
    for ch in CH:
        w(f"rdl_{ch} = ly{sub}_{ch} - (1 - l_wet) * {x[ch]};")
        w(f"rdh_{ch} = hy{sub}_{ch} - (1 - h_wet) * {x[ch]};")
        w(f"z{sub}_{ch} = rt_rl * rdl_{ch} + rt_rh * rdh_{ch} + rt_rb * rdb_{ch} + {x[ch]} * (1 - l_wet) * (1 - h_wet) * (1 - b_wet);")
    G.ind -= 1
    w("} else {")
    G.ind += 1
    for ch in CH:
        w(f"z{sub}_{ch} = z{sub}_{ch} + rt_rb * rdb_{ch};")
    G.ind -= 1
    w("}")
    G.ind -= 1
    w("}")
