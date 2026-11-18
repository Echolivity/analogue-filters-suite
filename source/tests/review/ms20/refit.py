# K35 model vs Stinchcombe MS-20 study. Run from source/.
import sys; sys.path.insert(0,'tests')
import numpy as np
from dsp import base, tf
fc=1000
for r in (0,50,80):
    K=0.05+2.03*(r/100)**1.1
    f,H=tf(base(l_on=1,l_model=1,l_cut=fc,l_res=r)); sel=(f>100)&(f<3000); s=1j*f[sel]/fc
    for name,d in (("2-K",2-K),("7/3-K",7/3-K)):
        Hm=1/(s*s+d*s+1); dev=20*np.log10(np.abs(H[sel])/np.abs(Hm)); print(f"res {r}: vs {name}: dev {dev.min():+.2f}..{dev.max():+.2f} dB")
