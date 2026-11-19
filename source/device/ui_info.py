"""Info View / hint text for every control (v1.5). Shown in Live's Info View when the
pointer is over a control and as the Max hint. Range, unit and default are appended
automatically from the parameter definition, so they can't drift from the device."""

DESC = {
    # LOW-PASS / HIGH-PASS
    "l_on": "Switches the low-pass stage in or out. Off = clean bypass, no colouration.",
    "l_model": "Circuit model for the low-pass stage. Each model runs its own engine; nothing is substituted.",
    "l_cut": "Low-pass cutoff frequency. Fully open (20 kHz) is transparent.",
    "l_res": "Resonance / feedback. High settings self-oscillate on models that do so in hardware.",
    "l_drive": "Input level into the model's nonlinear stages: more drive, more saturation.",
    "l_comp": "Level compensation for resonance-related passband loss. 100 % = full compensation.",
    "l_char": "Model-specific control; its name (below the knob) changes with the model.",
    "l_slope": "Filter slope in dB/oct. Slopes beyond the model's native order add extension stages.",
    "h_on": "Switches the high-pass stage in or out. Off = clean bypass, no colouration.",
    "h_model": "Circuit model for the high-pass stage. Each model runs its own engine; nothing is substituted.",
    "h_cut": "High-pass cutoff frequency. Fully down (20 Hz) is transparent.",
    "h_res": "Resonance / feedback of the high-pass stage.",
    "h_drive": "Input level into the high-pass model's nonlinear stages.",
    "h_comp": "Level compensation for resonance-related passband loss.",
    "h_char": "Model-specific control; its name (below the knob) changes with the model.",
    "h_slope": "Filter slope in dB/oct. Slopes beyond the model's native order add extension stages. The Korg 35 / MS-20 and Steiner-Parker high-passes are 6 dB/oct natively, as on the hardware, so on those models the settings give about 6, 18, 30 and 42 dB/oct.",
    # DUB FILTER centre
    "order_sel": "Series order of the low-pass and high-pass stages. Not used in PARALLEL routing.",
    "ovs_sel": "Oversampling for the filter engines and TUBE: 1x or 2x (see High Oversampling for 4x-16x). In REFERENCE mode this is a minimum: the engine runs at least at each active model's measured minimum.",
    "eng_mode": "REFERENCE: every active model runs at least at its measured minimum oversampling (filters <= -80 dBc aliasing at a bright test point; TUBE 8x). CREATIVE: the engine runs at exactly the factor you set, including 1x.",
    "k35_circ": "Which MS-20 filter circuit the K35 model (LPF and HPF) uses. OTA (Mk2): the later LM13600 design, with clipping diodes in the resonance feedback, as in v1.5. KORG-35 (Mk1): the original Korg35 Sallen-Key, with clipping diodes in the signal path, so loud signals distort at every frequency; CHARACTER sets how hard they are driven. Reference mode runs it at 8x (LPF) / 4x (HPF).",
    "sh_mode": "Sherman model (01) outputs. STAGE: low-pass in the LPF stage, high-pass in the HPF stage, as before. PANEL: the Filterbank 2's Balance and Correction knobs set the output (shared by both of its filters; the hardware has a pair per filter).",
    "sh_bal": "Filterbank 2 Lp/Bp/Hp balance: low-pass at 0, band-pass at 50, high-pass at 100, crossfading between. PANEL mode only.",
    "sh_corr": "Filterbank 2 correction knob: adds -Bp at -100, nothing at 0, -Bp+Lp+Hp at +100. With Balance on Bp: -100 is silent, +100 is a notch, +50 passes everything at about half level. PANEL mode only.",
    "sh_harm": "Filterbank 2 harmonics: filter 2 tuned to the cutoff divided by 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9 or 16, for twin resonant peaks. Applies at 24 dB (series); at 12 dB filter 2 plays alone at the cutoff.",
    "sh_limit": "Filterbank 2 Limit switch: leaves the filters more room to resonate when the input is heavily overdriven. Behavioural: the manual describes the effect, not the circuit.",
    "sh_clock": "Clocked character: runs both filters as clocked (switched-capacitor) stages, clock at 100 x cutoff, with a faint clock whine and staircase grain that grows at low cutoffs. Behavioural: clock ratio and feedthrough level are assumptions. Above about cutoff = engine rate / 100 the filter runs smooth. Reference mode runs at least 8x while it is on.",
    "ovs_hi": "Optional 4x, 8x or 16x oversampling for the filter engines and TUBE. Overrides the 1x/2x switch when not OFF. Higher factors cost CPU.",
    "out_db": "Device output level after all processing.",
    "softclip": "Gentle output soft clipper that catches peaks from resonance and drive.",
    # BAND-PASS
    "b_on": "Switches the band-pass engine in or out.",
    "b_model": "Circuit model for the band-pass engine. 'derived' models have no native BP mode in hardware.",
    "b_arch": "Band-pass structure. SVF uses Q; CASC (HP into LP) uses Bandwidth and Q; MULTI (ladder pole mix) uses Bandwidth.",
    "b_freq": "Band-pass centre frequency.",
    "b_bw": "Band width in octaves. Used by CASC and MULTI; not used by SVF.",
    "b_q": "Resonant width of the SVF band, or edge Q of the CASC band. Not used by MULTI.",
    "b_res": "Band-pass resonance / feedback.",
    "b_drive": "Input level into the band-pass model's nonlinear stages.",
    "b_comp": "Centre-gain compensation. Not used by MULTI, whose tap gain is already unity.",
    "b_mix": "Dry/wet mix of the band-pass engine.",
    "b_pos": "Where the band-pass sits in SERIES routing: before (PRE) or after (POST) LP/HP. Ignored in PARALLEL and HYBRID.",
    # PROCESSING CHAIN
    "c_order": "Order of TUBE, OPTO and VCA. Also set by dragging a block's grip or by the three suggested orders.",
    "key_listen": "Solo the sidechain key of the opto, VCA or gate so you can hear what the detector hears.",
    "t_on": "Switches the tube stage in or out.",
    "o_on": "Switches the opto compressor in or out.",
    "v_on": "Switches the VCA compressor in or out.",
    "g_on": "Switches the gate in or out.",
    "t_in": "Level into the triode stage.",
    "t_drive": "Triode drive: amount of saturation.",
    "t_bias": "Operating point of the triode; shifts even-order (asymmetric) harmonics.",
    "t_tone": "Low-pass tone control after the triode.",
    "t_mix": "Dry/wet mix of the tube stage (the dry path is phase-matched).",
    "t_out": "Level out of the tube stage.",
    "t_auto": "Auto gain keeps the tube stage's level steady as Drive changes (-12 dBFS program reference).",
    "o_in": "Level into the opto compressor.",
    "o_pr": "Peak Reduction: how hard the optical cell is driven, as on the LA-2A.",
    "o_emph": "The LA-2A's R37 control: cuts the low frequencies feeding the detector, so highs are levelled more than lows (at 100 %, about 12 dB more at 15 kHz than at 500 Hz). 0 % is flat.",
    "o_hpf": "High-pass filter on the opto's sidechain, so bass doesn't pump the compressor.",
    "o_link": "Stereo link of the opto detector. 100 % = fully linked.",
    "o_mix": "Dry/wet (parallel) mix of the opto compressor.",
    "o_out": "Make-up gain after the opto compressor.",
    "o_mode": "COMP is about 3:1. LIMIT follows the LA-2A's limiter curve: it rounds into a flat top about 10-15 dB past the threshold.",
    "o_src": "Opto sidechain source: INT (its own input), CHAIN (the chain input) or EXT (external key).",
    "v_in": "Level into the VCA compressor.",
    "v_thr": "VCA compressor threshold.",
    "v_rel": "VCA compressor release time.",
    "v_hpf": "High-pass filter on the VCA's sidechain.",
    "v_link": "Stereo link of the VCA detector. 100 % = fully linked.",
    "v_mix": "Dry/wet (parallel) mix of the VCA compressor.",
    "v_out": "Level out of the VCA compressor.",
    "v_ratio": "VCA compression ratio.",
    "v_att": "VCA attack time.",
    "v_knee": "Knee shape: HARD, MED or SOFT.",
    "v_thrust": "Sidechain Thrust: NORM is flat; MED and LOUD reduce the detector's bass sensitivity.",
    "v_type": "Detector topology: NEW (feed-forward) or OLD (feedback).",
    "v_auto": "Automatic make-up gain from the threshold and ratio.",
    "v_src": "VCA sidechain source: INT, CHAIN or EXT (external key).",
    "g_thr": "Gate opening threshold. It closes 4 dB below (hysteresis).",
    "g_att": "Gate attack (opening) time.",
    "g_hold": "Time the gate stays open after the key falls below threshold.",
    "g_rel": "Gate release (closing) time.",
    "g_range": "Attenuation when closed. -80 dB is fully closed.",
    "g_hpf": "High-pass filter on the gate key.",
    "g_lpf": "Low-pass filter on the gate key.",
    "g_src": "Gate key source: INT, CHAIN or EXT (external key).",
    # FILTER ROUTING
    "flt_route": "SERIES chains the filters; PARALLEL feeds LP, HP and BP from the input and sums them; HYBRID runs LP/HP in series and adds BP in parallel.",
    "par_l": "Low-pass level in the PARALLEL sum. Used only in PARALLEL.",
    "par_h": "High-pass level in the PARALLEL sum. Used only in PARALLEL.",
    "par_b": "Band-pass level in the PARALLEL sum and in HYBRID.",
}

