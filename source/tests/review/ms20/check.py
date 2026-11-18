# K35 model vs Stinchcombe MS-20 study. Run from source/.
import sys; sys.path.insert(0,'tests')
import numpy as np, dsp
from dsp import base, tf, run
SR=48000
# 1. LP small-signal TF vs Stinchcombe eq (5) (OTA/Mk2: 2-K) and eq (8) (Korg35/Mk1: 7/3-k)
fc=1000
for r in (0, 50, 80):
    K=0.05+2.03*(r/100)**1.1
    f,H=tf(base(l_on=1,l_model=1,l_cut=fc,l_res=r))
    sel=(f>100)&(f<8000); s=1j*f[sel]/fc
    best=None
    for name,d in (("eq5 Mk2 (2-K)",2-K),("eq8 Mk1 (7/3-K)",7/3-K)):
        Hm=1/(s*s+d*s+1); g=np.median(np.abs(H[sel])/np.abs(Hm))
        err=np.max(np.abs(20*np.log10(np.abs(H[sel])/(g*np.abs(Hm)))))
        print(f"res {r} (K={K:.2f}) vs {name}: max dev {err:.2f} dB")
    pk=20*np.log10(np.abs(H[sel]).max()/np.abs(H[(f>20)&(f<60)]).mean()); print(f"   measured peak {pk:.1f} dB")
# 2. HP slope below cutoff
f,H=tf(base(h_on=1,h_model=1,h_cut=1000,h_res=0))
a=lambda fr: 20*np.log10(np.abs(H[np.argmin(abs(f-fr))]))
print("K35 HP slope 125->250 Hz: %.1f dB/oct; 62->125: %.1f dB/oct (Stinchcombe: 6 dB/oct)"%(a(250)-a(125),a(125)-a(62.5)))
# 3. Stinchcombe's detection test: cutoff high (7 kHz), moderate res, 500 Hz sine, rising level -> THD
t=np.arange(SR*2)/SR
def thd(y,f0=500):
    y=y[SR:]; w=np.hanning(len(y)); Y=np.abs(np.fft.rfft(y*w)); fr=np.fft.rfftfreq(len(y),1/SR)
    pk=lambda h: Y[np.argmin(abs(fr-h*f0))-3:np.argmin(abs(fr-h*f0))+4].max()
    return 100*np.sqrt(sum(pk(h)**2 for h in range(2,12)))/pk(1)
for L in (-24,-12,-6,0):
    x=10**(L/20)*np.sin(2*np.pi*500*t)
    print(f"500 Hz at {L:+d} dBFS, fc 7 kHz res 50: THD {thd(run(x,base(l_on=1,l_model=1,l_cut=7000,l_res=50),SR)[:,0]):.3f} %   (res 0: {thd(run(x,base(l_on=1,l_model=1,l_cut=7000,l_res=0),SR)[:,0]):.3f} %)")
