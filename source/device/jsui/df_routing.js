// df_routing.js — Dub Filter v1.5 filter-routing diagram (jsui + mgraphics). Display only.
//
// Draws the topology the engine actually runs (source/src/routing.py, build_genexpr.py):
//   SERIES   : [BP if PRE] -> LP/HP in Stage Order -> [BP if POST]; bypassed stages pass signal
//   PARALLEL : IN feeds LP, HP and BP; outputs summed with the parallel levels; a bypassed
//              stage drops out of the sum; with all three bypassed the dry signal passes
//   HYBRID   : (LP/HP in Stage Order) + BP fed from IN, BP added at its level; BPF Position ignored
// Messages (from the native parameters): route n, order n, bpos n, lon n, hon n, bon n

inlets = 1;
outlets = 0;
setinletassist(0, "route / order / bpos / lon / hon / bon <int>");

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var C = {
    bg: [0.090, 0.086, 0.082, 1], wire: [0.949, 0.627, 0.227, 1], wireOff: [0.290, 0.267, 0.239, 1],
    box: [0.204, 0.192, 0.176, 1], boxOn: [0.949, 0.627, 0.227, 1], edge: [0.486, 0.447, 0.400, 1],
    text: [0.925, 0.894, 0.831, 1], textOn: [0.102, 0.078, 0.063, 1], dim: [0.369, 0.345, 0.314, 1]
};

var S = { route: 0, order: 0, bpos: 0, lon: 1, hon: 1, bon: 0 };

function route(v) { S.route = v | 0; mgraphics.redraw(); }
function order(v) { S.order = v | 0; mgraphics.redraw(); }
function bpos(v) { S.bpos = v | 0; mgraphics.redraw(); }
function lon(v) { S.lon = v ? 1 : 0; mgraphics.redraw(); }
function hon(v) { S.hon = v ? 1 : 0; mgraphics.redraw(); }
function bon(v) { S.bon = v ? 1 : 0; mgraphics.redraw(); }

// Pure description of the signal graph for a state (also used by the offline tests).
// series: ordered stage list; branches: parallel lanes, each an ordered stage list;
// on: which stages process; dry: whether the unprocessed input reaches the output.
function topology(st) {
    var on = { LP: st.lon, HP: st.hon, BP: st.bon };
    var lh = st.order ? ["HP", "LP"] : ["LP", "HP"];
    if (st.route === 0) {
        var seq = st.bpos ? ["BP"].concat(lh) : lh.concat(["BP"]);
        return { kind: "SERIES", series: seq, branches: [seq], on: on, dry: !(on.LP || on.HP || on.BP) };
    }
    if (st.route === 1) {
        return { kind: "PARALLEL", series: [], branches: [["LP"], ["HP"], ["BP"]], on: on,
                 dry: !(on.LP || on.HP || on.BP) };
    }
    return { kind: "HYBRID", series: lh, branches: [lh, ["BP"]], on: on, dry: false };
}

function size() {
    if (mgraphics.size) return mgraphics.size;
    return [box.rect[2] - box.rect[0], box.rect[3] - box.rect[1]];
}
function rgba(c) { mgraphics.set_source_rgba(c[0], c[1], c[2], c[3]); }

function line(x0, y0, x1, y1, lit) {
    var g = mgraphics;
    rgba(lit ? C.wire : C.wireOff);
    g.set_line_width(lit ? 1.5 : 1);
    g.move_to(x0, y0);
    g.line_to(x1, y1);
    g.stroke();
}

function stage(name, cx, cy, w, h, on) {
    var g = mgraphics;
    rgba(on ? C.boxOn : C.box);
    g.rectangle_rounded(cx - w / 2, cy - h / 2, w, h, 2, 2);
    g.fill();
    rgba(on ? C.boxOn : C.edge);
    g.set_line_width(1);
    g.rectangle_rounded(cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, 2, 2);
    g.stroke();
    g.select_font_face("Arial Bold");
    g.set_font_size(7.5);
    var t = on ? name : name + " ·";
    var tm = g.text_measure(t);
    rgba(on ? C.textOn : C.dim);
    g.move_to(cx - tm[0] / 2, cy + tm[1] * 0.32);
    g.show_text(t);
}

function sumNode(cx, cy, lit) {
    var g = mgraphics;
    rgba(C.bg);
    g.arc(cx, cy, 5, 0, Math.PI * 2);
    g.fill();
    rgba(lit ? C.wire : C.wireOff);
    g.set_line_width(1.2);
    g.arc(cx, cy, 5, 0, Math.PI * 2);
    g.stroke();
    g.move_to(cx - 2.5, cy); g.line_to(cx + 2.5, cy);
    g.move_to(cx, cy - 2.5); g.line_to(cx, cy + 2.5);
    g.stroke();
}

function caption(t, x, y, col) {
    var g = mgraphics;
    g.select_font_face("Arial Bold");
    g.set_font_size(6.5);
    rgba(col);
    g.move_to(x, y);
    g.show_text(t);
}

function paint() {
    var s = size(), w = s[0], h = s[1], g = mgraphics, T = topology(S);
    rgba(C.bg);
    g.rectangle_rounded(0, 0, w, h, 3, 3);
    g.fill();
    var xi = 16, xo = w - 18, bw = 30, bh = 13;
    caption("IN", 2, h / 2 + 2.5, C.text);
    caption("OUT", w - 16, h / 2 + 2.5, C.text);
    if (T.kind === "SERIES") {
        var n = T.series.length, cy = h / 2, step = (xo - xi) / n;
        line(xi, cy, xo, cy, true);              // every stage passes signal (bypass = wire)
        for (var i = 0; i < n; i++) {
            var nm = T.series[i];
            stage(nm, xi + step * (i + 0.5), cy, bw, bh, T.on[nm]);
        }
        return;
    }
    var xs = xi + 6, xsum = xo - 8, lanes = T.branches.length;
    var ys = [];
    for (var k = 0; k < lanes; k++) ys.push(lanes === 3 ? 8 + k * (h - 16) / 2 : h * (k ? 0.74 : 0.28));
    var anyLit = false;
    for (k = 0; k < lanes; k++) {
        var lane = T.branches[k], live = false;
        for (var j = 0; j < lane.length; j++) live = live || T.on[lane[j]];
        if (T.kind === "HYBRID" && k === 0) live = true;     // series lane always reaches the sum
        anyLit = anyLit || live;
        line(xs, h / 2, xs, ys[k], true);
        line(xs, ys[k], xsum, ys[k], live);
        line(xsum, ys[k], xsum, h / 2, live);
        var span = (xsum - xs) - 8, st = span / lane.length;
        for (j = 0; j < lane.length; j++) {
            stage(lane[j], xs + 4 + st * (j + 0.5), ys[k], Math.min(bw, st - 6), bh - 2, T.on[lane[j]]);
        }
    }
    line(xi, h / 2, xs, h / 2, true);
    if (T.dry) {                                             // all three bypassed: dry passes
        caption("DRY", (xs + xsum) / 2 - 8, h / 2 + 2.5, C.wire);
        anyLit = true;
    }
    sumNode(xsum, h / 2, anyLit);
    line(xsum + 5, h / 2, xo, h / 2, anyLit);
}
