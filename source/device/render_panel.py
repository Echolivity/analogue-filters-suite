"""Render the hardware-replica panel images (dfx_*.png, 1x and @2x) into device/panel/.
Deterministic; needs numpy, scipy, Pillow. Run from source/ after layout changes, then
rebuild (build.sh copies them next to the device).   python3 device/render_panel.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hwpanel
ns = {"__name__": "panelspec", "__file__": os.path.join(HERE, "build_device.py")}
exec(compile(open(os.path.join(HERE, "build_device.py")).read(), "build_device.py", "exec"), ns)
print("\n".join(hwpanel.render(ns["SPEC"], os.path.join(HERE, "panel"))))
