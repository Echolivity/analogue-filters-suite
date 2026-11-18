#!/usr/bin/env python3
"""v1.5 UI validation (offline). Checks what can be checked without Max/Live:
patch structure, parameter identity, sync wiring, layout, contrast, availability
rules against the DSP source, and the jsui JavaScript run through tools/jsui_sim.js.
It cannot check Max's rendering or Live's behaviour; see docs/UI_VALIDATION.md."""
import json, os, re, subprocess, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "device")); sys.path.insert(0, os.path.join(ROOT, "src"))
import ui_theme as T, dyn as DYN
P = json.load(open(os.path.join(ROOT, "build/device/DubFilter.maxpat")))["patcher"]
OLD = json.load(open(os.path.join(HERE, "baseline/DubFilter_v1.4.maxpat")))["patcher"]
AV = json.load(open(os.path.join(ROOT, "build/device/ui_availability.json")))
B = [b["box"] for b in P["boxes"]]; byid = {b["id"]: b for b in B}; byv = {b["varname"]: b for b in B if b.get("varname")}
L = [l["patchline"] for l in P["lines"]]
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))
def wired(a, b):
    return any(l["source"][0] == a and l["destination"][0] == b for l in L)
def wired_via(a, b):   # a -> (one object) -> b
    mids = {l["destination"][0] for l in L if l["source"][0] == a}
    return any(wired(m, b) for m in mids)
SIM = os.path.join(ROOT, "tools/jsui_sim.js"); JS = os.path.join(ROOT, "device/jsui")
def sim(f, w, h, args, script):
    r = subprocess.run(["node", SIM, os.path.join(JS, f), str(w), str(h), json.dumps(args), json.dumps(script)], capture_output=True, text=True)
    return json.loads(r.stdout)

# 1 parameters: same set, same definitions, same box ids as v1.4
par = lambda X: {b["box"]["id"]: (b["box"]["varname"], b["box"]["saved_attribute_attributes"]) for b in X["boxes"] if b["box"].get("parameter_enable")}
po, pn = par(OLD), par(P)
check("79 parameters, identical ids, names and definitions to v1.4", po == pn and len(pn) == 79, f"{len(pn)} parameters")
check("parameter table (Live identity) unchanged", OLD["parameters"] == P["parameters"])
gc = lambda X: next(b["box"]["patcher"]["boxes"][2]["box"]["code"] for b in X["boxes"] if b["box"].get("text") == "gen~")
check("gen~ code byte-identical to v1.4 (no DSP change)", gc(OLD) == gc(P))
ol = {json.dumps(l["patchline"], sort_keys=True) for l in OLD["lines"]}
check("all v1.4 connections kept", ol <= {json.dumps(l, sort_keys=True) for l in L})
check("every parameter control visible in presentation", all(byid[i].get("presentation") == 1 for i in pn))

# 2 Info View text
pb = [b for b in B if b.get("parameter_enable")]
check("every parameter has annotation_name, annotation and hint", all(b.get("annotation") and b.get("annotation_name") and b.get("hint") for b in pb))
check("annotations state range/options and default", all(("Default" in b["annotation"]) for b in pb))
check("jsui controls annotated", all(b.get("annotation") for b in B if b["maxclass"] == "jsui"))

# 3 layout: bounds + no overlapping interactive controls (per edit page / chain order)
W = P["devicewidth"]
vis = [b for b in B if b.get("presentation") and not (b.get("hidden") and not b.get("varname", "").startswith("pg") and not b.get("parameter_enable"))]
oob = [b.get("varname", b["id"]) for b in vis if (r := b["presentation_rect"]) and (r[0] < 0 or r[1] < 0 or r[0] + r[2] > W + 0.01 or r[1] + r[3] > T.H + 0.01)]
check("all presented objects inside the device (w=%d, h=169)" % W, not oob, ", ".join(map(str, oob[:5])))
INTER = {"live.dial", "live.tab", "live.text", "live.menu", "live.slider", "live.routing", "live.numbox"}
def page_of(b):
    vn = b.get("varname", "")
    if b.get("parameter_enable") and vn[:2] in ("t_", "o_", "v_", "g_") and not vn.endswith("_on"):
        return "tovg".index(vn[0])
    m = re.match(r"pg(\d)_", vn); return int(m.group(1)) if m else None
ctrls = [b for b in vis if (b["maxclass"] in INTER and not (b.get("hidden") and page_of(b) is None)) or b.get("filename") == "df_button.js"]
def ov(a, b):
    r, s = a["presentation_rect"], b["presentation_rect"]
    return r[0] < s[0] + s[2] - 0.5 and s[0] < r[0] + r[2] - 0.5 and r[1] < s[1] + s[3] - 0.5 and s[1] < r[1] + r[3] - 0.5
bad = [(a.get("varname"), b.get("varname")) for a, b in itertools.combinations(ctrls, 2)
       if ov(a, b) and (page_of(a) is None or page_of(b) is None or page_of(a) == page_of(b))]
