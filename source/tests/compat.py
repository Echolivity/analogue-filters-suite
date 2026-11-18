#!/usr/bin/env python3
"""Preset / automation / MIDI-mapping compatibility check against the v1.1 device.

Live identifies a Max for Live parameter by the object that owns it (its box id
and its parameter attributes). A Live Set, preset, automation lane or MIDI map
made with v1.1 keeps working when every v1.1 parameter object is unchanged and
still wired to the same gen~ Param. This script verifies exactly that, plus
that the v1.1 gen~ Params keep their names, defaults and ranges."""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
old = json.load(open(os.path.join(HERE, "baseline", "DubFilter_v1.1.maxpat")))["patcher"]
new = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "build", "device", "DubFilter.maxpat")))["patcher"]
ob = {b["box"]["id"]: b["box"] for b in old["boxes"]}
nb = {b["box"]["id"]: b["box"] for b in new["boxes"]}
problems, notes = [], []
for i, b in ob.items():
    if i not in nb:
        problems.append(f"missing box {i}"); continue
    n = nb[i]
    if b.get("text") == "gen~":
        if {k: v for k, v in b.items() if k != "patcher"} != {k: v for k, v in n.items() if k != "patcher"}:
            problems.append("gen~ box attributes changed")
        notes.append("gen~ engine code extended (expected)")
        continue
    if b != n:
        diff = [k for k in set(b) | set(n) if b.get(k) != n.get(k)]
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
print(f"v1.1 boxes checked: {len(ob)}  connections: {len(ol)}  parameters: {len(oldp)}")
print(f"new parameters ({len(added)}): {', '.join(added)}")
for n_ in notes:
    print("note:", n_)
print("COMPATIBLE" if not problems else "INCOMPATIBLE:\n  " + "\n  ".join(problems))
sys.exit(1 if problems else 0)
