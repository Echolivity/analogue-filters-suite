# Static model of the LA-2A attenuator from schematic C-10953 rev C (see docs/independent-review/LA2A_MANUAL_CHECK.md).
import numpy as np
f = np.array([50, 100, 200, 500, 1000, 2000, 5000, 10000, 15000.])
w = 2j*np.pi*f
C9, C12, C6, R30, R3 = 0.02e-6, 0.001e-6, 0.01e-6, 47e3, 1e6
def H(R37, Ct, Rout):
    Zs = Rout + 1/(w*C9)
    Zl = 1/(1/R3 + 1/(1/(w*C6) + 1/(1/R30 + w*Ct)))
    Zp = 0 if R37 == 0 else 1/(1/R37 + w*C12)
    return Zl/(Zl+Zs+Zp)
for Rout in (25e3, 35e3, 50e3):
  for Ct in (50e-12, 200e-12, 380e-12):
    flat = H(0, Ct, Rout)
    rel = 20*np.log10(np.abs(H(1e6, Ct, Rout)/flat))
    print(f"Rout {Rout/1e3:.0f}k Ct {Ct*1e12:.0f}p  R37=1M rel dB:", " ".join(f"{x:+.1f}" for x in rel), f"| 15k minus <=1k(max): {rel[-1]-rel[:5].max():+.1f}, minus 500: {rel[-1]-rel[3]:+.1f}")
print("f:", list(f))
# fit our shelf  y = x + E*(x - LP1(fc)) relative: |1 + E*jf/fc/(1+jf/fc)| normalised so HF = rel(15k)
