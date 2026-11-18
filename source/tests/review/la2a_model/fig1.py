# Static model of the LA-2A attenuator from schematic C-10953 rev C (see docs/independent-review/LA2A_MANUAL_CHECK.md).
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'static.py')).read().split('lv = np.arange(-50')[0])
lv = np.arange(-40, 40, 1.0)
def flat_start(R7, gam):
    out = np.array([20*np.log10(solve(10**(L/20), R7, gam, 30)[0]) for L in lv]); gr=(lv-out)-(lv[0]-out[0])
    brk = lv[np.argmax(gr > 1)]
    for i in range(len(lv)-20):
        if max(out[i:i+21]) - out[i] < 1.0: return lv[i]-brk, gr[i]
    return None, None
print("sense difference LIMIT/COMP at given GR (R7=1.8k): 1 + R7/Rcell")
for g in (5, 10, 15, 20, 30):
    a = 10**(-g/20); rsh = a*68e3/(1-a); print(f"  GR {g} dB: Rshunt ~{rsh/1e3:.1f}k -> +{20*np.log10(1+1800/rsh):.2f} dB")
for R7 in (1800, 2700, 10000, 30000, 60000):
    print("gam 2, R7", R7, "-> flat 20 dB window starts (dB above brk, GR there):", flat_start(R7, 2.0))
for gam in (4, 8, 16):
    print("R7 1800, gam", gam, "->", flat_start(1800, gam), "| COMP (R7=0) ->", flat_start(0, gam))
