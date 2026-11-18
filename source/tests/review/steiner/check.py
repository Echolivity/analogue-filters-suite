# Steiner-Parker model vs Steiner, Electronic Design 25 (6 Dec 1974) p. 96. Run from source/.
import numpy as np, sys
I=50e-6; n=1.9; Vt=0.02585; Vd=2*n*Vt          # one "R" = two 1N4148 in series
v=np.array([0.001,0.01,0.025,0.05,0.1])
iL=-I*(np.exp(-v/Vd)-1); iR=I*(np.exp(v/Vd)-1)   # mirrored halves: signal against / with the bias current
print("mirrored halves, conductance / small-signal at", v, "V:", np.round((iL+iR)/v/(2*I/Vd),3))
for Q,meas in ((1.2,-27),(30,-25),(1,-27)):
    K=3-1/Q; print(f"article plots: Q {Q}: K {K:.2f} -> passband {20*np.log10(K/48):.1f} dB (plot ~{meas} dB)")
sys.path.insert(0,'tests'); from dsp import base, run
from scipy.signal import welch
SR=48000
for L in (-40,-12,0):
    x=np.random.default_rng(1).standard_normal(SR*2)*10**(L/20)
    y=run(x,base(l_on=1,l_model=3,l_cut=1000,l_res=85,l_drive=60),SR)[SR//2:,0]
    f,P=welch(y,SR,nperseg=8192); Px=welch(x[SR//2:],SR,nperseg=8192)[1]; sel=(f>200)&(f<5000)
    print(f"model, noise {L:+d} dBFS, Drive 60: resonant peak {f[sel][np.argmax((P/Px)[sel])]:.0f} Hz")
