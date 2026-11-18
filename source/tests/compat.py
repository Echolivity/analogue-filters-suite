#!/usr/bin/env python3
"""Preset / automation / MIDI-mapping compatibility check against the v1.1 device.

Live identifies a Max for Live parameter by the object that owns it (its box id
and its parameter attributes). A Live Set, preset, automation lane or MIDI map
made with v1.1 keeps working when every v1.1 parameter object is unchanged and
still wired to the same gen~ Param. This script verifies exactly that, plus
that the v1.1 gen~ Params keep their names, defaults and ranges."""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
base_name = next((a[7:] for a in sys.argv[1:] if a.startswith("--base=")), "DubFilter_v1.1.maxpat")
old = json.load(open(os.path.join(HERE, "baseline", base_name)))["patcher"]
new = json.load(open(args[0] if args else os.path.join(HERE, "..", "build", "device", "DubFilter.maxpat")))["patcher"]
GEN_IO = {"patcher", "numinlets", "numoutlets", "outlettype"}  # v1.3: gen~ gains key inlets + meter outlets
# v1.5 --ui: a presentation-only redesign may change how a box looks and where it sits,
# never what it is. Allowed: geometry, visibility, fonts, colours, Info View text, comment
# text and the thispatcher scripting messages that place/show blocks. Everything a Live Set,
# preset, automation lane or MIDI map depends on (maxclass, varname, parameter definition,
# connections, gen~ Params) must stay identical; with a v1.4+ base the gen~ code must be
# byte-identical (no DSP change).
UI = "--ui" in sys.argv
UI_KEYS = {"presentation_rect", "presentation", "patching_rect", "hidden", "fontsize", "fontface", "fontname",
           "textjustification", "rounded", "border", "annotation", "annotation_name", "hint", "num_lines_presentation",
           "background"}
UI_TEXT = {"comment"}
def ui_key_ok(b, k):
    if k in UI_KEYS or k.endswith("color"):
        return True
    if k == "text" and b.get("maxclass") in UI_TEXT:
        return True
    if k == "text" and b.get("maxclass") == "message" and str(b.get("text", "")).startswith("script "):
        return True
    return False
ob = {b["box"]["id"]: b["box"] for b in old["boxes"]}
nb = {b["box"]["id"]: b["box"] for b in new["boxes"]}
problems, notes, notes_ui = [], [], []
for i, b in ob.items():
    if i not in nb:
        problems.append(f"missing box {i}"); continue
    n = nb[i]
    if b.get("text") == "gen~":
        if {k: v for k, v in b.items() if k not in GEN_IO} != {k: v for k, v in n.items() if k not in GEN_IO}:
            problems.append("gen~ box attributes changed")
        if n["numinlets"] < b["numinlets"] or n["numoutlets"] < b["numoutlets"]:
            problems.append("gen~ lost inlets/outlets")
        oi = {json.dumps(x["box"].get("text")) for x in b["patcher"]["boxes"]}
        ni = {json.dumps(x["box"].get("text")) for x in n["patcher"]["boxes"]}
        if not oi <= ni:
            problems.append("gen~ inner in/out objects missing")
        notes.append(f"gen~ engine code extended; inlets {b['numinlets']}->{n['numinlets']}, outlets {b['numoutlets']}->{n['numoutlets']} (expected)")
        continue
    if b != n:
        diff = [k for k in set(b) | set(n) if b.get(k) != n.get(k)]
        if UI:
            bad = [k for k in diff if not ui_key_ok(b, k)]
            if b.get("maxclass") == "message" and "text" in diff:
                if not all(c.strip().startswith(("script sendbox ", "script show ", "script hide ")) for c in n["text"].split(",")):
                    bad.append("text(non-scripting)")
            if b.get("parameter_enable") and n.get("presentation") != 1:
                bad.append("parameter control removed from presentation")
            if bad:
                problems.append(f"box {i} ({b.get('maxclass')} {b.get('varname', b.get('text', ''))}) changed: {bad}")
            else:
                notes_ui.append(i)
            continue
        problems.append(f"box {i} ({b.get('maxclass')} {b.get('varname', b.get('text', ''))}) changed: {diff}")
ol = {json.dumps(l["patchline"], sort_keys=True) for l in old["lines"]}
nl = {json.dumps(l["patchline"], sort_keys=True) for l in new["lines"]}
miss = ol - nl
if miss:
    problems.append(f"{len(miss)} v1.1 connections missing")
for k, v in old["parameters"].items():
    if new["parameters"].get(k) != v:
        problems.append(f"parameter entry {k} changed")
gold = lambda P: {m.group(1): m.group(2) for m in re.finditer(r"Param (\w+)\((.*?)\);", P)}
code = lambda P: next(b["box"]["patcher"]["boxes"][2]["box"]["code"] for b in P["boxes"] if b["box"].get("text") == "gen~")
og, ng = gold(code(old)), gold(code(new))
for k, v in og.items():
    if ng.get(k) != v:
        problems.append(f"gen~ Param {k} changed: {v} -> {ng.get(k)}")
oldp = [b["saved_attribute_attributes"]["valueof"]["parameter_longname"] for b in ob.values() if b.get("parameter_enable")]
newp = [b["saved_attribute_attributes"]["valueof"]["parameter_longname"] for b in nb.values() if b.get("parameter_enable")]
added = [p for p in newp if p not in oldp]
dups = len(newp) - len(set(newp))
if dups:
    problems.append(f"{dups} duplicate parameter names")
if UI:
    oc, nc = code(old), code(new)
    if base_name >= "DubFilter_v1.4" and oc != nc and "--allow-dsp" not in sys.argv:
        problems.append("gen~ code differs from the base: the UI release must not change DSP")
    elif oc == nc:
        notes.append("gen~ code byte-identical to the base (DSP unchanged)")
    else:
        notes.append("gen~ code changed (--allow-dsp: a DSP release); every base gen~ Param is still checked above")
    notes.append(f"{len(notes_ui)} boxes restyled/moved (presentation-only attributes)")
print(f"[{base_name}] boxes checked: {len(ob)}  connections: {len(ol)}  parameters: {len(oldp)}")
print(f"new parameters ({len(added)}): {', '.join(added)}")
for n_ in notes:
    print("note:", n_)
print("COMPATIBLE" if not problems else "INCOMPATIBLE:\n  " + "\n  ".join(problems))
sys.exit(1 if problems else 0)
