# LA-2A OPTO check (v1.6). Run from source/; needs build/harness and build/harness_v15 (built by build.sh).
import sys; sys.path.insert(0,'tests')
import numpy as np, dsp
from dyn_tests import M_OGR
P=lambda **k: dsp.dyn(**dict(dict(o_on=1,o_pr=100,o_mode=1,o_emph=0,o_src=0,o_hpf=20,o_mix=100),**k))
def gr_trace(x,p,old,sr):
    if old: p={k:v for k,v in p.items() if k not in('eng_mode','ovs_hi')}; dsp.HARN='build/harness_v15'
    else: dsp.HARN='build/harness'
    y,M=dsp.run(x,p,sr,meters=True); return y, M[:,M_OGR]*30
for sr in (48000,):
    rng=np.random.default_rng(1)
    t=np.arange(int(8*sr))/sr
    # burst: 1 kHz, 0 dBFS for 2 s, -20 for 2 s, 0 for 2 s, silence
    env=np.select([t<2,t<4,t<6],[1.0,0.1,1.0],0.0); burst=env*np.sqrt(2)*np.sin(2*np.pi*1000*t)
    # programme: pink-ish noise with 4 Hz amplitude modulation and kick-like LF hits
    n=np.cumsum(rng.standard_normal(len(t)))*0.002; n-=np.convolve(n,np.ones(400)/400,'same'); prog=n*(0.6+0.4*np.sin(2*np.pi*4*t))
    kick=np.sin(2*np.pi*55*t)*np.exp(-((t%0.5)*12))*0.8; prog=prog/np.max(abs(prog))*0.7+kick
    for name,x in (("burst",burst),("programme",prog)):
        for mode in (1,0):
            for old in (True,False):
                y,g=gr_trace(x,P(o_mode=mode),old,sr)
                d=np.diff(g[int(0.5*sr):int(6*sr):sr//200])          # 5 ms steps
                sgn=np.sign(d[np.abs(d)>0.05]); flips=int(np.sum(sgn[1:]!=sgn[:-1]))
                print(f"{name:9s} {'LIMIT' if mode else 'COMP '} {'before' if old else 'after '}: GR max {g.max():5.1f} dB, mean {g[int(0.5*sr):int(6*sr)].mean():5.1f}; GR direction reversals (5 ms grid, >0.05 dB) {flips}; out peak {20*np.log10(np.max(abs(y))):+.1f} dBFS; finite {np.isfinite(y).all()}")
# emphasis filter at other sample rates: GR(15k)-GR(500) at max vs flat
def tone(f,L,s,sr): t=np.arange(int(s*sr))/sr; return 10**(L/20)*np.sqrt(2)*np.sin(2*np.pi*f*t)
dsp.HARN='build/harness'
for sr in (44100,96000):
    r=lambda y:20*np.log10(np.sqrt(np.mean(y[-sr//2:]**2)))
    def ogr(f,e):
        x=tone(f,0,3,sr); return r(dsp.run(x,dsp.dyn(o_on=0),sr)[:,0])-r(dsp.run(x,P(o_pr=80,o_emph=e),sr)[:,0])
    print(sr, "emphasis GR(15k)-GR(500): flat", round(ogr(15000,0)-ogr(500,0),2), "max", round(ogr(15000,100)-ogr(500,100),2))
