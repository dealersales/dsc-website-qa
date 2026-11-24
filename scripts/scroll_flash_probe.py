#!/usr/bin/env python3
"""Detect a page that flashes blank/black while scrolling.

Reports a mean-brightness table: one frame grabbed immediately after each scroll
step, one after it settles. A flash can go either way and both are reported:

    4590  instant   0.0   settled 163.6   <- black flash (src-less iframe)
     700  instant 242.0   settled 183.9   <- white flash (full-viewport box)

Checking only for darkening misses the second kind entirely, which is what a
full-screen blank box looks like once the surface behind it is light.

Usage:
    python3 scroll_flash_probe.py <url> [outdir]

Why CDP directly: a browser-automation wrapper may refuse or time out on
window.scrollTo for heavy pages, and then you cannot reproduce the bug at all.
Driving headless Chrome over websocket and using Page.captureScreenshot gives
frame-accurate evidence. Needs: pip install websocket-client, Pillow.
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

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8181/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/scrollframes"
PORT = int(os.environ.get("PROBE_PORT", "9251"))
CHROME = os.environ.get(
    "CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

os.makedirs(OUT, exist_ok=True)

chrome = subprocess.Popen(
    [
        CHROME,
        f"--remote-debugging-port={PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--hide-scrollbars",
        "--window-size=1400,900",
        f"--user-data-dir=/tmp/scrollprobe-profile-{PORT}",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


def page_target():
    for _ in range(40):
        try:
            tabs = json.load(
                urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT}/json/list", timeout=2
                )
            )
            for tab in tabs:
                if tab.get("type") == "page":
                    return tab["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.5)
    chrome.terminate()
    raise SystemExit("chrome did not expose a debug target")


ws = websocket.create_connection(page_target(), timeout=30)
counter = [0]


def cmd(method, **params):
    counter[0] += 1
    ws.send(json.dumps({"id": counter[0], "method": method, "params": params}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == counter[0]:
            return msg.get("result", {})


cmd("Page.enable")
cmd("Runtime.enable")
cmd("Page.navigate", url=URL)
time.sleep(12)


def evaluate(expression):
    result = cmd("Runtime.evaluate", expression=expression, returnByValue=True)
    return result.get("result", {}).get("value")


height = evaluate("document.documentElement.scrollHeight") or 2000
print(f"url: {URL}\npage height: {height}")


def grab(name):
    data = cmd("Page.captureScreenshot", format="png").get("data")
    if not data:
        return None
    path = os.path.join(OUT, name)
    with open(path, "wb") as handle:
        handle.write(base64.b64decode(data))
    return path


steps = list(range(0, max(height, 1200), 700))
rows = []
for step in steps:
    evaluate(f"window.scrollTo(0,{step})")
    time.sleep(0.4)
    instant = grab(f"y{step}_instant.png")
    time.sleep(1.2)
    settled = grab(f"y{step}_settled.png")
    rows.append((step, instant, settled))

ws.close()
chrome.terminate()


def mean(path):
    if not path or not os.path.exists(path):
        return -1.0
    pixels = list(Image.open(path).convert("L").getdata())
    return round(sum(pixels) / len(pixels), 1)


print(f"\n  {'scroll':>7}  {'instant':>9}  {'settled':>9}")
suspects = 0
for step, instant, settled in rows:
    a, b = mean(instant), mean(settled)
    flag = ""
    gap = abs(a - b) if a >= 0 and b >= 0 else 0.0
    if gap > 25:
        flag = "  <-- flash"
        suspects += 1
    print(f"  {step:>7}  {a:>9}  {b:>9}{flag}")

print(f"\nframes saved to {OUT}")
if suspects:
    print(
        f"{suspects} scroll position(s) painted very differently from how they settle -- "
        "open the *_instant.png frames and inspect the markup at that offset. Black means an "
        "iframe with no src; near-white means a box resolving against the viewport."
    )
