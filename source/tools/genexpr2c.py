#!/usr/bin/env python3
"""GenExpr (subset) -> C transpiler used to test the exact gen~ code offline.

Supported: Param / History declarations, user functions with multiple return
values, if / else if / else, for loops in the documented GenExpr form
`for (i = a; cond; i += step) { ... }`, assignment, `+=`, multi-assignment,
ternary, the usual operators and the gen builtins used by the engine.

Static checks performed (each one is a way the code could fail in gen~):
  * every identifier is defined before use (no typos / undeclared names)
  * block scoping: a variable first assigned inside a block is not used after it
  * function arity and return-count consistency at every call site
  * multi-return functions are only used in multi-assignment statements
  * function parameters are never assigned
  * no History is read after it has been written in the main body
"""
import re, sys

TOK = re.compile(r"""
 (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
|(?P<num>(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?)
|(?P<id>[A-Za-z_][A-Za-z_0-9]*)
|(?P<op>\+=|==|!=|<=|>=|&&|\|\||[-+*/%<>=!?:,;(){}])
""", re.S | re.X)

BUILTIN_F = {
    "tanh": ("tanh", 1), "tan": ("tan", 1), "atan": ("atan", 1), "exp": ("exp", 1), "exp2": ("exp2", 1),
    "log2": ("log2", 1), "log": ("log", 1), "log10": ("log10", 1), "pow": ("pow", 2), "sqrt": ("sqrt", 1),
    "abs": ("fabs", 1), "min": ("fmin", 2), "max": ("fmax", 2), "clamp": ("gclamp", 3),
    "floor": ("floor", 1), "sin": ("sin", 1), "cos": ("cos", 1), "fixdenorm": ("fixdenorm", 1),
}
BUILTIN_V = {"samplerate": "g_sr", "pi": "M_PI", "in1": "in1", "in2": "in2", "in3": "in3", "in4": "in4"}
OUTPUTS = {f"out{i}" for i in range(1, 18)}


class Err(Exception):
    pass


def tokenize(src):
    pos, out = 0, []
    line = 1
    while pos < len(src):
        m = TOK.match(src, pos)
        if not m:
            raise Err(f"line {line}: bad char {src[pos]!r}")
        kind = m.lastgroup
        txt = m.group(0)
        if kind != "ws":
            out.append((kind, txt, line))
        line += txt.count("\n")
        pos = m.end()
    out.append(("eof", "", line))
    return out


