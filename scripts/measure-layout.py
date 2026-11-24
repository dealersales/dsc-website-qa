#!/usr/bin/env python3
"""Measure whether a page's interactive elements are clipped, at a range of viewport widths.

Why this exists: on these templates `html, body { overflow-x: hidden }` plus
`* { max-width: 100% }` means content that overruns is CLIPPED rather than scrollable, so
`document.documentElement.scrollWidth` equals the viewport and a width-only check reports a
clean pass on a page whose primary CTA is half off-screen. This measures the right edge of
every matching element against `window.innerWidth` instead.

Requires: `websocket-client` (system python3 on the DSC Macs has it) and Google Chrome.

Usage:
    python3 measure-layout.py https://example.co.uk/ 1024 1100 1280 1440
    python3 measure-layout.py URL 1024 1280 --selector 'header a, header button'
    python3 measure-layout.py URL 1024 1280 --css '@candidate.css'
    python3 measure-layout.py URL 1024 1280 --css '@media (min-width:1024px){header nav{gap:6px}}'

--css injects a candidate rule before measuring, so a fix can be tested before it is deployed.
Exit code 1 if any measured element overruns its viewport.
"""
import base64
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request

import websocket

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]
MIN_SLACK = 16  # px of headroom before calling a width safe


def parse_args(argv):
    if not argv:
        sys.exit(__doc__)
    url = argv[0]
    widths, selector, css = [], "header a, header button", ""
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--selector":
            selector = argv[i + 1]; i += 2
        elif a == "--css":
            v = argv[i + 1]
            css = open(v[1:]).read() if v.startswith("@") else v
            i += 2
        else:
            widths.append(int(a)); i += 1
    return url, (widths or [1024, 1100, 1280, 1440]), selector, css


def chrome_binary():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    sys.exit("no Chrome binary found; edit CHROME_CANDIDATES")


def main():
    url, widths, selector, css = parse_args(sys.argv[1:])
    port = 9333
    profile = "/tmp/dsc-measure-layout"
    proc = subprocess.Popen(
        [chrome_binary(), "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--remote-debugging-port={port}", f"--user-data-dir={profile}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def ws_url():
        for _ in range(60):
            try:
                for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json")):
                    if t.get("type") == "page":
                        return t["webSocketDebuggerUrl"]
            except Exception:
                pass
            time.sleep(0.25)
        sys.exit("devtools never became available")

    ws = websocket.create_connection(ws_url(), timeout=25)
    counter = [0]

    def cmd(method, **params):
        counter[0] += 1
        ws.send(json.dumps({"id": counter[0], "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == counter[0]:
                return msg.get("result", {})

    def js(expr):
        r = cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r.get("result", {}).get("value")

    failures = 0
    try:
        cmd("Page.enable")
        cmd("Page.navigate", url=url)
        time.sleep(4)
        if css:
            js("(() => {const s=document.createElement('style'); s.id='dsc-candidate';"
               f"s.textContent={json.dumps(css)}; document.head.appendChild(s); return true;}})()")

        print(f"{url}\n{'width':>6} {'innerW':>7} {'furthest':>9} {'slack':>6}  verdict  element")
        for w in widths:
            cmd("Emulation.setDeviceMetricsOverride", width=w, height=900,
                deviceScaleFactor=1, mobile=(w < 768))
            time.sleep(0.9)
            data = js("(() => {let worst=0,label='';"
                      f"document.querySelectorAll({json.dumps(selector)}).forEach(el=>{{const r=el.getBoundingClientRect();"
                      "if(r.width<1) return; if(r.right>worst){worst=r.right;"
                      "label=(el.textContent||el.getAttribute('aria-label')||'').trim().replace(/\\s+/g,' ').slice(0,24);}});"
                      "return {worst:Math.round(worst), label, inner:window.innerWidth};})()")
            if not data:
                print(f"{w:>6}  measurement failed")
                failures += 1
                continue
            slack = data["inner"] - data["worst"]
            verdict = "PASS" if slack >= MIN_SLACK else ("TIGHT" if slack >= 0 else "CLIPPED")
            if slack < MIN_SLACK:
                failures += 1
            print(f"{w:>6} {data['inner']:>7} {data['worst']:>9} {slack:>6}  {verdict:<7}  {data['label']}")
    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    print("\nAll widths have >=%dpx slack" % MIN_SLACK if not failures
          else f"\n{failures} width(s) at or past the edge")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
