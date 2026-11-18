// jsui_sim.js — runs a Dub Filter jsui file outside Max with a minimal mgraphics mock.
// It records drawing to SVG so the components can be tested and previewed offline.
// This checks the JavaScript logic and drawing calls; it is not Max's renderer.
//
// node jsui_sim.js <file.js> <w> <h> '<jsarguments json>' '<script json>' [out.svg]
//   script: list of steps, each [message, ...args] | ["click", x, y] | ["release", x, y]
//           | ["hover", x, y] | ["leave"] | ["eval", "<expression>"]
// prints JSON: { outlets: [...], evals: [...], errors: [...], ops: n }
"use strict";
const fs = require("fs"), vm = require("vm");
const [file, W, H, argsJ, scriptJ, out] = process.argv.slice(2);
const w = Number(W), h = Number(H);
let svg = [], path = [], src = "rgba(0,0,0,1)", lw = 1, font = 9, bold = false, cur = [0, 0], ops = 0;
const col = (r, g, b, a) => `rgba(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)},${a === undefined ? 1 : a})`;
const num = (...v) => { for (const x of v) if (typeof x !== "number" || !isFinite(x)) throw new Error("non-finite drawing argument"); };
const mg = {
  size: [w, h], relative_coords: 0, autofill: 0,
  init() {}, redraw() { this._dirty = true; },
  set_source_rgba(r, g, b, a) { if (Array.isArray(r)) throw new Error("array colour passed"); num(r, g, b, a); src = col(r, g, b, a); ops++; },
  set_line_width(v) { num(v); lw = v; },
  rectangle(x, y, ww, hh) { num(x, y, ww, hh); path.push(`M${x} ${y}h${ww}v${hh}h${-ww}Z`); },
  rectangle_rounded(x, y, ww, hh, rx, ry) { num(x, y, ww, hh, rx, ry); path.push(`M${x + rx} ${y}h${ww - 2 * rx}a${rx} ${ry} 0 0 1 ${rx} ${ry}v${hh - 2 * ry}a${rx} ${ry} 0 0 1 ${-rx} ${ry}h${-(ww - 2 * rx)}a${rx} ${ry} 0 0 1 ${-rx} ${-ry}v${-(hh - 2 * ry)}a${rx} ${ry} 0 0 1 ${rx} ${-ry}Z`); },
  arc(cx, cy, r, a0, a1) { num(cx, cy, r, a0, a1); const full = Math.abs(a1 - a0) >= 2 * Math.PI - 1e-6;
    if (full) path.push(`M${cx + r} ${cy}a${r} ${r} 0 1 1 ${-2 * r} 0a${r} ${r} 0 1 1 ${2 * r} 0Z`);
    else path.push(`M${cx + r * Math.cos(a0)} ${cy + r * Math.sin(a0)}A${r} ${r} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${cx + r * Math.cos(a1)} ${cy + r * Math.sin(a1)}`); },
  move_to(x, y) { num(x, y); cur = [x, y]; path.push(`M${x} ${y}`); },
  line_to(x, y) { num(x, y); cur = [x, y]; path.push(`L${x} ${y}`); },
  close_path() { path.push("Z"); },
  fill() { svg.push(`<path d="${path.join("")}" fill="${src}"/>`); path = []; ops++; },
  stroke() { svg.push(`<path d="${path.join("")}" fill="none" stroke="${src}" stroke-width="${lw}"/>`); path = []; ops++; },
  select_font_face(f) { bold = /bold/i.test(f); },
  set_font_size(s) { num(s); font = s; },
  text_measure(t) { return [String(t).length * font * (bold ? 0.6 : 0.55), font]; },
  show_text(t) { const e = String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    svg.push(`<text x="${cur[0]}" y="${cur[1]}" font-family="Arial, DejaVu Sans" font-weight="${bold ? 700 : 400}" font-size="${font}" fill="${src}">${e}</text>`); ops++; path = []; },
};
const outlets = [], evals = [], errors = [];
const ctx = {
  mgraphics: mg, jsarguments: [file].concat(JSON.parse(argsJ || "[]")), box: { rect: [0, 0, w, h] },
  outlet: (i, ...v) => outlets.push([i].concat(v)), post: () => {}, setinletassist() {}, setoutletassist() {},
  arrayfromargs: (a) => Array.prototype.slice.call(a), messagename: "", Math,
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(file, "utf8"), ctx, { filename: file });
const paint = () => { svg = []; path = []; ctx.paint(); };
try { paint(); } catch (e) { errors.push("initial paint: " + e.message); }
for (const step of JSON.parse(scriptJ || "[]")) {
  const [m, ...a] = step;
  try {
    if (m === "click") ctx.onclick(a[0], a[1], 1);
    else if (m === "release") ctx.ondrag(a[0], a[1], 0);
    else if (m === "hover") ctx.onidle(a[0], a[1]);
    else if (m === "leave") ctx.onidleout();
    else if (m === "eval") { evals.push(vm.runInContext(a[0], ctx)); continue; }
    else if (m === "int") ctx.msg_int(a[0]);
    else if (typeof ctx[m] === "function") ctx[m](...a);
    else { ctx.messagename = m; ctx.anything(...a); }
    paint();
  } catch (e) { errors.push(`${m}: ${e.message}`); }
}
if (out) fs.writeFileSync(out, `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${svg.join("")}</svg>`);
console.log(JSON.stringify({ outlets, evals, errors, ops }));
