// df_arch.js — Dub Filter v1.5 band-pass topology glyph (jsui + mgraphics). Display only.
//
// Shows the structure behind the selected BPF Architecture and which width controls it
// reads, as implemented in source/src/bpf.py:
//   SVF   : one 2-pole state-variable band-pass; width from Q        (Bandwidth unused)
//   CASC  : 2-pole HP into 2-pole LP; edges from Bandwidth, edge Q from Q
//   MULTI : 4-pole ladder, band-pass by pole mixing; Bandwidth sets the order mix (Q and
//           Compensation unused: the tap gain is unity)
// Messages: arch n, on n

inlets = 1;
outlets = 0;
setinletassist(0, "arch <0..2>; on <0|1>");

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var C = {
    bg: [0.090, 0.086, 0.082, 1], wire: [0.949, 0.627, 0.227, 1], wireOff: [0.369, 0.345, 0.314, 1],
    box: [0.204, 0.192, 0.176, 1], edge: [0.486, 0.447, 0.400, 1], text: [0.925, 0.894, 0.831, 1],
    label: [0.639, 0.604, 0.549, 1], dim: [0.369, 0.345, 0.314, 1]
};
var A = { arch: 0, on: 0 };
var NAMES = ["SVF", "CASCADE", "MULTIMODE"];
var USES = ["Q", "BW + Q", "BW"];

function arch(v) { A.arch = Math.max(0, Math.min(2, v | 0)); mgraphics.redraw(); }
function on(v) { A.on = v ? 1 : 0; mgraphics.redraw(); }

// which BPF width controls the architecture reads (offline tests compare with bpf.py)
function uses(a) { return [{ bw: 0, q: 1, comp: 1 }, { bw: 1, q: 1, comp: 1 }, { bw: 1, q: 0, comp: 0 }][a]; }

function size() {
    if (mgraphics.size) return mgraphics.size;
    return [box.rect[2] - box.rect[0], box.rect[3] - box.rect[1]];
}
function rgba(c) { mgraphics.set_source_rgba(c[0], c[1], c[2], c[3]); }

function text(t, cx, y, sz, col) {
    var g = mgraphics;
    g.select_font_face("Arial Bold");
    g.set_font_size(sz);
    var tm = g.text_measure(t);
    rgba(col);
    g.move_to(cx - tm[0] / 2, y);
    g.show_text(t);
}

function blk(t, cx, cy, w, h, lit) {
    var g = mgraphics;
    rgba(C.box);
    g.rectangle_rounded(cx - w / 2, cy - h / 2, w, h, 2, 2);
    g.fill();
    rgba(lit ? C.wire : C.edge);
    g.set_line_width(1);
    g.rectangle_rounded(cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, 2, 2);
    g.stroke();
    text(t, cx, cy + 2.5, 7, lit ? C.text : C.dim);
}

function vline(x, y0, y1, lit) {
    var g = mgraphics;
    rgba(lit ? C.wire : C.wireOff);
    g.set_line_width(lit ? 1.5 : 1);
    g.move_to(x, y0);
    g.line_to(x, y1);
    g.stroke();
}

function paint() {
    var s = size(), w = s[0], h = s[1], g = mgraphics, lit = A.on === 1, cx = w / 2;
    rgba(C.bg);
    g.rectangle_rounded(0, 0, w, h, 3, 3);
    g.fill();
    text(NAMES[A.arch], cx, 11, 7.5, lit ? C.wire : C.label);
    var top = 17, bot = h - 18;
    if (A.arch === 0) {
        vline(cx, top, bot, lit);
        blk("2P SVF", cx, (top + bot) / 2, w - 12, 18, lit);
        text("BP TAP", cx, (top + bot) / 2 + 20, 6.5, C.label);
    } else if (A.arch === 1) {
        vline(cx, top, bot, lit);
        var third = (bot - top) / 3;
        blk("HP 2P", cx, top + third, w - 12, 16, lit);
        blk("LP 2P", cx, top + 2 * third, w - 12, 16, lit);
    } else {
        var n = 4, st = (bot - top - 4) / n, xl = cx - 8;
        vline(xl, top, bot - 6, lit);
        for (var i = 0; i < n; i++) blk("P" + (i + 1), xl, top + 4 + st * (i + 0.5), 22, st - 4, lit);
        rgba(lit ? C.wire : C.wireOff);
        g.set_line_width(1);
        for (i = 0; i < n; i++) {
            var y = top + 4 + st * (i + 0.5);
            g.move_to(xl + 11, y);
            g.line_to(w - 9, y);
        }
        g.move_to(w - 9, top + 4);
        g.line_to(w - 9, bot);
        g.stroke();
        text("MIX", w - 9, top + 1, 6, C.label);
    }
    text("USES " + USES[A.arch], cx, h - 4, 7, lit ? C.text : C.label);
}
