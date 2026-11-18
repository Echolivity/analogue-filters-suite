# Offline check of the K35 Mk1 diode-stage solver (worst residual vs Newton iterations).
import numpy as np
NV=0.052; C=1.617e-5; RI=1/57.4468   # v(V) = V*RI + C*sinh(V/NV)   (Fig. 17 fit; R64/R63 = 270k/4.7k)
def v_of(V): return V*RI + C*np.sinh(V/NV)
def solve(Aa,B,it):
    # (1-B) v(V) - B V - Aa = 0
    vt=Aa/(1-B); a=np.abs(vt)
    V=np.sign(vt)*np.minimum(a/RI, NV*np.arcsinh(a/C))
    for _ in range(it):
        f=(1-B)*v_of(V)-B*V-Aa
        d=(1-B)*(RI+C/NV*np.cosh(V/NV))-B
        V=V-np.clip(f/d,-0.05,0.05)
    return V,(1-B)*v_of(V)-B*V-Aa
Aa=np.concatenate([-np.logspace(-7,0.5,4000)[::-1],[0],np.logspace(-7,0.5,4000)])
for B in (0,0.003,0.0096,0.012):
    for it in (3,4,6):
        V,r=solve(Aa,B,it)
        # relative residual in terms of input-referred volts
        rel=np.abs(r)/np.maximum(np.abs(Aa),1e-9)
        print(f"B {B}: {it} iters: max |res| {np.abs(r).max():.2e} V, max rel {rel.max():.2e}, |V| max {np.abs(V).max():.2f}")