check("no two interactive controls overlap (each edit page)", not bad, str(bad[:4]))
# chain block positions for all six orders (from the scripting messages)
blocks_ok = True
msgs = [b["text"] for b in B if b["maxclass"] == "message" and b.get("text", "").startswith("script sendbox")]
names = set(byv)
ref = {c.split()[2] for t in msgs for c in t.split(", ")}
check("scripting messages reference only existing objects", ref <= names, str(sorted(ref - names)[:5]))
for t in msgs:
    rects = {}
    for c in t.split(", "):
        f = c.split(); rects[f[2]] = list(map(float, f[4:8]))
    bgs = [rects[k] for k in rects if k.endswith("_bg")]
    for a_, b_ in itertools.combinations(bgs, 2):
        if a_[0] < b_[0] + b_[2] and b_[0] < a_[0] + a_[2]:
            blocks_ok = False
    gate = byv["blk_G_bg"]["presentation_rect"]
    if any(r[0] + r[2] > gate[0] for r in bgs):
        blocks_ok = False
check("6 chain orders: blocks never overlap each other or the gate block", blocks_ok and len(msgs) == 6)

# 4 sync wiring of custom graphics to native parameters
ordm = byv["c_order"]["id"]
for idx in DYN.PRESETS.values():
    j = byv[f"presetbtn_{idx}"]["id"]
    check(f"preset button {idx}: Chain Order -> button and button -> Chain Order", wired(ordm, j) and wired(j, ordm))
rd = byv["route_diagram"]["id"]
for vn in ("flt_route", "order_sel", "b_pos", "l_on", "h_on", "b_on"):
    check(f"routing diagram follows {vn}", wired_via(byv[vn]["id"], rd))
ag = byv["bpf_arch_glyph"]["id"]
check("arch glyph follows b_arch and b_on", wired_via(byv["b_arch"]["id"], ag) and wired_via(byv["b_on"]["id"], ag))
check("jsui displays have no outlet into the patch", all(not any(l["source"][0] == byv[v]["id"] for l in L) for v in ("route_diagram", "bpf_arch_glyph")))
check("no 'active' message sent to any control (all stay editable)", not any(re.match(r"\s*active\b", b.get("text", "")) for b in B if b["maxclass"] == "message"))

# 5 availability rules vs DSP source
bsrc = open(os.path.join(ROOT, "src/bpf.py")).read()
svf = bsrc[bsrc.index("# --- SVF ---"):bsrc.index("# --- CASCADE ---")]
casc = bsrc[bsrc.index("# --- CASCADE ---"):bsrc.index("# --- MULTIMODE ---")]
_mi = bsrc.index("# --- MULTIMODE ---"); multi = bsrc[_mi:bsrc.index("ARP 4072", _mi)]
check("DSP: SVF reads Q (_R) and not Bandwidth (_gh/_gl/_wb)", "_R" in svf and not re.search(r"_g[hl]\b|_wb", svf))
check("DSP: CASC reads Bandwidth (_gh/_gl) and Q (_R)", "_gh" in casc and "_gl" in casc and "_R" in casc)
check("DSP: MULTI reads Bandwidth (_wb), not Q (_R)", "_wb" in multi and "_R" not in multi)
check("DSP: MULTI raw gain is 1, so Compensation has no effect", "_a < 1.5 ? 1 / {p}_cn : 1)" in bsrc)
dom = lambda vn: range(int(byv[vn]["saved_attribute_attributes"]["valueof"]["parameter_mmax"]) + 1)
def ev(r, vals):
    ex = r["expr"].replace("&&", " and ")
    return bool(eval(re.sub(r"\$i(\d)", lambda m: str(vals[int(m.group(1)) - 1]), ex)))
both = all({ev(r, v) for v in itertools.product(*[dom(s) for s in r["sources"]])} == {True, False} for r in AV)
check(f"{len(AV)} availability rules: every rule reaches both states", both)
check("every availability target is a parameter control", all(byv[t].get("parameter_enable") for r in AV for t in r["targets"]))
def avail_at(vn, st):
    return all(ev(r, [st[s] for s in r["sources"]]) for r in AV if vn in r["targets"])
arch_ok = all(avail_at("b_bw", {"b_on": 1, "b_arch": a}) == (a != 0) and avail_at("b_q", {"b_on": 1, "b_arch": a}) == (a != 2)
              and avail_at("b_comp", {"b_on": 1, "b_arch": a}) == (a != 2) for a in range(3))
r = sim("df_arch.js", 62, 112, [], [["eval", "JSON.stringify([uses(0),uses(1),uses(2)])"]])
U = json.loads(r["evals"][0])
check("arch glyph 'USES' labels agree with the dimming rules and the DSP", arch_ok and [u["bw"] for u in U] == [0, 1, 1] and [u["q"] for u in U] == [1, 1, 0])
rs = open(os.path.join(ROOT, "src/routing.py")).read()
check("DSP: PARALLEL sums rt_rl, rt_rh, rt_rb; HYBRID adds only rt_rb", "rt_rl * rdl" in rs and "z{sub}_{ch} + rt_rb * rdb" in rs)
check("level dials dimmed exactly where the DSP ignores them",
      [avail_at("par_l", {"flt_route": x}) for x in range(3)] == [False, True, False] and [avail_at("par_b", {"flt_route": x}) for x in range(3)] == [False, True, True])

