# Static model of the LA-2A attenuator from schematic C-10953 rev C (see docs/independent-review/LA2A_MANUAL_CHECK.md).
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'static.py')).read().split('lv = np.arange(-50')[0])
lv = np.arange(-40, 40, 1.0)
def curve(R7, gam):
    out = np.array([20*np.log10(solve(10**(L/20), R7, gam, 30)[0]) for L in lv]); gr=(lv-out)-(lv[0]-out[0]); return out, gr
for gam in (2.0, 2.5, 3.0, 3.5, 4.0):
    oc, gc = curve(0, gam); ol, gl = curve(1800, gam)
    brk = lv[np.argmax(gl > 1)]
    fs = next(((lv[i]-brk, round(gl[i],1)) for i in range(len(lv)-20) if max(ol[i:i+21]) - ol[i] < 1.0), None)
    # Figure 1: output rise from breakaway to +10 / +15 / +30 dB above
    ib = np.searchsorted(lv, brk)
    fig = [round(ol[ib+k]-ol[ib], 1) for k in (5, 10, 15, 30)]
    # COMP: 6 dB input step -> output step, at GR 6, 12, 18 dB
    cr = []
    for g in (6, 12, 18):
        i = np.argmax(gc >= g); cr.append(round(6/(oc[i+6]-oc[i]), 2))
    print(f"gam {gam}: LIMIT flat window start {fs}; LIMIT out rise at brk+5/10/15/30: {fig} (Fig.1: ~3.4/5.1/5.6/5.7) | COMP 6-dB ratio at GR 6/12/18: {cr} (addendum ~2.6-3)")
