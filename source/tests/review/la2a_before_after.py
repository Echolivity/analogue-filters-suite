# LA-2A OPTO check (v1.6). Run from source/; needs build/harness and build/harness_v15 (built by build.sh).
import sys; sys.path.insert(0,'tests')
import numpy as np, dsp
SR=48000
def tone(f,L,s=4.0): t=np.arange(int(s*SR))/SR; return 10**(L/20)*np.sqrt(2)*np.sin(2*np.pi*f*t)
r=lambda y:20*np.log10(np.sqrt(np.mean(y[-SR//2:]**2)))
def run(x,p,old,sr=SR,meters=False):
    if old:
        p={k:v for k,v in p.items() if k not in('eng_mode','ovs_hi')}; dsp.HARN='build/harness_v15'
    else: dsp.HARN='build/harness'
    return dsp.run(x,p,sr,meters=meters) if meters else dsp.run(x,p,sr)
P=lambda **k: dsp.dyn(**dict(dict(o_on=1,o_pr=60,o_mode=1,o_emph=0,o_src=0,o_hpf=20,o_mix=100),**k))
lv=np.arange(-40,21,2.0)
for old in (True,False):
    tag='before' if old else 'after '
    for pr in (80,100):
        out=np.array([r(run(tone(1000,L),P(o_pr=pr),old)[:,0]) for L in lv]); gr=(lv-out)-(lv[0]-out[0])
        brk=lv[np.argmax(gr>1)]
        top=out[np.searchsorted(lv,0)]-out[np.searchsorted(lv,-20)]   # original metric: top 20 dB up to 0 dBFS
        best=min((max(out[i:i+11])-out[i],lv[i]) for i in range(len(lv)-10))
        rise=[round(out[np.searchsorted(lv,brk+k)]-out[np.searchsorted(lv,brk)],1) for k in (5,10,15,30) if brk+k<=lv[-1]]
        print(f"{tag} LIMIT PR{pr}: brk {brk:+.0f}; rise -20..0 dBFS {top:.2f} dB; best 20-dB window rise {best[0]:.2f} dB starting {best[1]-brk:+.0f} above brk; out rise brk+5/10/15/30 {rise}")
