"""Static checks for gen~ GenExpr compatibility (v1.6).

Max's gen~ compiler is not available in CI, and the C transpiler (tools/genexpr2c.py) is more permissive than
gen~. This lint catches the constructs most likely to make gen~ reject the code, using the v1.5 code (which
compiled in Max) as the reference for what is known to work:

  1. block scoping: a variable first assigned inside a { } block is local to that block in GenExpr; using it after
     the block closes is an error in gen~ ("not declared");
  2. use before assignment at the same or an outer level;
  3. names that shadow gen~ operators / constants (e.g. `rate`, `mix`, `e`, `step`);
  4. calls to functions that are neither user-defined, nor used by v1.5, nor in gen~'s documented operator set;
  5. number literal forms not present in v1.5 (e.g. exponent notation);
  6. function arity / return count beyond what v1.5 compiled.
Usage: genexpr_lint.py build/dubfilter.genexpr [tests/baseline/DubFilter_v1.5.maxpat]
"""
import json
import re
import sys

GEN_OPERATORS = set("""
abs absdiff accum acos acosh and asin asinh atan atan2 atanh bool buffer ceil change channels clamp clip cos cosh
counter cycle data dcblock degrees delay delta dim div elapsed eq exp exp2 fastcos fastexp fastpow fastsin fasttan
fixdenorm fixnan floor fold fract ftom gate gen gt gte history hypot in int interp isdenorm isnan latch ln log log10
log2 lookup lt lte max maximum min minimum mix mod mstosamps mtof mul mulequals neg neq noise not or out param
peek phasor plusequals poke pow radians rate rdiv round rsub sah samplerate samplestoms scale selector sign sin sinh
slide smoothstep sqrt step sub switch t60 t60time tan tanh train trunc vectorsize wave wrap xor
""".split())
GEN_CONSTANTS = set("pi twopi halfpi invpi e ln2 ln10 log2e log10e sqrt2 sqrt1_2 degtorad radtodeg PI TWOPI".split())
KEYWORDS = set("if else for while return break continue History Param Buffer Data Delay".split())

TOK = re.compile(r"""(?P<num>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)|(?P<id>[A-Za-z_]\w*)|(?P<op>==|!=|<=|>=|&&|\|\||[-+*/%<>=!?:,;(){}\[\]])""")


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    return re.sub(r"//[^\n]*", " ", s)


def tokens(s):
    out = []
    for m in TOK.finditer(s):
        k = m.lastgroup
        out.append((k, m.group(k), s.count("\n", 0, m.start()) + 1))
    return out


def split_functions(toks):
    """Returns (globals_decl_names, functions{name:(params, body_tokens)}, main_tokens)."""
    funcs, main, gdecl = {}, [], set()
    i = 0
    while i < len(toks):
        k, v, ln = toks[i]
        if k == "id" and v in ("History", "Param", "Buffer", "Data", "Delay"):
            gdecl.add(toks[i + 1][1])
            while toks[i][1] != ";":
                i += 1
            i += 1
            continue
        # function definition: id ( ids ) {
        if k == "id" and i + 1 < len(toks) and toks[i + 1][1] == "(":
            j = i + 2
            params, ok = [], True
            while toks[j][1] != ")":
                if toks[j][0] == "id":
                    params.append(toks[j][1])
                elif toks[j][1] != ",":
                    ok = False
                j += 1
            if ok and j + 1 < len(toks) and toks[j + 1][1] == "{":
                depth, b = 0, j + 1
                body = []
                while True:
                    if toks[b][1] == "{":
                        depth += 1
                    elif toks[b][1] == "}":
                        depth -= 1
                    body.append(toks[b])
                    b += 1
                    if depth == 0:
                        break
                funcs[v] = (params, body)
                i = b
                continue
        main.append(toks[i])
        i += 1
    return gdecl, funcs, main


def scope_check(toks, initial, known_globals, where, issues):
    """Walk statements; track block scopes. Declaration = first assignment target."""
    scopes = [set(initial)]
    pending_close = []   # stack of the scope sets popped, for "used after block" diagnosis
    block_local = {}     # name -> line where it was declared inside a block that has since closed

    def visible(n):
        return any(n in s for s in scopes)

    i = 0
    n = len(toks)
    while i < n:
        k, v, ln = toks[i]
        if v == "{":
            scopes.append(set())
            i += 1
            continue
        if v == "}":
            closed = scopes.pop()
            for nm in closed:
                block_local.setdefault(nm, ln)
            i += 1
            continue
        # assignment targets: id (, id)* = (not ==)
        if k == "id" and v not in KEYWORDS:
            j, names = i, []
            while j < n and toks[j][0] == "id":
                names.append(toks[j][1])
                if j + 1 < n and toks[j + 1][1] == ",":
                    j += 2
                    continue
                break
            if j + 1 < n and toks[j + 1][1] == "=" and (i == 0 or toks[i - 1][1] in (";", "{", "}", ")", "(")):
                for nm in names:
                    if not visible(nm):
                        scopes[-1].add(nm)
                i = j + 2
                continue
        if k == "id" and v not in KEYWORDS:
            is_call = i + 1 < n and toks[i + 1][1] == "("
            if not is_call and not visible(v) and v not in known_globals and v not in GEN_CONSTANTS:
                if v in block_local:
                    issues.append(f"{where}: line {ln}: '{v}' used outside the block that declared it (declared in a block closed at line {block_local[v]})")
                else:
                    issues.append(f"{where}: line {ln}: '{v}' used before assignment")
        i += 1
    return issues


