// df_button.js — Dub Filter v1.5 reusable illuminated button (jsui + mgraphics).
//
// The button never owns state. It shows the value of the native object it is wired
// to (send it an int) and, when clicked, asks that object for a change (outlet 0).
// The native object stays the single source of truth, so automation, MIDI mapping,
// presets and undo behave exactly as before.
//
// Arguments: label  index  mode
//   mode "select"    : lit when the incoming value == index; click outputs index
//   mode "toggle"    : lit when the incoming value != 0; click outputs the opposite
//   mode "momentary" : outputs 1 on press, 0 on release
// Messages:  int / float  current value       unavailable 0|1   reduced-contrast, ignores clicks
//            label <sym> change the caption

inlets = 1;
outlets = 1;
setinletassist(0, "current value (int); unavailable 0|1; label <text>");
setoutletassist(0, "requested value -> native control");

mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var C = {
    off: [0.204, 0.192, 0.176, 1], offHover: [0.255, 0.239, 0.220, 1],
    on: [0.949, 0.627, 0.227, 1], onHover: [1.0, 0.698, 0.310, 1],
    pressed: [0.141, 0.133, 0.122, 1], pressedOn: [0.769, 0.490, 0.157, 1],
    unavail: [0.129, 0.122, 0.114, 1], unavailOn: [0.420, 0.290, 0.141, 1],
    border: [0.310, 0.282, 0.255, 1], borderOn: [1.0, 0.776, 0.451, 1],
    text: [0.639, 0.604, 0.549, 1], textHover: [0.925, 0.894, 0.831, 1],
    textOn: [0.102, 0.078, 0.063, 1], textUnavail: [0.369, 0.345, 0.314, 1]
};

var label = jsarguments.length > 1 ? String(jsarguments[1]).replace(/_/g, " ") : "BUTTON";
var myIndex = jsarguments.length > 2 ? Number(jsarguments[2]) : 1;
var mode = jsarguments.length > 3 ? String(jsarguments[3]) : "toggle";
var value = 0, hover = 0, pressed = 0, unavail = 0;

function size() {
    if (mgraphics.size) return mgraphics.size;
    return [box.rect[2] - box.rect[0], box.rect[3] - box.rect[1]];
}

function isOn() { return mode === "select" ? value === myIndex : value !== 0; }

// one of: off, hover, pressed, selected, selected_hover, selected_pressed, unavailable, unavailable_on
function state() {
    if (unavail) return isOn() ? "unavailable_on" : "unavailable";
    var on = isOn();
    if (pressed) return on ? "selected_pressed" : "pressed";
    if (on) return hover ? "selected_hover" : "selected";
    return hover ? "hover" : "off";
}

var FILL = { off: "off", hover: "offHover", pressed: "pressed", selected: "on", selected_hover: "onHover",
             selected_pressed: "pressedOn", unavailable: "unavail", unavailable_on: "unavailOn" };
var INK = { off: "text", hover: "textHover", pressed: "text", selected: "textOn", selected_hover: "textOn",
            selected_pressed: "textOn", unavailable: "textUnavail", unavailable_on: "textUnavail" };

function paint() {
    var s = size(), w = s[0], h = s[1], st = state(), lit = st.indexOf("selected") === 0;
    var g = mgraphics;
    rgba(C[FILL[st]]);
    g.rectangle_rounded(0.5, 0.5, w - 1, h - 1, 3, 3);
    g.fill();
    if (lit) {                       // illumination: a soft top highlight, no gradient fill
        g.set_source_rgba(1, 0.86, 0.6, st === "selected_pressed" ? 0.0 : 0.35);
        g.rectangle(3, 1.5, w - 6, 1);
        g.fill();
    }
    if (st === "pressed" || st === "selected_pressed") {   // recessed: inner top shadow
        g.set_source_rgba(0, 0, 0, 0.45);
        g.rectangle(1.5, 1.5, w - 3, 1.5);
        g.fill();
    }
    rgba(lit ? C.borderOn : C.border);
    g.set_line_width(1);
    g.rectangle_rounded(0.5, 0.5, w - 1, h - 1, 3, 3);
    g.stroke();
    g.select_font_face("Arial Bold");
    g.set_font_size(Math.min(8.5, h * 0.58));
    var tm = g.text_measure(label);
    var dy = (st === "pressed" || st === "selected_pressed") ? 0.5 : 0;
    rgba(C[INK[st]]);
    g.move_to(Math.round((w - tm[0]) / 2), Math.round(h / 2 + tm[1] * 0.32 + dy));
    g.show_text(label);
}

function msg_int(v) { value = v | 0; mgraphics.redraw(); }
function msg_float(v) { msg_int(Math.round(v)); }
function unavailable(v) { unavail = v ? 1 : 0; if (unavail) { pressed = 0; } mgraphics.redraw(); }
function anything() {
    if (messagename === "label") { label = arrayfromargs(arguments).join(" "); mgraphics.redraw(); }
}
function rgba(c) { mgraphics.set_source_rgba(c[0], c[1], c[2], c[3]); }

function inside(x, y) { var s = size(); return x >= 0 && y >= 0 && x < s[0] && y < s[1]; }

function onclick(x, y, but) {
    if (unavail) return;
    pressed = 1;
    if (mode === "momentary") outlet(0, 1);
    mgraphics.redraw();
}

function ondrag(x, y, but) {
    if (but !== 0 || !pressed) return;     // release
    pressed = 0;
    if (mode === "momentary") outlet(0, 0);
    else if (inside(x, y)) outlet(0, mode === "select" ? myIndex : (isOn() ? 0 : 1));
    mgraphics.redraw();
}

function onidle(x, y) { if (!hover) { hover = 1; mgraphics.redraw(); } }
function onidleout() { if (hover) { hover = 0; mgraphics.redraw(); } }
