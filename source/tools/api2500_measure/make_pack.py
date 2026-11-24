"""API 2500 measurement pack: test signals whose renders reveal the knee, detector timing, variable release,
THRUST MED and link Shape filters. 48 kHz, 24-bit stereo. Every file starts with 0.5 s silence, a one-sample
sync click at 0.5 s, then 1.0 s silence; the test signal starts at exactly 1.5 s (sample 72000).
The schedule of every file is also written to schedule.json for the analysis.
Usage: python3 make_pack.py [out_dir]   (render instructions: RENDER_INSTRUCTIONS.txt)"""
import json, os, sys
import numpy as np
import soundfile as sf

SR = 48000
OUT = sys.argv[1] if len(sys.argv) > 1 else "API2500_test_pack"
os.makedirs(OUT, exist_ok=True)
FREQS = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
         2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000]
sched = {}


def a(dbfs):
    return 10 ** (dbfs / 20)


def head():
    h = np.zeros(int(1.5 * SR))
    h[int(0.5 * SR)] = a(-6)
    return h


def ramp(n, ms=5):
    """Raised-cosine fades so level changes don't click."""
    k = int(ms / 1000 * SR)
    w = np.ones(n)
    r = 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    w[:k] = r
    w[-k:] = r[::-1]
    return w


def tone(f, dbfs, sec, fade=True):
    n = int(sec * SR)
    y = a(dbfs) * np.sin(2 * np.pi * f * np.arange(n) / SR)
    return y * ramp(n) if fade else y


def level_track(f, segs):
    """One continuous sine whose level follows segs [(dbfs, sec)], 1 ms level ramps between segments."""
    env = np.concatenate([np.full(int(s * SR), a(d)) for d, s in segs])
    k = int(0.001 * SR)
    env = np.convolve(np.r_[np.full(k, env[0]), env], np.ones(k) / k, "valid")[:len(env)]
    return env * np.sin(2 * np.pi * f * np.arange(len(env)) / SR)


def write(name, L, R=None, info=None):
    R = L if R is None else R
    y = np.stack([np.r_[head(), L, np.zeros(SR)], np.r_[head(), R, np.zeros(SR)]], 1)
    assert np.abs(y).max() < 1
    sf.write(os.path.join(OUT, name), y, SR, subtype="PCM_24")
    sched[name] = dict(start_s=1.5, **(info or {}))


# 0 - calibration: 1 kHz at -20 dBFS (nothing compresses at the settings given)
write("00_calibration_1k_-20dBFS.wav", tone(1000, -20, 5), info=dict(segments=[[-20, 5]]))

# 1 - static curve: 1 kHz stepped -60 .. -1 dBFS in 1 dB steps of 0.5 s (continuous phase)
steps = [(-60 + i, 0.5) for i in range(60)]
write("01_static_curve_1k_steps.wav", level_track(1000, steps), info=dict(freq=1000, segments=steps))

# 2 - THRUST / detector frequency response: third-octave tones at -10 dBFS, 1.5 s each
L = np.concatenate([tone(f, -10, 1.5) for f in FREQS])
write("02_thrust_sweep_-10dBFS.wav", L, info=dict(freqs=FREQS, each_s=1.5, dbfs=-10))

# 3 - attack / detector timing: 1 kHz, -50 dBFS baseline with 5 bursts to -10 dBFS (1 s on, 1 s off)
seg = [(-50, 1.0)] + [(-10, 1.0), (-50, 1.0)] * 5
write("03_attack_bursts_1k.wav", level_track(1000, seg), info=dict(freq=1000, segments=seg))

# 4 - release / programme dependence: bursts 2, 17 and 32 dB over threshold (2 s), each followed by 6 s at -50
seg = [(-50, 1.0), (-40, 2.0), (-50, 6.0), (-25, 2.0), (-50, 6.0), (-10, 2.0), (-50, 6.0)]
write("04_release_bursts_1k.wav", level_track(1000, seg), info=dict(freq=1000, segments=seg))

# 5 - link Shape filters: Left = third-octave tones at -10 dBFS; Right = steady 1 kHz at -50 dBFS (below threshold,
#     so any gain change on Right comes through the link)
L = np.concatenate([tone(f, -10, 1.5) for f in FREQS])
R = tone(1000, -50, len(L) / SR, fade=False) * ramp(len(L), 20)
write("05_link_shape_L-sweep_R-1k.wav", L, R, info=dict(freqs=FREQS, each_s=1.5, left_dbfs=-10, right=[1000, -50]))

json.dump(sched, open(os.path.join(OUT, "schedule.json"), "w"), indent=1)
print("written:", sorted(os.listdir(OUT)))
