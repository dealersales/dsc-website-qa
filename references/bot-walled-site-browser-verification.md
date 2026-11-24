# Verifying a bot-walled site in a real browser (tunnel proxy)

SiteGround serves a `🐴 Robot Challenge` and answers **every** request from a flagged IP with
HTTP 202 + 183 bytes of challenge HTML — including static assets. `curl` and `browser_exec` both
die. Server-side `curl` over SSH still works fine.

So build a reverse proxy that fetches each request **from the server over SSH** and serve it on
localhost. A real Chrome then loads the real page, in the real order, with real JS.

## The three things that will bite you

1. **Rewrite absolute URLs in the response.** The page's own asset URLs are absolute
   (`https://example.co.uk/wp-content/...`). If you only proxy the HTML, the browser fetches the
   assets direct, hits the bot wall, gets HTML for a `.js` request and you get
   `net::ERR_BLOCKED_BY_ORB` — which looks exactly like a real site bug and is not one. Rewrite the
   origin to the proxy origin in every `text/*`, `javascript`, `css`, `json` response.
   This cost an hour of chasing a phantom `jQuery is not defined`.
2. **Never cache a failed or truncated fetch.** Persisting a 502 body means every later request
   serves it back and you chase that instead. Only write the cache on a real `BODY` marker.
3. **Purge the cached HTML before you believe a styling outage.** SiteGround Optimizer's combined
 stylesheet filename embeds a hash of its contents (`siteground-optimizer-combined-css-<hash>.css`)
 and that hash **changes on every purge**. A cached page still referencing the previous hash asks
 the origin for a file that no longer exists, gets a 404, and renders completely unstyled — giant
 fallback icons and stacked links, indistinguishable from the client's stylesheet having died. It
 is your cache, not their site. After any change that triggers a purge, drop the proxy's cached
 `text/html` entries and refetch; and confirm the real state server-side before reporting anything:
 `ssh … "curl -sI https://<domain>/wp-content/uploads/siteground-optimizer-assets/<href>.css"`.
 Every page's CSS answering 200 from the server is the answer to "did I break the site?".

## Shape

A working implementation is in `scripts/tunnel_proxy.py` — copy it into a **durable** directory (a
persistent tools folder, not the session scratch dir, which is pruned) and run it with
`[port] [origin] [ssh_host] [ssh_port] [ssh_key]` rather than rebuilding it from this prose.

```python
remote = ("curl -sS -L --max-time 60 -D /tmp/hdr -o /tmp/bdy \"$URL\"; "
          "printf 'HTTPHEADERS\\n'; cat /tmp/hdr; printf '\\nBODY\\n'; cat /tmp/bdy")
subprocess.run(SSH + [f'URL={url!r} bash -s'], input=remote.encode(), capture_output=True)
```

Serve with a threaded `http.server`, no-store, and rewrite on the way out.

## Prewarm, then test

Each asset is an SSH round trip, so a cold page load over the tunnel times out and gives you
half-loaded JS — another phantom. Before launching the browser, fetch the page, extract every
`src`/`href`, and fetch each one through the proxy. Then also prewarm **lazily-loaded webpack
chunks**: `find` every `.js` under the plugin `assets/js` and `build` dirs and fetch each through
the proxy, or you get `ChunkLoadError` for widget handlers that is purely an artefact.

## Driving it

`ssh -D` (SOCKS) is usually refused on SiteGround — `channel 2: open failed: administratively
prohibited`. Plain `-L`/`-D` forwarding is off; the SSH-command-per-request proxy above is the way.

Launch headless Chrome with `--remote-debugging-port` and drive raw CDP via `websocket-client`.
The user site-packages path may be absent in a non-interactive shell — add
`sys.path.insert(0, os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages'))` before
`import websocket`.

Useful probes once loaded: `typeof window.<global>`, element counts,
`elementorFrontend.hooks`, and `Page.addScriptToEvaluateOnNewDocument` to A/B a shim.

## When you have no SSH to the host — fetch the rendered HTML through microlink

The tunnel proxy above needs SSH. Staging accounts you were handed (not built) usually have
none, and then the whole build is behind a wall you cannot pass. **`api.microlink.io` will
fetch a bot-walled URL from its own IP and hand back the JS-rendered outer HTML** — enough
for every head-layer, form and link-state check:

```bash
curl -s "https://api.microlink.io/?url=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$URL")\
&meta=false&data.html.selector=html&data.html.type=html" | python3 -c "import json,sys;print('<html>'+json.load(sys.stdin)['data']['html'])"
```

It renders JS before returning, so `<form>` elements, widget output and icon markup are the
**mounted** ones, not the source templates — a real advantage over `curl`, and the reason a
`<form>` count from this source is trustworthy. Free tier rate-limits, so pace the requests
(6s between) and retry; a few pages will land on the challenge page instead, which is visible
as a ~38KB body titled `Robot Challenge Screen`. Read `data.html` with a length floor and a
challenge-string guard before trusting it.

`r.jina.ai` (`x-return-format: html`) also works and gives cleaner raw bytes — but it
Cloudflare-walls after a burst of requests, and its plain markdown mode reports the upstream
status (`Warning: Target URL returned error 404`), which makes it the cheapest status sweep
while it lasts. Use jina for status codes, microlink for guaranteed raw HTML.

**Routes that did NOT work on a SiteGround sgcaptcha wall — don't spend the pass on them:**
PSI (`pagespeedonline`) returns 429 on a shared VPN egress; `api.codetabs.com` 503;
`api.allorigins.win` 522; `corsproxy.io` keyless-blocked; thingproxy dead; scraperapi needs a
key. **Do not try to beat the challenge client-side**: the PoW token is bound to the client IP
and the server rejects it, so cookies, blob workers and `crypto.subtle` all testing fine in the
browser proves nothing. Confirm that diagnosis once (three one-line probes) and move to the
API route rather than rebuilding the browser harness.

### Guard the sweep against a challenge you did not anticipate

**There is more than one interstitial in this game, and the second one silently outranks the
first.** A sweep script that guards against SiteGround's `sgcaptcha` / `Robot Challenge` string
will happily score Cloudflare's edge page (`<title>Just a moment...</title>`) as a **200 with
zero content** — the guard matched the wall it was written for, the status classifier saw a
clean read, and 36 shell pages went into the results file looking like successes. Caught only
by reading a raw output file and noticing every one was ~5.8KB.

So do not classify on the presence of a known challenge string. Assert the **positive**:
require a title and a minimum body length, and fail anything that has neither.

```bash
# a real page has a usable title AND real body text
title=$(grep -m1 '^Title:' "$f" | sed 's/^Title: //')
body=$(sed -n '/Markdown Content:/,$p' "$f" | tr -d '\n' | wc -c)
[ -n "$title" ] && [ "$body" -gt 400 ] || echo "UNKNOWN (challenge?) $url"
```

Then **read the summary as a set, not a row at a time**: a status column where every entry is
identical (`200` ×36, or all `404`) is not a result, it is a wall. Any sweep whose outcome is
totally uniform has measured the transport, not the site. Same rule for comment-count sweeps
and link-status runs.