def literal_forms(toks):
    forms = set()
    for k, v, ln in toks:
        if k == "num":
            forms.add("exp" if re.search("[eE]", v) else ("lead-dot" if v.startswith(".") else ("trail-dot" if v.endswith(".") else "plain")))
    return forms


def returns_count(body):
    best = 0
    for i, (k, v, ln) in enumerate(body):
        if v == "return":
            c, j, depth = 1, i + 1, 0
            while body[j][1] != ";":
                if body[j][1] == "(":
                    depth += 1
                elif body[j][1] == ")":
                    depth -= 1
                elif body[j][1] == "," and depth == 0:
                    c += 1
                j += 1
            best = max(best, c)
    return best


def calls(toks):
    return {toks[i][1] for i in range(len(toks) - 1) if toks[i][0] == "id" and toks[i + 1][1] == "("
            and toks[i][1] not in KEYWORDS}


def analyse(code):
    toks = tokens(strip_comments(code))
    g, f, m = split_functions(toks)
    return toks, g, f, m


def main(path, base):
    code = open(path).read()
    toks, gdecl, funcs, main_t = analyse(code)
    issues = []
    builtins = {"in1", "in2", "in3", "in4", "samplerate", "vectorsize"} | {f"out{i}" for i in range(1, 64)}
    known = gdecl | builtins | set(funcs)
    for name, (params, body) in funcs.items():
        scope_check(body[1:-1], params, known - gdecl, f"function {name}", issues)   # functions cannot see Params/Histories
        for p in params:
            if p in GEN_OPERATORS or p in GEN_CONSTANTS:
                issues.append(f"function {name}: parameter '{p}' shadows a gen~ operator/constant")
    scope_check(main_t, set(), known, "main", issues)
    # names shadowing gen~ operators / constants (assignment targets)
    stmt_toks = main_t + [t for p_, b_ in funcs.values() for t in b_]     # excludes Param/History declarations
    assigned = {stmt_toks[i][1] for i in range(len(stmt_toks) - 1) if stmt_toks[i][0] == "id" and stmt_toks[i + 1][1] == "="}
    for nm in sorted(assigned & (GEN_OPERATORS | GEN_CONSTANTS)):
        issues.append(f"variable '{nm}' shadows a gen~ operator/constant")
    # reference comparison with v1.5
    ref = None
    if base:
        P = json.load(open(base))

        def walk(bs):
            for b in bs:
                yield b["box"]
                if "patcher" in b["box"]:
                    yield from walk(b["box"]["patcher"]["boxes"])
        for b in walk(P["patcher"]["boxes"]):
            if "code" in b:
                ref = b["code"]
    report = {}
    if ref:
        rt, rg, rf, rm = analyse(ref)
        ref_calls = calls(rt) | set(rf)
        rstmt = rm + [t for p_, b_ in rf.values() for t in b_]
        ref_calls = calls(rstmt) | set(rf)
        for c in sorted(calls(stmt_toks) - set(funcs) - ref_calls):
            if c not in GEN_OPERATORS:
                issues.append(f"call to '{c}': not a user function, not used by v1.5 and not a documented gen~ operator")
            else:
                report.setdefault("new gen~ operators used (documented, not used by v1.5)", []).append(c)
        nf = literal_forms(toks) - literal_forms(rt)
        if nf:
            issues.append(f"number literal forms not used by v1.5: {sorted(nf)}")
        ra = max(len(p) for p, b in rf.values()); rr = max(returns_count(b) for p, b in rf.values())
        na = max(len(p) for p, b in funcs.values()); nr = max(returns_count(b) for p, b in funcs.values())
        report["max function args (v1.5 -> now)"] = (ra, na)
        report["max function returns (v1.5 -> now)"] = (rr, nr)
        report["functions (v1.5 -> now)"] = (len(rf), len(funcs))
        if na > ra or nr > rr:
            report["NOTE"] = "larger functions than v1.5 compiled (gen~ documents no limit; flagged for the Max test)"
    for k, v in report.items():
        print(f"  {k}: {v}")
    if issues:
        print(f"GenExpr lint: {len(issues)} issue(s)")
        for s in issues:
            print("  FAIL", s)
        return 1
    print("GenExpr lint: 0 issues")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
