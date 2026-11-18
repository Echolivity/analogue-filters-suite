import numpy as np, subprocess, tempfile, os
HERE = os.path.dirname(os.path.abspath(__file__))
HARN = os.path.join(HERE, "..", "build", "harness")
LP_MODELS = ["Sherman", "K35/MS-20", "Ladder", "Steiner-Parker", "SEM", "Diode/303"]
HP_MODELS = ["Sherman", "K35/MS-20", "Ladder HP (ALT)", "Steiner-Parker", "SEM"]

def base(**kw):
    """Neutral setup: both stages off unless enabled via kw."""
    p = dict(l_on=0, h_on=0, l_cut=20000, h_cut=20, l_res=0, h_res=0, l_slope=0, h_slope=0,
             l_drive=0, h_drive=0, l_comp=100, h_comp=100, l_char=0, h_char=0, order_sel=0,
             ovs_sel=0, out_db=0, softclip=0)
    p.update(kw); return p

def run(x, params, sr=48000, events=(), ns=False, key=None, meters=False):
    """x: (n,2) or (n,) array. params: initial values (applied before sample 0, so
    smoothers still glide from their power-on values -> callers pre-roll)."""
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with tempfile.TemporaryDirectory() as d:
        fi, fo, fs, fk, fm = (os.path.join(d, n) for n in ("i", "o", "s", "k", "m"))
        x.astype(np.float32).tofile(fi)
        args = []
        if key is not None:
            key = np.asarray(key, np.float32)
            if key.ndim == 1: key = np.stack([key, key], 1)
            key.astype(np.float32).tofile(fk); args = [fk]
        if meters:
            args = (args or ["-"]) + [fm]
        with open(fs, "w") as f:
            for k, v in params.items(): f.write(f"-1 {k} {v}\n")
            for (fr, k, v) in events: f.write(f"{int(fr)} {k} {v}\n")
        r = subprocess.run([HARN, str(sr), fi, fo, fs] + args, capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stderr)
        y = np.fromfile(fo, np.float32).reshape(-1, 2).astype(np.float64)
        M = np.fromfile(fm, np.float32).reshape(-1, 12).astype(np.float64) if meters else None
    if meters:
        return y, M
    return (y, float(r.stdout)) if ns else y

def tf(params, sr=48000, n=1<<16, pre=None, level=1e-3, seed=1):
    """Small-signal transfer function via white-noise cross-spectrum (Welch)."""
    from scipy.signal import csd, welch
    pre = pre or sr // 2
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n + pre) * level
    y = run(x, params, sr)[pre:, 0]; x = x[pre:]
    f, pxy = csd(x, y, fs=sr, nperseg=8192); _, pxx = welch(x, fs=sr, nperseg=8192)
    return f, pxy / pxx
BP_MODELS = ["SEM", "Steiner-Parker", "K35/MS-20", "ARP 2600", "EMS VCS3"]
BP_ARCHS = ["SVF", "CASCADE", "MULTIMODE"]

def bpf(**kw):
    """BPF alone (LPF/HPF off)."""
    glob = {"softclip", "out_db", "order_sel", "ovs_sel"}
    d = dict(b_on=1)
    d.update({(k if (k.startswith(("b_", "l_", "h_")) or k in glob) else "b_" + k): v for k, v in kw.items()})
    return base(**d)
DYN_PERMS = ["TUBE>OPTO>VCA", "TUBE>VCA>OPTO", "OPTO>TUBE>VCA", "OPTO>VCA>TUBE", "VCA>TUBE>OPTO", "VCA>OPTO>TUBE"]

def dyn(**kw):
    """Dynamics only (filters off)."""
    return base(**kw)
