#!/usr/bin/env python3
"""Scroll a live page in headless Chrome over CDP and catch frames that paint black.

Why this exists: a page can look perfect in a screenshot at rest and still flash
blank while scrolling. Browser-harness helpers often cannot drive scrolling on a
heavy page (their runtime calls time out), so this talks to Chrome directly.

The method: navigate, then for each scroll offset capture twice - immediately
after the scroll, and again after the compositor settles - and print the mean
brightness of each frame. A *flash* shows as an instant frame far from its
settled partner in EITHER direction: mean ~0 is a fully black viewport, mean
~240 is a fully blank white one, and they are the same defect. A consistent
difference at one offset is a real defect; random dips are capture noise, so
run it twice.

Usage:
    python3 scroll_probe.py <url> [outdir] [viewport]
    python3 scroll_probe.py https://example.com/ /tmp/frames 1400x900

Requires: websocket-client, Pillow, and Google Chrome on macOS.
Compare against a control URL (e.g. https://example.com/) before reporting a
flash: the control should never show the same dip.
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

import websocket
from PIL import Image

URL = sys.argv[1] if len(sys.argv) > 1 else "about:blank"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/scrollframes"
VIEWPORT = sys.argv[3] if len(sys.argv) > 3 else "1400x900"
WIDTH, HEIGHT = (int(x) for x in VIEWPORT.lower().split("x"))
PORT = int(os.environ.get("SCROLL_PROBE_PORT", "9251"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

os.makedirs(OUT, exist_ok=True)

chrome = subprocess.Popen(
    [CHROME, f"--remote-debugging-port={PORT}", "--headless=new", "--disable-gpu",
     "--no-first-run", "--hide-scrollbars", f"--window-size={WIDTH},{HEIGHT}",
     f"--user-data-dir=/tmp/scrollprobe-profile-{PORT}", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)


def page_ws():
    for _ in range(40):
        try:
            for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2)):
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit("chrome did not expose a page target")


ws = websocket.create_connection(page_ws(), timeout=30)
_id = [0]


def cmd(method, **params):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id[0]:
            return msg.get("result", {})


cmd("Page.enable")
cmd("Runtime.enable")
cmd("Page.navigate", url=URL)
time.sleep(12)


def evaluate(expr):
    return cmd("Runtime.evaluate", expression=expr, returnByValue=True).get("result", {}).get("value")


def shot(name):
    data = cmd("Page.captureScreenshot", format="png").get("data")
    if not data:
        return None
    path = os.path.join(OUT, name)
    open(path, "wb").write(base64.b64decode(data))
    return path


height = evaluate("document.documentElement.scrollHeight") or 0
print("page height:", height)

frames = []
step = max(600, HEIGHT - 200)
offsets = list(range(0, max(height - HEIGHT, 0) + 1, step)) or [0]
for y in offsets:
    evaluate(f"window.scrollTo(0,{y})")
    # Read the offset back: a scroll can silently fail and every later frame is
    # then a clean capture of a page that never moved.
    actual = evaluate("window.scrollY") or 0
    time.sleep(0.4)
    instant = shot(f"y{y}_instant.png")
    time.sleep(1.2)
    settled = shot(f"y{y}_settled.png")
    frames.append((y, actual, instant, settled))

ws.close()
chrome.terminate()


def mean(path):
    if not path or not os.path.exists(path):
        return -1.0
    im = Image.open(path).convert("L")
    px = im.getdata()
    return round(sum(px) / len(px), 1)


print("\n  y      instant   settled   delta   verdict")
worst = None
for y, actual, a, b in frames:
    mi, ms = mean(a), mean(b)
    delta = round(abs(mi - ms), 1)
    verdict = ""
    if actual != y:
        verdict = "DID NOT SCROLL"
    # Either direction counts. A light flash is the same defect as a dark one:
    # an element painting at viewport size before layout settles.
    elif delta > 30:
        verdict = "DARK FLASH" if mi < ms else "LIGHT FLASH"
        if worst is None or delta > worst[3]:
            worst = (y, mi, ms, delta)
    print(f"  {y:<7} {mi:>8}  {ms:>8}  {delta:>6}   {verdict}")

if worst:
    print(f"\nWorst flash at y={worst[0]}: {worst[1]} vs {worst[2]} settled ({worst[3]} delta).")
    print(f"Frames saved in {OUT}. Look for an element resolving to viewport size")
    print("before layout settles (an iframe with height:100% inside a wrapper sized")
    print("by padding), a src-less iframe painting black, a dark html canvas, or a")
    print("background-attachment:fixed layer.")
else:
    print("\nNo frames more than 30 points from settled. Re-run to confirm before")
    print("reporting a clean bill.")
