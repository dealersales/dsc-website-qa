#!/usr/bin/env python3
"""Tunnel proxy: serve a bot-walled site through localhost by fetching each request over SSH.

For hosts (SiteGround and similar) that answer every request from a flagged IP with a challenge
page — including static assets — so a real browser cannot reach the site from this machine while
the server itself can. A browser pointed at this proxy loads the real page, in the real order,
with real JS.

usage:
  tunnel_proxy.py [port] [origin] [ssh_host] [ssh_port] [ssh_key]

example:
  tunnel_proxy.py 8199 https://example.co.uk user@ssh.example.co.uk 18765 ~/.ssh/key_ed25519

then:  curl http://127.0.0.1:8199/some-page/      # or point headless Chrome at it

Two rules keep this honest — both learned by chasing phantoms:

1. REWRITE the origin to the proxy in every text response. If you only proxy the HTML, the browser
   fetches assets straight from the live origin, gets challenge HTML for a .js request, and you get
   net::ERR_BLOCKED_BY_ORB — indistinguishable from a real site bug. (Cost an hour chasing a
   phantom "jQuery is not defined".)

2. NEVER cache a failed or truncated fetch. Persisting a 502 body means every later request serves
   it back and you debug that instead.

Also: after any change that purges the site's cache, drop the cached text/html entries (see
--purge-html) and refetch. Cache-busted asset filenames — SG Optimizer's combined CSS carries a
content hash — change on purge, so a stale cached page asks for a file that no longer exists and
renders unstyled. That is your cache, not their outage.
"""
import hashlib
import http.server
import os
import socketserver
import subprocess
import sys
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8199
ORIGIN = sys.argv[2] if len(sys.argv) > 2 else 'https://example.co.uk'
SSH_HOST = sys.argv[3] if len(sys.argv) > 3 else 'user@ssh.example.co.uk'
SSH_PORT = sys.argv[4] if len(sys.argv) > 4 else '22'
SSH_KEY = os.path.expanduser(sys.argv[5] if len(sys.argv) > 5 else '~/.ssh/id_ed25519')

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tunnel-cache')
os.makedirs(CACHE, exist_ok=True)

SSH = ['ssh', '-p', SSH_PORT, '-i', SSH_KEY, '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=60', SSH_HOST]

REMOTE = (
    "curl -sS -L --max-time 60 -D /tmp/hdr -o /tmp/bdy \"$URL\"; "
    "printf 'HTTPHEADERS\\n'; cat /tmp/hdr; printf '\\nBODY\\n'; cat /tmp/bdy"
)


def purge_html_cache():
    """Drop cached HTML pages so a changed page is refetched. Run this after any site edit."""
    n = 0
    for name in os.listdir(CACHE):
        path = os.path.join(CACHE, name)
        if not os.path.isfile(path):
            continue
        with open(path, 'rb') as f:
            head = f.read(300)
        if b'content-type: text/html' in head:
            os.remove(path)
            n += 1
    return n


def fetch(path, query=''):
    url = ORIGIN + path + (('?' + query) if query else '')
    key = hashlib.sha1(url.encode()).hexdigest()
    cached = os.path.join(CACHE, key)
    if os.path.exists(cached):
        with open(cached, 'rb') as f:
            return f.read()
    try:
        result = subprocess.run(SSH + [f'URL={url!r} bash -s'], input=REMOTE.encode(),
                                capture_output=True, timeout=180)
        data = result.stdout
    except subprocess.TimeoutExpired:
        return b''
    if data and b'\nBODY\n' in data:          # never persist a failure
        with open(cached, 'wb') as f:
            f.write(data)
    return data


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):             # keep the console quiet
        pass

    def do_GET(self):
        parts = urllib.parse.urlsplit(self.path)
        raw = fetch(parts.path, parts.query)
        if not raw:
            self.send_response(502)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if b'\nBODY\n' not in raw:
            body, ctype = raw, 'application/octet-stream'
        else:
            head, body = raw.split(b'\nBODY\n', 1)
            headers = head.split(b'HTTPHEADERS\n', 1)[-1].decode('utf-8', 'replace')
            ctype = 'text/html'
            for line in headers.splitlines():
                if line.lower().startswith('content-type:'):
                    ctype = line.split(':', 1)[1].strip()
            # rewrite absolute origin URLs so assets also come through the tunnel
            if any(t in ctype for t in ('html', 'css', 'javascript', 'json', 'xml', 'text/')):
                body = body.replace(ORIGIN.encode(), f'http://127.0.0.1:{PORT}'.encode())
                escaped = ORIGIN.replace('https://', 'https:\\/\\/').replace('/', '\\/')
                body = body.replace(escaped.encode(), f'http:\\/\\/127.0.0.1:{PORT}'.encode())
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(('127.0.0.1', PORT), Handler) as httpd:
    print(f'tunnel proxy :{PORT} -> {ORIGIN} via {SSH_HOST}  (cache: {CACHE})')
    print('purge cached HTML after any site edit, or you will chase a phantom styling outage')
    sys.stdout.flush()
    httpd.serve_forever()
