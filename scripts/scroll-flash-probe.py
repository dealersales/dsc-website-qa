#!/usr/bin/env python3
"""Find a blank or black frame that appears mid-scroll.

    python3 scroll-flash-probe.py https://example.co.uk/ [--step 700] [--out /tmp/frames]

A customer reports "the page goes blank for a second when I scroll". HTTP status
codes cannot see it and neither can a full-page screenshot: the fault is one
frame, painted before something loads, at one scroll position.

This walks the page in viewport-sized steps and, at each step, captures a frame
**immediately** after the scroll and again ~1.2 s later. A flash shows up as a
large gap between the two mean brightnesses. A completely black frame reads 0.0;
a completely white one reads ~242.

Requires `websocket-client` (pip install websocket-client) and Chrome.
Exit code 1 if any step flashes, so it can gate a deploy.

Why it is worth running even when the page "looks fine": a tall element that
paints before its content arrives (an iframe with no src yet, a
background-attachment:fixed layer, a container sized 100% of the viewport while
layout settles) covers the screen for a beat. The usual suspects, in the order
that has paid off:

  * an <iframe> with no src until a lazy loader fires - it paints black at its
    container's height, and if that height resolved against the viewport the
    whole page goes black;
  * the html canvas being dark (`html{background-color:#1f1f1f}`) so any
    unpainted moment reads as black - set it to the page's own background;
  * `background-attachment: fixed`, which forces a full-viewport repaint on
    every scroll frame.

Fix the sizing (bind the iframe to its wrapper with position:absolute;inset:0
and give the wrapper an explicit height), not the colour - changing the iframe's
surface from black to light turns a black flash into a white one and leaves the
cause in place.
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.request

PORT = 9261

def target_ws():
    for _ in range(40):
        try:
            data = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2))
            for t in data:
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit("chrome did not expose a page target")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--step", type=int, default=700, help="scroll increment in px")
    ap.add_argument("--out", default="/tmp/scroll-frames")
    ap.add_argument("--viewport", default="1400,900")
    ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--rounds", type=int, default=8)
    args = ap.parse_args()

    import websocket  # noqa: imported late so --help works without the dep

    os.makedirs(args.out, exist_ok=True)
    chrome = subprocess.Popen([
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--remote-debugging-port={PORT}", "--headless=new", "--disable-gpu",
        "--no-first-run", "--hide-scrollbars", f"--window-size={args.viewport}",
        f"--user-data-dir={args.out}/profile", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws = websocket.create_connection(target_ws(), timeout=30)
        seq = [0]

        def cmd(method, **params):
            seq[0] += 1
            ws.send(json.dumps({"id": seq[0], "method": method, "params": params}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == seq[0]:
                    return msg.get("result", {})

        cmd("Page.enable")
        cmd("Runtime.enable")
        cmd("Page.navigate", url=args.url)
        time.sleep(10)

        def evaluate(expr):
            r = cmd("Runtime.evaluate", expression=expr, returnByValue=True)
            return r.get("result", {}).get("value")

        def shot(name):
            data = cmd("Page.captureScreenshot", format="png").get("data")
            if not data:
                return None
            path = os.path.join(args.out, name)
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(data))
            return path

        height = evaluate("document.documentElement.scrollHeight") or 0
        print(f"page height {height}px, viewport {args.viewport}")
        print(f"{'y':>6}  {'instant':>8}  {'settled':>8}  verdict")

        from PIL import Image
        bad = 0
        for n in range(args.rounds):
            y = min(n * args.step, max(height - 900, 0))
            evaluate(f"window.scrollTo(0,{y})")
            time.sleep(0.4)
            a = shot(f"y{y}_instant.png")
            time.sleep(args.settle)
            b = shot(f"y{y}_settled.png")

            def mean(p):
                if not p or not os.path.exists(p):
                    return -1.0
                im = Image.open(p).convert("L")
                px = list(im.getdata())
                return sum(px) / len(px)

            ma, mb = mean(a), mean(b)
            flash = abs(ma - mb) > 40
            if flash:
                bad += 1
            print(f"{y:>6}  {ma:>8.1f}  {mb:>8.1f}  {'FLASH' if flash else 'ok'}")

        ws.close()
        if bad:
            print(f"\n{bad} position(s) flash. Inspect {args.out}/y*_instant.png")
            return 1
        print("\nNo blank frames detected.")
        return 0
    finally:
        chrome.terminate()

if __name__ == "__main__":
    sys.exit(main())