# 6 routing diagram: all 96 states run, topology matches the engine's flow table
flow = [b["text"][4:] for b in B if b["maxclass"] == "message" and b.get("text", "").startswith("set IN >")]
errs, mism = [], []
for route, order, bpos, lo, ho, bo in itertools.product(range(3), range(2), range(2), range(2), range(2), range(2)):
    st = [["route", route], ["order", order], ["bpos", bpos], ["lon", lo], ["hon", ho], ["bon", bo]]
    r = sim("df_routing.js", 188, 49, [], st + [["eval", "JSON.stringify(topology(S))"]])
    errs += r["errors"]
    t = json.loads(r["evals"][0])
    idx = (bpos + 2 * order) if route == 0 else (4 if route == 1 else 5 + order)
    exp = flow[idx]
    if route == 0:
        got = "IN > " + " > ".join(t["series"]) + " > OUT"
    elif route == 1:
        got = "IN > ( LP + HP + BP ) > OUT" if [x[0] for x in t["branches"]] == ["LP", "HP", "BP"] else "?"
    else:
        got = "IN > ( " + " > ".join(t["branches"][0]) + " ) + BP > OUT"
    if got != exp:
        mism.append((route, order, bpos, got, exp))
    if route == 1 and t["dry"] != (not (lo or ho or bo)):
        mism.append(("dry", lo, ho, bo))
check("routing diagram: 96 states draw without error", not errs, str(errs[:2]))
check("routing diagram topology == engine flow for all 96 states", not mism, str(mism[:3]))

# 7 button component: state matrix and click behaviour
r = sim("df_button.js", 70, 15, ["WARM_DUB", 0, "select"], [
    ["int", 3], ["eval", "state()"], ["hover", 2, 2], ["eval", "state()"], ["click", 2, 2], ["eval", "state()"], ["release", 2, 2],
    ["int", 0], ["leave"], ["eval", "state()"], ["hover", 2, 2], ["eval", "state()"], ["click", 2, 2], ["eval", "state()"], ["release", 90, 2],
    ["leave"], ["unavailable", 1], ["eval", "state()"], ["click", 2, 2], ["release", 2, 2], ["int", 3], ["eval", "state()"]])
check("button select mode: off/hover/pressed/selected/selected_hover/selected_pressed/unavailable states",
      r["evals"] == ["off", "hover", "pressed", "selected", "selected_hover", "selected_pressed", "unavailable_on", "unavailable"], str(r["evals"]))
check("button: click inside outputs its index, release outside cancels, unavailable ignores clicks", r["outlets"] == [[0, 0]] and not r["errors"], str(r["outlets"]))
r = sim("df_button.js", 40, 14, ["ON", 1, "toggle"], [["int", 0], ["click", 2, 2], ["release", 2, 2], ["eval", "state()"], ["int", 1], ["click", 2, 2], ["release", 2, 2]])
check("button toggle: requests the opposite value and waits for the parameter echo", r["outlets"] == [[0, 1], [0, 0]] and r["evals"] == ["off"])
r = sim("df_button.js", 40, 14, ["TAP", 1, "momentary"], [["click", 2, 2], ["release", 50, 50]])
check("button momentary: 1 on press, 0 on release", r["outlets"] == [[0, 1], [0, 0]])

# 8 contrast (WCAG ratio)
pairs = [("TEXT on PLATE", T.TEXT, T.PLATE, 7), ("LABEL on PLATE", T.LABEL, T.PLATE, 4.5), ("LABEL on HEADER", T.LABEL, T.HEADER, 4.5),
         ("LABEL on OFF button", T.LABEL, T.OFF, 3.5), ("TEXT_ON on AMBER", T.TEXT_ON, T.AMBER, 7), ("AMBER on PLATE", T.AMBER, T.PLATE, 4.5)]
for n, a, b, need in pairs:
    check(f"contrast {n} >= {need}:1", T.contrast(a, b) >= need, f"{T.contrast(a, b):.1f}:1")
cd = T.contrast(T.TEXT_DIM, T.PLATE)
check("unavailable labels are reduced but visible (1.8..3:1 on plate)", 1.8 <= cd < 3, f"{cd:.1f}:1")
check("unavailable arc distinct from active arc", T.contrast(T.AMBER, T.ARC_OFF) > 2.5, f"{T.contrast(T.AMBER, T.ARC_OFF):.1f}:1")

n_ok = sum(1 for _, ok, _ in results if ok)
print(f"\nUI tests: {n_ok}/{len(results)} passed")
json.dump([{"name": n, "pass": ok, "detail": d} for n, ok, d in results], open(os.path.join(ROOT, "build/ui_results.json"), "w"), indent=1)
sys.exit(0 if n_ok == len(results) else 1)
