# LA-2A OPTO LIMIT curve from -70 dBFS: Figure 1 metric and the dip before the 40 dB floor. Run from source/.
import sys; sys.path.insert(0,'tests')
import numpy as np, dsp
SR=48000
def tone(f,L,s=3.0): t=np.arange(int(s*SR))/SR; return 10**(L/20)*np.sqrt(2)*np.sin(2*np.pi*f*t)
r=lambda y:20*np.log10(np.sqrt(np.mean(y[-SR//2:]**2)))
lv=np.arange(-70,13,2.0)
for pr in (60,80,100):
    out=np.array([r(dsp.run(tone(1000,L),dsp.dyn(o_on=1,o_pr=pr,o_mode=1,o_src=0,o_hpf=20,o_mix=100),SR)[:,0]) for L in lv])
    gr=(lv-out)-(lv[0]-out[0]); brk=lv[np.argmax(gr>1)]; ip=int(np.argmax(out)); it=ip+int(np.argmin(out[ip:]))
    rise=[round(out[np.searchsorted(lv,brk+k)]-out[np.searchsorted(lv,brk)],1) for k in (5,10,15,30) if brk+k<=lv[-1]]
    print(f"PR{pr}: brk {brk:+.0f} dBFS; Fig1 metric {rise}; peak {out[ip]-out[0]:+.1f} at {lv[ip]:+.0f} dBFS (GR {gr[ip]:.0f}); trough {out[it]-out[ip]:+.1f} dB below peak at {lv[it]:+.0f} dBFS (GR {gr[it]:.0f})")
print("--- output vs breakaway (dB), LIMIT; GR in brackets")
import itertools
for pr in (80,):
    out=np.array([r(dsp.run(tone(1000,L),dsp.dyn(o_on=1,o_pr=pr,o_mode=1,o_src=0,o_hpf=20,o_mix=100),SR)[:,0]) for L in lv])
    gr=(lv-out)-(lv[0]-out[0]); brk=lv[np.argmax(gr>1)]; ib=np.searchsorted(lv,brk)
    print(" ".join(f"+{int(lv[i]-brk)}:{out[i]-out[ib]:+.1f}({gr[i]:.0f})" for i in range(ib,len(lv),2)))
    pre=[i for i in range(ib,len(lv)) if gr[i]<39]; ip=max(pre,key=lambda i:out[i]); it=min(pre[pre.index(ip):],key=lambda i:out[i])
    print(f"peak +{lv[ip]-brk:.0f} above brk, trough {out[it]-out[ip]:+.1f} dB at +{lv[it]-brk:.0f} (GR {gr[it]:.0f})")