# non-parameter controls (jsui / navigation)
UI_DESC = {
    "os_now_filters": ("Active filter oversampling", "The factor the filter engines are running at right now (REFERENCE may raise it above your setting)."),
    "os_now_tube": ("Active TUBE oversampling", "The factor the TUBE stage is running at right now."),
    "preset_0": ("WARM DUB", "Sets Chain Order to TUBE > OPTO > VCA: saturation first, then smooth opto levelling, then VCA control. Changes only the order."),
    "preset_4": ("PUNCH & COLOUR", "Sets Chain Order to VCA > TUBE > OPTO: VCA punch first, tube colour after, opto glue last. Changes only the order."),
    "preset_3": ("FINAL COLOUR", "Sets Chain Order to OPTO > VCA > TUBE: compression first, tube colour last. Changes only the order."),
    "edit_page": ("Edit Page", "Shows the controls of TUBE, OPTO, VCA or GATE below the chain."),
    "route_diagram": ("Routing Diagram", "Shows the signal path for the current routing, stage order, BPF position and ON states. Display only."),
    "bpf_arch_glyph": ("BPF Architecture", "Shows the selected band-pass structure and which width controls it uses. Display only."),
}

UNIT = {0: "", 1: "", 2: " ms", 3: " Hz", 4: " dB", 5: " %", 9: ""}


def describe(vn, valueof):
    v = valueof
    d = DESC.get(vn, "")
    if v.get("parameter_enum"):
        e = v["parameter_enum"]
        tail = f" Options: {', '.join(e)}. Default: {e[int(v['parameter_initial'][0])]}."
    else:
        u = v.get("parameter_units", "").replace("%0.1f", "").replace("%0.2f", "").strip()
        u = (" " + u) if u else UNIT.get(v["parameter_unitstyle"], "")
        tail = f" Range {v['parameter_mmin']:g} to {v['parameter_mmax']:g}{u}. Default {v['parameter_initial'][0]:g}{u}."
    return (d + tail).strip()
