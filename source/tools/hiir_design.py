"""Polyphase IIR half-band design (Valenzuela/Constantinides method, as used in
Laurent de Soras' HIIR). Prints coefficients and verifies 2x up/down response."""
import math, sys
import numpy as np


def transition_param(transition):
    k = math.tan((1 - transition * 2) * math.pi / 4)
    k *= k
    kksqrt = (1 - k * k) ** 0.25
    e = 0.5 * (1 - kksqrt) / (1 + kksqrt)
    e2 = e * e
    e4 = e2 * e2
    q = e * (1 + e4 * (2 + e4 * (15 + 150 * e4)))
    return k, q


def acc_num(q, order, c):
    i, j, acc = 0, 1, 0.0
    while True:
        t = q ** (i * (i + 1)) * math.sin((i * 2 + 1) * c * math.pi / order) * j
        acc += t
        j = -j
        i += 1
        if abs(t) <= 1e-100:
            return acc


def acc_den(q, order, c):
    i, j, acc = 1, -1, 0.0
    while True:
        t = q ** (i * i) * math.cos(i * 2 * c * math.pi / order) * j
        acc += t
        j = -j
        i += 1
        if abs(t) <= 1e-100:
            return acc


def coefs(n, transition):
    k, q = transition_param(transition)
    order = n * 2 + 1
    out = []
    for idx in range(n):
        c = idx + 1
        num = acc_num(q, order, c) * q ** 0.25
        den = acc_den(q, order, c) + 0.5
        ww = num / den
        wwsq = ww * ww
        x = math.sqrt((1 - wwsq * k) * (1 - wwsq / k)) / (1 + wwsq)
        out.append((1 - x) / (1 + x))
    return out


class AP:
    def __init__(self, cs):
        self.cs = cs
        self.z = [0.0] * (len(cs) + 1)

    def run(self, x):
        z = self.z
        xin = x
        for i, c in enumerate(self.cs):
            y = c * (xin - z[i + 1]) + z[i]
            z[i] = xin
            xin = y
        z[len(self.cs)] = xin
        return xin


def upsample(x, cs):
    a = AP(cs[0::2]); b = AP(cs[1::2])
    out = np.zeros(2 * len(x))
    for n, v in enumerate(x):
        out[2 * n] = a.run(v)
        out[2 * n + 1] = b.run(v)
    return out


def downsample(x, cs):
    a = AP(cs[0::2]); b = AP(cs[1::2])
    out = np.zeros(len(x) // 2)
    for n in range(len(out)):
        out[n] = 0.5 * (a.run(x[2 * n + 1]) + b.run(x[2 * n]))
    return out


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tb = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0227
    cs = coefs(N, tb)
    print("coefs", cs)
    # Up/down cascade impulse -> response
    imp = np.zeros(8192); imp[0] = 1
    up = upsample(imp, cs)
    H = np.abs(np.fft.rfft(up))
    f = np.fft.rfftfreq(len(up))  # relative to 2x rate
    pb = H[f < 0.25 - tb]; sb = H[f > 0.25 + tb]
    print("up passband ripple dB: %.4f .. %.4f" % (20*np.log10(pb.min()/2), 20*np.log10(pb.max()/2)))
    print("up image rejection dB: %.1f" % (20*np.log10(sb.max()/2)))
    rt = downsample(up, cs)
    Hr = np.abs(np.fft.rfft(rt))
    fr = np.fft.rfftfreq(len(rt))
    print("roundtrip passband (<0.45) dB: %.4f .. %.4f" % (20*np.log10(Hr[fr<0.45].min()), 20*np.log10(Hr[fr<0.45].max())))
    # downsampler alias rejection: tone above base Nyquist at 2x rate
    n = np.arange(65536)
    tone = np.sin(2*np.pi*0.3*n)
    d = downsample(tone, cs)[4096:]
    print("down alias rejection for 0.3fs tone dB: %.1f" % (20*np.log10(np.abs(d).max())))