class P:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self, k=0):
        return self.t[self.i + k]

    def nx(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expect(self, txt):
        tok = self.nx()
        if tok[1] != txt:
            raise Err(f"line {tok[2]}: expected {txt!r} got {tok[1]!r}")
        return tok

    # ---------- program ----------
    def program(self):
        decls, funcs, body = [], {}, []
        while self.peek()[0] != "eof":
            k, txt, ln = self.peek()
            if txt in ("Param", "History"):
                decls.append(self.decl())
            elif k == "id" and txt not in ("if", "for") and self.peek(1)[1] == "(" and self._is_funcdef():
                f = self.funcdef()
                if f["name"] in funcs:
                    raise Err(f"line {ln}: duplicate function {f['name']}")
                funcs[f["name"]] = f
            else:
                body.append(self.stmt())
        return decls, funcs, body

    def _is_funcdef(self):
        j = self.i + 2
        depth = 1
        while depth:
            t = self.t[j][1]
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1
            j += 1
        return self.t[j][1] == "{"

    def decl(self):
        kind = self.nx()[1]
        name = self.nx()
        if name[0] != "id":
            raise Err(f"line {name[2]}: bad decl")
        self.expect("(")
        default = self.signed_num()
        attrs = {}
        while self.peek()[1] == ",":
            self.nx()
            a = self.nx()[1]
            self.expect("=")
            attrs[a] = self.signed_num()
        self.expect(")")
        self.expect(";")
        return dict(kind=kind, name=name[1], default=default, attrs=attrs, line=name[2])

    def signed_num(self):
        sign = 1
        if self.peek()[1] == "-":
            self.nx()
            sign = -1
        t = self.nx()
        if t[0] != "num":
            raise Err(f"line {t[2]}: expected number")
        return sign * float(t[1])

    def funcdef(self):
        name = self.nx()
        self.expect("(")
        args = []
        if self.peek()[1] != ")":
            while True:
                args.append(self.nx()[1])
                if self.peek()[1] == ",":
                    self.nx()
                    continue
                break
        self.expect(")")
        body = self.block()
        return dict(name=name[1], args=args, body=body, line=name[2])

    def block(self):
        self.expect("{")
        out = []
        while self.peek()[1] != "}":
            out.append(self.stmt())
        self.expect("}")
        return out

    def stmt(self):
        k, txt, ln = self.peek()
        if txt == "if":
            self.nx()
            self.expect("(")
            c = self.expr()
            self.expect(")")
            then = self.block()
            els = None
            if self.peek()[1] == "else":
                self.nx()
                if self.peek()[1] == "if":
                    els = [self.stmt()]
                else:
                    els = self.block()
            return ("if", c, then, els, ln)
        if txt == "for":
            self.nx()
            self.expect("(")
            v = self.nx()
            if v[0] != "id":
                raise Err(f"line {v[2]}: for: expected loop variable")
            self.expect("=")
            init = self.expr()
            self.expect(";")
            cond = self.expr()
            self.expect(";")
            v2 = self.nx()
            if v2[1] != v[1]:
                raise Err(f"line {v2[2]}: for: update must increment the loop variable {v[1]}")
            self.expect("+=")
            step = self.expr()
            self.expect(")")
            body = self.block()
            return ("for", v[1], init, cond, step, body, ln)
        if txt == "return":
            self.nx()
            vals = [self.expr()]
            while self.peek()[1] == ",":
                self.nx()
                vals.append(self.expr())
            self.expect(";")
            return ("ret", vals, ln)
        # assignment
        targets = [self.nx()]
        while self.peek()[1] == ",":
            self.nx()
            targets.append(self.nx())
        for t in targets:
            if t[0] != "id":
                raise Err(f"line {t[2]}: bad assignment target {t[1]!r}")
        if len(targets) == 1 and self.peek()[1] == "+=":
            self.nx()
            e = self.expr()
            self.expect(";")
            return ("asg", [targets[0][1]], ("bin", "+", ("var", targets[0][1], ln), e), ln)
        self.expect("=")
        e = self.expr()
        self.expect(";")
        return ("asg", [t[1] for t in targets], e, ln)

    # ---------- expressions ----------
    def expr(self):
        return self.ternary()

    def ternary(self):
        c = self.binop(0)
        if self.peek()[1] == "?":
            self.nx()
            a = self.ternary()
            self.expect(":")
            b = self.ternary()
            return ("?", c, a, b)
        return c

    LEVELS = [["||"], ["&&"], ["==", "!="], ["<", ">", "<=", ">="], ["+", "-"], ["*", "/", "%"]]

    def binop(self, lvl):
        if lvl == len(self.LEVELS):
            return self.unary()
        left = self.binop(lvl + 1)
        while self.peek()[1] in self.LEVELS[lvl]:
            op = self.nx()[1]
            right = self.binop(lvl + 1)
            left = ("bin", op, left, right)
        return left

    def unary(self):
        if self.peek()[1] in ("-", "!"):
            op = self.nx()[1]
            return ("un", op, self.unary())
        return self.primary()

    def primary(self):
        k, txt, ln = self.nx()
        if k == "num":
            return ("num", txt)
        if txt == "(":
            e = self.expr()
            self.expect(")")
            return e
        if k == "id":
            if self.peek()[1] == "(":
                self.nx()
                args = []
                if self.peek()[1] != ")":
                    while True:
                        args.append(self.expr())
                        if self.peek()[1] == ",":
                            self.nx()
                            continue
                        break
                self.expect(")")
                return ("call", txt, args, ln)
            return ("var", txt, ln)
        raise Err(f"line {ln}: unexpected {txt!r}")


# ---------------------------------------------------------------------------
class Compiler:
    def __init__(self, decls, funcs, body):
        self.params = [d for d in decls if d["kind"] == "Param"]
        self.hists = [d for d in decls if d["kind"] == "History"]
        self.pnames = {d["name"] for d in self.params}
        self.hnames = {d["name"] for d in self.hists}
        if self.pnames & self.hnames:
            raise Err("param/history name clash")
        self.funcs = funcs
        self.nret = {}
        for f in funcs.values():
            self.nret[f["name"]] = self._count_ret(f)

    def _count_ret(self, f):
        counts = set()
        def walk(sts):
            for s in sts:
                if s[0] == "ret":
                    counts.add(len(s[1]))
                elif s[0] == "if":
                    walk(s[2])
                    if s[3]:
                        walk(s[3])
                elif s[0] == "for":
                    walk(s[5])
        walk(f["body"])
        if len(counts) != 1:
            raise Err(f"function {f['name']}: inconsistent return counts {counts}")
        last = f["body"][-1]
        if last[0] != "ret":
            raise Err(f"function {f['name']}: must end with return")
        return counts.pop()

    # ---- expression codegen with checks ----
    def ex(self, e, scope, ctx):
        t = e[0]
        if t == "num":
            v = e[1]
            return v if ("." in v or "e" in v or "E" in v) else v + ".0"
        if t == "var":
            n = e[1]
            if n in BUILTIN_V:
                return BUILTIN_V[n]
            if ctx["kind"] == "func":
                if n in ctx["args"]:
                    return "a_" + n
                if not scope.has(n):
                    raise Err(f"line {e[2]}: '{n}' used before assignment in {ctx['name']}")
                return "v_" + n
            # main
            if n in self.pnames:
                return "P_" + n
            if n in self.hnames:
                if n in ctx["hwritten"]:
                    raise Err(f"line {e[2]}: History '{n}' read after write")
                return "Hs_" + n
            if not scope.has(n):
                raise Err(f"line {e[2]}: '{n}' used before assignment (or out of scope)")
            return "v_" + n
        if t == "un":
            return f"({e[1]}{self.ex(e[2], scope, ctx)})"
        if t == "bin":
            a = self.ex(e[2], scope, ctx)
            b = self.ex(e[3], scope, ctx)
            op = e[1]
            if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return f"((double)(({a}) {op} ({b})))"
            if op == "%":
                return f"fmod({a}, {b})"
            return f"({a} {op} {b})"
        if t == "?":
            return f"(({self.ex(e[1], scope, ctx)}) != 0.0 ? ({self.ex(e[2], scope, ctx)}) : ({self.ex(e[3], scope, ctx)}))"
        if t == "call":
            name, args, ln = e[1], e[2], e[3]
            cargs = [self.ex(a, scope, ctx) for a in args]
            if name in BUILTIN_F:
                cn, ar = BUILTIN_F[name]
                if len(args) != ar:
                    raise Err(f"line {ln}: {name} expects {ar} args")
                return f"{cn}({', '.join(cargs)})"
            if name in self.funcs:
                f = self.funcs[name]
                if len(args) != len(f["args"]):
                    raise Err(f"line {ln}: {name} expects {len(f['args'])} args, got {len(args)}")
                if self.nret[name] != 1:
                    raise Err(f"line {ln}: multi-return function {name} used in expression")
                return f"F_{name}({', '.join(cargs)})"
            raise Err(f"line {ln}: unknown function {name}")
        raise Err(f"bad expr {e}")

    # ---- statements ----
    def st(self, s, scope, ctx, out, ind):
        pad = "    " * ind
        if s[0] == "asg":
            targets, e, ln = s[1], s[2], s[3]
            if len(targets) > 1:
                if e[0] != "call" or e[1] not in self.funcs:
                    raise Err(f"line {ln}: multi-assign needs a user function call")
                name = e[1]
                if self.nret[name] != len(targets):
                    raise Err(f"line {ln}: {name} returns {self.nret[name]} values, {len(targets)} targets")
                f = self.funcs[name]
                if len(e[2]) != len(f["args"]):
                    raise Err(f"line {ln}: {name} expects {len(f['args'])} args, got {len(e[2])}")
                cargs = [self.ex(a, scope, ctx) for a in e[2]]
                tmps = [f"_t{ctx['tmp'] + i}" for i in range(len(targets))]
                ctx["tmp"] += len(targets)
                out.append(pad + "{ double " + ", ".join(tmps) + "; F_" + name + "(" +
                           ", ".join(cargs + ["&" + t for t in tmps]) + ");")
                for tv, tn in zip(targets, tmps):
                    out.append(pad + "  " + self.lhs(tv, scope, ctx, ln) + " = " + tn + ";")
                out.append(pad + "}")
            else:
                val = self.ex(e, scope, ctx)
                out.append(pad + self.lhs(targets[0], scope, ctx, ln) + " = " + val + ";")
        elif s[0] == "if":
            c = self.ex(s[1], scope, ctx)
            out.append(pad + f"if (({c}) != 0.0) {{")
            self.blk(s[2], scope.child(), ctx, out, ind + 1)
            if s[3] is not None:
                out.append(pad + "} else {")
                self.blk(s[3], scope.child(), ctx, out, ind + 1)
            out.append(pad + "}")
        elif s[0] == "for":
            var, init, cond, step, body, ln = s[1], s[2], s[3], s[4], s[5], s[6]
            sc = scope.child()
            iv = self.ex(init, scope, ctx)
            lv = self.lhs(var, sc, ctx, ln)
            cv = self.ex(cond, sc, ctx)
            stv = self.ex(step, sc, ctx)
            out.append(pad + f"for ({lv} = {iv}; ({cv}) != 0.0; {lv} += {stv}) {{")
            self.blk(body, sc.child(), ctx, out, ind + 1)
            out.append(pad + "}")
        elif s[0] == "ret":
            if ctx["kind"] != "func":
                raise Err(f"line {s[2]}: return outside function")
            vals = [self.ex(v, scope, ctx) for v in s[1]]
            if len(vals) == 1:
                out.append(pad + f"return {vals[0]};")
            else:
                tmps = [f"_r{i}" for i in range(len(vals))]
                out.append(pad + "{ double " + ", ".join(f"{t} = {v}" for t, v in zip(tmps, vals)) + ";")
                for i, t in enumerate(tmps):
                    out.append(pad + f"  *o{i} = {t};")
                out.append(pad + "  return; }")

    def blk(self, sts, scope, ctx, out, ind):
        for s in sts:
            self.st(s, scope, ctx, out, ind)

    def lhs(self, name, scope, ctx, ln):
        if ctx["kind"] == "func":
            if name in ctx["args"]:
                raise Err(f"line {ln}: assignment to function parameter {name}")
            if name in BUILTIN_V or name in BUILTIN_F:
                raise Err(f"line {ln}: assignment to builtin {name}")
            scope.define(name)
            ctx["locals"].add(name)
            return "v_" + name
        if name in OUTPUTS:
            return f"outs[{int(name[3:]) - 1}]"
        if name in self.pnames:
            raise Err(f"line {ln}: assignment to Param {name}")
        if name in self.hnames:
            ctx["hwritten"].add(name)
            return "Hs_" + name
        if name in BUILTIN_V or name in BUILTIN_F or name in self.funcs:
            raise Err(f"line {ln}: assignment to reserved name {name}")
        scope.define(name)
        ctx["locals"].add(name)
        return "v_" + name

    def compile(self):
        out = []
        out.append("#include <math.h>\n#include <string.h>\n")
        out.append("static double g_sr = 48000.0;")
        out.append("static inline double gclamp(double x, double a, double b){ return x < a ? a : (x > b ? b : x); }")
        out.append("static inline double fixdenorm(double x){ return fabs(x) < 1e-30 ? 0.0 : x; }")
        for d in self.params:
            out.append(f"static double P_{d['name']} = {d['default']!r};")
        for d in self.hists:
            out.append(f"static double Hs_{d['name']} = {d['default']!r};")
        # prototypes
        for f in self.funcs.values():
            out.append(self.proto(f) + ";")
        for f in self.funcs.values():
            ctx = dict(kind="func", name=f["name"], args=set(f["args"]), locals=set(), tmp=0)
            body = []
            self.blk(f["body"], Scope(), ctx, body, 1)
            out.append(self.proto(f) + " {")
            if ctx["locals"]:
                out.append("    double " + ", ".join(f"v_{n} = 0.0" for n in sorted(ctx["locals"])) + ";")
            out.extend(body)
            out.append("}")
        ctx = dict(kind="main", name="main", args=set(), locals=set(), tmp=0, hwritten=set())
        body = []
        self.blk(self.body_stmts, Scope(), ctx, body, 1)
        out.append("void gen_perform(double in1, double in2, double in3, double in4, double* outs) {")
        if ctx["locals"]:
            out.append("    double " + ", ".join(f"v_{n} = 0.0" for n in sorted(ctx["locals"])) + ";")
        out.extend(body)
        out.append("}")
        # reset + param setter
        out.append("void gen_reset(void) {")
        for d in self.hists:
            out.append(f"    Hs_{d['name']} = {d['default']!r};")
        for d in self.params:
            out.append(f"    P_{d['name']} = {d['default']!r};")
        out.append("}")
        out.append("int gen_set_param(const char* n, double v) {")
        for d in self.params:
            lo = d["attrs"].get("min", -1e300)
            hi = d["attrs"].get("max", 1e300)
            out.append(f"    if (!strcmp(n, \"{d['name']}\")) {{ P_{d['name']} = gclamp(v, {lo!r}, {hi!r}); return 0; }}")
        out.append("    return -1;\n}")
        out.append("void gen_set_sr(double sr) { g_sr = sr; }")
        return "\n".join(out) + "\n"

    def proto(self, f):
        args = [f"double a_{a}" for a in f["args"]]
        n = self.nret[f["name"]]
        if n == 1:
            return f"static double F_{f['name']}({', '.join(args)})"
        args += [f"double* o{i}" for i in range(n)]
        return f"static void F_{f['name']}({', '.join(args)})"


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.names = set()

    def has(self, n):
        return n in self.names or (self.parent is not None and self.parent.has(n))

    def define(self, n):
        if not self.has(n):
            self.names.add(n)

    def child(self):
        return Scope(self)


def transpile(src):
    decls, funcs, body = P(tokenize(src)).program()
    c = Compiler(decls, funcs, body)
    c.body_stmts = body
    return c.compile(), c


if __name__ == "__main__":
    src = open(sys.argv[1]).read()
    try:
        code, comp = transpile(src)
    except Err as e:
        print("GENEXPR CHECK FAILED:", e)
        sys.exit(1)
    open(sys.argv[2], "w").write(code)
    print(f"ok: {len(comp.params)} params, {len(comp.hists)} histories, {len(comp.funcs)} functions")
